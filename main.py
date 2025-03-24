from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import Base, Country as CountryModel, Operator as OperatorModel, Advertiser as AdvertiserModel, Publisher as PublisherModel, Campaign as CampaignModel, User
from database import engine, SessionLocal
from schemas import Country, OperatorCreate, OperatorUpdate, Operator, AdvertiserCreate, AdvertiserUpdate, Advertiser, PublisherCreate, PublisherUpdate, Publisher, CampaignCreate, CampaignUpdate, UserCreate, UserLogin
import schemas  # Add this import
from crud import (
    create_country, get_countries, update_country, delete_country,
    create_operator, update_operator, delete_operator, get_operators_by_country, get_all_operators,
    create_advertiser, get_advertisers_by_operator, get_all_advertisers,
    update_advertiser, delete_advertiser,
    create_publisher, get_publishers, update_publisher, delete_publisher,
    create_campaign, get_campaigns, get_campaign, update_campaign, delete_campaign,
    create_user, authenticate_user, create_user_token,  # Add create_user_token
    # send_to_elasticsearch  # Add send_to_elasticsearch
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import verify_token
from sqlalchemy.exc import IntegrityError
import logging
from logging_config import setup_logging

Base.metadata.create_all(bind=engine)

# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="In-App Platform API",
    description="API for managing advertising campaigns",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Country Endpoints
@app.post("/countries/", response_model=schemas.Country)
def add_country(country: schemas.CountryCreate, db: Session = Depends(get_db)):
    """Create a new country"""
    logger.info("Creating a new country: %s", country.name)
    return create_country(db, country)

@app.get("/countries/", response_model=list[schemas.Country])
def list_countries(db: Session = Depends(get_db)):
    """Get a list of all countries"""
    logger.info("Fetching all countries")
    return get_countries(db)

@app.put("/countries/{country_id}/", response_model=schemas.Country)
def edit_country(country_id: int, country: schemas.CountryCreate, db: Session = Depends(get_db)):
    """Edit a country by ID"""
    logger.info("Editing country with ID: %d", country_id)
    return update_country(db, country_id, country)

@app.delete("/countries/{country_id}/", response_model=schemas.Country)
def remove_country(country_id: int, db: Session = Depends(get_db)):
    """Delete a country by ID"""
    logger.info("Deleting country with ID: %d", country_id)
    try:
        return delete_country(db, country_id)
    except IntegrityError:
        db.rollback()
        logger.error("Cannot delete country with linked operators, advertisers, or campaigns")
        raise HTTPException(status_code=400, detail="Cannot delete country with linked operators, advertisers, or campaigns")

# Operator Endpoints
@app.post("/operators/", response_model=schemas.Operator)
def add_operator(operator: schemas.OperatorCreate, db: Session = Depends(get_db)):
    """Create a new operator"""
    logger.info("Creating a new operator: %s", operator.name)
    return create_operator(db, operator)

@app.get("/operators/", response_model=list[schemas.Operator])
def list_all_operators(db: Session = Depends(get_db)):
    """Get a list of all operators"""
    logger.info("Fetching all operators")
    operators = get_all_operators(db)
    return operators

@app.get("/countries/{country_id}/operators/", response_model=list[schemas.Operator])
def list_operators(country_id: int, db: Session = Depends(get_db)):
    """Get a list of operators for a specific country"""
    logger.info("Fetching operators for country ID: %d", country_id)
    operators = get_operators_by_country(db, country_id)
    return operators

@app.put("/operators/{operator_id}/", response_model=schemas.Operator)
def edit_operator(operator_id: int, operator: schemas.OperatorUpdate, db: Session = Depends(get_db)):
    """Edit an operator by ID"""
    logger.info("Editing operator with ID: %d", operator_id)
    return update_operator(db, operator_id, operator)

@app.delete("/operators/{operator_id}/", response_model=schemas.Operator)
def remove_operator(operator_id: int, db: Session = Depends(get_db)):
    """Delete an operator by ID"""
    logger.info("Deleting operator with ID: %d", operator_id)
    try:
        return delete_operator(db, operator_id)
    except IntegrityError:
        db.rollback()
        logger.error("Cannot delete operator with linked advertisers or campaigns")
        raise HTTPException(status_code=400, detail="Cannot delete operator with linked advertisers or campaigns")

# Advertiser Endpoints
@app.post("/advertisers/", response_model=schemas.Advertiser)
def add_advertiser(advertiser: schemas.AdvertiserCreate, db: Session = Depends(get_db)):
    """Create a new advertiser"""
    logger.info("Creating a new advertiser: %s", advertiser.name)
    return create_advertiser(db, advertiser)

@app.get("/operators/{operator_id}/advertisers/", response_model=list[schemas.Advertiser])
def list_advertisers(operator_id: int, db: Session = Depends(get_db)):
    """Get a list of advertisers for a specific operator"""
    logger.info("Fetching advertisers for operator ID: %d", operator_id)
    return get_advertisers_by_operator(db, operator_id)

@app.get("/advertisers/", response_model=list[schemas.Advertiser])
def list_all_advertisers(db: Session = Depends(get_db)):
    """Get a list of all advertisers"""
    logger.info("Fetching all advertisers")
    advertisers = get_all_advertisers(db)
    advertiser_list = []
    for advertiser in advertisers:
        operator = db.query(OperatorModel).filter(OperatorModel.id == advertiser.operator_id).first()
        country = db.query(CountryModel).filter(CountryModel.id == advertiser.country_id).first()
        fallback_advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == advertiser.fallback_advertiser_id).first()
        advertiser_dict = advertiser.__dict__.copy()
        if operator:
            advertiser_dict['operator'] = schemas.OperatorSummary(id=operator.id, name=operator.name)
        if country:
            advertiser_dict['country'] = schemas.CountrySummary(id=country.id, name=country.name)
        if fallback_advertiser:
            advertiser_dict['fallback_advertiser'] = schemas.AdvertiserSummary(id=fallback_advertiser.id, name=fallback_advertiser.name)
        advertiser_list.append(schemas.Advertiser(**advertiser_dict))
    logger.info("Fetched %d advertisers", len(advertiser_list))
    return advertiser_list

