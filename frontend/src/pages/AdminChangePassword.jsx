import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { changeAdminPassword } from "../services/api";
import { LockIcon } from "../components/Icons.jsx";

export default function AdminChangePassword() {
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");

    if (newPassword.length < 8) {
      setErrorMessage("Your new password must be at least 8 characters.");
      return;
    }
    if (newPassword !== confirmPassword) {
      setErrorMessage("The two new passwords don't match.");
      return;
    }

    try {
      await changeAdminPassword(currentPassword, newPassword);
      localStorage.removeItem("lifeflow_admin_must_change");
      navigate("/admin/dashboard");
    } catch (error) {
      const detail = error.response?.data?.detail || "Could not update the password.";
      setErrorMessage(detail);
    }
  }

  return (
    <div className="page">
      <div className="card">
        <div className="list-row-top">
          <h2>Set your own admin password</h2>
          <LockIcon size={26} color="#B01E28" />
        </div>
        <p className="subtitle">
          This is a first-time login on the default account. Every hospital that installs LifeFlow starts with
          the same admin login, so before you can use the dashboard, please set a password only you know.
        </p>
        {errorMessage && <p className="error-text">{errorMessage}</p>}
        <form onSubmit={handleSubmit}>
          <label>Current password</label>
          <input
            type="password"
            placeholder="The default password you just logged in with"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />

          <label>New password</label>
          <input
            type="password"
            placeholder="At least 8 characters"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
          />

          <label>Confirm new password</label>
          <input
            type="password"
            placeholder="Type it again"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
          />

          <button type="submit">Save password &amp; continue</button>
        </form>
      </div>
    </div>
  );
}
