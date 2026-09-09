import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from medmirror.providers import build_chat_payload, load_local_env, model_registry


class ProviderConfigTest(unittest.TestCase):
    def test_local_env_loader_does_not_override_process_env(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir) / ".env.local"
            env_path.write_text("TEST_MEDMIRROR_KEY=from-file\n")
            previous = os.environ.get("TEST_MEDMIRROR_KEY")
            os.environ["TEST_MEDMIRROR_KEY"] = "from-process"
            try:
                load_local_env(env_path)
                self.assertEqual(os.environ["TEST_MEDMIRROR_KEY"], "from-process")
            finally:
                if previous is None:
                    os.environ.pop("TEST_MEDMIRROR_KEY", None)
                else:
                    os.environ["TEST_MEDMIRROR_KEY"] = previous

    def test_three_models_are_registered(self):
        registry = model_registry()
        self.assertEqual(set(registry), {"deepseek-v4-flash", "step-3.7-flash", "glm-5.3-flash"})

    def test_environment_overrides_model_endpoint(self):
        previous_model = os.environ.get("STEPFUN_MODEL")
        previous_url = os.environ.get("STEPFUN_BASE_URL")
        os.environ["STEPFUN_MODEL"] = "step-test-model"
        os.environ["STEPFUN_BASE_URL"] = "https://example.test/v1"
        try:
            config = model_registry()["step-3.7-flash"]
            self.assertEqual(config.model_id, "step-test-model")
            self.assertEqual(config.endpoint, "https://example.test/v1/chat/completions")
            self.assertFalse(config.confirmed)
        finally:
            if previous_model is None:
                os.environ.pop("STEPFUN_MODEL", None)
            else:
                os.environ["STEPFUN_MODEL"] = previous_model
            if previous_url is None:
                os.environ.pop("STEPFUN_BASE_URL", None)
            else:
                os.environ["STEPFUN_BASE_URL"] = previous_url

    def test_payload_is_openai_compatible_shape(self):
        config = model_registry()["deepseek-v4-flash"]
        payload = build_chat_payload(config, [{"role": "user", "content": "test"}])
        self.assertEqual(payload["model"], "deepseek-v4-flash")
        self.assertEqual(payload["messages"][0]["role"], "user")
        self.assertFalse(payload["stream"])

    def test_payload_can_set_thinking_mode(self):
        config = model_registry()["deepseek-v4-flash"]
        payload = build_chat_payload(config, [{"role": "user", "content": "test"}], thinking_mode="disabled")
        self.assertEqual(payload["thinking"], {"type": "disabled"})

    def test_payload_can_set_reasoning_effort(self):
        config = model_registry()["step-3.7-flash"]
        payload = build_chat_payload(config, [{"role": "user", "content": "test"}], reasoning_effort="low")
        self.assertEqual(payload["reasoning_effort"], "low")

    def test_endpoint_is_derived_without_double_slash(self):
        for config in model_registry().values():
            self.assertNotIn("//chat", config.endpoint)
            self.assertTrue(config.endpoint.endswith("/chat/completions"))


if __name__ == "__main__":
    unittest.main()
