"""
LifeFlow - Streamlit front end.

The original FastAPI backend (backend/app) is reused unchanged. It is
run *inside* this Streamlit process through FastAPI's TestClient, so no
separate server or port is needed -- ideal for Streamlit Community Cloud.
"""
import os
import sys
from datetime import datetime, time as dtime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent.resolve()
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# ---- Secrets -> environment (must happen before the backend is imported) ----
for _key in ("LIFEFLOW_SECRET_KEY", "LIFEFLOW_DATABASE_URL", "GROQ_API_KEY", "GROQ_MODEL"):
    try:
        if _key in st.secrets:
            os.environ[_key] = str(st.secrets[_key])
    except Exception:
        pass
os.environ.setdefault("LIFEFLOW_DATABASE_URL", f"sqlite:///{ROOT / 'lifeflow.db'}")

st.set_page_config(page_title="LifeFlow", page_icon="🩸", layout="wide")

BLOOD_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"]
SHIFTS = ["Shift 1", "Shift 2", "Shift 3", "Shift 4"]


@st.cache_resource(show_spinner="Starting LifeFlow...")
def get_client():
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


client = get_client()


# ------------------------------------------------------------------ helpers
def api(method, path, token=None, json=None, params=None, quiet=False):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = client.request(method, path, headers=headers, json=json, params=params)
    except Exception as exc:  # pragma: no cover
        if not quiet:
            st.error(f"Request failed: {exc}")
        return None
    if r.status_code >= 400:
        if not quiet:
            try:
                detail = r.json().get("detail")
            except Exception:
                detail = r.text
            if isinstance(detail, list):
                detail = "; ".join(f"{'.'.join(map(str, d.get('loc', [])[1:]))}: {d.get('msg')}" for d in detail)
            st.error(str(detail))
        return None
    if r.status_code == 204 or not r.content:
        return True
    return r.json()


def S():
    return st.session_state


def init_state():
    S().setdefault("role", None)
    S().setdefault("token", None)
    S().setdefault("must_change", False)
    S().setdefault("chat", [])
    S().setdefault("chat_slots", None)
    S().setdefault("prefill", {})


def logout():
    for k in ("role", "token", "must_change", "chat", "chat_slots", "prefill"):
        S().pop(k, None)
    init_state()
    st.rerun()


def fmt_dt(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "")).strftime("%d %b %Y, %H:%M")
    except Exception:
        return str(v)


def show_table(rows, columns=None, rename=None, key=None):
    if not rows:
        st.info("Nothing here yet.")
        return
    df = pd.DataFrame(rows)
    for c in df.columns:
        if "date" in c or c.endswith("_at"):
            df[c] = df[c].map(fmt_dt)
    if columns:
        df = df[[c for c in columns if c in df.columns]]
    if rename:
        df = df.rename(columns=rename)
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button("⬇️ Download CSV", df.to_csv(index=False).encode(), file_name="lifeflow_export.csv",
                       mime="text/csv", key=f"dl_{key or id(rows)}")


def urgency_payload(prefix):
    kind = st.selectbox("How soon is it needed?", ["emergency", "days", "months"], key=f"{prefix}_ut")
    value = None
    if kind != "emergency":
        value = st.number_input(f"Number of {kind}", min_value=1, value=3, key=f"{prefix}_uv")
    return kind, (int(value) if value else None)


# ------------------------------------------------------------- shared pieces
def platform_stats():
    data = api("GET", "/stats/platform", quiet=True)
    if not data:
        return
    c = st.columns(5)
    c[0].metric("Donors", data["total_donors"])
    c[1].metric("Hospitals", data["total_hospitals"])
    c[2].metric("Patients", data["total_patients_helped"])
    c[3].metric("Bags donated", data["total_units_donated"])
    c[4].metric("Requests fulfilled", data["total_requests_fulfilled"])


