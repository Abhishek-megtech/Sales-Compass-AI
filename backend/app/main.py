from fastapi import FastAPI
from app.api.search import router as search_router

from app.api.upload import router as upload_router


app = FastAPI(
    title="SalesCompass AI",
    version="1.0.0",
)


app.include_router(upload_router)
app.include_router(search_router)

@app.get("/")
def root():
    return {
        "message": "SalesCompass AI API is running"
    }