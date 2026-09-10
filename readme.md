# Vidinie

Turn a PDF or a web article into a narrated explainer video.

Upload a document or paste a URL. Vidinie reads it, proposes an outline, writes a
script, records a voiceover, gathers or generates the visuals, and renders a
finished MP4. You review and edit at every step — it is not a one-shot button.

## How a video gets made

Four stages run in order. Each one writes its result back to the pipeline record,
and the UI stops there so you can change what it produced before moving on.

```text
  PDF / URL
      │
      ▼
┌──────────────────┐  pdfplumber, PyMuPDF, BeautifulSoup
│ document         │  text out, embedded images out, images labelled by Claude
│ processing       │
└────────┬─────────┘
         ▼           you can add or delete sections and images here
┌──────────────────┐  Claude reads the sections
│ content          │  proposes an outline: N segments, one topic each
│ analysis         │
└────────┬─────────┘
         ▼           you can add, delete or reorder segments here
┌──────────────────┐  Claude writes narration per segment
│ script           │  ElevenLabs records it, picks background music
│ generation       │  Pexels / Flux / Seedance supply the visuals
└────────┬─────────┘
         ▼           you can rewrite a script and re-record here
┌──────────────────┐  a Claude agent writes Remotion React components
│ video            │  into a copy of _base/, then renders
│ generation       │
└────────┬─────────┘
         ▼
   outputs/<pipeline_id>/out/VidinieComposition.mp4
```

Stages are defined in `core/data/enums.py:VideoPipelineStage` and driven by
`api/core/execution/executor.py`.

## Services

Five containers, wired together by `docker-compose.yml`.

```text
        browser
           │
           ▼
┌────────────────────────┐
│ vidinie-frontend :3000 │  Next.js — pipeline UI, Better Auth, Stripe billing
└──────┬─────────────┬───┘
       │ JWT         │ session + subscriptions
       ▼             ▼
┌────────────────────────┐         ┌──────────┐
│ vidinie-backend :8000  │────────▶│ mongodb  │  pipelines, users, subscriptions
│ FastAPI                │         └──────────┘
└──────┬─────────────────┘              ▲
       │ enqueue stage                  │
       ▼                                │
┌──────────┐   broker + pub/sub   ┌──────────┐
│  redis   │◀────────────────────▶│ celery   │  runs the four stages
└──────────┘                      │ worker   │──┘
     ▲                            └────┬─────┘
     │ progress events                 │ shells out to
     │                                 ▼
     └── websocket ──▶ browser    Remotion CLI + Chromium
```

The frontend owns identity. Better Auth signs a JWT; the backend verifies it
against the frontend's JWKS endpoint (`api/core/auth/jwks.py`) — the backend
never sees a password.

Celery workers publish progress to Redis, and the backend relays it over two
websockets: `/video-pipelines/{id}/ws` for one pipeline,
`/users/{user_id}/video-pipelines/ws` for the whole list.

## Running it

You need Docker, and API keys for Anthropic, Replicate, ElevenLabs and Pexels.

```bash
cp env.example .env     # then fill in the keys
docker compose up --build
```

- App — http://localhost:3000
- API docs — http://localhost:8000/docs
- Rendered videos are served from http://localhost:8000/media and land in `outputs/`

### Without Docker

The backend needs Python 3.10, Node 20, FFmpeg and Chromium on the host, plus a
MongoDB and a Redis to talk to.

```bash
pip install -r requirements.txt
npm install                                    # Remotion, for rendering
uvicorn api.main:app --reload --port 8000
celery -A api.core.celery worker --loglevel=info

cd frontend && npm install && npm run dev
```

## Configuration

Everything comes from `.env` — there is no config file. Copy `env.example` and
fill it in.

