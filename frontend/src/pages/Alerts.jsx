import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api.js";
import { Card, Empty, ErrorBox, Loading, RiskBadge } from "../components/ui.jsx";
import { formatDateTime, formatMinutes } from "../utils.js";

export default function Alerts() {
  const [alerts, setAlerts] = useState(null);
  const [filter, setFilter] = useState("unread");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const { data } = await api.get("/api/alerts");
      setAlerts(data);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  const markRead = async (id) => {
    try { await api.patch(`/api/alerts/${id}/read`); load(); } catch (err) { setError(errorMessage(err)); }
  };
  const markAll = async () => {
    try { await api.patch("/api/alerts/read-all"); load(); } catch (err) { setError(errorMessage(err)); }
  };

  const shown = (alerts || []).filter((a) => filter === "all" || !a.is_read);
  const unread = (alerts || []).filter((a) => !a.is_read).length;

  return (
    <div>
      <div className="page-head">
        <h1>Alerts</h1>
        <div className="btn-row">
          <select value={filter} onChange={(e) => setFilter(e.target.value)}>
            <option value="unread">Unread ({unread})</option>
            <option value="all">All alerts</option>
          </select>
          <button className="btn" onClick={markAll} disabled={!unread}>Mark all read</button>
        </div>
      </div>
      <ErrorBox message={error} onRetry={load} />
      {!alerts ? <Loading /> : shown.length === 0 ? <Card><Empty title="No alerts" text="Alerts are created automatically when an active shipment is predicted HIGH risk." /></Card> : (
        <div className="alert-cards">
          {shown.map((a) => (
            <article key={a.id} className={`alert-card ${a.is_read ? "read" : ""}`}>
              <div className="alert-top">
                <div><Link to={`/shipments/${a.shipment_code}`} className="link strong">{a.shipment_code}</Link> <RiskBadge level={a.risk_level} /> {!a.is_read && <span className="badge badge-new">New</span>}</div>
                <small className="muted">{formatDateTime(a.created_at)}</small>
              </div>
              <p className="alert-msg">{a.message}</p>
              <div className="alert-meta">
                <span>Predicted: <strong>{formatMinutes(a.predicted_delivery_minutes)}</strong></span>
                <span>Promised: <strong>{formatMinutes(a.promised_delivery_minutes)}</strong></span>
                <span>Predicted ETA: <strong>{formatDateTime(a.predicted_eta)}</strong></span>
              </div>
              <p className="muted small">Reason: {a.reason}</p>
              {!a.is_read && <button className="btn btn-small" onClick={() => markRead(a.id)}>Mark as read</button>}
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
