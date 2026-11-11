"""Phase 3: 音響指標をGPTに送り、Cubase向けミックス助言を取得する。"""

from __future__ import annotations

import json
import os

from openai import OpenAI

SYSTEM_PROMPT = """
あなたはプロのミキシングエンジニアです。
Cubase 14 Proを使用するユーザーに助言してください。

入力はステレオミックスの音響測定値です。

ルール:
- 測定値から確実に言えることと推測を区別する
- 楽器ごとの問題を断定しない
- LUFSだけで音質を判断しない
- 必要なら追加のステム解析を提案する
- Cubaseの操作手順を具体的に示す
- EQの周波数、Q、ゲインは試行値として提示する
- 改善案は重要度順に最大3件
- 日本語で簡潔に回答する
"""


def get_advice(
    metrics: dict,
    genre: str = "rock",
    model: str | None = None,
) -> str:
    """解析結果をOpenAI APIへ送り、テキスト助言を返す。"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY が未設定です。"
            " $env:OPENAI_API_KEY=\"YOUR_API_KEY\" を実行してください。"
        )

    client = OpenAI(api_key=api_key)
    selected_model = model or os.getenv("OPENAI_MODEL", "gpt-4.1")

    response = client.responses.create(
        model=selected_model,
        instructions=SYSTEM_PROMPT,
        input=json.dumps(
            {
                "genre": genre,
                "metrics": metrics,
            },
            ensure_ascii=False,
        ),
    )

    return response.output_text
