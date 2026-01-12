"""Configuration management with validation using Pydantic."""

import re
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings with validation.

    Settings are loaded from environment variables and/or a .env file.
    Required fields must be set for the application to start.
    Optional fields have sensible defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===================
    # Required API Keys
    # ===================

    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for LLM operations",
        min_length=1,
    )

    serper_api_key: str = Field(
        ...,
        description="Serper API key for web search functionality",
        min_length=1,
    )

    mailgun_api: str = Field(
        ...,
        description="Mailgun API key for sending emails",
        min_length=1,
    )

    mailgun_domain: str = Field(
        ...,
        description="Mailgun domain for sending emails (e.g., mail.example.com)",
        min_length=1,
    )

    # ===================
    # Email Configuration
    # ===================

    email_recipients: List[str] = Field(
        default_factory=list,
        description="Comma-separated list of email recipients",
    )

    email_from: Optional[str] = Field(
        default=None,
        description="Email sender address (defaults to postmaster@mailgun_domain)",
    )

    # ===================
    # Optional API Keys
    # ===================

    github_token: Optional[str] = Field(
        default=None,
        description="GitHub personal access token for repository metadata",
    )

    twitter_bearer_token: Optional[str] = Field(
        default=None,
        description="Twitter/X API bearer token for sentiment analysis",
    )

    reddit_client_id: Optional[str] = Field(
        default=None,
        description="Reddit API client ID for sentiment analysis",
    )

    reddit_client_secret: Optional[str] = Field(
        default=None,
        description="Reddit API client secret for sentiment analysis",
    )

    alpha_vantage_api_key: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API key for stock price tracking",
    )

    finnhub_api_key: Optional[str] = Field(
        default=None,
        description="Finnhub API key for stock price tracking",
    )

    # ===================
    # Application Settings
    # ===================

    database_path: Path = Field(
        default=Path("ai-intel.db"),
        description="Path to SQLite database file",
    )

    output_directory: Path = Field(
        default=Path("ai-intel"),
        description="Directory for generated reports and output files",
    )

    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    # ===================
    # Validators
    # ===================

    @field_validator("email_recipients", mode="before")
    @classmethod
    def parse_email_recipients(cls, v):
        """Parse comma-separated email list or validate list input."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [email.strip() for email in v.split(",") if email.strip()]
        if isinstance(v, list):
            return [email.strip() for email in v if email and email.strip()]
        return []

    @field_validator("email_recipients", mode="after")
    @classmethod
    def validate_email_format(cls, v: List[str]) -> List[str]:
        """Validate email format for all recipients."""
        email_pattern = re.compile(
            r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        invalid_emails = [email for email in v if not email_pattern.match(email)]
        if invalid_emails:
            raise ValueError(f"Invalid email format: {', '.join(invalid_emails)}")
        return v

    @field_validator("email_from", mode="after")
    @classmethod
    def validate_email_from_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email_from format if provided."""
        if v is None:
            return v

        # Allow format like "Name <email@domain.com>" or just "email@domain.com"
        email_pattern = re.compile(
            r"^(?:[^<>]+<)?[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}>?$"
        )
        if not email_pattern.match(v):
            raise ValueError(f"Invalid email_from format: {v}")
        return v

    @field_validator("mailgun_domain", mode="after")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        """Validate domain format."""
        domain_pattern = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
        )
        if not domain_pattern.match(v):
            raise ValueError(f"Invalid domain format: {v}")
        return v

    @field_validator("log_level", mode="after")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log_level: {v}. Must be one of: {', '.join(valid_levels)}"
            )
        return v_upper

    @field_validator("database_path", "output_directory", mode="before")
    @classmethod
    def convert_to_path(cls, v):
        """Convert string paths to Path objects."""
        if isinstance(v, str):
            return Path(v)
        return v

    @model_validator(mode="after")
    def set_default_email_from(self):
        """Set default email_from based on mailgun_domain if not provided."""
        if self.email_from is None:
            self.email_from = f"AI Watcher <postmaster@{self.mailgun_domain}>"
        return self

    # ===================
    # Computed Properties
    # ===================

    @property
    def mailgun_base_url(self) -> str:
        """Get the Mailgun API base URL."""
        return f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"

    @property
    def has_github_integration(self) -> bool:
        """Check if GitHub integration is configured."""
        return self.github_token is not None and len(self.github_token) > 0

    @property
    def has_twitter_integration(self) -> bool:
        """Check if Twitter integration is configured."""
        return self.twitter_bearer_token is not None and len(self.twitter_bearer_token) > 0

    @property
    def has_reddit_integration(self) -> bool:
        """Check if Reddit integration is configured."""
        return (
            self.reddit_client_id is not None
            and self.reddit_client_secret is not None
            and len(self.reddit_client_id) > 0
            and len(self.reddit_client_secret) > 0
        )

    @property
    def has_stock_tracking(self) -> bool:
        """Check if any stock tracking API is configured."""
        return (
            (self.alpha_vantage_api_key is not None and len(self.alpha_vantage_api_key) > 0)
            or (self.finnhub_api_key is not None and len(self.finnhub_api_key) > 0)
        )

    @property
    def configured_integrations(self) -> List[str]:
        """Get list of configured optional integrations."""
        integrations = []
        if self.has_github_integration:
            integrations.append("GitHub")
        if self.has_twitter_integration:
            integrations.append("Twitter/X")
        if self.has_reddit_integration:
            integrations.append("Reddit")
        if self.alpha_vantage_api_key:
            integrations.append("Alpha Vantage")
        if self.finnhub_api_key:
            integrations.append("Finnhub")
        return integrations


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Get application settings (cached singleton).

    Returns:
        Settings: The validated application settings instance.

    Raises:
        pydantic.ValidationError: If required settings are missing or invalid.
    """
    return Settings()


def validate_environment() -> bool:
    """
    Validate that all required environment variables are set.

    Returns:
        bool: True if all required variables are valid, False otherwise.

    Prints validation errors to stderr for debugging.
    """
    import sys

    try:
        settings = get_settings()

        # Print configuration summary
        print("Configuration validated successfully!", file=sys.stderr)
        print(f"  - Database: {settings.database_path}", file=sys.stderr)
        print(f"  - Output directory: {settings.output_directory}", file=sys.stderr)
        print(f"  - Log level: {settings.log_level}", file=sys.stderr)
        print(f"  - Email recipients: {len(settings.email_recipients)}", file=sys.stderr)

        if settings.configured_integrations:
            print(
                f"  - Optional integrations: {', '.join(settings.configured_integrations)}",
                file=sys.stderr
            )
        else:
            print("  - No optional integrations configured", file=sys.stderr)

        return True

    except Exception as e:
        print(f"Configuration validation failed: {e}", file=sys.stderr)
        return False


def clear_settings_cache() -> None:
    """
    Clear the settings cache.

    Useful for testing or when environment variables change at runtime.
    """
    get_settings.cache_clear()


# ===================
# Convenience Exports
# ===================

__all__ = [
    "Settings",
    "get_settings",
    "validate_environment",
    "clear_settings_cache",
]
