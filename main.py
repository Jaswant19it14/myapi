from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from models import Base, Country as CountryModel, Operator as OperatorModel, Advertiser as AdvertiserModel, Publisher as PublisherModel, Campaign as CampaignModel, User
from database import engine, SessionLocal
from schemas import CountryCreate, Country, OperatorCreate, OperatorUpdate, Operator, AdvertiserCreate, AdvertiserUpdate, Advertiser, PublisherCreate, PublisherUpdate, Publisher, CampaignCreate, CampaignUpdate, UserCreate, UserLogin
import schemas  # Add this import
from crud import (
    create_country, get_countries, update_country, delete_country,
    create_operator, update_operator, delete_operator, get_operators_by_country, get_all_operators,
    create_advertiser, get_advertisers_by_operator, get_all_advertisers,
    update_advertiser, delete_advertiser,
    create_publisher, get_publishers, update_publisher, delete_publisher,
    create_campaign, get_campaigns, get_campaign, update_campaign, delete_campaign,
    create_user, authenticate_user, create_user_token  # Add create_user_token
)
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from auth import verify_token
from sqlalchemy.exc import IntegrityError
import logging

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Advertising Platform API",
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
    return create_country(db, country)

@app.get("/countries/", response_model=list[schemas.Country])
def list_countries(db: Session = Depends(get_db)):
    """Get a list of all countries"""
    return get_countries(db)

@app.put("/countries/{country_id}/", response_model=schemas.Country)
def edit_country(country_id: int, country: schemas.CountryCreate, db: Session = Depends(get_db)):
    """Edit a country by ID"""
    return update_country(db, country_id, country)

@app.delete("/countries/{country_id}/", response_model=schemas.Country)
def remove_country(country_id: int, db: Session = Depends(get_db)):
    """Delete a country by ID"""
    try:
        return delete_country(db, country_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete country with linked operators, advertisers, or campaigns")

# Operator Endpoints
@app.post("/operators/", response_model=schemas.Operator)
def add_operator(operator: schemas.OperatorCreate, db: Session = Depends(get_db)):
    """Create a new operator"""
    return create_operator(db, operator)

@app.get("/operators/", response_model=list[schemas.Operator])
def list_all_operators(db: Session = Depends(get_db)):
    """Get a list of all operators"""
    operators = get_all_operators(db)
    return operators

@app.get("/countries/{country_id}/operators/", response_model=list[schemas.Operator])
def list_operators(country_id: int, db: Session = Depends(get_db)):
    """Get a list of operators for a specific country"""
    operators = get_operators_by_country(db, country_id)
    return operators

@app.put("/operators/{operator_id}/", response_model=schemas.Operator)
def edit_operator(operator_id: int, operator: schemas.OperatorUpdate, db: Session = Depends(get_db)):
    """Edit an operator by ID"""
    return update_operator(db, operator_id, operator)

@app.delete("/operators/{operator_id}/", response_model=schemas.Operator)
def remove_operator(operator_id: int, db: Session = Depends(get_db)):
    """Delete an operator by ID"""
    try:
        return delete_operator(db, operator_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete operator with linked advertisers or campaigns")

# Advertiser Endpoints
@app.post("/advertisers/", response_model=schemas.Advertiser)
def add_advertiser(advertiser: schemas.AdvertiserCreate, db: Session = Depends(get_db)):
    """Create a new advertiser"""
    return create_advertiser(db, advertiser)

@app.get("/operators/{operator_id}/advertisers/", response_model=list[schemas.Advertiser])
def list_advertisers(operator_id: int, db: Session = Depends(get_db)):
    """Get a list of advertisers for a specific operator"""
    return get_advertisers_by_operator(db, operator_id)

@app.get("/advertisers/", response_model=list[schemas.Advertiser])
def list_all_advertisers(db: Session = Depends(get_db)):
    """Get a list of all advertisers"""
    advertisers = get_all_advertisers(db)
    advertiser_list = []
    for advertiser in advertisers:
        operator = db.query(OperatorModel).filter(OperatorModel.id == advertiser.operator_id).first()
        country = db.query(CountryModel).filter(CountryModel.id == advertiser.country_id).first()
        if operator and country:
            advertiser_dict = advertiser.__dict__.copy()
            advertiser_dict['operator'] = schemas.OperatorSummary(id=operator.id, name=operator.name)
            advertiser_dict['country'] = schemas.CountrySummary(id=country.id, name=country.name)
            advertiser_list.append(schemas.Advertiser(**advertiser_dict))
        else:
            advertiser_list.append(schemas.Advertiser.from_orm(advertiser))
    return advertiser_list

@app.put("/advertisers/{advertiser_id}/", response_model=schemas.Advertiser)
def update_advertiser_details(advertiser_id: int, advertiser: schemas.AdvertiserUpdate, db: Session = Depends(get_db)):
    """Update an advertiser's details"""
    return update_advertiser(db, advertiser_id, advertiser)

@app.delete("/advertisers/{advertiser_id}/", response_model=schemas.Advertiser)
def remove_advertiser(advertiser_id: int, db: Session = Depends(get_db)):
    """Delete an advertiser"""
    try:
        return delete_advertiser(db, advertiser_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete advertiser with linked campaigns")

# Publisher Endpoints
@app.post("/publishers/", response_model=schemas.Publisher)
def add_publisher(publisher: schemas.PublisherCreate, db: Session = Depends(get_db)):
    """Create a new publisher"""
    return create_publisher(db, publisher)

@app.get("/publishers/", response_model=list[schemas.Publisher])
def list_publishers(db: Session = Depends(get_db)):
    """Get a list of all publishers"""
    return get_publishers(db)

@app.put("/publishers/{publisher_id}/", response_model=schemas.Publisher)
def edit_publisher(publisher_id: int, publisher: schemas.PublisherUpdate, db: Session = Depends(get_db)):
    """Edit a publisher by ID"""
    return update_publisher(db, publisher_id, publisher)

@app.delete("/publishers/{publisher_id}/", response_model=schemas.Publisher)
def remove_publisher(publisher_id: int, db: Session = Depends(get_db)):
    """Delete a publisher by ID"""
    try:
        return delete_publisher(db, publisher_id)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete publisher with linked campaigns")

# Campaign Endpoints
@app.post("/campaigns/", response_model=schemas.Campaign)
def add_campaign(campaign: schemas.CampaignCreate, db: Session = Depends(get_db)):
    """Create a new campaign"""
    return create_campaign(db, campaign)

@app.get("/campaigns/", response_model=list[schemas.Campaign])
def list_campaigns(db: Session = Depends(get_db)):
    """Get a list of all campaigns"""
    campaigns = db.query(CampaignModel).all()
    campaign_list = []
    for campaign in campaigns:
        publisher = db.query(PublisherModel).filter(PublisherModel.id == campaign.publisher_id).first()
        country = db.query(CountryModel).filter(CountryModel.id == campaign.country_id).first()
        operator = db.query(OperatorModel).filter(OperatorModel.id == campaign.operator_id).first()
        advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.advertiser_id).first()
        redirection_advertiser = None
        if campaign.redirection_advertiser_id:
            redirection_advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.redirection_advertiser_id).first()
        
        campaign_dict = campaign.__dict__.copy()
        if publisher:
            campaign_dict['publisher'] = schemas.PublisherSummary(id=publisher.id, name=publisher.name)
        if country:
            campaign_dict['country'] = schemas.CountrySummary(id=country.id, name=country.name)
        if operator:
            campaign_dict['operator'] = schemas.OperatorSummary(id=operator.id, name=operator.name)
        if advertiser:
            campaign_dict['advertiser'] = schemas.AdvertiserSummary(id=advertiser.id, name=advertiser.name)
        if redirection_advertiser:
            campaign_dict['redirection_advertiser'] = schemas.AdvertiserSummary(id=redirection_advertiser.id, name=redirection_advertiser.name)
        
        campaign_list.append(schemas.Campaign(**campaign_dict))
    return campaign_list

@app.get("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def get_campaign_by_id(campaign_id: int, db: Session = Depends(get_db)):
    """Get a campaign by ID"""
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    campaign.publisher = db.query(PublisherModel).filter(PublisherModel.id == campaign.publisher_id).first()
    campaign.country = db.query(CountryModel).filter(CountryModel.id == campaign.country_id).first()
    campaign.operator = db.query(OperatorModel).filter(OperatorModel.id == campaign.operator_id).first()
    campaign.advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.advertiser_id).first()
    if campaign.redirection_advertiser_id:
        campaign.redirection_advertiser = db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.redirection_advertiser_id).first()
    return campaign

