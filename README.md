# Student Diagnostic Simulator

A game-like web and Android app that profiles how a student aged 11 to 18 thinks, learns and handles pressure, across **24 skills in 5 layers**, using **23 syllabus-free tasks** over **7 short sessions**, and turns it into an evidence-backed report for parents and the student. It is a screening profile, not a clinical assessment, and it never ranks students.

This repository implements the **P0 (pilot) scope** of the PRD and the Skill, Task and Signal Blueprint.

| Part | Path | Stack |
| --- | --- | --- |
| API, scoring engine, reports | `backend/` | FastAPI, SQLAlchemy 2, PostgreSQL 16, Alembic, Celery + Redis, Jinja2 + WeasyPrint |
| Shared task engine | `packages/task-library/` | TypeScript, no DOM or React Native dependencies |
| Web app (students, parents, schools, reviewers) | `apps/web/` | React 19, Vite, React Router |
| Android app (student shell) | `apps/mobile/` | Expo SDK 57, React Native, react-native-svg, a local Kotlin module for on-device voice (Vosk) |
| Shared test vectors and fixtures | `shared/` | JSON used by both Python and TypeScript tests |

## Quick start

Requirements: Python 3.12+ with [uv](https://docs.astral.sh/uv/), Node 20+, PostgreSQL 16, Redis (only for the Celery worker).

```bash
make install                          # uv sync + npm install
createdb -U postgres -O sds sds       # role sds/sds; see Makefile `db`
cd backend && uv run python -m app.cli demo     # demo school, students, completed cycles, reports
SDS_RELAX_SCHEDULE=1 uv run uvicorn app.main:app --port 8000   # dev: sessions open without waiting 2 days
npm run dev -w apps/web               # http://localhost:5173 (proxies /api to :8000)
```

Or with Docker: `docker compose up --build`, then `docker compose exec api python -m app.cli demo`.

In development the API creates tables and loads the item bank on start-up. Production runs `alembic upgrade head`, `python -m app.cli seed` and `python -m app.cli partitions` (see `docker-compose.yml`).

### Demo accounts (`app.cli demo`)

| Who | Sign in at | Credentials |
| --- | --- | --- |
| Student | `/play` | class code and PINs are printed by the demo command |
| Parent | `/parent` | phones `9810000001` to `9810000006`; the OTP appears at `GET /api/dev/outbox` |
| School admin | `/school` | `admin@sunrise-demo.in` / `demo-admin-123` |
| Teacher | `/school` | `teacher@sunrise-demo.in` / `demo-teacher-123` |
| Reviewer | `/admin` | `reviewer@revenuelogy-demo.in` / `demo-reviewer-123` |
| Superadmin | `/admin` | `superadmin@revenuelogy-demo.in` / `demo-super-123` |

The demo students are simulated personas with planted patterns, and their reports show them: Riya (pressure sensitivity), Kabir (strong working memory), Ananya (underconfident), Arjun (stronger in Hindi than English). Meera has consent but has not played; Dev's parent has not responded.

Staff accounts for real deployments: `uv run python -m app.cli create-staff --role reviewer --email … --name … --password …`.

## How a cycle works

1. **School onboarding.** The admin registers the school, creates classes (age band 11-14 or 15-18) and uploads a CSV (`name, parent_phone[, parent_language, student_language]`). Each student gets a class code + 4-digit PIN (shown once), and each parent gets a consent link by SMS.
2. **Parent consent.** The link shows a plain-language notice in English or Hindi. The parent verifies with an OTP and chooses: take part, voice capture, share the report with the school. No student can sign in, and no data is accepted, without consent. Every change is a new consent row; withdrawal deletes all of the child's data and confirms by SMS.
3. **Student sessions.** A warm-up checks language (English, Hindi, Hinglish), audio, microphone and text size. Seven sessions run every second day, each with a 3-day catch-up window, in order. Each session downloads one bundle (16-110 KB) and runs offline; answers are written to the device first and synced in batches. A long idle gap or three skips in a row offers a break; a session resumes at the first unfinished task.
4. **Scoring and reports.** Completing session 7 triggers scoring and report generation in the background. Reports pass an automated wording check; anything flagged goes to the review queue. Parents get the report in their language (switchable, with PDF); the student sees a one-screen version.

## Architecture

```
 Student device (web or Android)                         Server
 ┌────────────────────────────────────┐   bundle    ┌─────────────────────────────────────┐
 │ task-library SessionRunner         │◀────────────│ FastAPI  ─ auth, consent, scheduler  │
 │  · staircase, T13 ratings, pauses  │             │          ─ bundles from item bank    │
 │  · ItemTimer (ms, idle, switches)  │  events +   │          ─ event ingest (idempotent, │
 │  · voice: energy VAD / Vosk        │  features   │            answers re-checked)       │
 │  · OfflineBuffer (IndexedDB /      │────────────▶│ Celery   ─ scoring engine            │
 │    AsyncStorage), ordered sync     │             │          ─ report generator + PDF    │
 └────────────────────────────────────┘             │ Postgres ─ identity schema (names,   │
   audio never leaves the device                    │            phones, consent, audit)   │
                                                    │          ─ assessment schema (events,│
                                                    │            features, scores, reports)│
                                                    └─────────────────────────────────────┘
```

* **Identity and behaviour are split** into two Postgres schemas (`identity`, `assessment`), joined only by the student id. Guardian phone numbers are Fernet-encrypted with a keyed hash for lookup; PINs and OTPs are stored as keyed hashes. Reviewers see a pseudonym (`S-…`), never a name. Report content is stored with a `{name}` placeholder, filled in only when the parent or student views it.
* **Item events** are an append-only table range-partitioned by month (`app.cli partitions` creates partitions ahead of time), with an idempotency ledger for client event ids.
* **Voice** is processed on the device, on the web and on Android. The apps read microphone frames into memory, compute energy-based features (speech start, pauses, speaking time) and, when a Vosk model is installed, word timings for words per minute, read-aloud errors and self-corrections. Typed and transcribed answers are turned into numbers on the device (word count, variety, connectors, keyword coverage); the text is discarded. Audio frames exist only in memory: nothing is written to storage or uploaded, and there is no recording API anywhere in the code. Without voice consent the apps fall back to typing, and the Android app never asks for the microphone. The features are computed by the same shared code on both platforms (`task-library/src/voice/`). Hinglish has no speech model (the Hindi model writes Devanagari, Hinglish content is in Roman script), so Hinglish answers get energy-based timing only.
* **Every answer is re-checked on the server** from the server's answer key; the device's own correctness only drives the adaptive staircase.

## Scoring engine

Rule-based and versioned (`backend/app/scoring/`), so every finding can be explained and every report traces to a configuration version.

1. **Noise guard**: items answered in under 1 s (except rapid-response tasks) or with idle gaps over 20 s are excluded from speed and accuracy and counted as distraction events.
2. **Features per session** from events (spans, staircase levels, hit-minus-false-alarm, retention ratio, calibration gap, pressure drop, …), on-device voice/text features and session logs (on-schedule rate, returns between sessions).
3. **Normalise** each feature to 0-100 for the age band using configurable ranges (placeholders until pilot norms exist).
4. **24 skill scores** as weighted averages of their signals, following Blueprint A-E (for example, backward span counts double forward span; comprehension is 60% inference and 40% direct; calibration needs at least 60 rated items). A skill needs at least 2 signals.
5. **Language adjustment**: when the Hindi or Hinglish version of the same reasoning items scores clearly higher (gap above the threshold and at least 2 more items right), English-based scores are lifted and marked; the lift alone never creates a strength or an area to grow.
6. **Relative profile**: each skill against the student's own average; more than 1 SD above is a strength, more than 1 SD below an area to grow.
7. **Evidence level**: High = 3 agreeing signals across 2+ sessions; Medium = 2 across 2+ sessions or 3 in one session; Low = otherwise (kept internal as an early signal).
8. **Root-cause tags** on wrong answers (concept gap, careless slip, pressure-driven error, reading or language barrier, attention lapse, guess), applied only when the trigger and its confirming signal both appear.
9. **Patterns**: confidence mismatch, pressure pattern (must repeat in sessions 5 and 7), language adjustment.

Weights and thresholds live in `backend/app/scoring/config.py` as version `1.0.0` and can be versioned and activated in the admin console. The persona simulator (`backend/app/sim/`) plays complete cycles through the same bundles and API and is used by the tests to check that planted patterns are found.

## Item bank

1,472 items: procedurally generated, deterministic items for the language-neutral tasks (sequences, shapes, focus stream, number sense, routes, symbol codes, pressure pairs) and authored content in **English, Hindi and Hinglish** for the language tasks (info cards, passages with direct and inference questions, word-in-context, an invented mini-lesson, worked plans with a planted mistake, habit questions, conversation prompts, bilingual logic items). All content is everyday and syllabus-free. Items can be tagged, retired and inspected with difficulty and error statistics in the admin console; reseeding never overwrites edited items.

## Requirements coverage (PRD)

| ID | Requirement | Where |
| --- | --- | --- |
| FR-01 | Roles and access | `app/core/deps.py`, route guards; tested in `tests/test_access_admin.py` |
| FR-02 | Class code + PIN, parent OTP | `app/api/routes/auth.py`, lockout in `app/services/auth.py` |
| FR-03 | Consent choices, versioned log | `app/services/consent.py`, `app/api/routes/consent.py`, `/consent/:token` |
| FR-04 | Withdrawal deletes data, confirms | `app/services/withdrawal.py` (immediate job + daily sweep) |
| FR-05 | 23 tasks, easy/hard per age band | `app/content/`, renderers in `apps/web/src/student/items/`, `apps/mobile/src/items/` |
| FR-06 | 10-level staircase | `packages/task-library/src/staircase.ts`, `app/scoring/staircase.py` (shared vectors) |
| FR-07 | Confidence rating after scored items | `SessionRunner` (T13 prompt) |
| FR-08 | Same item in English and Hindi/Hinglish | T23 bilingual probe items, `variant_group` |
| FR-09 | 7 sessions over 14 days, 3-day catch-up | `app/services/scheduler.py` |
| FR-10 | Per-item signals | `ItemTimer` (task library), `ItemEvent` model |
| FR-11 | On-device voice, features only | `task-library/src/voice/`, `apps/web/src/voice/`, `apps/mobile/src/voice/`, `apps/mobile/modules/sds-voice/` |
| FR-13 to FR-17 | Features, 24 skills, evidence, relative profile, root causes, language adjustment | `app/scoring/` |
| FR-18 to FR-20 | Parent and student reports, wording check, language | `app/reports/` |
| FR-23 | Enrolment, consent, completion per class | `/school/dashboard`, `/school/class/:id` |
| FR-25 to FR-27 | Item bank, review queue, versioned scoring | `/admin/*`, `app/api/routes/admin.py` |

Not in this build (P1 and later): camera (FR-12), WhatsApp delivery (FR-21), cross-cycle progress (FR-22), class pattern dashboard (FR-24). The data model already carries camera consent and cycles.

## Testing

```bash
cd backend && uv run pytest            # 53 tests: content, engine personas, reports, consent, access, full API journey
npm test -w packages/task-library      # 26 tests: shared vectors, runner over real bundles, buffer, voice and text features
npm run build -w apps/web              # typecheck + production build
cd apps/web && npx playwright test     # browser journeys (needs the demo API running)
cd apps/mobile && npx tsc --noEmit && npx expo export --platform android
```

CI (`.github/workflows/ci.yml`) runs all of the above, checks that Alembic migrations match the models, and runs the Playwright journeys against a demo API. A separate workflow (`.github/workflows/android.yml`) builds the Android app with Gradle, runs the voice module's unit tests and uploads an installable APK.

## Configuration

All settings are `SDS_*` environment variables (`backend/app/core/config.py`). Important ones: `SDS_DATABASE_URL`, `SDS_REDIS_URL`, `SDS_SECRET_KEY` (required in production, 32+ characters), `SDS_FIELD_ENCRYPTION_KEY` (Fernet key for phone numbers), `SDS_CELERY_EAGER` (run jobs inline), `SDS_PUBLIC_WEB_URL` (consent links), `SDS_MESSAGING_PROVIDER` (only `console` exists until the SMS/WhatsApp provider is chosen), `SDS_ENVIRONMENT` (`dev`, `test`, `prod`). `SDS_RELAX_SCHEDULE=1` opens every session immediately in development.

The Android app reads its server addresses from `apps/mobile/app.json` (`extra.apiUrl`, default `http://10.0.2.2:8000`; `extra.modelsUrl`, default `http://10.0.2.2:5173/models`, both for the emulator). Set `SDS_API_URL` and `SDS_MODELS_URL` when building to override them; plain `http://` is allowed only when one of them uses it.

## Android app and on-device voice

The Android app has a small native module (`apps/mobile/modules/sds-voice/`, Kotlin) that reads the microphone at 16 kHz into memory and returns energy levels per 20 ms and, with a speech model, Vosk results with word timings. It needs a development or release build; in Expo Go the app still runs, with typed answers and silent reading.

```bash
./scripts/fetch-vosk-models.sh            # models + manifest.json into apps/web/public/models/ (served at /models/)
cd apps/mobile
npm run prebuild                          # generates android/ (not committed)
npm run android                           # debug build on an emulator or device (JS from Metro)
npm run android:release                   # standalone APK in android/app/build/outputs/apk/release/
```

When a parent has allowed voice, the app downloads the speech model for the student's language once (English about 36 MB, Hindi about 42 MB) from `SDS_MODELS_URL` and checks it against the SHA-256 in `manifest.json`. Until the model is ready, on phones with less than about 2.5 GB of memory, and for Hinglish, spoken answers get energy-based timing features only.

## Known limitations and next steps

* **Pilot calibration.** Normalisation ranges and the thresholds marked PILOT are placeholders; the relative profile works without norms, but evidence quality depends on pilot data.
* **SMS/WhatsApp provider** is a console stub pending the provider and DLT registration decision.
* **Android on a real phone.** The Android app is built and unit-tested in CI but has not yet been run on a device. Before a pilot: check voice on two or three low-cost phones, tune the energy threshold (`ANDROID_VAD` in `apps/mobile/src/voice/capture.ts`) and the memory limit for speech-to-text, and add `armeabi-v7a` to the build for 32-bit phones.
* **Answer keys ship in the session bundle** so the staircase works offline; the server re-checks every answer, so scores cannot be inflated, but a determined student could read the bundle.
* **Expert and legal review.** Wording, item content and the consent notice need the expert panel and legal review planned in phase 0 before any pilot.
