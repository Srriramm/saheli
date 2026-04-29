import json
import base64
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional
from llama_cpp import Llama
import llama_cpp.llama_cpp as _llama_lib
from config.settings import MAX_TOKENS, CONTEXT_LENGTH

# Disable CPU_REPACK: llama-cpp-python 0.3.x pre-allocates a ~1.8 GB contiguous
# buffer for weight repacking. On machines with ≤5 GB RAM this OOMs before the
# model weights even load. use_extra_bufts=False skips that buffer entirely.
_orig_model_params = _llama_lib.llama_model_default_params
def _no_repack_model_params():
    p = _orig_model_params()
    p.use_extra_bufts = False
    return p
_llama_lib.llama_model_default_params = _no_repack_model_params

# Set up logging for clinical inference calls
log_dir = Path("./logs")
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    filename=log_dir / "inference.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Derived mmproj path: same directory as GGUF, suffix replaced
def _mmproj_path(model_path: str) -> str:
    # e.g. gemma-4-E4B-IT-Q4_K_M.gguf → gemma-4-E4B-IT-mmproj-f16.gguf
    p = Path(model_path)
    base = p.stem  # strip .gguf
    # Replace the quant suffix (everything from the last -Q or -q) with mmproj tag
    import re
    base_no_quant = re.sub(r"-[Qq]\d.*$", "", base)
    return str(p.parent / f"{base_no_quant}-mmproj-f16.gguf")


