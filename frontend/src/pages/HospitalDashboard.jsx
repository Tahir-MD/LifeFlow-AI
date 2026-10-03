import React, { useEffect, useState } from "react";
import {
  createHospitalRequest,
  getMatches,
  getMyHospitalProfile,
  getHospitalDonationHistory,
  getHospitalRequestHistory,
  getHospitalStats,
  rateDonor,
  getMyInventory,
  updateMyInventory,
  listMyCamps,
  createCamp,
  listCampRsvps,
  createStaff,
  listMyStaff,
  removeStaff,
  getHospitalAllVisitors,
  getShortagePrediction,
} from "../services/api";
import StarRating from "../components/StarRating.jsx";
import PrintButton from "../components/PrintButton.jsx";
import PrintHeader from "../components/PrintHeader.jsx";
import AIReportAnalyzer from "../components/AIReportAnalyzer.jsx";
import AIChatWidget from "../components/AIChatWidget.jsx";
import { DropletIcon, BellRingIcon, HeartPulseIcon, UsersIcon, BoxIcon, MapPinIcon, StarIcon, SparkleIcon } from "../components/Icons.jsx";

const BLOOD_TYPES = ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"];

function describeUrgency(request) {
  if (request.urgency_type === "emergency") return "Emergency, needed right now";
  if (request.urgency_type === "days") return `Needed within ${request.urgency_value} day${request.urgency_value === 1 ? "" : "s"}`;
  if (request.urgency_type === "months") return `Needed within ${request.urgency_value} month${request.urgency_value === 1 ? "" : "s"}`;
  return "";
}

const SHIFT_CHOICES = ["Shift 1", "Shift 2", "Shift 3", "Shift 4"];

const TABS = [
  { key: "new", label: "New request", icon: DropletIcon },
  { key: "myrequests", label: "My requests (full history)", icon: BellRingIcon },
  { key: "history", label: "Requests received", icon: HeartPulseIcon },
  { key: "staff", label: "Staff & shifts", icon: UsersIcon },
  { key: "inventory", label: "Blood inventory", icon: BoxIcon },
  { key: "camps", label: "Donation camps", icon: MapPinIcon },
  { key: "shortage", label: "AI Shortage Prediction", icon: SparkleIcon },
  { key: "stats", label: "Stats", icon: StarIcon },
];

