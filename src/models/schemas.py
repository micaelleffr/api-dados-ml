from pydantic import BaseModel

class DataItem(BaseModel):
    id: int
    nome: str
    valor: float

class DataCreate(BaseModel):
    nome: str
    valor: float