import psycopg2
import pandas as pd
from mcp.server.fastmcp import FastMCP
from sklearn.ensemble import IsolationForest

mcp = FastMCP("Telecom_AI_Agent")

DB_CONFIG = {
    "dbname": "network_mcp",
    "user": "postgres",
    "password": "159753",
    "host": "localhost",
}


def run_query(query, params=None):
    """Parametre hatasını önlemek için güvenli sorgu fonksiyonu."""
    try:
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                # Parametre None ise boş tuple gönderiyoruz
                cur.execute(query, params or ())
                if cur.description:
                    return cur.fetchall()
                return None
    except Exception as e:
        return f"Veritabanı Hatası: {str(e)}"


# --- BÖLGE BAZLI TOOLLAR (Genel Teşhis) ---


@mcp.tool()
def get_region_metrics(region: str):
    """Bölge genelindeki tüm istasyonların özet performansını getirir."""
    sql = """
    SELECT b.cell_id, m.latency_ms, m.rsrp_dbm 
    FROM base_stations b
    JOIN network_metrics m ON b.cell_id = m.cell_id
    WHERE b.region = %s
    """
    return run_query(sql, (region,))


@mcp.tool()
def get_region_complaints(region: str):
    """Bölge bazlı müşteri şikayetlerini listeler."""
    sql = """
    SELECT c.issue, c.cell_id FROM complaints c
    JOIN base_stations b ON c.cell_id = b.cell_id
    WHERE b.region = %s
    """
    return run_query(sql, (region,))


# --- CİHAZ BAZLI TOOLLAR (Derin Analiz) ---


@mcp.tool()
def analyze_specific_cell(cell_id: str):
    sql = "SELECT latency_ms, packet_loss_pct, throughput_mbps FROM network_metrics WHERE cell_id = %s"
    data = run_query(sql, (cell_id,))

    if not data or isinstance(data, str):
        return "Yetersiz veri."

    df = pd.DataFrame(data, columns=["lat", "loss", "speed"])
    model = IsolationForest(contamination=0.05, random_state=42)
    df["anomaly"] = model.fit_predict(df)

    # --- KRİTİK FARK BURASI ---
    # Skorlar: 0'a yakınsa normal, negatifse (örn: -0.5) çok ciddi anomali
    scores = model.decision_function(df[["lat", "loss", "speed"]])
    avg_anomaly_score = scores[df["anomaly"] == -1].mean()

    anomaly_count = len(df[df["anomaly"] == -1])

    # Eğer skor çok düşükse (yani veriler çok norm dışıysa) KRİTİK de
    if avg_anomaly_score < -0.15:  # Bu eşiği verine göre ayarlayabilirsin
        return f"KRİTİK: {cell_id} için şiddetli anomaliler! (Skor: {avg_anomaly_score:.2f})"
    elif anomaly_count > 0:
        return (
            f"UYARI: {cell_id} için hafif sapmalar var. (Skor: {avg_anomaly_score:.2f})"
        )
    else:
        return f"NORMAL: {cell_id} stabil."


if __name__ == "__main__":
    mcp.run()
