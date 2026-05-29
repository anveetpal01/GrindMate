# GrindMate — Production Deployment Playbook

> Weekend-friendly, ₹0 budget, fresher-friendly. Pad ke ek baar samjh aane ke baad
> 4-6 ghante mein deploy ho jayega — agar pehli baar kar raha hai to ek pura
> Saturday rakh le, Sunday buffer ke liye chhod.

---

## 0. Pehle reality check

Sach yeh hai:

- **Free tier mein limits hain**, aur tujhe yeh accept karna hoga:
 - Backend pehli request pe **30 second cold start** lega (Render ki free service 15 min idle ke baad sleep ho jaati hai). Apne dost ko bata dena "first time slow hoga" — solve nahi karna isko.
 - **Celery worker free mein nahi milta**. Solution: GitHub Actions ka cron schedule har 6 ghante pe ek endpoint hit karega jo synchronously sab accounts ka sync karega. Ham yahi karenge — bilkul kaam karega, kuch missing nahi feel hoga.
 - **Custom domain (jaise grindmate.in) free mein nahi milta**. URL hoga `grindmate-api.onrender.com` aur `grindmate.vercel.app`. Domain chahiye to `.com` ~₹900/saal pe Namecheap / Porkbun se le sakta hai — par yeh **bilkul zaroori nahi hai abhi**.
 - **LeetCode ka unofficial GraphQL API kabhi-kabhi production IP block kar deta hai (Cloudflare)**. Ho sakta hai pehli baar sync na chale. Plan B: dashboard pe "manual mark solved" button hai — woh hamesha kaam karega. Yeh fragile dependency hai, bata diya hai dosto ko.

- **Yeh deploy kya prove karega:**
 - End-to-end stack chala lena (DB + API + frontend + cron + email + error tracking)
 - Resume pe likhne layak: "Deployed Django+React monorepo on Render+Vercel with managed Postgres, scheduled cron sync, Sentry monitoring."
 - Apne dost actually use kar payenge — woh sabse bada motivation hai.

- **Yeh deploy kya prove NAHI karega (aur uske liye stress mat le):**
 - Scale handling (1000+ users) — abhi 5-10 dosto ke liye bana hai
 - 99.9% uptime — free tier mein possible nahi
 - DDoS protection / WAF — overkill

**Mantra:** Deploy karo, dosto ko share karo, jo break ho fix karo. Pehle se perfect banane ki koshish mat karna.

---

## 1. Free-tier stack (kya use karenge aur kyun)

| Kya | Kya use karenge | Free tier limits | Kyun yeh |
|---------|----------------------|----------------------------------|--------------------------------------------|
| Backend host | **Render** | 1 web service, 512MB RAM, sleep after 15min idle | Sabse simple, GitHub se auto-deploy, render.yaml support |
| Postgres | **Neon** | 0.5GB storage, no expiry, branching | Generous free tier; sirf Postgres karta hai isliye solid hai |
| Cache / queue | **Skip Redis abhi** | — | Leaderboard cache LocMem se kaam chal jayega; Celery hata diya hai (cron use kar rahe hain) |
| Frontend host | **Vercel** | Unlimited deploys, 100GB bandwidth | React SPAs ke liye industry default; auto SSL, branch previews |
| Email | **Resend** | 100/day, 3000/month | Sabse easy signup, Django se SMTP via single env var |
| Cron / scheduler | **GitHub Actions** | Public repo: unlimited; private: 2000 min/month | Already ham GitHub use kar rahe hain — ek aur account banane se accha |
| Errors | **Sentry** (optional) | 5K events/month | Production mein kuch bhi break ho to email aa jayega |
| Source | **GitHub** | Unlimited public repos | obvious choice |

**Total cost: ₹0/month** jab tak users < 50. Custom domain optional hai (~₹900/saal).

---

## 2. Pre-deploy checklist (ek baar local pe karle)

Local pe sab kaam kar raha hai confirm:

```bash
# Backend
cd backend
source .venv/bin/activate
pytest # 60 tests pass hone chahiye
ruff check . # lint clean
python manage.py runserver # /health/ pe 200 OK

# Frontend (alag terminal)
cd frontend
npm run typecheck # TS clean
npm run lint # ESLint clean
npm run build # production bundle banta hai
```

Sab green hain? Phir aage.

