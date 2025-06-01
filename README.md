# PodcastVox

PDF ファイルから Gemini と VOICEVOX を使用してポッドキャスト音声を自動生成する Python アプリケーションです。

## 概要

PodcastVoxは、学術論文やドキュメントなどのPDFファイルを入力として、以下の処理を自動で行います：

1. **PDF解析**: PDFからテキストコンテンツを抽出
2. **ブログ記事生成**: AIがPDFの内容を分かりやすく解説する記事を作成
3. **対話台本生成**: ポッドキャスト形式の会話台本を生成
4. **音声合成**: VOICEVOXを使用して自然な音声ファイルを生成

## 主な機能

- 📄 PDF URL から自動でコンテンツを取得
- 🤖 Gemini AIによる内容の理解と解説生成
- 🎭 スピーカーとサポーターの二人による自然な対話形式
- 🎤 VOICEVOX/AIVCVOICE対応の音声合成
- 🌐 直感的なGradio Web UI
- 🔄 音声話者の変更・再録音機能

## 必要な環境

- [uv](https://docs.astral.sh/uv/) 
- VOICEVOX の API に対応した音声合成エンドポイント (Aivis Speech など) 
- Gemini API キー

## インストール

1. リポジトリをクローン:
```bash
git clone github.com/p1atdev/podcastvox
cd podcastvox
```

2. 仮想環境の作成:
```bash
uv sync
```


## セットアップ

### 1. 音声合成エンジンの準備

**VOICEVOX**の場合:
- [VOICEVOX公式サイト](https://voicevox.hiroshiba.jp/)からダウンロード
- アプリケーションを起動 (API): `http://localhost:50021`）

**Aivis Speech**の場合:
- [Aivis Speech公式サイト](https://aivis-project.com/)からダウンロード
- アプリケーションを起動 (API: `http://localhost:10101`)

### 2. API キーの設定

`.env`ファイルを作成し、Gemini API キーを設定:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

Gemini API キーは[Google AI Studio](https://aistudio.google.com/apikey)で取得できます。

## 使用方法

### Web UI の起動

```bash
source .venv/bin/activate
python webui.py
# または
# ./scripts/webui.sh
# または
# ./scripts/webui.bat
```

ブラウザで表示されるURLにアクセスし、以下の手順で使用：

1. **VOICEVOXエンドポイント**を確認（通常は http://localhost:50021）
2. **話者**を選択（メイン話者とサポーター話者）
3. **Gemini API Key**を入力（環境変数で設定済みの場合は不要）
4. **PDFのURL**を入力（例: https://arxiv.org/pdf/2308.06721）
5. **Synthesize**ボタンをクリック

## プロジェクト構成

```
podcastvox/
├── src/
│   ├── agent.py          # AI エージェント（ブログ生成、対話生成等）
│   ├── podcast.py        # ポッドキャスト生成のメインロジック
│   └── voicevox.py       # VOICEVOX API クライアント
├── tests/                # テストファイル
├── webui.py             # Gradio Web インターフェース
├── pyproject.toml       # プロジェクト設定
└── README.md            # このファイル
```


