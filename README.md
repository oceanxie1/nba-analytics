# NBA Analytics API

FastAPI backend for NBA analytics platform with player stats, team data, and game tracking.

## Setup

1. Create virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize database:
```bash
# Database is auto-created on first run
# Add sample data:
python add_sample_data.py
```

4. Run the server:
```bash
uvicorn app.main:app --reload
```

## API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
python test_api.py
```

## Project Structure

```
app/
├── main.py          # FastAPI app
├── db.py            # Database configuration
├── models.py        # SQLAlchemy models
├── schemas.py       # Pydantic schemas
├── routers/         # API endpoints
└── analytics/       # ML/feature engineering (future)
```

