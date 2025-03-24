from pydantic import BaseModel, EmailStr
from typing import Optional, Dict

class CountryBase(BaseModel):
    id: int
    name: str
    countryCode: str
    dialingCode: str

class Country(BaseModel):
    id: int
    name: str
    countryCode: str
    dialingCode: str

    class Config:
        orm_mode = True

class CountryCreate(BaseModel):
    countryCode: str
    name: str
    dialingCode: str

class CountrySummary(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
        from_attributes = True

class OperatorBase(BaseModel):
    name: str
    # email: str
    status: str

class OperatorCreate(OperatorBase):
    country_id: int

class OperatorUpdate(BaseModel):
    name: Optional[str] = None
    # email: Optional[str] = None
    status: Optional[str] = None
    country_id: Optional[int] = None

class Operator(BaseModel):
    id: int
    name: str
    # email: str
    status: str
    country: Optional[CountrySummary] = None

    class Config:
        orm_mode = True

class OperatorSummary(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class AdvertiserBase(BaseModel):
    name: str
    company_name: str
    email: str
    status: str
    sendOtpUrl: str
    verifyOtpUrl: str
    statusCheckUrl: str
    capping: str

class AdvertiserCreate(AdvertiserBase):
    operator_id: int
    country_id: int  # Add country_id field
    fallback_advertiser_id: Optional[int] = None  # Add fallback_advertiser_id field

class Advertiser(BaseModel):
    id: int
    name: str
    company_name: str
    country: Optional[CountrySummary] = None  # Add country field
    email: str
    status: str
    sendOtpUrl: str
    verifyOtpUrl: str
    statusCheckUrl: str
    capping: str
    operator: Optional[OperatorSummary] = None
    fallback_advertiser: Optional['AdvertiserSummary'] = None  # Add fallback_advertiser field
    class Config:
        orm_mode = True

class AdvertiserSummary(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class AdvertiserUpdate(BaseModel):
    company_name: str = None
    country_id: int = None  # Add country_id field
    email: str = None
    status: str = None
    sendOtpUrl: str = None
    verifyOtpUrl: str = None
    statusCheckUrl: str = None
    capping: Optional[str] = None
    operator_id: int = None
    fallback_advertiser_id: Optional[int] = None  # Add fallback_advertiser_id field

from pydantic import BaseModel

class PublisherBase(BaseModel):
    name: str
    company_name: str
    # email: str
    block_rule: str
    status: str
    cap: int  # Add cap attribute

class PublisherCreate(PublisherBase):
    pass

class PublisherUpdate(PublisherBase):
    pass

class Publisher(PublisherBase):
    id: int

    class Config:
        orm_mode = True

class PublisherSummary(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class CampaignBase(BaseModel):
    name: str
    publisherPrice: float
    advertiserPrice: float
    fallbackEnabled: bool

class CampaignCreate(CampaignBase):
    publisher_id: int
    country_id: int
    operator_id: int
    advertiser_id: int
    # redirection_advertiser_id: Optional[int] = None

class Campaign(BaseModel):
    id: int
    name: str
    publisherPrice: float
    advertiserPrice: float
    fallbackEnabled: bool
    isLive: bool
    publisher: PublisherSummary
    country: CountrySummary
    operator: OperatorSummary
    advertiser: AdvertiserSummary
    # redirection_advertiser: Optional[AdvertiserSummary] = None

    class Config:
        orm_mode = True

class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    publisher_id: Optional[int] = None
    country_id: Optional[int] = None
    operator_id: Optional[int] = None
    advertiser_id: Optional[int] = None
    publisherPrice: Optional[float] = None
    advertiserPrice: Optional[float] = None
    fallbackEnabled: Optional[bool] = None
    isLive: Optional[bool] = None
    # redirection_advertiser_id: Optional[int] = None

class UserBase(BaseModel):
    firstName: str
    lastName: str
    username: EmailStr

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: EmailStr
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class ElasticSearch(BaseModel):
    name: str
    role: str
    email: str
    experiance: str

class ElasticsearchRequest(BaseModel):
    document: Dict[str, str]