class GemmaRunner:
    """Core inference wrapper for Gemma 4 using llama.cpp"""

    def __init__(self, model_path: str, n_ctx: int = CONTEXT_LENGTH, n_gpu_layers: int = -1):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.llm = None
        self.llm_vision = None  # separate Llama instance with chat handler for vision

        # Load base text model
        try:
            self.llm = Llama(
                model_path=model_path,
                n_ctx=n_ctx,
                n_gpu_layers=n_gpu_layers,
                n_batch=128,
                chat_format="gemma",
                verbose=False,
            )
            logging.info(f"Text model loaded from {model_path}")
        except Exception as e:
            logging.error(f"Failed to load text model: {e}")

        # Load multimodal model variant if mmproj exists
        mmproj = _mmproj_path(model_path)
        if Path(mmproj).exists():
            try:
                from llama_cpp.llama_chat_format import Llava15ChatHandler
                handler = Llava15ChatHandler(clip_model_path=mmproj, verbose=False)
                self.llm_vision = Llama(
                    model_path=model_path,
                    n_ctx=n_ctx,
                    n_gpu_layers=n_gpu_layers,
                    chat_handler=handler,
                    verbose=False
                )
                logging.info(f"Vision model loaded with mmproj {mmproj}")
            except Exception as e:
                logging.warning(f"Vision model failed to load, image inputs will be text-only: {e}")
        else:
            logging.warning(
                f"mmproj file not found at {mmproj}. "
                "Image inputs will be described as text. "
                "Download the mmproj GGUF alongside the base model for full multimodal support."
            )

    def _log_inference(self, prompt: str, output: str, duration: float):
        logging.info(
            f"Input length: {len(prompt)} chars | "
            f"Output length: {len(output)} chars | "
            f"Duration: {duration:.2f}s"
        )

    def generate(self, prompt: str, max_tokens: int = MAX_TOKENS, temperature: float = 0.1) -> str:
        """Pure text generation. Temperature fixed at 0.1 for clinical consistency."""
        if not self.llm:
            return ""

        start = time.time()
        try:
            response = self.llm.create_chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as e:
            logging.warning(f"generate decode error: {e}")
            return ""
        output = response["choices"][0]["message"]["content"]
        self._log_inference(prompt, output, time.time() - start)
        return output

    def _encode_image(self, image_path: str) -> str:
        """Letterbox-resize to 336×336 and return base64 PNG via image_processor."""
        from vision.image_processor import load_and_encode
        return load_and_encode(image_path)

    def generate_with_image(self, prompt: str, image_path: str, max_tokens: int = MAX_TOKENS) -> str:
        """
        Multimodal generation combining text prompt and an image.

        If the mmproj file is present, uses LlavaImageData for true vision input.
        Otherwise falls back to a text description so the pipeline never hard-crashes.
        """
        start = time.time()

        if self.llm_vision:
            # True multimodal path — llama-cpp-python LlavaImageData
            try:
                from llama_cpp import LlavaImageData
                base64_img = self._encode_image(image_path)
                image_data = LlavaImageData(data=base64_img, id=1)

                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}},
                            {"type": "text", "text": prompt}
                        ]
                    }
                ]
                response = self.llm_vision.create_chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0.1
                )
                output = response["choices"][0]["message"]["content"]
                self._log_inference(f"MULTIMODAL:{prompt}", output, time.time() - start)
                return output
            except Exception as e:
                logging.warning(f"Vision inference failed, falling back to text-only: {e}")

        # Fallback: describe the image presence in the prompt so the text model
        # still reasons about it symbolically (used when mmproj is unavailable)
        fallback_prompt = (
            f"{prompt}\n\n"
            f"[A photo of the patient's symptoms was provided at: {image_path}. "
            "Assess based on the symptom description above and the known visual signs "
            "of maternal danger (oedema, pallor, jaundice, fundal height).]"
        )
        output = self.generate(fallback_prompt, max_tokens=max_tokens)
        self._log_inference(f"VISION_FALLBACK:{prompt}", output, time.time() - start)
        return output

    def call_raw(self, system_prompt: str, user_prompt: str, max_tokens: int = MAX_TOKENS, temperature: float = 0.1) -> str:
        """
        Pure-LLM passthrough: send system + user messages with NO tool schema
        injection and return the raw string response.

        Used by evaluate_model.py to measure the fine-tune's behaviour in isolation,
        without the rule-based safety-net in TriageEngine merging the risk upward.
        """
        if not self.llm:
            return ""

        start = time.time()
        response = self.llm.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        output = response["choices"][0]["message"]["content"]
        self._log_inference(f"RAW:{user_prompt}", output, time.time() - start)
        return output

    def _format_tool_prompt(self, prompt: str, tools: List[Dict]) -> str:
        """Inject JSON tool schemas into the system prompt for Gemma 4 function calling."""
        tool_schemas = json.dumps(tools, indent=2)
        system_instruction = (
            "You have access to the following tools. "
            "Return ONLY a JSON object representing the tool call when a tool is needed.\n\n"
            f"Tools:\n{tool_schemas}\n\n"
            "User Input:\n"
        )
        return system_instruction + prompt

    def _build_extraction_prompt(self, raw_text: str) -> str:
        """
        Build a single-turn extraction prompt for Gemma 4.

        Three deliberate choices:
          1. NO system role — Gemma's official chat template drops/merges system
             messages, so the instruction is moved into the user turn.
          2. Framed as 'symptom extraction' (a parsing task) — not 'triage' or
             'medical advice', which trips Gemma 4's safety training and
             produces conversational refusals.
          3. Two few-shot exemplars lock the output format to a single JSON
             object on one line, eliminating prose/markdown contamination.
        """
        return (
            "You are a symptom extraction parser. Convert each input sentence "
            "into a JSON object that lists the symptoms mentioned and the "
            "numeric vitals mentioned. Output ONE JSON object on ONE line. "
            "Output nothing else.\n\n"
            "Example 1\n"
            "Input: patient has severe headache and blurred vision\n"
            'Output: {"name":"assess_danger_signs","arguments":{"symptoms":["severe headache","blurred vision"],"vitals":{}}}\n\n'
            "Example 2\n"
            "Input: 28 weeks pregnant, blood pressure 150 over 100, swollen face\n"
            'Output: {"name":"assess_danger_signs","arguments":{"symptoms":["swollen face"],"vitals":{"bp_sys":150,"bp_dia":100}}}\n\n'
            "Example 3\n"
            "Input: feeling tired with mild nausea\n"
            'Output: {"name":"assess_danger_signs","arguments":{"symptoms":["fatigue","mild nausea"],"vitals":{}}}\n\n'
            f"Input: {raw_text.strip()}\n"
            "Output:"
        )

    @staticmethod
    def _parse_tool_output(output: str) -> Optional[Dict]:
        """Parse tool call from model output.

        Handles all known Gemma 4 output formats:
          A. Markdown ```json block
          B. {"tool_calls": [{...}]} wrapper (Unsloth Studio fine-tune)
          C. {"function":..., "parameters":...} alias keys
          D. {"name":..., "arguments":...} canonical form
          E. <|tool_call>call:FUNC{...}<tool_call|> native Gemma 4 format
          F. <|channel>thought ... thinking token prefix (strip before parsing)
        """
        import re as _re

        # ── Strip special/stop tokens that contaminate output ────────────────
        for tok in ('<eos>', '<end_of_turn>', '<|end_of_turn|>', '<bos>'):
            output = output.replace(tok, ' ')

        # ── Strip thinking tokens (<|channel>thought ... <|channel>response) ──
        if '<|channel>' in output:
            parts = output.split('<|channel>')
            for part in reversed(parts):
                tag_end = part.find('\n')
                tag = part[:tag_end].strip() if tag_end != -1 else part.strip()
                if tag not in ('thought',):
                    output = part[tag_end:].strip() if tag_end != -1 else part
                    break

        clean = output.strip()

        def _repair_json(s: str) -> str:
            """Add missing closing brackets/braces for truncated JSON."""
            # Count unclosed structures
            depth_brace   = s.count('{') - s.count('}')
            depth_bracket = s.count('[') - s.count(']')
            # Close any open string if the count of quotes is odd
            if s.count('"') % 2 == 1:
                s += '"'
            s += ']' * max(0, depth_bracket)
            s += '}' * max(0, depth_brace)
            return s

        # ── A. Markdown JSON block ────────────────────────────────────────────
        if clean.startswith("```json"):
            clean = clean[7:].rsplit("```", 1)[0].strip()
        elif clean.startswith("```"):
            clean = clean[3:].rsplit("```", 1)[0].strip()

        def _normalise(d) -> Optional[Dict]:
            """Normalise various key aliases into {name, arguments} form."""
            # Unwrap top-level list: [{...}]
            if isinstance(d, list):
                d = d[0] if d else None
            if not isinstance(d, dict):
                return None
            # Unwrap {"tool_calls": [{...}]} wrapper (plural)
            if "tool_calls" in d and isinstance(d["tool_calls"], list) and d["tool_calls"]:
                d = d["tool_calls"][0]
            # Unwrap {"tool_call": {...}} (singular)
            if "tool_call" in d and isinstance(d["tool_call"], dict):
                d = d["tool_call"]
            # Normalise key aliases
            name = d.get("name") or d.get("function")
            args = d.get("arguments") or d.get("parameters") or d.get("args") or {}
            if not name:
                return None
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            # Fix symptooms typo the model consistently produces
            if isinstance(args, dict) and "symptooms" in args and "symptoms" not in args:
                args["symptoms"] = args.pop("symptooms")
            return {"name": name, "arguments": args}

        try:
            parsed = json.loads(clean)
            result = _normalise(parsed)
            if result:
                return result
        except json.JSONDecodeError:
            pass

        # Retry with repaired JSON (handles truncated output missing closing braces)
        try:
            parsed = json.loads(_repair_json(clean))
            result = _normalise(parsed)
            if result:
                return result
        except json.JSONDecodeError:
            pass

        # ── B. Gemma 4 native <|tool_call>call:FUNC{...}<tool_call|> ─────────
        if '<|tool_call>' in output:
            start = output.find('<|tool_call>') + len('<|tool_call>')
            end   = output.find('<tool_call|>', start)
            call_str = output[start:end] if end != -1 else output[start:]
            m = _re.match(r'call:\s*(\w+)([\s\S]*)', call_str.strip())
            if m:
                func_name = m.group(1)
                args_str  = m.group(2).strip()
                args_str  = args_str.replace('<|"|>', '"').replace("<|'|>", "'")
                args_str  = _re.sub(r'(?<!")(\b[a-zA-Z_]\w*\b)(?=\s*:)', r'"\1"', args_str)
                for candidate in (args_str, _repair_json(args_str)):
                    try:
                        raw = json.loads(candidate)
                        if "symptooms" in raw and "symptoms" not in raw:
                            raw["symptoms"] = raw.pop("symptooms")
                        return {"name": func_name, "arguments": raw}
                    except json.JSONDecodeError:
                        pass

        # ── C. Any JSON object containing a function name anywhere in output ──
        for pattern in [
            r'\{[^{}]*"tool_calls"[^{}]*\[[^]]*\][^{}]*\}',   # tool_calls wrapper
            r'\{[^{}]*"name"[^{}]*"arguments"[^{}]*\}',        # canonical
            r'\{[^{}]*"function"[^{}]*"parameters"[^{}]*\}',   # alias keys
        ]:
            m = _re.search(pattern, output, _re.DOTALL)
            if m:
                for candidate in (m.group(0), _repair_json(m.group(0))):
                    try:
                        result = _normalise(json.loads(candidate))
                        if result:
                            return result
                    except (json.JSONDecodeError, ValueError):
                        pass

        return None

    def call_with_tools(self, prompt: str, tools: List[Dict], system: str = "", max_tokens: int = MAX_TOKENS) -> Optional[Dict]:
        """
        Extract structured danger-sign data from free-text using Gemma 4.

        Uses a raw text completion (not chat completion) with a few-shot
        extraction prompt. This sidesteps two issues:
          - llama-cpp-python's "gemma" chat_format mangles system roles for
            Gemma 4 (different chat tokens than Gemma 1/2).
          - Medical-advice framing triggers Gemma 4's safety training, which
            produces conversational refusals instead of JSON.

        Returns None on failure so the caller can fall back to rule-based
        classification (see triage_engine.run_triage).
        """
        if not self.llm:
            return None

        full_prompt = self._build_extraction_prompt(prompt)

        try:
            response = self.llm(
                full_prompt,
                max_tokens=128,            # one JSON line — never need more
                temperature=0.0,           # deterministic extraction
                stop=["\n", "Input:", "Example"],
            )
            output = response["choices"][0]["text"]
        except Exception as e:
            logging.warning(f"Tool call decode error: {e}")
            return None

        self._log_inference(f"TOOL:{prompt}", output, 0)
        result = self._parse_tool_output(output)
        if result:
            return result
        logging.warning(f"Tool call parse failed (raw output): {output[:200]}")
        return None
