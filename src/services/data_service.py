from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError
from src.config.settings import settings
from src.config.logging import logger

class DataService:
    def __init__(self):
        self.client = bigquery.Client(project=settings.PROJECT_ID)
        self.table_ref = f"{settings.PROJECT_ID}.{settings.BIGQUERY_DATASET}.{settings.BIGQUERY_TABLE}"

    def get_data(self, query: str):
        """Executa uma query SELECT no BigQuery."""
        try:
            query_job = self.client.query(query)
            results = query_job.result()
            return [dict(row) for row in results]
        except GoogleAPIError as e:
            logger.error(f"Erro na query BigQuery: {e}")
            raise

    def post_data(self, data: dict):
        """Insere dados na tabela do BigQuery."""
        try:
            errors = self.client.insert_rows_json(self.table_ref, [data])
            if errors:
                logger.error(f"Erros ao inserir: {errors}")
                raise ValueError("Falha ao inserir dados")
            logger.info("Dados inseridos com sucesso")
        except GoogleAPIError as e:
            logger.error(f"Erro na inserção BigQuery: {e}")
            raise

# Instância singleton para reuse
data_service = DataService()