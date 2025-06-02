import pytest
import dotenv
import os


from src.agent import (
    BloggerAgent,
    WriterAgent,
    StructureAgent,
    Conversation,
)
from src.fetcher import PDFFetcher

dotenv.load_dotenv(".env.local")
API_KEY = os.environ.get("GEMINI_API_KEY", "")
assert API_KEY != "", "GEMINI_API_KEY is not set in .env.local"


@pytest.mark.asyncio
async def test_blogger_agent():
    blogger = BloggerAgent(
        api_key=API_KEY,
    )

    fetcher = PDFFetcher()

    pdf_url = "https://arxiv.org/pdf/2309.17400"
    paper = await fetcher.fetch(pdf_url)

    # print("paper:", paper)

    blog = await blogger.task(paper)
    assert isinstance(blog, str)

    print(blog)

    with open("./dist/blog.md", "w", encoding="utf-8") as f:
        f.write(blog)


@pytest.mark.asyncio
async def test_writer_agent():
    writer = WriterAgent(
        api_key=API_KEY,
    )

    fetcher = PDFFetcher()

    pdf_url = "https://arxiv.org/pdf/2309.17400"
    paper = await fetcher.fetch(pdf_url)

    with open("./dist/blog.md", "r", encoding="utf-8") as f:
        blog = f.read()

    dialogue = await writer.task(paper, blog)
    assert isinstance(dialogue, str)

    with open("./dist/dialogue.md", "w", encoding="utf-8") as f:
        f.write(dialogue)


@pytest.mark.asyncio
async def test_structure_agent():
    structure_agent = StructureAgent(
        api_key=API_KEY,
    )

    with open("./dist/dialogue.md", "r", encoding="utf-8") as f:
        dialogue = f.read()

    conversation = await structure_agent.task(dialogue)
    assert isinstance(conversation, Conversation)

    with open("./dist/conversation2.json", "w", encoding="utf-8") as f:
        f.write(conversation.model_dump_json(indent=2))
