from pydantic import BaseModel
from typing import Optional

class AdvertiserBase(BaseModel):
    name: str
    company_name: str
    email: str
    status: str
    sendOtpUrl: str
    verifyOtpUrl: str
    statusCheckUrl: str
    blockRule: Optional[str] = None
    capping: Optional[str] = None
    operator_name: str

class AdvertiserCreate(AdvertiserBase):
    pass

class Advertiser(AdvertiserBase):
    id: int

    class Config:
        orm_mode: True