### GitHub pe push kar de

```bash
cd /home/anveet/Documents/Grindmate
git add .
git commit -m "Initial GrindMate scaffold ready for deploy"
# GitHub pe ek public repo bana (grindmate naam de), phir:
git remote add origin git@github.com:<your-username>/grindmate.git
git push -u origin main
```

> **Public repo kyun?** Free GitHub Actions minutes unlimited milte hain public mein. Plus portfolio dikhane ke kaam aata hai. **Sensitive cheez (API keys, .env) push mat karna** — `.gitignore` already handle karta hai.

---

## 3. Step 1 — Database setup karo (Neon, ~10 min)

**Account banao:**
1. https://neon.tech → "Sign up with GitHub"
2. Project name: `grindmate`, region **Singapore** (India ke liye fastest free option)
3. Bana lo. Default database `neondb` chal jayega — alag se `grindmate` banane ki zaroorat nahi.

**Connection string copy karo:**
- Neon dashboard → **Connection Details**
- "Pooled connection" select karo (yeh important hai — non-pooled connection limit jaldi exhaust hoti hai)
- URI dikhega kuch aisa: `postgresql://neondb_owner:xxxxx@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
- Copy karo, kahin save kar lo — yeh tera **DATABASE_URL** hai

**Test karo (optional but recommended):**
```bash
# Local pe Postgres URL test karne ke liye:
cd backend
DATABASE_URL="<paste neon url>" .venv/bin/python manage.py migrate
```
Agar yeh chal gaya, perfect. Local SQLite vs prod Postgres ka koi difference nahi rehna chahiye — humne portable ORM use kiya hai.

> **Gotcha:** Pooled URL connection limit 100 deta hai aur sleep nahi karta. Non-pooled URL agar use kiya to first cold start fail hoga. **Pooled hi le.**

---

## 4. Step 2 — Email setup karo (Resend, ~10 min)

Yeh **first deploy ke liye optional** hai. Email verification kaam nahi karega lekin signup-login chal jayega. Agar phir bhi karna hai (recommend karta hu, 10 min ka kaam hai):

1. https://resend.com → Sign up (GitHub se)
2. **API Keys** → "Create API Key" → naam de `grindmate-prod`, full access. Copy karo (sirf ek baar dikhega).
3. **Domains** → "Add domain". Yahan teen options hain:
 - **Apna domain hai (₹900):** Add kar, DNS records dale, verify ho jayega. Phir `noreply@yourdomain.com` se bhej sakta hai.
 - **Domain nahi hai:** Skip "Add domain". Resend ka shared domain `onboarding@resend.dev` use kar — works for testing. Production users ke spam folder mein ja sakta hai but functional hai.
4. Save: API key, sender email (`onboarding@resend.dev` ya `noreply@yourdomain.com`)

> **Spam folder gotcha:** Bina apne domain ke saath emails Gmail mein spam mein jayenge. Dosto ko bata dena ya unko whitelist karwana ek baar.

---

## 5. Step 3 — Backend deploy (Render, ~30 min first time)

**Account:**
1. https://render.com → Sign up with GitHub
2. Repo access do GitHub OAuth se

**Service create karo:**
1. Dashboard → "New +" → **Blueprint**
2. GitHub repo `grindmate` select karo
3. Render auto-detect karega `render.yaml` (jo humne already commit kiya hai). Agar nahi karta, manually `render.yaml` path daal de.
4. "Apply" karo. Render service ko queue karega.

**Environment variables daal — yeh pehle critical step hai:**

Service page kholo → **Environment** tab. Yeh values daalne hain (jo `render.yaml` mein `sync: false` mark hain woh manually):

```
DATABASE_URL = <Neon ka pooled URL paste karo>
DJANGO_ALLOWED_HOSTS = grindmate-api.onrender.com
 (apne service ka URL — Render assign karega, deploy attempt
 ke baad pata chalega. Pehli baar `*` daal de testing ke liye,
 deploy success hone ke baad asli URL daalna)
CSRF_TRUSTED_ORIGINS = https://grindmate.vercel.app
 (frontend deploy ke baad fill karenge — abhi blank chhod do)
CORS_ALLOWED_ORIGINS = https://grindmate.vercel.app
 (same as above — frontend ke baad)
FRONTEND_URL = https://grindmate.vercel.app
 (same as above — frontend ke baad)
