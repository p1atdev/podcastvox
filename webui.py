import tempfile
import asyncio
import aiohttp
import dotenv
import os
import time
import logging


from src.voicevox import VoiceVoxClient
from src.agent import Conversation
from src.podcast import PodcastStudio

import gradio as gr

dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

DEFAULT_MODELS = [
    "https://hub.aivis-project.com/aivm-models/a59cb814-0083-4369-8542-f51a29e72af7",  # Anneli
    "https://hub.aivis-project.com/aivm-models/4cf3e1d8-5583-41a9-a554-b2d2cda2c569",  # Anneli Whisper
    "https://hub.aivis-project.com/aivm-models/6acf95e8-11a9-414e-aa9c-6dbebf9113ca",  # F1
    "https://hub.aivis-project.com/aivm-models/25b39db7-5757-47ef-9fe4-2b7aff328a18",  # F2
    "https://hub.aivis-project.com/aivm-models/d7255c2c-ddd0-425a-808c-662cd94c7f41",  # M1
    "https://hub.aivis-project.com/aivm-models/d1a7446f-230d-4077-afdf-923eddabe53c",  # M2
    "https://hub.aivis-project.com/aivm-models/6d11c6c2-f4a4-4435-887e-23dd60f8b8dd",  # にせ
    "https://hub.aivis-project.com/aivm-models/e9339137-2ae3-4d41-9394-fb757a7e61e6",  # まい
    "https://hub.aivis-project.com/aivm-models/eefe1fbd-d15a-49ae-bc83-fc4aaad680e1",  # ハヤテ
    "https://hub.aivis-project.com/aivm-models/5d804388-665e-4174-ab60-53d448c0d7eb",  # 老当主
    "https://hub.aivis-project.com/aivm-models/71e72188-2726-4739-9aa9-39567396fb2a",  # ふみふみ
]
AIVIS_ENDPOINT = "http://127.0.0.1:10101"

NAVIGATOR_SAMPLE = "こんにちは！私の名前は {nickname} です。今回は私がポッドキャストをナビゲートします。よろしくお願いします！"
ASSISTANT_SAMPLE = "こんにちは！私の名前は {nickname} です。私はサポーターとして、ナビゲーターと一緒にポッドキャストを盛り上げていきます。頑張ります！"


