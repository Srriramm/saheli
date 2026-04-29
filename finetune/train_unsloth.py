"""
train_unsloth.py — Saheli Fine-Tuning with Unsloth (Gemma 4 E4B)
Kaggle T4 GPU / Google Colab.

Loads the hybrid-format dataset produced by finetune/prepare_dataset.py.
Each training conversation teaches the model to output:
  ```json
  {"name": "assess_danger_signs", "arguments": {...}}
  ```
  RED/YELLOW/GREEN. <plain-language reason>

This matches the production inference path (core/triage_engine.py → call_with_tools).

References:
  https://unsloth.ai/docs/models/gemma-4/train
"""

import os
import sys
import gc
import re
import torch

# ── GPU check ────────────────────────────────────────────────────────────────
if not torch.cuda.is_available():
    print("=" * 60)
    print("  ERROR: No GPU detected.")
    print("  Kaggle: Settings → Accelerator → GPU T4 x2")
    print("  Colab:  Runtime → Change runtime type → T4 GPU")
    print("=" * 60)
    sys.exit(1)

os.environ["PYTORCH_CUDA_ALLOC_CONF"]    = "expandable_segments:True"
os.environ["UNSLOTH_DISABLE_STATISTICS"] = "1"
os.environ.setdefault("TORCH_COMPILE_DISABLE",   "1")
os.environ.setdefault("UNSLOTH_COMPILE_DISABLE", "1")

gpu_name = torch.cuda.get_device_name(0)
gpu_vram = torch.cuda.get_device_properties(0).total_memory / 1e9
print(f"GPU  : {gpu_name}")
print(f"VRAM : {gpu_vram:.1f} GB")

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_MODEL     = os.environ.get("HF_MODEL_ID", "unsloth/gemma-4-E4B-it")
MAX_SEQ_LENGTH = int(os.environ.get("MAX_SEQ_LENGTH", "1024"))  # hybrid output is longer
DATASET_PATH   = os.environ.get("DATASET_PATH", "./finetune/datasets/saheli_anc_dataset")

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/kaggle/working/outputs")
MODEL_OUT  = os.environ.get("MODEL_OUT",  "/kaggle/working/models/saheli-gemma4-e4b")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODEL_OUT,  exist_ok=True)

# ── Load dataset prepared by finetune/prepare_dataset.py ─────────────────────
from datasets import load_from_disk

if not os.path.isdir(DATASET_PATH):
    print(f"ERROR: dataset not found at {DATASET_PATH}")
    print("Run `python finetune/prepare_dataset.py` first.")
    sys.exit(1)

dataset = load_from_disk(DATASET_PATH)
print(f"Train: {len(dataset['train'])}  Val: {len(dataset['validation'])}  Test: {len(dataset['test'])}")

# ── Load Gemma 4 with Unsloth FastModel ───────────────────────────────────────
print(f"\nLoading {BASE_MODEL} with Unsloth FastModel...")

from unsloth import FastModel
from unsloth.chat_templates import get_chat_template, train_on_responses_only


def clear_cuda():
    gc.collect()
    torch.cuda.empty_cache()


clear_cuda()

model, tokenizer = FastModel.from_pretrained(
    model_name      = BASE_MODEL,
    max_seq_length  = MAX_SEQ_LENGTH,
    dtype           = None,       # auto-detect (bfloat16 on A100, float16 on T4)
    load_in_4bit    = True,
    full_finetuning = False,
)

free_vram = torch.cuda.mem_get_info()[0] / 1e9
print(f"Free VRAM after model load: {free_vram:.2f} GB")

# ── LoRA adapters ─────────────────────────────────────────────────────────────
# r=16, alpha=32 per the Saheli spec — larger capacity than Unsloth's default
# because the clinical domain has many paraphrases and vitals patterns to learn.
model = FastModel.get_peft_model(
    model,
    finetune_vision_layers     = False,
    finetune_language_layers   = True,
    finetune_attention_modules = True,
    finetune_mlp_modules       = True,
    r                          = 16,
    lora_alpha                 = 32,
    lora_dropout               = 0,
    bias                       = "none",
    use_gradient_checkpointing = "unsloth",
    random_state               = 3407,
)
print(model.print_trainable_parameters())