def leaderboard_view():
    rows = api("GET", "/leaderboard/donors", quiet=True) or []
    show_table(rows, ["rank", "full_name", "blood_type", "points", "total_donations", "badge_tier"],
               {"rank": "Rank", "full_name": "Donor", "blood_type": "Blood", "points": "Points",
                "total_donations": "Donations", "badge_tier": "Badge"}, key="lb")


def inventory_public_view():
    data = api("GET", "/inventory", quiet=True) or []
    if not data:
        st.info("No hospital has published stock yet.")
    for h in data:
        with st.expander(f"🏥 {h['hospital_name']}"):
            cols = st.columns(8)
            for col, it in zip(cols, h["items"]):
                col.metric(it["blood_type"], it["units_available"], "LOW" if it["is_low"] else None,
                           delta_color="inverse")


def camps_public_view():
    camps = api("GET", "/camps", quiet=True) or []
    show_table(camps, ["title", "hospital_name", "location_label", "camp_date", "registered_count"],
               {"title": "Camp", "hospital_name": "Hospital", "location_label": "Location",
                "camp_date": "Date", "registered_count": "Registered"}, key="camps_pub")


def chatbot_widget(key="chat"):
    """Guided chatbot (POST /ai/chat). Fills S().prefill when ready."""
    for m in S().chat:
        with st.chat_message(m["role"]):
            st.write(m["text"])
    msg = st.chat_input("Describe what blood you need (e.g. 'Need 2 bags of B+ urgently at City Hospital')",
                        key=f"{key}_input")
    if msg:
        S().chat.append({"role": "user", "text": msg})
        res = api("POST", "/ai/chat", json={"message": msg, "slots": S().chat_slots})
        if res:
            S().chat_slots = res["slots"]
            S().chat.append({"role": "assistant", "text": res["reply"]})
            if res.get("ready_to_submit"):
                sl = res["slots"]
                S().prefill = {
                    "blood_type": sl.get("blood_type"), "units": sl.get("units"),
                    "urgency_type": sl.get("urgency_type"), "urgency_value": sl.get("urgency_value"),
                    "patient_name": sl.get("patient_name"),
                }
        st.rerun()
    if S().prefill:
        st.success(f"Chatbot collected: {S().prefill}. These values are pre-filled in the request form.")
    if S().chat and st.button("Reset chat", key=f"{key}_reset"):
        S().chat, S().chat_slots, S().prefill = [], None, {}
        st.rerun()


def analyzer_widget():
    text = st.text_area("Paste a prescription / lab report / referral note", height=140, key="an_text")
    if st.button("Analyze with AI", key="an_btn") and text.strip():
        res = api("POST", "/ai/analyze-report", json={"report_text": text})
        if res:
            st.json({k: v for k, v in res.items() if v not in (None, [], "")})
            S().prefill = {
                "blood_type": res.get("blood_type"), "units": res.get("units"),
                "urgency_type": res.get("urgency_type"), "urgency_value": res.get("urgency_value"),
                "patient_name": res.get("patient_name"),
            }
            st.success("Form below pre-filled with what was found. Review and submit.")


def request_form(role, token, defaults_lat=0.0, defaults_lon=0.0):
    pf = S().prefill or {}
    bt_default = pf.get("blood_type") if pf.get("blood_type") in BLOOD_TYPES else "O+"
    with st.form("new_request"):
        c1, c2 = st.columns(2)
        blood = c1.selectbox("Blood type needed", BLOOD_TYPES, index=BLOOD_TYPES.index(bt_default))
        units = c2.number_input("Bags needed", min_value=1, max_value=20, value=int(pf.get("units") or 1))
        patient = st.text_input("Patient name", value=pf.get("patient_name") or "")
        ut = st.selectbox("How soon?", ["emergency", "days", "months"],
                          index=["emergency", "days", "months"].index(pf.get("urgency_type") or "emergency"))
        uv = st.number_input("If days/months: how many?", min_value=0, value=int(pf.get("urgency_value") or 0))
        c3, c4 = st.columns(2)
        lat = c3.number_input("Latitude", value=float(defaults_lat), format="%.5f")
        lon = c4.number_input("Longitude", value=float(defaults_lon), format="%.5f")
        go = st.form_submit_button("🩸 Create request", type="primary")
    if go:
        payload = {"blood_type_needed": blood, "units_needed": int(units), "patient_name": patient or None,
                   "urgency_type": ut, "urgency_value": int(uv) if ut != "emergency" and uv else None,
                   "latitude": lat, "longitude": lon}
        res = api("POST", f"/requests/{role}", token, json=payload)
        if res:
            S().prefill = {}
            st.success(f"Request #{res['id']} created. Matching donors have been notified.")
            matches = api("GET", f"/matching/{res['id']}") or []
            st.subheader("Matching donors")
            show_table(matches, ["full_name", "blood_type", "phone_number", "distance_kilometers",
                                 "match_score", "is_exact_match", "availability_label"],
                       {"full_name": "Donor", "blood_type": "Blood", "phone_number": "Phone",
                        "distance_kilometers": "km", "match_score": "Score", "is_exact_match": "Exact type",
                        "availability_label": "Status"}, key=f"match_{res['id']}")


