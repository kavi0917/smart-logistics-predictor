import React, { useState } from "react";
import api, { errorMessage } from "../api.js";
import { DAYS, STATUSES, TRAFFIC, VEHICLES, WEATHER, titleCase } from "../utils.js";
import { ErrorBox } from "./ui.jsx";

const EMPTY = {
  shipment_id: "", source: "", destination: "", distance_km: 100, traffic_level: "MEDIUM", weather_condition: "CLEAR",
  vehicle_type: "VAN", hour_of_day: 10, day_of_week: 1, warehouse_delay_minutes: 0, previous_route_delay_minutes: 0,
  promised_delivery_minutes: 240, actual_delivery_minutes: "", current_status: "PENDING",
};

export default function ShipmentForm({ shipment, onSaved, onCancel }) {
  const editing = !!shipment;
  const [form, setForm] = useState(editing ? { ...EMPTY, ...shipment, actual_delivery_minutes: shipment.actual_delivery_minutes ?? "" } : EMPTY);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    const num = (v) => (v === "" || v === null ? null : Number(v));
    const body = {
      source: form.source.trim(), destination: form.destination.trim(), distance_km: Number(form.distance_km),
      traffic_level: form.traffic_level, weather_condition: form.weather_condition, vehicle_type: form.vehicle_type,
      hour_of_day: Number(form.hour_of_day), day_of_week: Number(form.day_of_week),
      warehouse_delay_minutes: Number(form.warehouse_delay_minutes), previous_route_delay_minutes: Number(form.previous_route_delay_minutes),
      promised_delivery_minutes: Number(form.promised_delivery_minutes), actual_delivery_minutes: num(form.actual_delivery_minutes),
      current_status: form.current_status,
    };
    try {
      let res;
      if (editing) {
        res = await api.put(`/api/shipments/${shipment.shipment_id}`, body);
      } else {
        if (form.shipment_id.trim()) body.shipment_id = form.shipment_id.trim();
        res = await api.post("/api/shipments", body);
      }
      onSaved(res.data);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSaving(false);
    }
  };

  const select = (k, options, label) => (
    <label className="field">{label}
      <select value={form[k]} onChange={set(k)}>
        {options.map((o) => <option key={o} value={o}>{titleCase(String(o))}</option>)}
      </select>
    </label>
  );
  const input = (k, label, props = {}) => (
    <label className="field">{label}
      <input value={form[k]} onChange={set(k)} {...props} />
    </label>
  );

  return (
    <form onSubmit={submit} className="form-grid">
      {!editing && input("shipment_id", "Shipment ID (optional)", { placeholder: "auto, e.g. L065" })}
      {input("source", "Source", { required: true })}
      {input("destination", "Destination", { required: true })}
      {input("distance_km", "Distance (km)", { type: "number", min: 1, step: "any", required: true })}
      {select("traffic_level", TRAFFIC, "Traffic")}
      {select("weather_condition", WEATHER, "Weather")}
      {select("vehicle_type", VEHICLES, "Vehicle")}
      {select("hour_of_day", [...Array(24).keys()], "Departure hour")}
      <label className="field">Day of week
        <select value={form.day_of_week} onChange={set("day_of_week")}>
          {DAYS.map((d, i) => <option key={d} value={i}>{d}</option>)}
        </select>
      </label>
      {input("warehouse_delay_minutes", "Warehouse delay (min)", { type: "number", min: 0 })}
      {input("previous_route_delay_minutes", "Previous route delay (min)", { type: "number", min: 0 })}
      {input("promised_delivery_minutes", "Promised delivery (min)", { type: "number", min: 1, required: true })}
      {input("actual_delivery_minutes", "Actual delivery (min, if delivered)", { type: "number", min: 1 })}
      {select("current_status", STATUSES, "Status")}
      <div className="form-actions full">
        <ErrorBox message={error} />
        <button type="button" className="btn" onClick={onCancel}>Cancel</button>
        <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? "Saving..." : editing ? "Save changes" : "Create shipment"}</button>
      </div>
    </form>
  );
}
