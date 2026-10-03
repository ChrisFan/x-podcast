# 夜航 MCP

Python 3.11+。通过同一账户 HTTP API 管理真实播客生命周期，不持有 TTS 密钥。基于 [官方 Python MCP SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0)，固定 SDK 1.30.0。

```sh
python3 -m venv mcp/.venv
mcp/.venv/bin/pip install -r mcp/requirements.txt
```

在夜航 Web「设置」创建访问令牌，私密配置到 MCP 客户端。请勿贴在聊天或提交到 Git。标准 stdio 客户端配置（替换绝对路径和令牌占位符）：

```json
{
  "mcpServers": {
    "night-harbor": {
      "command": "/absolute/path/AIPodcast/mcp/.venv/bin/python",
      "args": ["/absolute/path/AIPodcast/mcp/server.py"],
      "env": {
        "AIPODCAST_API_URL": "https://alu-designer.pawlpixel.com/podcast/api",
        "AIPODCAST_TOKEN": "<personal-access-token>"
      }
    }
  }
}
```

只 stdout 输出 MCP 协议；日志走 stderr。不自动读取仓库 .env 或提取 TTS 凭据。HTTP API 必须 HTTPS，只有 loopback 允许 HTTP。

远程服务：

```sh
AIPODCAST_API_URL=http://127.0.0.1:3211/podcast/api mcp/.venv/bin/python mcp/server.py --transport streamable-http
```

绑定 `127.0.0.1:3212`，端点 `/podcast/mcp`，使用无会话 Streamable HTTP。反向代理需保留 Authorization、Host 与请求路径，公开端必须 HTTPS；不要用全局账户令牌启动远程 MCP。每个请求使用客户端自己的 `Authorization: Bearer ...` 并实时调用 `/auth/me` 校验，工具继续携带该账户的令牌，所有权由 API 再检查。令牌撤销下次请求立即生效。公共默认主机是 `alu-designer.pawlpixel.com`；新增主机/浏览器 Origin 时分别配置 `AIPODCAST_MCP_ALLOWED_HOSTS` / `AIPODCAST_MCP_ALLOWED_ORIGINS` 逗号列表，不关闭 DNS 重绑定保护。

本 MVP 未实现 OAuth 授权发现或客户端注册，适用于可配置 stdio 或 Bearer HTTP 的 MCP 客户端；未宣称在 ChatGPT 产品内安装通过。Skill 在 `skills/night-harbor/SKILL.md`，也由 `nightharbor://authoring-guide` resource 提供给模型；其他 resources 提供实时 JSON Schema、设置、范例，`prepare_sleep_podcast` prompt 提供引导。

工具包括 catalog、偏好读写、服务端脚本验证、创建/修改草稿、列表/状态/历史、生成/重试/取消/删除、听取进度、音频端点。生成与重试显式接受 request_id 以免网络重发重复付费。草稿创建非幂等，未知结果先按 script.id 查列表恢复。音频 URL 不含凭据，必须账户授权；普通分享链接不提供私人音频。

验证：

```sh
mcp/.venv/bin/python -m unittest discover -s mcp/tests -v
```

测试启动隔离假 API 和真实 MCP SDK stdio/HTTP transport，检查握手、工具/resource/prompt、付费请求 ID、认证与不同账户隔离。实际服务验收由项目 `acceptance/` 记录；假 API 测试不证明真实 TTS 成片。

实际服务的 SDK 验收工具（环境变量配置同上）：

```sh
# 只读检查实际服务的工具、规范和偏好
mcp/.venv/bin/python mcp/smoke.py
# 经授权的一次真实短音频制作，保留作品供 App 验收
mcp/.venv/bin/python mcp/smoke.py --remote https://alu-designer.pawlpixel.com/podcast/mcp --generate
# 对已有成片检查认证音频 Range 响应，不产生新 TTS 调用
mcp/.venv/bin/python mcp/smoke.py --podcast-id <podcast-uuid>
```

`--generate` 会产生真实 TTS 调用和费用；脚本不会自动重试失败生成。输出只含验收状态、公开 URL 和播客 ID，不输出令牌。
