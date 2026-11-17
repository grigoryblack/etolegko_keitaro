from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    base_url: str = Field(min_length=1, description="Tracker base URL, e.g. https://tracker.example.com")
    login: str = Field(min_length=1)
    password: str = Field(min_length=1)

    @field_validator("base_url")
    @classmethod
    def normalize_url(cls, v: str) -> str:
        v = v.strip().rstrip("/")
        return v[:-6] if v.endswith("/admin") else v
