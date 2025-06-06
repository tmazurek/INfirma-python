"""Application configuration using Pydantic BaseSettings."""

from decimal import Decimal
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = Field(default="InFirma", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./infirma.db", 
        env="DATABASE_URL"
    )
    
    # Default ZUS Settings (2024 rates for Poland)
    default_zus_base_amount: Decimal = Field(
        default=Decimal("5203.80"), 
        env="DEFAULT_ZUS_BASE_AMOUNT"
    )
    default_emerytalne_rate: Decimal = Field(
        default=Decimal("19.52"), 
        env="DEFAULT_EMERYTALNE_RATE"
    )
    default_rentowe_rate: Decimal = Field(
        default=Decimal("8.00"), 
        env="DEFAULT_RENTOWE_RATE"
    )
    default_wypadkowe_rate: Decimal = Field(
        default=Decimal("1.67"), 
        env="DEFAULT_WYPADKOWE_RATE"
    )
    default_chorobowe_rate: Decimal = Field(
        default=Decimal("2.45"), 
        env="DEFAULT_CHOROBOWE_RATE"
    )
    default_labor_fund_rate: Decimal = Field(
        default=Decimal("2.45"), 
        env="DEFAULT_LABOR_FUND_RATE"
    )
    default_fep_rate: Decimal = Field(
        default=Decimal("0.10"), 
        env="DEFAULT_FEP_RATE"
    )
    
    # Default Tax Settings
    default_vat_rate: Decimal = Field(
        default=Decimal("23.00"), 
        env="DEFAULT_VAT_RATE"
    )
    default_pit_ryczalt_rate: Decimal = Field(
        default=Decimal("12.00"), 
        env="DEFAULT_PIT_RYCZALT_RATE"
    )
    
    # Security (for future authentication)
    secret_key: str = Field(
        default="dev-secret-key-change-in-production", 
        env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, 
        env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


# Global settings instance
settings = Settings()
