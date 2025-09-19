from fastapi import FastAPI
from src.routes.get_data import router as get_router
from src.routes.post_data import router as post_router
from src.config.logging import logger

app = FastAPI(title="API Dados ML")

app.include_router(get_router)
app.include_router(post_router)

@app.get("/")
def root():
    return {"message": "API rodando!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)