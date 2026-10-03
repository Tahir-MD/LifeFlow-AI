import React from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import LifeFlowLogo from "./LifeFlowLogo.jsx";
import NotificationBell from "./NotificationBell.jsx";
import { logout } from "../services/api";
import {
  DropletIcon, HeartPulseIcon, HospitalIcon, ShieldCheckIcon, UsersIcon,
  StarIcon, InfoIcon, MapPinIcon,
} from "./Icons.jsx";

const ROLE_LABELS = {
  donor: "Donor",
  receiver: "Patient",
  hospital: "Hospital",
  admin: "Admin",
  staff: "Staff",
};

export default function NavigationBar() {
  const location = useLocation();
  const navigate = useNavigate();

  const token = localStorage.getItem("lifeflow_token");
  const role = localStorage.getItem("lifeflow_role");
  const isLoggedIn = Boolean(token && role);

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <div className="nav">
      <Link to="/" className="nav-logo">
        <LifeFlowLogo />
        LifeFlow
      </Link>

      {isLoggedIn ? (
        <div className="nav-links">
          <Link to="/#about"><InfoIcon size={16} /> About</Link>
          <Link to="/#contact"><MapPinIcon size={16} /> Contact</Link>
          <span className="role-tag">{ROLE_LABELS[role] || role}</span>
          <Link to={`/${role}/dashboard`}>My dashboard</Link>
          {role === "donor" && <Link to="/leaderboard"><StarIcon size={16} color="#B01E28" /> Leaderboard</Link>}
          {role !== "admin" && role !== "staff" && <NotificationBell role={role} />}
          <button onClick={handleLogout} className="btn-outline" style={{ marginTop: 0, padding: "8px 16px" }}>
            Log out
          </button>
        </div>
      ) : (
        <div className="nav-links">
          <Link to="/#about"><InfoIcon size={16} /> About</Link>
          <Link to="/#contact"><MapPinIcon size={16} /> Contact</Link>
          <Link to="/donor/login"><DropletIcon size={16} /> Donor login</Link>
          <Link to="/receiver/login"><HeartPulseIcon size={16} /> Patient login</Link>
          <Link to="/hospital/login"><HospitalIcon size={16} /> Hospital login</Link>
          <Link to="/admin/login" className="admin-link"><ShieldCheckIcon size={14} /> Admin</Link>
          <Link to="/staff/login" className="admin-link"><UsersIcon size={14} /> Staff</Link>
        </div>
      )}
    </div>
  );
}
