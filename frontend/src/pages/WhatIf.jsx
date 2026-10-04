import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import api, { errorMessage } from "../api.js";
import { Card, Empty, ErrorBox, ProbabilityBar, ReasonList, RiskBadge } from "../components/ui.jsx";
import { TRAFFIC, VEHICLES, WEATHER, formatMinutes, titleCase } from "../utils.js";

export default function WhatIf() {
  const [params] = useSearchParams();
  const [shipments, setShipments] = useState([]);
  const [code, setCode] = useState(params.get("shipment") || "");
  const [base, setBase] = useState(null);
  const [changes, setChanges] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/api/shipments").then((r) => {
      const usable = r.data.filter((s) => s.current_status !== "CANCELLED");
      setShipments(usable);
      if (!code && usable.length) setCode(usable[0].shipment_id);
    }).catch((e) => setError(errorMessage(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const s = shipments.find((x) => x.shipment_id === code);
    if (!s) return;
    setBase(s);
    setChanges({
      traffic_level: s.traffic_level, weather_condition: s.weather_condition, vehicle_type: s.vehicle_type,
      warehouse_delay_minutes: s.warehouse_delay_minutes, previous_route_delay_minutes: s.previous_route_delay_minutes,
    });
    setResult(null);
  }, [code, shipments]);

  const run = async () => {
    setBusy(true);
    setError("");
    try {
      const { data } = await api.post("/api/predictions/what-if", {
        base: {
          distance_km: base.distance_km, traffic_level: base.traffic_level, weather_condition: base.weather_condition,
          vehicle_type: base.vehicle_type, hour_of_day: base.hour_of_day, day_of_week: base.day_of_week,
          warehouse_delay_minutes: base.warehouse_delay_minutes, previous_route_delay_minutes: base.previous_route_delay_minutes,
          promised_delivery_minutes: base.promised_delivery_minutes, source: base.source, destination: base.destination,
        },
        overrides: {
          ...changes,
          warehouse_delay_minutes: Number(changes.warehouse_delay_minutes),
          previous_route_delay_minutes: Number(changes.previous_route_delay_minutes),
        },
      });
      setResult(data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const set = (k) => (e) => setChanges({ ...changes, [k]: e.target.value });
  const select = (k, options, label) => (
    <label className="field">{label} <small className="muted">(now: {titleCase(String(base[k]))})</small>
      <select value={changes[k]} onChange={set(k)}>{options.map((o) => <option key={o} value={o}>{titleCase(o)}</option>)}</select>
    </label>
  );

  const diff = result?.difference_minutes;

  return (
    <div>
      <div className="page-head"><h1>What-If Simulation</h1></div>
      <p className="muted">Change the conditions of a shipment and the ML model is run again with the new inputs. Nothing is saved.</p>
      <ErrorBox message={error} />
      <div className="grid-2">
        <Card title="Scenario">
          {!base || !changes ? <Empty title="No shipment selected" /> : (
            <div className="form-grid">
              <label className="field full">Shipment
                <select value={code} onChange={(e) => setCode(e.target.value)}>
                  {shipments.map((s) => <option key={s.id} value={s.shipment_id}>{s.shipment_id} · {s.source} → {s.destination} ({s.distance_km} km)</option>)}
                </select>
              </label>
              {select("traffic_level", TRAFFIC, "Traffic")}
              {select("weather_condition", WEATHER, "Weather")}
              {select("vehicle_type", VEHICLES, "Vehicle")}
              <label className="field">Warehouse delay (min) <small className="muted">(now: {base.warehouse_delay_minutes})</small>
                <input type="number" min="0" value={changes.warehouse_delay_minutes} onChange={set("warehouse_delay_minutes")} />
              </label>
              <label className="field">Previous route delay (min) <small className="muted">(now: {base.previous_route_delay_minutes})</small>
                <input type="number" min="0" value={changes.previous_route_delay_minutes} onChange={set("previous_route_delay_minutes")} />
              </label>
              <div className="form-actions full"><button className="btn btn-primary" onClick={run} disabled={busy}>{busy ? "Calculating..." : "Run simulation"}</button></div>
            </div>
          )}
        </Card>
        <Card title="Result">
          {!result ? <Empty title="Run a simulation" text="Pick a shipment, change conditions and press Run simulation." /> : (
            <div>
              <div className="compare">
                <div className="compare-col">
                  <span className="muted small">Original prediction</span>
                  <div className="big">{result.original.predicted_delivery_minutes} min</div>
                  <small>{formatMinutes(result.original.predicted_delivery_minutes)}</small>
                  <div className="top-gap"><RiskBadge level={result.original.risk_level} /></div>
                </div>
                <div className={`compare-diff ${diff < 0 ? "good" : diff > 0 ? "bad" : ""}`}>
                  <span className="muted small">Difference</span>
                  <div className="big">{diff > 0 ? "+" : ""}{diff} min</div>
                  <small>{diff < 0 ? "faster" : diff > 0 ? "slower" : "no change"}</small>
                </div>
                <div className="compare-col">
                  <span className="muted small">New prediction</span>
                  <div className="big">{result.modified.predicted_delivery_minutes} min</div>
                  <small>{formatMinutes(result.modified.predicted_delivery_minutes)}</small>
                  <div className="top-gap"><RiskBadge level={result.modified.risk_level} /></div>
                </div>
              </div>
              <p className="small top-gap">
                Risk: <RiskBadge level={result.original.risk_level} /> → <RiskBadge level={result.modified.risk_level} />{" "}
                {result.risk_changed ? <strong>(risk level changed)</strong> : <span className="muted">(unchanged)</span>}
              </p>
              <span className="muted small">New delay probability (heuristic)</span>
              <ProbabilityBar value={result.modified.delay_probability} />
              <h4>Risk reasons in the new scenario</h4>
              <ReasonList reasons={result.modified.risk_reasons} />
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}
