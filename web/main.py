from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Import project settings and auth utils
try:
    from core.settings import settings
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
from .routes_cabinet import router as cabinet_router

# Middleware to add CSP header to responses
class CSPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        try:
            csp_origin = getattr(getattr(settings, 'web', None), 'csp_allowed_origin', None) or getattr(settings, 'CSP_ALLOWED_ORIGIN', None)
            if csp_origin:
                # Minimal CSP allowing our origin and inline for Telegram WebApp wrapper context if needed
                response.headers["Content-Security-Policy"] = f"default-src 'self' {csp_origin}; script-src 'self' {csp_origin} 'unsafe-inline'; connect-src 'self' {csp_origin}; style-src 'self' {csp_origin} 'unsafe-inline'; img-src 'self' data: {csp_origin}; frame-ancestors 'self' https://web.telegram.org https://telegram.org;"
        except Exception:
            pass
        return response

app = FastAPI(title="KARMABOT1 WebApp API")

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

# Routers
app.include_router(auth_router, prefix="/auth", tags=["auth"]) 
app.include_router(auth_email_router, prefix="/auth", tags=["auth"]) 
app.include_router(cabinet_router, prefix="/cabinet", tags=["cabinet"]) 

@app.get("/health")
async def health():
    return {"status": "ok"}


# Minimal WebApp landing page so WEBAPP_QR_URL can point to the root URL
import os as _os
_SHOW_DEBUG_UI = str(_os.getenv("SHOW_DEBUG_UI", "0")).strip() in ("1","true","yes","on")

INDEX_HTML = f"""
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
    </style>
  </head>
  <body>
    <div class=\"shell\">
      <div class=\"card\">
      <div class=\"toolbar\">
        <div class=\"title\">🪄 <span>KARMABOT1 WebApp</span></div>
        <div class=\"actions\">
          <button id=\"btnScanQR\" class=\"btn primary\" style=\"display:none\">🧾 Сканировать QR</button>
          <button id=\"openInBrowser\" class=\"btn ghost\">🌐 Открыть в браузере</button>
          <button id=\"toggleDetails\" class=\"btn ghost\">Показать детали</button>
          <button id=\"showToken\" class=\"btn ghost\">Показать токен</button>
          <button id=\"copyToken\" class=\"btn\" style=\"display:none\">Копировать</button>
        </div>
      </div>
      <div class=\"spacer\"></div>
      <p class=\"muted\">Авторизация через Telegram initData → POST /auth/webapp → /auth/me</p>
      <div id=\"status\">Инициализация…</div>
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
          <div class=\"tab\" data-tab=\"orders\">Заказы</div>
        </div>

        <div id=\"section-profile\" class=\"section active\">
          <h3>Профиль</h3>
          <div id=\"profileBox\" class=\"muted\">Загрузка…</div>
        </div>

        <div id=\"section-orders\" class=\"section\">
          <h3>Заказы</h3>
          <ul id=\"ordersList\" class=\"clean\"></ul>
          <div id=\"ordersEmpty\" class=\"muted\" style=\"display:none\">Нет заказов</div>
        </div>
      </div>
    </div>

    <script>
      const SHOW_DEBUG_UI = {str(_SHOW_DEBUG_UI).lower()};
      function selectTab(name) {
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.tab === name));
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        const el = document.getElementById('section-' + name);
        if (el) el.classList.add('active');
      }

      async function loadProfile(token) {
        const box = document.getElementById('profileBox');
        box.textContent = 'Загрузка…';
        try {
          const r = await fetch('/cabinet/profile', { headers: { 'Authorization': 'Bearer ' + token } });
          if (!r.ok) throw new Error('HTTP ' + r.status);
          const data = await r.json();
          box.textContent = `ID: ${data.user_id} · Язык: ${data.lang} · Источник: ${data.source}`;
        } catch (e) {
          box.textContent = 'Ошибка загрузки профиля: ' + (e.message || e);
        }
      }

      async function loadOrders(token) {
        const list = document.getElementById('ordersList');
        const empty = document.getElementById('ordersEmpty');
        list.innerHTML = '';
        empty.style.display = 'none';
        try {
          const r = await fetch('/cabinet/orders?limit=20', { headers: { 'Authorization': 'Bearer ' + token } });
          if (!r.ok) throw new Error('HTTP ' + r.status);
          const data = await r.json();
          const items = (data && data.items) || [];
          if (!items.length) {
            empty.style.display = 'block';
            return;
          }
          for (const it of items) {
            const li = document.createElement('li');
            li.textContent = `${it.title || it.id} — ${it.status || ''}`;
            list.appendChild(li);
          }
        } catch (e) {
          const li = document.createElement('li');
          li.textContent = 'Ошибка загрузки заказов: ' + (e.message || e);
          list.appendChild(li);
        }
      }

      async function authWithInitData() {
        const s = document.getElementById('status');
        const retry = document.getElementById('retry');
        const claimsBox = document.getElementById('claims');
        const claimsPre = document.getElementById('claimsPre');
        try {
          retry.style.display = 'none';
          claimsBox.style.display = 'none';
          s.textContent = 'Чтение initData из Telegram…';
          const initData = (window.Telegram && Telegram.WebApp && Telegram.WebApp.initData) || '';
          if (!initData) {
            s.innerHTML = '<span class="error">initData отсутствует. Откройте страницу из Telegram WebApp.</span>';
            retry.style.display = 'inline-block';
            return;
          }

          s.textContent = 'Отправка initData → /auth/webapp…';
          const resp = await fetch('/auth/webapp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ initData })
          });
          if (!resp.ok) {
            const text = await resp.text();
            s.innerHTML = `<span class="error">Ошибка авторизации (${resp.status}): ${text}</span>`;
            retry.style.display = 'inline-block';
            return;
          }
          const data = await resp.json();
          const token = data.token;
          if (!token) {
            s.innerHTML = '<span class="error">Сервер не вернул token</span>';
            retry.style.display = 'inline-block';
            return;
          }
          localStorage.setItem('jwt', token);
          s.innerHTML = '<span class="ok">Успешно. Запрашиваю /auth/me…</span>';

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
          claimsPre.textContent = JSON.stringify(me, null, 2);
          // Не показываем детали автоматически; доступны по кнопке
          s.innerHTML = '<span class="ok">Готово</span>';

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
          s.innerHTML = '<span class="error">' + (e && e.message ? e.message : e) + '</span>';
          retry.style.display = 'inline-block';
        }
      }
      document.getElementById('retry').addEventListener('click', authWithInitData);
      document.addEventListener('click', async (ev) => {
        const t = ev.target;
        if (t && t.classList && t.classList.contains('tab')) {
          const name = t.dataset.tab;
          selectTab(name);
          if (name === 'orders') {
            const token = localStorage.getItem('jwt');
            if (token) await loadOrders(token);
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
        const saved = localStorage.getItem('jwt');
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
      authWithInitData();
    </script>
  </body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
  return HTMLResponse(content=INDEX_HTML)


@app.get("/app", response_class=HTMLResponse)
async def app_page():
  return HTMLResponse(content=INDEX_HTML)
