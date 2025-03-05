from pydantic import BaseModel
from typing import Optional

class CampaignBase(BaseModel):
    name: str
    publisher_id: int
    country_id: int
    operator_id: int
    advertiser_id: int
    publisherPrice: float
    advertiserPrice: float
    fallbackEnabled: bool
    redirection_advertiser_id: Optional[int] = None

class CampaignCreate(CampaignBase):
    publisher_name: str
    country_name: str
    operator_name: str
    advertiser_name: str
    redirection_advertiser_name: Optional[str] = None

class Campaign(CampaignBase):
    id: int
    publisher_name: str
    country_name: str
    operator_name: str
    advertiser_name: str
    redirection_advertiser_name: Optional[str] = None

    class Config:
        orm_mode: True
