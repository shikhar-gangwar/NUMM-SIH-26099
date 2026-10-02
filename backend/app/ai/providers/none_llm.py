from app.ai.providers.base import LLMProvider, ModelFingerprint

class NoneLLM(LLMProvider):
    def __init__(self):
        self.name = "none"
        self.model_id = "none"
        self.version = "v0"

    def complete_json(self, task: str, payload: dict, schema: dict, temperature: float = 0.0) -> dict:
        return {"result": "disabled", "status": "LLM_PROVIDER_NONE"}

    def fingerprint(self) -> ModelFingerprint:
        return ModelFingerprint(
            provider=self.name,
            model_id=self.model_id,
            model_version=self.version
        )
