"""音声取得経路の診断。UR22 Loopback / Line / その他を数秒ずつ計測する。"""

from __future__ import annotations

import soundcard as sc
import numpy as np

SAMPLE_RATE = 48000
SECONDS = 3


def measure(mic, seconds: int = SECONDS) -> dict:
    peaks = []
    rmss = []
    with mic.recorder(samplerate=SAMPLE_RATE, channels=2) as recorder:
        for _ in range(seconds):
            audio = recorder.record(numframes=SAMPLE_RATE)
            peak = float(np.max(np.abs(audio)))
            rms = float(np.sqrt(np.mean(audio**2)))
            peaks.append(peak)
            rmss.append(rms)

    peak = max(peaks)
    rms = float(np.mean(rmss))
    return {
        "peak_dbfs": round(20 * np.log10(max(peak, 1e-12)), 1),
        "rms_dbfs": round(20 * np.log10(max(rms, 1e-12)), 1),
        "has_signal": peak > 1e-4,
    }


def main() -> None:
    devices = list(sc.all_microphones(include_loopback=True))
    print("=== Capture diagnose ===\n")
    for index, device in enumerate(devices):
        loopback = getattr(device, "isloopback", False)
        print(f"[{index}] {device.name}  loopback={loopback}")
        try:
            result = measure(device)
            flag = "SIGNAL" if result["has_signal"] else "silent"
            print(
                f"    Peak {result['peak_dbfs']:7.1f} dBFS  "
                f"RMS {result['rms_dbfs']:7.1f} dBFS  ({flag})"
            )
        except Exception as exc:
            print(f"    ERROR: {exc}")
        print()

    print("解釈:")
    print("- Cubase が ASIO 使用中だと、WASAPI Loopback は無音になりやすい")
    print("- UR22（非C）はハードウェアループバック非対応のことが多い")
    print("- 次の手段: 物理配線 / Voicemeeter等 / VST3 Audio Tap")


if __name__ == "__main__":
    main()
