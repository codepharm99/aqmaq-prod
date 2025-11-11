from fastapi import FastAPI
from pydantic import BaseModel
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import os, json

load_dotenv()

app = FastAPI(title="Aqmaq Demo API")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("AQMAQ_DATA_DIR", str(BASE_DIR / "aqmaq-data")))
DB_DIR = DATA_DIR / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
INC_PATH = DB_DIR / "incidents.jsonl"

class Incident(BaseModel):
    timestamp: float
    event: str
    y: int | None = None

@app.get("/health")
def health():
    return {"ok": True, "db": str(INC_PATH), "exists": INC_PATH.exists()}

@app.post("/incidents")
def incidents(inc: Incident):
    rec = inc.model_dump()
    rec["iso"] = datetime.now(timezone.utc).isoformat()
    with INC_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"ok": True, "written": True}