def notifications_view(role, token):
    items = api("GET", f"/notifications/{role}", token) or []
    unread = sum(1 for n in items if not n["is_read"])
    st.write(f"**{unread} unread** of {len(items)}")
    if unread and st.button("Mark all as read", key=f"readall_{role}"):
        api("POST", f"/notifications/{role}/read-all", token)
        st.rerun()
    for n in items:
        icon = "🔵" if not n["is_read"] else "⚪"
        st.markdown(f"{icon} **{n['title']}** — {n['message']}  \n<small>{fmt_dt(n['created_at'])}</small>",
                    unsafe_allow_html=True)


def history_requests(role, token):
    rows = api("GET", f"/requests/{role}/history", token) or []
    show_table(rows, ["id", "blood_type_needed", "units_needed", "units_fulfilled", "status",
                      "urgency_type", "patient_name", "created_at"],
               {"id": "ID", "blood_type_needed": "Blood", "units_needed": "Needed",
                "units_fulfilled": "Given", "status": "Status", "urgency_type": "Urgency",
                "patient_name": "Patient", "created_at": "Created"}, key=f"rh_{role}")
    return rows


def donations_received(role, token):
    rows = api("GET", f"/donations/{role}/history", token) or []
    show_table(rows, ["donation_id", "donor_name", "donor_blood_type", "donor_phone", "units_donated", "donated_at"],
               {"donation_id": "ID", "donor_name": "Donor", "donor_blood_type": "Blood",
                "donor_phone": "Phone", "units_donated": "Bags", "donated_at": "When"}, key=f"dr_{role}")
    if rows:
        st.markdown("##### Rate a donor")
        opts = {f"#{r['donation_id']} — {r['donor_name']} ({r['units_donated']} bag)": r["donation_id"] for r in rows}
        pick = st.selectbox("Donation", list(opts), key=f"rate_pick_{role}")
        stars = st.slider("Stars", 1, 5, 5, key=f"rate_stars_{role}")
        comment = st.text_input("Comment (optional)", key=f"rate_c_{role}")
        if st.button("Submit rating", key=f"rate_go_{role}"):
            if api("POST", f"/ratings/{opts[pick]}/rate-donor", token, json={"stars": stars, "comment": comment or None}):
                st.success("Thanks for rating!")


# ------------------------------------------------------------------- pages
def page_home():
    st.title("🩸 LifeFlow")
    st.caption("Connecting blood donors with hospitals and patients who need blood.")
    platform_stats()
    t1, t2, t3, t4 = st.tabs(["🤖 AI assistant", "🏆 Leaderboard", "🏥 Blood stock", "📅 Donation camps"])
    with t1:
        st.write("Describe what you need; once everything is collected, log in as a patient or hospital to submit it.")
        chatbot_widget("home_chat")
    with t2:
        leaderboard_view()
    with t3:
        inventory_public_view()
    with t4:
        camps_public_view()


