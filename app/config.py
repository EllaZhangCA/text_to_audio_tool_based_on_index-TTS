import os

# 输出目录
OUT_DIR = os.path.abspath(os.environ.get("RADIO_OUT_DIR", "radio_out"))

# 情绪强度（传给 IndexTTS2 的 emo_alpha）
DEFAULT_EMO_ALPHA = float(os.environ.get("DEFAULT_EMO_ALPHA", "0.6"))

# 合并时每段间的静音（毫秒）
DEFAULT_SILENCE_MS = int(os.environ.get("DEFAULT_SILENCE_MS", "200"))
