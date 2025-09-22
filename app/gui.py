import os
import json
from typing import List, Dict, Optional

import gradio as gr
import pandas as pd

from .models import Segment
from .dialogue_extraction import extract_all_segments_singlevoice
from .synthesis import batch_synthesize
from .merging import merge_all

OUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "radio_out"))
os.makedirs(OUT_DIR, exist_ok=True)

def _segments_to_df(segs: List[Segment]) -> pd.DataFrame:
    rows = []
    for s in segs:
        rows.append({
            "seq": s.seq,
            "Type": "dialog" if s.kind == "dialog" else "narration",
            "Text": s.text,
            "Emotion hint": s.emo_text
        })
    return pd.DataFrame(rows, columns=["seq", "Type", "Text", "Emotion hint"])

def _df_to_json_str(df: pd.DataFrame) -> str:
    return json.dumps(df.to_dict(orient="records"), ensure_ascii=False, indent=2)

def _check_residual_warning() -> str:
    if not os.path.isdir(OUT_DIR):
        return ""
    wavs = [f for f in os.listdir(OUT_DIR) if f.lower().endswith(".wav")]
    if wavs:
        return "检测到 radio_out 文件夹存在上次生成的残留音频，建议删除后再继续使用。"
    return ""

def _read_txt_file(txt_file: Optional[gr.File]) -> str:
    if not txt_file:
        return ""
    path = txt_file if isinstance(txt_file, str) else txt_file.name
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def _build_voice_map_single(voice_fp: Optional[str]) -> Dict[str, str]:
    """台词与旁白都使用同一个参考音频"""
    if not voice_fp or not os.path.isfile(voice_fp):
        raise ValueError("请先上传参考音频文件。")
    return {"ref": voice_fp}

def _rows_to_segments(rows: List[dict]) -> List[Segment]:
    segs: List[Segment] = []
    for r in rows:
        segs.append(Segment(
            seq=int(r["seq"]),
            kind="dialog" if r["Type"] == "dialog" else "narration",
            text=r["Text"],
            emo_text=r["Emotion hint"],
            start_idx=0,
            meta={}
        ))
    return segs

def on_extract(novel_file, _voice_fp_unused):
    text = _read_txt_file(novel_file)
    if not text.strip():
        return gr.update(), gr.update(), "请先上传 txt 文件。", []
    segs = extract_all_segments_singlevoice(text)
    df = _segments_to_df(segs)
    js = _df_to_json_str(df)
    msg = f"已抓取 {len(segs)} 条"
    return df, js, msg, []

def on_generate_all(segments_json, voice_fp, emo_alpha: float):
    if not segments_json:
        return "请先抓取或粘贴 Segments JSON。", [], []
    try:
        rows = json.loads(segments_json)
    except Exception as e:
        return f"JSON 解析失败：{e}", [], []
    segs = _rows_to_segments(rows)
    voice_map = _build_voice_map_single(voice_fp)
    outs = batch_synthesize(segs, voice_map, emo_alpha, OUT_DIR)
    role_list = [p for (p, _, lbl) in outs if "nar" not in os.path.basename(p)]
    narr_list = [p for (p, _, lbl) in outs if "nar" in os.path.basename(p)]
    return f"生成完成，共 {len(outs)} 条。", role_list, narr_list

def on_generate_one(segments_json, voice_fp, seq_to_gen: int, emo_alpha: float):
    """按 seq 生成单条：仅返回状态文本（不再返回音频预览）。"""
    if not segments_json:
        return "请先抓取或粘贴 Segments JSON。"
    try:
        rows = json.loads(segments_json)
    except Exception as e:
        return f"JSON 解析失败：{e}"
    targets = [r for r in rows if int(r["seq"]) == int(seq_to_gen)]
    if not targets:
        return f"未找到 seq={seq_to_gen}。"
    seg = _rows_to_segments(targets)[0]
    voice_map = _build_voice_map_single(voice_fp)
    outs = batch_synthesize([seg], voice_map, emo_alpha, OUT_DIR)
    p = outs[0][0]
    if seg.kind == "dialog":
        return f"已生成第 {seq_to_gen} 条台词：{os.path.basename(p)}"
    else:
        return f"已生成第 {seq_to_gen} 条旁白：{os.path.basename(p)}"

def on_merge(gap_ms: int):
    merged = os.path.join(OUT_DIR, "merged.wav")
    path = merge_all(OUT_DIR, merged_path=merged, gap_ms=int(gap_ms))
    return f"合并完成（间隔 {gap_ms} ms）：{os.path.basename(path)}", path

def launch_app(lang: str = "zh", port: int = 7861):
    with gr.Blocks(css=".gr-button{font-size:16px}") as demo:
        warn = _check_residual_warning()
        if warn:
            gr.Markdown(f"**提示**：{warn}")

        gr.Markdown("## 听书生成器（基于IndexTTS2）")

        # 输入区
        with gr.Row():
            ref_audio = gr.File(label="上传参考单音色音频", file_types=[".wav", ".mp3", ".flac"])
            novel_txt = gr.File(label="上传小说 TXT", file_types=[".txt"])
            emo_alpha = gr.Slider(0.0, 1.0, value=0.5, step=0.05, label="情绪强度")

        extract_btn = gr.Button("台词抓取（角色台词与旁白）")

        seg_table = gr.Dataframe(
            headers=["seq", "Type", "Text", "Emotion hint"],
            interactive=False, wrap=True, label="抓取结果（只读）"
        )
        # JSON 可编辑
        seg_json = gr.Textbox(label="Segments JSON（可编辑）", lines=12, interactive=True, visible=True)
        status_box = gr.Markdown("")

        # 生成与试听（去掉两个预览 Audio，仅保留文件列表）
        gr.Markdown("### 生成与试听")
        with gr.Row():
            gen_all_btn = gr.Button("一键生成", scale=2)
            seq_to_gen = gr.Number(value=1, label="按序号生成（seq）", precision=0)
            gen_one_btn = gr.Button("生成单条")
        role_audios = gr.Files(label="台词音频列表", interactive=False)
        narr_audios = gr.Files(label="旁白音频列表", interactive=False)

        # 合并
        gr.Markdown("### 合并输出")
        with gr.Row():
            gap_ms = gr.Slider(0, 2000, value=200, step=50, label="合并静音（毫秒）")
            merge_btn = gr.Button("按序号顺序合并 radio_out 中所有音频")
        merged_audio = gr.Audio(label="合并结果预览", interactive=False)

        # 事件绑定
        extract_btn.click(
            fn=on_extract,
            inputs=[novel_txt, ref_audio],
            outputs=[seg_table, seg_json, status_box, role_audios]
        )
        gen_all_btn.click(
            fn=on_generate_all,
            inputs=[seg_json, ref_audio, emo_alpha],
            outputs=[status_box, role_audios, narr_audios]
        )
        # 这里仅返回 status 文本，不再输出两个预览组件
        gen_one_btn.click(
            fn=on_generate_one,
            inputs=[seg_json, ref_audio, seq_to_gen, emo_alpha],
            outputs=[status_box]
        )
        merge_btn.click(
            fn=on_merge,
            inputs=[gap_ms],
            outputs=[status_box, merged_audio]
        )

    demo.queue(api_open=False).launch(server_port=port, share=False)

def app():
    launch_app()

if __name__ == "__main__":
    launch_app()