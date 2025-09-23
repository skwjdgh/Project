import regex as re

EMOJI_RE = re.compile(r"[\p{Emoji}\p{Emoji_Presentation}\p{Emoji_Modifier}\p{Emoji_Modifier_Base}\p{Emoji_Component}]+", flags=re.UNICODE)

def strip_emoji(text: str) -> str:
    """Remove emojis and emoji-like pictographs."""
    return EMOJI_RE.sub('', text or '')