def auth_page(role_label, role_key, login_path, register_fn, is_admin=False):
    st.header(f"{role_label} access")
    tabs = st.tabs(["Log in"] + ([] if is_admin or register_fn is None else ["Sign up"]))
    with tabs[0]:
        with st.form(f"login_{role_key}"):
            email = st.text_input("Email")
            pwd = st.text_input("Password", type="password")
            ok = st.form_submit_button("Log in", type="primary")
        if ok:
            res = api("POST", login_path, json={"email": email, "password": pwd})
            if res:
                S().role, S().token = role_key, res["access_token"]
                S().must_change = bool(res.get("must_change_password"))
                st.rerun()
    if len(tabs) > 1:
        with tabs[1]:
            register_fn()


def reg_donor():
    with st.form("reg_donor"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        blood = st.selectbox("Blood type", BLOOD_TYPES)
        phone = st.text_input("Phone number")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=31.5204, format="%.5f")
        lon = c2.number_input("Longitude", value=74.3587, format="%.5f")
        go = st.form_submit_button("Create donor account", type="primary")
    if go:
        if api("POST", "/auth/register/donor", json=dict(full_name=name, email=email, password=pwd,
                                                         blood_type=blood, phone_number=phone,
                                                         latitude=lat, longitude=lon)):
            st.success("Account created. Switch to the Log in tab.")


def reg_receiver():
    with st.form("reg_receiver"):
        name = st.text_input("Full name")
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        phone = st.text_input("Phone number")
        cnic = st.text_input("CNIC number")
        addr = st.text_input("Address")
        patient = st.text_input("Patient name (if for someone else)")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=31.5204, format="%.5f")
        lon = c2.number_input("Longitude", value=74.3587, format="%.5f")
        go = st.form_submit_button("Create patient account", type="primary")
    if go:
        if api("POST", "/auth/register/receiver", json=dict(full_name=name, email=email, password=pwd,
                                                            phone_number=phone, cnic_number=cnic, address=addr,
                                                            patient_name=patient or None, latitude=lat,
                                                            longitude=lon)):
            st.success("Account created. Switch to the Log in tab.")


def reg_hospital():
    with st.form("reg_hospital"):
        name = st.text_input("Hospital name")
        email = st.text_input("Email")
        pwd = st.text_input("Password", type="password")
        lic = st.text_input("License number")
        phone = st.text_input("Phone number")
        c1, c2 = st.columns(2)
        lat = c1.number_input("Latitude", value=31.5204, format="%.5f")
        lon = c2.number_input("Longitude", value=74.3587, format="%.5f")
        go = st.form_submit_button("Create hospital account", type="primary")
    if go:
        if api("POST", "/auth/register/hospital", json=dict(name=name, email=email, password=pwd,
                                                            license_number=lic, phone_number=phone,
                                                            latitude=lat, longitude=lon)):
            st.success("Account created. Switch to the Log in tab.")


