# """
# Application configuration settings loaded from environment variables.
# """

# from functools import lru_cache
# from pathlib import Path
# from typing import Optional

# from pydantic import BaseSettings, Field, validator


# class Settings(BaseSettings):
#     app_name: str = "PodSummarize Backend"
#     environment: str = Field("development", env="ENVIRONMENT")
#     api_prefix: str = "/api"

#     storage_dir: Path = Field(Path("storage"), env="STORAGE_DIR")
#     temp_dir: Path = Field(Path("storage/temp"), env="TEMP_DIR")
#     results_dir: Path = Field(Path("storage/results"), env="RESULTS_DIR")

#     # Whisper / transcription configuration
#     whisper_model: str = Field("medium", env="WHISPER_MODEL")
#     transcription_provider: str = Field(
#         "openai", env="TRANSCRIPTION_PROVIDER"
#     )  # openai | assemblyai | google
#     openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
#     assembly_ai_key: Optional[str] = Field(None, env="ASSEMBLY_AI_KEY")
#     google_credentials_json: Optional[str] = Field(None, env="GOOGLE_CREDENTIALS_JSON")

#     # LLM summarization
#     llm_provider: str = Field("openai", env="LLM_PROVIDER")  # openai | deepseek | gemini | custom
#     llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")
#     llm_api_key: Optional[str] = Field(None, env="LLM_API_KEY")
#     gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")

#     # TTS settings (optional)
#     tts_provider: str = Field("azure", env="TTS_PROVIDER")  # azure | google | coqui | none
#     tts_voice: str = Field("en-US-JennyMultilingualNeural", env="TTS_VOICE")
#     azure_speech_key: Optional[str] = Field(None, env="AZURE_SPEECH_KEY")
#     azure_speech_region: Optional[str] = Field(None, env="AZURE_SPEECH_REGION")

#     cors_origins: str = Field("*", env="CORS_ORIGINS")

#     class Config:
#         env_file = ".env"
#         env_file_encoding = "utf-8"

#     @validator("storage_dir", "temp_dir", "results_dir", pre=True)
#     def _ensure_path(cls, value: Path) -> Path:
#         path = Path(value)
#         path.mkdir(parents=True, exist_ok=True)
#         return path


# @lru_cache()
# def get_settings() -> Settings:
#     """Return cached settings instance."""
#     return Settings()
"""
Application configuration settings loaded from environment variables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    app_name: str = "PodSummarize Backend"
    environment: str = Field("development", env="ENVIRONMENT")
    api_prefix: str = "/api"

    storage_dir: Path = Field(Path("storage"), env="STORAGE_DIR")
    temp_dir: Path = Field(Path("storage/temp"), env="TEMP_DIR")
    results_dir: Path = Field(Path("storage/results"), env="RESULTS_DIR")

    # Whisper / transcription configuration
    whisper_model: str = Field("medium", env="WHISPER_MODEL")
    transcription_provider: str = Field(
        "openai", env="TRANSCRIPTION_PROVIDER"
    )  # openai | assemblyai | google
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    assembly_ai_key: Optional[str] = Field(None, env="ASSEMBLY_AI_KEY")
    google_credentials_json: Optional[str] = Field(None, env="GOOGLE_CREDENTIALS_JSON")

    # LLM summarization
    llm_provider: str = Field("openai", env="LLM_PROVIDER")  # openai | deepseek | gemini | custom
    llm_model: str = Field("gpt-4o-mini", env="LLM_MODEL")
    llm_api_key: Optional[str] = Field(None, env="LLM_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")

    # TTS settings (optional)
    # Default provider switched to ElevenLabs to avoid Azure DNS/region issues.
    tts_provider: str = Field("elevenlabs", env="TTS_PROVIDER")  # azure | google | coqui | elevenlabs | none
    tts_voice: str = Field("en-US-JennyMultilingualNeural", env="TTS_VOICE")
    azure_speech_key: Optional[str] = Field(None, env="AZURE_SPEECH_KEY")
    azure_speech_region: Optional[str] = Field(None, env="AZURE_SPEECH_REGION")

    # --- ElevenLabs (ADDED) ---
    elevenlabs_api_key: Optional[str] = Field(None, env="ELEVENLABS_API_KEY")
    elevenlabs_voice: Optional[str] = Field(None, env="ELEVENLABS_VOICE")
    # ---------------------------

    cors_origins: str = Field("*", env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @validator("storage_dir", "temp_dir", "results_dir", pre=True)
    def _ensure_path(cls, value: Path) -> Path:
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
