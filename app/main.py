from fastapi import FastAPI
import uvicorn

# Initialize FastAPI app
app = FastAPI()

# Root route
@app.get("/")
def read_root():
    return {"message": "🚀 FinMate Backend is running fine!"}

# Optional: Health route
@app.get("/health")
def health_check():
    return {"status": "ok"}

# Entry point for local run
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