EMAIL_HOST_PASSWORD = <Resend API key>
DEFAULT_FROM_EMAIL = GrindMate <onboarding@resend.dev>
 (ya apne domain wala address)
SENTRY_DSN = (abhi blank — Step 7 mein dalenge)
```

`DJANGO_SECRET_KEY` aur `CRON_SHARED_SECRET` ko Render auto-generate kar dega kyunki `render.yaml` mein `generateValue: true` likha hai — usse haath mat lagana.

**Deploy karo:**
1. Render apne aap deploy try karega. Logs **Logs** tab mein dekho live.
2. First build ~5-10 min lagega. `pip install`, `collectstatic`, `migrate` sab chalegi.
3. Build pass hone par "Live" status dikhega.

**Verify:**
```bash
curl https://<your-service>.onrender.com/health/
# Expected: {"status": "ok"}
```

Agar `502 Bad Gateway` aaye:
- Logs mein dekho — common: `DJANGO_ALLOWED_HOSTS` mein hostname missing, ya migration fail hua
- Settings tab pe "Manual Deploy" button se rebuild kar sakte ho

> **Cold start yaad rakh:** Pehli request 30 sec lagegi (free plan sleep ke baad). Subsequent requests instant.

---

## 6. Step 4 — Frontend deploy (Vercel, ~15 min)

**Account:**
1. https://vercel.com → Sign up with GitHub

**Import project:**
1. Dashboard → "Add New..." → **Project**
2. GitHub repo `grindmate` import karo
3. **Root Directory** → `frontend` set karo (yeh important — varna Vercel root mein build dhundega)
4. Framework preset auto-detect: **Vite** (correct)
5. Environment Variables daal:
 ```
 VITE_API_BASE_URL = https://<render-service>.onrender.com/api/v1
 VITE_APP_NAME = GrindMate
 ```
6. **Deploy** click karo

Build 1-2 min mein hojayega. URL milegi: `https://grindmate-<random>.vercel.app` ya `grindmate.vercel.app` agar available hai.

**Verify:**
1. URL pe ja, login page khulega
2. Browser DevTools → Network tab open kar
3. Login attempt kar (fake user se) — `/api/v1/auth/login/` request Render backend pe hit honi chahiye
4. Agar 401 ya validation error aaye, **API connect ho gaya** — yahi chahiye

**Ab Render pe wapas ja aur woh blank env vars fill kar:**
```
DJANGO_ALLOWED_HOSTS = grindmate-api.onrender.com
CSRF_TRUSTED_ORIGINS = https://grindmate.vercel.app
CORS_ALLOWED_ORIGINS = https://grindmate.vercel.app
FRONTEND_URL = https://grindmate.vercel.app
```
"Save Changes" se Render apne aap rebuild karega (~3 min).

**End-to-end test:**
1. Vercel URL kholo
2. Signup kar — apne ek alag email se
3. Resend logs mein verification email dikhna chahiye (Resend dashboard → Emails)
4. Login kar
5. Dashboard kholega

Yahan tak pahuch gaya = **app live hai**.

---

## 7. Step 5 — Periodic LeetCode sync (GitHub Actions, ~5 min)

`render.yaml` ne `CRON_SHARED_SECRET` auto-generate kiya hai. Render dashboard → Environment tab khole, woh value copy kar.

**GitHub repo settings mein secrets add karo:**
1. Repo → Settings → Secrets and variables → Actions → "New repository secret"
2. Add:
 - `API_BASE_URL` = `https://<render-service>.onrender.com`
 - `CRON_SHARED_SECRET` = `<jo Render ne generate kiya>`

**Test karo:**
1. GitHub repo → Actions tab → "Scheduled LeetCode sync" workflow
2. "Run workflow" button → main branch select → Run
3. ~30 sec mein job complete hoga (Render cold start + sync)
4. Logs mein `{"synced": N, "failed": 0, "total": N}` aana chahiye

Ab har 6 ghante mein automatic chalega. Bina Celery worker ke. Win.

> **Free Actions minutes:** Public repo unlimited. Private repo: 2000/month. Ek run ~1 min leta hai, 6h frequency = 4 runs/day = 120/month. Bilkul fits.

---

## 8. Step 6 — Sentry (errors monitoring, ~5 min, optional but recommended)