| Variable | Used for |
|---|---|
| `ANTHROPIC_API_KEY` | content analysis, outlines, scripts, image labelling, and the agent that writes the Remotion code |
| `REPLICATE_API_TOKEN` | generated images (`black-forest-labs/flux-schnell`) and clips (`bytedance/seedance-1-lite`) |
| `ELEVENLABS_API_KEY` | voiceover and background music |
| `PEXELS_API_KEY` | stock images and video |
| `MONGODB_URI`, `DB_NAME` | pipelines, users, subscriptions |
| `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` | Redis, for the task queue and progress events |
| `BETTER_AUTH_SECRET`, `BETTER_AUTH_URL` | session signing and the JWKS endpoint the backend verifies against |
| `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`, `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_SECRET` | Google sign-in |
| `NEXT_PUBLIC_STRIPE_SECRET_KEY`, `NEXT_PUBLIC_STRIPE_WEBHOOK_SECRET` | subscriptions |
| `NEXT_PUBLIC_STARTER_PLAN_PRICE_ID`, `NEXT_PUBLIC_PROFESSIONAL_PLAN_PRICE_ID` | the two paid plans |
| `NEXT_PUBLIC_RESEND_API_KEY` | verification, password reset and welcome emails |
| `NEXT_PUBLIC_API_URL`, `FRONTEND_URL` | how the two halves address each other, and CORS |
| `NEXT_PUBLIC_POSTHOG_KEY`, `NEXT_PUBLIC_POSTHOG_HOST` | product analytics |

Paths, directory layout and chunk sizes live in `core/utils/config_loader.py`.

## API

All routes need a Better Auth JWT as a bearer token.

| Method | Path | Does |
|---|---|---|
| `POST` | `/video-pipelines/from-file` | start a pipeline from an uploaded PDF |
| `POST` | `/video-pipelines/from-url` | start a pipeline from an article URL |
| `GET` | `/video-pipelines/` | list your pipelines |
| `GET` | `/video-pipelines/{id}` | full pipeline state |
| `POST` | `/video-pipelines/{id}/process` | run document processing |
| `POST` | `/video-pipelines/{id}/sections` · `DELETE .../sections/{i}` | edit extracted content |
| `POST` | `/video-pipelines/{id}/images` · `DELETE .../images/{i}` | edit the image set |
| `POST` | `/video-pipelines/{id}/outline/segments` · `DELETE .../{i}` | edit the outline |
| `POST` | `/video-pipelines/{id}/generate-scripts` | write scripts and record voiceovers |
| `POST` | `/video-pipelines/{id}/generate` | render the video |
| `POST` | `/video-pipelines/{id}/review` | record a rating and feedback on the finished video |
| `GET` | `/video-pipelines/{id}/output/stream` · `/download` | watch or fetch the MP4 |
| `WS` | `/video-pipelines/{id}/ws` | live stage progress |

Full schema at `/docs` once the backend is up.

## Layout

```text
core/            everything that makes a video, framework-free
  clients/         one wrapper per provider: reasoning, image, video, audio, music
  operators/       one job each: content_analyzer, script_generator, video_generator, …
  operations/      stage-level orchestration over the operators
  processors/      pdf and html to text + images
  data/            pydantic models and the VideoPipeline record
  prompts/         jinja2 templates for every Claude call

api/             the HTTP and queue layer around core/
  routes/          pipelines and users
  core/execution/  the stage runner
  core/auth/       JWT verification against Better Auth's JWKS
  core/celery.py   the worker

frontend/        Next.js app — auth, billing, the pipeline editor
_base/           Remotion project the agent copies and fills in per video
landing/         static marketing site
outputs/         rendered videos, one directory per pipeline
```

The split matters: `core/` knows nothing about HTTP, Celery or Mongo, so a stage
can be run directly from Python without the rest of the stack.

## Plans

Free accounts get 2 videos. Starter is 5 a month, Professional 20, both through
Stripe. The counts live on the user record (`videos_remaining`,
`videos_generated`) and the limits are set in `frontend/lib/auth.ts`.

## Licence

MIT
