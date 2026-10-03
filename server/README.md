# 夜航服务端与制作台

Python 3.13 + FastAPI + PostgreSQL。Web 制作台同源托管于 `/podcast/`，API `/podcast/api`。单进程内含一个串行真实阿里云 TTS 工作线程；禁止使用多个 uvicorn workers 或同时运行第二个服务实例。连接池最多 3 个连接。

## 配置与运行

使用项目 `.venv/bin/pip install -r server/requirements.txt`。由迁移 owner 在专属 `aipodcast` 数据库执行 `server/schema.sql`，再给 `aipodcast_runtime` 所有 public 表 SELECT/INSERT/UPDATE/DELETE、所有 sequence USAGE/SELECT。数据库迁移不能由 runtime 自动执行。

环境变量：

- `DATABASE_URL`：runtime PostgreSQL DSN，必须配置。
- `PODCAST_PUBLIC_BASE_URL`：默认 `http://127.0.0.1:3211/podcast/api`，部署应设置公开 HTTPS API URL。
- `PODCAST_DATA_DIR`：持久化数据目录，默认 `output/service`。仅服务用户可读写，必须随数据库一起备份。
- `DASHSCOPE_API_KEY` / `DASHSCOPE_REGION`：真实阿里云 TTS；region 为 beijing/singapore。也可从根目录 `.env` 加载。
- `PODCAST_INVITE_CODE`：配置后注册必须提供相同邀请码；未配置时开放注册。
- `FFMPEG_BINARY`：可选 ffmpeg 路径，否则从 PATH 查找；可用时生成 64 kbps MP3，否则保留 WAV。

运行：`python -m uvicorn server.app:app --host 127.0.0.1 --port 3211 --workers 1`。反向代理保留 `/podcast/` 前缀。`GET /podcast/api/health` 同时检查数据库与工作线程。HTTP Range 由 Starlette FileResponse 提供（授权后）。Web 使用 Bearer 拉取压缩音频为本地 blob 再播放，原生客户端可使用授权 Range。

## 生成与恢复

所有脚本由 Pydantic 校验；`GET /catalog` 为权威 JSON Schema、设置范围、样例。最多 20 段、每段 600 字符、总共 2400 字符；最多 200 个未删除作品、每账户最多 3 个活跃任务。128 KiB 请求上限。只开放已接入的模型、Serena/Ethan、中文、雨夜旅馆场景。环境声为合成雨声占位，非实地录音；不承诺助眠疗效。

保存草稿不会计费。generate/retry 要求 UUID request_id；账户范围去重，跨作品复用同一 id 返回 409。job 对作品有唯一活跃索引。取消/删除在每个生成阶段检查 job 身份，旧任务不会复活新重试。正在供应商侧执行的请求无法撤销，仍可能计费。段落缓存按用户隔离，重试复用成功下载的音频。服务重启将 generating/mixing 标成 failed，手动重试以避免自动重复计费；queued 保留并恢复。运行期间数据库暂时断开时，工作线程保留当前任务并在连接恢复后仅补写失败状态，不会再次调用 TTS；期间取消或删除的任务不会被复活。

删除为软删除，立即撤销访问但尚未自动清理历史文件；MVP 运维需监测磁盘并安排保留策略。API session 有效 30 天，哈希保存；API token 仅首次显示、支持撤销，无过期日。API token 不允许创建/列出其他 token。密码使用独立 salt 的 scrypt；MVP 无邮箱验证、找回密码或账户删除界面。邀请制试用建议由管理员协助账户问题。

## 验证

`DATABASE_URL` 指向专用测试 PostgreSQL 后执行。当前部署 SSH 密钥禁止端口转发，因此本机 `.local/server.env` 的隧道示例不能直接连接 ECS；云端数据库测试需在服务器运行，并先停止本 App 工作线程，结束后恢复服务：

```
.venv/bin/python -m unittest server.test_validation server.test_integration -v
node --check web/app.js
```

测试通过真实 PostgreSQL + HTTP TestClient 验证隔离、范围读取、持久化、取消/删除、防复活、重试、token 撤销、输入限制和幂等。只有测试内音频提供者被替换为短波形；生产始终调用根目录 `podcast.get_clip` 的阿里云接口。测试只清理自身随机账号。不要对正在运行工作线程的数据库并行执行本测试（启动恢复会影响在制任务）。
