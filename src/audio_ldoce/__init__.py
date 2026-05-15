from aqt import mw
from aqt.qt import QAction, QInputDialog
from aqt.utils import showInfo

from anki.notes import Note

from .ldoce_client import LDOCEClient


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


def create_card(word: str, audio_filename: str):
    col = mw.col

    model = get_or_create_model()
    note = Note(col, model)

    note["Text"] = word
    note["Audio"] = f"[sound:{audio_filename}]"

    deck_id = col.decks.current()["id"]

    col.add_note(note, deck_id)
    mw.reset()


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


def main():
    action = QAction("Add Word (LDOCE Audio)", mw)
    action.triggered.connect(add_word_with_audio)
    mw.form.menuTools.addAction(action)


if __name__ == "__main__":
    main()
