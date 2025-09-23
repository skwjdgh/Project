import MeCab
import platform
import logging

def tokenize_text(text):
    """
    Tokenizes Korean text using Mecab-ko, extracting key parts of speech.
    Falls back to splitting by whitespace if Mecab fails.
    """
    try:
        # Initialize Mecab
        mecab = MeCab.Tagger()
    except Exception as e:
        logging.warning(f"Mecab initialization failed: {e}. Falling back to whitespace tokenization.")
        return text.split()

    # Perform morphological analysis
    morphs = mecab.parse(text).splitlines()
    
    keywords = []
    for line in morphs:
        if line == "EOS":
            break
        try:
            word, features = line.split("\t")
            tag = features.split(",")[0]  # 품사 태그
            if tag.startswith(('N', 'V', 'S')) or tag in ['VA']:
                keywords.append(word)
        except:
            continue

    # Return a list of unique keywords while preserving order
    return list(dict.fromkeys(keywords))
