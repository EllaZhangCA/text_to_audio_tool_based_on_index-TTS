import re
from typing import List, Tuple, Optional
from .models import Segment
from .text_processing import normalize_text

# 支持中英文标点
COLON_CLASS = r'[:：]'
QUOTE_OPEN_CLASS = r'[“"「『]'
QUOTE_CLOSE_CLASS = r'[”"」』]'
SENT_ENDERS = "。！？….!?;；\n"

def _strip_quotes(s: str) -> str:
    return re.sub(rf'{QUOTE_OPEN_CLASS}|{QUOTE_CLOSE_CLASS}', '', s)

def _iter_sentences(text: str) -> List[Tuple[str, int, int]]:
    """返回 (句子文本, abs_start, abs_end)；以 SENT_ENDERS 断句，保留末尾标点。"""
    spans: List[Tuple[str, int, int]] = []
    i, n = 0, len(text)
    buf_start = 0
    while i < n:
        ch = text[i]
        if ch in SENT_ENDERS:
            sent = text[buf_start:i+1]
            if sent.strip():
                spans.append((sent, buf_start, i+1))
            buf_start = i+1
        i += 1
    if buf_start < n:
        tail = text[buf_start:]
        if tail.strip():
            spans.append((tail, buf_start, n))
    return spans

def _find_all_quote_spans(s: str) -> List[Tuple[int, int]]:
    """返回句子 s 中所有引号包裹的 span（含引号）"""
    return [m.span() for m in re.finditer(rf'{QUOTE_OPEN_CLASS}.+?{QUOTE_CLOSE_CLASS}', s)]

def _find_colon_dialog_span(s: str) -> Optional[Tuple[int, int]]:
    """若句子中出现冒号，返回“冒号后内容”的 span（不包含冒号），否则 None。"""
    m = re.search(COLON_CLASS, s)
    if not m:
        return None
    st = m.end()
    if st >= len(s):
        return None
    return (st, len(s))

def extract_all_segments_singlevoice(raw_text: str) -> List[Segment]:
    """
    单声线抓取：
      - 台词：kind="dialog"，text=引号内/冒号后文本，emo_text=text
      - 旁白：kind="narration"，text=该句剩余文本（或整句），emo_text=text
      - 不含 speaker 字段
    """
    text = normalize_text(raw_text)
    segs: List[Segment] = []
    abs_seq = 0

    for sent, absL, absR in _iter_sentences(text):
        sent_dialog_spans = _find_all_quote_spans(sent)
        colon_span = _find_colon_dialog_span(sent) if not sent_dialog_spans else None

        used_local_spans: List[Tuple[int, int]] = []

        # 1) 引号台词（同一句可多段）
        if sent_dialog_spans:
            for (L, R) in sent_dialog_spans:
                content = _strip_quotes(sent[L:R]).strip()
                if not content:
                    continue
                abs_seq += 1
                segs.append(Segment(
                    seq=abs_seq,
                    kind="dialog",
                    text=content,
                    emo_text=content,
                    start_idx=absL + L,
                    meta={"rule": "quote"}
                ))
                used_local_spans.append((L, R))

        # 2) 冒号台词（仅在无引号台词时生效）
        elif colon_span:
            L, R = colon_span
            content = sent[L:R].strip()
            if content:
                abs_seq += 1
                segs.append(Segment(
                    seq=abs_seq,
                    kind="dialog",
                    text=content,
                    emo_text=content,
                    start_idx=absL + L,
                    meta={"rule": "colon"}
                ))
                used_local_spans.append((L, R))

        # 3) 旁白（逐句）
        if used_local_spans:
            mask = [1] * len(sent)
            for L, R in used_local_spans:
                for i in range(L, R):
                    mask[i] = 0
            remaining = "".join(ch for i, ch in enumerate(sent) if mask[i] == 1).strip()
            remaining = re.sub(r'\s+', ' ', remaining)
        else:
            remaining = sent.strip()

        if remaining:
            abs_seq += 1
            segs.append(Segment(
                seq=abs_seq,
                kind="narration",
                text=remaining,
                emo_text=remaining,
                start_idx=absL,
                meta={"rule": "per_sentence"}
            ))

    segs.sort(key=lambda s: s.start_idx)
    for i, s in enumerate(segs, 1):
        s.seq = i
    return segs
