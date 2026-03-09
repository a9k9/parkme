# ParkMe

Unified workspace for the ParkMe backend and frontend.

## Services

- Backend (Django API): http://localhost:8000
- Frontend (Vite): http://localhost:5173

## Docker

Run everything from the repo root:

- `docker compose up --build -d`

Optional migrations:

- `docker compose run --rm migrate`

## Local development (without Docker)

### Backend

- From backend/: use the existing Python venv and run `make run`.

### Frontend

- From frontend/: `pnpm install` then `pnpm dev`.

## Notes

- The frontend expects the API at $VITE_API_BASE_URL (defaults to http://localhost:8000).
- Seed data can be generated in Docker: `docker compose exec web python manage.py seed_parking --reset --facilities 10 --zones-per-facility 5 --spots-per-zone 30`.
