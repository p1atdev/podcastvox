import pytest
import dotenv
import os

from src.voicevox import VoiceVoxClient
from src.podcast import PodcastStudio

dotenv.load_dotenv(".env.local")
API_KEY = os.environ.get("GEMINI_API_KEY", "")
assert API_KEY != "", "GEMINI_API_KEY is not set in .env.local"


@pytest.mark.asyncio
async def test_record_podcast():
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

    with open("./dist/podcast.wav", "wb") as f:
        f.write(podcast_audio.wav)
    print("Podcast audio recorded successfully.")
