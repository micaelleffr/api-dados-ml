import logging
from functools import lru_cache
from io import BytesIO
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

BASE_URL = "https://dados.ons.org.br/api/3/action/package_show?id="
app = FastAPI()

def make_session(retries: int = 3, backoff: float = 0.3) -> requests.Session:
    s = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff, status_forcelist=(500, 502, 503, 504))
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    return s

_session = make_session()

@lru_cache(maxsize=128)
def fetch_package_metadata(package_id: str) -> dict:
    url = f"{BASE_URL}{package_id}"
    logging.info(f"Fetching metadata for package_id={package_id}")
    resp = _session.get(url, timeout=(5, 30))
    resp.raise_for_status()
    data = resp.json()

    if not data.get("success"):
        raise ValueError("Resposta inválida da API do ONS")
    return data["result"]

def find_parquet_url(metadata: dict, ano: Optional[int] = None) -> Optional[str]:
    resources = metadata.get("resources", []) or []

    parquet_candidates = [
        r for r in resources
        if (r.get("format") or "").upper() == "PARQUET" or (r.get("url") or "").lower().endswith(".parquet")
    ]
    logging.info(f"{len(parquet_candidates)} parquet resources found.")
    if not parquet_candidates:
        return None

    if ano is None:
        return parquet_candidates[0]["url"]

    for r in parquet_candidates:
        if str(ano) in (r.get("name") or "") or str(ano) in (r.get("url") or ""):
            return r["url"]

    return parquet_candidates[0]["url"]

def read_parquet_from_url(url: str) -> pd.DataFrame:
    logging.info(f"Reading parquet from {url}")
    try:
        df = pd.read_parquet(url, engine="pyarrow")
        logging.info("read_parquet(url) succeeded")
        return df
    except Exception as e:
        logging.info(f"pd.read_parquet(url) failed: {e}; will stream bytes and read from buffer")
    resp = _session.get(url, stream=True, timeout=(5, 60))
    resp.raise_for_status()
    buf = BytesIO(resp.content)
    df = pd.read_parquet(buf, engine="pyarrow")
    return df

def records_from_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
    df = df.where(pd.notnull(df), None)
    recs = df.to_dict(orient="records")
    cleaned: List[Dict[str, Any]] = []
    for r in recs:
        nr: Dict[str, Any] = {}
        for k, v in r.items():
            if isinstance(v, (np.integer,)):
                nr[k] = int(v)
            elif isinstance(v, (np.floating, float)):
                fv = float(v)
                nr[k] = fv if np.isfinite(fv) else None
            elif hasattr(v, "to_pydatetime"):
                try:
                    dt = v.to_pydatetime()
                    nr[k] = dt.strftime("%Y-%m-%d")
                except Exception:
                    nr[k] = None
            elif isinstance(v, str):
                s = v.strip()
                nr[k] = s if s != "" else None
            else:
                nr[k] = v
        cleaned.append(nr)
    return cleaned

@app.get("/data")
def get_data(
    package_id: str = Query(...),
    ano: Optional[int] = Query(None),
    mes: Optional[int] = Query(None),
    nome_reservatorio: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    page: int = Query(1),
    page_size: int = Query(100)
):
    try:
        metadata = fetch_package_metadata(package_id)

        if start_date and end_date:
            start_ts, end_ts = pd.to_datetime(start_date), pd.to_datetime(end_date)
            years = list(range(start_ts.year, end_ts.year + 1))
        elif ano:
            years = [ano]
            start_ts = end_ts = None
        else:
            return JSONResponse({"error": "Informe 'ano' ou 'start_date'/'end_date'."}, status_code=400)

        df_list = [
            read_parquet_from_url(find_parquet_url(metadata, y))
            for y in years
            if find_parquet_url(metadata, y)
        ]
        if not df_list:
            return JSONResponse({"error": "Nenhum parquet encontrado para os anos requisitados."}, status_code=404)

        df = pd.concat(df_list, ignore_index=True)

        if "ear_data" in df.columns:
            df["ear_data"] = pd.to_datetime(df["ear_data"], errors="coerce", dayfirst=True)

            if start_date and end_date:
                df = df[(df["ear_data"] >= start_ts) & (df["ear_data"] <= end_ts)]
            else:
                if mes:
                    df = df[(df["ear_data"].dt.year == ano) & (df["ear_data"].dt.month == mes)]
                else:
                    df = df[df["ear_data"].dt.year == ano]

        if nome_reservatorio:
            df = df[df["nom_reservatorio"].astype(str).str.contains(nome_reservatorio, case=False, na=False)]

        start_idx = (page - 1) * page_size
        page_df = df.iloc[start_idx:start_idx + page_size]
        has_more = len(df) > start_idx + page_size

        records = records_from_dataframe(page_df)
        return JSONResponse({"page": page, "page_size": page_size, "has_more": has_more, "data": records})

    except Exception as e:
        logging.exception("Erro processando requisição")
        return JSONResponse({"error": str(e)}, status_code=500)
