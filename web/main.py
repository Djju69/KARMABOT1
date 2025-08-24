from fastapi import FastAPI, Request, Response, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

# Import project settings and auth utils
try:
    from core.settings import settings
    from core.database.migrations import ensure_database_ready
except Exception:
    # Simple fallback settings if core.settings is not available in this environment
    class _Simple:
        class _Features:
            webapp_security = True
        features = _Features()
        class _Web:
            allowed_origin = "*"
            csp_allowed_origin = "*"
        web = _Web()
    settings = _Simple()  # type: ignore

from .routes_auth import router as auth_router
from .routes_auth_email import router as auth_email_router
from web.routes_cabinet import router as cabinet_router
from web.routes_admin import router as admin_router
from web.routes_bot import router as bot_hooks_router
from core.services.cache import cache_service
from ops.session_state import load as ss_load, save as ss_save, update as ss_update, snapshot as ss_snapshot

# Helper: HTML no-store (avoid stale cached bundles)
def _html(content: str, status_code: int = 200) -> HTMLResponse:
    resp = HTMLResponse(content=content, status_code=status_code)
    try:
        resp.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
    except Exception:
        pass
    return resp

# Middleware to add CSP header to responses
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        try:
            csp_origin = getattr(getattr(settings, 'web', None), 'csp_allowed_origin', None) or getattr(settings, 'CSP_ALLOWED_ORIGIN', None)
            if csp_origin:
                # CSP allowing our origin, Telegram resources and inline where necessary for WebApp
                tg_script = "https://telegram.org"
                tg_web = "https://web.telegram.org"
                response.headers["Content-Security-Policy"] = (
                    "default-src 'self' " + str(csp_origin) + "; "
                    "script-src 'self' " + str(csp_origin) + " 'unsafe-inline' " + tg_script + "; "
                    "connect-src 'self' " + str(csp_origin) + " " + tg_script + " " + tg_web + "; "
                    "style-src 'self' " + str(csp_origin) + " 'unsafe-inline'; "
                    "img-src 'self' data: " + str(csp_origin) + "; "
                    "frame-ancestors 'self' " + tg_web + " " + tg_script + ";"
                )
        except Exception:
            pass
        return response

# Middleware: capture ?token= and persist to cookies, with redirect for idempotent methods
class TokenCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            token = request.query_params.get("token")
        except Exception:
            token = None
        # If no token in query, proceed
        if not token:
            return await call_next(request)

        # Inject Authorization/X-Auth-Token into current request scope
        try:
            token_b = token.encode()
            auth_b = b"Bearer " + token_b
            # Clone scope headers and replace/append
            headers = [(k, v) for (k, v) in request.scope.get("headers", []) if k not in (b"authorization", b"x-auth-token")]
            headers.append((b"authorization", auth_b))
            headers.append((b"x-auth-token", token_b))
            scope = dict(request.scope)
            scope["headers"] = headers
            new_request = Request(scope=scope, receive=request.receive)
        except Exception:
            new_request = request

        # Proceed without redirect; token may remain in URL, but cookies will be set
        resp = await call_next(new_request)

        try:
            max_age = 60 * 60 * 24 * 7  # 7 days
            # In Telegram WebView/embedded contexts, cookies require SameSite=None; Secure
            resp.set_cookie("partner_jwt", token, max_age=max_age, path="/", httponly=False, samesite="none", secure=True)
            resp.set_cookie("authToken", token, max_age=max_age, path="/", httponly=False, samesite="none", secure=True)
            resp.set_cookie("jwt", token, max_age=max_age, path="/", httponly=False, samesite="none", secure=True)
        except Exception:
            pass
        return resp

app = FastAPI(title="KARMABOT1 WebApp API")

# Global handler to gracefully handle Method Not Allowed (405)
@app.exception_handler(StarletteHTTPException)
async def _http_exc_handler(request: Request, exc: StarletteHTTPException):
    try:
        if exc.status_code == 405:
            path = request.url.path or ""
            method = (request.method or "").upper()
            # Serve SPA for our UI route regardless of method
            if path.startswith("/cabinet/partner/cards/page"):
                return _html(INDEX_HTML, status_code=200)
            # Generic safety for HEAD/OPTIONS anywhere
            if method in ("HEAD", "OPTIONS"):
                return Response(status_code=204)
    except Exception:
        pass
    return JSONResponse(status_code=exc.status_code, content={"detail": getattr(exc, 'detail', 'error')})

# CORS
try:
    allowed_origin = getattr(getattr(settings, 'web', None), 'allowed_origin', None) or getattr(settings, 'WEBAPP_ALLOWED_ORIGIN', None)
    if allowed_origin:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[allowed_origin],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
except Exception:
    pass

# CSP
app.add_middleware(CSPMiddleware)
app.add_middleware(TokenCookieMiddleware)

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"]) 
app.include_router(auth_email_router, prefix="/auth", tags=["auth"]) 
app.include_router(cabinet_router, prefix="/cabinet", tags=["cabinet"]) 
app.include_router(admin_router, tags=["admin"]) 
app.include_router(bot_hooks_router, prefix="/bot/hooks", tags=["bot_hooks"]) 

# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Cache service lifecycle
@app.on_event("startup")
async def on_startup():
    try:
        # Ensure database is migrated and ready (fail-fast on critical error)
        try:
            ok = ensure_database_ready()
            if not ok:
                # Trigger failure so platform restarts the service with logs
                raise RuntimeError("Database is not ready")
        except Exception as e:
            # Re-raise to prevent starting a broken app
            raise
        # Load persisted session state early
        try:
            ss_load()
            # Optionally enrich components with feature flags if available
            try:
                feats = getattr(settings, 'features', None)
                if feats:
                    ss_update(patch={
                        "feature_flags": {k: bool(getattr(feats, k)) for k in dir(feats) if not k.startswith('_')}
                    })
            except Exception:
                pass
        except Exception:
            pass
        await cache_service.connect()
    except Exception:
        pass


@app.on_event("shutdown")
async def on_shutdown():
    try:
        # Persist final session state snapshot
        try:
            ss_save()
        except Exception:
            pass
        await cache_service.close()
    except Exception:
        pass

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/healthz")
async def healthz():
    try:
        snap = ss_snapshot()
    except Exception:
        snap = {"version": getattr(settings, 'VERSION', 'v0.0.0'), "generated_at": None, "components": {}}
    return {
        "status": "ok",
        "version": snap.get("version"),
        "generated_at": snap.get("generated_at"),
        "node_id": snap.get("node_id"),
        "components": list((snap.get("components") or {}).keys()),
    }


# --- Utility: set JWT into cookies and redirect to partner cards
@app.api_route("/auth/set-token", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def set_token(request: Request, token: str | None = Query(default=None), token_body: str | None = Form(default=None)):
    """Accepts ?token=...; sets cookies 'partner_jwt' and 'authToken' and redirects to /cabinet/partner/cards.
    Works both inside and outside Telegram WebApp.
    """
    token_val = token or token_body
    if not token_val:
        # try JSON body {"token": "..."}
        try:
            data = await request.json()
            if isinstance(data, dict):
                token_val = data.get("token")
        except Exception:
            pass
    if not token_val:
        # No token provided
        return JSONResponse(status_code=400, content={"detail": "missing token parameter"})
    # Set cookies for WebView/browser; SameSite=None and Secure=True for embedded contexts
    max_age = 60 * 60 * 24 * 7  # 7 days
    resp = RedirectResponse(url="/cabinet/partner/cards/page", status_code=302)
    try:
        resp.set_cookie("partner_jwt", token_val, max_age=max_age, path="/", httponly=False, samesite="none", secure=True)
        resp.set_cookie("authToken", token_val, max_age=max_age, path="/", httponly=False, samesite="none", secure=True)
        resp.set_cookie("jwt", token_val, max_age=max_age, path="/", httponly=False, samesite="none", secure=True)
    except Exception:
        pass
    return resp


# --- Partner Cards UI page (HTML) at /cabinet/partner/cards/page
# Allow GET/POST/HEAD/OPTIONS to avoid 405 from various clients/embeds
@app.api_route("/cabinet/partner/cards/page", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], response_class=HTMLResponse)
async def partner_cards_page():
    # Serve the main SPA/HTML used by partner cards UI
    # Token can be set beforehand via /auth/set-token?token=...
    # Frontend also attempts to read token from URL/localStorage and fallback to cookies
    return _html(INDEX_HTML)

# Support trailing slash to avoid 405/redirect loops on some clients
@app.api_route("/cabinet/partner/cards/page/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"], response_class=HTMLResponse)
async def partner_cards_page_slash():
    return _html(INDEX_HTML)

# Global HEAD/OPTIONS catch-all to prevent 405 for preflights and HEAD probes
@app.api_route("/{_catch_all:path}", methods=["HEAD", "OPTIONS"])
async def catch_all_head_options(_catch_all: str):
    return Response(status_code=204)

# --- Disable any legacy PWA artifacts and noisy assets
@app.get("/sw.js")
async def sw_js():
    # Explicitly disabled service worker to avoid cache hijacking
    return Response(content="/* service worker disabled */", media_type="application/javascript", headers={
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
    })

@app.get("/favicon.ico")
async def favicon():
    # Avoid 405 in logs
    return Response(status_code=204)

@app.get("/dist/{path:path}")
async def legacy_dist(path: str):
    # Tell browser these bundles are gone
    return Response(status_code=410)


# Minimal WebApp landing page so WEBAPP_QR_URL can point to the root URL
import os as _os
_SHOW_DEBUG_UI = str(_os.getenv("SHOW_DEBUG_UI", "0")).strip() in ("1","true","yes","on")

