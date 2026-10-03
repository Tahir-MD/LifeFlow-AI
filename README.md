# LifeFlow

## Deploying on Streamlit (quick start)

This project now ships with a Streamlit front end (`streamlit_app.py`) that runs the
original FastAPI backend in the same process -- no separate server, no ports.

Run locally:

    pip install -r requirements.txt
    streamlit run streamlit_app.py

Deploy on Streamlit Community Cloud:

1. Push this whole folder to a GitHub repository (keep `streamlit_app.py` and
   `requirements.txt` at the repository root).
2. Go to https://share.streamlit.io -> New app -> pick the repo, branch, and set
   the main file to `streamlit_app.py`.
3. Open "Advanced settings -> Secrets" and paste (see `.streamlit/secrets.toml.example`):

       LIFEFLOW_SECRET_KEY = "a-long-random-string"
       # optional: LIFEFLOW_DATABASE_URL, GROQ_API_KEY

4. Deploy. First admin login: admin@lifeflow.com / Admin@123 (you must change it).

Important: Streamlit Cloud has an ephemeral disk, so the default SQLite file is wiped
whenever the app restarts or redeploys. For permanent data, create a free Postgres
database (Neon or Supabase), add `psycopg2-binary` to requirements.txt, and set
`LIFEFLOW_DATABASE_URL = "postgresql+psycopg2://user:pass@host/dbname"` in Secrets.

The original React frontend is still included in `frontend/` for reference, and
the backend still runs standalone with `uvicorn app.main:app` as described below.

---


LifeFlow connects blood donors with hospitals and with individual
patients who need blood directly. This project has two parts: a
backend that handles data and matching, and a frontend that people
use in the browser.

## Running the backend

1. Open a terminal and go into the backend folder.
   cd backend

2. Create a virtual environment and turn it on.
   python -m venv venv
   On Windows: venv\Scripts\activate
   On Mac or Linux: source venv/bin/activate

3. Install the required packages.
   pip install -r requirements.txt

4. Start the server.
   uvicorn app.main:app --reload

5. The backend is now running at
   http://127.0.0.1:8000

   You can view the automatic documentation and try every route at
   http://127.0.0.1:8000/docs

A file named lifeflow.db will be created automatically the first time
you run it. This is the database, and it needs no separate setup.

## Running the frontend

1. Open a second terminal and go into the frontend folder.
   cd frontend

2. Install the required packages.
   npm install

3. Start the development server.
   npm run dev

4. Open the address shown in the terminal, usually
   http://127.0.0.1:5173

The frontend expects the backend to be running at
http://127.0.0.1:8000

If you started the backend on a different port, open
frontend/src/services/api.js and change the BASE_URL value to match.

## The three kinds of accounts

Donor, a person who can give blood. Signs up with a blood type,
phone number, and location.

Patient, called a receiver in the code, a person who needs blood
directly for themselves or a family member, without going through a
hospital. Signs up with a phone number, CNIC number, and address, so
a donor can see exactly who they would be helping.

Hospital, a licensed institution. Signs up with a license number and
phone number.

## The admin account

There is also one built-in Admin account, used to see every donor,
hospital, and patient's full history in one place -- every request
(open, closed, or still waiting), every completed donation, and
every message/request notification ever sent, across all of them.

It is created automatically the first time the backend starts, with:

    email:    admin@lifeflow.com
    password: Admin@123

Log in at /admin/login on the frontend. Change
DEFAULT_ADMIN_PASSWORD in backend/app/main.py (or seed a different
one) before putting this online for real.

## Pop-up requests and full history

Every donor, hospital, and patient sees a notification bell in the
top bar, and a live pop-up appears the moment a new request or
message comes in, without needing to refresh. All of this -- and
every donation and request -- is saved permanently in the database
per account, so it is never lost: logging out and back in, even the
next day, shows exactly the same history, and it never mixes
between different users signed in on the same device.

## Hospital staff and shifts

