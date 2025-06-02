import asyncio
from tqdm import tqdm
import logging

from .agent import BloggerAgent, WriterAgent, StructureAgent, Conversation
from .fetcher import AutoFetcher
from .voicevox import VoiceVoxClient, SpeakerId, Audio


class PodcastStudio:
    def __init__(self, api_key: str, logging_level: int = logging.INFO):
        self.blogger = BloggerAgent(api_key=api_key)
        self.writer = WriterAgent(api_key=api_key)
        self.structure_agent = StructureAgent(api_key=api_key)

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging_level)

        self.fetcher = AutoFetcher()

    async def create_conversation(self, url: str) -> tuple[str, str, Conversation]:
        self.logger.info(f"Fetching paper from {url}...")
        paper = await self.fetcher.fetch(url)
        self.logger.info("Paper fetched successfully.")
        self.logger.debug(
            f"Paper content: {paper[:100]}..."
        )  # Log first 100 characters

        self.logger.info("Creating blog from paper...")
        blog = await self.blogger.task(paper)
        self.logger.info("Blog created successfully.")
        self.logger.debug(f"{blog[:100]}...")  # Log first 100 characters

        self.logger.info("Creating dialogue from blog...")
        dialogue = await self.writer.task(paper, blog)
        self.logger.info("Dialogue created successfully.")
        self.logger.debug(f"{dialogue[:100]}...")  # Log first 100 characters

        self.logger.info("Structuring conversation from dialogue...")
        conversation = await self.structure_agent.task(dialogue)
        self.logger.info("Conversation structured successfully.")
        for _d in conversation.conversation:
            self.logger.debug(f"{_d.role}: {_d.content[:100]}...")

        return blog, dialogue, conversation

    async def record_podcast(
        self,
        conversation: Conversation,
        voicevox_client: VoiceVoxClient,
        speaker_id: SpeakerId,
        supporter_id: SpeakerId,
    ) -> Audio:
        progress_bar = tqdm(
            total=len(conversation.conversation),
            desc="Synthesizing audio",
            ncols=100,
        )

        async def _synthesis(
            speaker_id: SpeakerId,
            text: str,
            index: int,
            progress: tqdm,
        ) -> tuple[int, Audio]:
            audio_query = await voicevox_client.post_audio_query(
                text=text,
                speaker=speaker_id,
            )
            audio_query.speedScale = 1.1

            audio = await voicevox_client.post_synthesis(
                speaker=speaker_id,
                audio_query=audio_query,
            )
            progress.update(1)

            progress.set_postfix({"text": text[:20] + "..."})

            return index, audio

        results = []
        for i, dialogue in enumerate(conversation.conversation):
            results.append(
                await _synthesis(
                    speaker_id=(
                        speaker_id if dialogue.role == "speaker" else supporter_id
                    ),
                    text=dialogue.content,
                    index=i,
                    progress=progress_bar,
                )
            )
        progress_bar.close()

        # sort results by index
        results.sort(key=lambda x: x[0])

        audios = [audio for _, audio in results]

        # connect audio files
        podcast = await voicevox_client.post_connect_waves(
            audio_list=audios,
        )
        return podcast
