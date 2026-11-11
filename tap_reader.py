"""VST3 Audio Tap 共有メモリからステレオPCMを読む。"""

from __future__ import annotations

import mmap
import struct
import time
from collections import deque

import numpy as np

MAGIC = 0x54414243  # 'CBAT'
HEADER_FMT = "<IIIIIIQII"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
SHM_NAME = "CubaseAiAdvisorTap"
DEFAULT_CAPACITY_FRAMES = 48000 * 30


class TapReader:
    def __init__(self, capacity_frames: int = DEFAULT_CAPACITY_FRAMES):
        self.capacity_frames = capacity_frames
        self.channels = 2
        self.size = HEADER_SIZE + capacity_frames * self.channels * 4
        self._mm: mmap.mmap | None = None
        self._last_write_index = 0

    def connect(self, timeout_sec: float = 30.0) -> None:
        deadline = time.monotonic() + timeout_sec
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                mm = mmap.mmap(-1, self.size, tagname=SHM_NAME)
                magic, version, *_ = struct.unpack_from(HEADER_FMT, mm, 0)
                if magic == MAGIC and version == 1:
                    self._mm = mm
                    self._last_write_index = self.write_index
                    return
                mm.close()
            except Exception as exc:  # noqa: BLE001
                last_error = exc
            time.sleep(0.25)
        raise TimeoutError(
            f"Shared memory '{SHM_NAME}' に接続できません。"
            f" Cubase の Stereo Out に Audio Tap を挿して再生してください。"
            f" last_error={last_error}"
        )

    def close(self) -> None:
        if self._mm is not None:
            self._mm.close()
            self._mm = None

    @property
    def header(self) -> dict:
        assert self._mm is not None
        (
            magic,
            version,
            sample_rate,
            channels,
            capacity_frames,
            bytes_per_frame,
            write_index,
            active,
            reserved,
        ) = struct.unpack_from(HEADER_FMT, self._mm, 0)
        return {
            "magic": magic,
            "version": version,
            "sample_rate": sample_rate,
            "channels": channels,
            "capacity_frames": capacity_frames,
            "bytes_per_frame": bytes_per_frame,
            "write_index": write_index,
            "active": active,
            "reserved": reserved,
        }

    @property
    def write_index(self) -> int:
        assert self._mm is not None
        return struct.unpack_from("<Q", self._mm, 24)[0]

    def read_new_frames(self) -> np.ndarray:
        """前回以降に書き込まれたフレームを (N, 2) float32 で返す。"""
        assert self._mm is not None
        header = self.header
        if header["magic"] != MAGIC:
            raise RuntimeError("Invalid shared memory magic")

        write_index = header["write_index"]
        capacity = header["capacity_frames"]
        channels = header["channels"]
        sample_rate = header["sample_rate"] or 48000

        available = write_index - self._last_write_index
        if available <= 0:
            return np.zeros((0, channels), dtype=np.float32)
        if available > capacity:
            # オーバーラン: 最新 capacity 分だけ残す
            self._last_write_index = write_index - capacity
            available = capacity

        start = self._last_write_index
        end = write_index
        self._last_write_index = write_index

        frames = np.empty((available, channels), dtype=np.float32)
        for i, abs_frame in enumerate(range(start, end)):
            pos = abs_frame % capacity
            offset = HEADER_SIZE + pos * channels * 4
            frames[i] = np.frombuffer(
                self._mm, dtype=np.float32, count=channels, offset=offset
            ).copy()
        return frames

    def read_latest_seconds(self, seconds: float) -> tuple[np.ndarray, int]:
        assert self._mm is not None
        header = self.header
        sample_rate = header["sample_rate"] or 48000
        channels = header["channels"]
        capacity = header["capacity_frames"]
        write_index = header["write_index"]
        n = min(int(seconds * sample_rate), capacity, write_index)
        if n <= 0:
            return np.zeros((0, channels), dtype=np.float32), sample_rate

        out = np.empty((n, channels), dtype=np.float32)
        start = write_index - n
        for i, abs_frame in enumerate(range(start, write_index)):
            pos = abs_frame % capacity
            offset = HEADER_SIZE + pos * channels * 4
            out[i] = np.frombuffer(
                self._mm, dtype=np.float32, count=channels, offset=offset
            ).copy()
        return out, sample_rate


def main() -> None:
    reader = TapReader()
    print(f"Waiting for shared memory '{SHM_NAME}' ...")
    reader.connect()
    print("Connected:", reader.header)

    buffer: deque[np.ndarray] = deque(maxlen=10)
    while True:
        chunk = reader.read_new_frames()
        if len(chunk) == 0:
            time.sleep(0.05)
            continue

        # 約1秒単位で集約表示
        buffer.append(chunk)
        total = sum(len(x) for x in buffer)
        sr = reader.header["sample_rate"] or 48000
        if total < sr:
            continue

        audio = np.concatenate(list(buffer), axis=0)
        buffer.clear()
        peak = float(np.max(np.abs(audio)))
        rms = float(np.sqrt(np.mean(audio**2)))
        peak_db = 20 * np.log10(max(peak, 1e-12))
        rms_db = 20 * np.log10(max(rms, 1e-12))
        active = reader.header["active"]
        print(
            f"active={active}  Peak: {peak_db:7.1f} dBFS  "
            f"RMS: {rms_db:7.1f} dBFS  frames={len(audio)}"
        )


if __name__ == "__main__":
    main()
