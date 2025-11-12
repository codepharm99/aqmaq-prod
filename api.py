from fastapi import FastAPI

from aqmaq import get_settings
from aqmaq.models import Incident
from aqmaq.storage import JsonlIncidentStore

settings = get_settings()
store = JsonlIncidentStore(settings.incidents_path)

app = FastAPI(title="Aqmaq Demo API")


@app.get("/health")
def health():
    return {"ok": True, "db": str(store.path), "exists": store.path.exists()}


@app.post("/incidents")
def incidents(incident: Incident):
    store.append(incident)
    return {"ok": True, "written": True}
