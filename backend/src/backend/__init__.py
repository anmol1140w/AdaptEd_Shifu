def main() -> None:
    """Run the FastAPI application with the project's supported ASGI server."""
    import os

    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
