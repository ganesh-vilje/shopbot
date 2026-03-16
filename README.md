# 🛍️ ShopBot — AI-Powered E-Commerce Chat Assistant

A production-ready full-stack web application with a ChatGPT-style interface backed by an intelligent SQL agent that answers customer queries in a warm, human-like tone.

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Docker & Docker Compose installed
- OpenAI API key (optional — fallback mode works without it)

### 1. Clone & Configure
```bash
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY (optional but recommended)
```

### 2. Start Everything
```bash
docker compose up --build
```

### 3. Open the App
| Service    | URL                        |
|------------|---------------------------|
| Frontend   | http://localhost:3000      |
| Backend API| http://localhost:8000      |
| API Docs   | http://localhost:8000/docs |

### Demo Credentials
| Email                   | Password    |
|-------------------------|-------------|
| alex@example.com        | Demo@12345  |
| sarah@example.com       | Demo@12345  |
| mike@example.com        | Demo@12345  |

---

## 🏗️ Architecture

```
shopbot/
├── backend/          # FastAPI + Python
│   ├── app/
│   │   ├── agents/   # 4-stage AI pipeline
│   │   ├── api/      # REST endpoints
│   │   ├── models/   # SQLAlchemy ORM
│   │   └── core/     # Config, security, Redis
│   ├── alembic/      # DB migrations
│   └── scripts/      # Seed data
└── frontend/         # Next.js 14
    ├── app/          # App Router pages
    ├── components/   # UI components
    ├── hooks/        # Custom React hooks
    └── lib/          # API client
```

## 🤖 AI Agent Pipeline

```
User Query
    │
    ▼
1. Intent Classifier (GPT-4o-mini)
   → order_status | product_search | price_check | ...
    │
    ▼
2. SQL Generator
   → Safe parameterised SQL template
    │
    ▼
3. Query Executor (PostgreSQL)
   → Raw data rows
    │
    ▼
4. Response Synthesiser (GPT-4o)
   → Warm, human-like streamed response
```

## 🗄️ Database Schema

- **customers** — User profiles, loyalty points, OAuth support
- **products** — Full product catalogue with pricing and stock
- **orders** — Order lifecycle with status tracking
- **order_items** — Line items linking orders to products
- **conversations** — Chat history per user
- **messages** — Individual messages with intent metadata

## 🔒 Security Features

- JWT authentication (15-min access tokens)
- bcrypt password hashing
- Rate limiting (10 login attempts / 15 min per IP)
- CORS protection
- Parameterised SQL (no injection possible)
- Soft deletes for GDPR compliance

## 💬 Example Queries to Try

- "Where is my latest order?"
- "Show me Sony headphones under $400"
- "Is the iPhone 15 Pro in stock?"
- "What are your top-rated laptops?"
- "How many loyalty points do I have?"
- "What's your return policy?"

## ⚙️ Environment Variables

See `.env.example` for all required variables.

Key ones to set for full functionality:
- `OPENAI_API_KEY` — For GPT-powered responses
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — For Google OAuth
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` — For GitHub OAuth

## 🛠️ Development

```bash
# Backend only
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend only  
cd frontend && npm install && npm run dev

# Run migrations
cd backend && alembic upgrade head

# Seed data
cd backend && python scripts/seed_data.py
```
