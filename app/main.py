from fastapi import FastAPI
from app.database.database import Base, engine
from app.routers.users import DBSession, router as users_router
try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
except Exception as e:
    print(f"Failed to create tables: {e}")

app = FastAPI()
app.include_router(users_router)
@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}





