import pytest
import aiohttp
import dotenv
import tempfile
import os


from src.agent import (
    BloggerAgent,
    WriterAgent,
    StructureAgent,
    PDF2MDAgent,
    Conversation,
)

dotenv.load_dotenv(".env.local")
API_KEY = os.environ.get("GEMINI_API_KEY", "")
assert API_KEY != "", "GEMINI_API_KEY is not set in .env.local"


@pytest.mark.asyncio
async def test_blogger_agent():
    blogger = BloggerAgent(
        api_key=API_KEY,
    )

    pdf2md = PDF2MDAgent()

    pdf_url = "https://arxiv.org/pdf/2309.17400"

    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download PDF: {response.status}")
                temp_pdf.write(await response.read())
        temp_pdf_path = temp_pdf.name
        paper = pdf2md.read_local(temp_pdf_path)

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

    pdf2md = PDF2MDAgent()

    pdf_url = "https://arxiv.org/pdf/2309.17400"

    with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as temp_pdf:
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to download PDF: {response.status}")
                temp_pdf.write(await response.read())
        temp_pdf_path = temp_pdf.name
        paper = pdf2md.read_local(temp_pdf_path)

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
