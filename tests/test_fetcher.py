import pytest


from src.fetcher import PDFFetcher, HTMLFetcher, AutoFetcher


@pytest.mark.asyncio
async def test_fetch_pdf():
    pdf_url = "https://arxiv.org/pdf/2309.17400"

    fetcher = PDFFetcher()

    markdown = await fetcher.fetch(pdf_url)
    assert isinstance(markdown, str)
    assert len(markdown) > 0


@pytest.mark.asyncio
async def test_fetch_html():
    html_url = "https://www.aozora.gr.jp/cards/000879/files/127_15260.html"

    fetcher = HTMLFetcher()

    markdown = await fetcher.fetch(html_url)
    assert isinstance(markdown, str)
    assert len(markdown) > 0


@pytest.mark.asyncio
async def test_fetch_auto():
    pdf_url = "https://arxiv.org/pdf/2309.17400"
    html_url = "https://www.aozora.gr.jp/cards/000879/files/127_15260.html"

    fetcher = AutoFetcher()

    markdown_pdf = await fetcher.fetch(pdf_url)
    assert isinstance(markdown_pdf, str)
    assert len(markdown_pdf) > 0

    markdown_html = await fetcher.fetch(html_url)
    assert isinstance(markdown_html, str)
    assert len(markdown_html) > 0
