# 夜航部署与恢复

2026-10-02 已部署到共享 ECS `120.55.99.193`，当前运行 release `/opt/aipodcast/releases/20261002-222336`。独立部署责任属于 AIPodcast；不要用其他项目的安装器清理或重建共用数据库。

| 资源 | 当前值 |
| --- | --- |
| HTTPS | `https://alu-designer.pawlpixel.com/podcast/` |
| API / MCP | `/podcast/api` / `/podcast/mcp` |
| 服务 | `aipodcast.service` / `aipodcast-mcp.service` |
| 本机端口 | 3211 / 3212；不对公网直连开放 |
| 系统用户 | `aipodcast`，无交互 shell |
| 程序 | `/opt/aipodcast/current` → `releases/<timestamp>` |
| Python | `/opt/aipodcast/venv/bin/python`（3.13.16） |
| 数据 | `/var/lib/aipodcast`，包括分账户缓存和成片 |
| 私密配置 | `/etc/aipodcast/api.env`，root、0600 |
| PostgreSQL | 共用容器 `aluminum-cloud-test-db`，loopback 55439，独立库 `aipodcast` |
| 数据库角色 | 迁移 `aipodcast_owner`；运行 `aipodcast_runtime`，最多 3 个连接 |
| 备份 | `/var/backups/aipodcast/snapshot-*`，7 天，文件私密 |
| 定时备份 | `aipodcast-backup.timer`，北京时间每天 03:40，随机延迟最多 5 分钟 |
| 资源限制 | API 内存 600 MiB / CPU 100%；MCP 128 MiB / CPU 30% |

SSH：`ssh -i ~/.ssh/alu-designer-deploy -o IdentitiesOnly=yes -o BatchMode=yes -o StrictHostKeyChecking=yes deploy@120.55.99.193`。当前部署密钥禁止 TCP 转发；不要依赖本机 55440 隧道，也不要为此修改共享 SSH 安全设置。

## 发布与回退

`deploy/release.py` 只打包代码，不包含 `.env`、`.local`、音频或私钥。无 `--publish` 时上传并切换 `current`，不重启运行进程；`--publish` 会重启本 App API/MCP、安装 Nginx snippet 并测试、reload Nginx。执行前需在维护窗口确认无正在制作的任务；重启会把录制/混音中的任务标为失败，等待用户手动重试。

初次配置由 `deploy/provision.py` 完成；它不是日常发布命令。数据库迁移必须以 owner 执行，再给 runtime 必要表权限；runtime 无 schema CREATE，无其他 App 数据库 CONNECT。生产 worker 只能运行一个进程。

Nginx 独立 snippet 为 `/etc/nginx/snippets/aipodcast.conf`，在原站点 TLS vhost 的 root 后 include。原配置备份在 `/etc/nginx/aipodcast-backups`。已将同一 include 写入 `pawlpixel-studio/nginx/pawlpixel.conf`，避免后续该站点部署丢失路由。不要覆盖整份共享 Nginx 配置。

回退只针对本 App：读取 `/etc/aipodcast/previous-release.txt`，核实路径属于 `/opt/aipodcast/releases/`、版本与数据库兼容，停止本 App API/MCP，将 `current` 指回该版本，安装该版本自身的 systemd units、daemon-reload，然后启动并检查 `/podcast/api/health`。代码回退不回退数据库，禁止恢复整个共用 PostgreSQL 实例。此轮已验证重启与持久化；未执行带 schema 变更的版本回退演练。

## 备份与恢复

手动运行 `sudo systemctl start aipodcast-backup.service`。每个快照包含：数据库 custom dump、账户音频与段落缓存、私密配置、专属角色创建模板、release 路径、SHA256SUMS。`roles.sql` 不保存密码；runtime 密码来自受保护的配置，owner 密码应重新设置。备份里包含敏感数据，不上传公开仓库。

本地运行 `.venv/bin/python deploy/restore_check.py`，会在服务器创建唯一命名的 `aipodcast_restore_*` 临时库，保留 owner 与 ACL 恢复 dump，比较主样片文案指纹、统计就绪作品、验证 runtime 权限，并还原音频文件逐一比较 SHA256；最后删除自己的临时库与提取目录。不会覆盖生产数据或其他 App。

整机重建时先准备相同 PostgreSQL 主版本和独立角色，审核后执行角色模板，建立 `aipodcast` 库并收紧 CONNECT，恢复 dump、assets、config，恢复文件 owner/权限与指定 release 的依赖，再启动服务。角色不在普通 pg_dump 内，不能省略。当前恢复演练使用同实例已有角色，未模拟整机重建；尚无异地备份或 RPO/RTO 承诺。

取消不能撤回已经发往供应商的请求。重试复用已下载段落；若供应商已完成但尚未下载，手动重试可能重新产生该段用量。删除为软删除，历史文件保留，需持续监测磁盘。

## 共享主机约束

不得删除或重启共用 PostgreSQL 容器/卷，不使用全局 Docker prune；不修改 AluminumDesigner、Waterline、Umami 的账户、配置、服务或备份。当前只读健康快照在 `acceptance/infrastructure-health.txt`，当前数据库隔离证据在 `acceptance/database-isolation.json`。资源快照只说明检查时状态，不构成并发容量承诺。
