import re

# 常用标点与引号
QUOTE_OPEN_CLASS = r'[“"「『]'
QUOTE_CLOSE_CLASS = r'[”"」』]'
SENT_ENDERS = "。！？….!?;；\n"

def normalize_text(s: str) -> str:
    """轻量规范化：换行统一、去 BOM、合并连续空白。"""
    if not isinstance(s, str):
        s = str(s or "")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = s.replace("\ufeff", "")
    return s

def strip_quotes(s: str) -> str:
    return re.sub(rf'{QUOTE_OPEN_CLASS}|{QUOTE_CLOSE_CLASS}', '', s)

def sentence_spans(text: str):
    """以句末标点/换行作为边界，返回 (L, R) 闭开区间。"""
    L = 0
    n = len(text)
    for i, ch in enumerate(text):
        if ch in SENT_ENDERS:
            yield (L, i + 1)
            L = i + 1
    if L < n:
        yield (L, n)
