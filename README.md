# Rally Planner

A full-stack practice planner for volleyball coaches. Build a **drill library**, then assemble drills into **timed practice plans** and see at a glance whether the plan fits your practice length.

**Stack:** React 18 + Vite + React Router (frontend) · Flask + SQLAlchemy + Alembic (backend) · SQLite (relational database) · session-cookie authentication with bcrypt-hashed passwords.

![Plans page](docs/screenshots/plans.png)

## The problem it solves

Coaches plan practices in notes apps, spreadsheets or their heads. It is easy to run over time, repeat the same drills, or forget what you ran last week. Rally Planner keeps reusable drills in one place and shows planned minutes against the practice length while you build the plan.

## Features

- Sign up, log in, log out (sessions persist across page reloads)
- **Drills:** create, view, edit, delete; filter by category and skill level; search by name
- **Practice plans:** create, view, edit, delete; title, focus, date, target length, notes
- **Plan items:** add drills to a plan, edit minutes/notes per block, reorder with ↑/↓, remove
- Live "planned vs. target minutes" bar
- Loading, empty and error states everywhere; two-step confirm before deleting
- Responsive layout (desktop and phone)

## Data model

```
User 1 ──< Drill
User 1 ──< PracticePlan 1 ──< PlanDrill >── 1 Drill
```

| Table | Columns |
|---|---|
| `users` | id, username (unique), password_hash |
| `drills` | id, user_id, name, description, category, skill_level, default_minutes, equipment |
| `practice_plans` | id, user_id, title, focus, practice_date, target_minutes, notes |
| `plan_drills` | id, plan_id, drill_id, position, minutes, notes |

`plan_drills` links plans and drills (many-to-many) and stores the extra data for each use of a drill: its order, minutes and notes. Deleting a plan or a drill removes its `plan_drills` rows. Every query is scoped to the logged-in user, so one coach can never read or change another coach's data.

## Installation and setup

You need **Python 3.10+** and **Node 18+**. Open **two terminal tabs**.

### Tab 1: backend

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
hash -r
which python            # must print a path ending in server/.venv/bin/python
pip install -r requirements.txt
cp .env.example .env
flask --app app db upgrade   # creates the database tables
python seed.py               # optional demo data
flask --app app run --debug --port 5555
```

> If you see `No such command 'db'` or `ModuleNotFoundError`, the virtual environment is not active. Run `source .venv/bin/activate`, `hash -r`, check `which python`, then `pip install -r requirements.txt` again.

### Tab 2: frontend

```bash
cd client
npm install
npm run dev
```

Open **http://localhost:5173**. Demo login after seeding: `coach` / `volleyball123`, or sign up for a new account.

The Vite dev server forwards `/api` requests to Flask on port 5555, so the login cookie is same-origin and no CORS setup is needed.

### Run the tests

```bash
cd server
source .venv/bin/activate
python -m pytest -q
```

## API routes

All routes are under `/api`. Errors always return JSON: `{"error": "message"}`.

| Method | Route | What it does | Success |
|---|---|---|---|
| GET | `/health` | Is the backend running? | 200 |
| POST | `/signup` | Create account and log in | 201 |
| POST | `/login` | Log in | 200 |
| DELETE | `/logout` | Log out | 204 |
| GET | `/check_session` | Who is logged in? (`user: null` if nobody) | 200 |
| GET | `/drill-options` | Allowed categories and skill levels | 200 |
| GET | `/drills?category=&skill_level=&q=` | List my drills (filters optional) | 200 |
| POST | `/drills` | Create a drill | 201 |
| GET / PATCH / DELETE | `/drills/<id>` | Read / update / delete one drill | 200 / 200 / 204 |
| GET | `/plans` | List my plans (with totals) | 200 |
| POST | `/plans` | Create a plan | 201 |
| GET / PATCH / DELETE | `/plans/<id>` | Read (with items) / update / delete a plan | 200 / 200 / 204 |
| POST | `/plans/<id>/items` | Add a drill to a plan `{drill_id, minutes?, notes?}` | 201 |
| PATCH | `/plans/<id>/items/<item_id>` | Change minutes or notes | 200 |
| DELETE | `/plans/<id>/items/<item_id>` | Remove a drill from a plan | 200 |
| PUT | `/plans/<id>/items/order` | Reorder `{item_ids: [...]}` | 200 |

Status codes used for errors: 400 (body not JSON), 401 (not logged in), 404 (not found or not yours), 405, 409 (duplicate username or drill name), 422 (validation failed), 500.

## Project structure

```
server/
  app.py            app factory, error handlers, health check
  config.py         settings (secret key, database URL, cookies)
  extensions.py     db, migrate, bcrypt objects
  models.py         User, Drill, PracticePlan, PlanDrill + validation
  routes/           auth.py, drills.py, plans.py, helpers.py
  migrations/       Alembic database migrations
  seed.py           demo data
  tests/            30 pytest tests
client/src/
  api.js            every fetch call lives here
  context/AuthContext.jsx   logged-in user state
  hooks.js          useLoad (loading/error/data), useDebounced
  pages/            AuthPage, PlansPage, PlanDetailPage, DrillsPage, NotFound
  components/       NavBar, ProtectedRoute, DrillForm, PlanForm, TimeBar, ConfirmButton, StatusMessage
```

## Screenshots

| Plan builder | Drill library |
|---|---|
| ![Plan detail](docs/screenshots/plan-detail.png) | ![Drills](docs/screenshots/drills.png) |

| Phone layout | Login error handling |
|---|---|
| ![Mobile](docs/screenshots/mobile-plan.png) | ![Login error](docs/screenshots/login-error.png) |

## Known limitations / future ideas

- Reordering uses ↑/↓ buttons, not drag and drop.
- No password reset or email.
- SQLite is used for simplicity; set `DATABASE_URL` to use Postgres.
- Ideas: copy a plan, share a plan with assistant coaches, print view, attendance tracking.
