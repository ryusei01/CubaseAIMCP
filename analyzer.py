"""Phase 2: ステレオミックスの簡易音響解析。"""

from __future__ import annotations

import numpy as np
import pyloudnorm as pyln
from scipy.signal import welch

BANDS = {
    "sub": (20, 60),
    "bass": (60, 250),
    "low_mid": (250, 500),
    "mid": (500, 2000),
    "presence": (2000, 6000),
    "high": (6000, 20000),
}


def analyze_audio(audio, sample_rate: int = 48000) -> dict:
    """ステレオPCMから基本的なミックス指標を返す。

    Peakはサンプルピーク（True Peakではない）。
    帯域エネルギーは簡易Welch法によるもの。
    """
    audio = np.asarray(audio, dtype=np.float64)

    if audio.ndim != 2 or audio.shape[1] != 2:
        raise ValueError("Stereo audio is required")

    if len(audio) < sample_rate:
        raise ValueError("At least one second is required")

    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio**2)))

    meter = pyln.Meter(sample_rate)
    lufs = meter.integrated_loudness(audio)

    mono = np.mean(audio, axis=1)
    frequencies, psd = welch(mono, fs=sample_rate, nperseg=8192)

    band_energy = {}
    for name, (low, high) in BANDS.items():
        mask = (frequencies >= low) & (frequencies < high)
        if not np.any(mask):
            band_energy[name] = -100.0
            continue
        power = np.trapezoid(psd[mask], frequencies[mask])
        band_energy[name] = round(float(10 * np.log10(max(power, 1e-20))), 2)

    left = audio[:, 0]
    right = audio[:, 1]
    if np.std(left) > 1e-8 and np.std(right) > 1e-8:
        correlation = float(np.corrcoef(left, right)[0, 1])
    else:
        correlation = None

    return {
        "lufs": round(float(lufs), 2),
        "peak_dbfs": round(float(20 * np.log10(max(peak, 1e-12))), 2),
        "rms_dbfs": round(float(20 * np.log10(max(rms, 1e-12))), 2),
        "stereo_correlation": (
            None if correlation is None else round(correlation, 3)
        ),
        "band_energy_db": band_energy,
    }
