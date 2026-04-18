import os

import psycopg2
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

mcp = FastMCP("Telecom_AI_Agent")

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "network_mcp"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
}


def run_query(query, params=None):
    """Run SQL safely and return fetched rows if query has output."""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if cur.description:
                    return cur.fetchall()
                return None
    except Exception as e:
        return f"Veritabani Hatasi: {str(e)}"


@mcp.tool()
def get_region_metrics(region: str):
    """Get raw metrics for all cells in the region."""
    sql = """
    SELECT b.cell_id, m.latency_ms, m.rsrp_dbm
    FROM base_stations b
    JOIN network_metrics m ON b.cell_id = m.cell_id
    WHERE LOWER(b.region) = LOWER(%s)
    """
    return run_query(sql, (region,))


@mcp.tool()
def get_region_complaints(region: str):
    """Get complaints in the given region."""
    sql = """
    SELECT c.issue, c.cell_id
    FROM complaints c
    JOIN base_stations b ON c.cell_id = b.cell_id
    WHERE LOWER(b.region) = LOWER(%s)
    """
    return run_query(sql, (region,))


@mcp.tool()
def analyze_specific_cell(cell_id: str):
    """
    Read anomaly_results (combined algorithm) and return cell anomaly status.
    This tool does not retrain model; it reads precomputed anomaly outputs.
    """
    sql_latest_anomaly = """
    SELECT is_anomaly, anomaly_score, severity, root_cause, triggered_by, metric_recorded_at
    FROM anomaly_results
    WHERE cell_id = %s
      AND algorithm = 'combined'
    ORDER BY metric_recorded_at DESC
    LIMIT 1
    """

    sql_window_summary = """
    SELECT
        COUNT(*) AS total_count,
        COUNT(*) FILTER (WHERE is_anomaly) AS anomaly_count,
        AVG(anomaly_score) FILTER (WHERE is_anomaly) AS avg_anomaly_score
    FROM anomaly_results
    WHERE cell_id = %s
      AND algorithm = 'combined'
      AND metric_recorded_at >= NOW() - INTERVAL '7 days'
    """

    sql_latest_metric = """
    SELECT latency_ms, packet_loss_pct, throughput_mbps, load_pct, recorded_at
    FROM network_metrics
    WHERE cell_id = %s
    ORDER BY recorded_at DESC
    LIMIT 1
    """

    sql_open_faults = """
    SELECT COUNT(*)
    FROM faults
    WHERE cell_id = %s
      AND resolved = FALSE
    """

    latest_anomaly = run_query(sql_latest_anomaly, (cell_id,))
    summary = run_query(sql_window_summary, (cell_id,))
    latest_metric = run_query(sql_latest_metric, (cell_id,))
    open_faults = run_query(sql_open_faults, (cell_id,))

    if any(isinstance(x, str) for x in [latest_anomaly, summary, latest_metric, open_faults]):
        return {
            "status": "UNKNOWN",
            "cell_id": cell_id,
            "message": "Sorgu sirasinda veritabani hatasi olustu.",
        }

    if not latest_anomaly or not summary:
        return {
            "status": "UNKNOWN",
            "cell_id": cell_id,
            "message": "Bu hucre icin anomaly_results kaydi bulunamadi.",
        }

    la = latest_anomaly[0]
    sm = summary[0]
    mt = latest_metric[0] if latest_metric else None
    open_fault_count = int(open_faults[0][0]) if open_faults else 0

    total_count = int(sm[0] or 0)
    anomaly_count = int(sm[1] or 0)
    anomaly_ratio = (anomaly_count / total_count) if total_count else 0.0
    avg_anomaly_score = float(sm[2]) if sm[2] is not None else None

    latest_is_anomaly = bool(la[0])
    latest_score = float(la[1]) if la[1] is not None else None
    latest_severity = la[2]
    latest_root_cause = la[3]
    latest_triggered_by = la[4]
    latest_anomaly_time = la[5]

    if latest_is_anomaly:
        status = latest_severity if latest_severity else "WARNING"
        message = f"{status}: {cell_id} icin son olcum anomali."
    else:
        status = "NORMAL"
        message = f"NORMAL: {cell_id} icin son olcumde anomali yok."

    return {
        "status": status,
        "cell_id": cell_id,
        "window_days": 7,
        "total_count": total_count,
        "anomaly_count": anomaly_count,
        "anomaly_ratio": round(anomaly_ratio, 4),
        "avg_anomaly_score": round(avg_anomaly_score, 4) if avg_anomaly_score is not None else None,
        "latest_combined_anomaly": {
            "is_anomaly": latest_is_anomaly,
            "anomaly_score": round(latest_score, 4) if latest_score is not None else None,
            "severity": latest_severity,
            "root_cause": latest_root_cause,
            "triggered_by": latest_triggered_by,
            "metric_recorded_at": latest_anomaly_time.isoformat() if latest_anomaly_time else None,
        },
        "latest_metric": None if not mt else {
            "latency_ms": float(mt[0]) if mt[0] is not None else None,
            "packet_loss_pct": float(mt[1]) if mt[1] is not None else None,
            "throughput_mbps": float(mt[2]) if mt[2] is not None else None,
            "load_pct": float(mt[3]) if mt[3] is not None else None,
            "recorded_at": mt[4].isoformat() if mt[4] else None,
        },
        "open_fault_count": open_fault_count,
        "message": message,
    }


if __name__ == "__main__":
    mcp.run()
