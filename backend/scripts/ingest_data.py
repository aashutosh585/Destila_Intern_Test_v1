"""
Production Exception Monitoring - Data Ingestion Script

This script loads CSV data, cleans it, and saves exceptions to the database.
"""
import sys
import os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set UTF-8 encoding for console
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Get the script directory and set up paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

def get_absolute_path(relative_path):
    """Convert relative path to absolute based on project root."""
    return PROJECT_ROOT / relative_path

def main():
    print("=" * 60)
    print("PRODUCTION EXCEPTION MONITORING - DATA INGESTION")
    print("=" * 60)
    
    # Define file paths using pathlib for cross-platform compatibility
    plan_csv_path = get_absolute_path("data/production_plan.csv")
    actual_csv_path = get_absolute_path("data/actual_production.csv")
    
    # Verify files exist
    if not plan_csv_path.exists():
        print(f"Error: Production plan CSV not found at {plan_csv_path}")
        return
    if not actual_csv_path.exists():
        print(f"Error: Actual production CSV not found at {actual_csv_path}")
        return
    
    # Add project root to sys.path for app imports
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(SCRIPT_DIR.parent))
    
    try:
        from app.database import Base, engine
        from app.models import RawPlan, RawProduction, CleanPlan, CleanProduction, Exception as ExceptionModel, Severity, ExceptionStatus
    except ImportError as e:
        print(f"Error importing app modules: {e}")
        return
    
    # Create all tables
    print("\n[1/6] Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
    
    # =========================================================
    # STEP 1: LOAD RAW DATA
    # =========================================================
    print("\n[2/6] Loading raw CSV files...")
    
    try:
        raw_plan = pd.read_csv(plan_csv_path)
        raw_actual = pd.read_csv(actual_csv_path)
    except FileNotFoundError as e:
        print(f"Error loading CSV files: {e}")
        print(f"  Expected files: {plan_csv_path}, {actual_csv_path}")
        return
    
    # Display raw data counts
    print(f"Raw plan rows: {len(raw_plan)}")
    print(f"Raw actual rows: {len(raw_actual)}")
    
    # =========================================================
    # STEP 2A: SAVE RAW TABLES TO DATABASE
    # =========================================================
    print("\n[3/6] Saving raw data to database...")
    
    # Clear existing raw tables
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM raw_plan"))
        conn.execute(text("DELETE FROM raw_production"))
        conn.commit()
    
    # Create database session
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
    
    # Rename columns to match database schema
    plan = plan.rename(columns={
        "plan_date": "date",
        "plant": "plant_id", 
        "sku": "product_code"
    })
    
    # Parse date columns (handle both YYYY-MM-DD and DD/MM/YYYY formats)
    plan["date"] = pd.to_datetime(plan["date"], format="mixed", dayfirst=True, errors="coerce")
    
    # Remove invalid date records
    invalid_dates = plan[plan["date"].isna()]
    if len(invalid_dates) > 0:
        print(f"  Warning: {len(invalid_dates)} records with invalid dates were rejected")
    
    plan = plan[plan["date"].notna()]
    
    # Clean text fields
    plan["plant_id"] = plan["plant_id"].astype(str).str.strip().str.upper()
    plan["product_code"] = plan["product_code"].astype(str).str.strip().str.upper()
    
    # Report cleaning operations
    original_skus = raw_plan["sku"].nunique()
    cleaned_skus = plan["product_code"].nunique()
    if original_skus != cleaned_skus:
        print(f"  SKU normalization: {original_skus} -> {cleaned_skus} unique SKUs")
    
    plan = plan.drop_duplicates()
    plan = plan.dropna(subset=["planned_units"])
    
    print(f"Clean plan rows: {len(plan)}")
    
    # =========================================================
    # STEP 2C: CLEAN ACTUAL PRODUCTION DATA
    # =========================================================
    print("\n[5/6] Cleaning actual production data...")
    
    actual = raw_actual.copy()
    actual["date"] = pd.to_datetime(actual["date"], format="mixed", dayfirst=True, errors="coerce")
    
    # Remove invalid dates
    invalid_actual_dates = actual[actual["date"].isna()]
    if len(invalid_actual_dates) > 0:
        print(f"  Warning: {len(invalid_actual_dates)} actual records with invalid dates rejected")
    
    actual = actual[actual["date"].notna()]
    
    # Clean text fields
    actual["plant_id"] = actual["plant_id"].astype(str).str.strip().str.upper()
    actual["product_code"] = actual["product_code"].astype(str).str.strip().str.upper()
    
    actual = actual.drop_duplicates()
    
    print(f"Clean actual rows: {len(actual)}")
    
    # =========================================================
    # STEP 3: SAVE CLEAN DATA TO DATABASE
    # =========================================================
    print("\n[6/6] Saving clean tables to database...")
    
    # Clear existing clean tables
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM clean_plan"))
        conn.execute(text("DELETE FROM clean_production"))
        conn.commit()
    
    session = Session()
    
    try:
        # Save clean plan data
        for _, row in plan.iterrows():
            clean_plan_record = CleanPlan(
                date=row['date'],
                plant_id=row['plant_id'],
                product_code=row['product_code'],
                planned_units=float(row['planned_units'])
            )
            session.add(clean_plan_record)
        
        # Save clean actual data
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
    # STEP 4: DETECT DEFICIT EXCEPTIONS
    # =========================================================
    print("\n[7/7] Detecting exceptions...")
    
    # Merge plan and actual data
    merged = plan.merge(actual, on=["date", "plant_id", "product_code"], how="left")
    
    # Handle missing actual data
    missing_actual = merged["units_produced"].isna().sum()
    if missing_actual > 0:
        print(f"  Policy: {missing_actual} planned records without actual data treated as zero production")
    
    merged["units_produced"] = merged["units_produced"].fillna(0)
    
    # Calculate production metrics
    merged["production_ratio"] = merged["units_produced"] / merged["planned_units"]
    
    # Detect deficit exceptions (actual < 90% of planned)
    exceptions = merged[merged["units_produced"] < (0.9 * merged["planned_units"])].copy()
    
    print(f"Found {len(exceptions)} deficit exceptions")
    
    # Assign severity levels
    def assign_severity(row):
        if row["units_produced"] < (0.7 * row["planned_units"]):
            return Severity.HIGH.value
        return Severity.MEDIUM.value
    
    exceptions["severity"] = exceptions.apply(assign_severity, axis=1)
    exceptions["deficit_units"] = exceptions["planned_units"] - exceptions["units_produced"]
    exceptions["status"] = ExceptionStatus.OPEN.value
    
    # Generate stable exception IDs based on composite key
    exceptions["composite_key"] = (
        exceptions["date"].dt.strftime("%Y-%m-%d") + "_" +
        exceptions["plant_id"] + "_" +
        exceptions["product_code"]
    )
    
    unique_keys = exceptions["composite_key"].unique()
    key_to_id = {key: idx + 1 for idx, key in enumerate(sorted(unique_keys))}
    exceptions["id"] = exceptions["composite_key"].map(key_to_id)
    
    # Clean up and prepare final dataset
    exceptions = exceptions.drop(columns=["composite_key"])
    column_order = ["id", "date", "plant_id", "product_code", 
                   "planned_units", "units_produced", "production_ratio",
                   "deficit_units", "severity", "status"]
    exceptions = exceptions[column_order]
    
    # =========================================================
    # STEP 5: SAVE EXCEPTIONS TO DATABASE
    # =========================================================
    print("  Saving exceptions to database...")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Query existing exceptions to preserve status on re-runs
        existing_exceptions = session.query(ExceptionModel.status).filter(ExceptionModel.id.in_(exceptions["id"])).all()
        existing_status_map = {}
        for exc in existing_exceptions:
            existing_status_map[exc[0]] = exc[0]
        
        if len(existing_exceptions) > 0:
            print(f"  Preserving status for {len(existing_exceptions)} existing exceptions")
        
        # Clear and re-insert exceptions to maintain idempotency
        with engine.connect() as conn:
            conn.execute(text("DELETE FROM exceptions"))
            conn.commit()
        
        # Save all exceptions
        for _, row in exceptions.iterrows():
            exception_record = ExceptionModel(
                id=int(row['id']),
                date=row['date'],
                plant_id=row['plant_id'],
                product_code=row['product_code'],
                planned_units=float(row['planned_units']),
                units_produced=float(row['units_produced']),
                production_ratio=float(row['production_ratio']),
                deficit_units=float(row['deficit_units']),
                severity=row['severity'],
                status=existing_status_map.get(int(row['id']), ExceptionStatus.OPEN.value)
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
    # RESULTS AND SUMMARY
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