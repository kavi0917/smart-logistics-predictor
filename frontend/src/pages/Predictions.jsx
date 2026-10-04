import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api.js";
import { Card, Empty, ErrorBox, ProbabilityBar, ReasonList, RiskBadge } from "../components/ui.jsx";
import { DAYS, TRAFFIC, VEHICLES, WEATHER, formatDateTime, formatMinutes, titleCase } from "../utils.js";

const DEFAULTS = {
  distance_km: 50, traffic_level: "HIGH", weather_condition: "RAIN", vehicle_type: "TRUCK", hour_of_day: 15, day_of_week: 2,
  warehouse_delay_minutes: 10, previous_route_delay_minutes: 5, promised_delivery_minutes: 90,
};

export default function Predictions() {
  const [form, setForm] = useState(DEFAULTS);
  const [shipmentId, setShipmentId] = useState("");
  const [shipments, setShipments] = useState([]);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadHistory = useCallback(() => {
    api.get("/api/predictions/history", { params: { limit: 50 } }).then((r) => setHistory(r.data)).catch((e) => setError(errorMessage(e)));
  }, []);

  useEffect(() => {
    loadHistory();
    api.get("/api/shipments").then((r) => setShipments(r.data)).catch(() => {});
  }, [loadHistory]);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const pickShipment = (code) => {
    setShipmentId(code);
    const s = shipments.find((x) => x.shipment_id === code);
    if (s) {
      setForm({
        distance_km: s.distance_km, traffic_level: s.traffic_level, weather_condition: s.weather_condition, vehicle_type: s.vehicle_type,
        hour_of_day: s.hour_of_day, day_of_week: s.day_of_week, warehouse_delay_minutes: s.warehouse_delay_minutes,
        previous_route_delay_minutes: s.previous_route_delay_minutes, promised_delivery_minutes: s.promised_delivery_minutes,
      });
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError("");
    const body = {
      distance_km: Number(form.distance_km), traffic_level: form.traffic_level, weather_condition: form.weather_condition,
      vehicle_type: form.vehicle_type, hour_of_day: Number(form.hour_of_day), day_of_week: Number(form.day_of_week),
      warehouse_delay_minutes: Number(form.warehouse_delay_minutes), previous_route_delay_minutes: Number(form.previous_route_delay_minutes),
      promised_delivery_minutes: Number(form.promised_delivery_minutes),
    };
    if (shipmentId) body.shipment_id = shipmentId;
    try {
      const { data } = await api.post("/api/predictions/predict", body);
      setResult(data);
      loadHistory();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const select = (k, options, label) => (
    <label className="field">{label}
      <select value={form[k]} onChange={set(k)}>{options.map((o) => <option key={o} value={o}>{titleCase(String(o))}</option>)}</select>
    </label>
  );
  const num = (k, label, min = 0) => (
    <label className="field">{label}<input type="number" min={min} step="any" required value={form[k]} onChange={set(k)} /></label>
  );

  return (
    <div>
      <div className="page-head"><h1>ETA & Risk Prediction</h1></div>
      <div className="grid-2">
        <Card title="Prediction inputs">
          <form onSubmit={submit} className="form-grid">
            <label className="field full">Link to existing shipment (optional)
              <select value={shipmentId} onChange={(e) => pickShipment(e.target.value)}>
                <option value="">Ad-hoc prediction (not linked)</option>
                {shipments.map((s) => <option key={s.id} value={s.shipment_id}>{s.shipment_id} · {s.source} → {s.destination}</option>)}
              </select>
            </label>
            {num("distance_km", "Distance (km)", 1)}
            {select("vehicle_type", VEHICLES, "Vehicle")}
            {select("traffic_level", TRAFFIC, "Traffic")}
            {select("weather_condition", WEATHER, "Weather")}
            {select("hour_of_day", [...Array(24).keys()], "Departure hour")}
            <label className="field">Day of week
              <select value={form.day_of_week} onChange={set("day_of_week")}>{DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}</select>
            </label>
            {num("warehouse_delay_minutes", "Warehouse delay (min)")}
            {num("previous_route_delay_minutes", "Previous route delay (min)")}
            {num("promised_delivery_minutes", "Promised delivery (min)", 1)}
            <div className="form-actions full">
              <ErrorBox message={error} />
              <button className="btn btn-primary" disabled={busy}>{busy ? "Predicting..." : "Predict delivery time"}</button>
            </div>
          </form>
        </Card>

        <Card title="Prediction result">
          {!result ? <Empty title="No prediction yet" text="Fill the form and run the model." /> : (
            <div>
              <div className="result-hero">
                <div><span className="muted small">Predicted delivery</span><div className="big">{formatMinutes(result.predicted_delivery_minutes)}</div><small>{result.predicted_delivery_minutes} min</small></div>
                <div><span className="muted small">Promised</span><div className="big">{formatMinutes(result.promised_delivery_minutes)}</div><small>{result.promised_delivery_minutes} min</small></div>
                <div><span className="muted small">Risk</span><div className="big"><RiskBadge level={result.risk_level} /></div><small>{result.expected_delay_minutes > 0 ? `~${result.expected_delay_minutes} min late` : "Within promise"}</small></div>
              </div>
              <p className="muted small top-gap">Predicted ETA (if dispatched now): <strong>{formatDateTime(result.predicted_eta)}</strong></p>
              <span className="muted small">Delay probability (heuristic score)</span>
              <ProbabilityBar value={result.delay_probability} />
              <h4>Why this risk level?</h4>
              <ReasonList reasons={result.risk_reasons} />
            </div>
          )}
        </Card>
      </div>

      <Card title="Prediction history" actions={<button className="btn btn-small" onClick={loadHistory}>Refresh</button>}>
        {!history || history.length === 0 ? <Empty title="No predictions stored" /> : (
          <div className="table-wrap">
            <table className="table">
              <thead><tr><th>When</th><th>Shipment</th><th>Predicted</th><th>Promised</th><th>Actual</th><th>Error</th><th>Risk</th><th>Prob.</th></tr></thead>
              <tbody>
                {history.map((p) => (
                  <tr key={p.id}>
                    <td>{formatDateTime(p.created_at)}</td>
                    <td>{p.shipment_code ? <Link className="link" to={`/shipments/${p.shipment_code}`}>{p.shipment_code}</Link> : <span className="muted">ad-hoc</span>}</td>
                    <td>{p.predicted_delivery_minutes} min</td>
                    <td>{p.promised_delivery_minutes} min</td>
                    <td>{p.actual_delivery_minutes ?? "-"}</td>
                    <td>{p.prediction_error_minutes != null ? `${p.prediction_error_minutes} min` : "-"}</td>
                    <td><RiskBadge level={p.risk_level} /></td>
                    <td>{Math.round(p.delay_probability * 100)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