# ── Apply Gemma 4 chat template ───────────────────────────────────────────────
tokenizer = get_chat_template(
    tokenizer,
    chat_template = "gemma-4-thinking",
)


def format_conversations(examples):
    texts = [
        tokenizer.apply_chat_template(
            convo,
            tokenize              = False,
            add_generation_prompt = False,
        ).removeprefix("<bos>")
        for convo in examples["conversations"]
    ]
    return {"text": texts}


dataset_train_fmt = dataset["train"].map(format_conversations, batched=True)
dataset_val_fmt   = dataset["validation"].map(format_conversations, batched=True)

# ── Non-negotiable separator check ───────────────────────────────────────────
# If the printed SAMPLE does NOT contain <start_of_turn>user / <start_of_turn>model,
# the separator constants below are wrong and train_on_responses_only will
# silently fail to mask the prompt. Inspect the output before training starts.
print("\n" + "=" * 60)
print("CHECK FORMATTED SAMPLE (look for <start_of_turn>user / model):")
print("=" * 60)
print(dataset_train_fmt[0]["text"][:600])
print("=" * 60)

USER_TURN_SEP  = "<|turn>user\n"
MODEL_TURN_SEP = "<|turn>model\n"

if USER_TURN_SEP not in dataset_train_fmt[0]["text"]:
    print("\nERROR: expected user-turn separator not found in formatted sample.")
    print("The 'gemma-4-thinking' chat template may have changed. Aborting to avoid")
    print("silently training with unmasked prompts (which wastes GPU hours).")
    match = re.search(r"<[^>]*user[^>]*>\n?", dataset_train_fmt[0]["text"])
    if match:
        print(f"Auto-detected user marker: {match.group()!r}")
    sys.exit(1)

if MODEL_TURN_SEP not in dataset_train_fmt[0]["text"]:
    print("\nERROR: expected model-turn separator not found. Aborting.")
    sys.exit(1)

print(f"OK: separators present — masking will work. user={USER_TURN_SEP!r} model={MODEL_TURN_SEP!r}")

# ── SFTTrainer ────────────────────────────────────────────────────────────────
from trl import SFTTrainer, SFTConfig

trainer = SFTTrainer(
    model         = model,
    tokenizer     = tokenizer,
    train_dataset = dataset_train_fmt,
    eval_dataset  = dataset_val_fmt,
    args = SFTConfig(
        dataset_text_field          = "text",
        per_device_train_batch_size = 1,
        gradient_accumulation_steps = 4,        # effective batch = 4
        warmup_steps                = 50,        # ~5% of 900 total steps (1200 train / batch-4 / 3 epochs)
        num_train_epochs            = 3,        # replaces max_steps=60
        learning_rate               = 2e-4,
        logging_steps               = 10,
        eval_strategy               = "steps",
        eval_steps                  = 50,
        save_strategy               = "no",
        optim                       = "adamw_8bit",
        weight_decay                = 0.01,
        lr_scheduler_type           = "linear",
        seed                        = 3407,
        output_dir                  = OUTPUT_DIR,
        report_to                   = "none",
        fp16                        = not torch.cuda.is_bf16_supported(),
        bf16                        = torch.cuda.is_bf16_supported(),
        dataloader_pin_memory       = False,
        dataloader_num_workers      = 0,
        max_seq_length              = MAX_SEQ_LENGTH,
    ),
)

# Mask loss on the instruction part — only train on model responses
trainer = train_on_responses_only(
    trainer,
    instruction_part = USER_TURN_SEP,
    response_part    = MODEL_TURN_SEP,
)

# ── Train ─────────────────────────────────────────────────────────────────────
print("\nStarting training (3 epochs)...")
trainer_stats = trainer.train()
final_loss = trainer_stats.training_loss
print(f"\nTraining complete!")
print(f"  Loss          : {final_loss:.4f}")
print(f"  Runtime       : {trainer_stats.metrics.get('train_runtime', 0):.0f}s")

if final_loss > 1.2:
    print(f"\nWARNING: final training loss {final_loss:.4f} is high.")
    print("Likely causes: (a) response-mask separators are wrong, check SAMPLE output above;")
    print("              (b) dataset not loaded correctly.")

# ── Save LoRA adapter weights ─────────────────────────────────────────────────
model.save_pretrained(MODEL_OUT)
tokenizer.save_pretrained(MODEL_OUT)
print(f"\nSaved adapter weights to: {MODEL_OUT}")

