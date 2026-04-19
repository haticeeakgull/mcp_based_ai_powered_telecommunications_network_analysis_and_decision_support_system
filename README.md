# MCP Based AI Powered Telecommunications Network Analysis and Decision Support System

Telekom NOC odakli bu proje su katmanlardan olusur:
- veri uretimi (`database/`),
- offline anomali hesaplama (`anamoly_detector.py`),
- MCP tool katmani (`main.py`),
- FastAPI endpoint katmani (`api.py`),
- basit AJAX frontend (`frontend/`).

## 1) Mimari Ozeti

- `network_metrics`, `faults`, `complaints`, `base_stations` tablolari veri kaynagidir.
- `anamoly_detector.py` bu verilerden anomaliyi hesaplar ve `anomaly_results` tablosuna yazar.
- MCP toollari ve API endpointleri agir modeli tekrar calistirmadan bu tablolari okur.

## 2) Dosya Yapisi

- `services.py`
  - Ortak is mantigi ve DB sorgulari
  - MCP ve API ayni servis fonksiyonlarini kullanir
- `main.py`
  - Sadece MCP server ve tool tanimlari
- `api.py`
  - Sadece FastAPI endpointleri (`/chat` dahil)
- `frontend/`
  - `index.html`, `style.css`, `app.js` (AJAX chat arayuzu)
- `anamoly_detector.py`
  - Offline anomaly pipeline (Isolation Forest + Z-Score -> `anomaly_results`)

## 3) Kurulum

```bash
pip install -r requirements.txt
```

## 4) Ortam Degiskenleri

`.env.example` dosyasini `.env` olarak kopyalayip doldurun:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=network_mcp
DB_USER=postgres
DB_PASSWORD=your_password
```

## 5) Calistirma

### A) MCP Server

```bash
python main.py
```

Inspector ile test:

```bash
npx @modelcontextprotocol/inspector python main.py
```

### B) FastAPI Server

```bash
uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

Kontrol:
- Root: `http://127.0.0.1:8000/`
- Health: `http://127.0.0.1:8000/health`
- Docs: `http://127.0.0.1:8000/docs`

### C) Frontend (AJAX)

```bash
cd frontend
python -m http.server 5500
```

Tarayici:
- `http://127.0.0.1:5500`

## 6) MCP Toollari

1. `get_metrics(cell_id, slice_type=None, since=None, limit=10)`
2. `get_anomalies(cell_id=None, severity=None, only_anomalies=True, limit=50)`
3. `get_faults(cell_id=None, region=None, resolved=None, limit=50)`
4. `get_complaints(cell_id=None, region=None, since=None, limit=50)`
5. `get_station(cell_id=None, region=None, status=None, limit=50)`

## 7) FastAPI Endpointleri

- `GET /`
- `GET /health`
- `GET /metrics`
- `GET /anomalies`
- `GET /faults`
- `GET /complaints`
- `GET /stations`
- `POST /chat`

### `/chat` ornek request

```json
{
  "message": "CELL_017 icin anomali var mi?",
  "limit": 20
}
```

## 8) Demo Akisi (Onerilen)

1. Seed verilerini yukle (`database/` scriptleri).
2. Bir kez anomali hesapla:

```bash
python anamoly_detector.py --mode full
```

3. API ve/veya MCP'yi baslat.
4. Su tip sorularla demo yap:
- `CELL_017 icin anomali var mi?`
- `Buca bolgesinde acik fault var mi?`
- `Konak bolgesinde sikayet var mi?`

## 9) Guvenlik Notlari

- Gercek sifreleri kodda tutmayin.
- `.env` dosyasini repoya eklemeyin (`.gitignore`).
- Sifre sizdigi durumlarda credential rotation uygulayin.

## 10) Sorun Giderme

- `ModuleNotFoundError`: `pip install -r requirements.txt`
- `{"detail":"Not Found"}`:
  - dogru endpoint kullandiginizi kontrol edin (`/`, `/health`, `/docs`)
- Bos sonuc:
  - tabloda veri oldugunu ve filtrelerin dogru oldugunu kontrol edin
  - `anomaly_results` icin `anamoly_detector.py` calistirilmis olmali
