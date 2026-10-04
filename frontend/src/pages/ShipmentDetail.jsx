import React, { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import api, { errorMessage } from "../api.js";
import ShipmentForm from "../components/ShipmentForm.jsx";
import { Card, Empty, ErrorBox, Loading, Modal, ProbabilityBar, ReasonList, RiskBadge, StatusBadge } from "../components/ui.jsx";
import { DAYS, formatDateTime, formatMinutes, titleCase } from "../utils.js";

function Field({ label, children }) {
  return <div className="kv"><span>{label}</span><strong>{children}</strong></div>;
}

function TimeBars({ promised, predicted, actual }) {
  const max = Math.max(promised || 0, predicted || 0, actual || 0, 1);
  const bar = (label, value, cls) => value != null && (
    <div className="timebar">
      <span>{label}</span>
      <div className="timebar-track"><div className={`timebar-fill ${cls}`} style={{ width: `${(value / max) * 100}%` }} /></div>
      <strong>{formatMinutes(value)}</strong>
    </div>
  );
  return <div>{bar("Promised", promised, "t-promised")}{bar("Predicted", predicted, "t-predicted")}{bar("Actual", actual, "t-actual")}</div>;
}

export default function ShipmentDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [s, setS] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const { data } = await api.get(`/api/shipments/${id}`);
      setS(data);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const runPrediction = async () => {
    setBusy(true);
    try {
      await api.post(`/api/shipments/${id}/predict`);
      await load();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  if (error && !s) return <div><Link to="/shipments" className="link">← Back to shipments</Link><ErrorBox message={error} onRetry={load} /></div>;
  if (!s) return <Loading />;

  const delay = s.predicted_delivery_minutes != null ? s.predicted_delivery_minutes - s.promised_delivery_minutes : null;

  return (
    <div>
      <Link to="/shipments" className="link">← Back to shipments</Link>
      <div className="page-head">
        <h1>Shipment {s.shipment_id} <StatusBadge status={s.current_status} /></h1>
        <div className="btn-row">
          <button className="btn btn-primary" onClick={runPrediction} disabled={busy}>{busy ? "Predicting..." : "Run prediction"}</button>
          <button className="btn" onClick={() => navigate(`/what-if?shipment=${s.shipment_id}`)}>What-if</button>
          <button className="btn" onClick={() => setEditing(true)}>Edit</button>
        </div>
      </div>
      <ErrorBox message={error} />

      <div className="grid-2">
        <Card title="Shipment details">
          <div className="kv-grid">
            <Field label="Source">{s.source}</Field>
            <Field label="Destination">{s.destination}</Field>
            <Field label="Distance">{s.distance_km} km</Field>
            <Field label="Vehicle">{titleCase(s.vehicle_type)}</Field>
            <Field label="Traffic">{titleCase(s.traffic_level)}</Field>
            <Field label="Weather">{titleCase(s.weather_condition)}</Field>
            <Field label="Departure">{DAYS[s.day_of_week]}, {String(s.hour_of_day).padStart(2, "0")}:00</Field>
            <Field label="Warehouse delay">{s.warehouse_delay_minutes} min</Field>
            <Field label="Previous route delay">{s.previous_route_delay_minutes} min</Field>
            <Field label="Created">{formatDateTime(s.created_at)}</Field>
          </div>
        </Card>
        <Card title="Delivery time & risk">
          <TimeBars promised={s.promised_delivery_minutes} predicted={s.predicted_delivery_minutes} actual={s.actual_delivery_minutes} />
          <div className="kv-grid top-gap">
            <Field label="Promised">{s.promised_delivery_minutes} min</Field>
            <Field label="Predicted">{s.predicted_delivery_minutes != null ? `${s.predicted_delivery_minutes} min` : "-"}</Field>
            <Field label="Actual">{s.actual_delivery_minutes != null ? `${s.actual_delivery_minutes} min` : "Not delivered yet"}</Field>
            <Field label="Predicted ETA">{formatDateTime(s.predicted_eta)}</Field>
            <Field label="Risk level"><RiskBadge level={s.risk_level} /></Field>
            <Field label="Expected delay">{delay != null ? (delay > 0 ? `${delay} min late` : "None") : "-"}</Field>
          </div>
          <div className="top-gap"><span className="muted small">Delay probability (heuristic score)</span><ProbabilityBar value={s.delay_probability} /></div>
          <h4>Risk reasons</h4>
          <ReasonList reasons={s.risk_reasons} />
        </Card>
      </div>

      <Card title="Prediction history">
        {s.prediction_history.length === 0 ? <Empty title="No predictions yet" text="Click Run prediction." /> : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>When</th><th>Predicted</th><th>Promised</th><th>Actual</th><th>Error</th><th>Risk</th><th>Probability</th><th>Reasons</th></tr></thead>
              <tbody>
                {s.prediction_history.map((p) => (
                  <tr key={p.id}>
                    <td>{formatDateTime(p.created_at)}</td>
                    <td>{p.predicted_delivery_minutes} min</td>
                    <td>{p.promised_delivery_minutes} min</td>
                    <td>{p.actual_delivery_minutes ?? "-"}</td>
                    <td>{p.prediction_error_minutes != null ? `${p.prediction_error_minutes} min` : "-"}</td>
                    <td><RiskBadge level={p.risk_level} /></td>
                    <td>{Math.round(p.delay_probability * 100)}%</td>
                    <td className="small">{(p.risk_reasons || []).join(", ") || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {editing && (
        <Modal title={`Edit ${s.shipment_id}`} onClose={() => setEditing(false)}>
          <ShipmentForm shipment={s} onCancel={() => setEditing(false)} onSaved={() => { setEditing(false); load(); }} />
        </Modal>
      )}
    </div>
  );
}
