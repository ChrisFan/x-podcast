import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import numpy as np

import podcast as p


class PodcastTests(unittest.TestCase):
    def setUp(self):
        self.doc = p.load_script(p.ROOT / "scripts/rainy-inn.json")

    def wav_fixture(self, directory):
        # Test-only sine wave, never exposed as a TTS result to the user.
        path = Path(directory) / "fixture.wav"
        rate = 24000
        samples = (.1 * np.sin(2 * np.pi * 220 * np.arange(rate) / rate)).astype(np.float32)
        p.write_wav(path, samples, rate)
        return path.read_bytes()

    def test_cache_prevents_paid_calls_and_voice_change_invalidates_it(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "cache"
            audio = self.wav_fixture(directory)
            with patch.dict(p.os.environ, {"DASHSCOPE_API_KEY": "test-only"}):
                with patch.object(p, "synthesize", return_value=(audio, {"usage": {"characters": 1}})) as api:
                    first = p.get_clip(self.doc, self.doc["segments"][0], "beijing", cache, True)
                    second = p.get_clip(self.doc, self.doc["segments"][0], "beijing", cache, True)
                    self.assertEqual(api.call_count, 1)
                    self.assertFalse(first[2]["cached"])
                    self.assertTrue(second[2]["cached"])
                    self.doc["voice"] = "Ethan"
                    p.get_clip(self.doc, self.doc["segments"][0], "beijing", cache, True)
                    self.assertEqual(api.call_count, 2)

    def test_offline_render_missing_cache_cannot_call_api(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(p, "synthesize") as api:
            with self.assertRaises(p.PodcastError):
                p.get_clip(self.doc, self.doc["segments"][0], "beijing", Path(directory), False)
            api.assert_not_called()

    def test_render_preserves_timing_and_has_fade_and_no_clipping(self):
        doc = copy.deepcopy(self.doc)
        doc["segments"] = doc["segments"][:2]
        doc["mix"].update(intro_seconds=1, tail_seconds=2, fade_out_seconds=1)
        with tempfile.TemporaryDirectory() as directory:
            samples, rate = p.read_wav(self.wav_fixture(directory))
            clips = [(samples, rate, {"cached": True})] * 2
            report = p.render(doc, clips, Path(directory), False, None)
            narration, _ = p.read_wav((Path(directory) / "narration.wav").read_bytes())
            mixed, _ = p.read_wav((Path(directory) / "podcast.wav").read_bytes())
            # 1 s intro + 2 x 1 s speech + 3 s/4 s pauses + 2 s tail.
            self.assertEqual(report["duration_seconds"], 12)
            self.assertEqual(report["timeline"][1]["start_seconds"], 5)
            self.assertTrue(np.all(narration[2 * rate:5 * rate] == 0))
            self.assertTrue(np.all(narration[-2 * rate:] == 0))
            self.assertLessEqual(float(np.max(np.abs(mixed))), 10 ** (-1 / 20))
            self.assertEqual(mixed[-1], 0)
            self.assertEqual(report["clipped_samples"], 0)
            self.assertEqual(report["listening_review"], "pending")

    def test_mismatched_sample_rates_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(p.PodcastError, "采样率"):
                p.render(self.doc, [(np.ones(100), 16000, {}), (np.ones(100), 24000, {})], Path(directory), False, None)

    def test_api_failure_is_not_retried_or_leaked(self):
        secret = "test-private-key"
        error = HTTPError("https://example.invalid", 401, secret, {}, io.BytesIO(secret.encode()))
        with patch.object(p, "urlopen", side_effect=error) as api:
            with self.assertRaises(p.PodcastError) as context:
                p.synthesize({}, "beijing", secret)
            self.assertNotIn(secret, str(context.exception))
            self.assertEqual(api.call_count, 1)

    def test_script_rejects_overlong_text_and_production_markers(self):
        for invalid in ("字" * 601, "正文【停顿十秒】"):
            with self.subTest(text_length=len(invalid)), tempfile.TemporaryDirectory() as directory:
                doc = copy.deepcopy(self.doc)
                doc["segments"][0]["text"] = invalid
                path = Path(directory) / "bad.json"
                path.write_text(json.dumps(doc))
                with self.assertRaises(p.PodcastError):
                    p.load_script(path)

    def test_signed_url_only_uses_expected_host_and_https(self):
        self.assertEqual(p.download_url("http://result.oss-cn-beijing.aliyuncs.com/a.wav?Signature=test"),
                         "https://result.oss-cn-beijing.aliyuncs.com/a.wav?Signature=test")
        for url in ("https://example.com/a.wav", "http://127.0.0.1/a.wav", "file:///etc/passwd"):
            with self.assertRaises(p.PodcastError):
                p.download_url(url)


if __name__ == "__main__":
    unittest.main()
