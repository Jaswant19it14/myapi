from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from models import Country, Operator, Advertiser, Publisher, Campaign, User
from schemas import CountryCreate, OperatorCreate, OperatorUpdate, AdvertiserCreate, AdvertiserUpdate, PublisherCreate, PublisherUpdate, CampaignCreate, CampaignUpdate, UserCreate, UserLogin
from fastapi import HTTPException
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import timedelta
import logging
import requests

logger = logging.getLogger(__name__)

# def send_to_elasticsearch(document: dict):
#     url = "https://localhost:9200/1/_doc"
#     headers = {"Content-Type": "application/json"}
#     auth = ("elastic", "M6U6CMqfXb*dQdLEJ*sq")  # Replace with actual username and password

#     logger.info("Sending document to Elasticsearch: %s", document)

#     response = requests.post(url, json=document, headers=headers, auth=auth, verify=False)  # Disable SSL verification for local testing

#     if response.status_code not in [200, 201]:
#         logger.error("Failed to send document to Elasticsearch: %s", response.json())
#         raise HTTPException(status_code=response.status_code, detail="Failed to send document to Elasticsearch")

#     logger.info("Document sent to Elasticsearch: %s", response.json())
#     return response.json()

# Country CRUD
def create_country(db: Session, country: CountryCreate):
    logger.info("Creating a new country: %s", country.name)
    db_country = Country(
        countryCode=country.countryCode,
        name=country.name,
        dialingCode=country.dialingCode
    )
    db.add(db_country)
    db.commit()
    db.refresh(db_country)
    logger.info("Created country: %s", db_country.__dict__)
    return db_country

def get_countries(db: Session):
    logger.info("Fetching all countries")
    countries = db.query(Country).all()
    logger.info("Fetched countries: %s", [country.__dict__ for country in countries])
    return countries

def update_country(db: Session, country_id: int, country: CountryCreate):
    logger.info("Updating country with ID: %d", country_id)
    db_country = db.query(Country).filter(Country.id == country_id).first()
    if not db_country:
        logger.error("Country with ID %d not found", country_id)
        raise HTTPException(status_code=404, detail="Country not found")
    for key, value in country.dict().items():
        setattr(db_country, key, value)
    db.commit()
    db.refresh(db_country)
    logger.info("Updated country: %s", db_country.__dict__)
    return db_country

def delete_country(db: Session, country_id: int):
    logger.info("Deleting country with ID: %d", country_id)
    country = db.query(Country).filter(Country.id == country_id).first()
    if not country:
        logger.error("Country with ID %d not found", country_id)
        raise HTTPException(status_code=404, detail="Country not found")
    
    # Check if the country is linked to any operators
    linked_operators = db.query(Operator).filter(Operator.country_id == country_id).first()
    if linked_operators:
        logger.error("Cannot delete country with linked operators")
        raise HTTPException(status_code=400, detail="Cannot delete country with linked operators")
    
    db.delete(country)
    db.commit()
    logger.info("Deleted country: %s", country.__dict__)
    return country

# Operator CRUD
def create_operator(db: Session, operator: OperatorCreate):
    logger.info("Creating a new operator: %s", operator.name)
    # Find the country by id
    country = db.query(Country).filter(Country.id == operator.country_id).first()
    if not country:
        logger.error("Country with ID %d not found", operator.country_id)
        raise HTTPException(status_code=404, detail="Country not found")

    db_operator = Operator(
        name=operator.name,
        status=operator.status,
        country_id=country.id
    )
    db.add(db_operator)
    db.commit()
    db.refresh(db_operator)
    logger.info("Created operator: %s", db_operator.__dict__)
    return db_operator

def update_operator(db: Session, operator_id: int, operator: OperatorUpdate):
    logger.info("Updating operator with ID: %d", operator_id)
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not db_operator:
        logger.error("Operator with ID %d not found", operator_id)
        raise HTTPException(status_code=404, detail="Operator not found")
    for key, value in operator.dict().items():
        if value is not None:
            setattr(db_operator, key, value)
    db.commit()
    db.refresh(db_operator)
    logger.info("Updated operator: %s", db_operator.__dict__)
    return db_operator