# Use a plain string and substitute a placeholder to avoid f-string brace issues with CSS/JS
_INDEX_HTML_RAW = """
<!doctype html>
<html lang=\"ru\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>KARMABOT1 WebApp</title>
    <script src=\"https://telegram.org/js/telegram-web-app.js\"></script>
    <style>
      :root { --bg:#0b1020; --card:#0f172a; --text:#e5e7eb; --muted:#94a3b8; --primary:#2563eb; --stroke:#1f2937; }
      * { box-sizing: border-box; }
      body { font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin:0; background: var(--bg); color: var(--text); }
      .shell { max-width: 980px; margin: 0 auto; padding: 20px; }
      .card { border: 1px solid var(--stroke); border-radius: 14px; background: linear-gradient(180deg, #0f172a 0%, #0b1224 100%); padding: 16px; }
      .toolbar { display:flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 12px; border:1px solid var(--stroke); border-radius: 12px; background: rgba(255,255,255,0.02); }
      .title { display:flex; align-items:center; gap:10px; font-weight:600; letter-spacing:0.2px; }
      .actions { display:flex; gap:8px; flex-wrap:wrap; }
      .btn { padding:9px 12px; border-radius:10px; border:1px solid var(--stroke); background:#0b1327; color:var(--text); cursor:pointer; }
      .btn:hover { background:#0d1731; }
      .btn.primary { background: var(--primary); border-color: var(--primary); }
      .btn.ghost { background: transparent; }
      .muted { color: var(--muted); }
      pre { background: #0b1327; color:#e2e8f0; padding: 12px; border-radius: 10px; overflow: auto; border:1px solid var(--stroke); }
      .tabs { display:flex; gap:8px; margin: 14px 0; flex-wrap: wrap; }
      .tab { padding:8px 12px; border:1px solid var(--stroke); border-radius:10px; background:#0b1327; cursor:pointer; color:#cbd5e1; }
      .tab.active { background:#0f172a; color:#fff; border-color:#334155; }
      .section { display:none; }
      .section.active { display:block; }
      ul.clean { list-style:none; padding-left:0; }
      ul.clean li { padding:8px 0; border-bottom:1px dashed #273247; }
      .spacer { height: 12px; }
      /* Compact controls */
      .controls { position:relative; display:flex; gap:8px; align-items:center; flex-wrap:wrap }
      .controls.filter-open > #q,
      .controls.filter-open > #btnSearch,
      .controls.filter-open > #btnAdd { display: none; }
      .lbl { color: var(--muted); font-size:10px; margin-right:2px }
      /* ~70% sizing */
      .xs { padding:3px 7px !important; border-radius:6px !important; font-size:10px !important; line-height:1.2 }
      /* ~90% reduction for filter selects */
      .xs-slim { padding:2px 5px !important; border-radius:6px !important; font-size:9px !important; line-height:1.1 }
      select.xs, input.xs { background:#0b1020; border:1px solid #334155; color:#e5e7eb }
      select.xs { min-width: 90px }
      #q.xs { min-width: 140px }
      .filter-popover { position:absolute; right:0; top: calc(100% + 6px); background:#0b1327; border:1px solid #334155; border-radius:10px; padding:10px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); min-width: 240px; display:none; z-index: 1000 }
      .filter-popover .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap }
      .filter-actions { display:flex; gap:8px; justify-content:flex-end; margin-top:5mm }
    </style>
  </head>
  <body>
          <button id=\"openInBrowser\" class=\"btn ghost\">🌐 Открыть в браузере</button>
          <button id=\"btnMyCards\" class=\"btn primary\">Мои карточки</button>
          <button id=\"toggleDetails\" class=\"btn ghost\">Показать детали</button>
          <button id=\"showToken\" class=\"btn ghost\">Показать токен</button>
          <button id=\"copyToken\" class=\"btn\" style=\"display:none\">Копировать</button>
          <button id=\"btnDevToken\" class=\"btn ghost\" title=\"Получить dev-токен без Telegram\">Dev токен</button>
        </div>
        <div id=\"devTokenPanel\" style=\"margin:8px 0; display:block\">
          <input id=\"tokenInput\" class=\"xs\" type=\"text\" placeholder=\"Вставьте JWT токен (admin/partner)\" style=\"min-width:320px\" />
          <button id=\"btnApplyToken\" class=\"btn\">Применить токен</button>
        </div>
      <!-- Image lightbox -->
      <div id="imgLightbox" style="position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.8);z-index:1600">
        <img id="imgLightboxImg" src="" alt="" style="max-width:95vw;max-height:90vh;border-radius:10px;border:1px solid #334155"/>
      </div>
      </div>
      <div class=\"spacer\"></div>
      <p class=\"muted\">Авторизация через Telegram initData → POST /auth/webapp → /auth/me</p>
      <div id=\"status\">Инициализация…</div>
      <div id=\"error\" class=\"muted\" style=\"color:#f87171; margin-top:6px\"></div>
      <pre id=\"diag\" class=\"muted\" style=\"white-space:pre-wrap; margin-top:6px\"></pre>
      <div id=\"claims\" style=\"display:none\">
        <h3>Claims</h3>
        <pre id=\"claimsPre\"></pre>
      </div>
      <div style=\"margin-top:12px\">
        <button id=\"retry\" class=\"btn\" style=\"display:none\">Повторить авторизацию</button>
      </div>
      <div id=\"tokenBox\" class=\"muted\" style=\"display:none; word-break:break-all; margin-top:6px\"></div>
      <div id=\"cabinet\" style=\"display:none; margin-top:16px\">
        <div class=\"tabs\"> 
          <div class=\"tab active\" data-tab=\"profile\">Профиль</div>
          <div class=\"tab\" data-tab=\"mycards\">Мои карточки</div>
        </div>

        <div id=\"section-profile\" class=\"section active\">
          <h3>Профиль</h3>
          <div id=\"authStatus\" class=\"muted\"></div>
          <div id=\"profileBox\" class=\"muted\">Загрузка…</div>
        </div>

        <div id=\"section-mycards\" class=\"section\"> 
          <h3>Мои карточки</h3>
          <div id=\"cardsEmpty\" class=\"muted\" style=\"display:none\">Карточек пока нет</div>
          <ul id=\"cardsList\" class=\"clean\"></ul>
        </div>
      </div>
    </div>

    <script>
      const SHOW_DEBUG_UI = __SHOW_DEBUG_PLACEHOLDER__;
      // --- Auth bootstrap helpers: read token from URL/localStorage/cookies and inject Authorization header globally
      function getQueryParam(name){
        try { return new URL(window.location.href).searchParams.get(name); } catch(_) { return null }
      }

      // Dev token flow: allow manual token entry when Telegram is unavailable
      async function devTokenFlow(tokenFromUI){
        try {
          let t = tokenFromUI;
          if (!t) t = prompt('Вставьте JWT токен (admin/partner):');
          if (!t) return;
          try {
            localStorage.setItem('partner_jwt', t);
            localStorage.setItem('jwt', t);
            localStorage.setItem('authToken', t);
          } catch(_) {}
          document.cookie = 'partner_jwt=' + encodeURIComponent(t) + '; path=/';
          document.cookie = 'authToken=' + encodeURIComponent(t) + '; path=/';
          document.cookie = 'jwt=' + encodeURIComponent(t) + '; path=/';
          window.__authToken = t;
          try { const s = document.getElementById('status'); if (s) s.textContent = 'Сохраняю токен…'; } catch(_) {}
          try { await fetch('/auth/set-token?token=' + encodeURIComponent(t), { method: 'POST' }); } catch(_) {}
          // Сразу пробуем загрузить профиль без ожидания редиректа — чтобы пользователь видел результат
          try { const s = document.getElementById('status'); if (s) s.textContent = 'Загружаю профиль…'; } catch(_) {}
          try { await loadProfile(t); } catch(_) {}
          // Затем "мягко" пробуем перейти на canonical URL с ?token
          try { window.location.href = '/cabinet/partner/cards/page?token=' + encodeURIComponent(t); return; } catch(_) {}
        } catch (e) {
          alert('Ошибка установки токена: ' + (e && e.message ? e.message : e));
        }
      }
      (function installDevTokenHandler(){
        try {
          const btn = document.getElementById('btnDevToken');
          if (btn) btn.addEventListener('click', () => devTokenFlow());
          const applyBtn = document.getElementById('btnApplyToken');
          const input = document.getElementById('tokenInput');
          if (applyBtn && input) {
            applyBtn.addEventListener('click', () => {
              try { const s = document.getElementById('status'); if (s) s.textContent = 'Применяю токен…'; } catch(_) {}
              devTokenFlow(input.value && input.value.trim());
            });
            // Нажатие Enter в поле ввода — как клик по кнопке
            input.addEventListener('keydown', (ev) => {
              if (ev && (ev.key === 'Enter' || ev.keyCode === 13)) {
                ev.preventDefault();
                applyBtn.click();
              }
            });
          }
          // Fallback: delegation, in case initial binding failed or DOM replaced
          document.addEventListener('click', (ev) => {
            const el = ev.target && (ev.target.closest ? ev.target.closest('#btnDevToken') : null);
            if (el) { ev.preventDefault(); devTokenFlow(); }
          }, { capture: true });
        } catch(_) {}
      })();
      function readCookie(name){
        try {
          const m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\\/\+^])/g,'\\$1') + '=([^;]*)'));
          return m ? decodeURIComponent(m[1]) : null;
        } catch(_) { return null }
      }
      function pickToken(){
        try {
          const q = getQueryParam('token');
          if (q) {
            try {
              localStorage.setItem('partner_jwt', q);
              localStorage.setItem('jwt', q);
              console.info('[auth] token picked from ?token, saved to localStorage');
            } catch(_) {}
            return q;
          }
        } catch(_) {}
        try {
          const ls = localStorage.getItem('partner_jwt') || localStorage.getItem('authToken') || localStorage.getItem('jwt');
          if (ls) return ls;
        } catch(_) {}
        try {
          const c = readCookie('partner_jwt') || readCookie('authToken') || readCookie('jwt');
          if (c) return c;
        } catch(_) {}
        return null;
      }
      function asciiToken(t){
        try {
          const s = String(t);
          let out = '';
          for (let i = 0; i < s.length; i++) {
            const code = s.charCodeAt(i);
            if (code >= 32 && code <= 126) out += s[i];
          }
          return out;
        } catch(_) { return ''; }
      }
      // Minimal error helper used by cards/profile loaders
      function showError(msg){
        try {
          const el = document.getElementById('status') || document.getElementById('authStatus');
          if (el) el.textContent = typeof msg === 'string' ? msg : (msg && msg.message) ? msg.message : String(msg);
        } catch(_) { /* no-op */ }
      }
      async function clearCachesAndSW(){
        try {
          if ('serviceWorker' in navigator) {
            const regs = await navigator.serviceWorker.getRegistrations();
            for (const r of regs) try { await r.unregister(); } catch(_) {}
          }
        } catch(_) {}
        try {
          if (window.caches && caches.keys) {
            const keys = await caches.keys();
            for (const k of keys) try { await caches.delete(k); } catch(_) {}
          }
        } catch(_) {}
      }
      (function installFetchAuth(){
        try {
          const orig = window.fetch;
          if (!orig || orig.__withAuthInstalled) return;
          window.fetch = async function(input, init){
            try {
              const url = (typeof input === 'string') ? input : (input && input.url) || '';
              const sameOrigin = !/^https?:\/\//i.test(url) || url.startsWith(window.location.origin);
              const token = window.__authToken || pickToken();
              if (sameOrigin && token) {
                init = init || {};
                const headers = new Headers(init.headers || (typeof input !== 'string' && input && input.headers) || {});
                const at = asciiToken(token);
                if (at && !headers.has('Authorization')) headers.set('Authorization', 'Bearer ' + at);
                init.headers = headers;
              }
            } catch(_) { /* ignore */ }
            return orig.apply(this, arguments);
          };
          window.fetch.__withAuthInstalled = true;
        } catch (_) { /* ignore */ }
      })();

      function logDiag(msg){
        try{
          const d = document.getElementById('diag');
          if (d) d.textContent = (d.textContent ? (d.textContent + "\n") : '') + msg;
        }catch(_){ }
      }
      async function bootstrapAuthIfPossible(){
        try{
          // best-effort: clear caches/SW once to avoid stale bundles
          clearCachesAndSW().catch(()=>{});
          try { const s = document.getElementById('status'); if (s) s.textContent = 'Поиск токена…'; } catch(_) {}
          const token = pickToken();
          if (token) {
            window.__authToken = token;
            try { document.getElementById('authStatus').textContent = 'Токен найден'; } catch(_) {}
            logDiag('token: найден (URL/cookie/localStorage)');
            try { const s = document.getElementById('status'); if (s) s.textContent = 'Токен найден, загружаю профиль…'; } catch(_) {}
          } else {
            try { document.getElementById('authStatus').textContent = 'Токен не найден'; } catch(_) {}
            try { const inp = document.getElementById('tokenInput'); if (inp) { inp.focus(); inp.select && inp.select(); } } catch(_) {}
            logDiag('token: не найден, пробую Telegram initData');
            try { const s = document.getElementById('status'); if (s) s.textContent = 'Токен не найден, пытаюсь Telegram initData…'; } catch(_) {}
          }
          if (token) {
            await loadProfile(token);
          } else {
            // fallback to Telegram initData authorization
            authWithInitData();
          }
        } catch (e) {
          console.error('[auth] bootstrap error', e);
          logDiag('bootstrap error: ' + (e && e.message ? e.message : e));
        }
      }
      async function loadProfile(token) {
        const box = document.getElementById('profileBox');
        try {
          console.info('[auth] loading profile…');
          const at = asciiToken(token);
          let r = await fetch('/cabinet/profile', { headers: { 'Authorization': 'Bearer ' + at } });
          if (!r.ok) {
            const txt = await r.text().catch(()=> '');
            console.warn('[auth] profile with header failed', r.status, txt);
            // Retry with query param to bypass header issues
            r = await fetch('/cabinet/profile?token=' + encodeURIComponent(token));
          }
          if (!r.ok) {
            const t2 = await r.text().catch(()=> '');
            throw new Error('HTTP ' + r.status + (t2 ? (' · ' + t2) : ''));
          }
          const data = await r.json();
          box.textContent = `ID: ${data.user_id} · Язык: ${data.lang} · Источник: ${data.source}`;
          const s = document.getElementById('authStatus');
          if (s) s.textContent = 'Авторизация успешна';
          try { const cab = document.getElementById('cabinet'); if (cab) cab.style.display = 'block'; } catch(_) {}
          // После успешной загрузки профиля — подгрузим «Мои карточки»
          try { await loadMyCards(token); } catch(_e) { console.warn('[cards] load after profile failed', _e); }
        } catch (e) {
          box.textContent = 'Ошибка загрузки профиля: ' + (e.message || e);
          const s = document.getElementById('authStatus');
          if (s) s.textContent = 'Нет авторизации или ошибка профиля';
          console.error('[auth] profile error', e);
        }
      }

      async function loadMyCards(token) {
        const list = document.getElementById('cardsList');
        const empty = document.getElementById('cardsEmpty');
        if (!list || !empty) return;
        list.innerHTML = '';
        empty.style.display = 'none';
        try {
          console.info('[cards] loading…');
          const at = asciiToken(token);
          let r = await fetch('/cabinet/partner/cards?limit=20', { headers: { 'Authorization': 'Bearer ' + at } });
          if (!r.ok) {
            const txt = await r.text().catch(()=> '');
            console.warn('[cards] header auth failed', r.status, txt);
            r = await fetch('/cabinet/partner/cards?limit=20&token=' + encodeURIComponent(token));
          }
          if (!r.ok) throw new Error('HTTP ' + r.status);
          const data = await r.json();
          const items = (data && data.items) || [];
          if (!items.length) {
            empty.style.display = 'block';
            console.info('[cards] empty list');
            return;
          }
          for (const it of items) {
            const li = document.createElement('li');
            li.textContent = `#${it.id} · ${it.title || '(без названия)'} · статус: ${it.status}`;
            list.appendChild(li);
          }
        } catch (e) {
          showError('Ошибка загрузки карточек: ' + (e && e.message ? e.message : e));
          console.error('[cards] error', e);
        }
      }

      async function authWithInitData() {
        const s = document.getElementById('status');
        const retry = document.getElementById('retry');
        const err = document.getElementById('error');
        try {
          console.info('[auth] trying Telegram initData flow…');
          if (err) err.textContent = '';
          if (retry) retry.style.display = 'none';
          const initData = (window.Telegram && Telegram.WebApp && Telegram.WebApp.initData) || '';
          if (!initData) {
            throw new Error('initData пустой: откройте в Telegram WebApp');
          }

          s.textContent = 'Отправка initData → /auth/webapp…';
          const resp = await fetch('/auth/webapp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData })
          });

          if (!resp.ok) {
            const text = await resp.text();
            if (err) err.textContent = 'Ошибка авторизации (' + resp.status + '): ' + text;
            if (retry) retry.style.display = 'inline-block';
            return;
          }
          const data = await resp.json();
          const token = data.token;
          if (!token) {
            if (err) err.textContent = 'Сервер не вернул token';
            if (retry) retry.style.display = 'inline-block';
            return;
          }
          try { localStorage.setItem('partner_jwt', token); localStorage.setItem('jwt', token); } catch(_){ }
          window.__authToken = token;
          s.textContent = 'Успешно! Загружаю профиль…';
          // Reveal token tools (debug only)
          try {
            const tb = document.getElementById('tokenBox');
            const copyBtn = document.getElementById('copyToken');
            const showBtn = document.getElementById('showToken');
            if (SHOW_DEBUG_UI) {
              showBtn.style.display = 'inline-block';
              showBtn.onclick = () => {
                tb.textContent = token;
                tb.style.display = 'block';
                copyBtn.style.display = 'inline-block';
              };
              copyBtn.onclick = async () => {
                try { await navigator.clipboard.writeText(token); showBtn.textContent = 'Токен скопирован'; }
                catch (_) { showBtn.textContent = 'Скопируйте вручную ниже'; }
              };
            } else {
              showBtn.style.display = 'none';
            }
          } catch (e) { /* no-op */ }

          const meResp = await fetch('/auth/me', { headers: { 'Authorization': 'Bearer ' + token } });
          const me = await meResp.json().catch(() => ({}));
          const claimsPre = document.getElementById('claimsPre');
          claimsPre.textContent = JSON.stringify(me, null, 2);
          // Не показываем детали автоматически; доступны по кнопке
          s.textContent = 'Успешно! Запрашиваю /auth/me…';

          // Ensure toolbar has "Мои карточки" entry (fallback in case of cached HTML)
          try {
            const actions = document.querySelector('.toolbar .actions');
            if (actions && !document.getElementById('btnMyCards')) {
              const btn = document.createElement('button');
              btn.id = 'btnMyCards';
              btn.className = 'btn primary';
              btn.textContent = 'Мои карточки';
              btn.addEventListener('click', () => {
                const url = window.location.origin + '/cabinet/partner/cards/page';
                window.location.href = url;
              });
              // insert as first button after openInBrowser if present
              const ref = document.getElementById('openInBrowser');
              if (ref && ref.parentElement === actions) {
                actions.insertBefore(btn, ref.nextSibling);
              } else {
                actions.prepend(btn);
              }
            }
          } catch (e) { /* ignore */ }

          // In-page fallback entry inside cabinet content
          try {
            const cab = document.getElementById('cabinet');
            if (cab && !document.getElementById('gotoMyCards')) {
              const wrap = document.createElement('div');
              wrap.style.margin = '8px 0 0';
              const a = document.createElement('a');
              a.id = 'gotoMyCards';
              a.href = '/cabinet/partner/cards/page';
              a.textContent = '→ Перейти к моим карточкам';
              a.className = 'btn';
              a.style.marginLeft = '8px';
              a.addEventListener('click', (ev) => {
                ev.preventDefault();
                const url = window.location.origin + '/cabinet/partner/cards/page';
                window.location.href = url;
              });
              wrap.appendChild(a);
              cab.insertBefore(wrap, cab.firstChild);
            }
          } catch (e) { /* ignore */ }

          // Show cabinet sections and load data
          document.getElementById('cabinet').style.display = 'block';
          try {
            const caps = (me && me.capabilities) || [];
            const canScan = (me && me.partner && me.partner.can_scan_qr) || (Array.isArray(caps) && caps.includes('qr:scan'));
            const btnScan = document.getElementById('btnScanQR');
            if (canScan && btnScan) {
              btnScan.style.display = 'inline-block';
            } else if (btnScan) {
              btnScan.style.display = 'none';
            }
          } catch (e) { /* ignore */ }
          await loadProfile(token);
          // Defer orders until tab click to save requests
        } catch (e) {
          err.textContent = 'Ошибка авторизации: ' + (e.message || e);
          retry.style.display = 'inline-block';
          console.error('[auth] initData error', e);
        }
      }
      document.getElementById('retry').addEventListener('click', authWithInitData);
      // Kick off bootstrap on page load
      try {
        if (document.readyState === 'loading') {
          document.addEventListener('DOMContentLoaded', ()=> { bootstrapAuthIfPossible().catch(()=>{}); });
        } else {
          // already loaded
          bootstrapAuthIfPossible().catch(()=>{});
        }
      } catch(_) { /* ignore */ }
      // Simple tab switcher used by click handler
      function selectTab(name){
        try {
          const tabs = document.querySelectorAll('.tab');
          tabs.forEach(t => t.classList.remove('active'));
          const sections = document.querySelectorAll('.section');
          sections.forEach(s => s.classList.remove('active'));
          const tabEl = document.querySelector('.tab[data-tab="' + name + '"]');
          if (tabEl) tabEl.classList.add('active');
          const sec = document.getElementById('section-' + name);
          if (sec) sec.classList.add('active');
        } catch(_) { /* ignore */ }
      }
      document.addEventListener('click', async (ev) => {
        const t = ev.target;
        if (t && t.classList && t.classList.contains('tab')) {
          const name = t.dataset.tab;
          selectTab(name);
          if (name === 'mycards') {
            try {
              const token = window.__authToken || pickToken();
              if (token) {
                await loadMyCards(token);
              } else {
                // как fallback оставим переход на standalone-страницу
                const url = window.location.origin + '/cabinet/partner/cards/page';
                window.location.href = url;
              }
            } catch(_) {}
          }
        }
      });
      // Open in external browser
      try {
        const btn = document.getElementById('openInBrowser');
        if (btn) {
          btn.addEventListener('click', () => {
            const url = window.location.href;
            if (window.Telegram && Telegram.WebApp && typeof Telegram.WebApp.openLink === 'function') {
              Telegram.WebApp.openLink(url);
            } else {
              window.open(url, '_blank');
            }
          });
        }
      } catch (e) { /* noop */ }
      // Open partner cards UI (navigate in-place to avoid external window issues in Telegram)
      try {
        const btn = document.getElementById('btnMyCards');
        if (btn) {
          btn.addEventListener('click', () => {
            const url = window.location.origin + '/cabinet/partner/cards/page';
            window.location.href = url;
          });
        }
      } catch (e) { /* noop */ }
      // Toggle details (claims) — debug only
      try {
        const btn = document.getElementById('toggleDetails');
        const box = document.getElementById('claims');
        if (btn && box) {
          if (!SHOW_DEBUG_UI) { btn.style.display = 'none'; box.style.display='none'; }
          btn.addEventListener('click', () => {
            const shown = box.style.display !== 'none';
            box.style.display = shown ? 'none' : 'block';
            btn.textContent = shown ? 'Показать детали' : 'Скрыть детали';
          });
          // стартуем скрытым
          box.style.display = 'none';
        }
      } catch (e) { /* noop */ }
      // QR button click placeholder
      try {
        const btn = document.getElementById('btnScanQR');
        if (btn) {
          btn.addEventListener('click', () => {
            alert('Сканер QR будет доступен в мобильном приложении. Пока заглушка.');
          });
        }
      } catch (e) { /* noop */ }
      // If token already saved (повторный визит), настрой debug-кнопки
      try {
        const saved = localStorage.getItem('partner_jwt') || localStorage.getItem('authToken') || localStorage.getItem('jwt');
        if (saved) {
          const tb = document.getElementById('tokenBox');
          const copyBtn = document.getElementById('copyToken');
          const showBtn = document.getElementById('showToken');
          if (SHOW_DEBUG_UI) {
            showBtn.style.display = 'inline-block';
            showBtn.onclick = () => {
              tb.textContent = saved;
              tb.style.display = 'block';
              copyBtn.style.display = 'inline-block';
            };
            copyBtn.onclick = async () => {
              try { await navigator.clipboard.writeText(saved); showBtn.textContent = 'Токен скопирован'; }
              catch (_) { showBtn.textContent = 'Скопируйте вручную ниже'; }
            };
          } else {
            showBtn.style.display = 'none';
          }
        }
      } catch (e) { /* ignore */ }
      // Unified bootstrap handled by bootstrapAuthIfPossible() above
    </script>
  </body>
</html>
"""

