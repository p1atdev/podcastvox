import json
import aiohttp
import tempfile
from typing import Literal
from pydantic import BaseModel
from markitdown import MarkItDown

import litellm
from litellm.types.utils import ModelResponse

SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
]


class BloggerAgent:
    instructions = [
        {
            "role": "user",
            "content": "与えられる情報について、重要なポイントを踏まえて平易な言葉で解説・紹介する記事を書いてください",
        },
    ]
    model: str = "gemini/gemini-2.5-flash-preview-05-20"
    temperature: float = 1.0
    max_tokens: int = 4096
    thinking_budget: int = 1024
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def task(self, information: str) -> str:
        messages = self.instructions.copy()
        messages.append({"role": "user", "content": information})

        res = await litellm.acompletion(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
            thinking={"type": "enabled", "budget_tokens": self.thinking_budget},
            safety_settings=SAFETY_SETTINGS,
        )
        assert isinstance(res, ModelResponse)

        blog = res.choices[0].message.content
        assert isinstance(blog, str)

        return blog


class WriterAgent:
    instructions = [
        {
            "role": "user",
            "content": """与えられる情報ソースとその解説記事をもとに、コンテンツを紹介する Podcast の会話を作成してください。
Podcast では、二人の人物が交互に会話をします。

# 登場人物
- スピーカー: コンテンツ紹介をリードする人で、主にこの人物が解説を行う
- サポーター: スピーカーの説明を聞き、うなづいたり、さらに質問を投げかけることで、理解を助ける。

# 構成
1. イントロ: まず、スピーカーとサポーターが何について話すのか、挨拶を交えながら会話します。自己紹介は省略する。
2. 解説: 前提知識の確認をしながら、内容を解説していきます
3. アウトロ: 今後の展望を交えながら締めくくります

---
このような内容になるような Podcast の脚本を作成してください。
""".strip(),
        },
    ]
    model: str = "gemini/gemini-2.5-flash-preview-05-20"
    temperature: float = 1.0
    max_tokens: int = 4096
    thinking_budget: int = 1024
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def task(self, information: str, blog: str) -> str:
        messages = self.instructions.copy()
        messages.append(
            {"role": "user", "content": f"# 情報\n{information}\n\n# 解説\n{blog}"}
        )

        res = await litellm.acompletion(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
            thinking={"type": "enabled", "budget_tokens": self.thinking_budget},
            safety_settings=SAFETY_SETTINGS,
        )
        assert isinstance(res, ModelResponse)

        dialogue = res.choices[0].message.content
        assert isinstance(dialogue, str)

        return dialogue


class Dialogue(BaseModel):
    role: Literal["speaker", "supporter"]
    content: str


class Conversation(BaseModel):
    conversation: list[Dialogue]


class StructureAgent:
    instructions = [
        {
            "role": "user",
            "content": """この会話を指定されたスキーマに従った形に変換してください。スピーカーの role は `speaker`、サポーターは `supporter` です。""".strip(),
        },
    ]
    model: str = "gemini/gemini-2.5-flash-preview-05-20"
    temperature: float = 0.1
    max_tokens: int = 12_288
    thinking_budget: int = 0
    api_key: str

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def task(self, dialogue: str) -> Conversation:
        messages = self.instructions.copy()
        messages.append({"role": "user", "content": dialogue})

        res = await litellm.acompletion(
            api_key=self.api_key,
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_completion_tokens=self.max_tokens,
            thinking={"type": "disabled"},
            response_format=Conversation,
            safety_settings=SAFETY_SETTINGS,
        )

        conversation = Conversation.model_validate(
            json.loads(res.choices[0].message.content)
        )

        return conversation
