from aqt import mw
from aqt.qt import *
from aqt.utils import showInfo

from anki.notes import Note

import urllib.request
import urllib.error
import re

import os

from .ldoce_client import LDOCEClient


# =========================
# HELPER: FETCH HTML
# =========================
def fetch_html(url: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.read().decode("utf-8", errors="ignore")
    except urllib.error.URLError:
        return None


# =========================
# 1. TÌM AUDIO TỪ LDOCE
# =========================
def get_audio_url(word: str):
    url = f"https://www.ldoceonline.com/dictionary/{word}"

    html = fetch_html(url)
    if not html:
        return None

    match = re.search(
        r'https://www\.ldoceonline\.com/media/english/(?:exaProns|pron)/[^"]+\.mp3',
        html,
    )

    if match:
        return match.group(0)

    return None


# =========================
# 2. DOWNLOAD AUDIO
# =========================
def download_audio(url: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as res:
            data = res.read()
    except urllib.error.URLError:
        return None

    filename = url.split("/")[-1].split("?")[0]

    media_dir = mw.col.media.dir()
    path = os.path.join(media_dir, filename)

    # tránh overwrite
    if os.path.exists(path):
        base, ext = os.path.splitext(filename)
        filename = f"{base}_1{ext}"
        path = os.path.join(media_dir, filename)

    with open(path, "wb") as f:
        f.write(data)

    return filename


def get_or_create_model():
    col = mw.col
    model_name = "My Audio Model"

    # 1. check tồn tại
    model = col.models.by_name(model_name)
    if model:
        return model

    # 2. tạo mới
    model = col.models.new(model_name)

    # tạo fields
    field_text = col.models.new_field("Text")
    field_audio = col.models.new_field("Audio")

    col.models.add_field(model, field_text)
    col.models.add_field(model, field_audio)

    # tạo template
    template = col.models.new_template("Card 1")

    template["qfmt"] = "{{Audio}}"
    template["afmt"] = "{{FrontSide}}<hr>{{Text}}"

    col.models.add_template(model, template)

    # (optional) style
    model["css"] = """
    .card {
        font-family: arial;
        font-size: 24px;
        text-align: center;
    }
    """

    # save model
    col.models.add(model)

    return model

# =========================
# 3. TẠO CARD
# =========================
def create_card(word: str, audio_filename: str):
    col = mw.col

    model = get_or_create_model()
    note = Note(col, model)

    note["Text"] = word
    note["Audio"] = f"[sound:{audio_filename}]"

    deck_id = col.decks.current()["id"]
    # note.model()["did"] = deck_id

    col.add_note(note, deck_id)
    mw.reset()

# =========================
# 4. MAIN FLOW
# =========================
def add_word_with_audio():
    word, ok = QInputDialog.getText(None, "Nhập từ", "Word:")

    if not ok or not word:
        return

    client = LDOCEClient()
    examples = client.get_examples(word.strip())

    for example in examples:
        text = example["text"]
        audio = example["audio"]
        if text and audio:
            showInfo(f"text: {text} - audio: {audio}")

            with client.download_audio(audio) as audio_file:
                media = mw.col.media
                filename = media.add_file(audio_file.as_posix())
                create_card(text, filename)
                pass

# =========================
# 5. MENU
# =========================
action = QAction("Add Word (LDOCE Audio)", mw)
action.triggered.connect(add_word_with_audio)
mw.form.menuTools.addAction(action)
