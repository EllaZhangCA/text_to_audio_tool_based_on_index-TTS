import os
from typing import Optional
from .config import DEFAULT_EMO_ALPHA

ENV_CKPT = "INDEXTTS_CHECKPOINTS"  # 指向包含 config.yaml 的目录

class MissingIndexTTS(Exception):
    pass

def _to_bool(v: Optional[str], default: bool) -> bool:
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")

class TTSWrapper:
    """
    - 优先使用构造参数 checkpoints_dir，其次用环境变量 INDEXTTS_CHECKPOINTS，最后回退 D:\\index-tts\\checkpoints
    - 只调用 IndexTTS2.infer()
    """
    def __init__(self, checkpoints_dir: Optional[str] = None):
        try:
            from indextts.infer_v2 import IndexTTS2
        except Exception as e:
            raise MissingIndexTTS("未找到 IndexTTS2，请先安装并确保可导入 indextts.infer_v2。") from e

        ckpt_dir = os.path.abspath(
            checkpoints_dir or os.environ.get(ENV_CKPT) or r"D:\index-tts\checkpoints"
        )
        cfg_path = os.path.join(ckpt_dir, "config.yaml")
        if not os.path.isfile(cfg_path):
            raise RuntimeError(
                f"未找到配置文件：{cfg_path}\n"
                f"请在 GUI 顶部填写正确 checkpoints 目录，或设置环境变量 {ENV_CKPT}。"
            )

        use_fp16 = _to_bool(os.environ.get("INDEXTTS_USE_FP16"), True)
        use_cuda_kernel = _to_bool(os.environ.get("INDEXTTS_USE_CUDA_KERNEL"), True)
        use_deepspeed = _to_bool(os.environ.get("INDEXTTS_USE_DEEPSPEED"), True)

        self.tts = IndexTTS2(
            cfg_path=cfg_path,
            model_dir=ckpt_dir,
            use_fp16=use_fp16,
            use_cuda_kernel=use_cuda_kernel,
            use_deepspeed=use_deepspeed,
        )

    def synth(self, speaker_audio: str, text: str, out_path: str,
              emo_text: Optional[str] = None, emo_alpha: float = DEFAULT_EMO_ALPHA) -> str:
        if not speaker_audio or not os.path.isfile(speaker_audio):
            raise FileNotFoundError("参考音频未选择或路径不存在。")
        kwargs = dict(spk_audio_prompt=speaker_audio, text=text, output_path=out_path, verbose=False)
        if emo_text and emo_text.strip():
            kwargs.update(dict(use_emo_text=True, emo_text=emo_text, emo_alpha=float(emo_alpha)))
        self.tts.infer(**kwargs)
        return out_path
