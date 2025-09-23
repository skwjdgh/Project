from utils.clean_text import clean_text

def test_clean_text_basic():
    assert clean_text("안녕  \t 세상\n😀") == "안녕 세상"
