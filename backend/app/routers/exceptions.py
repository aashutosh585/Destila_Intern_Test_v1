from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from .. import schemas, crud, models
from ..database import get_db

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


@router.get("", response_model=schemas.ExceptionListResponse)
def list_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    product_code: Optional[str] = Query(None),
    severity: Optional[str] = Query(None, pattern="^(high|medium)$"),
    status: Optional[str] = Query(None, pattern="^(open|acknowledged|resolved)$"),
    plant_id: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    List exceptions with filtering and pagination.
    Default sorting: date descending, worst deficit first within each day.
    """
    skip = (page - 1) * page_size
    
    # Parse dates if provided
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None
    
    exceptions, total = crud.get_exceptions(
        db=db,
        skip=skip,
        limit=page_size,
        product_code=product_code,
        severity=severity,
        status=status,
        plant_id=plant_id,
        start_date=start_dt,
        end_date=end_dt
    )
    
    return schemas.ExceptionListResponse(
        items=exceptions,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{exception_id}", response_model=schemas.ExceptionDetail)
def get_exception_detail(exception_id: int, db: Session = Depends(get_db)):
    """
    Get detailed exception information including 7-day trend.
    """
    exception = crud.get_exception(db, exception_id)
    if not exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception with id {exception_id} not found"
        )
    
    trend = crud.get_exception_trend(db, exception_id)
    
    return schemas.ExceptionDetail(
        id=exception.id,
        date=exception.date,
        plant_id=exception.plant_id,
        product_code=exception.product_code,
        planned_units=exception.planned_units,
        units_produced=exception.units_produced,
        production_ratio=exception.production_ratio,
        deficit_units=exception.deficit_units,
        severity=exception.severity,
        status=exception.status,
        created_at=exception.created_at,
        updated_at=exception.updated_at,
        trend=trend
    )


@router.patch("/{exception_id}", response_model=schemas.ExceptionResponse)
def update_exception(
    exception_id: int,
    exception_update: schemas.ExceptionUpdate,
    db: Session = Depends(get_db)
):
    """
    Update exception status (open → acknowledged → resolved).
    """
    # Validate status
    valid_statuses = [s.value for s in models.ExceptionStatus]
    if exception_update.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    exception = crud.update_exception_status(
        db=db,
        exception_id=exception_id,
        status=exception_update.status
    )
    
    if not exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception with id {exception_id} not found"
        )
    
    return exception
