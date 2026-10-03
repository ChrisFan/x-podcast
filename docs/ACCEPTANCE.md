# 夜航 MVP 验收记录

日期：2026-10-02。三端共享真实账户与作品库，生成调用阿里云，数据在独立 PostgreSQL。公网入口：https://alu-designer.pawlpixel.com/podcast/ 。当前部署运行代码与本地 SHA256 已核对一致，详见 `acceptance/deployed-source.json`。

| 范围 | 实际结果 | 证据 |
| --- | --- | --- |
| iPhone 原生 | SwiftUI 构建、iPhone 17 Pro 模拟器启动、Keychain 真实登录、云端草稿创建/删除、深色睡眠界面通过 | `ios/evidence/native-acceptance.json`、`tonight.png`、`editor.png` |
| iPhone 收听 | 真实 MP3 下载播放、跳转、后台时钟继续增长、20.24 秒短片自然到尾停止、选择本集结束定时通过 | `ios/evidence/live-player.png`、`end-of-track-stopped.png` |
| iPhone 离线与隔离 | 重启 App 后拒绝全部网络请求，真实缓存播放时钟增长；恢复联网后退出登录，缓存作品不再显示 | `ios/evidence/offline-cached-player.png`、`logout-hides-cached-library.png` |
| Web | 真实登录、同账户作品、编辑保存草稿、删除、MP3 播放时钟、seek、定时菜单、退出停止播放通过 | `acceptance/web-live-results.json` 与 Web PNG |
| Web 移动布局 | 390×844 无横向溢出；浏览器无 JavaScript 错误 | `acceptance/web-mobile.png` |
| 账户 | 邀请注册/登录、无认证拒绝、账户偏好保存、个人 MCP token 创建与撤销通过 | `acceptance/api-live-results.json` |
| 云端生成 | 实际生成《雨夜旅馆 · 云端首夜》374.44 秒，draft → queued → generating → mixing → ready，各阶段事件可查询 | `acceptance/api-live-results.json` |
| 音频与进度 | 成片授权 Range 206、MP3 解码播放、进度写入并读回通过 | API 与 Web live 证据 |
| 生命周期 | 供应商失败后重试、取消/删除期间完成不复活、账户级 request_id 幂等、跨作品冲突拒绝、数据库断连后只补写失败不重发 TTS，通过真实 PostgreSQL 集成测试 | `server/test_integration.py`，`acceptance/test-results.json` |
| 权限 | 双账户作品详情/音频/删除/取消越权均拒绝；runtime 非管理员、无 schema CREATE、两个业务库互相无 CONNECT | `acceptance/api-live-results.json`、`database-isolation.json` |
| MCP 发现 | 实际 SDK initialize，16 tools / 4 resources / 1 prompt，返回实时 schema、两种声音、引导与偏好，通过 HTTP 及 stdio | `mcp/evidence/real-http.json`、`real-stdio.json` |
| MCP 制作 | 真实短脚本验证、草稿创建、生成、幂等重发、就绪事件及授权音频 Range 通过；成片 20.24 秒保留在体验账户 | `mcp/evidence/real-http.json` |
| MCP 隔离 | 真实 SDK transport + 隔离假 API 测试：缺失/无效/撤销令牌、并发不同账户、参数与路径注入通过 | `mcp/tests/test_transport.py` |
| 服务重启 | 真实供应商制作中重启，任务转失败并保持等待；显式 retry 成片，测试作品清理；旧账户/成片/文案/进度不丢失 | `acceptance/restart-results.json` |
| 部署 | HTTPS；API/MCP/DB 仅监听 loopback；独立进程、用户与私密配置；连接池最多 3 | `acceptance/infrastructure-health.txt`、`docs/DEPLOYMENT.md` |
| 共享 ECS | AluminumDesigner 健康；Waterline 与 Umami 容器仍 healthy；未重启共用数据库或其他 App 服务 | `acceptance/infrastructure-health.txt` |
| 备份恢复 | 独立 dump + 音频 + 配置 + 角色模板 + 校验和；临时库恢复后核对 2 份就绪作品、主脚本文本指纹、表 owner/ACL、6 个 MP3 哈希，通过后清理临时库 | `acceptance/restore-results.json` |

自动化测试：本地音频逻辑 7 项，后端输入及数据库集成 13 项，MCP 传输 3 项，iOS 单测 6 项均通过；另有 iOS 首次进入 UI 测试及 89 秒真实云端完整 UI 测试通过。数据库测试在停止本 App worker 的维护窗口执行，测试替身音频与真实供应商验收分别记录。使用错误的根目录 Python 跑 MCP 测试曾因缺少 SDK 失败；切换其专属 `mcp/.venv` 后 3 项通过。

## 验证边界

- Web 实际 UI 验收覆盖登录、草稿、库和播放；邀请注册、制作、失败与重试由真实 HTTP/MCP 及数据库测试覆盖，没有逐一在每个客户端重复付费制作。
- iPhone 已验证“本集结束”停播；15/30/45/60 分钟倒计时及末尾 10 秒渐弱已实现，未等待完整定时周期实测。
- iPhone 为模拟器 MVP；真机签名、锁屏遥控实机、整夜播放、TestFlight/App Store 均非本轮发布成果。后台播放不等于已完成真机锁屏验收。
- Web 和 App 首次收听先下载 MP3；不是边生成边播放。当前只有一种场景、两种声音，环境声为合成噪声占位。
- MCP 支持静态 Bearer HTTP 与 stdio；未实现 OAuth，未验证 ChatGPT 内直接安装。
- 备份恢复在同机已有角色环境测试，尚无异地备份或整机重建验收。代码回退流程已记录，没有数据库 schema 版本回退演练。
- 功能可用于邀请制体验；尚无邮箱验证、密码找回、完整计费配额、音频自动清理。真实生成与播放器时钟通过不表示已验证听感或助眠效果。
