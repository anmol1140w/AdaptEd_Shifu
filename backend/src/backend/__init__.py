def main() -> None:
    """Run the FastAPI application with the project's supported ASGI server."""
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
