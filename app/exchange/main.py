from fastapi import FastAPI

from .database.database import Base, DBSession, sync_engine
from .middleware.metrics import setup_prometheus
from .routers.users import router as users_router
from .routers.auctions import router as auctions_router
from .routers.ssp import router as ssp_router

try:
    Base.metadata.create_all(bind=sync_engine)
    print("Tables created successfully")
except Exception as e:
    print(f"Failed to create tables: {e}")

app = FastAPI(title="Exchange FastAPI")
setup_prometheus(app)

app.include_router(users_router)
app.include_router(auctions_router)
app.include_router(ssp_router)

@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}

@app.get('/healthz')
def health_check():
    return {"status": "healty"}