# Inject the actual boolean literal safely
INDEX_HTML = _INDEX_HTML_RAW.replace("__SHOW_DEBUG_PLACEHOLDER__", "true" if _SHOW_DEBUG_UI else "false")


@app.api_route("/", methods=["GET", "HEAD", "OPTIONS"], response_class=HTMLResponse)
async def index():
  try:
    env = getattr(settings, 'ENVIRONMENT', None) or getattr(settings, 'environment', None) or getattr(getattr(settings, 'web', None), 'environment', None)
    if str(env).lower() == 'production':
      from fastapi.responses import RedirectResponse
      import time as _t
      return RedirectResponse(url=f"/cabinet/partner/cards/page?v={int(_t.time())}", status_code=302)
  except Exception:
    pass
  return _html(INDEX_HTML)


@app.api_route("/app", methods=["GET", "HEAD", "OPTIONS"], response_class=HTMLResponse)
async def app_page():
  try:
    env = getattr(settings, 'ENVIRONMENT', None) or getattr(settings, 'environment', None) or getattr(getattr(settings, 'web', None), 'environment', None)
    if str(env).lower() == 'production':
      from fastapi.responses import RedirectResponse
      import time as _t
      return RedirectResponse(url=f"/cabinet/partner/cards/page?v={int(_t.time())}", status_code=302)
  except Exception:
    pass
  return _html(INDEX_HTML)


