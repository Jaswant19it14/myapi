from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class Country(Base):
    __tablename__ = "countries"
    id = Column(Integer, primary_key=True, index=True)
    countryCode = Column(String(10), unique=True, index=True)  # New field
    name = Column(String(100), unique=True, index=True)
    dialingCode = Column(String(10))
    operators = relationship("Operator", back_populates="country")
    advertisers = relationship("Advertiser", back_populates="country")
    campaigns = relationship("Campaign", back_populates="country")

class Operator(Base):
    __tablename__ = "operators"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Ensure id is auto-incremented
    name = Column(String(100), index=True)  # Specify length
    email = Column(String(100), unique=True, index=True)  # Specify length
    status = Column(String(50))  # Specify length
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="RESTRICT"))
    country = relationship("Country", back_populates="operators")
    advertisers = relationship("Advertiser", back_populates="operator")
    campaigns = relationship("Campaign", back_populates="operator")

class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Ensure id is auto-incremented
    name = Column(String(100), unique=True, index=True)
    company_name = Column(String(100), index=True)  # Add company_name attribute
    email = Column(String(100), unique=True, index=True)
    block_rule = Column(String(100))  # Change blockRule to block_rule
    status = Column(String(100), unique=False, index=True)
    cap = Column(Integer, default=0)  # Add cap attribute with default value

class Advertiser(Base):
    __tablename__ = "advertisers"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Ensure id is auto-incremented
    name = Column(String(100), index=True)  # Specify length
    company_name = Column(String(100), index=True)  # Specify length
    email = Column(String(100), unique=True, index=True)  # Specify length
    status = Column(String(50))  # Specify length
    sendOtpUrl = Column(String(200))
    verifyOtpUrl = Column(String(200))
    statusCheckUrl = Column(String(200))
    capping = Column(String(100))  # Add capping attribute
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="RESTRICT"))  # Add country_id field
    operator_id = Column(Integer, ForeignKey("operators.id", ondelete="RESTRICT"))  # Update foreign key reference
    operator = relationship("Operator", back_populates="advertisers")
    country = relationship("Country", back_populates="advertisers")

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Ensure id is auto-incremented
    name = Column(String(100), unique=True, index=True)  # Ensure this field is unique
    publisher_id = Column(Integer, ForeignKey("publishers.id"))
    country_id = Column(Integer, ForeignKey("countries.id", ondelete="RESTRICT"))
    operator_id = Column(Integer, ForeignKey("operators.id", ondelete="RESTRICT"))  # Update foreign key reference
    advertiser_id = Column(Integer, ForeignKey("advertisers.id"))
    publisherPrice = Column(Float)
    advertiserPrice = Column(Float)
    fallbackEnabled = Column(Boolean, default=False)
    redirection_advertiser_id = Column(Integer, ForeignKey("advertisers.id"), nullable=True)

    # Relationships (optional, for easier querying)
    publisher = relationship("Publisher", foreign_keys=[publisher_id])
    country = relationship("Country", foreign_keys=[country_id], back_populates="campaigns")
    operator = relationship("Operator", foreign_keys=[operator_id], back_populates="campaigns")
    advertiser = relationship("Advertiser", foreign_keys=[advertiser_id])
    redirection_advertiser = relationship("Advertiser", foreign_keys=[redirection_advertiser_id])

    __table_args__ = (UniqueConstraint('name', name='uq_campaign_name'),)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    firstName = Column(String(100), nullable=False)
    lastName = Column(String(100), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(100), nullable=False)

