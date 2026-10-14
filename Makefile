# Common developer commands. Requires: uv, node 20+, Postgres 16, Redis.
.PHONY: install db test lint api worker web demo e2e mobile-check android-apk vectors

install:
	cd backend && uv sync
	npm install

db:  ## create local databases (sds, sds_test) for the sds/sds user
	createdb -U postgres -O sds sds || true
	createdb -U postgres -O sds sds_test || true

test:
	cd backend && uv run pytest
	npm run test

lint:
	cd backend && uv run ruff check . && uv run ruff format --check .
	npm run typecheck

api:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

worker:
	cd backend && SDS_CELERY_EAGER=false uv run celery -A app.workers.celery_app worker --beat --loglevel=info

web:
	npm run dev -w apps/web

demo:  ## demo school, consented students and completed cycles
	cd backend && uv run python -m app.cli demo

e2e:
	npm run e2e -w apps/web

mobile-check:
	cd apps/mobile && npm install && npx tsc --noEmit && npx expo export --platform android

# Needs the Android SDK and JDK 17+. The APK is in apps/mobile/android/app/build/outputs/apk/release/.
android-apk:
	cd apps/mobile && npm install && npm run prebuild && npm run android:release
