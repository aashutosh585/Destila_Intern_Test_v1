from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text
from datetime import datetime, timedelta
from typing import List, Optional
from . import models, schemas


def get_exception(db: Session, exception_id: int) -> Optional[models.Exception]:
    return db.query(models.Exception).filter(models.Exception.id == exception_id).first()


def get_exceptions(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    product_code: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    plant_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> tuple[List[models.Exception], int]:
    query = db.query(models.Exception)
    
    # Apply filters
    if product_code:
        query = query.filter(models.Exception.product_code == product_code.upper())
    if severity:
        query = query.filter(models.Exception.severity == severity)
    if status:
        query = query.filter(models.Exception.status == status)
    if plant_id:
        query = query.filter(models.Exception.plant_id == plant_id.upper())
    if start_date:
        query = query.filter(models.Exception.date >= start_date)
    if end_date:
        query = query.filter(models.Exception.date <= end_date)
    
    # Get total count
    total = query.count()
    
    # Sort by date descending, then by deficit descending (worst first)
    query = query.order_by(desc(models.Exception.date), desc(models.Exception.deficit_units))
    
    # Apply pagination
    exceptions = query.offset(skip).limit(limit).all()
    
    return exceptions, total


def update_exception_status(
    db: Session,
    exception_id: int,
    status: str
) -> Optional[models.Exception]:
    exception = get_exception(db, exception_id)
    if not exception:
        return None
    
    # Record status change in history
    old_status = exception.status
    if old_status != status:
        history = models.ExceptionStatusHistory(
            exception_id=exception_id,
            old_status=old_status,
            new_status=status
        )
        db.add(history)
    
    exception.status = status
    db.commit()
    db.refresh(exception)
    return exception


def get_exception_trend(
    db: Session,
    exception_id: int
) -> List[dict]:
    exception = get_exception(db, exception_id)
    if not exception:
        return []
    
    # Get 7-day trend for the same plant and product
    end_date = exception.date
    start_date = end_date - timedelta(days=6)
    
    # Join clean_plan and clean_production for trend data
    trend_data = db.execute(text(f"""
        SELECT 
            cp.date,
            cp.planned_units,
            COALESCE(cpr.units_produced, 0) as units_produced,
            CASE 
                WHEN cp.planned_units > 0 THEN COALESCE(cpr.units_produced, 0) / cp.planned_units
                ELSE 0 
            END as production_ratio
        FROM clean_plan cp
        LEFT JOIN clean_production cpr ON 
            cp.date = cpr.date AND 
            cp.plant_id = cpr.plant_id AND 
            cp.product_code = cpr.product_code
        WHERE cp.plant_id = '{exception.plant_id}'
            AND cp.product_code = '{exception.product_code}'
            AND cp.date BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        ORDER BY cp.date ASC
    """)).fetchall()
    
    return [
        {
            "date": row[0],
            "planned_units": row[1],
            "units_produced": row[2],
            "production_ratio": row[3]
        }
        for row in trend_data
    ]


def get_dashboard_summary(db: Session) -> schemas.DashboardSummary:
    total_exceptions = db.query(models.Exception).count()
    open_count = db.query(models.Exception).filter(models.Exception.status == models.ExceptionStatus.OPEN).count()
    acknowledged_count = db.query(models.Exception).filter(models.Exception.status == models.ExceptionStatus.ACKNOWLEDGED).count()
    resolved_count = db.query(models.Exception).filter(models.Exception.status == models.ExceptionStatus.RESOLVED).count()
    high_severity_count = db.query(models.Exception).filter(models.Exception.severity == models.Severity.HIGH).count()
    medium_severity_count = db.query(models.Exception).filter(models.Exception.severity == models.Severity.MEDIUM).count()
    
    # Exceptions by date
    exceptions_by_date = db.execute(text("""
        SELECT date(date) as date, COUNT(*) as count
        FROM exceptions
        GROUP BY date(date)
        ORDER BY date DESC
        LIMIT 30
    """)).fetchall()
    
    # Exceptions by plant
    exceptions_by_plant = db.execute(text("""
        SELECT plant_id, COUNT(*) as count
        FROM exceptions
        GROUP BY plant_id
        ORDER BY count DESC
    """)).fetchall()
    
    # Exceptions by product
    exceptions_by_product = db.execute(text("""
        SELECT product_code, COUNT(*) as count
        FROM exceptions
        GROUP BY product_code
        ORDER BY count DESC
        LIMIT 10
    """)).fetchall()
    
    return schemas.DashboardSummary(
        total_exceptions=total_exceptions,
        open_count=open_count,
        acknowledged_count=acknowledged_count,
        resolved_count=resolved_count,
        high_severity_count=high_severity_count,
        medium_severity_count=medium_severity_count,
        exceptions_by_date=[{"date": str(row[0]), "count": row[1]} for row in exceptions_by_date],
        exceptions_by_plant=[{"plant_id": row[0], "count": row[1]} for row in exceptions_by_plant],
        exceptions_by_product=[{"product_code": row[0], "count": row[1]} for row in exceptions_by_product]
    )
