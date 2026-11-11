"""Phase 1〜3: 音声取得 → 解析 → GPTアドバイスのMVP。

既定では30秒ごとに解析・助言する（費用抑制）。
環境変数:
  OPENAI_API_KEY  必須（GPT助言時）
  OPENAI_MODEL    任意（既定: gpt-4.1）
  ADVICE_INTERVAL 任意（秒、既定: 30）
  GENRE           任意（既定: rock）
"""

from __future__ import annotations

import os
import time
from collections import deque

import numpy as np
import soundcard as sc

from advisor import get_advice
from analyzer import analyze_audio

SAMPLE_RATE = 48000
BLOCK_SECONDS = 1
ANALYSIS_SECONDS = 10


def choose_device():
    devices = list(sc.all_microphones(include_loopback=True))
    if not devices:
        raise RuntimeError(
            "入力デバイスが見つかりません。"
            "Loopback対応IF、または仮想オーディオデバイスを確認してください。"
        )

    print("Available input devices:")
    for index, device in enumerate(devices):
        loopback = " [loopback]" if getattr(device, "isloopback", False) else ""
        print(f"{index}: {device.name}{loopback}")

    device_index = int(input("Device index: "))
    if device_index < 0 or device_index >= len(devices):
        raise RuntimeError("Invalid device index")
    return devices[device_index]


def main() -> None:
    advice_interval = float(os.getenv("ADVICE_INTERVAL", "30"))
    genre = os.getenv("GENRE", "rock")
    enable_ai = bool(os.getenv("OPENAI_API_KEY"))

    device = choose_device()
    print(f"Capturing: {device.name}")
    print(
        f"Buffer={ANALYSIS_SECONDS}s, "
        f"advice every {advice_interval:.0f}s, "
        f"AI={'ON' if enable_ai else 'OFF (metrics only)'}"
    )

    buffer: deque[np.ndarray] = deque(maxlen=ANALYSIS_SECONDS)
    last_analysis = 0.0

    with device.recorder(samplerate=SAMPLE_RATE, channels=2) as recorder:
        while True:
            audio = recorder.record(numframes=SAMPLE_RATE * BLOCK_SECONDS)
            buffer.append(audio.copy())

            if len(buffer) < ANALYSIS_SECONDS:
                filled = len(buffer)
                print(f"Buffering... {filled}/{ANALYSIS_SECONDS}s", end="\r")
                continue

            now = time.monotonic()
            if now - last_analysis < advice_interval:
                continue

            last_analysis = now
            segment = np.concatenate(list(buffer), axis=0)
            metrics = analyze_audio(segment, SAMPLE_RATE)
            print("\nMetrics:", metrics)

            if not enable_ai:
                print("AI skipped: OPENAI_API_KEY not set")
                continue

            try:
                advice = get_advice(metrics, genre=genre)
                print("AI advice:")
                print(advice)
            except Exception as exc:
                print("AI request failed:", exc)


if __name__ == "__main__":
    main()