# Optional utility endpoints for local smoke checks
@app.get("/qr/ping")
async def qr_ping():
    return {"status": "ok"}


@app.post("/cache/invalidate")
async def cache_invalidate(payload: dict | None = None):
    # Safe no-op stub for local testing; integrate cache_service if needed
    scope = (payload or {}).get("scope") if isinstance(payload, dict) else None
    try:
        # If cache_service has clear/invalidate in your project, you can call it here.
        # We keep it a stub to avoid import/runtime issues.
        pass
    except Exception:
        pass
    return {"status": "ok", "scope": scope or "*"}


@app.get("/reports/rate_limit")
async def reports_rate_limit():
    # Static demo data for smoke testing
    return {"window": "1m", "limit": 1000, "remaining": 1000, "reset_sec": 60}


@app.get("/i18n/keys")
async def i18n_keys():
    # Minimal key list for UI checks
    return {"keys": [
        "home.title",
        "menu.refresh",
        "error.generic",
        "auth.login",
        "auth.logout",
    ]}

# --- Static assets (logo etc.)
try:
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
except Exception:
    # If folder absent locally, ignore
    pass

# --- Privacy Policy page (/policy)
_POLICY_HTML = """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Политика обработки персональных данных — Karma System</title>
    <style>
      body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0b1020;color:#e5e7eb}
      .page{max-width:900px;margin:0 auto;padding:24px}
      .card{background:#0f172a;border:1px solid #1f2937;border-radius:14px;padding:20px}
      h1{margin:0 0 8px 0;font-size:22px}
      .muted{color:#94a3b8}
      img.logo{width:80px;height:80px;border-radius:50%;object-fit:cover}
      .hdr{display:flex;gap:14px;align-items:center;margin:8px 0 18px}
      h2{font-size:18px;margin:18px 0 8px}
      ul{margin:8px 0 8px 20px}
      li{margin:6px 0}
    </style>
  </head>
  <body>
    <div class="page">
      <div class="card">
        <div class="hdr">
          <img class="logo" src="/static/logo.png" alt="Karma System" onerror="this.style.display='none'" />
          <div>
            <h1>📄 Политика обработки персональных данных</h1>
            <div class="muted">Karma System</div>
          </div>
        </div>
        <div id="content">
          <p><b>Кто мы</b><br/>Оператор: karma_system_official<br/>Для связи по вопросам персональных данных: @karma_system_official</p>
          <p>Публичное лицо проекта: @karma_system_official (лицо, осуществляющее коммуникацию).</p>
          <h2>1. Общие положения</h2>
          <p>Настоящая Политика действует в отношении всех данных, которые karma_system_official (далее — «Оператор») может получить от пользователей Telegram-бота, а также других цифровых продуктов под брендом Karma System.</p>
          <h2>2. Какие данные мы собираем</h2>
          <ul>
            <li>Имя и username в Telegram</li>
            <li>Контактные данные (телефон, email — если указаны пользователем)</li>
            <li>Ответы в формах и заявках</li>
            <li>IP-адрес и технические метаданные (если применимо)</li>
          </ul>
          <h2>3. Цели обработки данных</h2>
          <ul>
            <li>Обработка заявок и коммуникация по услугам</li>
            <li>Маркетинговая аналитика</li>
          </ul>
          <h2>4. Кто имеет доступ к данным</h2>
          <ul>
            <li>Оператор и лица, осуществляющие взаимодействие с пользователями</li>
            <li>Подрядчики по договорам (например, техподдержка)</li>
            <li>Другие пользователи бота при участии в нетворкинге (только username, с согласия)</li>
            <li>Пользователь, пригласивший вас по ссылке (только username)</li>
          </ul>
          <h2>5. Безопасность данных</h2>
          <p>Мы применяем административные, технические и физические меры для защиты информации от несанкционированного доступа, утраты или раскрытия.</p>
          <h2>6. Срок хранения</h2>
          <p>Данные хранятся до отзыва согласия пользователем или до окончания актуальности деловых отношений.</p>
          <h2>7. Как отозвать согласие</h2>
          <p>Пользователь может отозвать согласие, обратившись в техподдержку бота.</p>
          <p class="muted">© 2025 Karma System. Все права защищены.</p>
        </div>
      </div>
    </div>
  </body>
 </html>
"""


