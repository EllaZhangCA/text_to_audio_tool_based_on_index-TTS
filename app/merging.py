import os
import re
from typing import List, Optional
import soundfile as sf
import numpy as np

def _sorted_wavs_by_seq(out_dir: str) -> List[str]:
    files = [f for f in os.listdir(out_dir) if f.lower().endswith(".wav")]
    def key(f):
        m = re.match(r"(\d+)", f)
        return int(m.group(1)) if m else 10**9
    return [os.path.join(out_dir, f) for f in sorted(files, key=key)]

def merge_all(out_dir: str, merged_path: Optional[str] = None, gap_ms: int = 200) -> str:
    """
    将 out_dir 下的 wav 按文件名前缀的数字序号合并。
    gap_ms: 片段之间插入的静音，毫秒。
    """
    wavs = _sorted_wavs_by_seq(out_dir)
    if not wavs:
        raise FileNotFoundError("radio_out 目录下没有可合并的音频。")

    audio_all = []
    sr0 = None
    for i, path in enumerate(wavs):
        data, sr = sf.read(path, dtype="float32", always_2d=True)
        if sr0 is None:
            sr0 = sr
        elif sr != sr0:
            # 简单处理：若采样率不一致，做线性插值到 sr0（单声道/立体声都可以）
            # 为了简单和稳健，可在你的环境中保证 IndexTTS2 输出恒定采样率，这段很少触发
            import numpy as np
            ratio = sr0 / sr
            new_len = int(round(data.shape[0] * ratio))
            x_old = np.linspace(0, 1, num=data.shape[0], endpoint=False)
            x_new = np.linspace(0, 1, num=new_len, endpoint=False)
            data = np.stack([np.interp(x_new, x_old, data[:, ch]) for ch in range(data.shape[1])], axis=1).astype("float32")

        audio_all.append(data)
        if i != len(wavs) - 1 and gap_ms > 0:
            gap_samples = int(sr0 * gap_ms / 1000.0)
            audio_all.append(np.zeros((gap_samples, data.shape[1]), dtype="float32"))

    merged = np.vstack(audio_all)
    if not merged_path:
        merged_path = os.path.join(out_dir, "merged.wav")
    sf.write(merged_path, merged, sr0, subtype="PCM_16")
    return merged_path
