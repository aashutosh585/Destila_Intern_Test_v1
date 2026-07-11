import os
import sys
import subprocess
import time
from pathlib import Path

# Set UTF-8 encoding for console
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Get the project root directory
project_root = Path(__file__).parent
print(f"Project root: {project_root}")

# Change to backend directory and run ingestion script
backend_dir = project_root / "backend"
os.chdir(backend_dir)

# Add parent directory to sys.path so we can import app modules
sys.path.insert(0, str(project_root))

print("Running data ingestion script...")
try:
    from scripts.ingest_data import main
    main()
    print("✓ Data ingestion completed successfully")
except Exception as e:
    print(f"✗ Data ingestion failed: {e}")
    sys.exit(1)

print("=" * 60)
print("PIPELINE COMPLETED SUCCESSFULLY")
print("=" * 60)
print("\nSummary:")
print("  - Database tables created")
print("  - Raw CSV files loaded")
print("  - Raw data saved to database")
print("  - Plan and actual data cleaned and saved")
print("  - Exceptions detected and saved to database")

# Print exception summary
from app.models import Exception as ExceptionModel
from app.database import SessionLocal

try:
    db = SessionLocal()
    count = db.query(ExceptionModel).count()
    high_sev = db.query(ExceptionModel).filter(ExceptionModel.severity == ExceptionModel.Severity.HIGH).count()
    medium_sev = db.query(ExceptionModel).filter(ExceptionModel.severity == ExceptionModel.Severity.MEDIUM).count()
    open_count = db.query(ExceptionModel).filter(ExceptionModel.status == ExceptionModel.ExceptionStatus.OPEN).count()
    
    print(f"\n  - Total exceptions: {count}")
    print(f"  - High severity: {high_sev}")
    print(f"  - Medium severity: {medium_sev}")
    print(f"  - Currently open: {open_count}")
    
    db.close()
except Exception as e:
    print(f"  ! Could not generate exception summary: {e}")

print("\n✓ Full pipeline run completed successfully!")