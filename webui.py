import tempfile
import asyncio
import dotenv
import os


from src.voicevox import VoiceVoxClient
from src.agent import Conversation
from src.podcast import PodcastStudio

import gradio as gr

dotenv.load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


async def generate_podcast(
    voicevox_endpoint: str,
    llm_api_key: str,
    pdf_url: str,
    speaker_name: str,
    supporter_name: str,
    speaker2id: dict[str, int],
) -> tuple[str, str, object, Conversation]:
    client = VoiceVoxClient(voicevox_endpoint)

    speaker_id = speaker2id[speaker_name]
    supporter_id = speaker2id[supporter_name]

    podcast_studio = PodcastStudio(api_key=llm_api_key)

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

    return (
        temp_file_path,
        blog,
        conversation.model_dump(),
        conversation,
        gr.update(visible=True),
    )


async def change_speaker(
    voicevox_endpoint: str,
    speaker_name: str,
    supporter_name: str,
    speaker2id: dict[str, int],
    conversation_cache: Conversation,
) -> str:
    client = VoiceVoxClient(voicevox_endpoint)

    speaker_id = speaker2id[speaker_name]
    supporter_id = speaker2id[supporter_name]

    podcast_studio = PodcastStudio(api_key="")

    podcast_audio = await podcast_studio.record_podcast(
        conversation=conversation_cache,
        voicevox_client=client,
        speaker_id=speaker_id,
        supporter_id=supporter_id,
    )

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(podcast_audio.wav)
        temp_file_path = temp_file.name

    return temp_file_path


async def get_speakers(endpoint: str):
    client = VoiceVoxClient(endpoint)

    speakers = await client.get_speakers()

    choices = []
    speaker_ids = []
    for speaker in speakers:
        for style in speaker.styles:
            choices.append(f"{speaker.name} ({style.name})")
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


async def main():
    initial_endpoint = "http://localhost:50021"
    try:
        speakers, spaker2id = await get_speakers(initial_endpoint)
    except Exception as _e:
        speakers = []
        spaker2id = {}

    with gr.Blocks() as demo:
        with gr.Row():
            with gr.Column():
                with gr.Group():
                    endpoint_text = gr.Textbox(
                        label="VOICEVOX エンドポイント",
                        value=initial_endpoint,
                        placeholder="http://localhost:50021",
                        info="VOICEVOX 型 の REST API に対応したエンドポイントを入力してください",
                    )
                    with gr.Row():
                        speakers_dropdown = gr.Dropdown(
                            label="メイン話者",
                            choices=speakers,
                            value=None if len(speakers) == 0 else speakers[0],
                            multiselect=False,
                        )
                        supporter_dropdown = gr.Dropdown(
                            label="サポーター話者",
                            choices=speakers,
                            value=None if len(speakers) < 2 else speakers[1],
                            multiselect=False,
                        )
                    spaker2id_map = gr.State(value=spaker2id)

                    change_speaker_button = gr.Button(
                        "この話者で再録音",
                        variant="secondary",
                        visible=False,
                    )

                with gr.Group():
                    llm_api_key_text = gr.Textbox(
                        label="Gemini API Key",
                        info="https://aistudio.google.com/apikey",
                        placeholder="Enter your Gemini API key",
                        value=GEMINI_API_KEY,
                        type="password",
                        visible=GEMINI_API_KEY == "",
                    )

            with gr.Column():
                with gr.Group():
                    pdf_url_text = gr.Textbox(
                        label="PDF の URL",
                        placeholder="https://arxiv.org/pdf/2308.06721",
                        lines=1,
                        info="Podcast のテーマとなる PDF の URL を入力してください。PDF は公開されている必要があります。",
                    )
                    submit_button = gr.Button("Synthesize", variant="primary")

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
            outputs=[output_audio],
            concurrency_limit=10,
        )

    demo.launch()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Web UI stopped by user.")
