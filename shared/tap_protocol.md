# Cubase AI Advisor — Audio Tap Protocol

VST3 Audio Tap と Python 解析プロセス間の共有メモリ仕様。

## Shared memory name

```
CubaseAiAdvisorTap
```

Windows `CreateFileMapping` / Python `mmap.mmap(..., tagname=...)` で共有する。

## Layout

| Offset | Type | Field | Description |
|--------|------|-------|-------------|
| 0 | uint32 | magic | `0x54414243` (`CBAT`) |
| 4 | uint32 | version | `1` |
| 8 | uint32 | sample_rate | 例: 48000 |
| 12 | uint32 | channels | 常に `2` |
| 16 | uint32 | capacity_frames | リング容量（既定 30秒分） |
| 20 | uint32 | bytes_per_frame | `channels * sizeof(float32)` |
| 24 | uint64 | write_index | 累計書き込みフレーム数（単調増加） |
| 32 | uint32 | active | 処理中なら `1` |
| 36 | uint32 | reserved | 0 |
| 40 | float32[] | samples | interleaved L,R … 長さ `capacity_frames * channels` |

総サイズ = `40 + capacity_frames * channels * 4`

## Ring buffer

- 書き込み位置: `write_index % capacity_frames`
- 読み手は前回の `write_index` から最新までを読む
- オーバーラン時は古いデータを捨て、最新側を優先

## 注意

- VST3 音声スレッドではネットワーク・malloc・ロック待ちをしない
- 解析・GPT 呼び出しは Python 側の別スレッドで行う
