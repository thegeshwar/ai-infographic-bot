# InfographAI — Product Design Spec

**Date:** 2026-03-31
**Status:** Approved
**Author:** Thegeshwar + Claude

---

## 1. What It Is

A web app that generates daily LinkedIn-ready infographics + captions for professionals. Users sign up, pick their industry and tone, and receive a fresh infographic every day on their dashboard. They download the PNG + copy the caption and post to LinkedIn themselves.

**Pricing:** $15-20/mo (exact TBD at launch)
**Free tier:** 3 posts/month, email sign-up required
**Paid tier:** Daily generation (30/mo), rework capability, post history

---

## 2. User Journey

```
1. Land on marketing page → see example infographics
2. Sign up with email → verify email
3. Onboarding wizard:
   a. Pick industry (1 of 10)
   b. Optional: company name + logo upload
   c. Pick tone (Data-driven / Thought leader / Educator / Contrarian)
   d. Enter 3-5 focus keywords/topics
4. Dashboard shows: "Your first post is generating..." (first one triggers immediately)
5. Post appears: infographic preview + caption + hashtags
6. User clicks "Copy Caption" + "Download PNG"
7. User posts to LinkedIn manually
8. Next day: new post waiting on dashboard
9. Optional: click "Rework" to regenerate with different angle
```

---

## 3. Architecture

### 3.1 High-Level

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Next.js App │────▶│  Supabase    │────▶│  Generation     │
│  (Frontend)  │     │  (Auth + DB) │     │  Worker (Python) │
└─────────────┘     └──────────────┘     └─────────────────┘
                                                │
                                          ┌─────▼─────┐
                                          │ Claude CLI │
                                          │ + Playwright│
                                          └───────────┘
```

### 3.2 Components

**A. Next.js Web App**
- Marketing/landing page
- Auth (Supabase Auth — email + password, Google OAuth)
- Onboarding wizard
- User dashboard (today's post, history, settings)
- Admin panel (user management, generation logs, health)
- API routes for generation triggers and webhook callbacks

**B. Supabase**
- Auth: email/password + Google OAuth, email verification
- Database (Postgres): users, preferences, posts, generations, subscriptions
- Storage: generated PNGs, user-uploaded logos
- Row Level Security on all tables

**C. Generation Worker (Python)**
- Runs on VPS as a systemd service
- Polls for pending generation jobs (or triggered via Supabase Realtime)
- Per job: calls Claude CLI with user preferences as prompt constraints
- Claude discovers news → writes story.json → generates HTML
- Worker validates HTML (existing validate.py) → renders PNG (Playwright) → uploads to Supabase Storage
- Updates post record with image URL, caption, hashtags, status

**D. Scheduler (Cron)**
- Runs daily at configurable time
- Queries all users due for generation (paid = daily, free = if under 3/mo)
- Creates generation jobs in the database
- Worker picks them up sequentially (or parallel with rate limiting)

### 3.3 Separation of Concerns

```
┌────────────────────────────────────────────────┐
│ Web Layer (Next.js)                            │
│  - Auth, UI, API routes                        │
│  - NEVER generates infographics directly       │
│  - Creates "generation jobs" in DB             │
└────────────────────┬───────────────────────────┘
                     │ Supabase DB
┌────────────────────▼───────────────────────────┐
│ Generation Layer (Python worker)               │
│  - Picks up jobs from DB                       │
│  - Calls Claude CLI                            │
│  - Validates, renders, uploads                 │
│  - Updates job status in DB                    │
└────────────────────┬───────────────────────────┘
                     │
┌────────────────────▼───────────────────────────┐
│ Design Layer (Skills + Rules)                  │
│  - Content pillars per industry                │
│  - Design rules (1920x1080, validation)        │
│  - Strategy rotation (voice, hook, type)       │
│  - Per-user custom design prefs (future)       │
└────────────────────────────────────────────────┘
```

This 3-layer separation means:
- Web layer can be swapped (mobile app later) without touching generation
- Generation worker can scale to a separate server without touching web
- Design layer can be customized per-user (future) without touching infrastructure

---

## 4. Database Schema

```sql
-- Users (extends Supabase auth.users)
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null,
  display_name text,
  company_name text,
  logo_url text,
  industry text not null,           -- one of 10 industries
  tone text not null default 'data-driven',
  keywords text[] default '{}',     -- 3-5 focus topics
  timezone text default 'America/New_York',
  generation_hour int default 8,    -- hour in user's timezone
  plan text not null default 'free', -- 'free' | 'paid'
  stripe_customer_id text,
  stripe_subscription_id text,
  posts_this_month int default 0,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Per-user design preferences (future expansion)
