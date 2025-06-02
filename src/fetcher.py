import aiohttp
import io
from markitdown import MarkItDown


class PDFFetcher:
    def __init__(self):
        self.md = MarkItDown(enable_plugins=True)

    def read_local(self, pdf_path: str) -> str:
        result = self.md.convert(pdf_path)

        markdown = self.postprocess(result.text_content)

        return markdown

    def postprocess(self, markdown: str) -> str:
        pages = markdown.split("\f")
        markdown = "\n".join(pages)
        return markdown.strip()

    async def fetch(self, pdf_url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(pdf_url) as res:
                if res.status != 200:
                    raise Exception(f"Failed to download PDF: {res.status}")

                pdf_content = await res.read()

        markdown = self.md.convert_stream(io.BytesIO(pdf_content)).text_content

        markdown = self.postprocess(markdown)

        return markdown


class HTMLFetcher:
    def __init__(self):
        self.md = MarkItDown(enable_plugins=True)

    async def fetch(self, html_url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(html_url) as res:
                if res.status != 200:
                    raise Exception(f"Failed to download HTML: {res.status}")

                data = await res.read()

            markdown = self.md.convert_stream(io.BytesIO(data))

        return markdown.text_content


class AutoFetcher:
    def __init__(self):
        self.pdf_fetcher = PDFFetcher()
        self.html_fetcher = HTMLFetcher()

        self.md = MarkItDown(enable_plugins=True)

    async def fetch(self, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                if res.status != 200:
                    raise Exception(f"Failed to download HTML: {res.status}")

                data = await res.read()
                content_type = res.headers.get(
                    "Content-Type",
                    res.headers.get("content-type", "text/plain"),
                )

        if "application/pdf" in content_type:
            return self.pdf_fetcher.postprocess(
                self.md.convert_stream(io.BytesIO(data)).text_content
            )

        elif "text/html" in content_type:
            return self.md.convert_stream(io.BytesIO(data)).text_content

        else:
            # plain?
            return self.md.convert_stream(io.BytesIO(data)).text_content
