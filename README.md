# ShopBot
backend run command: python -m uvicorn app.main:app --reload

ShopBot is a full-stack e-commerce chat assistant with a Next.js frontend and a FastAPI backend backed by PostgreSQL.

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An external PostgreSQL database
- Optional: OpenAI API key for the AI-backed intent and response pipeline

### 1. Configure environment

Copy `.env.example` to `.env` and set at least:

```bash
DATABASE_URL=postgresql://username:password@your-postgres-host:5432/shopbot_db
JWT_SECRET_KEY=replace_this_with_a_real_secret
NEXT_PUBLIC_API_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
```

### 2. Start the backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open the app

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

## Architecture

- `frontend/`: Next.js 14 app router UI
- `backend/app/api/`: FastAPI endpoints
- `backend/app/agents/`: intent classification, SQL generation, execution, and response synthesis
- `backend/app/models/`: SQLAlchemy models
- `backend/alembic/`: database migrations

## Notes

- The app now expects PostgreSQL to be provided externally through `DATABASE_URL`.
- Redis is no longer required.
- Docker is no longer required.
- Refresh sessions are handled with signed JWT cookies instead of Redis-backed token storage.

## Demo accounts

- `alex@example.com` / `Demo@12345`
- `sarah@example.com` / `Demo@12345`
- `mike@example.com` / `Demo@12345`
