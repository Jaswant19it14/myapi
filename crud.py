from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from models import Country, Operator, Advertiser, Publisher, Campaign, User
from schemas import CountryCreate, OperatorCreate, OperatorUpdate, AdvertiserCreate, AdvertiserUpdate, PublisherCreate, PublisherUpdate, CampaignCreate, CampaignUpdate, UserCreate, UserLogin
from fastapi import HTTPException
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta

# Country CRUD
def create_country(db: Session, country: CountryCreate):
    db_country = Country(
        countryCode=country.countryCode,
        name=country.name,
        dialingCode=country.dialingCode
    )
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    return db_country

def get_countries(db: Session):
    return db.query(Country).all()

def update_country(db: Session, country_id: int, country: CountryCreate):
    db_country = db.query(Country).filter(Country.id == country_id).first()
    if not db_country:
        raise HTTPException(status_code=404, detail="Country not found")
    for key, value in country.dict().items():
        setattr(db_country, key, value)
    db.commit()
    db.refresh(db_country)
    return db_country

def delete_country(db: Session, country_id: int):
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Check if the country is linked to any operators
    linked_operators = db.query(Operator).filter(Operator.country_id == country_id).first()
    if linked_operators:
        raise HTTPException(status_code=400, detail="Cannot delete country with linked operators")
    
    db.delete(country)
    db.commit()
    return country

