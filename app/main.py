from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.router import api_router

from sqlalchemy import text

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# Auto-migrate: ensure summary_metrics column exists
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE excel_upload_log ADD COLUMN summary_metrics JSON"))
        conn.commit()
    except Exception:
        pass


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Wealth & Asset Consolidation Dashboard",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
