# CarBridge — PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive website for importing cars from China (CarBridge). The platform's business logic and workflow must be deeply integrated with Bitrix24 CRM.

## System Roles
- **Administrator** — full platform control
- **Client** — registration, My Garage, Deals & Tenders, Documents
- **Contractor** — register, tender offers, stage-specific chats, public profile
- **Moderator** — approve contractors, prepayments, deal stages

## Tech Stack
- **Frontend**: React + Shadcn/UI + TailwindCSS
- **Backend**: FastAPI + MongoDB
- **i18n**: Custom React Context (RU/EN)

---

## What's Been Implemented

### Core Platform
- Role-based dashboards, JWT auth, MongoDB
- Database auto-seed on startup (admin, test user, contractor sync)

### Features
- Live car catalog (Che168), My Garage with cost calculator
- Deal/Tender system, Documents with chat, Contractor profiles
- Customs calculator (Decree 140), Two-way Telegram, AI Assistant
- Full i18n RU/EN (Landing, Dashboard, Contractors, Calculator)

### Local Development Setup (Apr 2026)
- `docker-compose.yml` — MongoDB on localhost:27017
- `backend/.env.example` / `frontend/.env.example` — шаблоны переменных
- `scripts/sync-db.sh` — mongodump/mongorestore
- `README.md` — полная инструкция по запуску
- `.gitignore` очищен, `.env.example` разрешён

### Backend Refactoring (Partial)
- `deals.py`, `telegram.py`, `catalog.py` → `/app/backend/routes/`

---

## Pending

### P0
- Backend file uploads for deal stages

### P1
- Continue server.py refactoring (Moderator, Contractors, Applications routes)
- Refactor large frontend components (ModeratorPage, ContractorDashboard)

### P2 / Future
- Payment/escrow system
- WhatsApp Business API (awaiting Meta credentials)
- Cache translated car descriptions

---

## Production Notes
- Production: `carbridge.by`
- Preview changes do NOT auto-deploy — user must redeploy
