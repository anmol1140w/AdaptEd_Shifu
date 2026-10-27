from fastapi import FastAPI

from backend.app.api.v1.router import api_router

app = FastAPI(
    title="AdaptEd API",
    description="AI-powered adaptive learning platform",
    version="1.0.0",
)

app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Welcome to AdaptEd"}