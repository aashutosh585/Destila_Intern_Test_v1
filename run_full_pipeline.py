import os
import sys
from pathlib import Path

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Change to the backend directory
backend_dir = Path(__file__).parent / 'backend'
os.chdir(backend_dir)

# Run the ingestion script
sys.path.insert(0, str(Path(__file__).parent))
print("Running ingestion script...")

# Import and run main from ingest_data
from scripts.ingest_data import main

main()

print("Done.")