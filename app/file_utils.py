import os
from typing import List, Tuple

AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}

def list_audio_files(folder: str) -> List[Tuple[int, str]]:
    """列出输出目录下的音频，并尝试从文件名前缀提取 seq。"""
    res = []
    if not os.path.isdir(folder):
        return res
    for name in os.listdir(folder):
        ext = os.path.splitext(name)[1].lower()
        if ext not in AUDIO_EXTS:
            continue
        seq = 10**9
        stem = os.path.splitext(name)[0]
        try:
            seq = int(stem.split("_", 1)[0])
        except Exception:
            pass
        res.append((seq, os.path.join(folder, name)))
    res.sort(key=lambda x: x[0])
    return res