export default function HospitalDashboard() {
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
  const [inventory, setInventory] = useState([]);
  const [camps, setCamps] = useState([]);
  const [campRsvps, setCampRsvps] = useState({});
  const [staffList, setStaffList] = useState([]);
  const [allVisitors, setAllVisitors] = useState([]);
  const [staffForm, setStaffForm] = useState({ full_name: "", email: "", password: "", shift: SHIFT_CHOICES[0], phone_number: "" });
  const [staffMessage, setStaffMessage] = useState("");
  const [campForm, setCampForm] = useState({
    title: "", description: "", location_label: "", latitude: "", longitude: "", camp_date: "",
  });
  const [shortage, setShortage] = useState([]);

  async function loadProfile() {
    try {
      const response = await getMyHospitalProfile();
      setProfile(response.data);
    } catch (error) {
      setProfile(null);
    }
  }
  async function loadHistory() {
    try {
      const response = await getHospitalDonationHistory();
      setHistory(response.data);
    } catch (error) {
      setHistory([]);
    }
  }
  async function loadMyRequests() {
    try {
      const response = await getHospitalRequestHistory();
      setMyRequests(response.data);
    } catch (error) {
      setMyRequests([]);
    }
  }
  async function loadStats() {
    try {
      const response = await getHospitalStats();
      setStats(response.data);
    } catch (error) {
      setStats(null);
    }
  }
  async function loadInventory() {
    try {
      const response = await getMyInventory();
      setInventory(response.data);
    } catch (error) {
      setInventory([]);
    }
  }
  async function loadCamps() {
    try {
      const response = await listMyCamps();
      setCamps(response.data);
    } catch (error) {
      setCamps([]);
    }
  }
  async function loadShortage() {
    try {
      const response = await getShortagePrediction();
      setShortage(response.data);
    } catch (error) {
      setShortage([]);
    }
  }
  async function loadStaff() {
    try {
      const response = await listMyStaff();
      setStaffList(response.data);
    } catch (error) {
      setStaffList([]);
    }
  }
  async function loadAllVisitors() {
    try {
      const response = await getHospitalAllVisitors();
      setAllVisitors(response.data);
    } catch (error) {
      setAllVisitors([]);
    }
  }

  useEffect(() => {
    loadProfile();
    loadHistory();
    loadMyRequests();
    loadStats();
    loadInventory();
    loadCamps();
    loadStaff();
    loadAllVisitors();
    loadShortage();

    // Picks up anything the floating AI assistant collected on another
    // page and carries it into this form so the person doesn't have
    // to repeat themselves.
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

  function handleStaffFormChange(event) {
    setStaffForm({ ...staffForm, [event.target.name]: event.target.value });
  }

  async function handleCreateStaff(event) {
    event.preventDefault();
    setStaffMessage("");
    try {
      await createStaff(staffForm);
      setStaffForm({ full_name: "", email: "", password: "", shift: SHIFT_CHOICES[0], phone_number: "" });
      loadStaff();
    } catch (error) {
      setStaffMessage("Could not create this staff login. The email may already be used.");
    }
  }

  async function handleRemoveStaff(staffId) {
    try {
      await removeStaff(staffId);
      loadStaff();
      loadAllVisitors();
    } catch (error) {
      // The list simply stays as it was if the removal fails.
    }
  }

  function handleChange(event) {
    setForm({ ...form, [event.target.name]: event.target.value });
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");
    try {
      const response = await createHospitalRequest({
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

  async function handleInventoryChange(blood_type, field, value) {
    setInventory(inventory.map((row) => (row.blood_type === blood_type ? { ...row, [field]: value } : row)));
  }

  async function handleInventorySave(row) {
    try {
      await updateMyInventory({
        blood_type: row.blood_type,
        units_available: parseInt(row.units_available, 10) || 0,
        low_stock_threshold: parseInt(row.low_stock_threshold, 10) || 0,
      });
      loadInventory();
      loadStats();
    } catch (error) {
      // The row simply keeps its last saved value if the update fails.
    }
  }

  function handleCampFormChange(event) {
    setCampForm({ ...campForm, [event.target.name]: event.target.value });
  }

  async function handleCreateCamp(event) {
    event.preventDefault();
    try {
      await createCamp({
        ...campForm,
        latitude: parseFloat(campForm.latitude),
        longitude: parseFloat(campForm.longitude),
        camp_date: new Date(campForm.camp_date).toISOString(),
      });
      setCampForm({ title: "", description: "", location_label: "", latitude: "", longitude: "", camp_date: "" });
      loadCamps();
    } catch (error) {
      // Form stays filled in so the hospital can retry.
    }
  }

  async function toggleCampRsvps(campId) {
    if (campRsvps[campId]) {
      const updated = { ...campRsvps };
      delete updated[campId];
      setCampRsvps(updated);
      return;
    }
    try {
      const response = await listCampRsvps(campId);
      setCampRsvps({ ...campRsvps, [campId]: response.data });
    } catch (error) {
      // Leave the panel closed if the fetch fails.
    }
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
            <span className="role-tag">Hospital</span>
            <span className="name">{profile.name}</span>
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
            <h2>Create an emergency blood request</h2>
            <p className="subtitle">Donors are ranked by compatibility, distance, and eligibility.</p>
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
          <PrintHeader title="My requests — full history" subtitle={profile ? profile.name : ""} />
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
          <PrintHeader title="Requests received" subtitle={profile ? profile.name : ""} />
          <div className="list-row-top">
            <h2>Requests received</h2>
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

      {tab === "staff" && (
        <>
          <div className="card">
            <h2>Add a staff login</h2>
            <p className="subtitle">Create a login for whoever is coming on duty. Give them the email and password you set here.</p>
            {staffMessage && <p className="error-text">{staffMessage}</p>}
            <form onSubmit={handleCreateStaff}>
              <label>Full name</label>
              <input name="full_name" value={staffForm.full_name} onChange={handleStaffFormChange} required />
              <label>Login email</label>
              <input name="email" type="email" value={staffForm.email} onChange={handleStaffFormChange} required />
              <label>Login password</label>
              <input name="password" type="password" value={staffForm.password} onChange={handleStaffFormChange} required />
              <label>Shift</label>
              <select name="shift" value={staffForm.shift} onChange={handleStaffFormChange}>
                {SHIFT_CHOICES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
              <label>Phone number, optional</label>
              <input name="phone_number" value={staffForm.phone_number} onChange={handleStaffFormChange} />
              <button type="submit">Create staff login</button>
            </form>
          </div>

          <div className="card">
            <h2>Your staff, by shift</h2>
            {staffList.length === 0 && <p className="empty-state">No staff logins yet.</p>}
            {staffList.map((s) => (
              <div className="list-row-stack" key={s.id}>
                <div className="list-row-top">
                  <div className="meta">
                    <span className="badge">{s.shift}</span>
                    &nbsp; {s.full_name} &nbsp;
                    <span className="empty-state" style={{ display: "inline" }}>{s.email}</span>
                  </div>
                  <button className="inline-btn btn-outline" onClick={() => handleRemoveStaff(s.id)}>Remove</button>
                </div>
              </div>
            ))}
          </div>

          <div className="card">
            <PrintHeader title="Combined staff shift record" subtitle={profile ? profile.name : ""} />
            <div className="list-row-top">
              <h2>Combined record — every staff member, every shift</h2>
              <PrintButton />
            </div>
            <p className="subtitle no-print">Every donor and patient logged by any staff member, with who logged it and on which shift.</p>
            {allVisitors.length === 0 && <p className="empty-state">No visits logged yet.</p>}
            {allVisitors.map((v) => (
              <div className="list-row-stack" key={v.id}>
                <div className="list-row-top">
                  <div className="meta">
                    <span className={v.visitor_type === "donor" ? "tag-hospital" : "tag-receiver"}>
                      {v.visitor_type === "donor" ? "Donor" : "Patient"}
                    </span>
                    &nbsp; {v.full_name} {v.blood_type ? `· ${v.blood_type}` : ""}
                  </div>
                  <span className="distance">{new Date(v.logged_at).toLocaleString()}</span>
                </div>
                <div className="empty-state">
                  Logged by {v.staff_name} ({v.staff_shift})
                  {v.from_location ? ` · From: ${v.from_location}` : ""}
                  {v.phone_number ? ` · Phone: ${v.phone_number}` : ""}
                  {v.notes ? ` · ${v.notes}` : ""}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === "shortage" && (
        <div className="card">
          <div className="list-row-top">
            <h2><SparkleIcon size={18} color="#B01E28" /> AI Blood Shortage Prediction</h2>
            <button type="button" className="inline-btn btn-outline" onClick={loadShortage}>Refresh</button>
          </div>
          <p className="subtitle">
            Projects how many days your current stock of each blood type will last, based on your actual usage
            over the last 30 days, and flags what's likely to run low.
          </p>
          {shortage.map((row) => (
            <div className={`list-row-stack risk-row ${row.risk_level}`} key={row.blood_type}>
              <div className="list-row-top">
                <div className="meta">
                  <span className="badge">{row.blood_type}</span>
                  &nbsp; {row.units_available} units in stock
                </div>
                <span className="distance">{row.risk_label}</span>
              </div>
              <div className="empty-state">
                Avg. {row.avg_daily_consumption} units/day used
                {row.projected_days_remaining != null
                  ? ` · About ${row.projected_days_remaining} day(s) of stock left at this rate`
                  : " · No recent usage to project from"}
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "inventory" && (
        <div className="card">
          <h2>Blood bank inventory</h2>
          <p className="subtitle">Keep your on-hand stock current so patients and donors can see it.</p>
          <table className="simple-table">
            <thead>
              <tr>
                <th>Blood type</th>
                <th>Units available</th>
                <th>Low stock alert below</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {inventory.map((row) => (
                <tr key={row.blood_type}>
                  <td><span className="badge">{row.blood_type}</span></td>
                  <td>
                    <input
                      type="number" min="0" value={row.units_available}
                      onChange={(e) => handleInventoryChange(row.blood_type, "units_available", e.target.value)}
                    />
                    {row.is_low && <div className="low-stock">Low stock</div>}
                  </td>
                  <td>
                    <input
                      type="number" min="0" value={row.low_stock_threshold}
                      onChange={(e) => handleInventoryChange(row.blood_type, "low_stock_threshold", e.target.value)}
                    />
                  </td>
                  <td><button className="inline-btn" onClick={() => handleInventorySave(row)}>Save</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "camps" && (
        <>
          <div className="card">
            <h2>Organize a donation camp</h2>
            <p className="subtitle">Every donor on LifeFlow is notified when you publish one.</p>
            <form onSubmit={handleCreateCamp}>
              <label>Title</label>
              <input name="title" value={campForm.title} onChange={handleCampFormChange} required />
              <label>Description, optional</label>
              <input name="description" value={campForm.description} onChange={handleCampFormChange} />
              <label>Location</label>
              <input name="location_label" value={campForm.location_label} onChange={handleCampFormChange} required />
              <label>Latitude</label>
              <input name="latitude" value={campForm.latitude} onChange={handleCampFormChange} required />
              <label>Longitude</label>
              <input name="longitude" value={campForm.longitude} onChange={handleCampFormChange} required />
              <label>Date and time</label>
              <input type="datetime-local" name="camp_date" value={campForm.camp_date} onChange={handleCampFormChange} required />
              <button type="submit">Publish camp</button>
            </form>
          </div>

          <div className="card">
            <h2>Your camps</h2>
            {camps.length === 0 && <p className="empty-state">You have not organized a camp yet.</p>}
            {camps.map((camp) => (
              <div className="list-row-stack" key={camp.id}>
                <div className="list-row-top">
                  <div className="meta"><strong>{camp.title}</strong></div>
                  <span className="distance">{new Date(camp.camp_date).toLocaleString()}</span>
                </div>
                <div className="empty-state">{camp.location_label} · {camp.registered_count} donor{camp.registered_count === 1 ? "" : "s"} registered</div>
                <button className="inline-btn btn-outline" onClick={() => toggleCampRsvps(camp.id)}>
                  {campRsvps[camp.id] ? "Hide registered donors" : "View registered donors"}
                </button>
                {campRsvps[camp.id] && (
                  <table className="simple-table" style={{ marginTop: "10px" }}>
                    <thead><tr><th>Donor</th><th>Blood type</th><th>Phone</th></tr></thead>
                    <tbody>
                      {campRsvps[camp.id].map((r) => (
                        <tr key={r.id}><td>{r.donor_name}</td><td>{r.donor_blood_type}</td><td>{r.donor_phone}</td></tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            ))}
          </div>
        </>
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
          {stats.low_stock_types.length > 0 && (
            <p className="error-text">Low stock: {stats.low_stock_types.join(", ")}</p>
          )}
        </div>
      )}
    </div>
  );
}
