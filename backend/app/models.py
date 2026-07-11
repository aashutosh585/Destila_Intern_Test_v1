from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, Index
from sqlalchemy.sql import func
from .database import Base
import enum


class Severity(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"


class ExceptionStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class RawPlan(Base):
    __tablename__ = "raw_plan"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_date = Column(String, nullable=False)
    plant = Column(String, nullable=False)
    sku = Column(String, nullable=False)
    planned_units = Column(Float, nullable=True)
    
    __table_args__ = {'extend_existing': True}


class RawProduction(Base):
    __tablename__ = "raw_production"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    plant_id = Column(String, nullable=False)
    product_code = Column(String, nullable=False)
    units_produced = Column(Integer, nullable=False)
    
    __table_args__ = {'extend_existing': True}


class CleanPlan(Base):
    __tablename__ = "clean_plan"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    plant_id = Column(String, nullable=False)
    product_code = Column(String, nullable=False)
    planned_units = Column(Float, nullable=False)
    
    __table_args__ = (
        Index('idx_clean_plan_date', 'date'),
        Index('idx_clean_plan_product', 'product_code'),
        Index('idx_clean_plan_plant', 'plant_id'),
    )


class CleanProduction(Base):
    __tablename__ = "clean_production"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    plant_id = Column(String, nullable=False)
    product_code = Column(String, nullable=False)
    units_produced = Column(Integer, nullable=False)
    
    __table_args__ = (
        Index('idx_clean_production_date', 'date'),
        Index('idx_clean_production_product', 'product_code'),
        Index('idx_clean_production_plant', 'plant_id'),
    )


class Exception(Base):
    __tablename__ = "exceptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False)
    plant_id = Column(String, nullable=False)
    product_code = Column(String, nullable=False)
    planned_units = Column(Float, nullable=False)
    units_produced = Column(Float, nullable=False)
    production_ratio = Column(Float, nullable=False)
    deficit_units = Column(Float, nullable=False)
    severity = Column(Enum(Severity), nullable=False)
    status = Column(Enum(ExceptionStatus), nullable=False, default=ExceptionStatus.OPEN)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_exceptions_date', 'date'),
        Index('idx_exceptions_product', 'product_code'),
        Index('idx_exceptions_plant', 'plant_id'),
        Index('idx_exceptions_severity', 'severity'),
        Index('idx_exceptions_status', 'status'),
        Index('idx_exceptions_composite', 'date', 'plant_id', 'product_code', unique=True),
    )


class ExceptionStatusHistory(Base):
    __tablename__ = "exception_status_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exception_id = Column(Integer, nullable=False)
    old_status = Column(Enum(ExceptionStatus), nullable=False)
    new_status = Column(Enum(ExceptionStatus), nullable=False)
    changed_at = Column(DateTime, server_default=func.now())
    
    __table_args__ = (
        Index('idx_status_history_exception', 'exception_id'),
    )