@app.api_route("/policy", methods=["GET", "HEAD", "OPTIONS"], response_class=HTMLResponse)
async def policy_page():
    return _html(_POLICY_HTML)

# --- FAQ page (/faq)
_FAQ_HTML = """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>FAQ — Karma System</title>
    <style>
      body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0b1020;color:#e5e7eb}
      .page{max-width:900px;margin:0 auto;padding:24px}
      .card{background:#0f172a;border:1px solid #1f2937;border-radius:14px;padding:20px}
      h1{margin:0 0 8px 0;font-size:22px}
      .muted{color:#94a3b8}
      ul{margin:8px 0 8px 20px}
      li{margin:6px 0}
      a{color:#60a5fa;text-decoration:none}
      a:hover{text-decoration:underline}
    </style>
  </head>
  <body>
    <div class="page">
      <div class="card">
        <h1>❓ FAQ</h1>
        <div class="muted">Краткие инструкции по использованию бота</div>
        <h2>Основное</h2>
        <ul>
          <li>Откройте бота в Telegram и нажмите «Главное меню».</li>
          <li>Выберите раздел: Категории, Рядом, По районам, Личный кабинет.</li>
          <li>Язык меняется через пункт «Язык».</li>
        </ul>
        <h2>Партнёрам</h2>
        <ul>
          <li>Добавьте свою компанию: используйте пункт «Стать партнёром» в /help.</li>
        </ul>
        <h2>Поддержка</h2>
        <ul>
          <li><a href="https://t.me/karma_system_official">Написать администратору</a></li>
          <li><a href="/policy">Политика конфиденциальности</a></li>
        </ul>
      </div>
    </div>
  </body>
</html>
"""


@app.get("/faq", response_class=HTMLResponse)
async def faq_page():
    return _html(_FAQ_HTML)