create table public.design_preferences (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  key text not null,                -- e.g. 'color_palette', 'font_style', 'layout_preference'
  value jsonb not null,             -- flexible JSON for any design rule
  created_at timestamptz default now(),
  unique(user_id, key)
);

-- Generated posts
create table public.posts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  headline text not null,
  hook text not null,
  caption text not null,
  hashtags text[] default '{}',
  body text[] default '{}',
  insight text,
  source text,
  source_url text,
  pillar text,
  strategy jsonb,                   -- voice, hook_style, depth, type, color
  image_url text,                   -- Supabase Storage URL
  image_filename text,
  html text,                        -- full HTML (for re-rendering)
  status text default 'generating', -- generating | ready | failed
  rework_count int default 0,
  created_at timestamptz default now()
);

-- Generation jobs (queue)
create table public.generation_jobs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.profiles(id) on delete cascade,
  post_id uuid references public.posts(id),
  type text not null default 'generate', -- 'generate' | 'rework'
  status text default 'pending',         -- pending | processing | completed | failed
  rework_prompt text,                    -- for rework jobs
  error text,
  started_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz default now()
);

-- Row Level Security
alter table public.profiles enable row level security;
alter table public.posts enable row level security;
alter table public.design_preferences enable row level security;
alter table public.generation_jobs enable row level security;

-- Users can only see/edit their own data
create policy "Users see own profile" on public.profiles
  for all using (auth.uid() = id);
create policy "Users see own posts" on public.posts
  for all using (auth.uid() = user_id);
create policy "Users see own prefs" on public.design_preferences
  for all using (auth.uid() = user_id);
create policy "Users see own jobs" on public.generation_jobs
  for all using (auth.uid() = user_id);
```

**Why `design_preferences` is a separate table:** This is the expansion point you asked for. Right now it's empty. Later, users can set custom color palettes, font preferences, layout rules, banned elements, brand guidelines — all as key-value JSON. The generation worker reads these and injects them as additional constraints into the Claude prompt. No schema migration needed to add new preference types.

---

## 5. Industries (V1)

Each industry maps to a content pillar configuration:

| Industry | Search Domains | Example Topics |
|----------|---------------|----------------|
| Tech/AI | AI releases, benchmarks, funding | GPT updates, compute costs, open-source |
| Electronics/Manufacturing | PCB, semiconductors, supply chain | Copper prices, lead times, fab news |
| SaaS/Startups | Funding, launches, metrics | Series rounds, ARR milestones, pivots |
| Fintech/Finance | Markets, regulation, payments | Rate changes, IPOs, compliance |
| Healthcare/Biotech | FDA, trials, funding, devices | Approvals, breakthroughs, M&A |
| Cybersecurity | Breaches, threats, compliance | CVEs, ransomware, zero-days |
| Real Estate | Rates, inventory, regulations | Housing data, commercial trends |
| E-commerce/Retail | Platform changes, consumer data | Shopify/Amazon updates, trends |
| Clean Energy/Climate | Policy, investments, milestones | Solar/EV data, carbon markets |
| Recruiting/HR Tech | Hiring trends, tools, policy | Remote work data, AI hiring |

Each industry config includes:
- 5-6 content pillars with search queries
- Industry-specific voice options
- Appropriate infographic types (e.g., Real Estate loves map/geographic, Finance loves stat-driven)
- Color palette tendencies (e.g., Finance = navy/gold, Clean Energy = green/white)

Stored as JSON configs in the codebase: `config/industries/{industry-slug}.json`

---

## 6. Generation Pipeline (per user)

```
1. Scheduler creates generation_job (status: pending)
2. Worker picks up job, sets status: processing
3. Worker builds Claude prompt:
   - Industry pillar config
   - User's tone + keywords
   - User's company name + logo (if set)
   - Rotation constraints (avoid last 5 pillars/types/voices)
   - User's design_preferences (future)