A hospital can create a login for each staff member from its
dashboard ("Staff & shifts" tab), assigning them to one of four
fixed shifts: Shift 1, Shift 2, Shift 3, Shift 4. The hospital hands
that email and password to whoever is coming on duty.

Each staff member logs in separately, at /staff/login, and records
every donor or patient they attend to during their shift (name,
blood type, phone number, where they came from, and notes). This
builds up that staff member's own shift record, completely separate
from every other staff member's -- so at the end of their duty they
can review exactly how many donors and patients they saw, and print
or save it as a PDF (see below). The hospital can see the combined
record from every staff member and shift together, and the admin can
see every hospital's staff and every one of their shift records too.

## The 4 AI features

All four work out of the box with no setup, using fast rule-based
logic (regex/keyword extraction, weighted scoring, and a statistical
usage-trend projection) -- no external AI service, no cost, nothing
to configure. Two of them (the report analyzer and the chatbot) can
optionally be upgraded to a real large language model by setting one
environment variable; see "Optional: upgrading to a real LLM (Groq)"
below.

**1. AI Request Analyzer** -- on the "New request" tab (patient or
hospital), paste the text of a prescription, lab report, or referral
note into the "AI Request Analyzer" box and click "Analyze with AI".
It pulls out the blood type, units needed, hospital name, patient
name, and urgency, and offers to fill the request form with what it
found -- the person still reviews and submits the form themselves.
(`POST /ai/analyze-report`)

**2. AI Smart Donor Matching** -- every list of matching donors
(shown after creating a request) is ranked by a blended match score,
not just distance: an exact blood-type match is weighted higher than
a cross-compatible one (e.g. a universal O- donor), closer donors
score higher, and donors with a stronger donation history score
slightly higher too. Each donor shows their score and an "Exact
type" badge when relevant. (`GET /matching/{request_id}`)

**3. Blood Shortage Prediction** -- on a hospital's "AI Shortage
Prediction" tab (and from the admin dashboard, for any hospital),
each blood type is shown with its current stock, the average daily
usage from real donation history over the last 30 days, and a
projected number of days of supply remaining -- bucketed into
🟢 Stable / 🟡 May become low / 🔴 Critical. This is a transparent
moving-average projection, not a trained model, so it works
immediately even for a brand-new hospital with no history yet.
(`GET /ai/shortage-prediction`, `GET /admin/hospital/{id}/shortage-prediction`)

**4. AI Chatbot** -- also on the "New request" tab, the "AI Chatbot"
box lets a person describe what they need in plain language (English
or common Roman Urdu phrases like "chahiye" / "zarurat" / "emergency"),
one message at a time. It asks for whatever is still missing (blood
type, units, hospital, contact number) and, once everything is
filled in, offers to carry those details into the request form below
for the person to review and submit. It never creates a request by
itself. (`POST /ai/chat`)

### Optional: upgrading to a real LLM (Groq)

By default, the report analyzer and chatbot understand text using
built-in rules (regex and keyword matching), so they work immediately
with no setup and no cost. To upgrade their free-text understanding
to a real language model, get a free API key at
https://console.groq.com and set it as an environment variable before
starting the backend:

    export GROQ_API_KEY=your-key-here

That's the only step -- no package to install (it's a plain REST
call using Python's standard library) and no code to change. Leaving
it unset is completely safe; the app falls back to the rule-based
engine automatically. See `backend/app/services/llm_client.py` for
details, including how to pick a different Groq model via
`GROQ_MODEL`.

## The floating AI assistant

A robot-icon button sits in the bottom-right corner on every page,
including the signed-out home page. It's the same guided chatbot
described above (feature 4) -- click it, describe what's needed, and
once every required detail is collected it offers to carry those
details into the right request form, taking the person to the
patient or hospital dashboard to review and submit it themselves.

## Signing up, from the login page

The top navigation only shows "Donor login" / "Patient login" /
"Hospital login" now, to keep it simple. Each login page has a "New
here? Sign up" link at the bottom for anyone who isn't registered
yet, which goes to that role's sign-up form.

