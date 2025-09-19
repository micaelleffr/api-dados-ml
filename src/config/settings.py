import os
from dotenv import load_dotenv

load_dotenv() 

class Settings:
    PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "seu-projeto-gcp")  
    BIGQUERY_TABLE: str = "sua_tabela"     
settings = Settings()