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
- Landing Page fully translated
- Dashboard Sidebar translated
- ContractorsPage fully translated (including ContractorCard component)
- Calculator page fully translated
- Translation dictionaries: `/app/frontend/src/translations/ru.js` and `en.js`
- Toast messages translated via `messages.*` keys

### Backend Refactoring (Partial)
- `deals.py` extracted to `/app/backend/routes/`
- `telegram.py` extracted to `/app/backend/routes/`
- `catalog.py` in `/app/backend/routes/`

---

## Pending / In Progress

### P0 — High Priority
- **Backend File Uploads for Deal Stages**: UI exists but backend logic to store/associate files with deal stages is missing

### P1 — Medium Priority
- **Continue server.py Refactoring**: Extract Moderator, Contractors, Applications routes into `/app/backend/routes/`
- **Refactor Large Frontend Components**: Break down `ModeratorPage.js` and `ContractorDashboard.js`

### P2 — Low Priority / Future
- Implement full payment/escrow system
- Cache translated car descriptions in MongoDB
- WhatsApp Business API integration (awaiting user Meta credentials)
- Production Telegram webhook update (user action required)

---

## Architecture

```
/app
├── backend/
│   ├── routes/
│   │   ├── deals.py
│   │   ├── telegram.py
│   │   └── catalog.py
│   └── server.py
├── frontend/
│   └── src/
│       ├── contexts/
│       │   ├── AuthContext.js
│       │   └── LanguageContext.js
│       ├── hooks/
│       │   └── useTranslation.js
│       ├── translations/
│       │   ├── ru.js
│       │   └── en.js
│       ├── pages/
│       │   ├── Calculator.js
│       │   ├── ContractorsPage.js
│       │   ├── ContractorProfilePage.js
│       │   ├── LandingPage.js
│       │   └── dashboard/
│       └── components/ui/
└── memory/
    ├── PRD.md
    └── test_credentials.md
```

## Key API Endpoints
- `GET /api/contractors` — list contractors by type
- `GET /api/contractors/page/{id}` — public contractor profile
- `POST /api/calculator` — customs cost calculation
- `POST /api/chat` — AI assistant (accepts `lang` param)
- `DELETE /api/moderator/contractors/{id}` — cascade delete

## Production Notes
- Production domain: `carbridge.by`
- Preview changes do NOT auto-deploy to production — user must redeploy
