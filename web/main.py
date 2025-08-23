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
INDEX_HTML = """
<!doctype html>
<html lang=\"ru\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>KARMABOT1 WebApp</title>
    <script src=\"https://telegram.org/js/telegram-web-app.js\"></script>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; }
      .card { max-width: 860px; margin: 0 auto; padding: 20px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fff; }
      .muted { color: #6b7280; }
      pre { background: #f9fafb; padding: 12px; border-radius: 8px; overflow: auto; }
      .error { color: #b91c1c; }
      .ok { color: #065f46; }
      button { padding: 10px 14px; border-radius: 8px; border: 1px solid #d1d5db; background: #111827; color: #fff; cursor: pointer; }
      .tabs { display:flex; gap:8px; margin: 14px 0; flex-wrap: wrap; }
      .tab { padding:8px 12px; border:1px solid #d1d5db; border-radius:8px; background:#f3f4f6; cursor:pointer; }
      .tab.active { background:#111827; color:#fff; border-color:#111827; }
      .section { display:none; }
      .section.active { display:block; }
      ul.clean { list-style:none; padding-left:0; }
      ul.clean li { padding:8px 0; border-bottom:1px dashed #e5e7eb; }
    </style>
  </head>
  <body>
    <div class=\"card\">
      <h1>KARMABOT1 WebApp</h1>
      <p class=\"muted\">Авторизация через Telegram initData → POST /auth/webapp → /auth/me</p>
      <div id=\"status\">Инициализация…</div>
      <div id=\"claims\" style=\"display:none\">
        <h3>Claims</h3>
        <pre id=\"claimsPre\"></pre>
      </div>
      <div style="margin-top:12px">
        <button id="retry" style="display:none">Повторить авторизацию</button>
      </div>
      <div id="tokenTools" style="margin-top:8px; display:none">
        <button id="showToken">Показать токен</button>
        <button id="copyToken" style="display:none">Копировать</button>
        <div id="tokenBox" class="muted" style="display:none; word-break:break-all; margin-top:6px"></div>
      </div>
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

          // Reveal token tools
          try {
            document.getElementById('tokenTools').style.display = 'block';
            const tb = document.getElementById('tokenBox');
            const copyBtn = document.getElementById('copyToken');
            const showBtn = document.getElementById('showToken');
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
          } catch (e) { /* no-op */ }

          const meResp = await fetch('/auth/me', { headers: { 'Authorization': 'Bearer ' + token } });
          const me = await meResp.json().catch(() => ({}));
          claimsPre.textContent = JSON.stringify(me, null, 2);
          claimsBox.style.display = 'block';
          s.innerHTML = '<span class="ok">Готово</span>';

          // Show cabinet sections and load data
          document.getElementById('cabinet').style.display = 'block';
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
      // If token already saved (повторный визит), покажем инструменты
      try {
        const saved = localStorage.getItem('jwt');
        if (saved) {
          document.getElementById('tokenTools').style.display = 'block';
          const tb = document.getElementById('tokenBox');
          const copyBtn = document.getElementById('copyToken');
          const showBtn = document.getElementById('showToken');
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
