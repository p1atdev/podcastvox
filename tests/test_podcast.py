import pytest
import dotenv
import os

from src.voicevox import VoiceVoxClient
from src.podcast import PodcastStudio

dotenv.load_dotenv(".env.local")
API_KEY = os.environ.get("GEMINI_API_KEY", "")
assert API_KEY != "", "GEMINI_API_KEY is not set in .env.local"


@pytest.mark.asyncio
async def test_record_podcast_pdf():
    pdf_url = "https://arxiv.org/pdf/2309.17400"

    podcast_studio = PodcastStudio(api_key=API_KEY)
    voicevox = VoiceVoxClient("http://localhost:10101")

    _blog, _dialogue, conversation = await podcast_studio.create_conversation(pdf_url)
    podcast_audio = await podcast_studio.record_podcast(
        conversation=conversation,
        voicevox_client=voicevox,
        speaker_id=1937616896,  # にせ ノーマル
        supporter_id=888753760,  # Anneli ノーマル
    )

    assert podcast_audio is not None
    assert isinstance(podcast_audio.wav, bytes)

    with open("./dist/arxiv_draft_blog.md", "wb") as f:
        f.write(_blog.encode("utf-8"))

    with open("./dist/arxiv_draft_dialogue.md", "wb") as f:
        f.write(_dialogue.encode("utf-8"))

    with open("./dist/arxiv_draft_conversation.json", "w", encoding="utf-8") as f:
        f.write(conversation.model_dump_json(indent=2, exclude_none=True))

    with open("./dist/arxiv_draft_podcast.wav", "wb") as f:
        f.write(podcast_audio.wav)

    print("Podcast audio recorded successfully.")


@pytest.mark.asyncio
async def test_record_podcast_html():
    url = "https://www.aozora.gr.jp/cards/000879/files/127_15260.html"  # 羅生門

    podcast_studio = PodcastStudio(api_key=API_KEY)
    voicevox = VoiceVoxClient("http://localhost:10101")

    _blog, _dialogue, conversation = await podcast_studio.create_conversation(url)
    podcast_audio = await podcast_studio.record_podcast(
        conversation=conversation,
        voicevox_client=voicevox,
        speaker_id=1937616896,  # にせ ノーマル
        supporter_id=888753760,  # Anneli ノーマル
    )

    assert podcast_audio is not None
    assert isinstance(podcast_audio.wav, bytes)

    with open("./dist/rashoumon_blog.md", "wb") as f:
        f.write(_blog.encode("utf-8"))

    with open("./dist/rashoumon_dialogue.md", "wb") as f:
        f.write(_dialogue.encode("utf-8"))

    with open("./dist/rashoumon_conversation.json", "w", encoding="utf-8") as f:
        f.write(conversation.model_dump_json(indent=2, exclude_none=True))

    with open("./dist/rashoumon_podcast.wav", "wb") as f:
        f.write(podcast_audio.wav)

    print("Podcast audio recorded successfully.")