@app.put("/advertisers/{advertiser_id}/", response_model=schemas.Advertiser)
def update_advertiser_details(advertiser_id: int, advertiser: schemas.AdvertiserUpdate, db: Session = Depends(get_db)):
    """Update an advertiser's details"""
    logger.info("Updating advertiser with ID: %d", advertiser_id)
    return update_advertiser(db, advertiser_id, advertiser)

@app.delete("/advertisers/{advertiser_id}/", response_model=schemas.Advertiser)
def remove_advertiser(advertiser_id: int, db: Session = Depends(get_db)):
    """Delete an advertiser"""
    logger.info("Deleting advertiser with ID: %d", advertiser_id)
    try:
        return delete_advertiser(db, advertiser_id)
    except IntegrityError:
        db.rollback()
        logger.error("Cannot delete advertiser with linked campaigns")
        raise HTTPException(status_code=400, detail="Cannot delete advertiser with linked campaigns")

# Publisher Endpoints
@app.post("/publishers/", response_model=schemas.Publisher)
def add_publisher(publisher: schemas.PublisherCreate, db: Session = Depends(get_db)):
    """Create a new publisher"""
    logger.info("Creating a new publisher: %s", publisher.name)
    return create_publisher(db, publisher)

@app.get("/publishers/", response_model=list[schemas.Publisher])
def list_publishers(db: Session = Depends(get_db)):
    """Get a list of all publishers"""
    logger.info("Fetching all publishers")
    return get_publishers(db)

@app.put("/publishers/{publisher_id}/", response_model=schemas.Publisher)
def edit_publisher(publisher_id: int, publisher: schemas.PublisherUpdate, db: Session = Depends(get_db)):
    """Edit a publisher by ID"""
    logger.info("Editing publisher with ID: %d", publisher_id)
    return update_publisher(db, publisher_id, publisher)

@app.delete("/publishers/{publisher_id}/", response_model=schemas.Publisher)
def remove_publisher(publisher_id: int, db: Session = Depends(get_db)):
    """Delete a publisher by ID"""
    logger.info("Deleting publisher with ID: %d", publisher_id)
    try:
        return delete_publisher(db, publisher_id)
    except IntegrityError:
        db.rollback()
        logger.error("Cannot delete publisher with linked campaigns")
        raise HTTPException(status_code=400, detail="Cannot delete publisher with linked campaigns")

