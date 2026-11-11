"""Phase 1: Cubase再生音のリアルタイム取得確認。

WindowsのWASAPI経由でLoopback入力を取得し、Peak / RMSを表示する。
ASIOドライバーを直接読むのではなく、Windows側に公開された入力を使う。
"""

from __future__ import annotations

import soundcard as sc
import numpy as np

SAMPLE_RATE = 48000
BLOCK_SIZE = 48000


def list_devices() -> list:
    return list(sc.all_microphones(include_loopback=True))


def select_device_by_name(device_name: str):
    devices = [
        mic
        for mic in list_devices()
        if device_name.lower() in mic.name.lower()
    ]
    if len(devices) != 1:
        raise RuntimeError(
            f"Expected one matching device, found {len(devices)}"
        )
    return devices[0]


def main() -> None:
    print("Available microphones:")
    for mic in list_devices():
        print(mic.name, mic.id, "loopback:", mic.isloopback)

    device_name = input("Input device name (partial match): ").strip()
    mic = select_device_by_name(device_name)
    print("Capturing:", mic.name)

    with mic.recorder(samplerate=SAMPLE_RATE, channels=2) as recorder:
        while True:
            audio = recorder.record(numframes=BLOCK_SIZE)

            peak = np.max(np.abs(audio))
            rms = np.sqrt(np.mean(audio**2))

            peak_db = 20 * np.log10(max(peak, 1e-12))
            rms_db = 20 * np.log10(max(rms, 1e-12))

            print(f"Peak: {peak_db:.1f} dBFS, RMS: {rms_db:.1f} dBFS")


if __name__ == "__main__":
    main()
