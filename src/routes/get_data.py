from fastapi import APIRouter, HTTPException
from src.services.data_service import data_service
from src.models.schemas import DataItem
from src.config.logging import logger

router = APIRouter(prefix="/data", tags=["data"])

@router.get("/", response_model=list[DataItem])
def get_data(limit: int = 10):
    query = f"SELECT * FROM `{data_service.table_ref}` LIMIT {limit}"
    try:
        results = data_service.get_data(query)
        return results
    except Exception as e:
        logger.error(f"Erro no GET: {e}")
        raise HTTPException(status_code=500, detail="Erro ao consultar dados")