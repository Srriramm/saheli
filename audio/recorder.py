import os
import wave
import tempfile
import logging
from typing import Optional

try:
    import pyaudio
except ImportError:
    logging.warning("PyAudio not found. Mic recording will fail.")

def play_feedback_beep() -> None:
    """Short frequency beep to signal 'start speaking' and 'stop speaking'."""
    # Often a simple system beep is sufficient on basic hardware.
    # In Windows, we can use winsound. On Linux/Pi, we can just print \a
    import platform
    if platform.system() == "Windows":
        import winsound
        winsound.Beep(1000, 200) # 1000 Hz for 200 ms
    else:
        print('\a', end='', flush=True)

def record_audio(duration: int = 10, sample_rate: int = 16000) -> Optional[str]:
    """Records raw audio from the default microphone and saves to a temporary .wav file."""
    if 'pyaudio' not in globals():
        return None

    chunk = 1024
    channels = 1
    format = pyaudio.paInt16

    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=format,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk)

        logging.info(f"Start recording for {duration} seconds.")
        play_feedback_beep()
        
        frames = []
        for _ in range(0, int(sample_rate / chunk * duration)):
            data = stream.read(chunk)
            frames.append(data)

        logging.info("Recording finished.")
        play_feedback_beep()
        
        stream.stop_stream()
        stream.close()
        p.terminate()

        # Save to temp file
        temp_dir = tempfile.gettempdir()
        wav_filename = os.path.join(temp_dir, "query_saheli.wav")
        
        wf = wave.open(wav_filename, 'wb')
        wf.setnchannels(channels)
        wf.setsampwidth(p.get_sample_size(format))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))
        wf.close()

        return wav_filename

    except Exception as e:
        logging.error(f"Failed to record audio: {e}")
        return None
