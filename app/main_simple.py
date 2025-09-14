"""Simplified main application for testing."""
from fastapi import FastAPI

app = FastAPI(
    title="Intelligent Detection and Monitoring Platform",
    description="A distributed system for intelligent sensor data monitoring and anomaly detection",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "platform": "intelligent-detection-monitoring"}

@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Intelligent Detection and Monitoring Platform", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)