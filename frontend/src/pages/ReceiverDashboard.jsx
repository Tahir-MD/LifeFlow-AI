import React, { useEffect, useState } from "react";
import {
  createReceiverRequest,
  getMatches,
  getMyReceiverProfile,
  getReceiverDonationHistory,
  getReceiverRequestHistory,
  getReceiverStats,
  rateDonor,
} from "../services/api";
import StarRating from "../components/StarRating.jsx";
import PrintButton from "../components/PrintButton.jsx";
import PrintHeader from "../components/PrintHeader.jsx";
import AIReportAnalyzer from "../components/AIReportAnalyzer.jsx";
import AIChatWidget from "../components/AIChatWidget.jsx";
import { HeartPulseIcon, BellRingIcon, DropletIcon, StarIcon } from "../components/Icons.jsx";

const BLOOD_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];

function describeUrgency(request) {
  if (request.urgency_type === "emergency") return "Emergency, needed right now";
  if (request.urgency_type === "days") return `Needed within ${request.urgency_value} day${request.urgency_value === 1 ? "" : "s"}`;
  if (request.urgency_type === "months") return `Needed within ${request.urgency_value} month${request.urgency_value === 1 ? "" : "s"}`;
  return "";
}

const TABS = [
  { key: "new", label: "Request blood", icon: HeartPulseIcon },
  { key: "myrequests", label: "My requests (full history)", icon: BellRingIcon },
  { key: "history", label: "Donations received", icon: DropletIcon },
  { key: "stats", label: "Stats", icon: StarIcon },
];

