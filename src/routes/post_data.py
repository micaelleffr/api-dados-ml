from fastapi import APIRouter, HTTPException
from src.services.data_service import data_service
from src.models.schemas import DataCreate
from src.config.logging import logger

router = APIRouter(prefix="/data", tags=["data"])

@router.post("/", status_code=201)
def post_data(data: DataCreate):
    try:
        data_service.post_data(data.dict())
        return {"message": "Dados inseridos com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro no POST: {e}")
        raise HTTPException(status_code=500, detail="Erro ao inserir dados")