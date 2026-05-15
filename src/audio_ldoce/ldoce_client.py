import contextlib
import importlib
import os
import sys
import tempfile
from pathlib import Path
from typing import Generator
from urllib.parse import urlparse

VENDOR_PATH = Path(__file__).parent / "vendor"

if VENDOR_PATH not in sys.path:
    sys.path.insert(0, VENDOR_PATH.as_posix())

requests = importlib.import_module("requests")
bs4 = importlib.import_module("bs4")


class LDOCEClient:
    BASE_URL = "https://www.ldoceonline.com/dictionary/"

    def __init__(self, timeout: int = 10) -> None:
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})
        self._timeout = timeout

    def fetch_page(self, word: str) -> str:
        url = self.BASE_URL + word
        res = self._session.get(url, timeout=self._timeout)
        res.raise_for_status()
        return res.text

    def get_examples(self, word: str) -> list[dict[str, str]]:
        html = self.fetch_page(word)
        soup = bs4.BeautifulSoup(html, "html.parser")

        results = []

        for ex in soup.select("span.EXAMPLE"):
            speaker = ex.select_one("span.speaker")
            audio = speaker.get("data-src-mp3") if speaker else None

            text = ex.get_text(strip=True)

            results.append({"text": text, "audio": audio})

        return results

    @contextlib.contextmanager
    def download_audio(self, url: str) -> Generator[Path, None, None]:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

        res = self._session.get(url, timeout=self._timeout)
        res.raise_for_status()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / filename
            path.write_bytes(res.content)
            yield path