def delete_operator(db: Session, operator_id: int):
    logger.info("Deleting operator with ID: %d", operator_id)
    db_operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not db_operator:
        logger.error("Operator with ID %d not found", operator_id)
        raise HTTPException(status_code=404, detail="Operator not found")

    # Check if the operator is linked to any advertisers
    linked_advertisers = db.query(Advertiser).filter(Advertiser.operator_id == operator_id).first()
    if linked_advertisers:
        logger.error("Cannot delete operator with linked advertisers")
        raise HTTPException(status_code=400, detail="Cannot delete operator with linked advertisers")

    # Check if the operator is linked to any campaigns
    linked_campaigns = db.query(Campaign).filter(Campaign.operator_id == operator_id).first()
    if linked_campaigns:
        logger.error("Cannot delete operator with linked campaigns")
        raise HTTPException(status_code=400, detail="Cannot delete operator with linked campaigns")

    db.delete(db_operator)
    db.commit()
    logger.info("Deleted operator: %s", db_operator.__dict__)
    return db_operator

def get_all_operators(db: Session):
    logger.info("Fetching all operators")
    operators = db.query(Operator).options(joinedload(Operator.country)).all()
    logger.info("Fetched operators: %s", [operator.__dict__ for operator in operators])
    return operators

def get_operators_by_country(db: Session, country_id: int):
    logger.info("Fetching operators for country_id: %d", country_id)
    operators = db.query(Operator).options(joinedload(Operator.country)).filter(Operator.country_id == country_id, Operator.status == 'Active').all()
    logger.info("Fetched operators: %s", [operator.__dict__ for operator in operators])
    return operators

# Advertiser CRUD
def create_advertiser(db: Session, advertiser: AdvertiserCreate):
    logger.info("Creating a new advertiser: %s", advertiser.name)
    db_advertiser = Advertiser(
        name=advertiser.name,
        company_name=advertiser.company_name,
        email=advertiser.email,
        status=advertiser.status,
        sendOtpUrl=advertiser.sendOtpUrl,
        verifyOtpUrl=advertiser.verifyOtpUrl,
        statusCheckUrl=advertiser.statusCheckUrl,
        capping=advertiser.capping,
        operator_id=advertiser.operator_id,
        country_id=advertiser.country_id,
        # fallback_advertiser_id=advertiser.fallback_advertiser_id
    )
    db.add(db_advertiser)
    db.commit()
    db.refresh(db_advertiser)
    logger.info("Created advertiser: %s", db_advertiser.__dict__)
    return db_advertiser

def get_advertisers_by_operator(db: Session, operator_id: int):
    logger.info("Fetching advertisers for operator_id: %d", operator_id)
    advertisers = db.query(Advertiser).options(joinedload(Advertiser.operator)).filter(Advertiser.operator_id == operator_id).all()
    logger.info("Fetched advertisers: %s", [advertiser.__dict__ for advertiser in advertisers])
    return advertisers

def get_all_advertisers(db: Session):
    logger.info("Fetching all advertisers")
    advertisers = db.query(Advertiser).options(joinedload(Advertiser.operator), joinedload(Advertiser.country)).all()
    logger.info("Fetched advertisers: %s", [advertiser.__dict__ for advertiser in advertisers])
    return advertisers

def update_advertiser(db: Session, advertiser_id: int, advertiser: AdvertiserUpdate):
    logger.info("Updating advertiser with ID: %d", advertiser_id)
    db_advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not db_advertiser:
        logger.error("Advertiser with ID %d not found", advertiser_id)
        raise HTTPException(status_code=404, detail="Advertiser not found")
    for key, value in advertiser.dict().items():
        if value is not None:
            setattr(db_advertiser, key, value)
    db.commit()
    db.refresh(db_advertiser)
    logger.info("Updated advertiser: %s", db_advertiser.__dict__)
    return db_advertiser