async def generate_podcast(
    voicevox_endpoint: str,
    llm_api_key: str,
    pdf_url: str,
    speaker_name: str,
    supporter_name: str,
    speaker2id: dict[str, int],
) -> tuple[str, str, object, Conversation, str, dict]:
    client = VoiceVoxClient(voicevox_endpoint)

    speaker_id = speaker2id[speaker_name]
    supporter_id = speaker2id[supporter_name]

    podcast_studio = PodcastStudio(
        api_key=llm_api_key,
        logging_level=logging.DEBUG,
    )

    start_time = time.time()

    blog, _dialogue, conversation = await podcast_studio.create_conversation(pdf_url)
    podcast_audio = await podcast_studio.record_podcast(
        conversation=conversation,
        voicevox_client=client,
        speaker_id=speaker_id,
        supporter_id=supporter_id,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(podcast_audio.wav)
        temp_file_path = temp_file.name

    elapsed_time = time.time() - start_time
    time_elapsed_text = f"処理時間: {elapsed_time:.2f} 秒"

    return (
        temp_file_path,
        blog,
        conversation.model_dump(),
        conversation,
        time_elapsed_text,
        gr.update(visible=True),
    )


async def change_speaker(
    voicevox_endpoint: str,
    speaker_name: str,
    supporter_name: str,
    speaker2id: dict[str, int],
    conversation_cache: Conversation,
) -> tuple[str, str]:
    client = VoiceVoxClient(voicevox_endpoint)

    speaker_id = speaker2id[speaker_name]
    supporter_id = speaker2id[supporter_name]

    podcast_studio = PodcastStudio(api_key="")  # only voice synthesis

    start_time = time.time()
    podcast_audio = await podcast_studio.record_podcast(
        conversation=conversation_cache,
        voicevox_client=client,
        speaker_id=speaker_id,
        supporter_id=supporter_id,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(podcast_audio.wav)
        temp_file_path = temp_file.name

    elapsed_time = time.time() - start_time
    time_elapsed_text = f"処理時間: {elapsed_time:.2f} 秒"

    return temp_file_path, time_elapsed_text


async def get_speakers(endpoint: str):
    client = VoiceVoxClient(endpoint)

    speakers = await client.get_speakers()

    print(f"Found {len(speakers)} speakers at {endpoint}")

    choices = []
    speaker_ids = []
    for speaker in speakers:
        for style in speaker.styles:
            spekaer_name = f"{speaker.name} ({style.name})"
            print(f"Speaker: {spekaer_name}, ID: {style.id}")
            choices.append(spekaer_name)
            speaker_ids.append(style.id)

    speaker2id = dict(zip(choices, speaker_ids))

    return choices, speaker2id


async def on_endpoint_change(endpoint_text: str):
    try:
        speakers, speaker2id = await get_speakers(endpoint_text)
        return (
            gr.update(choices=speakers, value=speakers[0]),
            gr.update(choices=speakers, value=speakers[1]),
            speaker2id,
        )
    except Exception as e:
        return gr.update(), gr.update(), gr.update()


async def preview_speaker_voice(
    voicevox_endpoint: str,
    speaker_name: str,
    speaker_id: int,
    is_main_speaker: bool = True,
):
    client = VoiceVoxClient(voicevox_endpoint)

    speaker_nickname = speaker_name.split("(")[0].strip()

    if is_main_speaker:
        sample_text = NAVIGATOR_SAMPLE.format(nickname=speaker_nickname)
    else:
        sample_text = ASSISTANT_SAMPLE.format(nickname=speaker_nickname)

    audio_query = await client.post_audio_query(
        text=sample_text,
        speaker=speaker_id,
    )
    if audio_query.tempoDynamicsScale is not None:
        audio_query.tempoDynamicsScale = 1.1
    else:
        audio_query.speedScale = 1.1

    audio = await client.post_synthesis(
        speaker=speaker_id,
        audio_query=audio_query,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(audio.wav)
        temp_file_path = temp_file.name

    return temp_file_path


async def on_change_speaker(
    voicevox_endpoint: str,
    speaker_name: str,
    speaker2id: dict[str, int],
    is_main_speaker: bool,
):
    speaker_id = speaker2id[speaker_name]
    return await preview_speaker_voice(
        voicevox_endpoint=voicevox_endpoint,
        speaker_name=speaker_name,
        speaker_id=speaker_id,
        is_main_speaker=is_main_speaker,
    )


async def wait_for_endpoint(url: str, timeout: float = 30.0, interval: float = 0.5):
    """url が 200 を返すまで待機"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as res:
                    if res.status == 200:
                        return
        except Exception:
            pass
        await asyncio.sleep(interval)
    raise RuntimeError(f"Endpoint {url} did not become ready in {timeout}s")


async def main():
    await wait_for_endpoint(AIVIS_ENDPOINT)

    initial_endpoint = AIVIS_ENDPOINT
    try:
        speakers, spaker2id = await get_speakers(initial_endpoint)
    except Exception as _e:
        speakers = []
        spaker2id = {}

    main_speaker_name = "Anneli (テンション高め)"
    supporter_speaker_name = "まい (ノーマル)"

    main_speaker_preview = None
    supporter_speaker_preview = None
    if main_speaker_name is not None:
        main_speaker_preview = await preview_speaker_voice(
            voicevox_endpoint=initial_endpoint,
            speaker_name=main_speaker_name,
            speaker_id=spaker2id.get(main_speaker_name, 0),
            is_main_speaker=True,
        )
    if supporter_speaker_name is not None:
        supporter_speaker_preview = await preview_speaker_voice(
            voicevox_endpoint=initial_endpoint,
            speaker_name=supporter_speaker_name,
            speaker_id=spaker2id.get(supporter_speaker_name, 0),
            is_main_speaker=False,
        )

    with gr.Blocks() as demo:
        gr.Markdown(
            """
# PodcastVox (Aivis Speech)

Gemini Flash 2.5 と Aivis Speech を利用して、Web サイトを情報源とした Podcast を生成することができます。

## 注意点

**情報に基づいた会話を生成しますが、ハルシネーションや誤った解釈、間違った単語の読み方が発生する場合があります。生成された内容の正確性や信頼性については保証できませんので、注意してご利用ください。**

"""
        )

        with gr.Row():
            with gr.Column():
                with gr.Group():
                    endpoint_text = gr.Textbox(
                        label="VOICEVOX エンドポイント",
                        value=initial_endpoint,
                        placeholder=AIVIS_ENDPOINT,
                        info="VOICEVOX 型 の REST API に対応したエンドポイントを入力してください",
                        visible=False,
                    )
                    with gr.Row():
                        with gr.Column():
                            speakers_dropdown = gr.Dropdown(
                                label="メイン話者",
                                choices=speakers,
                                value=main_speaker_name,
                                multiselect=False,
                            )
                            speaker_preview_audio = gr.Audio(
                                label="メイン話者音声プレビュー",
                                type="filepath",
                                value=main_speaker_preview,
                            )

                        with gr.Column():
                            supporter_dropdown = gr.Dropdown(
                                label="サポーター話者",
                                choices=speakers,
                                value=supporter_speaker_name,
                                multiselect=False,
                            )
                            supporter_preview_audio = gr.Audio(
                                label="サポーター音声プレビュー",
                                type="filepath",
                                value=supporter_speaker_preview,
                            )

                    spaker2id_map = gr.State(value=spaker2id)

                    change_speaker_button = gr.Button(
                        "この話者で再生成",
                        variant="secondary",
                        visible=False,
                    )

                with gr.Group():
                    llm_api_key_text = gr.Textbox(
                        label="Gemini API Key",
                        info="Podcast を生成するには API キーが必要です。https://aistudio.google.com/apikey から取得できます。",
                        placeholder="Enter your Gemini API key",
                        value=GEMINI_API_KEY,
                        type="password",
                        visible=GEMINI_API_KEY == "",
                    )

            with gr.Column():
                with gr.Group():
                    pdf_url_text = gr.Textbox(
                        label="情報源となる Web サイト の URL (1つのみ)",
                        placeholder="例) https://arxiv.org/pdf/2308.06721, https://example.com/index.html",
                        lines=1,
                        info="Podcast のテーマとなる Web サイト の URL を入力してください。HTML、PDF に対応しています。",
                    )
                    submit_button = gr.Button(
                        "生成 (約 5 分程度かかります)", variant="primary"
                    )

                time_elapsed_text = gr.Markdown(
                    value="",
                )

                output_audio = gr.Audio(
                    label="Output Podcast Audio",
                    type="filepath",
                    autoplay=True,
                )
                conversation_cache = gr.State(value=None)

                with gr.Accordion("生成されたブログ", open=False):
                    blog_output = gr.Markdown(
                        label="Blog Output",
                        value="生成されたブログはここに表示されます。",
                    )

                with gr.Accordion("生成された会話", open=False):
                    conversation_output = gr.JSON(label="Conversation Output", value={})

        gr.Examples(
            examples=[
                ["https://arxiv.org/pdf/2106.09685"],  # LoRA
                ["https://arxiv.org/pdf/2501.03575"],  # Cosmos
                ["https://arxiv.org/pdf/2503.07565"],  # Inductive Moment Matching
                ["https://arxiv.org/pdf/2303.15343"],  # SigLIP
                ["https://arxiv.org/pdf/2212.09748"],  # DiT
                ["https://arxiv.org/pdf/2501.16937"],  # TAID
                [
                    "https://lilianweng.github.io/posts/2021-05-31-contrastive/"
                ],  # Contrastive Learning
                [
                    "https://www.aozora.gr.jp/cards/000879/files/127_15260.html"
                ],  # 羅生門
                ["https://tech-blog.abeja.asia/entry/hyperbolic_ml_2019"],  # 双極空間
                [
                    "https://uehara-mech.github.io/assets/nlp2025-asagi-vlm.pdf"
                ],  # Asagi VLM
            ],
            inputs=[pdf_url_text],
        )

        gr.on(
            triggers=[endpoint_text.change],
            fn=on_endpoint_change,
            inputs=[endpoint_text],
            outputs=[
                speakers_dropdown,
                supporter_dropdown,
                spaker2id_map,
            ],
            concurrency_limit=10,
        )
        gr.on(
            triggers=[submit_button.click],
            fn=generate_podcast,
            inputs=[
                endpoint_text,
                llm_api_key_text,
                pdf_url_text,
                speakers_dropdown,
                supporter_dropdown,
                spaker2id_map,
            ],
            outputs=[
                output_audio,
                blog_output,
                conversation_output,
                conversation_cache,
                time_elapsed_text,
                change_speaker_button,  # make visible after generation
            ],
            concurrency_limit=10,
        )
        gr.on(
            triggers=[change_speaker_button.click],
            fn=change_speaker,
            inputs=[
                endpoint_text,
                speakers_dropdown,
                supporter_dropdown,
                spaker2id_map,
                conversation_cache,
            ],
            outputs=[
                output_audio,
                time_elapsed_text,
            ],
            concurrency_limit=10,
        )
        gr.on(
            triggers=[
                speakers_dropdown.change,
            ],
            fn=on_change_speaker,
            inputs=[
                endpoint_text,
                speakers_dropdown,
                spaker2id_map,
                gr.State(value=True),
            ],
            outputs=[speaker_preview_audio],
            concurrency_limit=10,
        )
        gr.on(
            triggers=[
                supporter_dropdown.change,
            ],
            fn=on_change_speaker,
            inputs=[
                endpoint_text,
                supporter_dropdown,
                spaker2id_map,
                gr.State(value=False),
            ],
            outputs=[supporter_preview_audio],
            concurrency_limit=10,
        )

    demo.launch()


async def runner():
    webui = asyncio.create_task(main())

    await asyncio.gather(webui)


if __name__ == "__main__":
    asyncio.run(runner())