export default function ReceiverDashboard() {
  const [tab, setTab] = useState("new");
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState({
    blood_type_needed: "O+",
    units_needed: 1,
    patient_name: "",
    urgency_type: "emergency",
    urgency_value: "",
    latitude: "",
    longitude: "",
  });
  const [matches, setMatches] = useState([]);
  const [searched, setSearched] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const [history, setHistory] = useState([]);
  const [myRequests, setMyRequests] = useState([]);
  const [stats, setStats] = useState(null);

  async function loadProfile() {
    try {
      const response = await getMyReceiverProfile();
      setProfile(response.data);
    } catch (error) {
      setProfile(null);
    }
  }
  async function loadHistory() {
    try {
      const response = await getReceiverDonationHistory();
      setHistory(response.data);
    } catch (error) {
      setHistory([]);
    }
  }
  async function loadMyRequests() {
    try {
      const response = await getReceiverRequestHistory();
      setMyRequests(response.data);
    } catch (error) {
      setMyRequests([]);
    }
  }
  async function loadStats() {
    try {
      const response = await getReceiverStats();
      setStats(response.data);
    } catch (error) {
      setStats(null);
    }
  }

  useEffect(() => {
    loadProfile();
    loadHistory();
    loadMyRequests();
    loadStats();

    // Picks up anything the floating AI assistant collected on another
    // page (including while signed out, on the home page) and carries
    // it into this form so the person doesn't have to repeat themselves.
    const pending = localStorage.getItem("lifeflow_ai_pending_request");
    if (pending) {
      try {
        applyAiResult(JSON.parse(pending));
      } catch (error) {
        // Ignore a malformed value and just leave the form as-is.
      }
      localStorage.removeItem("lifeflow_ai_pending_request");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleChange(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");
    try {
      const response = await createReceiverRequest({
        ...form,
        units_needed: parseInt(form.units_needed, 10),
        urgency_value: form.urgency_type === "emergency" ? null : parseInt(form.urgency_value, 10),
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
      });
      const matchResponse = await getMatches(response.data.id);
      setMatches(matchResponse.data);
      setSearched(true);
      loadMyRequests();
    } catch (error) {
      setErrorMessage("Could not create the request. Please check your details and login status.");
    }
  }

  function applyAiResult(result) {
    setForm((prev) => ({
      ...prev,
      blood_type_needed: result.blood_type || prev.blood_type_needed,
      units_needed: result.units || prev.units_needed,
      patient_name: result.patient_name || prev.patient_name,
      urgency_type: result.urgency_type || prev.urgency_type,
      urgency_value: result.urgency_value || prev.urgency_value,
    }));
  }

  async function handleRateDonor(donationId, stars) {
    try {
      await rateDonor(donationId, stars, "");
    } catch (error) {
      // Silently ignore; the control already shows as submitted.
    }
  }

  return (
    <div className="page">
      {profile && (
        <div className="profile-bar">
          <div>
            <span className="role-tag">Patient</span>
            <span className="name">{profile.full_name}</span>
          </div>
          <div>{profile.phone_number}</div>
        </div>
      )}

      <div className="tab-row">
        {TABS.map((t) => (
          <button key={t.key} className={`tab-button ${tab === t.key ? "active" : ""}`} onClick={() => setTab(t.key)}>
            <t.icon size={15} /> {t.label}
          </button>
        ))}
      </div>

      {tab === "new" && (
        <>
          <AIReportAnalyzer onUseResult={applyAiResult} />
          <AIChatWidget onUseResult={applyAiResult} />

          <div className="card">
            <h2>Request blood</h2>
            <p className="subtitle">Tell donors how many bags you need and how soon.</p>
            {errorMessage && <p className="error-text">{errorMessage}</p>}
            <form onSubmit={handleSubmit}>
              <label>Blood type needed</label>
              <select name="blood_type_needed" value={form.blood_type_needed} onChange={handleChange}>
                {BLOOD_TYPES.map((type) => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>

              <label>Bags needed</label>
              <input name="units_needed" type="number" min="1" placeholder="Bags needed" value={form.units_needed} onChange={handleChange} required />

              <label>Patient name, optional</label>
              <input name="patient_name" placeholder="Patient name" value={form.patient_name} onChange={handleChange} />

              <label>How soon is it needed</label>
              <select name="urgency_type" value={form.urgency_type} onChange={handleChange}>
                <option value="emergency">Emergency, needed right now</option>
                <option value="days">Needed within a number of days</option>
                <option value="months">Needed within a number of months</option>
              </select>

              {form.urgency_type !== "emergency" && (
                <>
                  <label>Number of {form.urgency_type === "days" ? "days" : "months"}</label>
                  <input name="urgency_value" type="number" min="1" placeholder={`Number of ${form.urgency_type}`} value={form.urgency_value} onChange={handleChange} required />
                </>
              )}

              <label>Latitude</label>
              <input name="latitude" placeholder="Latitude" value={form.latitude} onChange={handleChange} required />

              <label>Longitude</label>
              <input name="longitude" placeholder="Longitude" value={form.longitude} onChange={handleChange} required />

              <button type="submit">Send request and find donors</button>
            </form>
          </div>

          {searched && (
            <div className="card">
              <h2>AI Smart Donor Matching</h2>
              <p className="subtitle">Ranked by a blended score — blood-type match, distance, and donation reliability — best match first.</p>
              {matches.length === 0 && (
                <p className="empty-state">No compatible donors were found within range for this request.</p>
              )}
              {matches.map((match) => (
                <div className="list-row-stack" key={match.donor_id}>
                  <div className="list-row-top">
                    <div className="meta">
                      <span className="badge">{match.blood_type}</span>
                      &nbsp; {match.full_name}
                      {match.is_exact_match && <span className="exact-match-badge">Exact type</span>}
                      <span className="match-score-badge" style={{ marginLeft: "6px" }}>Match {match.match_score}</span>
                    </div>
                    <span className="distance">{match.distance_kilometers} km away · {match.availability_label}</span>
                  </div>
                  <div className="contact-block">
                    <div className="contact-label">Contact this donor</div>
                    <div className="contact-phone">{match.phone_number}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {tab === "myrequests" && (
        <div className="card">
          <PrintHeader title="My requests — full history" subtitle={profile ? profile.full_name : ""} />
          <div className="list-row-top">
            <h2>My requests — full history</h2>
            <PrintButton />
          </div>
          <p className="subtitle no-print">Every request you have ever sent, open, closed, or still waiting for a donor.</p>
          {myRequests.length === 0 && <p className="empty-state">You have not sent a request yet.</p>}
          {myRequests.map((r) => (
            <div className="list-row-stack" key={r.id}>
              <div className="list-row-top">
                <div className="meta">
                  <span className="badge">{r.blood_type_needed}</span>
                  &nbsp; {r.units_fulfilled}/{r.units_needed} bags fulfilled
                </div>
                <span className="distance">{new Date(r.created_at).toLocaleString()}</span>
              </div>
              <div className="empty-state">
                Status: {r.status} · {describeUrgency(r)}
                {r.patient_name ? ` · Patient: ${r.patient_name}` : ""}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "history" && (
        <div className="card">
          <PrintHeader title="Donations received" subtitle={profile ? profile.full_name : ""} />
          <div className="list-row-top">
            <h2>Donations received</h2>
            <PrintButton />
          </div>
          <p className="subtitle no-print">Every donation given against your requests, with full donor details.</p>
          {history.length === 0 && <p className="empty-state">No donor has fulfilled a request yet.</p>}
          {history.map((item) => (
            <div className="list-row-stack" key={item.donation_id}>
              <div className="list-row-top">
                <div className="meta">
                  <span className="badge">{item.donor_blood_type}</span>
                  &nbsp; {item.donor_name}
                </div>
                <span className="distance">{new Date(item.donated_at).toLocaleString()}</span>
              </div>
              <div className="empty-state">
                {item.units_donated} bag{item.units_donated === 1 ? "" : "s"} donated · Phone: {item.donor_phone}
                {item.patient_name ? ` · Patient: ${item.patient_name}` : ""} · Request status: {item.request_status}
              </div>
              <div style={{ marginTop: "10px" }}>
                <div className="contact-label" style={{ marginBottom: "4px" }}>Rate this donor</div>
                <StarRating onSubmit={(stars) => handleRateDonor(item.donation_id, stars)} />
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "stats" && stats && (
        <div className="card">
          <h2>Stats</h2>
          <div className="stat-grid">
            <div className="stat-card"><div className="stat-value">{stats.total_requests}</div><div className="stat-label">Total requests</div></div>
            <div className="stat-card"><div className="stat-value">{stats.open_requests}</div><div className="stat-label">Open requests</div></div>
            <div className="stat-card"><div className="stat-value">{stats.fulfilled_requests}</div><div className="stat-label">Fulfilled requests</div></div>
            <div className="stat-card"><div className="stat-value">{stats.total_units_received}</div><div className="stat-label">Bags received</div></div>
          </div>
        </div>
      )}
    </div>
  );
}
