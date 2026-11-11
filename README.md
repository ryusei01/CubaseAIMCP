# Cubase AI Mix Advisor

Cubase 14 Pro のマスター音をリアルタイム解析し、GPT がミックス改善案を提案するシステムです。

UR22 はハードウェアループバック非対応のため、**VST3 Audio Tap** で Stereo Out から直接取得します。  
Cubase 操作・ファイル解析の補助に **yoka-cubase-mcp** を併用できます。

## 役割分担

| 層 | 役割 |
|----|------|
| VST3 Audio Tap | Stereo Out の音声を共有メモリへコピー（音は変えない） |
| Python (`tap_reader` / `main_tap`) | 共有メモリ読取 → LUFS/FFT/相関 → GPT助言 |
| yoka-cubase-mcp | MCU経由のCubase制御、Nickerによるファイル解析・助言 |

ASIO ドライバー（Yamaha Steinberg USB ASIO）は変更しません。

## いまの前提（確認済み）

- ASIO: Yamaha Steinberg USB ASIO
- IF: Steinberg UR22（Loopback入力なし）
- WASAPI Loopback では Cubase 音が取れない → VST3 方式が本命

## セットアップ

### 1. Python（このリポジトリ）

```powershell
cd d:\document\program\project\Cubase
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. VST3 Audio Tap のビルドと導入

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_vst3.ps1
```

導入先:

- `%LOCALAPPDATA%\Programs\Common\VST3\CubaseAiAudioTap.vst3`
- `C:\Program Files\Common Files\VST3\CubaseAiAudioTap.vst3`

Cubase 側:

1. Cubase を再起動（またはプラグイン再スキャン）
2. `F3` で MixConsole
3. 右端 **Stereo Out** の Insert に **Cubase AI Audio Tap** を追加
4. Ozone 等の後段を解析したい場合は、その後ろに配置

### 3. 動作確認

```powershell
python tap_reader.py
```

再生中に Peak/RMS が動けば成功です。

GPT 助言付き:

```powershell
$env:OPENAI_API_KEY="YOUR_API_KEY"
python main_tap.py
```

## yoka-cubase-mcp（任意・推奨）

クローン済み: `d:\document\program\project\yoka-cubase-mcp`  
Cursor MCP 登録済み: `C:\Users\konan\.cursor\mcp.json`  
Selftest: 77/77 OK / Doctor: MCP 64 tools OK

### まだ必要な手動手順

1. **loopMIDI** を起動（インストール済）
2. 次の仮想ポートを作成（名前は完全一致）
   - `MACKIE_FROM_CUBASE`
   - `MACKIE_TO_CUBASE`
   - `AI_INPUT`
3. Cubase「スタジオ」→「スタジオ設定」→ Mackie Control を追加  
   - 入力: `MACKIE_TO_CUBASE`  
   - 出力: `MACKIE_FROM_CUBASE`
4. Cursor を再起動して MCP 接続を確認

詳細: [yoka-cubase-mcp INSTALL](https://github.com/yokadeeds-dev/yoka-cubase-mcp/blob/main/INSTALL.md)

## 主なファイル

| ファイル | 内容 |
|---------|------|
| `vst3_audio_tap/` | Audio Tap VST3 ソース |
| `tap_reader.py` | 共有メモリ読取メーター |
| `main_tap.py` | 解析 + GPT（VST3経路） |
| `analyzer.py` / `advisor.py` | 音響解析 / GPT助言 |
| `shared/tap_protocol.md` | 共有メモリ仕様 |
| `capture.py` / `main.py` | WASAPI経路（UR22では非推奨） |

## 開発フェーズ

| Phase | 内容 | 状態 |
|------|------|------|
| 1 | リアルタイム取得 | VST3 実装・導入済 |
| 2 | LUFS / 周波数 / ステレオ | 実装済 |
| 3 | GPT 改善案 | 実装済 (`main_tap.py`) |
| 4 | リファレンス比較 | 未着手 |
| 5 | 各楽器個別解析 | 未着手（複数 Tap 挿しで拡張可） |
| 6 | Cubase パラメーター連携 | yoka-cubase-mcp で着手可 |
