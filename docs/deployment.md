# Public Deployment Runbook

This app has two deployable services:

- Backend API: FastAPI in `backend/`
- Frontend: Next.js in `frontend/`

Recommended low-friction production path:

- Backend on Render
- Frontend on Vercel

## Backend: Render

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Render will read `render.yaml` at the repo root and create a web service named `home-affordability-api`.
4. Set the `CORS_ORIGINS` environment variable after the frontend URL is known:

```sh
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

5. Deploy. The backend should expose:

```sh
https://your-render-backend-url.onrender.com/v1/health
```

Expected response:

```json
{"status":"ok"}
```

## Frontend: Vercel

1. In Vercel, choose **Add New Project** and select the same GitHub repository.
2. Set the project root directory to:

```sh
frontend
```

3. Add production environment variables:

```sh
NEXT_PUBLIC_API_BASE=/api/backend
BACKEND_API_URL=https://your-render-backend-url.onrender.com
```

4. Deploy. The public app should load at:

```sh
https://your-vercel-app.vercel.app
```

The frontend uses a Next.js rewrite, so browser requests go to `/api/backend/*` and the Vercel server forwards them to FastAPI.

## Verification

After both services deploy:

1. Open the backend health URL:

```sh
https://your-render-backend-url.onrender.com/v1/health
```

2. Open the frontend URL and confirm the dashboard loads without an error banner.
3. In the Vercel project, run or locally simulate the frontend proxy smoke test by setting:

```sh
SMOKE_API_BASE=https://your-vercel-app.vercel.app/api/backend npm run smoke:api
```

## Production Notes

- Keep `CORS_ORIGINS` restricted to the deployed frontend URL.
- Do not log request bodies containing household financial assumptions.
- This app currently has no authentication or persistence, so users should not assume saved cloud storage.
- Keep the planning/not-financial-advice disclaimer visible before public sharing.
- Render free services may sleep after inactivity, so first load can be slow.
