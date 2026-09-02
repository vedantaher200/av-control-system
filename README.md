# Smart AV Conference Room Automation & Control System

A professional conference-room AV control simulation built with React, Vite, FastAPI, Pydantic, and Supabase PostgreSQL. It models displays, cameras, microphones, speakers, lighting, room modes, automations, monitoring, notifications, activity history, profile management, and an application-aware assistant. It does not claim to control physical AV hardware.

## Run locally

Frontend:

```bash
npm install
npm run dev
```

Backend:

```bash
cd backend
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Frontend defaults to `http://localhost:5173` and uses `VITE_API_URL` from `.env`. The UI remains usable in demo mode when the API or Supabase credentials are unavailable.

## Features

- AV dashboard with room quick controls and live simulated device state
- Profile editing, avatar preview/persistence, and dynamic dashboard greeting
- Notification badge, dropdown, read-all, clear-all, and event generation
- Device, automation, monitoring, activity-log, settings, and profile surfaces
- FastAPI validation, role-protected control/settings routes, health check, and CORS
- Supabase schema for profiles, rooms, devices, history, automations, logs, notifications, and settings
- Vercel-compatible API entry point at `backend/api/index.py`

## Environment

Copy `.env.example` to `.env` for the frontend. Copy `backend/.env.example` to `backend/.env` for the API.

- `VITE_API_URL`
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `SUPABASE_URL`
- `SUPABASE_KEY` or `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET`
- `CORS_ORIGINS`

Never expose service-role credentials to the frontend.

## Supabase

Run `supabase/schema.sql` in the Supabase SQL editor. It creates the core tables, indexes, room seed data, and baseline row-level security policies. Configure Supabase Auth users and create a matching row in `profiles`; profile image references can be stored in the configured Storage bucket.

## API

- `GET /api/health`
- `GET /api/dashboard`
- `GET|PUT /api/profile`
- `GET /api/users`
- `GET /api/rooms`
- `GET|PATCH /api/devices`
- `GET|POST /api/automations`
- `GET|PATCH /api/audio`
- `GET /api/monitoring`
- `GET /api/activity-logs`
- `GET|PATCH|DELETE /api/notifications`
- `GET|PUT /api/settings`

Control routes require a non-viewer role. Settings and user listing require an administrator role. In local demo mode the default role is `Admin`.

## Vercel

Import the repository into Vercel, set `VITE_API_URL` and the server-side Supabase variables, and deploy. `vercel.json` rewrites `/api/*` to the FastAPI ASGI entry point. For production, use a separate API deployment or Vercel Python runtime configuration appropriate to your account and keep service credentials server-side.

## Project structure

```text
src/                 React UI and feature styling
backend/app/main.py  FastAPI API and demo state engine
backend/api/index.py Vercel ASGI entry point
supabase/schema.sql  Supabase schema, indexes, seed, and RLS
```