# Operator CRUD
def create_operator(db: Session, operator: OperatorCreate):
    # Check if an operator with the same email already exists
    existing_operator = db.query(Operator).filter(Operator.email == operator.email).first()
    if existing_operator:
        raise HTTPException(status_code=400, detail="Operator with this email already exists")

    # Find the country by id
    country = db.query(Country).filter(Country.id == operator.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    db_operator = Operator(
        name=operator.name,
        email=operator.email,
        status=operator.status,
        country_id=country.id
    )
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    return db_operator

def update_operator(db: Session, operator_id: int, operator: OperatorUpdate):
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not db_operator:
        raise HTTPException(status_code=404, detail="Operator not found")
    for key, value in operator.dict().items():
        if value is not None:
            setattr(db_operator, key, value)
    db.commit()
    db.refresh(db_operator)
    return db_operator

def delete_operator(db: Session, operator_id: int):
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not db_operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Check if the operator is linked to any advertisers
    linked_advertisers = db.query(Advertiser).filter(Advertiser.operator_id == operator_id).first()
    if linked_advertisers:
        raise HTTPException(status_code=400, detail="Cannot delete operator with linked advertisers")

    # Check if the operator is linked to any campaigns
    linked_campaigns = db.query(Campaign).filter(Campaign.operator_id == operator_id).first()
    if linked_campaigns:
        raise HTTPException(status_code=400, detail="Cannot delete operator with linked campaigns")

    db.delete(db_operator)
    db.commit()
    return db_operator

def get_all_operators(db: Session):
    return db.query(Operator).options(joinedload(Operator.country)).all()

def get_operators_by_country(db: Session, country_id: int):
    return db.query(Operator).options(joinedload(Operator.country)).filter(Operator.country_id == country_id).all()

# Advertiser CRUD
def create_advertiser(db: Session, advertiser: AdvertiserCreate):
    # Find the operator by id
    operator = db.query(Operator).filter(Operator.id == advertiser.operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Find the country by id
    country = db.query(Country).filter(Country.id == advertiser.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    db_advertiser = Advertiser(
        name=advertiser.name,
        company_name=advertiser.company_name,
        email=advertiser.email,
        status=advertiser.status,
        sendOtpUrl=advertiser.sendOtpUrl,
        verifyOtpUrl=advertiser.verifyOtpUrl,
        statusCheckUrl=advertiser.statusCheckUrl,
        capping=advertiser.capping,
        operator_id=operator.id,
        country_id=country.id  # Add country_id field
    )
    try:
        db.add(db_advertiser)
        db.commit()
        db.refresh(db_advertiser)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Advertiser with this email already exists")
    return db_advertiser

def get_advertisers_by_operator(db: Session, operator_id: int):
    return db.query(Advertiser).options(joinedload(Advertiser.operator)).filter(Advertiser.operator_id == operator_id).all()

def get_all_advertisers(db: Session):
    return db.query(Advertiser).options(joinedload(Advertiser.operator), joinedload(Advertiser.country)).all()

def update_advertiser(db: Session, advertiser_id: int, advertiser: AdvertiserUpdate):
    db_advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not db_advertiser:
        raise HTTPException(status_code=404, detail="Advertiser not found")
    for key, value in advertiser.dict().items():
        if value is not None:
            setattr(db_advertiser, key, value)
    db.commit()
    db.refresh(db_advertiser)
    return db_advertiser

def delete_advertiser(db: Session, advertiser_id: int):
    db_advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not db_advertiser:
        raise HTTPException(status_code=404, detail="Advertiser not found")
    db.delete(db_advertiser)
    db.commit()
    return db_advertiser

# Publisher CRUD
def create_publisher(db: Session, publisher: PublisherCreate):
    # Check for duplicate email
    existing_publisher = db.query(Publisher).filter(Publisher.email == publisher.email).first()
    if existing_publisher:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_publisher = Publisher(
        name=publisher.name,
        company_name=publisher.company_name,
        email=publisher.email,
        block_rule=publisher.block_rule,  # Change blockRule to block_rule
        status=publisher.status,  # Add company_name field
        cap=publisher.cap  # Add cap field
    )
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

def get_publishers(db: Session):
    return db.query(Publisher).all()

def update_publisher(db: Session, publisher_id: int, publisher: PublisherUpdate):
    db_publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not db_publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")
    for key, value in publisher.dict().items():
        setattr(db_publisher, key, value)
    db.commit()
    db.refresh(db_publisher)
    return db_publisher

def delete_publisher(db: Session, publisher_id: int):
    db_publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not db_publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")

    # Delete all campaigns associated with the publisher
    db.query(Campaign).filter(Campaign.publisher_id == db_publisher.id).delete()

    db.delete(db_publisher)
    db.commit()
    return db_publisher

# Campaign CRUD
def create_campaign(db: Session, campaign: CampaignCreate):
    # Find the publisher by id
    publisher = db.query(Publisher).filter(Publisher.id == campaign.publisher_id).first()
    if not publisher:
        raise HTTPException(status_code=404, detail="Publisher not found")

    # Find the country by id
    country = db.query(Country).filter(Country.id == campaign.country_id).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    # Find the operator by id
    operator = db.query(Operator).filter(Operator.id == campaign.operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Find the advertiser by id
    advertiser = db.query(Advertiser).filter(Advertiser.id == campaign.advertiser_id).first()
    if not advertiser:
        raise HTTPException(status_code=404, detail="Advertiser not found")

    # Find the redirection advertiser by id (if provided and fallbackEnabled is true)
    redirection_advertiser = None
    if campaign.fallbackEnabled and campaign.redirection_advertiser_id:
        redirection_advertiser = db.query(Advertiser).filter(Advertiser.id == campaign.redirection_advertiser_id).first()
        if not redirection_advertiser:
            raise HTTPException(status_code=404, detail="Redirection Advertiser not found")

    db_campaign = Campaign(
        name=campaign.name,
        publisher_id=publisher.id,
        country_id=country.id,
        operator_id=operator.id,
        advertiser_id=advertiser.id,
        publisherPrice=campaign.publisherPrice,
        advertiserPrice=campaign.advertiserPrice,
        fallbackEnabled=campaign.fallbackEnabled,
        redirection_advertiser_id=redirection_advertiser.id if redirection_advertiser else None
    )
    try:
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Campaign with this name already exists")

    return db_campaign

def get_campaigns(db: Session):
    campaigns = db.query(Campaign).all()
    for campaign in campaigns:
        campaign.publisher_id = campaign.publisher.id if campaign.publisher else None
        campaign.country_id = campaign.country.id if campaign.country else None
        campaign.operator_id = campaign.operator.id if campaign.operator else None
        campaign.advertiser_id = campaign.advertiser.id if campaign.advertiser else None
        if campaign.redirection_advertiser_id:
            campaign.redirection_advertiser_id = campaign.redirection_advertiser.id if campaign.redirection_advertiser else None
    return campaigns

def get_campaign(db: Session, campaign_id: int):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign:
        campaign.publisher_id = campaign.publisher.id if campaign.publisher else None
        campaign.country_id = campaign.country.id if campaign.country else None
        campaign.operator_id = campaign.operator.id if campaign.operator else None
        campaign.advertiser_id = campaign.advertiser.id if campaign.advertiser else None
        if campaign.redirection_advertiser_id:
            campaign.redirection_advertiser_id = campaign.redirection_advertiser.id if campaign.redirection_advertiser else None
    return campaign

def update_campaign(db: Session, campaign_id: int, campaign: CampaignUpdate):
    db_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    for key, value in campaign.dict().items():
        if value is not None:
            setattr(db_campaign, key, value)
    db.commit()
    db.refresh(db_campaign)
    return db_campaign

def delete_campaign(db: Session, campaign_id: int):
    db_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not db_campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(db_campaign)
    db.commit()
    return db_campaign

# User CRUD
def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(
        firstName=user.firstName,
        lastName=user.lastName,
        username=user.username,
        password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

def create_user_token(user: User):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return access_token