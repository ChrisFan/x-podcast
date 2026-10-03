# 睡眠播客本地 MVP

> 这是最初本地音频实验的保留说明；项目现已扩展为 App、Web、服务端和 MCP，当前入口见根目录 README。下面命令仍用于独立本地制作与混音。

提前准备一份中文脚本，在本地调用阿里云百炼 TTS，下载人声，再加入停顿、环境声与渐弱结尾，导出可直接试听的 WAV。当前样本为《雨夜旅馆 · 靠窗的房间》：10 段，930 字符，后半段逐渐减少叙述并拉长段间停顿。

本阶段验证文案、声音和节奏能否形成舒服的睡前收听体验。不开发 App、账户、MCP 或 Skill；脚本输入与音频制作相互独立，之后可以接入这些入口。

2026-10-02 首次真实 API 实跑已完成：预览版 76.3 秒，完整版 371.88 秒（约 6 分 12 秒），24 kHz / 16-bit / 单声道；完整版峰值 -4.56 dBFS，未检测到削波。主观听感尚待用户试听，技术指标不代表助眠效果。当前工作目录已配置 `.venv`，可以直接运行 `.venv/bin/python podcast.py check`。

## 安装和配置

Python 3.10 或以上：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

首次使用时，将 `.env.example` 复制为 `.env`，填入百炼 API Key 和所属地域。已有 `.env` 时直接编辑，不要覆盖。`.env` 已加入忽略规则。程序不会执行文件中的 shell 表达式，也不会输出密钥、完整 API 错误响应或临时音频下载链接。

```dotenv
DASHSCOPE_API_KEY=你的百炼APIKey
DASHSCOPE_REGION=beijing
```

本地环境变量优先于 `.env`；地域可以是 `beijing` 或 `singapore`。文本模型使用的 `/compatible-mode/v1` 不是本项目 TTS 接口。此版本按 Qwen-TTS 官方文档使用所属地域的 `/api/v1/services/aigc/multimodal-generation/generation`，不使用业务空间专属的文本生成 URL。

## 使用

```sh
# 校验脚本和配置，不请求 API
python podcast.py check

# 前两段试听；会调用阿里云 API，产生该账户的实际用量
python podcast.py generate --preview

# 全篇；会复用已经成功下载的相同段落
python podcast.py generate

# 更换声音重新生成，属于新的 API 用量
python podcast.py generate --preview --voice Ethan

# 修改停顿或背景声电平后，只使用缓存重新混音；不会请求 TTS
python podcast.py render
```

每次输出到 `output/<脚本id>-preview或full-<唯一编号>/`，保留历史试听版本：

- `podcast.wav`：人声加背景声。
- `narration.wav`：同一时间线的纯人声对照版，包含相同停顿和结尾留白。
- `script.json`：本次制作所用脚本快照。
- `report.json`：真实时长、采样率、峰值、削波数、各段时间、API request ID 和返回用量。

macOS 可以双击 WAV，或运行 `afplay output/具体目录/podcast.wav`。

## 脚本和声音设置

`scripts/rainy-inn.json` 是制作的唯一输入。`scripts/rainy-inn.txt` 是初版正文的阅读副本；修改阅读副本不会改变制作结果。

- `text` 只放需要朗读的正文，每段最多 600 字符。
- `instructions` 放朗读风格要求；`label` 和 `pause_after_seconds` 不会被念出。
- 默认使用 `qwen3-tts-instruct-flash-2026-01-26` 和系统女声 `Serena`。这是本次实验的选择，不是对所有阿里云声音模型的比较结论。
- 前段间隔为 3 至 6 秒，中后段为 8 至 18 秒，最后保留 60 秒背景声，末尾 30 秒渐弱；预览版只有 8 秒结尾。
- 当前没有强制拉伸语音或保证目标语速；自然语言风格指令是否奏效需要试听。成片时长以实际合成结果为准。

背景声默认是**本地合成的柔和有色噪声占位**，不是实录雨声，也不是阿里云生成的环境音。它用于先验证混音和渐弱链路，真实雨感不在此占位音的质量承诺范围内。可以通过 `--ambience-wav /绝对路径/rain.wav` 使用自备环境声，要求 16-bit PCM WAV、采样率与人声一致且时长不短于成片；本版不自动循环或重采样。

`mix.ambience_dbfs` 控制背景声 RMS 电平，默认 -38 dBFS；它不是 LUFS 或实际耳机音量。人声按活跃样本 RMS 做有限增益调整，边缘有 8 毫秒淡入淡出，混音峰值限制为不高于 -1 dBFS。每段原始音频仍保存在缓存中。

## 缓存与失败

缓存键包含地域端点、模型、声音、正文和朗读指令。修改这些字段会重新调用 TTS；只调整本地停顿、环境声或渐弱不会重新生成。临时音频链接不写入报告，成功后立即下载 WAV。

API 失败或超时不自动重试，以免不确定的请求重复计费。修复问题后可以重跑，已下载段落会复用；如果远端已合成但下载失败，重跑该段可能再次计费。`report.json` 记录用量，不推算账单价格。

## 验证

```sh
python -m unittest discover -s tests -v
```

离线测试覆盖缓存与更换声音、禁止离线命令调用 API、时间线停顿、结尾渐弱、削波约束、采样率不一致、脚本长度、错误信息隐藏与下载域名。测试中的正弦波只存在于临时目录，不能代替真实 TTS 试听。

试听时先关注三个问题：声音是否让人愿意继续听，停顿是否自然，背景声是否抢注意力。可先听预览版，再听全篇后半段与结尾。报告默认标注主观试听待完成，播放时长和技术检查不能证明助眠效果。

## 接口依据

接口核对日期：2026-10-02。

- [阿里云 Qwen-TTS API](https://help.aliyun.com/zh/model-studio/qwen-tts-api)
- [非实时语音合成与指令控制](https://help.aliyun.com/zh/model-studio/non-realtime-tts-user-guide)
- [Qwen-TTS 系统音色](https://help.aliyun.com/zh/model-studio/qwen-tts-voice-list)
