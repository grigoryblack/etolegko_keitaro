from pydantic import BaseModel, Field


class OfferAddRequest(BaseModel):
    offer_id: int = Field(gt=0)