4. Worker calls: claude -p "<prompt>" --dangerously-skip-permissions
5. Claude:
   a. WebSearch for trending news in user's niche
   b. Picks best story
   c. Writes story.json (hook, headline, body, caption, HTML)
   d. Saves to /tmp/infographai/{user_id}/{date}/story.json
6. Worker validates HTML (validate.py — 5 rules)
7. If validation fails: retry once with error feedback, then mark failed
8. Worker renders PNG (Playwright, 1920x1080 @ 2x)
9. Worker uploads PNG to Supabase Storage (public bucket, user-scoped path)
10. Worker creates/updates post record (status: ready)
11. Worker updates job (status: completed)
12. Optional: send email notification "Your post is ready!"
```

---

## 7. Pages

### 7.1 Marketing / Landing Page (`/`)
- Hero: animated showcase of 6-8 best infographics (carousel or grid)
- Value prop: "Daily LinkedIn infographics. AI-generated. Industry-specific."
- How it works: 3 steps (Sign up → Pick your niche → Get daily posts)
- Pricing: Free (3/mo) vs Paid ($15-20/mo)
- Social proof: example posts with engagement metrics from your real posts
- CTA: "Start Free" → sign up

### 7.2 Auth (`/login`, `/signup`)
- Email + password sign up
- Google OAuth
- Email verification required
- Password reset flow

### 7.3 Onboarding (`/onboard`)
- Step 1: Pick industry (10 cards with icons)
- Step 2: Company name + logo (optional, skip button)
- Step 3: Pick tone (4 options with examples of each)
- Step 4: Enter 3-5 keywords
- "Generate your first post" CTA → triggers immediate generation

### 7.4 Dashboard (`/dashboard`)
- Today's post (large preview): infographic image + caption + hashtags
- Action buttons: "Copy Caption" (clipboard), "Download PNG", "Rework"
- Post status indicator: Generating (spinner) / Ready / Failed
- History sidebar or tab: past 30 days, thumbnail grid
- Usage counter (free tier): "2 of 3 posts used this month"

### 7.5 Post Detail (`/dashboard/posts/{id}`)
- Full-size infographic preview
- Editable caption textarea
- Hashtags display
- Source link
- Rework button with optional prompt
- Download button
- Metadata: industry, voice, hook style, type

### 7.6 Settings (`/settings`)
- Profile: name, email, company, logo
- Content preferences: industry, tone, keywords
- Notification preferences: email on post ready
- Billing: current plan, upgrade/downgrade, Stripe portal link
- Design preferences (future): color palette, font style, layout rules

### 7.7 Admin (`/admin`) — Your eyes only
- User list with plan, industry, generation stats
- Generation job queue (pending, processing, failed)
- System health: worker status, last run, error rates
- Manual triggers: regenerate for user, bulk operations

---

## 8. Payments (Stripe)

- Stripe Checkout for initial subscription
- Stripe Customer Portal for plan changes, cancellation, invoices
- Webhook handler for: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`
- Free → Paid upgrade: redirect to Stripe Checkout
- Paid → Free downgrade: handled via Stripe Portal, update profile on webhook
- Grace period: if payment fails, 3-day grace before downgrading to free

---

## 9. Security