# Campaign Endpoints
@app.post("/campaigns/", response_model=schemas.Campaign)
def add_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign"""
    logger.info("Creating a new campaign: %s", campaign.name)
    return create_campaign(db, campaign)

@app.get("/campaigns/", response_model=list[schemas.Campaign])
def list_campaigns(db: Session = Depends(get_db)):
    """Get a list of all campaigns"""
    logger.info("Fetching all campaigns")
    campaigns = db.query(CampaignModel).all()
    campaign_list = []
    for campaign in campaigns:
        publisher = db.query(PublisherModel).filter(PublisherModel.id == campaign.publisher_id).first()
        country = db.query(CountryModel).filter(CountryModel.id == campaign.country_id).first()
        operator = db.query(OperatorModel).filter(OperatorModel.id == campaign.operator_id).first()
        advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.advertiser_id).first()
        # redirection_advertiser = None
        # if campaign.redirection_advertiser_id:
        #     redirection_advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.redirection_advertiser_id).first()
        
        campaign_dict = campaign.__dict__.copy()
        if publisher:
            campaign_dict['publisher'] = schemas.PublisherSummary(id=publisher.id, name=publisher.name)
        if country:
            campaign_dict['country'] = schemas.CountrySummary(id=country.id, name=country.name)
        if operator:
            campaign_dict['operator'] = schemas.OperatorSummary(id=operator.id, name=operator.name)
        if advertiser:
            campaign_dict['advertiser'] = schemas.AdvertiserSummary(id=advertiser.id, name=advertiser.name)
        # if redirection_advertiser:
        #     campaign_dict['redirection_advertiser'] = schemas.AdvertiserSummary(id=redirection_advertiser.id, name=redirection_advertiser.name)
        
        campaign_list.append(schemas.Campaign(**campaign_dict))
    logger.info("Fetched %d campaigns", len(campaign_list))
    return campaign_list

@app.get("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def get_campaign_by_id(campaign_id: int, db: Session = Depends(get_db)):
    """Get a campaign by ID"""
    logger.info("Fetching campaign with ID: %d", campaign_id)
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if campaign is None:
        logger.error("Campaign with ID %d not found", campaign_id)
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.publisher = db.query(PublisherModel).filter(PublisherModel.id == campaign.publisher_id).first()
    campaign.country = db.query(CountryModel).filter(CountryModel.id == campaign.country_id).first()
    campaign.operator = db.query(OperatorModel).filter(OperatorModel.id == campaign.operator_id).first()
    campaign.advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.advertiser_id).first()
    # if campaign.redirection_advertiser_id:
    #     campaign.redirection_advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.redirection_advertiser_id).first()
    return campaign

@app.put("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def update_campaign_by_id(campaign_id: int, campaign: schemas.CampaignUpdate, db: Session = Depends(get_db)):
    """Update a campaign's details"""
    logger.info("Updating campaign with ID: %d", campaign_id)
    # Ensure related records exist
    if campaign.publisher_id and not db.query(PublisherModel).filter(PublisherModel.id == campaign.publisher_id).first():
        logger.error("Publisher with ID %d not found", campaign.publisher_id)
        raise HTTPException(status_code=404, detail="Publisher not found")
    if campaign.country_id and not db.query(Country).filter(Country.id == campaign.country_id).first():
        logger.error("Country with ID %d not found", campaign.country_id)
        raise HTTPException(status_code=404, detail="Country not found")
    if campaign.operator_id and not db.query(OperatorModel).filter(OperatorModel.id == campaign.operator_id).first():
        logger.error("Operator with ID %d not found", campaign.operator_id)
        raise HTTPException(status_code=404, detail="Operator not found")
    if campaign.advertiser_id and not db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.advertiser_id).first():
        logger.error("Advertiser with ID %d not found", campaign.advertiser_id)
        raise HTTPException(status_code=404, detail="Advertiser not found")
    # if campaign.fallbackEnabled and campaign.redirection_advertiser_id:
    #     if not db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.redirection_advertiser_id).first():
    #         logger.error("Redirection Advertiser with ID %d not found", campaign.redirection_advertiser_id)
    #         raise HTTPException(status_code=404, detail="Redirection Advertiser not found")

    db_campaign = update_campaign(db, campaign_id, campaign)
    if db_campaign is None:
        logger.error("Campaign with ID %d not found", campaign_id)
        raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign

@app.delete("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def delete_campaign_by_id(campaign_id: int, db: Session = Depends(get_db)):
    """Delete a campaign"""
    logger.info("Deleting campaign with ID: %d", campaign_id)
    try:
        db_campaign = delete_campaign(db, campaign_id)
        if db_campaign is None:
            logger.error("Campaign with ID %d not found", campaign_id)
            raise HTTPException(status_code=404, detail="Campaign not found")
        return db_campaign
    except IntegrityError:
        db.rollback()
        logger.error("Cannot delete campaign with linked records")
        raise HTTPException(status_code=400, detail="Cannot delete campaign with linked records")

# User Endpoints
@app.post("/register/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    logger.info("Registering a new user: %s", user.username)
    db_user = create_user(db, user)
    return db_user

@app.post("/login/")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login a user"""
    logger.info("User login attempt: %s", form_data.username)
    db_user = authenticate_user(db, form_data.username, form_data.password)
    if not db_user:
        logger.error("Invalid username or password for user: %s", form_data.username)
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = create_user_token(db_user)
    logger.info("User logged in: %s", form_data.username)
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_token(token)
    if username is None:
        logger.error("Invalid token")
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        logger.error("Invalid token for user: %s", username)
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


# @app.post("/send-to-elasticsearch/")
# def send_document(request: ElasticsearchRequest):
#     try:
#         result = send_to_elasticsearch(request.document)
#         return result
#     except HTTPException as e:
#         raise e
#     except Exception as e:
#         logger.error("An error occurred: %s", str(e))
#         raise HTTPException(status_code=500, detail="An internal error occurred")

# @app.get("/redis/publisher/{publisher_id}")
# def check_redis_publisher(publisher_id: int):
#     """Check if the Redis key for the publisher exists and its value"""
#     redis_key = f"PUB_{publisher_id}"
#     value = redis_client.get(redis_key)
#     if value is None:
#         logger.error("Redis key %s not found", redis_key)
#         raise HTTPException(status_code=404, detail="Redis key not found")
#     logger.info("Redis key %s found with value %s", redis_key, value.decode())
#     return {"key": redis_key, "value": value.decode()}