def delete_advertiser(db: Session, advertiser_id: int):
    logger.info("Deleting advertiser with ID: %d", advertiser_id)
    db_advertiser = db.query(Advertiser).filter(Advertiser.id == advertiser_id).first()
    if not db_advertiser:
        logger.error("Advertiser with ID %d not found", advertiser_id)
        raise HTTPException(status_code=404, detail="Advertiser not found")
    db.delete(db_advertiser)
    db.commit()
    logger.info("Deleted advertiser: %s", db_advertiser.__dict__)
    return db_advertiser

# Publisher CRUD
def create_publisher(db: Session, publisher: PublisherCreate):
    logger.info("Creating a new publisher: %s", publisher.name)
    # Check for duplicate email
    # existing_publisher = db.query(Publisher).filter(Publisher.email == publisher.email).first()
    # if existing_publisher:
    #     logger.error("Email already registered: %s", publisher.email)
    #     raise HTTPException(status_code=400, detail="Email already registered")
    
    db_publisher = Publisher(
        name=publisher.name,
        company_name=publisher.company_name,
        # email=publisher.email,
        block_rule=publisher.block_rule,  # Change blockRule to block_rule
        status=publisher.status,  # Add company_name field
        cap=publisher.cap  # Add cap field
    )
    db.add(db_publisher)
    db.commit()
    db.refresh(db_publisher)
    logger.info("Created publisher: %s", db_publisher.__dict__)
    return db_publisher

def get_publishers(db: Session):
    logger.info("Fetching all publishers")
    publishers = db.query(Publisher).all()
    logger.info("Fetched publishers: %s", [publisher.__dict__ for publisher in publishers])
    return publishers

def update_publisher(db: Session, publisher_id: int, publisher: PublisherUpdate):
    logger.info("Updating publisher with ID: %d", publisher_id)
    db_publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not db_publisher:
        logger.error("Publisher with ID %d not found", publisher_id)
        raise HTTPException(status_code=404, detail="Publisher not found")
    for key, value in publisher.dict().items():
        setattr(db_publisher, key, value)
    db.commit()
    db.refresh(db_publisher)
    logger.info("Updated publisher: %s", db_publisher.__dict__)
    return db_publisher

def delete_publisher(db: Session, publisher_id: int):
    logger.info("Deleting publisher with ID: %d", publisher_id)
    db_publisher = db.query(Publisher).filter(Publisher.id == publisher_id).first()
    if not db_publisher:
        logger.error("Publisher with ID %d not found", publisher_id)
        raise HTTPException(status_code=404, detail="Publisher not found")

    # Delete all campaigns associated with the publisher
    db.query(Campaign).filter(Campaign.publisher_id == db_publisher.id).delete()

    db.delete(db_publisher)
    db.commit()
    logger.info("Deleted publisher: %s", db_publisher.__dict__)
    return db_publisher

