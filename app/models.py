from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Enum, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

import enum

Base = declarative_base()


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    field = Column(String)
    description = Column(String)
    filename = Column(String)
    
    okrs = relationship('Okr', back_populates="company", cascade="all, delete-orphan")


class Okr(Base):
    __tablename__ = "okr"
    id = Column(Integer, primary_key=True, index=True)
    is_objective = Column(Boolean)
    input_sentence = Column(String)
    upper_objective = Column(String)
    team = Column(String)
    guideline = Column(String)
    revision = Column(String)
    revision_description = Column(String)
    created_at = Column(DateTime,nullable=False, default=datetime.utcnow)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"))

    company = relationship("Company", back_populates="okrs")
    predictions = relationship('Prediction', back_populates="okr", cascade="all, delete-orphan")
    

class Prediction(Base):
    __tablename__ = "prediction"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String)
    score = Column(Integer)
    description = Column(String)
    okr_id = Column(Integer, ForeignKey("okr.id", ondelete="CASCADE"))
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    okr = relationship("Okr", back_populates="predictions")
    