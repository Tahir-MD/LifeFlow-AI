import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { loginHospital } from "../services/api";
import AuthLayout from "../components/AuthLayout.jsx";
import { HospitalIcon } from "../components/Icons.jsx";

export default function HospitalLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");
    try {
      const response = await loginHospital(email, password);
      localStorage.setItem("lifeflow_token", response.data.access_token);
      localStorage.setItem("lifeflow_role", "hospital");
      navigate("/hospital/dashboard");
    } catch (error) {
      setErrorMessage("Incorrect email or password.");
    }
  }

  return (
    <AuthLayout
      icon={HospitalIcon}
      eyebrow="Hospital login"
      title="Your ward, one dashboard."
      tagline="Log in to raise a request, check inventory, manage staff shifts, and see matching donors."
    >
      <div className="card">
        <h2>Hospital login</h2>
        <p className="subtitle">Log in to raise an emergency request and see matching donors.</p>
        {errorMessage && <p className="error-text">{errorMessage}</p>}
        <form onSubmit={handleSubmit}>
          <label>Email</label>
          <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />

          <label>Password</label>
          <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />

          <button type="submit">Log in</button>
        </form>
      </div>
      <p className="empty-state">New here? <Link to="/hospital/register">Register your hospital</Link>.</p>
    </AuthLayout>
  );
}
