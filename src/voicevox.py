import aiohttp
from typing import Literal
from pydantic import BaseModel
import io
import base64

SpeakerId = int


class SpeakerStyle(BaseModel):
    name: str
    id: SpeakerId
    type: Literal["talk"]


class Speaker(BaseModel):
    name: str
    speaker_uuid: str
    styles: list[SpeakerStyle]
    version: str


class AudioQuery(BaseModel):
    accent_phrases: list[dict]
    speedScale: float
    intonationScale: float
    tempoDynamicsScale: float | None = None
    pitchScale: float
    volumeScale: float
    prePhonemeLength: float
    postPhonemeLength: float
    pauseLength: float | None
    pauseLengthScale: float
    outputSamplingRate: int
    outputStereo: bool
    kana: str


class Audio(BaseModel):
    wav: bytes


class VoiceVoxClient:
    endpoint: str

    def __init__(self, endpoint: str = "http://127.0.0.1:50021"):
        self.endpoint = endpoint

    async def get_speakers(self) -> list[Speaker]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.endpoint}/speakers") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get speakers: {response.status}")
                return [
                    Speaker.model_validate(speaker) for speaker in await response.json()
                ]

    async def get_core_versions(self) -> list[str]:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.endpoint}/core_versions") as response:
                if response.status != 200:
                    raise Exception(f"Failed to get core version: {response.status}")
                return await response.json()

    async def post_audio_query(
        self,
        text: str,
        speaker: SpeakerId,
        core_version: str | None = None,
    ) -> AudioQuery:
        async with aiohttp.ClientSession() as session:
            params: dict[str, str | int | float] = {"text": text, "speaker": speaker}
            if core_version:
                params["core_version"] = core_version
            async with session.post(
                f"{self.endpoint}/audio_query",
                params=params,
            ) as res:
                if res.status != 200:
                    raise Exception(f"Failed to post audio query: {res.status}")
                json_data = await res.json()
                return AudioQuery.model_validate(json_data)

    async def post_synthesis(
        self,
        speaker: SpeakerId,
        audio_query: AudioQuery,
        enable_interrogative_upspeak: bool = True,
        core_version: str | None = None,
    ) -> Audio:
        async with aiohttp.ClientSession() as session:
            params: dict[str, str | int | float] = {
                "speaker": speaker,
                "enable_interrogative_upspeak": (
                    "true" if enable_interrogative_upspeak else "false"
                ),
            }
            if core_version:
                params["core_version"] = core_version
            async with session.post(
                f"{self.endpoint}/synthesis",
                params=params,
                json=audio_query.model_dump(),
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to post synthesis: {response.status}")
                wav = io.BytesIO(await response.read())
                return Audio(wav=wav.getvalue())

    async def post_connect_waves(
        self,
        audio_list: list[Audio],
    ) -> Audio:
        async with aiohttp.ClientSession() as session:
            audio_data = [
                base64.b64encode(audio.wav).decode("utf-8") for audio in audio_list
            ]
            async with session.post(
                f"{self.endpoint}/connect_waves",
                json=audio_data,
            ) as response:
                if response.status != 200:
                    raise Exception(f"Failed to connect waves: {response.status}")
                wav = io.BytesIO(await response.read())
                return Audio(wav=wav.getvalue())