# ---- Donor dashboard
def dash_donor():
    tok = S().token
    me = api("GET", "/donors/me", tok)
    if not me:
        return logout()
    stats = api("GET", "/donors/me/stats", tok) or {}
    st.title(f"🩸 Welcome, {me['full_name']}")
    c = st.columns(5)
    c[0].metric("Blood type", me["blood_type"])
    c[1].metric("Donations", stats.get("total_donations", 0))
    c[2].metric("Bags given", stats.get("total_units_donated", 0))
    c[3].metric("Points", stats.get("points", 0))
    c[4].metric("Rank", f"#{stats.get('leaderboard_rank')}" if stats.get("leaderboard_rank") else "-")
    st.caption(f"Badge: **{stats.get('badge_tier')}** · Lives impacted ≈ {stats.get('estimated_lives_impacted', 0)} · "
               + ("✅ Eligible to donate now" if stats.get("is_eligible_now")
                  else f"⏳ Next eligible: {fmt_dt(stats.get('next_eligible_date'))}"))

    tabs = st.tabs(["Open requests", "My donations", "Camps", "Notifications", "Leaderboard", "Blood stock"])
    with tabs[0]:
        reqs = [r for r in (api("GET", "/requests") or []) if r["status"] == "open"]
        if not reqs:
            st.info("No open requests right now.")
        for r in reqs:
            tag = "🚨 EMERGENCY" if r["urgency_type"] == "emergency" else f"⏱ {r['urgency_value']} {r['urgency_type']}"
            with st.expander(f"#{r['id']} · {r['blood_type_needed']} · {r['units_remaining']} bag(s) left · {tag} · {r['requester_name']}"):
                st.write(f"**Requester:** {r['requester_name']} ({r['requester_type']}) · 📞 {r['requester_phone']}")
                if r.get("requester_cnic"):
                    st.write(f"**CNIC:** {r['requester_cnic']} · **Address:** {r['requester_address']}")
                if r.get("patient_name"):
                    st.write(f"**Patient:** {r['patient_name']}")
                n = st.number_input("Bags you can give", 1, max(r["units_remaining"], 1), 1, key=f"acc_n_{r['id']}")
                if st.button("✅ Accept & donate", key=f"acc_{r['id']}", type="primary"):
                    res = api("POST", f"/matching/{r['id']}/accept", tok, json={"units_donated": int(n)})
                    if res:
                        st.success(res["message"] + f" Contact {res['requester_name']}: {res['requester_phone']}")
                        st.rerun()
    with tabs[1]:
        rows = api("GET", "/donations/donor/history", tok) or []
        show_table(rows, ["donation_id", "requester_name", "requester_phone", "requester_cnic", "requester_address",
                          "blood_type_needed", "units_donated", "donated_at"],
                   {"donation_id": "ID", "requester_name": "Recipient", "requester_phone": "Phone",
                    "requester_cnic": "CNIC", "requester_address": "Address", "blood_type_needed": "Blood",
                    "units_donated": "Bags", "donated_at": "When"}, key="dh")
        if rows:
            st.markdown("##### Rate the recipient")
            opts = {f"#{r['donation_id']} — {r['requester_name']}": r["donation_id"] for r in rows}
            pick = st.selectbox("Donation", list(opts), key="dr_pick")
            stars = st.slider("Stars", 1, 5, 5, key="dr_stars")
            cm = st.text_input("Comment (optional)", key="dr_c")
            if st.button("Submit rating", key="dr_go"):
                if api("POST", f"/ratings/{opts[pick]}/rate-requester", tok, json={"stars": stars, "comment": cm or None}):
                    st.success("Thanks for rating!")
    with tabs[2]:
        camps = api("GET", "/camps") or []
        mine = {r["camp_id"] for r in (api("GET", "/camps/mine/rsvps", tok) or [])}
        if not camps:
            st.info("No upcoming camps.")
        for cp in camps:
            with st.expander(f"{cp['title']} · {cp['hospital_name']} · {fmt_dt(cp['camp_date'])}"):
                st.write(f"📍 {cp['location_label']}")
                if cp.get("description"):
                    st.write(cp["description"])
                st.caption(f"{cp['registered_count']} donor(s) registered")
                if cp["id"] in mine:
                    st.success("You are registered ✔")
                elif st.button("Register for this camp", key=f"rsvp_{cp['id']}"):
                    if api("POST", f"/camps/{cp['id']}/rsvp", tok):
                        st.rerun()
    with tabs[3]:
        notifications_view("donor", tok)
    with tabs[4]:
        leaderboard_view()
    with tabs[5]:
        inventory_public_view()


