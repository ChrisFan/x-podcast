#!/usr/bin/env python3
"""Local sleep-podcast experiment: script -> DashScope TTS -> PCM WAV mixes."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
import wave

import numpy as np

ROOT = Path(__file__).resolve().parent
ENDPOINTS = {
    "beijing": "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
    "singapore": "https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
}


class PodcastError(Exception):
    pass


def load_env(path: Path) -> None:
    """Read literal KEY=value only; never execute shell interpolation."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key.strip()):
            raise PodcastError(".env 格式应为 KEY=value，不支持 shell 命令。")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def number(value, label: str, low: float, high: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise PodcastError(f"{label} 必须是数字。")
    if not math.isfinite(value) or not low <= value <= high:
        raise PodcastError(f"{label} 必须在 {low} 到 {high} 之间。")
    return float(value)


def load_script(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("version") != 1:
        raise PodcastError("只支持 version=1 的脚本。")
    for key in ("id", "title", "voice", "instructions"):
        if not isinstance(doc.get(key), str) or not doc[key].strip():
            raise PodcastError(f"脚本缺少 {key}。")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", doc["id"]):
        raise PodcastError("脚本 id 仅支持字母、数字、下划线和连字符。")
    if doc.get("model") not in ("qwen3-tts-instruct-flash", "qwen3-tts-instruct-flash-2026-01-26"):
        raise PodcastError("此 MVP 只接入 Qwen3-TTS-Instruct-Flash，其他模型的接口不能混用。")
    if doc.get("language_type") != "Chinese":
        raise PodcastError("此测试脚本要求 language_type=Chinese。")
    segments = doc.get("segments")
    if not isinstance(segments, list) or not 1 <= len(segments) <= 40:
        raise PodcastError("脚本需要 1 到 40 段正文。")
    seen = set()
    for segment in segments:
        sid, text = segment.get("id"), segment.get("text")
        if not isinstance(sid, str) or not re.fullmatch(r"[a-zA-Z0-9_-]+", sid) or sid in seen:
            raise PodcastError("段落 id 必须唯一且仅含字母、数字、下划线、连字符。")
        seen.add(sid)
        if not isinstance(text, str) or not text.strip() or len(text) > 600:
            raise PodcastError(f"段落 {sid} 需要 1 到 600 字符；请按语义拆段。")
        if re.search(r"[\[\]<>【】]", text):
            raise PodcastError(f"段落 {sid} 包含标记；制作指令请放到正文之外。")
        number(segment.get("pause_after_seconds"), "停顿秒数", 0, 60)
    mix = doc.get("mix", {})
    for key, bounds in {"intro_seconds": (0, 30), "tail_seconds": (0, 180),
                        "fade_out_seconds": (0, 180), "ambience_dbfs": (-60, -25)}.items():
        number(mix.get(key), key, *bounds)
    if mix["fade_out_seconds"] > mix["tail_seconds"]:
        raise PodcastError("渐弱时长不能超过结尾环境声时长，以免截断人声。")
    if not isinstance(mix.get("seed"), int) or not 0 <= mix["seed"] < 2**32:
        raise PodcastError("mix.seed 必须是 0 到 2^32-1 的整数。")
    return doc


def request_body(doc: dict, segment: dict) -> dict:
    return {"model": doc["model"], "input": {
        "text": segment["text"], "voice": doc["voice"],
        "language_type": doc["language_type"], "instructions": doc["instructions"],
        "optimize_instructions": False,
    }}


def cache_key(body: dict, region: str) -> str:
    data = json.dumps({"endpoint": ENDPOINTS[region], "body": body}, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(data.encode()).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(data)
    temp.replace(path)


def save_json(path: Path, data: dict) -> None:
    atomic_write(path, (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode())


def read_wav(data: bytes) -> tuple[np.ndarray, int]:
    try:
        with wave.open(io.BytesIO(data), "rb") as source:
            if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
                raise PodcastError("只支持 16-bit PCM WAV；请先转换音频格式。")
            channels, rate, frames = source.getnchannels(), source.getframerate(), source.getnframes()
            raw = source.readframes(frames)
            if not frames or len(raw) != frames * channels * 2:
                raise PodcastError("WAV 文件为空或不完整。")
            samples = np.frombuffer(raw, dtype="<i2").astype(np.float32) / 32768
            samples = samples.reshape(-1, channels).mean(axis=1)
            return samples, rate
    except (wave.Error, EOFError) as error:
        raise PodcastError("返回的音频不是可读的 PCM WAV。") from error


def write_wav(path: Path, samples: np.ndarray, rate: int) -> None:
    if not np.all(np.isfinite(samples)) or np.max(np.abs(samples)) >= 1:
        raise PodcastError("音频存在非有限值或削波风险，停止导出。")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(rate)
        output.writeframes(np.rint(samples * 32767).astype("<i2").tobytes())
    atomic_write(path, buf.getvalue())


def download_url(value: str) -> str:
    url = urlsplit(value)
    host = url.hostname or ""
    if url.scheme not in ("http", "https") or not host.endswith(".aliyuncs.com") or url.username or url.password or url.port not in (None, 443):
        raise PodcastError("返回的音频地址不在预期的阿里云 HTTPS 域名内。")
    # Official examples return http OSS URLs; use HTTPS without changing the signature.
    return urlunsplit(("https", url.netloc, url.path, url.query, url.fragment))


def synthesize(body: dict, region: str, api_key: str) -> tuple[bytes, dict]:
    req = Request(ENDPOINTS[region], data=json.dumps(body).encode(), headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
    }, method="POST")
    start = time.monotonic()
    try:
        with urlopen(req, timeout=120) as response:
            result = json.load(response)
    except HTTPError as error:
        # Never log server messages, headers, raw responses, or signed download URLs.
        hints = {401: "检查 API Key 和地域是否匹配", 403: "检查模型权限与服务开通状态",
                 429: "达到限流或额度限制，稍后手动重试"}
        raise PodcastError(f"TTS HTTP {error.code}：{hints.get(error.code, '检查请求或服务状态')}。") from None
    except (URLError, TimeoutError, OSError):
        raise PodcastError("TTS 网络失败或超时；未自动重试，以免重复计费。已生成的段落会保留。") from None
    if result.get("code") or result.get("status_code", 200) != 200:
        raise PodcastError("TTS 返回业务错误；请检查模型权限、地域和额度。")
    url = result.get("output", {}).get("audio", {}).get("url")
    if not url:
        raise PodcastError("TTS 未返回音频 URL，停止生成。")
    try:
        with urlopen(download_url(url), timeout=120) as response:
            audio = response.read(50 * 1024 * 1024 + 1)
        if len(audio) > 50 * 1024 * 1024:
            raise PodcastError("单段音频超过 50 MiB，停止下载。")
        read_wav(audio)
    except (HTTPError, URLError, TimeoutError, OSError):
        raise PodcastError("音频已合成但下载失败；重跑本段可能再次计费。") from None
    return audio, {"request_id": result.get("request_id"), "usage": result.get("usage", {}),
                   "elapsed_seconds": round(time.monotonic() - start, 3)}


def get_clip(doc: dict, segment: dict, region: str, cache: Path, generate: bool) -> tuple[np.ndarray, int, dict]:
    body = request_body(doc, segment)
    key = cache_key(body, region)
    wav_path, meta_path = cache / (key + ".wav"), cache / (key + ".json")
    if wav_path.exists():
        samples, rate = read_wav(wav_path.read_bytes())
        info = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        return samples, rate, {**info, "cached": True, "cache_key": key}
    if not generate:
        raise PodcastError(f"缺少 {segment['id']} 的缓存；先运行 generate。")
    api_key = os.environ.get("DASHSCOPE_API_KEY", "").strip()
    if not api_key:
        raise PodcastError("尚未配置 DASHSCOPE_API_KEY。请填入项目 .env，勿在聊天中发送密钥。")
    audio, info = synthesize(body, region, api_key)
    samples, rate = read_wav(audio)
    cache.mkdir(parents=True, exist_ok=True)
    atomic_write(wav_path, audio)
    save_json(meta_path, info)
    return samples, rate, {**info, "cached": False, "cache_key": key}


def normalize_voice(samples: np.ndarray, rate: int) -> tuple[np.ndarray, float]:
    active = samples[np.abs(samples) > 10 ** (-45 / 20)]
    if not len(active):
        raise PodcastError("TTS 段落没有可检测的人声电平。")
    rms = float(np.sqrt(np.mean(active**2)))
    gain = min(float(np.clip(10 ** (-23 / 20) / rms, 0.5, 2.0)), 0.65 / float(np.max(np.abs(samples))))
    audio = samples * gain
    # Millisecond edge fades avoid clicks, without trimming or time-stretching speech.
    edge = min(round(rate * .008), len(audio) // 2)
    audio[:edge] *= np.linspace(0, 1, edge)
    audio[-edge:] *= np.linspace(1, 0, edge)
    return audio, gain


def synthetic_rain(length: int, rate: int, seed: int) -> np.ndarray:
    """Soft colored noise placeholder, not a field recording or generated weather SFX."""
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(length + 128, dtype=np.float32)
    soft = np.convolve(noise, np.ones(96, dtype=np.float32) / 96, mode="valid")[:length]
    rain = (soft * 3 + noise[:length] * .12).astype(np.float32)
    envelope = np.interp(np.arange(length), np.linspace(0, length - 1, max(2, length // rate // 8)),
                         rng.uniform(.85, 1.0, max(2, length // rate // 8)))
    rain *= envelope
    return rain


def render(doc: dict, clips: list[tuple], output: Path, preview: bool, ambience_wav: Path | None) -> dict:
    rates = {clip[1] for clip in clips}
    if len(rates) != 1:
        raise PodcastError("段落采样率不一致，停止拼接；不能直接更改 WAV 头代替重采样。")
    rate = rates.pop()
    mix = doc["mix"]
    intro = mix["intro_seconds"]
    tail = 8 if preview else mix["tail_seconds"]
    fade = min(5 if preview else mix["fade_out_seconds"], tail)
    parts = [np.zeros(round(intro * rate), dtype=np.float32)]
    cursor, timeline = intro, []
    for segment, (samples, _, info) in zip(doc["segments"], clips):
        processed, gain = normalize_voice(samples, rate)
        duration = len(processed) / rate
        pause = segment["pause_after_seconds"]
        timeline.append({"id": segment["id"], "start_seconds": round(cursor, 3),
                         "duration_seconds": round(duration, 3), "pause_after_seconds": pause,
                         "gain_db": round(20 * math.log10(gain), 2), **info})
        parts.extend([processed, np.zeros(round(pause * rate), dtype=np.float32)])
        cursor += duration + pause
    parts.append(np.zeros(round(tail * rate), dtype=np.float32))
    narration = np.concatenate(parts)
    if ambience_wav:
        bed, bed_rate = read_wav(ambience_wav.read_bytes())
        if bed_rate != rate or len(bed) < len(narration):
            raise PodcastError("自备环境声须为同采样率且不短于成片的 16-bit PCM WAV；此版不自动循环或重采样。")
        bed = bed[:len(narration)].copy()
        source = "user_provided_wav"
    else:
        bed = synthetic_rain(len(narration), rate, mix["seed"])
        source = "synthetic_colored_noise_placeholder"
    rms = float(np.sqrt(np.mean(bed**2)))
    if rms <= 1e-8:
        raise PodcastError("环境声音频为空或静音。")
    bed *= 10 ** (mix["ambience_dbfs"] / 20) / rms
    fade_in_frames = min(round(3 * rate), len(bed))
    bed[:fade_in_frames] *= np.linspace(0, 1, fade_in_frames)
    fade_frames = min(round(fade * rate), len(bed))
    if fade_frames:
        bed[-fade_frames:] *= np.linspace(1, 0, fade_frames)
    combined = narration + bed
    peak = float(np.max(np.abs(combined)))
    master_gain = min(1.0, 10 ** (-1 / 20) / max(peak, 1e-9))
    narration *= master_gain
    combined *= master_gain
    output.mkdir(parents=True, exist_ok=True)
    write_wav(output / "narration.wav", narration, rate)
    write_wav(output / "podcast.wav", combined, rate)
    report = {"title": doc["title"], "preview": preview, "model": doc["model"], "voice": doc["voice"],
              "sample_rate": rate, "duration_seconds": round(len(combined) / rate, 3),
              "peak_dbfs": round(20 * math.log10(max(float(np.max(np.abs(combined))), 1e-9)), 2),
              "clipped_samples": int(np.count_nonzero(np.abs(combined) >= 1)),
              "ambience": source, "ambience_dbfs_before_fades": mix["ambience_dbfs"],
              "master_gain_db": round(20 * math.log10(master_gain), 3), "timeline": timeline,
              "listening_review": "pending", "sleep_effectiveness": "not_evaluated"}
    save_json(output / "report.json", report)
    save_json(output / "script.json", doc)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="睡眠播客本地 MVP：脚本 → 阿里云 TTS → WAV")
    parser.add_argument("command", choices=["check", "generate", "render"])
    parser.add_argument("--script", type=Path, default=ROOT / "scripts/rainy-inn.json")
    parser.add_argument("--preview", action="store_true", help="仅生成前两段，试听通过后再生成全篇")
    parser.add_argument("--voice", help="覆盖音色，例如 Serena 或 Ethan")
    parser.add_argument("--region", choices=list(ENDPOINTS))
    parser.add_argument("--ambience-wav", type=Path, help="可选的自备环境声 WAV")
    parser.add_argument("--output", type=Path, default=ROOT / "output")
    args = parser.parse_args()
    load_env(ROOT / ".env")
    region = args.region or os.environ.get("DASHSCOPE_REGION", "beijing")
    if region not in ENDPOINTS:
        raise PodcastError("DASHSCOPE_REGION 必须为 beijing 或 singapore。")
    doc = load_script(args.script)
    if args.voice:
        doc["voice"] = args.voice
    if args.preview:
        doc["segments"] = doc["segments"][:2]
    count = sum(len(s["text"]) for s in doc["segments"])
    print(f"{doc['title']} | {doc['voice']} | {region} | {len(doc['segments'])} 段 / {count} 字符", flush=True)
    if args.command == "check":
        configured = bool(os.environ.get("DASHSCOPE_API_KEY", "").strip())
        print(f"脚本校验通过；API Key {'已配置（未验证有效性）' if configured else '未配置'}；未请求 API。")
        return 0
    clips = []
    cache = args.output / "cache"
    for i, segment in enumerate(doc["segments"], 1):
        print(f"[{i}/{len(doc['segments'])}] {segment.get('label', segment['id'])}…", flush=True)
        clip = get_clip(doc, segment, region, cache, args.command == "generate")
        clips.append(clip)
        print(f"  {'复用缓存' if clip[2]['cached'] else '已下载'} · {len(clip[0]) / clip[1]:.1f} 秒", flush=True)
    # Every render gets its own folder, preserving previous audition versions.
    output = args.output / f"{doc['id']}-{'preview' if args.preview else 'full'}-{time.time_ns()}"
    report = render(doc, clips, output, args.preview, args.ambience_wav)
    print(f"已导出 {report['duration_seconds']:.1f} 秒；峰值 {report['peak_dbfs']} dBFS；削波 {report['clipped_samples']}。")
    print(f"混音：{output / 'podcast.wav'}\n纯人声：{output / 'narration.wav'}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (PodcastError, OSError, ValueError, KeyError, TypeError) as error:
        if isinstance(error, PodcastError):
            print(f"错误：{error}", file=sys.stderr)
        else:
            print(f"错误：输入或本地文件处理失败（{type(error).__name__}）。请检查脚本格式、路径和文件权限。", file=sys.stderr)
        sys.exit(1)
