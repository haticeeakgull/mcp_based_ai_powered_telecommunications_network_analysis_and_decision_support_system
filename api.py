from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services import (
    build_answer,
    extract_cell_id,
    extract_region,
    get_anomalies_service,
    get_complaints_service,
    get_faults_service,
    get_metrics_service,
    get_station_service,
    route_chat,
)

app = FastAPI(title="Telecom NOC API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    limit: int = 20


class ChatResponse(BaseModel):
    route: str
    parsed: dict[str, Any]
    data: dict[str, Any]
    answer: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Telecom NOC API is running"}


@app.get("/metrics")
def metrics_endpoint(
    cell_id: str,
    slice_type: str | None = None,
    since: str | None = None,
    limit: int = Query(default=10, ge=1, le=500),
):
    try:
        return get_metrics_service(cell_id=cell_id, slice_type=slice_type, since=since, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies")
def anomalies_endpoint(
    cell_id: str | None = None,
    severity: str | None = None,
    only_anomalies: bool = True,
    limit: int = Query(default=50, ge=1, le=1000),
):
    try:
        return get_anomalies_service(
            cell_id=cell_id,
            severity=severity,
            only_anomalies=only_anomalies,
            limit=limit,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/faults")
def faults_endpoint(
    cell_id: str | None = None,
    region: str | None = None,
    resolved: bool | None = None,
    limit: int = Query(default=50, ge=1, le=1000),
):
    try:
        return get_faults_service(cell_id=cell_id, region=region, resolved=resolved, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/complaints")
def complaints_endpoint(
    cell_id: str | None = None,
    region: str | None = None,
    since: str | None = None,
    limit: int = Query(default=50, ge=1, le=1000),
):
    try:
        return get_complaints_service(cell_id=cell_id, region=region, since=since, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stations")
def stations_endpoint(
    cell_id: str | None = None,
    region: str | None = None,
    status: str | None = None,
    limit: int = Query(default=50, ge=1, le=1000),
):
    try:
        return get_station_service(cell_id=cell_id, region=region, status=status, limit=limit)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    msg = payload.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="message bos olamaz")

    route = route_chat(msg)
    cell_id = extract_cell_id(msg)
    region = extract_region(msg)
    parsed = {"cell_id": cell_id, "region": region, "limit": payload.limit}

    try:
        if route == "metrics":
            if not cell_id:
                raise HTTPException(
                    status_code=400,
                    detail="Metrik sorgusu icin mesajda CELL_XXX belirtin.",
                )
            data = get_metrics_service(cell_id=cell_id, limit=payload.limit)
        elif route == "anomalies":
            data = get_anomalies_service(cell_id=cell_id, only_anomalies=True, limit=payload.limit)
        elif route == "faults":
            data = get_faults_service(cell_id=cell_id, region=region, resolved=False, limit=payload.limit)
        elif route == "complaints":
            data = get_complaints_service(cell_id=cell_id, region=region, limit=payload.limit)
        else:
            data = get_station_service(cell_id=cell_id, region=region, limit=payload.limit)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    answer = build_answer(route, parsed, data)
    return ChatResponse(route=route, parsed=parsed, data=data, answer=answer)
