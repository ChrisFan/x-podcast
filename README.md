# 夜航 · Night Harbor

一个可真实使用的睡眠播客 MVP：在 Web、iPhone 或 MCP 保存脚本，云端调用阿里云生成语音并混入环境声，成片进入同一账户的作品库。提前创作、睡前收听；保存草稿不产生 TTS 用量，点击制作或重试才会调用供应商。

## 开始体验

- **iPhone TestFlight Beta**：`0.1.0 (1)` 已上传并处理为 Ready to Test，见 [Beta 发布记录](docs/BETA-RELEASE.md)。已向指定测试邮箱发送邀请，App Store Connect 状态为 Invited，等待真机安装。
- **Web 制作台**：https://alu-designer.pawlpixel.com/podcast/
- **体验账户与邀请码**：本机私密文件 [.local/ACCESS.md](.local/ACCESS.md)。可用现成账户播放已生成样片，或邀请注册独立账户。不要公开该文件。
- **iPhone 原生工程**：[ios/NightHarbor.xcodeproj](ios/NightHarbor.xcodeproj)。Xcode 打开，选 NightHarbor 和 iPhone 模拟器运行；默认已连接云端。见 [iOS 说明](ios/README.md)。真机需要自己的开发者签名。
- **MCP**：远程入口 `https://alu-designer.pawlpixel.com/podcast/mcp`，支持个人 Bearer 令牌和 stdio；在 Web「偏好与连接」创建令牌。见 [配置说明](mcp/README.md) 与 [创作 Skill](skills/night-harbor/SKILL.md)。当前没有 OAuth，未验收 ChatGPT 内直接安装。

体验账户有《雨夜旅馆 · 云端首夜》（374.44 秒）及 MCP 制作的短样片，都是实际阿里云调用生成。首次播放先下载 MP3；iPhone 缓存后可离线收听。

## 产品流程

1. 在现成模型工具中按 MCP 提供的 JSON Schema 与创作指导生成脚本，或先用内置范例。
2. 保存或导入脚本，选择声音、环境声电平、停顿与结尾留白，校验后存为草稿。
3. 确认制作，依次显示排队、录制、混音、就绪；失败可见，支持取消、手动重试和删除。
4. Web 或 iPhone 收听；iPhone 提供进度、后台播放、离线缓存、睡眠定时和跨端进度同步。

当前开放雨夜旅馆、中文、Serena/Ethan 两种声音，最多 20 段、每段 600 字符、总计 2400 字符。环境声是合成噪声占位，尚未做真实雨声素材库或主观睡眠效果验证。界面不内置文案生成模型。

## 代码与运行

| 目录 | 用途 |
| --- | --- |
| `ios/` | SwiftUI 原生 iPhone App，iOS 17+，无第三方依赖 |
| `server/` | FastAPI、PostgreSQL、账户与作品生命周期、串行 TTS worker |
| `web/` | 同源制作台、JSON 编辑导入、作品库与播放器 |
| `mcp/`、`skills/` | MCP SDK 服务、参数及格式发现、模型创作指导 |
| `podcast.py`、`scripts/` | 原始本地 TTS、段落缓存、混音与测试文案 |
| `deploy/`、`acceptance/` | 专属 ECS 部署、备份恢复、实际验收脚本与证据 |

后端使用 Python 3.13；按 [服务端说明](server/README.md) 配置专属数据库和私密环境变量。生产依赖快照在 `deploy/requirements-linux.lock`。API 与 MCP 分别只绑定 `127.0.0.1:3211/3212`，由 Nginx HTTPS 代理。单进程、单 worker，不能横向启动多个实例。

```sh
# 本地音频逻辑；不访问供应商
.venv/bin/python -m unittest discover -s tests -v
# MCP SDK 传输与账户隔离；使用 MCP 自己的依赖环境
mcp/.venv/bin/python -m unittest discover -s mcp/tests -v
```

后端数据库集成测试需用专用测试库，或停止本 App 生产 worker 后在 ECS 维护窗口运行；不能与生产 worker 共用同一库并发测试。原始本地生成命令保留在 [本地音频 MVP 说明](docs/LOCAL-AUDIO.md)。

## 验收与运维

见 [验收记录](docs/ACCEPTANCE.md) 和 [部署恢复说明](docs/DEPLOYMENT.md)。已验证真实云端生成、Web 播放、MCP 两种传输、账户隔离、任务中断恢复、数据库与音频还原；iPhone 实测记录在验收文档。

本版适合邀请制验证：没有邮箱验证、找回密码、OAuth、App Store 发布或完整配额计费系统。软删除立即撤销访问，历史音频尚未自动清理。备份在同一台 ECS，不能覆盖整机丢失。音频技术验收不等于主观听感或助眠效果验证。
