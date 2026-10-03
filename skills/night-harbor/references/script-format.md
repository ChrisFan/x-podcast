# 脚本 v1

先调用 `catalog`，其中 `script_schema` 是机器可读的完整 JSON Schema，`preferences_schema` 是账户偏好 schema，`sample_script` 是可直接修改的范例。服务器的 schema 和 `validate_script` 的语义校验优先于本文件中的示例。

| 字段 | 用途与写法 |
| --- | --- |
| version | 固定 1 |
| id | 文案标识，字母、数字、下划线、连字符；不同文案使用不同标识；不是服务器播客 UUID |
| title | 用户在 App/Web 看到的标题 |
| model | 使用 catalog 范例中的已支持模型，不询问普通用户 |
| voice | catalog.voices 中的 id；继承用户偏好 |
| language_type | 当前 Chinese |
| instructions | 发音/语速/语气说明，非正文，不写外部工具操作要求 |
| mix.intro_seconds | 人声开始前的环境声秒数 |
| mix.tail_seconds | 人声结束后的环境声秒数 |
| mix.fade_out_seconds | 尾段渐弱秒数，不超过 tail_seconds |
| mix.ambience_dbfs | 环境声强度，负值更小更轻；不是手机实际音量或医学安全阈值 |
| mix.seed | 0 到 2^32−1 的整数，固定时雨声可复现 |
| segments | 顺序排列的段落，数量/总字符限制由服务校验 |
| segments[].id | 在此文案内唯一；字母、数字、下划线、连字符 |
| segments[].label | 段落标题，不会朗读 |
| segments[].text | 纯朗读正文，不放 [停顿]、【雨声】、XML 或 Markdown 标记 |
| segments[].pause_after_seconds | 此段之后的安静间隔，由混音器实现 |

最小示例（用于验证或短试听，不能称为完整长篇播客）：

```json
{
  "version": 1,
  "id": "rainy-room-short-01",
  "title": "雨夜旅馆 · 安静的房间",
  "model": "qwen3-tts-instruct-flash-2026-01-26",
  "voice": "Serena",
  "language_type": "Chinese",
  "instructions": "用柔和、自然、平稳的普通话缓慢叙述。不要气声耳语，不添加音效，只朗读正文。",
  "mix": {
    "intro_seconds": 4,
    "tail_seconds": 30,
    "fade_out_seconds": 20,
    "ambience_dbfs": -38,
    "seed": 20261002
  },
  "segments": [
    {
      "id": "window",
      "label": "窗边",
      "text": "窗外是细细的雨。灯光停在床边，被子已经暖了起来。房间里的每样东西，都安静地留在原来的地方。",
      "pause_after_seconds": 8
    },
    {
      "id": "rest",
      "label": "渐静",
      "text": "雨声轻轻延续。枕头托着你，夜晚慢慢过去。",
      "pause_after_seconds": 0
    }
  ]
}
```

`create_draft` 的请求是 `{ "script": <上述对象>, "scene": "rainy-inn" }`；scene 不应被擅自加进脚本 schema。`generate_podcast` 使用返回的服务器 UUID 和单独 UUID request_id。