- Supabase Auth handles password hashing, JWTs, session management
- Row Level Security on ALL tables — users can never see other users' data
- Supabase Storage policies: users can only access their own folder
- API routes validate auth token on every request
- Stripe webhook signature verification
- Rate limiting on generation triggers (prevent abuse)
- No user credentials stored for LinkedIn (they post manually)
- Environment variables for all secrets (Stripe keys, Supabase keys, admin password)
- HTTPS everywhere (Nginx + Let's Encrypt on VPS)

---

## 10. What's NOT in V1

- Auto-posting to LinkedIn (future — needs LinkedIn API approval)
- Per-user custom design rules (schema ready via `design_preferences` table, UI not built)
- Team/multi-user accounts
- Post performance analytics
- Multiple posts per day
- Cross-platform (Instagram, Twitter)
- Mobile app
- Custom brand kit editor (colors, fonts, logo placement)
- A/B testing of post styles
- Referral program

All of these are designed to be addable without schema migrations or architecture changes.

---

## 11. Tech Stack Summary

| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | Next.js 15 (App Router) | Already used in QMS Leader, SSR for landing page SEO |
| Styling | Tailwind CSS | Fast iteration, consistent design |
| Auth | Supabase Auth | Free tier generous, RLS integration, Google OAuth built-in |
| Database | Supabase Cloud (Postgres) | RLS, Realtime for job status updates, separate from VPS Supabase |
| Storage | Supabase Cloud Storage | PNG hosting, user logo uploads, CDN |
| Payments | Stripe | Industry standard, Checkout + Portal + Webhooks |
| Worker | Python (systemd service) | Existing pipeline code reuse |
| Rendering | Playwright (Python) | Already proven in current pipeline |
| AI | Claude CLI | Zero marginal cost on existing subscription |
| Hosting | VPS (existing Oracle) | Already running, nginx + SSL configured |
| Email | Resend or Supabase built-in | Transactional emails (verification, post ready) |

### 11.1 Design Direction

**Light theme. Minimal. Not dark, not navy, not blue-heavy.**

- Background: warm white (#FAFAF8) or light cream
- Typography: clean sans-serif (Inter or similar), generous spacing
- Accent: single warm accent color (coral, amber, or teal — NOT blue)
- Cards: subtle shadows, no heavy borders, rounded but not bubbly
- Infographic previews are the star — UI gets out of the way
- Inspiration: Linear, Notion, Readwise — functional beauty, zero clutter
- Mobile-responsive from day one
- No gradients, no glassmorphism, no dark mode in V1

---

## 12. Repo Structure

```
infographai/
├── src/                          # Next.js app
│   ├── app/
│   │   ├── page.tsx              # Landing page
│   │   ├── login/
│   │   ├── signup/
│   │   ├── onboard/
│   │   ├── dashboard/
│   │   │   ├── page.tsx          # Main dashboard
│   │   │   └── posts/[id]/
│   │   ├── settings/
│   │   ├── admin/
│   │   └── api/
│   │       ├── webhooks/stripe/
│   │       ├── generate/         # Trigger generation
│   │       └── rework/           # Trigger rework
│   ├── components/
│   │   ├── ui/                   # Shared UI components
│   │   ├── landing/              # Marketing page components
│   │   ├── dashboard/            # Dashboard components
│   │   └── onboard/              # Onboarding wizard
│   ├── lib/
│   │   ├── supabase/             # Client + server Supabase clients
│   │   ├── stripe/               # Stripe helpers
│   │   └── utils/
│   └── styles/
├── worker/                       # Python generation worker
│   ├── main.py                   # Job polling loop
│   ├── generator.py              # Claude CLI orchestration
│   ├── validator.py              # HTML validation (from existing)
│   ├── renderer.py               # Playwright rendering (from existing)
│   ├── uploader.py               # Supabase Storage upload
│   └── config/
│       └── industries/           # Per-industry JSON configs
│           ├── tech-ai.json
│           ├── electronics.json
│           ├── saas-startups.json
│           ├── fintech.json
│           ├── healthcare.json
│           ├── cybersecurity.json
│           ├── real-estate.json
│           ├── ecommerce.json
│           ├── clean-energy.json
│           └── recruiting-hr.json
├── supabase/
│   ├── migrations/               # SQL migrations
│   └── seed.sql                  # Dev seed data
├── scripts/
│   ├── scheduler.py              # Daily cron: create jobs for all users
│   └── setup-worker.sh           # systemd service setup
├── public/                       # Static assets
├── CLAUDE.md
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── .env.example
```

---

## 13. Expansion Points (by design)

| Future Feature | How It's Already Supported |
|---------------|--------------------------|
| Per-user design rules | `design_preferences` table (key-value JSON) |
| New industries | Drop a JSON file in `worker/config/industries/` |
| Auto-posting | Add a `posting_service` module to worker, update post status |
| Multiple posts/day | Change `generation_hour` to `generation_schedule` (array of hours) |
| Team accounts | Add `organization_id` to profiles, update RLS policies |
| Mobile app | API routes already serve JSON, build React Native client |
| Separate generation server | Worker already decoupled — just point it at a different machine |
| Analytics | Add `post_metrics` table, LinkedIn API read-only for impressions |
