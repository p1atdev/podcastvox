import asyncio

from .agent import BloggerAgent, WriterAgent, StructureAgent, Conversation, PDF2MDAgent
from .voicevox import VoiceVoxClient, SpeakerId, Audio


class PodcastStudio:
    def __init__(self, api_key: str):
        self.blogger = BloggerAgent(api_key=api_key)
        self.writer = WriterAgent(api_key=api_key)
        self.structure_agent = StructureAgent(api_key=api_key)

        self.pdf2md = PDF2MDAgent()

    async def create_conversation(self, pdf_url: str) -> tuple[str, str, Conversation]:
        paper = await self.pdf2md.read_remote(pdf_url)

        blog = await self.blogger.task(paper)
        dialogue = await self.writer.task(paper, blog)
        conversation = await self.structure_agent.task(dialogue)

        return blog, dialogue, conversation

    async def record_podcast(
        self,
        conversation: Conversation,
        voicevox_client: VoiceVoxClient,
        speaker_id: SpeakerId,
        supporter_id: SpeakerId,
    ) -> Audio:
        async def _synthesis(
            speaker_id: SpeakerId, text: str, index: int
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
            return index, audio

        results = await asyncio.gather(
            *[
                _synthesis(
                    speaker_id=speaker_id
                    if dialogue.role == "speaker"
                    else supporter_id,
                    text=dialogue.content,
                    index=i,
                )
                for i, dialogue in enumerate(conversation.conversation)
            ]
        )
        # sort results by index
        results.sort(key=lambda x: x[0])

        audios = [audio for _, audio in results]

        # connect audio files
        podcast = await voicevox_client.post_connect_waves(
            audio_list=audios,
        )
        return podcast