@app.put("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def update_campaign_by_id(campaign_id: int, campaign: schemas.CampaignUpdate, db: Session = Depends(get_db)):
    """Update a campaign's details"""
    # Ensure related records exist
    if campaign.publisher_id and not db.query(PublisherModel).filter(PublisherModel.id == campaign.publisher_id).first():
        raise HTTPException(status_code=404, detail="Publisher not found")
    if campaign.country_id and not db.query(Country).filter(Country.id == campaign.country_id).first():
        raise HTTPException(status_code=404, detail="Country not found")
    if campaign.operator_id and not db.query(OperatorModel).filter(OperatorModel.id == campaign.operator_id).first():
        raise HTTPException(status_code=404, detail="Operator not found")
    if campaign.advertiser_id and not db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.advertiser_id).first():
        raise HTTPException(status_code=404, detail="Advertiser not found")
    if campaign.fallbackEnabled and campaign.redirection_advertiser_id:
        if not db.query(AdvertiserModel).filter(AdvertiserModel.id == campaign.redirection_advertiser_id).first():
            raise HTTPException(status_code=404, detail="Redirection Advertiser not found")

    db_campaign = update_campaign(db, campaign_id, campaign)
    if db_campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return db_campaign

@app.delete("/campaigns/{campaign_id}", response_model=schemas.Campaign)
def delete_campaign_by_id(campaign_id: int, db: Session = Depends(get_db)):
    """Delete a campaign"""
    try:
        db_campaign = delete_campaign(db, campaign_id)
        if db_campaign is None:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return db_campaign
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Cannot delete campaign with linked records")

# User Endpoints
@app.post("/register/", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = create_user(db, user)
    return db_user

@app.post("/login/")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login a user"""
    db_user = authenticate_user(db, form_data.username, form_data.password)
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = create_user_token(db_user)
    return {"access_token": access_token, "token_type": "bearer", "username": db_user.username}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    username = verify_token(token)
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user