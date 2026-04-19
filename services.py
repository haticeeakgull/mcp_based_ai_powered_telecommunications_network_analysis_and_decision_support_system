import os
import re
from datetime import date, datetime
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "network_mcp"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}

KNOWN_REGIONS = [
    "Bornova", "Konak", "Karsiyaka", "Buca", "Cigli", "Bayrakli", "Gaziemir",
    "Menemen", "Torbali", "Kemalpasa", "Karabaglar", "Urla", "Balcova",
    "Narlidere", "Guzelbahce", "Seferihisar", "Menderes", "Aliaga", "Cesme",
    "Selcuk", "Foca", "Karaburun", "Tire", "Odemis", "Kiraz", "Beydag",
    "Kinik", "Dikili", "Bergama", "Bayindir",
]


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _serialize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: _serialize_value(v) for k, v in row.items()} for row in rows]


def query_rows(sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, params)
                return list(cur.fetchall())
    except Exception as e:
        raise RuntimeError(f"Veritabani Hatasi: {e}")


def get_metrics_service(
    cell_id: str,
    slice_type: str | None = None,
    since: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    where = ["nm.cell_id = %s"]
    params: list[Any] = [cell_id]
    if slice_type:
        where.append("nm.slice_type = %s")
        params.append(slice_type)
    if since:
        where.append("nm.recorded_at >= %s")
        params.append(since)
    params.append(limit)
    sql = f"""
    SELECT nm.id, nm.cell_id, nm.slice_type, nm.latency_ms, nm.packet_loss_pct,
           nm.throughput_mbps, nm.load_pct, nm.rsrp_dbm, nm.rsrq_db,
           nm.connected_users, nm.recorded_at
    FROM network_metrics nm
    WHERE {' AND '.join(where)}
    ORDER BY nm.recorded_at DESC
    LIMIT %s
    """
    rows = _serialize_rows(query_rows(sql, tuple(params)))
    return {"cell_id": cell_id, "slice_type": slice_type, "since": since, "limit": limit, "count": len(rows), "items": rows}


def get_anomalies_service(
    cell_id: str | None = None,
    severity: str | None = None,
    only_anomalies: bool = True,
    limit: int = 50,
) -> dict[str, Any]:
    where = ["ar.algorithm = 'combined'"]
    params: list[Any] = []
    if only_anomalies:
        where.append("ar.is_anomaly = TRUE")
    if cell_id:
        where.append("ar.cell_id = %s")
        params.append(cell_id)
    if severity:
        where.append("ar.severity = %s")
        params.append(severity)
    params.append(limit)
    sql = f"""
    SELECT ar.id, ar.cell_id, ar.metric_id, ar.is_anomaly, ar.anomaly_score,
           ar.triggered_by, ar.severity, ar.root_cause, ar.metric_recorded_at,
           ar.detected_at
    FROM anomaly_results ar
    WHERE {' AND '.join(where)}
    ORDER BY ar.metric_recorded_at DESC
    LIMIT %s
    """
    rows = _serialize_rows(query_rows(sql, tuple(params)))
    return {
        "filters": {"cell_id": cell_id, "severity": severity, "only_anomalies": only_anomalies, "limit": limit},
        "count": len(rows),
        "items": rows,
    }


def get_faults_service(
    cell_id: str | None = None,
    region: str | None = None,
    resolved: bool | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    where = ["1=1"]
    params: list[Any] = []
    if cell_id:
        where.append("f.cell_id = %s")
        params.append(cell_id)
    if region:
        where.append("LOWER(bs.region) = LOWER(%s)")
        params.append(region)
    if resolved is not None:
        where.append("f.resolved = %s")
        params.append(resolved)
    params.append(limit)
    sql = f"""
    SELECT f.id, f.cell_id, bs.region, f.severity, f.fault_type, f.message,
           f.resolved, f.created_at, f.resolved_at
    FROM faults f
    JOIN base_stations bs ON bs.cell_id = f.cell_id
    WHERE {' AND '.join(where)}
    ORDER BY f.created_at DESC
    LIMIT %s
    """
    rows = _serialize_rows(query_rows(sql, tuple(params)))
    return {
        "filters": {"cell_id": cell_id, "region": region, "resolved": resolved, "limit": limit},
        "count": len(rows),
        "items": rows,
    }


def get_complaints_service(
    cell_id: str | None = None,
    region: str | None = None,
    since: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    where = ["1=1"]
    params: list[Any] = []
    if cell_id:
        where.append("c.cell_id = %s")
        params.append(cell_id)
    if region:
        where.append("LOWER(c.region) = LOWER(%s)")
        params.append(region)
    if since:
        where.append("c.created_at >= %s")
        params.append(since)
    params.append(limit)
    sql = f"""
    SELECT c.id, c.customer_id, c.region, c.issue, c.cell_id, c.created_at
    FROM complaints c
    WHERE {' AND '.join(where)}
    ORDER BY c.created_at DESC
    LIMIT %s
    """
    rows = _serialize_rows(query_rows(sql, tuple(params)))
    return {
        "filters": {"cell_id": cell_id, "region": region, "since": since, "limit": limit},
        "count": len(rows),
        "items": rows,
    }


def get_station_service(
    cell_id: str | None = None,
    region: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    where = ["1=1"]
    params: list[Any] = []
    if cell_id:
        where.append("bs.cell_id = %s")
        params.append(cell_id)
    if region:
        where.append("LOWER(bs.region) = LOWER(%s)")
        params.append(region)
    if status:
        where.append("LOWER(bs.status) = LOWER(%s)")
        params.append(status)
    params.append(limit)
    sql = f"""
    SELECT bs.cell_id, bs.region, bs.lat, bs.lng, bs.status
    FROM base_stations bs
    WHERE {' AND '.join(where)}
    ORDER BY bs.cell_id
    LIMIT %s
    """
    rows = _serialize_rows(query_rows(sql, tuple(params)))
    return {
        "filters": {"cell_id": cell_id, "region": region, "status": status, "limit": limit},
        "count": len(rows),
        "items": rows,
    }


def extract_cell_id(text: str) -> str | None:
    match = re.search(r"(CELL_\d{3})", text, flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


def extract_region(text: str) -> str | None:
    normalized = text.lower()
    for region in KNOWN_REGIONS:
        if region.lower() in normalized:
            return region
    return None


def route_chat(message: str) -> str:
    m = message.lower()
    if any(k in m for k in ["anomali", "anomaly", "severity", "root cause"]):
        return "anomalies"
    if any(k in m for k in ["fault", "ariza", "alarm"]):
        return "faults"
    if any(k in m for k in ["sikayet", "complaint", "musteri"]):
        return "complaints"
    if any(k in m for k in ["station", "istasyon", "status", "offline", "online"]):
        return "stations"
    return "metrics"


def build_answer(route: str, parsed: dict[str, Any], data: dict[str, Any]) -> str:
    count = data.get("count", 0)
    if route == "metrics":
        target = parsed.get("cell_id") or "hedef"
        return f"{target} icin {count} metrik kaydi bulundu."
    if route == "anomalies":
        target = parsed.get("cell_id") or parsed.get("region") or "secim"
        return f"{target} icin {count} anomali kaydi bulundu."
    if route == "faults":
        target = parsed.get("region") or parsed.get("cell_id") or "secim"
        return f"{target} icin {count} fault kaydi bulundu."
    if route == "complaints":
        target = parsed.get("region") or parsed.get("cell_id") or "secim"
        return f"{target} icin {count} sikayet kaydi bulundu."
    target = parsed.get("region") or parsed.get("cell_id") or "secim"
    return f"{target} icin {count} istasyon kaydi bulundu."
