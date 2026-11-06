from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.routers import customers, tickets, repairs, insights, followups, memory, dashboard

# Initialize tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FixLoop AI Repair Intelligence & Proactive Operations API"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for development/demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(tickets.router)
app.include_router(repairs.router)
app.include_router(insights.router)
app.include_router(followups.router)
app.include_router(memory.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "hindsight_configured": bool(settings.HINDSIGHT_API_KEY),
        "groq_configured": bool(settings.GROQ_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
