from fastapi import FastAPI

# Import routers
from app.routes.health import router as health_router
from app.routes.upload import router as upload_router
from app.routes.process import router as process_router
from app.routes.analyze import router as analyze_router
from app.routes.summary import router as summary_router

app = FastAPI()

# Register routes
app.include_router(health_router)
app.include_router(upload_router)
app.include_router(process_router)    
app.include_router(analyze_router)
app.include_router(summary_router)


@app.get("/")
def read_root():
    return {"message": "🚀 FinMate Backend is running fine!"}
