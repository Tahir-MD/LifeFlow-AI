import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { loginStaff } from "../services/api";
import AuthLayout from "../components/AuthLayout.jsx";
import { UsersIcon } from "../components/Icons.jsx";

export default function StaffLogin() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setErrorMessage("");
    try {
      const response = await loginStaff(email, password);
      localStorage.setItem("lifeflow_token", response.data.access_token);
      localStorage.setItem("lifeflow_role", "staff");
      navigate("/staff/dashboard");
    } catch (error) {
      setErrorMessage("Incorrect email or password. Ask your hospital admin for your login.");
    }
  }

  return (
    <AuthLayout
      icon={UsersIcon}
      eyebrow="Staff login"
      title="Ready for your shift?"
      tagline="Log in with the login your hospital gave you, record every donor and patient you attend to, and print your shift record when you go off duty."
    >
      <div className="card">
        <h2>Staff login</h2>
        <p className="subtitle">Log in at the start of your shift with the login your hospital gave you.</p>
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
