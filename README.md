# Novel-to-Audio (IndexTTS2 GUI)

基于 [index-tts / IndexTTS2](https://github.com/index-tts/index-tts) 的小说转听书工具。
本仓库只包含本项目代码与依赖清单，不包含 IndexTTS 的模型与仓库内容。

> 重要：如果不选择下载右边的release版本的话，请先按 IndexTTS2 官方说明安装好运行环境与模型（含 `checkpoints/`），本项目仅在其之上提供 GUI、台词抽取与批量合成逻辑。

## 功能概览
此项目可以快速将大段文字转换成用指定声线有感情地朗读的有声书

## 运行前置
安装并配置好 **IndexTTS2** 及其依赖。

## 安装依赖
1. 用conda打开你的Index TTS虚拟环境
```bash
conda activate Index-TTS
```
2. 打开本项目文件夹（假设本项目位于D:\txt2radio）
```bash
conda activate Index-TTS
```
3. 安装依赖
```bash
pip install -r requirements.txt
```
## 启动方式
```bash
python main.py
```
默认在 `http://127.0.0.1:7861` 启动，如需变更，可以在gui.py的最底下更改。

启动main.py后通过浏览器打开http://127.0.0.1:7861

## 使用方式
在角色名单里写入主要角色的名字，上传角色参考音频 抓取台词etc...教学视频制作中。
## 合规与授权
- “本项目包含的模型文件来源于 bilibili indextts2，其使用必须遵守 bilibili Model Use License Agreement。本项目代码部分则按MIT发布。”
- 使用参考音频进行音色克隆时，请确保你拥有合法授权；商业用途请遵守当地法律法规与平台政策。本项目不对使用者的任何行为负责。
