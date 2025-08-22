# KARMABOT1: Production Checklist (Railway)

This checklist documents the verified production configuration for KARMABOT1 bot + FastAPI WebApp on Railway. Use it for post-release validation and future redeploys.

## 1) Services and Deployments
- [ ] Only one active service holds the production BOT_TOKEN.
- [ ] No duplicate services in the project with the same BOT_TOKEN.
- [ ] Current successful deployment is pinned.
- [ ] Autodeploy is configured to the intended branch only, or disabled (manual deploys).

## 2) Environment Variables (Service level)
Do NOT add quotes or trailing spaces. Keep secrets out of VCS.

Required
- BOT_TOKEN = <telegram bot token for the bot used in production>
- ADMIN_ID = 6391215556
- ENVIRONMENT = production
- DATABASE_URL = (Railway Postgres) e.g. ${Postgres.DATABASE_URL}

WebApp & Security
- WEBAPP_QR_URL = https://web-production-d51c7.up.railway.app
- WEBAPP_ALLOWED_ORIGIN = https://web-production-d51c7.up.railway.app
- CSP_ALLOWED_ORIGIN = https://web-production-d51c7.up.railway.app
- JWT_SECRET = <strong random secret>
- AUTH_WINDOW_SEC = 300

Optional
- REDIS_URL = ${Redis.REDIS_URL}
- LOG_LEVEL = INFO

## 3) Health and Endpoints (Production)
- [ ] GET /health returns {"status":"ok"}
- [ ] GET /auth/debug-token returns 404/405 (dev endpoint disabled in prod)
- [ ] WebApp index available at GET / and GET /app

## 4) WebApp Auth Flow (Smoke Test)
Steps
1. In Telegram, open the bot and press the WebApp button (inline keyboard).
2. The page loads and reads Telegram `initData`.
3. Browser sends POST /auth/webapp with initData.
4. Server returns JWT.
5. Browser calls GET /auth/me with the JWT → should return { ok: true, claims: { sub, src: "tg_webapp", ... } }.

Notes
- If you see 401 invalid initData: ensure BOT_TOKEN matches the bot that opened the WebApp.
- If you see "expired": consider increasing AUTH_WINDOW_SEC (e.g., 600–900), but prefer fresh open.

## 5) Monitoring & Alerts
- [ ] Enable Railway alerts: Deployment failed, Service unhealthy.
- [ ] Keep log level at INFO in production.

### If your Railway plan/UI does not have these controls
- Pin/Rollback alternative: use git tags and revert strategy. Keep the last good tag (e.g., v0.1.2). If a deploy breaks, revert the commit or force-push the last good commit to the deploy branch.
- Autodeploy alternative: protect the deploy branch in GitHub (require PR/approvals), and deploy only from this branch. Avoid pushing directly to production branch to prevent unintended deploys.
- Alerts alternative: set external uptime monitoring on GET /health (e.g., UptimeRobot/Better Stack) → email/Telegram alerts. Optionally add a lightweight cron/Action that pings /health and notifies on failure.

## 6) Release Hygiene
- [ ] Tag the release in git (example: v0.1.2) with notes:
  - Fix: Transport/Tours handlers (proper bot param)
  - Add: WebApp landing at / and /app
  - Add: WebApp initData verification + JWT /auth/webapp → /auth/me
  - Add: Version logs for deployment verification

## 7) Rollback Strategy
- Keep the last stable deployment pinned.
- If a new deploy fails or misbehaves, unpin to the previous known good deployment and re‑pin it.

## 8) Security Notes
- Never expose BOT_TOKEN or JWT_SECRET in docs, logs, or screenshots.
- Ensure CORS/CSP origins match the production domain.
- Dev-only endpoints must stay disabled in production.
