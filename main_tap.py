"""VST3 Audio Tap → 解析 → GPT助言。

ASIO / UR22 でも Stereo Out の Insert 経由でマスター音を取得できる。
"""

from __future__ import annotations

import os
import time
from collections import deque

import numpy as np

from advisor import get_advice
from analyzer import analyze_audio
from tap_reader import TapReader

SAMPLE_RATE_FALLBACK = 48000
BLOCK_SECONDS = 1
ANALYSIS_SECONDS = 10


def main() -> None:
    advice_interval = float(os.getenv("ADVICE_INTERVAL", "30"))
    genre = os.getenv("GENRE", "rock")
    enable_ai = bool(os.getenv("OPENAI_API_KEY"))

    reader = TapReader()
    print("Waiting for Cubase AI Audio Tap shared memory...")
    print("Insert 'Cubase AI Audio Tap' on Stereo Out, then play.")
    reader.connect(timeout_sec=120)
    print("Connected:", reader.header)

    buffer: deque[np.ndarray] = deque()
    buffered_frames = 0
    last_analysis = 0.0

    try:
        while True:
            chunk = reader.read_new_frames()
            if len(chunk) == 0:
                time.sleep(0.02)
                continue

            buffer.append(chunk)
            buffered_frames += len(chunk)
            sr = reader.header["sample_rate"] or SAMPLE_RATE_FALLBACK
            target = ANALYSIS_SECONDS * sr

            if buffered_frames < target:
                print(f"Buffering... {buffered_frames}/{target} frames", end="\r")
                continue

            # 直近 ANALYSIS_SECONDS 秒だけ残す
            audio = np.concatenate(list(buffer), axis=0)
            if len(audio) > target:
                audio = audio[-target:]
            buffer.clear()
            buffer.append(audio)
            buffered_frames = len(audio)

            now = time.monotonic()
            if now - last_analysis < advice_interval:
                continue
            last_analysis = now

            metrics = analyze_audio(audio.astype(np.float64), sr)
            print("\nMetrics:", metrics)

            if not enable_ai:
                print("AI skipped: OPENAI_API_KEY not set")
                continue

            try:
                advice = get_advice(metrics, genre=genre)
                print("AI advice:")
                print(advice)
            except Exception as exc:  # noqa: BLE001
                print("AI request failed:", exc)
    finally:
        reader.close()


if __name__ == "__main__":
    main()
