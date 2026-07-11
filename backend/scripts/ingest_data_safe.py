import pandas as pd
from sqlalchemy import create_engine, text
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine, DATABASE_URL
from app.models import RawPlan, RawProduction, CleanPlan, CleanProduction, Exception as ExceptionModel, Severity, ExceptionStatus

PLAN_FILE = "../../data/production_plan.csv"
ACTUAL_FILE = "../../data/actual_production.csv"


def main():
    print("=" * 60)
    print("PRODUCTION EXCEPTION MONITORING - DATA INGESTION")
    print("=" * 60)
    
    # Create all tables
    print("\n[1/6] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
    
    # =========================================================
    # STEP 1: LOAD RAW DATA
    # =========================================================
    print("\n[2/6] Loading raw CSV files...")
    
    try:
        raw_plan = pd.read_csv(PLAN_FILE)
        raw_actual = pd.read_csv(ACTUAL_FILE)
    except FileNotFoundError as e:
        print(f"Error loading CSV files: {e}")
        print(f"  Expected files: {PLAN_FILE}, {ACTUAL_FILE}")
        return
    
    # Remove any checkmarks that cause encoding issues
    raw_plan_rows = len(raw_plan)
    raw_actual_rows = len(raw_actual)
    print(f"Raw plan rows: {raw_plan_rows}")
    print(f"Raw actual rows: {raw_actual_rows}")
    
    # =========================================================
    # STEP 2A: SAVE RAW TABLES
    # =========================================================
    print("\n[3/6] Saving raw data to database...")
    
    # Clear existing raw tables
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw_plan"))
        conn.execute(text("DELETE FROM raw_production"))
        conn.commit()
    
    # Insert raw data using SQLAlchemy models
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Insert raw plan data
        for _, row in raw_plan.iterrows():
            raw_plan_record = RawPlan(
                plan_date=str(row['plan_date']),
                plant=str(row['plant']),
                sku=str(row['sku']),
                planned_units=float(row['planned_units']) if pd.notna(row['planned_units']) else None
            )
            session.add(raw_plan_record)
        
        # Insert raw actual data
        for _, row in raw_actual.iterrows():
            raw_actual_record = RawProduction(
                date=str(row['date']),
                plant_id=str(row['plant_id']),
                product_code=str(row['product_code']),
                units_produced=int(row['units_produced'])
            )
            session.add(raw_actual_record)
        
        session.commit()
        print("Raw tables saved")
    except Exception as e:
        session.rollback()
        print(f"Error saving raw data: {e}")
        return
    finally:
        session.close()
    
    # =========================================================
    # STEP 2B: CLEAN PLAN DATA
    # =========================================================
    print("\n[4/6] Cleaning plan data...")
    
    plan = raw_plan.copy()
    
    # Rename columns
    plan = plan.rename(columns={
        "plan_date": "date",
        "plant": "plant_id",
        "sku": "product_code"
    })
    
    # Parse mixed date formats
    # Handle both YYYY-MM-DD and DD/MM/YYYY formats
    plan["date"] = pd.to_datetime(
        plan["date"],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    )
    
    # Report invalid dates
    invalid_dates = plan[plan["date"].isna()]
    if len(invalid_dates) > 0:
        print(f" Warning: {len(invalid_dates)} records with invalid dates were rejected")
    
    plan = plan[plan["date"].notna()]
    
    # Clean plant IDs
    plan["plant_id"] = (
        plan["plant_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    # Clean product codes
    plan["product_code"] = (
        plan["product_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    # Report whitespace/case cleaning
    original_skus = raw_plan["sku"].nunique()
    cleaned_skus = plan["product_code"].nunique()
    if original_skus != cleaned_skus:
        print(f" SKU normalization: {original_skus} -> {cleaned_skus} unique SKUs")
    
    # Remove exact duplicate rows
    before_dedup = len(plan)
    plan = plan.drop_duplicates()
    after_dedup = len(plan)
    if before_dedup != after_dedup:
        print(f" Removed {before_dedup - after_dedup} duplicate rows")
    
    # Remove records without planned units
    before_null_removal = len(plan)
    plan = plan.dropna(subset=["planned_units"])
    after_null_removal = len(plan)
    if before_null_removal != after_null_removal:
        print(f" Removed {before_null_removal - after_null_removal} records without planned_units")
    
    print(f"Clean plan rows: {len(plan)}")
    
    # =========================================================
    # STEP 2C: CLEAN ACTUAL PRODUCTION DATA
    # =========================================================
    print("\n[5/6] Cleaning actual production data...")
    
    actual = raw_actual.copy()
    
    actual["date"] = pd.to_datetime(
        actual["date"],
        format="mixed",
        dayfirst=True,
        errors="coerce"
    )
    
    # Report invalid dates in actual
    invalid_actual_dates = actual[actual["date"].isna()]
    if len(invalid_actual_dates) > 0:
        print(f" Warning: {len(invalid_actual_dates)} actual records with invalid dates rejected")
    
    actual = actual[actual["date"].notna()]
    
    actual["plant_id"] = (
        actual["plant_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    actual["product_code"] = (
        actual["product_code"]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    
    actual = actual.drop_duplicates()
    
    print(f"Clean actual rows: {len(actual)}")
    
    # =========================================================
    # SAVE CLEAN TABLES
    # =========================================================
    print("\n[6/6] Saving clean tables to database...")
    
    # Clear existing clean tables
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM clean_plan"))
        conn.execute(text("DELETE FROM clean_production"))
        conn.commit()
    
    session = Session()
    
    try:
        # Insert clean plan data
        for _, row in plan.iterrows():
            clean_plan_record = CleanPlan(
                date=row['date'],
                plant_id=row['plant_id'],
                product_code=row['product_code'],
                planned_units=float(row['planned_units'])
            )
            session.add(clean_plan_record)
        
        # Insert clean actual data
        for _, row in actual.iterrows():
            clean_actual_record = CleanProduction(
                date=row['date'],
                plant_id=row['plant_id'],
                product_code=row['product_code'],
                units_produced=int(row['units_produced'])
            )
            session.add(clean_actual_record)
        
        session.commit()
        print("Clean tables saved")
    except Exception as e:
        session.rollback()
        print(f"Error saving clean data: {e}")
        return
    finally:
        session.close()
    
    # =========================================================
    # STEP 3: JOIN PLAN AND ACTUAL DATA
    # =========================================================
    print("\n[7/7] Detecting exceptions...")
    
    merged = plan.merge(
        actual,
        on=[
            "date",
            "plant_id",
            "product_code"
        ],
        how="left"
    )
    
    # Policy: Missing actual production means zero production
    # This is a conservative approach - if we didn't produce, we have a deficit
    missing_actual = merged["units_produced"].isna().sum()
    if missing_actual > 0:
        print(f"  Policy: {missing_actual} planned records without actual data treated as zero production")
    
    merged["units_produced"] = (
        merged["units_produced"].fillna(0)
    )
    
    # Calculate ratio
    merged["production_ratio"] = (
        merged["units_produced"]
        / merged["planned_units"]
    )
    
    # Find deficit exceptions (units_produced < 0.9 * planned_units)
    exceptions = merged[
        merged["units_produced"]
        < (0.9 * merged["planned_units"])
    ].copy()
    
    print(f"Found {len(exceptions)} deficit exceptions")
    
    # =========================================================
    # ASSIGN SEVERITY
    # =========================================================
    def assign_severity(row):
        if row["units_produced"] < 0.7 * row["planned_units"]:
            return Severity.HIGH.value
        return Severity.MEDIUM.value
    
    exceptions["severity"] = exceptions.apply(
        assign_severity,
        axis=1
    )
    
    # =========================================================
    # ADD EXCEPTION INFORMATION
    # =========================================================
    exceptions["deficit_units"] = (
        exceptions["planned_units"]
        - exceptions["units_produced"]
    )
    
    exceptions["status"] = ExceptionStatus.OPEN.value
    
    # Sort by date descending, then by deficit descending (worst first)
    exceptions = exceptions.sort_values(
        by=["date", "deficit_units"],
        ascending=[False, False]
    )
    
    exceptions = exceptions.reset_index(drop=True)
    
    # Generate stable IDs based on composite key
    # This ensures idempotency - same exception gets same ID on re-run
    exceptions["composite_key"] = (
        exceptions["date"].dt.strftime("%Y-%m-%d") + "_" +
        exceptions["plant_id"] + "_" +
        exceptions["product_code"]
    )
    
    # Create a mapping from composite key to stable ID
    unique_keys = exceptions["composite_key"].unique()
    key_to_id = {key: idx + 1 for idx, key in enumerate(sorted(unique_keys))}
    exceptions["id"] = exceptions["composite_key"].map(key_to_id)
    
    # Drop the temporary composite key column
    exceptions = exceptions.drop(columns=["composite_key"])
    
    # Reorder columns to match model
    column_order = [
        "id", "date", "plant_id", "product_code",
        "planned_units", "units_produced", "production_ratio",
        "deficit_units", "severity", "status"
    ]
    exceptions = exceptions[column_order]
    
    # =========================================================
    # SAVE EXCEPTIONS (IDEMPOTENT)
    # =========================================================
    print("  Saving exceptions to database...")
    
    # Get existing exceptions to preserve status
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get existing exception statuses
        existing_exceptions = session.query(ExceptionModel.id, ExceptionModel.status).all()
        existing_status_map = {exc.id: exc.status for exc in existing_exceptions}
        
        if len(existing_exceptions) > 0:
            print(f"  Preserving status for {len(existing_exceptions)} existing exceptions")
        
        # Clear existing exceptions table (but we'll preserve status)
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM exceptions"))
            conn.commit()
        
        # Insert exceptions using SQLAlchemy models
        for _, row in exceptions.iterrows():
            exc_id = int(row['id'])
            # Use existing status if available, otherwise use "open"
            status = existing_status_map.get(exc_id, ExceptionStatus.OPEN.value)
            
            exception_record = ExceptionModel(
                id=exc_id,
                date=row['date'],
                plant_id=row['plant_id'],
                product_code=row['product_code'],
                planned_units=float(row['planned_units']),
                units_produced=float(row['units_produced']),
                production_ratio=float(row['production_ratio']),
                deficit_units=float(row['deficit_units']),
                severity=row['severity'],
                status=status
            )
            session.add(exception_record)
        
        session.commit()
        print("Exceptions saved to database")
    except Exception as e:
        session.rollback()
        print(f"Error saving exceptions: {e}")
        return
    finally:
        session.close()
    
    # =========================================================
    # RESULTS
    # =========================================================
    print("\n" + "=" * 60)
    print("PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  Raw plan rows: {len(raw_plan)}")
    print(f"  Raw actual rows: {len(raw_actual)}")
    print(f"  Clean plan rows: {len(plan)}")
    print(f"  Clean actual rows: {len(actual)}")
    print(f"  Exceptions found: {len(exceptions)}")
    
    print(f"\nSeverity distribution:")
    severity_counts = exceptions["severity"].value_counts()
    for severity, count in severity_counts.items():
        print(f"  {severity}: {count}")
    
    print(f"\nStatus distribution:")
    status_counts = exceptions["status"].value_counts()
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()