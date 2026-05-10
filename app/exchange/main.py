from fastapi import FastAPI
from app.database.database import Base, DBSession, engine
from app.routers.users import router as users_router
from app.routers.auctions import router as auctions_router
try:
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")
except Exception as e:
    print(f"Failed to create tables: {e}")

app = FastAPI()
app.include_router(users_router)
app.include_router(auctions_router)

@app.get('/')
def get_root(db: DBSession):
    return {'this':"is index page"}


# ssp debug
from datetime import datetime
@app.get('/SSP/{id}')
async def respond_ssp(id: int):
        return {
                'id': id,
                'ads_url': f"http://localhost:8000/SSP/{id}"
                'date_shown': datetime.utcnow()
                }

@app.post('/SSP/{id}')#add response schema which is the same but with a url added
async def respond_to_ad_request(id: int, user_info):#make user_info a schema
    user_info.ad_url = f"http://localhost:8000/SSP/{id}"
    return user_info