# --- Partner Cabinet: Cards UI (/cabinet/partner/cards)
_PARTNER_CARDS_HTML = """
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Мои карточки — Karma System</title>
    <style>
      body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#0b1020;color:#e5e7eb}
      .page{max-width:1100px;margin:0 auto;padding:24px}
      .card{background:#0f172a;border:1px solid #1f2937;border-radius:14px;padding:20px}
      h1{margin:0 0 14px 0;font-size:22px}
      .page .card .row > .controls{display:flex;gap:8px;align-items:center;justify-content:flex-end;position:relative}
      #q{width:180px}
      #btnSearch, #btnAreaFilter { font-weight:500 }
      .controls-add{display:flex;justify-content:flex-end;margin-top:8px}
      input[type="text"]{background:#0b1020;border:1px solid #334155;border-radius:10px;padding:10px 12px;color:#e5e7eb;min-width:220px}
      button{background:#475569;border:0;color:white;border-radius:10px;padding:10px 14px;cursor:pointer}
      button.secondary{background:#334155}
      button:disabled{opacity:.5;cursor:not-allowed}
      table{width:100%;border-collapse:collapse;margin-top:14px}
      th,td{padding:10px;border-bottom:1px solid #1f2937;text-align:left}
      .badge{display:inline-block;padding:2px 8px;border-radius:999px;font-size:12px}
      .muted{color:#94a3b8}
      .status-pending{background:#7c2d12;color:#fde68a}
      .status-approved{background:#065f46;color:#bbf7d0}
      .status-archived{background:#374151;color:#e5e7eb}
      .status-rejected{background:#7f1d1d;color:#fecaca}
      /* filter popover */
      .lbl { color: #94a3b8; font-size:10px; margin-right:4px }
      .xs { padding:6px 10px !important; border-radius:8px !important; font-size:12px !important; line-height:1.2 }
      .xs-slim { padding:4px 6px !important; border-radius:8px !important; font-size:11px !important; line-height:1.1 }
      select.xs, input.xs { background:#0b1020; border:1px solid #334155; color:#e5e7eb }
      .filter-popover { position:absolute; left:0; top: calc(100% + 6px); background:#0b1327; border:1px solid #334155; border-radius:10px; padding:10px; box-shadow: 0 8px 24px rgba(0,0,0,0.35); width: 280px; max-height: 2cm; overflow:auto; display:none; z-index: 1000 }
      .filter-popover .row { display:grid; grid-template-columns:auto 1fr; column-gap:8px; row-gap:6px; align-items:center }
      /* Prevent controls inside popover from stretching full width */
      .filter-popover select,
      .filter-popover input { width:100% !important; min-width:0; box-sizing:border-box }
      .filter-actions { display:flex; gap:8px; justify-content:flex-end; margin-top:5mm }
      /* End filter popover */
      /* preview modal */
      #previewModal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.6);z-index:1500}
      #previewModal .panel{width:420px;max-width:95%;background:#0f172a;border:1px solid #1f2937;border-radius:14px;padding:16px;box-sizing:border-box}
      .bot-card{background:#0b1327;border:1px solid #334155;border-radius:12px;padding:12px}
      .bot-card .title{font-size:16px;font-weight:600;margin-bottom:6px}
      .bot-card .meta{font-size:12px;color:#94a3b8;margin-bottom:8px}
      .bot-card .desc{font-size:13px;color:#e5e7eb;margin-bottom:10px}
      .bot-card .thumbs{display:flex;gap:6px;flex-wrap:wrap}
      .bot-card .thumbs img{width:96px;height:96px;object-fit:cover;border-radius:8px;border:1px solid #334155}
      /* gallery items in editor */
      .gallery{display:flex;gap:8px;flex-wrap:wrap}
      .gallery .gitem{display:flex;flex-direction:column;align-items:center}
      .gallery .gitem img{width:96px;height:96px;object-fit:cover;border-radius:8px;border:1px solid #334155;cursor:pointer}
      .gallery .gitem button{margin-top:6px}
      /* modal */
      .modal{position:fixed;inset:0;display:none;align-items:center;justify-content:center;background:rgba(0,0,0,.5)}
      .modal .panel{width:640px;max-width:95%;background:#0f172a;border:1px solid #1f2937;border-radius:14px;padding:16px;box-sizing:border-box}
      .grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start}
      .grid .full{grid-column:1/-1}
      label{font-size:12px;color:#94a3b8;margin-bottom:4px;display:block}
      .field{margin-bottom:10px}
      select, input[type="tel"], input[type="url"], textarea, input[type="text"]{width:100%;max-width:100%;background:#0b1020;border:1px solid #334155;border-radius:10px;padding:10px 12px;color:#e5e7eb;box-sizing:border-box}
      textarea{min-height:100px;resize:vertical}
      /* inline validation */
      .field.invalid select,
      .field.invalid input,
      .field.invalid textarea{border-color:#dc2626; box-shadow:0 0 0 1px #dc2626 inset}
      .error-text{display:none;color:#fca5a5;font-size:12px;margin-top:4px}
      .field.invalid .error-text{display:block}
      /* gallery */
      .gal{margin-top:14px;border-top:1px solid #1f2937;padding-top:12px}
      .gal .row{align-items:flex-start}
      .gal input[type="file"]{background:#0b1020;border:1px solid #334155;border-radius:10px;padding:8px;color:#e5e7eb}
      .previews{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
      .previews .ph{width:64px;height:64px;border:1px solid #334155;border-radius:8px;overflow:hidden;background:#0b1020;display:flex;align-items:center;justify-content:center}
      .previews .ph img{width:100%;height:100%;object-fit:cover}
      .gallery{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
      .gallery .item{position:relative}
      .gallery .item img{width:96px;height:96px;border-radius:10px;object-fit:cover;border:1px solid #334155;display:block}
      .gallery .item button{position:absolute;top:4px;right:4px;background:#ef4444}
    </style>
  </head>
  <body>
    <div class="page">
      <div class="card">
        <div class="row">
          <h1>Мои карточки <span style="font-size:12px;color:#94a3b8">UI v0.3</span></h1>
          <div class="spacer"></div>
          <div class="controls">
            <input id="q" class="xs" type="text" placeholder="Поиск" />
            <button id="btnSearch" class="xs">Поиск</button>
            <button id="btnAreaFilter" class="xs" aria-expanded="false">Фильтр</button>
            <div id="filterPanel" class="filter-popover" aria-hidden="true">
              <div style="font-size:12px;color:#94a3b8;margin-bottom:6px">Фильтр по локации</div>
              <div class="row">
                <span class="lbl">Город</span>
                <select id="h_city" class="xs"></select>
                <span class="lbl">Район</span>
                <select id="h_area" class="xs"></select>
              </div>
              <div class="filter-actions">
                <button id="btnApplyFilter" class="xs">Применить</button>
              </div>
            </div>
          </div>
          <div class="controls-add">
            <button id="btnAdd">Добавить</button>
          </div>
        </div>
        <div id="state" class="muted" style="margin-top:8px"></div>
        <table id="tbl">
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Статус</th>
              <th>Создано</th>
              <th>Изменено</th>
              <th></th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
        <div style="margin-top:10px" class="row">
          <div class="spacer"></div>
          <button id="btnMore" class="secondary">Показать ещё</button>
        </div>
      </div>
    </div>

    <div id="modal" class="modal">
      <div class="panel">
        <h2 style="margin:0 0 10px 0;font-size:18px">Создать / Редактировать карточку</h2>
        <div class="grid">
          <div class="field">
            <label>Категория</label>
            <select id="f_category"></select>
            <div class="error-text" id="e_category"></div>
          </div>
          <div class="field">
            <label>Подкатегория</label>
            <select id="f_subcategory"></select>
            <div class="error-text" id="e_subcategory"></div>
          </div>
          <div class="field">
            <label>Название</label>
            <input id="f_title" type="text" maxlength="120" />
            <div class="error-text" id="e_title"></div>
          </div>
          <div class="field">
            <label>Город</label>
            <select id="f_city"></select>
            <div class="error-text" id="e_city"></div>
          </div>
          <div class="field">
            <label>Район</label>
            <select id="f_area"></select>
            <div class="error-text" id="e_area"></div>
          </div>
          <div class="field full">
            <label>Описание</label>
            <textarea id="f_description" maxlength="2000"></textarea>
            <div class="error-text" id="e_description"></div>
          </div>
          <div class="field">
            <label>Адрес</label>
            <input id="f_address" type="text" maxlength="300" />
            <div class="error-text" id="e_address"></div>
          </div>
          <div class="field">
            <label>Телефон</label>
            <input id="f_phone" type="tel" maxlength="20" />
            <div class="error-text" id="e_phone"></div>
          </div>
          <div class="field">
            <label>Google Maps URL</label>
            <input id="f_gmaps" type="url" maxlength="500" />
            <div class="error-text" id="e_gmaps"></div>
          </div>
          <div class="field">
            <label>Скидка/бонус</label>
            <input id="f_discount" type="text" maxlength="200" />
            <div class="error-text" id="e_discount"></div>
          </div>
        </div>
        <div class="gal">
          <div class="row">
            <div>
              <label style="display:block;margin-bottom:6px">Фотогалерея</label>
              <input id="f_images_input" type="file" accept="image/*" multiple />
              <div id="f_images_preview" class="previews"></div>
              <div style="margin-top:8px">
                <button id="f_images_upload_btn" class="xs">Загрузить выбранные</button>
                <span class="muted" id="f_images_hint">Доступно после сохранения/при редактировании карточки</span>
              </div>
            </div>
          </div>
          <div id="f_gallery_list" class="gallery"></div>
        </div>
        <div class="row" style="margin-top:10px">
          <button id="btnDeleteRequest" class="secondary" title="Отправить заявку на удаление карточки">Удалить</button>
          <div id="deleteStatus" class="muted" style="margin-left:8px"></div>
        </div>
        <div class="row" style="margin-top:10px">
          <div class="spacer"></div>
          <button id="btnCancel" class="secondary">Отмена</button>
          <button id="btnPreview" class="secondary">Предпросмотр</button>
          <button id="btnSave">Сохранить</button>
        </div>
      </div>
    </div>

    <!-- Bot-like preview modal -->
    <div id="previewModal">
      <div class="panel">
        <div class="bot-card">
          <div class="title" id="pv_title"></div>
          <div class="meta" id="pv_meta"></div>
          <div class="desc" id="pv_desc"></div>
          <div class="thumbs" id="pv_imgs"></div>
        </div>
        <div class="row" style="margin-top:10px;justify-content:flex-end">
          <button id="btnPreviewClose" class="secondary">Закрыть</button>
        </div>
      </div>
    </div>

    <script>
      const $ = (sel) => document.querySelector(sel);
      const tokenFromQuery = new URLSearchParams(location.search).get('token');
      if (tokenFromQuery) localStorage.setItem('partner_jwt', tokenFromQuery);
      // Support both keys: 'partner_jwt' (primary) and 'authToken' (fallback for convenience)
      const token = tokenFromQuery
        || localStorage.getItem('partner_jwt')
        || localStorage.getItem('authToken')
        || '';
      // Dynamic API base: if opened directly on API port (8001/8002) → same-origin.
      // Otherwise (preview/other port) → probe 8001 then 8002.
      let apiBase = '';
      let categoriesFromApi = true;
      async function initApiBase(){
        if (location.hostname === '127.0.0.1' && (location.port === '8001' || location.port === '8002')){
          apiBase = '';
          console.log('CabinetUI apiBase = same-origin', location.origin);
          return;
        }
        for (const p of ['8001','8002']){
          try {
            const r = await fetch(`http://127.0.0.1:${p}/cabinet/partner/categories`, { headers: { 'Authorization': `Bearer ${token}` }});
            if (r && (r.ok || r.status === 401 || r.status === 403)){
              apiBase = `http://127.0.0.1:${p}`;
              console.log('CabinetUI apiBase =', apiBase);
              return;
            }
          } catch(_){}
        }
        apiBase = '';
        console.log('CabinetUI apiBase fallback = same-origin', location.origin);
      }
      if (!token){
        try {
          const pasted = window.prompt('Нет токена. Вставьте сюда JWT (или откройте страницу со ссылкой ?token=...)');
          if (pasted && pasted.trim().length > 0){
            localStorage.setItem('partner_jwt', pasted.trim());
            location.reload();
          } else {
            alert('Токен не задан. Откройте страницу со ссылкой ?token=... или вставьте JWT в появившееся окно.');
          }
        } catch(_) {
          alert('Нет токена. Откройте страницу со ссылкой ?token=...');
        }
      }
      const stateEl = $('#state');
      const tbody = $('#tbl tbody');
      const btnMore = $('#btnMore');
      const btnSearch = $('#btnSearch');
      const btnAreaFilter = $('#btnAreaFilter');
      const filterPanel = $('#filterPanel');
      const btnApplyFilter = $('#btnApplyFilter');
      const h = { city: $('#h_city'), area: $('#h_area') };
      const inputQ = $('#q');
      let afterId = null;
      let lastItems = [];
      // Keep an ID → row map across pages so Edit works even after pagination/filtering
      const lastById = new Map();
      // Track already rendered IDs to avoid duplicate rows on keyset pagination
      const renderedIds = new Set();

      const statusMap = (row) => {
        const s = row.status;
        if (s === 'pending') return {text:'На модерации', cls:'status-pending'};
        if (s === 'approved') return {text: (row.status === 'approved' ? 'Активная' : 'Активная'), cls:'status-approved'};
        if (s === 'archived') return {text:'Скрытая', cls:'status-archived'};
        if (s === 'rejected') return {text:'Отклонена', cls:'status-rejected'};
        return {text:s, cls:'status-archived'};
      };

      function fmtDate(ts){ return ts || '—'; }

      function rowActions(row){
        const canEdit = true; // owner
        const canToggle = true;
        const actions = [];
        if (canEdit) actions.push(`<button class="secondary" data-act="edit" data-id="${row.id}">Редактировать</button>`);
        if (canToggle && row.status === 'approved') actions.push(`<button class="secondary" data-act="hide" data-id="${row.id}">Скрыть</button>`);
        if (canToggle && row.status === 'archived') actions.push(`<button class="secondary" data-act="unhide" data-id="${row.id}">Показать</button>`);
        // QR: доступно только для approved & !hidden
        if (row.status === 'approved') actions.push(`<button class="secondary" disabled data-id="${row.id}">Создать QR</button>`);
        return actions.join(' ');
      }

      function applyHeaderFilter(items){
        try{
          const selectedCity = h.city && h.city.value ? Number(h.city.value) : 0;
          const selectedArea = h.area && h.area.value ? Number(h.area.value) : 0;
          if (!selectedCity && !selectedArea) return items;
          return items.filter(row => {
            if (selectedCity && typeof row.city_id === 'number' && row.city_id !== selectedCity) return false;
            if (selectedArea && typeof row.area_id === 'number' && row.area_id !== selectedArea) return false;
            return true;
          });
        }catch(_){ return items; }
      }

      async function load(reset=false){
        if (reset){ tbody.innerHTML=''; afterId=null; lastById.clear(); renderedIds.clear(); }
        stateEl.textContent = 'Загрузка...';
        const params = new URLSearchParams();
        if (inputQ.value) params.set('q', inputQ.value);
        if (afterId) params.set('after_id', afterId);
        params.set('limit', '20');
        const url = `${apiBase}/cabinet/partner/cards?${params.toString()}`;
        // sanitize token for header
        const at = (token || '').replace(/[^\x20-\x7E]/g, '');
        let res = await fetch(url, { headers: { 'Authorization': `Bearer ${at}` } });
        if (!res.ok){
          // fallback with query token
          res = await fetch(url + `&token=${encodeURIComponent(token||'')}`);
        }
        if (!res.ok){ stateEl.textContent = 'Ошибка загрузки'; return; }
        const data = await res.json();
        const items = data.items || [];
        lastItems = items;
        // Update ID map with the latest batch
        items.forEach(it => lastById.set(String(it.id), it));
        if (items.length === 0 && !tbody.children.length) stateEl.textContent = 'Пусто. Нажмите «Добавить карточку».';
        else stateEl.textContent = '';
        const toRender = applyHeaderFilter(items);
        toRender.forEach(row => {
          // Skip if this id already rendered earlier (dedupe across pages)
          if (renderedIds.has(String(row.id))) return;
          const st = statusMap(row);
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${row.id}</td>
            <td>${row.title || '—'}</td>
            <td><span class="badge ${st.cls}">${st.text}</span></td>
            <td>${fmtDate(row.created_at)}</td>
            <td>${fmtDate(row.updated_at)}</td>
            <td>${rowActions(row)}</td>
          `;
          tbody.appendChild(tr);
          renderedIds.add(String(row.id));
        });
        if (items.length){ afterId = items[items.length-1].id; }
      }

      async function headerLoadCities(){
        try{
          const res = await fetch(`${apiBase}/cabinet/partner/cities`, { headers: { 'Authorization': `Bearer ${token}` }});
          if (!res.ok){ if (h.city) h.city.innerHTML=''; return; }
          const items = await res.json();
          if (!Array.isArray(items) || !items.length){ if (h.city) h.city.innerHTML=''; return; }
          if (h.city) h.city.innerHTML = items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
          // Default to Nha Trang (1)
          if (h.city && !h.city.value){ h.city.value = '1'; }
          await headerLoadAreas(Number(h.city && h.city.value ? h.city.value : 0));
        }catch(_){ if (h.city) h.city.innerHTML=''; }
      }

      async function headerLoadAreas(cityId){
        if (!cityId){ if (h.area) h.area.innerHTML=''; return; }
        try{
          const res = await fetch(`${apiBase}/cabinet/partner/areas?city_id=${encodeURIComponent(cityId)}`, { headers: { 'Authorization': `Bearer ${token}` }});
          if (!res.ok){ if (h.area) h.area.innerHTML=''; return; }
          const items = await res.json();
          if (!Array.isArray(items) || !items.length){ if (h.area) h.area.innerHTML=''; return; }
          if (h.area) h.area.innerHTML = '<option value="">— Все районы —</option>' + items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
        }catch(_){ if (h.area) h.area.innerHTML=''; }
      }

      // Modal logic
      const modal = $('#modal');
      const f = {
        category: $('#f_category'),
        subcategory: $('#f_subcategory'),
        title: $('#f_title'),
        city: $('#f_city'),
        area: $('#f_area'),
        description: $('#f_description'),
        address: $('#f_address'),
        phone: $('#f_phone'),
        gmaps: $('#f_gmaps'),
        discount: $('#f_discount'),
      };
      const fe = {
        category: $('#e_category'),
        subcategory: $('#e_subcategory'),
        title: $('#e_title'),
        city: $('#e_city'),
        area: $('#e_area'),
        description: $('#e_description'),
        address: $('#e_address'),
        phone: $('#e_phone'),
        gmaps: $('#e_gmaps'),
        discount: $('#e_discount'),
      };
      let editingId = null;
      let existingImages = [];
      function openModal(row=null){
        editingId = row ? row.id : null;
        // Ensure category select has options immediately
        if (!f.category.options.length){
          f.category.innerHTML = '<option value="1">Рестораны</option><option value="2">SPA и массаж</option><option value="3">Аренда байков</option><option value="4">Отели</option><option value="5">Экскурсии</option>';
        }
        f.category.value = row?.category_id || f.category.value || '';
        if (!f.category.value && f.category.options.length){ f.category.selectedIndex = 0; }
        // reset subcategory and city
        f.subcategory.innerHTML = '';
        f.city.innerHTML = '';
        f.area.innerHTML = '';
        f.title.value = row?.title || '';
        f.description.value = row?.description || '';
        f.address.value = row?.address || '';
        f.phone.value = row?.contact || '';
        f.gmaps.value = row?.google_maps_url || '';
        f.discount.value = row?.discount_text || '';
        clearErrors();
        modal.style.display = 'flex';
        // Gallery init
        existingImages = [];
        $('#f_images_preview').innerHTML = '';
        $('#f_gallery_list').innerHTML = '';
        const imgInput = $('#f_images_input');
        const uploadBtn = $('#f_images_upload_btn');
        const hint = $('#f_images_hint');
        if (editingId){
          imgInput.disabled = false;
          uploadBtn.disabled = false;
          hint.textContent = '';
          // Load existing images
          fetch(`${apiBase}/cabinet/partner/cards/${editingId}/images`, { headers:{'Authorization':`Bearer ${token}`} })
            .then(r=> r.ok ? r.json(): [])
            .then(list=>{ existingImages = Array.isArray(list)? list: []; renderGallery(); })
            .catch(()=>{});
        } else {
          imgInput.disabled = false; // позволим выбрать, но предупредим при загрузке
          uploadBtn.disabled = false;
          hint.textContent = 'Фото привяжутся после сохранения карточки';
        }
        // Refresh categories from API in background, then load subcats and cities
        loadCategories()
          .then(()=> loadSubcategories(Number(f.category.value||0)))
          .then(()=> { if (row && row.subcategory_id) { f.subcategory.value = String(row.subcategory_id); } })
          .catch(()=>{})
          .finally(()=> {
            loadCities()
              .then(async ()=>{
                if (row && row.city_id) { f.city.value = String(row.city_id); }
                await loadAreas(Number(f.city.value||0));
                if (row && row.area_id) { f.area.value = String(row.area_id); }
              })
              .catch(()=>{});
          });
      }
      function closeModal(){ modal.style.display = 'none'; }

      function renderGallery(){
        const wrap = $('#f_gallery_list');
        wrap.innerHTML = existingImages.map(x=>`<div class="gitem"><img src="${x.url}" alt="" data-full="${x.url}"/><button class="secondary" data-del="${x.id}">Удалить</button></div>`).join('');
      }

      // Handle local previews before upload
      $('#f_images_input').addEventListener('change', (e)=>{
        const files = Array.from(e.target.files || []);
        const left = 6 - existingImages.length;
        const toUse = left > 0 ? files.slice(0, left) : [];
        if (files.length > toUse.length){ alert('Можно максимум 6 фото на карточку'); }
        const prev = $('#f_images_preview');
        prev.innerHTML = '';
        toUse.forEach(f=>{
          const reader = new FileReader();
          reader.onload = ()=>{
            const img = document.createElement('img');
            img.src = reader.result;
            img.style.width = '96px'; img.style.height='96px'; img.style.objectFit='cover'; img.style.borderRadius='8px'; img.style.border='1px solid #334155'; img.style.marginRight='6px';
            img.style.cursor = 'pointer'; img.setAttribute('data-full', reader.result);
            prev.appendChild(img);
          };
          reader.readAsDataURL(f);
        });
      });

      // Upload selected images (max 5 total)
      $('#f_images_upload_btn').addEventListener('click', async ()=>{
        if (!editingId){ alert('Сначала сохраните карточку'); return; }
        const input = $('#f_images_input');
        const files = Array.from(input.files || []);
        if (!files.length){ alert('Выберите фото'); return; }
        const left = 6 - existingImages.length;
        if (left <= 0){ alert('Достигнут лимит 6 фото'); return; }
        const toSend = files.slice(0, left);
        const fd = new FormData();
        toSend.forEach(f=> fd.append('files', f));
        const res = await fetch(`${apiBase}/cabinet/partner/cards/${editingId}/images`, { method:'POST', headers:{ 'Authorization':`Bearer ${token}` }, body: fd });
        if (!res.ok){ alert('Не удалось загрузить фото'); return; }
        const list = await res.json();
        existingImages = existingImages.concat(list);
        renderGallery();
        $('#f_images_preview').innerHTML = '';
        input.value = '';
      });

      // Delete image
      $('#f_gallery_list').addEventListener('click', async (e)=>{
        const t = e.target;
        if (!(t instanceof HTMLElement)) return;
        const id = t.getAttribute('data-del');
        if (!id) return;
        if (!confirm('Удалить фото?')) return;
        const res = await fetch(`${apiBase}/cabinet/partner/cards/${editingId}/images/${id}`, { method:'DELETE', headers:{'Authorization':`Bearer ${token}`} });
        if (!res.ok){ alert('Не удалось удалить'); return; }
        existingImages = existingImages.filter(x=> String(x.id) !== String(id));
        renderGallery();
      });

      // Preview modal
      const pv = { wrap: $('#previewModal'), title: $('#pv_title'), meta: $('#pv_meta'), desc: $('#pv_desc'), imgs: $('#pv_imgs') };
      function openPreview(){
        pv.title.textContent = (f.title.value || 'Без названия');
        const cityTxt = f.city.options[f.city.selectedIndex]?.textContent || '';
        const areaTxt = f.area.options[f.area.selectedIndex]?.textContent || '';
        const catTxt = f.category.options[f.category.selectedIndex]?.textContent || '';
        const subTxt = f.subcategory.options[f.subcategory.selectedIndex]?.textContent || '';
        const parts = [catTxt, subTxt, cityTxt, areaTxt].filter(Boolean);
        pv.meta.textContent = parts.join(' • ');
        pv.desc.textContent = f.discount.value ? (f.discount.value + ' • ') + (f.description.value || '') : (f.description.value || '');
        pv.imgs.innerHTML = '';
        // combine existing images and new previews
        existingImages.slice(0,6).forEach(x=>{
          const im = document.createElement('img'); im.src = x.url; pv.imgs.appendChild(im);
        });
        const localPrev = $('#f_images_preview').querySelectorAll('img');
        localPrev.forEach((img)=>{ if (pv.imgs.children.length < 6){ const im = document.createElement('img'); im.src = img.src; pv.imgs.appendChild(im); } });
        pv.wrap.style.display = 'flex';
      }
      function closePreview(){ pv.wrap.style.display = 'none'; }

      function validPhone(p){ return /^\+\d{7,15}$/.test(p||''); }
      function validGmaps(u){ return !u || /^https?:\/\/(maps\.app\.goo\.gl|goo\.gl\/maps|www\.google\.com\/maps)/.test(u); }

      async function loadCategories(){
        const res = await fetch(`${apiBase}/cabinet/partner/categories`, { headers: { 'Authorization': `Bearer ${token}` }});
        if (!res.ok){
          // Fallback: simple static list if categories not available
          categoriesFromApi = false;
          f.category.innerHTML = '<option value="1">Рестораны</option><option value="2">SPA и массаж</option><option value="3">Аренда байков</option><option value="4">Отели</option><option value="5">Экскурсии</option>';
          // auto-select first
          f.category.value = '1';
          return;
        }
        categoriesFromApi = true;
        const items = await res.json();
        if (!items.length){
          f.category.innerHTML = '<option value="" disabled selected>Нет категорий</option>';
        } else {
          f.category.innerHTML = items.map(i => `<option value="${i.id}">${i.emoji ? i.emoji + ' ' : ''}${i.name}</option>`).join('');
          // auto-select first option to avoid empty value
          f.category.selectedIndex = 0;
        }
      }

      async function loadSubcategories(categoryId){
        if (!categoryId){ f.subcategory.innerHTML=''; return; }
        try{
          const res = await fetch(`${apiBase}/cabinet/partner/subcategories?category_id=${encodeURIComponent(categoryId)}`, { headers: { 'Authorization': `Bearer ${token}` }});
          if (!res.ok){
            // Local fallback when categories not from API
            if (!categoriesFromApi){
              const name = (f.category.options[f.category.selectedIndex]?.textContent || '').toLowerCase();
              let opts = '';
              if (name.includes('spa') || name.includes('спа') || name.includes('массаж')){
                opts = '<option value="">— Не выбрано —</option>'+
                  '<option value="401">Спа-салоны</option>'+
                  '<option value="402">Массаж</option>'+
                  '<option value="403">Бани/сауны</option>';
              } else if (name.includes('экскурс')){
                opts = '<option value="">— Не выбрано —</option>'+
                  '<option value="301">Групповые</option>'+
                  '<option value="302">Индивидуальные</option>';
              } else if (name.includes('аренда') || name.includes('байк') || name.includes('скутер') || name.includes('транспорт') || name.includes('авто')){
                opts = '<option value="">— Не выбрано —</option>'+
                  '<option value="201">Авто</option>'+
                  '<option value="202">Байки/скутеры</option>'+
                  '<option value="203">Велосипеды</option>';
              } else if (name.includes('рестора') || name.includes('каф')){
                opts = '<option value="">— Не выбрано —</option>'+
                  '<option value="101">Европейская кухня</option>'+
                  '<option value="102">Азиатская кухня</option>'+
                  '<option value="103">Грузинская кухня</option>'+
                  '<option value="104">Итальянская кухня</option>';
              }
              f.subcategory.innerHTML = opts; return;
            }
            f.subcategory.innerHTML=''; return;
          }
          const items = await res.json();
          if (!Array.isArray(items) || !items.length){ f.subcategory.innerHTML=''; return; }
          f.subcategory.innerHTML = '<option value="">— Не выбрано —</option>' + items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
        }catch(_){ f.subcategory.innerHTML=''; }
      }

      async function loadCities(){
        try{
          const res = await fetch(`${apiBase}/cabinet/partner/cities`, { headers: { 'Authorization': `Bearer ${token}` }});
          if (!res.ok){ f.city.innerHTML=''; return; }
          const items = await res.json();
          if (!Array.isArray(items) || !items.length){ f.city.innerHTML=''; return; }
          f.city.innerHTML = items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
          // Город по умолчанию — Нячанг (id=1)
          if (!f.city.value){ f.city.value = '1'; }
          // После выбора города — загрузить районы
          await loadAreas(Number(f.city.value||0));
        }catch(_){ f.city.innerHTML=''; }
      }

      async function loadAreas(cityId){
        if (!cityId){ f.area.innerHTML=''; return; }
        try{
          const res = await fetch(`${apiBase}/cabinet/partner/areas?city_id=${encodeURIComponent(cityId)}`, { headers: { 'Authorization': `Bearer ${token}` }});
          if (!res.ok){ f.area.innerHTML=''; return; }
          const items = await res.json();
          if (!Array.isArray(items) || !items.length){ f.area.innerHTML=''; return; }
          f.area.innerHTML = '<option value="">— Не выбрано —</option>' + items.map(i => `<option value="${i.id}">${i.name}</option>`).join('');
        }catch(_){ f.area.innerHTML=''; }
      }

      function setError(fieldKey, message){
        const el = f[fieldKey];
        const wrap = el.closest('.field');
        if (wrap){ wrap.classList.add('invalid'); }
        if (fe[fieldKey]) fe[fieldKey].textContent = message || '';
      }
      function clearErrors(){
        document.querySelectorAll('.field.invalid').forEach(x=>x.classList.remove('invalid'));
        Object.values(fe).forEach(e => e && (e.textContent = ''));
      }
      // clear on input
      Object.entries(f).forEach(([k,el])=>{
        el.addEventListener('input', ()=>{
          const wrap = el.closest('.field');
          if (wrap) wrap.classList.remove('invalid');
          if (fe[k]) fe[k].textContent = '';
        });
        el.addEventListener('change', ()=>{
          const wrap = el.closest('.field');
          if (wrap) wrap.classList.remove('invalid');
          if (fe[k]) fe[k].textContent = '';
        });
      });

      async function save(){
        clearErrors();
        const payload = {
          category_id: Number(f.category.value||0),
          subcategory_id: f.subcategory && f.subcategory.value ? Number(f.subcategory.value) : null,
          city_id: f.city && f.city.value ? Number(f.city.value) : null,
          area_id: f.area && f.area.value ? Number(f.area.value) : null,
          title: f.title.value.trim(),
          description: f.description.value.trim()||null,
          address: f.address.value.trim()||null,
          contact: f.phone.value.trim()||null,
          google_maps_url: f.gmaps.value.trim()||null,
          discount_text: f.discount.value.trim()||null,
        };
        let hasErr = false;
        if (!payload.category_id){ setError('category', 'Выберите категорию'); hasErr = true; }
        if (!payload.title){ setError('title', 'Введите название'); hasErr = true; }
        if (!payload.city_id){ setError('city', 'Выберите город'); hasErr = true; }
        if (payload.contact && !validPhone(payload.contact)){ setError('phone', 'Телефон в формате +E.164'); hasErr = true; }
        if (!validGmaps(payload.google_maps_url)){ setError('gmaps', 'Некорректный Google Maps URL'); hasErr = true; }
        if (hasErr) return;
        const url = editingId ? `${apiBase}/cabinet/partner/cards/${editingId}` : `${apiBase}/cabinet/partner/cards`;
        const method = editingId ? 'PATCH' : 'POST';
        const res = await fetch(url, {
          method,
          headers: { 'Content-Type':'application/json', 'Authorization':`Bearer ${token}` },
          body: JSON.stringify(payload)
        });
        if (!res.ok){
          // Try show server error message
          try { const err = await res.json(); alert(err.detail || 'Ошибка сохранения'); }
          catch { alert('Ошибка сохранения'); }
          return;
        }
        closeModal();
        await load(true);
      }

      // Event handlers
      btnMore.addEventListener('click', ()=> load(false));
      btnSearch.addEventListener('click', ()=> load(true));
      btnAreaFilter.addEventListener('click', (e)=> {
        e.stopPropagation();
        const open = filterPanel.style.display === 'block';
        if (open) {
          filterPanel.style.display = 'none';
          btnAreaFilter.setAttribute('aria-expanded', 'false');
          filterPanel.setAttribute('aria-hidden', 'true');
          const controls = btnAreaFilter.closest('.controls');
          if (controls) controls.classList.remove('filter-open');
          return;
        }
        // position under the button within the controls container
        const controls = btnAreaFilter.closest('.controls');
        const btnRect = btnAreaFilter.getBoundingClientRect();
        const ctrRect = controls.getBoundingClientRect();
        const left = (btnRect.left - ctrRect.left) | 0;
        const top = (btnRect.top - ctrRect.top + btnAreaFilter.offsetHeight + 6) | 0;
        filterPanel.style.left = left + 'px';
        filterPanel.style.top = top + 'px';
        // Enforce compact size inline to beat any external CSS
        filterPanel.style.width = '280px';
        filterPanel.style.maxHeight = '2cm';
        filterPanel.style.overflow = 'auto';
        filterPanel.style.display = 'block';
        btnAreaFilter.setAttribute('aria-expanded', 'true');
        filterPanel.setAttribute('aria-hidden', 'false');
        if (controls) controls.classList.add('filter-open');
      });
      btnApplyFilter.addEventListener('click', ()=> {
        // Re-render current page with applied filter
        const toRender = applyHeaderFilter(lastItems);
        tbody.innerHTML = '';
        toRender.forEach(row => {
          const st = statusMap(row);
          const tr = document.createElement('tr');
          tr.innerHTML = `<td>${row.id}</td><td>${row.title}</td><td><span class="badge ${st.cls}">${st.text}</span></td><td>${fmtDate(row.created_at)}</td><td>${fmtDate(row.updated_at)}</td><td>${rowActions(row)}</td>`;
          tbody.appendChild(tr);
        });
        // close panel
        filterPanel.style.display = 'none';
        btnAreaFilter.setAttribute('aria-expanded', 'false');
        filterPanel.setAttribute('aria-hidden', 'true');
        const controls = btnAreaFilter.closest('.controls');
        if (controls) controls.classList.remove('filter-open');
      });
      // Close on outside click
      document.addEventListener('click', (e)=>{
        if (!filterPanel) return;
        const isOpen = filterPanel.style.display === 'block';
        if (!isOpen) return;
        if (!filterPanel.contains(e.target) && e.target !== btnAreaFilter) {
          filterPanel.style.display = 'none';
          btnAreaFilter.setAttribute('aria-expanded', 'false');
          filterPanel.setAttribute('aria-hidden', 'true');
          const controls = btnAreaFilter.closest('.controls');
          if (controls) controls.classList.remove('filter-open');
        }
      });
      if (h.city) h.city.addEventListener('change', ()=> headerLoadAreas(Number(h.city.value||0)));
      $('#btnAdd').addEventListener('click', ()=> openModal(null));
      $('#btnCancel').addEventListener('click', closeModal);
      $('#btnPreview').addEventListener('click', openPreview);
      $('#btnPreviewClose').addEventListener('click', closePreview);
      $('#btnSave').addEventListener('click', save);
      // react to category change to reload subcategories
      f.category.addEventListener('change', ()=>{
        loadSubcategories(Number(f.category.value||0));
      });
      // react to city change to reload areas
      f.city.addEventListener('change', ()=>{
        loadAreas(Number(f.city.value||0));
      });
      tbody.addEventListener('click', async (e)=>{
        const t = e.target;
        if (!(t instanceof HTMLElement)) return;
        const act = t.getAttribute('data-act');
        const id = t.getAttribute('data-id');
        if (!act || !id) return;
        if (act === 'edit'){
          // Use cached data across all loaded pages
          const row = lastById.get(String(id));
          if (!row) { alert('Не удалось загрузить карточку'); return; }
          openModal(row);
        } else if (act === 'hide'){
          const res = await fetch(`${apiBase}/cabinet/partner/cards/${id}/hide`, { method:'POST', headers:{'Authorization':`Bearer ${token}`} });
          if (!res.ok){ alert('Не удалось скрыть'); return; }
          await load(true);
        } else if (act === 'unhide'){
          const res = await fetch(`${apiBase}/cabinet/partner/cards/${id}/unhide`, { method:'POST', headers:{'Authorization':`Bearer ${token}`} });
          if (!res.ok){ alert('Не удалось показать'); return; }
          await load(true);
        }
      });

      initApiBase().then(()=> Promise.all([headerLoadCities(), loadCategories()]).then(()=> load(true)));
    </script>
  </body>
</html>
"""
