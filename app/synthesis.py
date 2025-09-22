import os
from typing import List, Tuple, Dict

from .models import Segment
from .tts_wrapper import TTSWrapper

def _label_for(seg: Segment) -> str:
    return f"{seg.seq:05d}_{'dlg' if seg.kind=='dialog' else 'nar'}"

def batch_synthesize(
    segments: List[Segment],
    voice_map: Dict[str, str],   # 单音色版：传入 {"ref": <参考音频路径>} 或 {"旁白":..., "角色":...} 也行
    emo_alpha: float,
    out_dir: str
) -> List[Tuple[str, int, str]]:
    """
    批量合成（单音色）：忽略 speaker，统一使用同一个参考音频。
    返回 [(输出路径, seq, label), ...]
    """
    os.makedirs(out_dir, exist_ok=True)
    # 取第一个可用的参考音频
    ref_audio = None
    for k in ("ref", "旁白", "角色"):
        if k in voice_map and voice_map[k]:
            ref_audio = voice_map[k]
            break
    if not ref_audio:
        # 如果 dict 里只有一个值，也取它
        if voice_map:
            ref_audio = list(voice_map.values())[0]
        else:
            raise ValueError("未提供参考音频。")

    tts = TTSWrapper()
    results: List[Tuple[str, int, str]] = []

    for seg in segments:
        label = _label_for(seg)
        out_path = os.path.join(out_dir, f"{label}.wav")
        tts.synth(
            speaker_audio=ref_audio,
            text=seg.text,
            out_path=out_path,
            emo_text=seg.emo_text,
            emo_alpha=emo_alpha,
        )
        results.append((out_path, seg.seq, label))

    return results
