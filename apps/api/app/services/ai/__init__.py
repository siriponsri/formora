from app.config import Settings
from app.services.ai.base import AIProvider
from app.services.ai.mock import MockAIProvider


def build_ai_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "typhoon":
        from app.services.ai.typhoon import TyphoonAIProvider

        return TyphoonAIProvider(settings)
    return MockAIProvider()


__all__ = ["AIProvider", "MockAIProvider", "build_ai_provider"]