# ---- Receiver dashboard
def dash_receiver():
    tok = S().token
    me = api("GET", "/receivers/me", tok)
    if not me:
        return logout()
    stats = api("GET", "/receivers/me/stats", tok) or {}
    st.title(f"🧑‍⚕️ Welcome, {me['full_name']}")
    c = st.columns(4)
    c[0].metric("Requests", stats.get("total_requests", 0))
    c[1].metric("Open", stats.get("open_requests", 0))
    c[2].metric("Fulfilled", stats.get("fulfilled_requests", 0))
    c[3].metric("Bags received", stats.get("total_units_received", 0))
    tabs = st.tabs(["New request", "My requests", "Donations received", "Notifications", "Blood stock", "Camps"])
    with tabs[0]:
        with st.expander("🤖 AI Request Analyzer"):
            analyzer_widget()
        with st.expander("💬 AI Chatbot"):
            chatbot_widget("rx_chat")
        request_form("receiver", tok, me["latitude"], me["longitude"])
    with tabs[1]:
        history_requests("receiver", tok)
    with tabs[2]:
        donations_received("receiver", tok)
    with tabs[3]:
        notifications_view("receiver", tok)
    with tabs[4]:
        inventory_public_view()
    with tabs[5]:
        camps_public_view()


# ---- Hospital dashboard
def dash_hospital():
    tok = S().token
    me = api("GET", "/hospitals/me", tok)
    if not me:
        return logout()
    stats = api("GET", "/hospitals/me/stats", tok) or {}
    st.title(f"🏥 {me['name']}")
    c = st.columns(4)
    c[0].metric("Requests", stats.get("total_requests", 0))
    c[1].metric("Open", stats.get("open_requests", 0))
    c[2].metric("Fulfilled", stats.get("fulfilled_requests", 0))
    c[3].metric("Bags received", stats.get("total_units_received", 0))
    if stats.get("low_stock_types"):
        st.warning("Low stock: " + ", ".join(stats["low_stock_types"]))
    tabs = st.tabs(["New request", "My requests", "Donations received", "Blood inventory",
                    "AI shortage prediction", "Camps", "Staff & shifts", "Notifications"])
    with tabs[0]:
        with st.expander("🤖 AI Request Analyzer"):
            analyzer_widget()
        with st.expander("💬 AI Chatbot"):
            chatbot_widget("hp_chat")
        request_form("hospital", tok, me["latitude"], me["longitude"])
    with tabs[1]:
        history_requests("hospital", tok)
    with tabs[2]:
        donations_received("hospital", tok)
    with tabs[3]:
        inv = api("GET", "/inventory/me", tok) or []
        show_table(inv, ["blood_type", "units_available", "low_stock_threshold", "is_low", "updated_at"],
                   {"blood_type": "Blood", "units_available": "Units", "low_stock_threshold": "Low threshold",
                    "is_low": "Low?", "updated_at": "Updated"}, key="inv")
        with st.form("inv_form"):
            c1, c2, c3 = st.columns(3)
            bt = c1.selectbox("Blood type", BLOOD_TYPES)
            units = c2.number_input("Units available", min_value=0, value=0)
            thr = c3.number_input("Low-stock threshold", min_value=0, value=5)
            if st.form_submit_button("Update stock", type="primary"):
                if api("PUT", "/inventory/me", tok, json={"blood_type": bt, "units_available": int(units),
                                                           "low_stock_threshold": int(thr)}):
                    st.rerun()
    with tabs[4]:
        pred = api("GET", "/ai/shortage-prediction", tok) or []
        show_table(pred, ["blood_type", "units_available", "avg_daily_consumption", "projected_days_remaining",
                          "risk_label"],
                   {"blood_type": "Blood", "units_available": "Stock", "avg_daily_consumption": "Avg/day (30d)",
                    "projected_days_remaining": "Days left", "risk_label": "Risk"}, key="pred")
    with tabs[5]:
        mine = api("GET", "/camps/mine", tok) or []
        for cp in mine:
            with st.expander(f"{cp['title']} · {fmt_dt(cp['camp_date'])} · {cp['registered_count']} registered"):
                rs = api("GET", f"/camps/{cp['id']}/rsvps", tok) or []
                show_table(rs, ["donor_name", "donor_blood_type", "donor_phone", "status", "created_at"], key=f"rs{cp['id']}")
        st.markdown("##### Organize a new camp")
        with st.form("camp_form"):
            title = st.text_input("Title")
            desc = st.text_area("Description")
            loc = st.text_input("Location label")
            d = st.date_input("Date", value=datetime.now().date() + timedelta(days=7))
            c1, c2 = st.columns(2)
            lat = c1.number_input("Latitude", value=float(me["latitude"]), format="%.5f")
            lon = c2.number_input("Longitude", value=float(me["longitude"]), format="%.5f")
            if st.form_submit_button("Publish camp", type="primary"):
                if api("POST", "/camps", tok, json={"title": title, "description": desc or None, "location_label": loc,
                                                   "latitude": lat, "longitude": lon,
                                                   "camp_date": datetime.combine(d, dtime(9, 0)).isoformat()}):
                    st.success("Camp published; donors were notified.")
                    st.rerun()
    with tabs[6]:
        staff = api("GET", "/staff", tok) or []
        show_table(staff, ["full_name", "email", "shift", "phone_number"], key="staff_list")
        for s in staff:
            if st.button(f"Remove {s['full_name']}", key=f"rm_{s['id']}"):
                api("DELETE", f"/staff/{s['id']}", tok)
                st.rerun()
        with st.form("staff_form"):
            st.markdown("##### Create staff login")
            c1, c2 = st.columns(2)
            n = c1.text_input("Full name")
            e = c2.text_input("Email")
            p = c1.text_input("Password", type="password")
            sh = c2.selectbox("Shift", SHIFTS)
            ph = st.text_input("Phone (optional)")
            if st.form_submit_button("Create staff", type="primary"):
                if api("POST", "/staff", tok, json={"full_name": n, "email": e, "password": p, "shift": sh,
                                                   "phone_number": ph or None}):
                    st.rerun()
        st.markdown("##### Combined visitor record (all shifts)")
        v = api("GET", "/staff/hospital/visitors", tok) or []
        show_table(v, ["logged_at", "staff_name", "staff_shift", "visitor_type", "full_name", "blood_type",
                       "phone_number", "from_location", "notes"], key="hv")
    with tabs[7]:
        notifications_view("hospital", tok)


