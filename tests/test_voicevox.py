import pytest


from src.voicevox import VoiceVoxClient


@pytest.mark.asyncio
async def test_voicevox_get_speakers():
    client = VoiceVoxClient("http://localhost:50021")

    speakers = await client.get_speakers()
    assert isinstance(speakers, list)
    assert len(speakers) > 0


@pytest.mark.asyncio
async def test_aivis_get_speakers():
    client = VoiceVoxClient("http://localhost:10101")

    speakers = await client.get_speakers()
    assert isinstance(speakers, list)
    assert len(speakers) > 0


@pytest.mark.asyncio
async def test_voicevox_audio_query():
    client = VoiceVoxClient("http://localhost:50021")

    speakers = await client.get_speakers()
    assert len(speakers) > 0

    core_version = (await client.get_core_versions())[0]
    assert isinstance(core_version, str)

    audio_query = await client.post_audio_query(
        text="こんにちは！",
        speaker=speakers[0].styles[0].id,
        core_version=core_version,
    )
    assert audio_query is not None


@pytest.mark.asyncio
async def test_aivis_audio_query():
    client = VoiceVoxClient("http://localhost:10101")

    speakers = await client.get_speakers()
    assert len(speakers) > 0

    core_version = (await client.get_core_versions())[0]
    assert isinstance(core_version, str)

    audio_query = await client.post_audio_query(
        text="こんにちは！",
        speaker=speakers[0].styles[0].id,
        core_version=core_version,
    )
    assert audio_query is not None


@pytest.mark.asyncio
async def test_aivis_synthesis():
    client = VoiceVoxClient("http://localhost:10101")

    speakers = await client.get_speakers()
    assert len(speakers) > 0

    core_version = (await client.get_core_versions())[0]
    assert isinstance(core_version, str)

    audio_query = await client.post_audio_query(
        text="こんにちは！",
        speaker=speakers[0].styles[0].id,
        core_version=core_version,
    )
    assert audio_query is not None

    audio_data = await client.post_synthesis(
        speaker=speakers[0].styles[0].id,
        audio_query=audio_query,
        enable_interrogative_upspeak=True,
        core_version=core_version,
    )
    assert audio_data is not None
    assert isinstance(audio_data.wav, bytes)


@pytest.mark.asyncio
async def test_aivis_connect_waves():
    client = VoiceVoxClient("http://localhost:10101")

    speakers = await client.get_speakers()
    assert len(speakers) > 0

    core_version = (await client.get_core_versions())[0]
    assert isinstance(core_version, str)

    audio_query = await client.post_audio_query(
        text="こんにちは！",
        speaker=speakers[0].styles[0].id,
        core_version=core_version,
    )
    assert audio_query is not None

    audio_data = await client.post_synthesis(
        speaker=speakers[0].styles[0].id,
        audio_query=audio_query,
        enable_interrogative_upspeak=True,
        core_version=core_version,
    )
    assert audio_data is not None
    assert isinstance(audio_data.wav, bytes)

    audio_data2 = await client.post_synthesis(
        speaker=speakers[0].styles[0].id,
        audio_query=audio_query,
        enable_interrogative_upspeak=True,
        core_version=core_version,
    )
    assert audio_data2 is not None
    assert isinstance(audio_data2.wav, bytes)

    connected_waves = await client.post_connect_waves(
        [audio_data, audio_data2],
    )
    assert connected_waves is not None
    assert isinstance(connected_waves.wav, bytes)