Pure Saturday lagaya hai, ab koi bug aaya to `Render logs` 7-day retention pe rakh ke debug karna pain hai. Sentry email/Slack pe alert deta hai.

1. https://sentry.io → Sign up
2. Create project → **Django** select
3. DSN dikhega: `https://abc123@o123.ingest.sentry.io/123`
4. Render dashboard → Environment → `SENTRY_DSN` set karo, save

Frontend bhi karna ho to Sentry mein **React** project alag se bana, key vercel mein env var ke through daal de. **Backend ke liye yeh enough hai abhi.**

Test: backend pe ek random URL hit kar (`/api/v1/foo-bar/`) — 404 throw karega. Sentry mein 30 sec mein event aa jayega.

---

## 9. Common gotchas (jab fas, yeh padh)

### "CORS error" / "Access blocked by CORS policy"
- Render env var `CORS_ALLOWED_ORIGINS` mein **exact** Vercel URL (with `https://`, no trailing slash) set hai?
- Save ke baad Render rebuild hua? "Manual Deploy" se force kar.
- Vercel ka URL `vercel.app` ke alawa aur kuch ho (preview URL `<branch>-<repo>.vercel.app`) — har preview ke liye alag CORS daalna pain hai. Production URL pe focus rakh.

### "CSRF verification failed" on POST
- Render env var `CSRF_TRUSTED_ORIGINS` set hai? Scheme + host chahiye: `https://grindmate.vercel.app`
- Lower-case `https` use kar.
- Multiple origins comma-separated, no spaces.

### Login pe 500 / "Internal Server Error"
- Render Logs khol. Sabse common: `DATABASE_URL` typo. Pooled vs non-pooled mismatch.
- Ya migration nahi chali. Render shell open kar (free tier mein "Shell" tab paid hai — workaround: ek `python manage.py migrate` ko rebuild ke part of `buildCommand` mein rakha hai render.yaml mein, woh chala chahiye).

### Vercel build fail
- Logs mein dekh — sabse common: `npm ci` ke baad `tsc -b` mein typecheck error.
- Local pe `cd frontend && npm run build` chal raha hai? Wahi exact command Vercel chala raha hai.

### LeetCode sync fail (production-only)
- Render IP ko Cloudflare ne block kar diya (yeh actually hota hai).
- Logs: `Rate limited (HTTP 403)` ya `Cloudflare`.
- Fix karne ka koi clean tareeka nahi free mein. Workaround:
 - User dashboard pe "manual mark solved" use kare
 - Account page pe "Sync now" button se test kar — agar 403 dikhe, user-agent rotate karna pad sakta hai (`apps/leetcode/services.py` mein header)

### Render service deploy ho gaya, but `*.onrender.com` pe 502
- Cold start ho raha hai — 30 sec wait kar. Phir refresh.
- Persistent 502: Logs check, gunicorn boot fail ho raha hoga (env var missing).

### Email nahi aaya
- Resend dashboard → Emails tab mein delivery status dekho
- "Bounced" / "Failed" — `DEFAULT_FROM_EMAIL` ka domain Resend mein verified nahi hai
- Sender domain `resend.dev` ka use kar rahe ho? Gmail spam mein dalta hai — spam folder check karwa.

### Tests ki 422 / 401 jab manually `/api/v1/leetcode/cron/sync-all/` curl karta hai
- `X-Cron-Token` header bhej raha hai? Lowercase ya space mat dal.
- `CRON_SHARED_SECRET` Render aur GitHub secret bilkul same hai? Whitespace check kar.

---

## 10. What NOT to do (apne aap ko rok)

Yeh sab cheezein **abhi mat kar**, baad mein kar — pehle kaam karna chahiye:

- Custom domain abhi mat le (₹900 spend karke 1 user use karega — pehle 5 dost le aa)
- Cloudflare CDN setup mat kar (Vercel + Render dono pe HTTPS already free hai)
- Stripe / payments mat add kar (project ka scope nahi hai)
- Multi-environment (staging) mat bana — main hi enough hai abhi
- "100% test coverage" ke liye time mat waste kar — 60 tests, 83% coverage already strong hai
- Backups ke liye S3 setup mat kar — Neon free tier 7-day point-in-time recovery deta hai (paid feature actually) chal jayega; manual backup chahiye to `pg_dump` weekly run kar
- Docker mat use kar deploy ke liye — Render auto handle karta hai Python apps ko, Docker overkill hai
- Monitoring dashboards mat bana — Render basic metrics deta hai, Sentry errors alert deta hai, bas
- Rate limiting / WAF mat add kar — DRF ka throttle already hai
- "Microservices" mat sochna — yeh ek monolith hai, rakh isko monolith

