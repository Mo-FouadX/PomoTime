"""
Audio synthesis module for PomoTime.

Generates soft, bell-like notification chimes in pure Python (math, wave, struct)
without any external multimedia assets or QtMultimedia dependency.
"""

import math
import os
import platform
import shutil
import struct
import subprocess
import tempfile
import wave

# Audio files cache
_audio_cache = {}


def generate_chime(notes, filename, volume=1.0, sample_rate=44100):
    """Synthesize a soft, bell-like chime from a musical note sequence.

    Each note is ``(frequency_hz, start_ms, duration_ms, gain)``. Notes are
    mixed together and shaped with a short fade-in, exponential decay and a
    short fade-out, producing a warm marimba/bell tone without clicks or pops.
    """
    if not notes:
        return

    total_ms = max(start_ms + dur_ms for _, start_ms, dur_ms, _ in notes)
    total_samples = max(1, int(sample_rate * total_ms / 1000.0))
    buffer = [0.0] * total_samples

    for freq, start_ms, dur_ms, gain in notes:
        start_sample = int(sample_rate * start_ms / 1000.0)
        note_samples = max(1, int(sample_rate * dur_ms / 1000.0))
        attack = max(1, int(0.006 * sample_rate))          # 6 ms fade-in
        release = max(1, min(int(0.020 * sample_rate), note_samples // 3))

        for i in range(note_samples):
            index = start_sample + i
            if index >= total_samples:
                break

            t = i / sample_rate
            position = i / note_samples

            envelope = math.exp(-4.5 * position)
            if i < attack:
                envelope *= i / attack
            remaining = note_samples - i
            if remaining < release:
                envelope *= remaining / release

            # Bell/marimba voicing: fundamental plus soft harmonics.
            waveform = (
                0.65 * math.sin(2 * math.pi * freq * t)
                + 0.25 * math.sin(2 * math.pi * 2.0 * freq * t)
                + 0.10 * math.sin(2 * math.pi * 3.0 * freq * t)
            )
            buffer[index] += gain * envelope * waveform

    peak = max((abs(sample) for sample in buffer), default=0.0)
    scale = (0.95 / peak) if peak > 0.95 else 1.0
    amplitude = max(0.0, min(1.0, volume)) * scale

    frames = []
    for sample in buffer:
        value = int(32767 * max(-1.0, min(1.0, sample * amplitude)))
        frames.append(struct.pack("<h", value))

    with wave.open(filename, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"".join(frames))


def get_audio_file(sound_key):
    """Get or generate the notification chime WAV file for *sound_key*."""
    cache_key = f"v2_{sound_key}"

    if cache_key not in _audio_cache:
        sound = SOUNDS.get(sound_key)
        if sound and "notes" in sound:
            temp_dir = tempfile.gettempdir()
            filename = os.path.join(temp_dir, f"pomotime_{cache_key}.wav")
            if not os.path.exists(filename):
                generate_chime(sound["notes"], filename)
            _audio_cache[cache_key] = filename

    return _audio_cache.get(cache_key)


def get_player_command(audio_file):
    """Return the native command used to play a WAV file, or None if unavailable."""
    system = platform.system()
    if system == "Linux":
        if shutil.which("paplay"):
            return ["paplay", audio_file]
        if shutil.which("aplay"):
            return ["aplay", "-q", audio_file]
    elif system == "Darwin":
        if shutil.which("afplay"):
            return ["afplay", audio_file]
    return None


# Sound Definitions
# Notification sounds are musical note sequences:
#   (frequency_hz, start_ms, duration_ms, gain)
SOUNDS = {
    # Very soft wood/pop tap for buttons and controls.
    "click": {
        "notes": [(520.0, 0.0, 45.0, 0.20)],
        "dur": 45,
    },
    # Uplifting C5 -> G5 ascending chime.
    "start_focus": {
        "notes": [
            (523.25, 0.0, 260.0, 0.55),
            (783.99, 135.0, 260.0, 0.50),
        ],
        "dur": 400,
    },
    # Warm G5 -> E5 descending chime.
    "start_break": {
        "notes": [
            (783.99, 0.0, 260.0, 0.50),
            (659.25, 135.0, 260.0, 0.55),
        ],
        "dur": 400,
    },
    # Gentle C5 -> E5 -> G5 -> C6 arpeggio, like a modern OS notification.
    "alert": {
        "notes": [
            (523.25, 0.0, 420.0, 0.45),
            (659.25, 110.0, 420.0, 0.42),
            (783.99, 220.0, 420.0, 0.40),
            (1046.50, 330.0, 480.0, 0.35),
        ],
        "dur": 850,
    },
}

__all__ = [
    "generate_chime",
    "get_audio_file",
    "get_player_command",
    "SOUNDS",
    "play_tone",
]


def play_tone(sound_key):
    """Play a soft notification chime using native OS audio playback."""
    sound = SOUNDS.get(sound_key)
    if not sound:
        return

    audio_file = get_audio_file(sound_key)
    if audio_file and os.path.exists(audio_file):
        try:
            if platform.system() == "Windows":
                import winsound

                flags = winsound.SND_FILENAME | winsound.SND_ASYNC  # type: ignore[attr-defined]
                winsound.PlaySound(audio_file, flags)  # type: ignore[attr-defined]
                return

            player = get_player_command(audio_file)
            if player:
                subprocess.Popen(
                    player,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return
        except Exception:
            pass

    # Fallback: a short system beep if WAV playback is unavailable.
    try:
        if platform.system() == "Windows":
            import winsound

            notes = sound.get("notes") or []
            freq = notes[0][0] if notes else sound.get("freq", 800)
            winsound.Beep(int(freq), int(sound.get("dur", 100)))  # type: ignore[attr-defined]
            return
    except Exception:
        pass

    # Final fallback to the terminal bell.
    print("\a", end="", flush=True)
