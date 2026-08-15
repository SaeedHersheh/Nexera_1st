# Address Intelligence Engine

Independent service for understanding Palestinian descriptive addresses.

## Milestone 1
- PostgreSQL + PostGIS database
- Scalable address knowledge schema
- Arabic address normalizer
- Versioned FastAPI API
- Initial `/api/v1/address/parse` contract
- Health endpoint

## Run

### 1) Start PostgreSQL/PostGIS
```bash
docker compose up -d
```

### 2) Create Python environment
```bash
python -m venv .venv
```

Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

### 4) Copy environment file
Windows:
```powershell
copy .env.example .env
```

Linux/macOS:
```bash
cp .env.example .env
```

### 5) Start API
```bash
uvicorn app.main:app --reload
```

Open:
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

## First test

POST `/api/v1/address/parse`

```json
{
  "address": "طولكرم، اكتابا، بعد مسجد عثمان أول دخلة يمين، البيت الأبيض جنب السوبرماركت"
}
```

This first parser is intentionally conservative. It establishes the API contract and Arabic normalization layer. NLP entity extraction will be added in the next milestone.