# ── Export to GGUF for llama.cpp ──────────────────────────────────────────────
# On Kaggle's 20 GB working quota the merge-to-16bit step overflows disk.
# Set SKIP_GGUF=1 to save only the LoRA adapter (small, ~150 MB) and do the
# GGUF conversion in a second session with more disk headroom.
SKIP_GGUF = os.environ.get("SKIP_GGUF", "0") == "1"

if SKIP_GGUF:
    print("\nSKIP_GGUF=1 set — skipping GGUF export. Adapter weights are sufficient")
    print("for HuggingFace upload. Convert to GGUF in a separate session.")
else:
    print("\nExporting GGUF Q4_K_M for llama.cpp (offline inference)...")
    try:
        model.save_pretrained_gguf(
            MODEL_OUT,
            tokenizer,
            quantization_method = "q4_k_m",
        )
        print(f"GGUF saved to: {MODEL_OUT}")
    except Exception as e:
        print(f"GGUF export failed: {e}")
        print("Adapter weights are saved — run llama.cpp convert manually if needed.")

# ── Sanity check: 5 cases covering RED / YELLOW / GREEN, vitals, paraphrase ──
print("\nRunning sanity check on fine-tuned model...")
FastModel.for_inference(model)

SANITY_CASES = [
    # Single-symptom RED
    ("Patient is 32 weeks pregnant and has severe headache and blurred vision. BP 150/100.", "RED"),
    # No foetal movement RED
    ("28-week patient, baby has not moved all day.",                                         "RED"),
    # Multi-symptom RED — eclampsia
    ("Patient is 35 weeks pregnant. She had fits last night and was unconscious. BP 172/114.", "RED"),
    # Multi-symptom YELLOW — early pre-eclampsia
    ("33-week patient: swollen face and hands, headache for two days. BP 143/91.",           "YELLOW"),
    # Single-symptom YELLOW — anaemia
    ("ASHA visit: 24w, feeling very weak, haemoglobin 6.5.",                                 "YELLOW"),
    # Confuser GREEN — mild headache, normal BP
    ("Patient is 20 weeks pregnant with a mild headache. BP is normal.",                     "GREEN"),
    # Hindi code-mix RED
    ("32 hafte ki patient ko bahut tez sar dard hai aur aankhein dhundhli ho gayi hain. BP 158/106.", "RED"),
    # GREEN — routine
    ("16-week patient, some nausea in the mornings.",                                        "GREEN"),
]

SYSTEM_PROMPT_SANITY = (
    "You are Saheli, a maternal health assistant for ASHA workers. "
    "Given the patient's symptoms and vitals, output a JSON tool call to "
    "assess_danger_signs followed by a short RED/YELLOW/GREEN recommendation "
    "in plain language. Use WHO Antenatal Care guidelines."
)

def _content(text):
    # transformers 5.x requires content as list-of-dicts for Gemma 4 multimodal template
    return [{"type": "text", "text": text}]

correct = 0
for user_msg, expected in SANITY_CASES:
    messages = [
        {"role": "system", "content": _content(SYSTEM_PROMPT_SANITY)},
        {"role": "user",   "content": _content(user_msg)},
    ]
    inputs = tokenizer.apply_chat_template(
        messages,
        tokenize              = True,
        add_generation_prompt = True,
        return_tensors        = "pt",
    ).to("cuda")
    with torch.no_grad():
        outputs = model.generate(
            input_ids      = inputs,
            max_new_tokens = 200,
            temperature    = 0.1,
            do_sample      = True,
        )
    response = tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
    match = re.search(r"\b(RED|YELLOW|GREEN)\b", response.upper())
    predicted = match.group(1) if match else "?"
    ok = predicted == expected
    correct += int(ok)
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] expected {expected:<6} got {predicted:<6} | {user_msg[:70]}")

print(f"\nSanity check: {correct}/{len(SANITY_CASES)} correct")
if correct < 4:
    print("Sanity check weak — re-check dataset and mask separators before trusting GGUF.")

print(f"\nNext: Upload {MODEL_OUT} to HuggingFace as saheli-gemma4-e4b")
print("Then run finetune/evaluate_model.py with the fine-tuned GGUF.")
