import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginAdmin } from "../services/api";
import AuthLayout from "../components/AuthLayout.jsx";
import { ShieldCheckIcon } from "../components/Icons.jsx";

export default function AdminLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");
    try {
      const response = await loginAdmin(email, password);
      localStorage.setItem("lifeflow_token", response.data.access_token);
      localStorage.setItem("lifeflow_role", "admin");
      if (response.data.must_change_password) {
        localStorage.setItem("lifeflow_admin_must_change", "1");
        navigate("/admin/change-password");
      } else {
        localStorage.removeItem("lifeflow_admin_must_change");
        navigate("/admin/dashboard");
      }
    } catch (error) {
      setErrorMessage("Incorrect email or password.");
    }
  }

  return (
    <AuthLayout
      icon={ShieldCheckIcon}
      eyebrow="Admin login"
      title="The full picture, in one place."
      tagline="See every donor, hospital, and patient's complete history, and every hospital's staff and shifts."
    >
      <div className="card">
        <h2>Admin login</h2>
        <p className="subtitle">
          See every donor, hospital, and patient's full history in one place.
        </p>
        {errorMessage && <p className="error-text">{errorMessage}</p>}
        <form onSubmit={handleSubmit}>
          <label>Email</label>
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />

          <label>Password</label>
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />

          <button type="submit">Log in</button>
        </form>
      </div>
    </AuthLayout>
  );
}
