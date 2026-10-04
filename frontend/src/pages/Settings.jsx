import React, { useEffect, useState } from "react";
import api, { API_URL, errorMessage } from "../api.js";
import { useAuth } from "../auth.jsx";
import { Card, ErrorBox, Loading } from "../components/ui.jsx";

export default function Settings() {
  const { email, logout } = useAuth();
  const [data, setData] = useState(null);
  const [health, setHealth] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/settings").then((r) => setData(r.data)).catch((e) => setError(errorMessage(e)));
    api.get("/health").then((r) => setHealth(r.data)).catch(() => setHealth({ status: "unreachable" }));
  }, []);

  if (error) return <ErrorBox message={error} />;
  if (!data) return <Loading />;
  const m = data.model.metrics;

  return (
    <div>
      <div className="page-head"><h1>Settings</h1></div>
      <div className="grid-2">
        <Card title="Risk classification (read-only, set in backend config)">
          <div className="kv-grid">
            <div className="kv"><span>MEDIUM when predicted / promised &gt;</span><strong>{data.risk_thresholds.medium_if_predicted_over_promised_ratio}</strong></div>
            <div className="kv"><span>HIGH when predicted / promised &gt;</span><strong>{data.risk_thresholds.high_if_predicted_over_promised_ratio}</strong></div>
            <div className="kv"><span>Long distance reason from</span><strong>{data.reason_thresholds.long_distance_km} km</strong></div>
            <div className="kv"><span>Warehouse delay reason from</span><strong>{data.reason_thresholds.warehouse_delay_minutes} min</strong></div>
            <div className="kv"><span>Previous route delay reason from</span><strong>{data.reason_thresholds.previous_route_delay_minutes} min</strong></div>
            <div className="kv"><span>Peak hours</span><strong>{data.reason_thresholds.peak_hours.join(", ")}</strong></div>
          </div>
          <p className="muted small top-gap">{data.note} Change thresholds with environment variables (RISK_HIGH_RATIO etc.) and restart the backend.</p>
        </Card>
        <Card title="ML model">
          <div className="kv-grid">
            <div className="kv"><span>Algorithm</span><strong>{m?.algorithm || "RandomForestRegressor"}</strong></div>
            <div className="kv"><span>Model file</span><strong>{data.model.file_exists ? "Found" : "Missing"}</strong></div>
            {m && <><div className="kv"><span>MAE (test set)</span><strong>{m.mae} min</strong></div>
              <div className="kv"><span>RMSE (test set)</span><strong>{m.rmse} min</strong></div>
              <div className="kv"><span>R² (test set)</span><strong>{m.r2}</strong></div>
              <div className="kv"><span>Training rows</span><strong>{m.train_rows}</strong></div></>}
          </div>
          <p className="muted small top-gap">Trained on a synthetic dataset for academic prototyping.</p>
        </Card>
      </div>
      <Card title="Connection & account">
        <div className="kv-grid">
          <div className="kv"><span>API URL</span><strong>{API_URL}</strong></div>
          <div className="kv"><span>Backend health</span><strong>{health?.status || "..."}</strong></div>
          <div className="kv"><span>Signed in as</span><strong>{email}</strong></div>
        </div>
        <div className="top-gap"><button className="btn" onClick={logout}>Sign out</button></div>
      </Card>
    </div>
  );
}