## Admin password, set on first login

The seeded admin account (see "The admin account" above) is the same
on every fresh install, so the first time anyone logs in with it,
LifeFlow requires setting a new password before the dashboard is
reachable -- this matters because every hospital that installs this
project would otherwise share the exact same default login. After
that first change, the admin logs in with their own password as
normal. (`POST /auth/admin/change-password`)

## Saving and printing any history as a PDF

Every history view across the site -- a donor's donations, a
hospital's or patient's requests, a staff member's shift record, and
every admin view -- has a "Print / Save as PDF" button. It opens the
browser's normal print dialog; choosing "Save as PDF" there saves
that exact record as a PDF file, or it can be sent straight to a
printer. No extra software is needed.

## Trying it out

1. Open the frontend in the browser.
2. Sign up as a donor with a blood type, phone number, and location.
3. Sign up as a patient, or as a hospital, whichever you want to try.
4. Log in as the patient or hospital and create a request, choosing
   how many bags are needed and how soon, either an emergency, a
   number of days, or a number of months.
5. You will see the list of matching donors, ranked by distance,
   each with a phone number.
6. Log in as the donor and see the open request, showing the
   requester's name, phone number, and, for a patient request, their
   CNIC number and address.
7. Choose how many bags you can give and accept. If the request
   needed more bags than you gave, it stays open for another donor
   to cover the rest. Once every bag is covered, the request closes
   and disappears from the open list.

## Project layout

backend, the Python server built with FastAPI. Handles sign up,
login, requests, and the matching logic for all three account types.

frontend, the React website. Lets donors, patients, and hospitals
sign up, log in, create requests, and see matches.

## What is included in this version

Sign up and login for donors, patients, and hospitals, with secure
passwords and login tokens. Emergency and scheduled blood requests,
in bags, with an urgency timeframe. Matching by blood type
compatibility, distance, and eligibility, with contact numbers shown
on both sides. A request can be filled by more than one donor if
no single donor covers every bag needed. Points for donors based on
how many bags they give.

On top of that original core, this version adds:

- **Full donation history on every dashboard.** A donor sees every
  bag they gave and exactly who received it (hospital or patient,
  with phone number, and CNIC and address for a patient). A hospital
  or patient sees every donation they received, with the donor's
  full name, blood type, phone number, and the date and time.
- **In-app notifications.** Every account has a notification bell.
  Donors are notified the moment a compatible request opens nearby;
  hospitals and patients are notified the moment a donor accepts;
  everyone is notified about new donation camps. This stands in for
  the SMS/email/push alerts a production deployment would send
  through a provider such as Twilio or SendGrid.
- **Two-way ratings.** After a donation, the requester can rate the
  donor and the donor can rate the requester, building a visible
  reputation for both sides.
- **Donor badges, points, and a public leaderboard.** Donors earn a
  tier (Bronze through Platinum Lifesaver) based on total donations,
  and can see their community rank.
- **Hospital blood bank inventory.** Hospitals track how many bags of
  each blood type they currently hold, with a low stock warning.
- **Donation camps / blood drives.** Hospitals can organize and
  publish a camp; donors are notified and can register; hospitals see
  the full list of registered donors with contact details.
- **Per-role stats dashboards.** Donors see total donations, bags
  given, estimated lives impacted, and next eligible donation date.
  Hospitals and patients see total, open, and fulfilled requests and
  total bags received.

## What is not included yet

Real SMS/email delivery (Twilio, SendGrid, or similar), push
notifications to a mobile app, offline mode, shortage prediction,
permanent tamper proof records, multi-language support, and a formal
admin/verification panel for licensing hospitals and confirming
donor eligibility with a medical provider. A production deployment
would also replace SQLite with PostgreSQL and add Alembic migrations
before the schema changes in this version, since `Base.metadata.create_all`
only creates tables that do not exist yet - if you already have a
`lifeflow.db` from an earlier version, delete it before running this
one so the new tables and columns are created fresh.
