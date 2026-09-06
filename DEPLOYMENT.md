# Deploying FlowMind AI

The frontend and backend deploy separately. This guide uses **Vercel** (frontend)
and **Render** (backend + Postgres + Redis) — both have free tiers and need no
credit card to start. Railway or Fly.io work the same way if you prefer them.

## 1. Backend → Render

1. Push this repo to GitHub (see the main README).
2. On https://render.com → **New → Blueprint** → connect the repo. Render reads
   `render.yaml` at the root and provisions the web service, a Postgres database,
   and Redis automatically.
3. Set the secret env vars Render leaves blank (`sync: false`):
   - `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY` — your AI provider keys (either or both)
   - `GOOGLE_CLIENT_ID` — if using Google Sign-In
   - `ALLOWED_ORIGINS` — your Vercel URL, e.g. `https://flowmind-ai.vercel.app`
4. Deploy. Confirm it's healthy at `https://<your-service>.onrender.com/health`.

**No Blueprint support / doing it manually:** create a Web Service pointing at
`backend/Dockerfile`, add a Postgres and a Redis instance from the Render
dashboard, and copy their connection strings into `DATABASE_URL` and `REDIS_URL`.

## 2. Frontend → Vercel

1. On https://vercel.com → **New Project** → import the repo → set the
   **root directory** to `frontend`.
2. Add environment variables (Project Settings → Environment Variables):
   - `NEXT_PUBLIC_API_URL` = your Render backend URL (from step 1)
   - `NEXT_PUBLIC_WS_URL` = same host, `wss://` instead of `https://`
   - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` = same value as the backend's `GOOGLE_CLIENT_ID`
3. Deploy. Vercel builds and gives you a live URL automatically on every push to `main`.
4. Go back to Render and set `ALLOWED_ORIGINS` to that Vercel URL, then redeploy
   the backend so CORS allows it.

## 3. Google Cloud Console — add the production URL

If you're using Google Sign-In, add your live Vercel URL (not just
`localhost:3000`) to **Authorized JavaScript origins** on the OAuth Client ID
at https://console.cloud.google.com/apis/credentials.

## Local Docker alternative

`docker compose up --build` runs the whole stack (frontend, backend, Redis)
on one machine — good for a demo or a college lab machine that doesn't have
public internet access to deploy to.

## Checklist before you demo it live

- [ ] `/health` and `/health/detailed` return 200 on the deployed backend URL
- [ ] Signup/login works end to end from the deployed frontend
- [ ] CORS is set to the exact frontend URL (not `*`) in production
- [ ] At least one AI provider key is set, so document Q&A isn't extractive-only
- [ ] The GitHub Actions CI badge in the README is green