Agar kuch bhi yahan se karne ka mann ho raha hai — ruk, deploy karle, dosto se feedback le, **tab decide kar.**

---

## 11. Post-deploy: chhote polish (1-2 ghante max)

Deploy ho gaya, dosto ko share karna hai. Yeh kar:

1. **Tu khud apna LeetCode handle link kar.** Sync chala. Dashboard pe stats dikh rahe hain. Verify kar sab kaam karta hai.
2. **Ek group bana**, invite link generate kar, **doosre device se** (phone) join kar — invite flow test kar.
3. **README mein live URL add kar:**
 ```markdown
 ## Live demo
 - Web: https://grindmate.vercel.app
 - Demo account: demo@grindmate.app / demogrind123 (LeetCode handle: anveet linked)
 ```
4. **Demo account bana** taaki interviewer / friends signup kiye bina dekh sakein. Ek group bana, 3-4 members add kar (apne factories.py se mock data ya khud sign up kar ke).
5. **Repo pe LICENSE file** add kar (MIT) — `gh repo edit --license mit` ya manually copy karle GitHub se.
6. **Resume entry tayar kar:**
 > **GrindMate** — Friend-group DSA tracker (Django + DRF + React + TypeScript)
 > • Designed and shipped a real-world web app: 60+ tests, 83% coverage, CI/CD via GitHub Actions
 > • Custom Postgres data model (User, Group, SubmissionLog) with composite indexes & cached leaderboard query
 > • External GraphQL integration with retry/backoff and graceful failure handling
 > • Free-tier deploy: Render + Vercel + Neon + Resend + Sentry, scheduled sync via GitHub Actions cron
 > • [Live demo](https://...) · [Code](https://github.com/...)

---

## 12. Going further (jab GrindMate kaam karta hai, **abhi nahi**)

Ye sab Sprint 2 / Sprint 3 ke liye hai — **deploy ho gaya tab dekh:**

- Heatmap calendar (GitHub-style solve grid) — `apps/leetcode/managers.py` mein `distinct_solved_dates` already hai
- Daily Challenge feature (admin sets a problem, group race)
- Discord/Slack webhook for daily group summaries
- Google OAuth login (`dj-rest-auth` + `django-allauth` already in requirements)
- Custom domain (jab confidence aaye)
- Stripe ya UPI payments — agar SaaS karna ho (pakka mat soch)

---

## 13. Final checklist (deploy karne se pehle ek baar dekh)

- [ ] Local pe `pytest` aur `npm run build` pass
- [ ] Code GitHub pe push hai (public repo)
- [ ] Neon project bana, pooled DATABASE_URL save
- [ ] Resend account, API key save (optional)
- [ ] Render service deployed, env vars set
- [ ] `/health/` se 200 OK
- [ ] Vercel project deployed, `VITE_API_BASE_URL` set
- [ ] Render env mein frontend URL backfill (CORS, CSRF, FRONTEND_URL)
- [ ] Vercel URL pe signup → login → dashboard kaam kar raha
- [ ] GitHub Actions secrets set (`API_BASE_URL`, `CRON_SHARED_SECRET`)
- [ ] "Scheduled LeetCode sync" workflow manual run pe `synced > 0`
- [ ] Sentry DSN set, intentional 404 se event capture hua
- [ ] README mein live URL + demo account
- [ ] 1 dost ko link share kiya — woh signup kar paya

---

## 14. Agar fas gaya, koi cheez kaam nahi kar rahi

Mujhe bata. Logs paste kar — Render logs, Vercel build log, ya browser console error. **Specifically yeh batana:**

1. Konsa step pe stuck hai (number 1-13)?
2. Exact error message kya hai?
3. Maine kya try kiya hai?

Phir saath debug karenge. Stuck rehne ka koi point nahi hai — ek baar setup ho gaya, second time bahut tezi se hoga.

Best of luck bhai. **Friday raat pyari rakh, weekend deploy kar dega.**
