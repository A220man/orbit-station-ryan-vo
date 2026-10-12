import pytest
from app.core.config import settings

def test_settings_initialization():
    assert settings.app_name == "Orbit Station"
    assert settings.port == 8000
    assert isinstance(settings.demo_mode, bool)