# ---- Staff dashboard
def dash_staff():
    tok = S().token
    me = api("GET", "/staff/me", tok)
    if not me:
        return logout()
    st.title(f"🧑‍⚕️ {me['full_name']} — {me['shift']}")
    t1, t2 = st.tabs(["Log a visitor", "My shift record"])
    with t1:
        with st.form("visitor"):
            vt = st.radio("Type", ["donor", "patient"], horizontal=True)
            c1, c2 = st.columns(2)
            nm = c1.text_input("Full name")
            bt = c2.selectbox("Blood type", [""] + BLOOD_TYPES)
            ph = c1.text_input("Phone")
            fl = c2.text_input("Came from")
            nt = st.text_area("Notes")
            if st.form_submit_button("Save entry", type="primary"):
                if api("POST", "/staff/visitors", tok, json={"visitor_type": vt, "full_name": nm,
                                                            "blood_type": bt or None, "phone_number": ph or None,
                                                            "from_location": fl or None, "notes": nt or None}):
                    st.success("Logged.")
    with t2:
        rows = api("GET", "/staff/visitors/mine", tok) or []
        c = st.columns(2)
        c[0].metric("Donors seen", sum(1 for r in rows if r["visitor_type"] == "donor"))
        c[1].metric("Patients seen", sum(1 for r in rows if r["visitor_type"] == "patient"))
        show_table(rows, ["logged_at", "visitor_type", "full_name", "blood_type", "phone_number", "from_location",
                          "notes"], key="mine_v")


