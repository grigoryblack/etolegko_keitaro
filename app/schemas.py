import re

from pydantic import BaseModel, Field, field_validator


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    geo: str = Field(min_length=2, max_length=2, description="ISO-3166 alpha-2 country code")
    offer_id: int = Field(gt=0)
    domain_id: int | None = None
    group_id: int | None = None
    source_id: int | None = None

    @field_validator("geo")
    @classmethod
    def normalize_geo(cls, v: str) -> str:
        return v.strip().upper()

    @property
    def alias(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.name.lower()).strip("-")
        return slug or "campaign"


class LoginRequest(BaseModel):
    base_url: str = Field(min_length=1, description="Tracker base URL, e.g. https://tracker.example.com")
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)

    @field_validator("base_url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        return v[:-6] if v.endswith("/admin") else v


class OfferAddRequest(BaseModel):
    offer_id: int = Field(gt=0)