# Campaign CRUD
def create_campaign(db: Session, campaign: CampaignCreate):
    logger.info("Creating a new campaign: %s", campaign.name)
    # Find the publisher by id
    publisher = db.query(Publisher).filter(Publisher.id == campaign.publisher_id).first()
    if not publisher:
        logger.error("Publisher with ID %d not found", campaign.publisher_id)
        raise HTTPException(status_code=404, detail="Publisher not found")

    # Find the country by id
    country = db.query(Country).filter(Country.id == campaign.country_id).first()
    if not country:
        logger.error("Country with ID %d not found", campaign.country_id)
        raise HTTPException(status_code=404, detail="Country not found")

    # Find the operator by id
    operator = db.query(Operator).filter(Operator.id == campaign.operator_id).first()
    if not operator:
        logger.error("Operator with ID %d not found", campaign.operator_id)
        raise HTTPException(status_code=404, detail="Operator not found")

    # Find the advertiser by id
    advertiser = db.query(Advertiser).filter(Advertiser.id == campaign.advertiser_id).first()
    if not advertiser:
        logger.error("Advertiser with ID %d not found", campaign.advertiser_id)
        raise HTTPException(status_code=404, detail="Advertiser not found")

    db_campaign = Campaign(
        name=campaign.name,
        publisher_id=publisher.id,
        country_id=country.id,
        operator_id=operator.id,
        advertiser_id=advertiser.id,
        publisherPrice=campaign.publisherPrice,
        advertiserPrice=campaign.advertiserPrice,
        fallbackEnabled=campaign.fallbackEnabled,
    )
    try:
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        logger.info("Created campaign: %s", db_campaign.__dict__)
    except IntegrityError:
        db.rollback()
        logger.error("Campaign with name %s already exists", campaign.name)
        raise HTTPException(status_code=400, detail="Campaign with this name already exists")

    return db_campaign

def get_campaigns(db: Session):
    logger.info("Fetching all campaigns")
    campaigns = db.query(Campaign).all()
    for campaign in campaigns:
        campaign.publisher_id = campaign.publisher.id if campaign.publisher else None
        campaign.country_id = campaign.country.id if campaign.country else None
        campaign.operator_id = campaign.operator.id if campaign.operator else None
        campaign.advertiser_id = campaign.advertiser.id if campaign.advertiser else None
    logger.info("Fetched campaigns: %s", [campaign.__dict__ for campaign in campaigns])
    return campaigns

def get_campaign(db: Session, campaign_id: int):
    logger.info("Fetching campaign with ID: %d", campaign_id)
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if campaign:
        campaign.publisher_id = campaign.publisher.id if campaign.publisher else None
        campaign.country_id = campaign.country.id if campaign.country else None
        campaign.operator_id = campaign.operator.id if campaign.operator else None
        campaign.advertiser_id = campaign.advertiser.id if campaign.advertiser else None
        logger.info("Fetched campaign: %s", campaign.__dict__)
    else:
        logger.error("Campaign with ID %d not found", campaign_id)
    return campaign

def update_campaign(db: Session, campaign_id: int, campaign: CampaignUpdate):
    logger.info("Updating campaign with ID: %d", campaign_id)
    db_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not db_campaign:
        logger.error("Campaign with ID %d not found", campaign_id)
        raise HTTPException(status_code=404, detail="Campaign not found")
    for key, value in campaign.dict().items():
        if value is not None:
            setattr(db_campaign, key, value)
    db.commit()
    db.refresh(db_campaign)
    logger.info("Updated campaign: %s", db_campaign.__dict__)
    return db_campaign

def delete_campaign(db: Session, campaign_id: int):
    logger.info("Deleting campaign with ID: %d", campaign_id)
    db_campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not db_campaign:
        logger.error("Campaign with ID %d not found", campaign_id)
        raise HTTPException(status_code=404, detail="Campaign not found")
    db.delete(db_campaign)
    db.commit()
    logger.info("Deleted campaign: %s", db_campaign.__dict__)
    return db_campaign

# User CRUD
def create_user(db: Session, user: UserCreate):
    logger.info("Creating a new user: %s", user.username)
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
    logger.info("Created user: %s", db_user.__dict__)
    return db_user

def authenticate_user(db: Session, username: str, password: str):
    logger.info("Authenticating user: %s", username)
    user = db.query(User).filter(User.username == username).first()
    if not user:
        logger.error("User with username %s not found", username)
        return None
    if not verify_password(password, user.password):
        logger.error("Invalid password for user: %s", username)
        return None
    logger.info("Authenticated user: %s", user.__dict__)
    return user

def create_user_token(user: User):
    logger.info("Creating token for user: %s", user.username)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info("Created token for user: %s", user.__dict__)
    return access_token

