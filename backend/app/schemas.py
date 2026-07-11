from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"


class ExceptionStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class ExceptionBase(BaseModel):
    date: datetime
    plant_id: str
    product_code: str
    planned_units: float
    units_produced: float
    production_ratio: float
    deficit_units: float
    severity: Severity
    status: ExceptionStatus = ExceptionStatus.OPEN


class ExceptionCreate(ExceptionBase):
    pass


class ExceptionUpdate(BaseModel):
    status: ExceptionStatus


class ExceptionResponse(ExceptionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class TrendDataPoint(BaseModel):
    date: datetime
    planned_units: Optional[float]
    units_produced: Optional[float]
    production_ratio: Optional[float]


class ExceptionDetail(ExceptionResponse):
    trend: List[TrendDataPoint]


class ExceptionListResponse(BaseModel):
    items: List[ExceptionResponse]
    total: int
    page: int
    page_size: int


class DashboardSummary(BaseModel):
    total_exceptions: int
    open_count: int
    acknowledged_count: int
    resolved_count: int
    high_severity_count: int
    medium_severity_count: int
    exceptions_by_date: List[dict]
    exceptions_by_plant: List[dict]
    exceptions_by_product: List[dict]
