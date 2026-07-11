from app.models import Exception
from app.database import SessionLocal

db = SessionLocal()
count = db.query(Exception).count()
print('Exceptions in DB:', count)
db.close()