# ---- Admin dashboard
def dash_admin():
    tok = S().token
    if S().must_change:
        st.title("🔐 Set a new admin password")
        st.info("This is the default admin account. Choose a new password before continuing.")
        with st.form("chgpw"):
            cur = st.text_input("Current password", type="password")
            new = st.text_input("New password (min 8 chars)", type="password")
            if st.form_submit_button("Update password", type="primary"):
                if api("POST", "/auth/admin/change-password", tok,
                       json={"current_password": cur, "new_password": new}):
                    S().must_change = False
                    st.rerun()
        return
    st.title("🛡️ Admin")
    platform_stats()
    tabs = st.tabs(["Donors", "Hospitals", "Patients", "Requests", "Donations", "Notifications",
                    "Staff & shifts", "Shortage prediction"])
    with tabs[0]:
        show_table(api("GET", "/admin/donors", tok) or [], ["id", "full_name", "email", "blood_type", "phone_number",
                                                           "points", "last_donation_date"], key="a_d")
    with tabs[1]:
        show_table(api("GET", "/admin/hospitals", tok) or [], ["id", "name", "email", "license_number",
                                                              "phone_number"], key="a_h")
    with tabs[2]:
        show_table(api("GET", "/admin/receivers", tok) or [], ["id", "full_name", "email", "phone_number",
                                                              "cnic_number", "address"], key="a_r")
    with tabs[3]:
        show_table(api("GET", "/admin/requests", tok) or [], ["id", "requester_type", "requester_name",
                                                             "blood_type_needed", "units_needed", "units_fulfilled",
                                                             "status", "urgency_type", "created_at"], key="a_q")
    with tabs[4]:
        show_table(api("GET", "/admin/donations", tok) or [], ["donation_id", "donor_name", "requester_name",
                                                              "blood_type_needed", "units_donated", "donated_at"],
                   key="a_dn")
    with tabs[5]:
        show_table(api("GET", "/admin/notifications", tok) or [], ["created_at", "user_type", "user_id", "title",
                                                                  "message"], key="a_n")
    with tabs[6]:
        staff = api("GET", "/admin/staff", tok) or []
        show_table(staff, ["id", "hospital_id", "full_name", "email", "shift"], key="a_s")
        if staff:
            opts = {f"{s['full_name']} ({s['shift']}, hospital {s['hospital_id']})": s["id"] for s in staff}
            pick = st.selectbox("View a staff member's shift record", list(opts))
            show_table(api("GET", f"/admin/staff/{opts[pick]}/visitors", tok) or [],
                       ["logged_at", "visitor_type", "full_name", "blood_type", "phone_number", "from_location",
                        "notes"], key="a_sv")
    with tabs[7]:
        hs = api("GET", "/admin/hospitals", tok) or []
        if hs:
            opts = {h["name"]: h["id"] for h in hs}
            pick = st.selectbox("Hospital", list(opts))
            show_table(api("GET", f"/admin/hospital/{opts[pick]}/shortage-prediction", tok) or [],
                       ["blood_type", "units_available", "avg_daily_consumption", "projected_days_remaining",
                        "risk_label"], key="a_sp")
        else:
            st.info("No hospitals yet.")


# ------------------------------------------------------------------- router
def main():
    init_state()
    role = S().role

    with st.sidebar:
        st.markdown("## 🩸 LifeFlow")
        if role:
            st.write(f"Signed in as **{role}**")
            if st.button("Log out"):
                logout()
            page = "dash"
        else:
            page = st.radio("Go to", ["Home", "Donor", "Patient", "Hospital", "Staff", "Admin"],
                            label_visibility="collapsed")
        st.divider()
        st.caption("Blood donation, matched fast.")

    if role:
        {"donor": dash_donor, "receiver": dash_receiver, "hospital": dash_hospital,
         "staff": dash_staff, "admin": dash_admin}[role]()
        return

    if page == "Home":
        page_home()
    elif page == "Donor":
        auth_page("Donor", "donor", "/auth/login/donor", reg_donor)
    elif page == "Patient":
        auth_page("Patient", "receiver", "/auth/login/receiver", reg_receiver)
    elif page == "Hospital":
        auth_page("Hospital", "hospital", "/auth/login/hospital", reg_hospital)
    elif page == "Staff":
        auth_page("Hospital staff", "staff", "/auth/login/staff", None)
    elif page == "Admin":
        auth_page("Admin", "admin", "/auth/login/admin", None, is_admin=True)
        st.caption("Default first-time login: admin@lifeflow.com / Admin@123 (you will be asked to change it).")


main()
