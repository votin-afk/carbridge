# CarBridge — PRD (Product Requirements Document)

## Original Problem Statement
Build a comprehensive website for importing cars from China (CarBridge). The platform's business logic and workflow must be deeply integrated with Bitrix24 CRM.

## System Roles
- **Administrator** — full platform control
- **Client** — registration (creates Bitrix24 contact), My Garage (cost calculator), Prepayment ($500), Deals & Tenders, Documents (stage infographic + chat + files), Contractor Assignment
- **Contractor** — register, submit tender offers, stage-specific chats, public profile
- **Moderator** — approve contractors, prepayments, deal stages

## Core Integrations
- Bitrix24 CRM (user webhook)
- Telegram Bot (two-way notifications)
- Che168 API / auto-api.com (car catalog)
- AI Assistant (Emergent LLM Key)
- WhatsApp Business API (pending user credentials)

## Tech Stack
- **Frontend**: React + Shadcn/UI + TailwindCSS
- **Backend**: FastAPI + MongoDB
- **i18n**: Custom React Context (LanguageContext + useTranslation hook), RU/EN

---

## What's Been Implemented

### Core Platform
- Full-stack app with role-based dashboards (Client, Contractor, Moderator, Admin)
- JWT authentication with registration/login
- MongoDB data layer for users, contractors, deals, tenders, applications, garage
- **Database auto-seed on startup** — creates admin users, test user, syncs approved contractor applications

### Car Catalog & Garage
- Live car catalog from Che168 via auto-api.com proxy
- Image proxy (`/api/proxy/image`) to bypass referrer blocks
- My Garage with cost calculation (turnkey in Belarus)

### Deals & Tenders
- Deal creation flow with stage infographic
- Tender system (contractors submit offers, clients choose)
- Documents section with chat and file upload UI

### Contractor System
- Contractor registration and approval workflow
- Public contractor profile pages (`/contractor/:id`)
- Contractor dashboard with tender management
- Cascade deletion (contractor + associated tenders/deals)

### Calculator
- Full customs clearance calculator (individual/legal entity)
- Decree 140 benefit support (50% discount)
- Platform fee breakdown

### Notifications
- Two-way Telegram integration
- Stage-change notifications

### AI Assistant
- Integrated AI chat on landing page and dashboard
- Language-aware system prompt

### i18n Localization (RU/EN) — COMPLETED Feb 2026
- Custom React Context + useTranslation hook
- Landing Page, Dashboard Sidebar, ContractorsPage, Calculator fully translated
- Translation dictionaries: `ru.js` and `en.js` with `calc.*`, `contractors.*`, `messages.*` sections

### Backend Refactoring (Partial)
- `deals.py`, `telegram.py`, `catalog.py` extracted to `/app/backend/routes/`

### Database Initialization (Apr 2026)
- `@app.on_event("startup")` seed_database function
- Auto-creates admin users from ADMIN_EMAILS list
- Auto-creates test user (test@test.com / test)
- Syncs approved contractor_applications to contractors collection

---

## Pending / In Progress

### P0
- **Backend File Uploads for Deal Stages**: UI exists but backend logic missing

### P1
- **Continue server.py Refactoring**: Extract Moderator, Contractors, Applications routes
- **Refactor Large Frontend Components**: ModeratorPage.js, ContractorDashboard.js

### P2 / Future
- Full payment/escrow system
- Cache translated car descriptions in MongoDB
- WhatsApp Business API (awaiting Meta credentials)
- Production Telegram webhook (user action)

---

## Architecture

```
/app
├── backend/
│   ├── routes/ (deals.py, telegram.py, catalog.py)
│   ├── services/ (bitrix24.py, telegram_service.py, che168.py)
│   └── server.py (main app + startup seed)
├── frontend/src/
│   ├── contexts/ (AuthContext, LanguageContext)
│   ├── hooks/ (useTranslation)
│   ├── translations/ (ru.js, en.js)
│   ├── pages/ (Calculator, ContractorsPage, LandingPage, dashboard/...)
│   └── components/ui/
└── memory/ (PRD.md, test_credentials.md)
```

## Key API Endpoints
- `GET /api/contractors` — list approved contractors
- `POST /api/auth/register` / `POST /api/auth/login`
- `POST /api/calculator` — customs cost calculation
- `POST /api/moderator/applications/{id}/approve` — approve contractor
- `POST /api/moderator/contractors/{id}/approve` — approve contractor (v2)

## Production Notes
- Production: `carbridge.by`
- Preview changes do NOT auto-deploy — user must redeploy
- Admin emails auto-assigned admin role: votin@tut.by, admin@carbridge.by
