import React, { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { errorMessage } from "../api.js";
import { useAuth } from "../auth.jsx";
import { ErrorBox } from "../components/ui.jsx";

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-art">
        <h1>Know which shipments will be late<br />before the customer does.</h1>
        <p>Smart Logistics Delivery Prediction System: ETA prediction, delay-risk classification and early alerts for logistics managers.</p>
        <div className="route-line"><span /><span /><span /><span /></div>
      </div>
      <form className="login-card" onSubmit={submit}>
        <h2>Sign in</h2>
        <label className="field">Email
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="admin@logistics.local" required autoFocus />
        </label>
        <label className="field">Password
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </label>
        <ErrorBox message={error} />
        <button className="btn btn-primary btn-block" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
        <p className="muted small">Local demo account: admin@logistics.local / Admin@123</p>
      </form>
    </div>
  );
}
