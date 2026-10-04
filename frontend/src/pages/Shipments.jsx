import React, { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { errorMessage } from "../api.js";
import ShipmentForm from "../components/ShipmentForm.jsx";
import { Card, Empty, ErrorBox, Loading, Modal, RiskBadge, StatusBadge } from "../components/ui.jsx";
import { STATUSES, formatMinutes, titleCase } from "../utils.js";

export default function Shipments() {
  const navigate = useNavigate();
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [risk, setRisk] = useState("");
  const [modal, setModal] = useState(null); // {mode:'create'} | {mode:'edit', shipment}
  const [toDelete, setToDelete] = useState(null);

  const load = useCallback(async () => {
    setError("");
    try {
      const params = {};
      if (search) params.search = search;
      if (status) params.status = status;
      if (risk) params.risk_level = risk;
      const { data } = await api.get("/api/shipments", { params });
      setRows(data);
    } catch (err) {
      setError(errorMessage(err));
    }
  }, [search, status, risk]);

  useEffect(() => {
    const t = setTimeout(load, 250); // small debounce for the search box
    return () => clearTimeout(t);
  }, [load]);

  const confirmDelete = async () => {
    try {
      await api.delete(`/api/shipments/${toDelete.shipment_id}`);
      setToDelete(null);
      load();
    } catch (err) {
      setError(errorMessage(err));
      setToDelete(null);
    }
  };

  return (
    <div>
      <div className="page-head">
        <h1>Shipments</h1>
        <button className="btn btn-primary" onClick={() => setModal({ mode: "create" })}>+ New shipment</button>
      </div>
      <Card>
        <div className="filters">
          <input placeholder="Search ID, source or destination" value={search} onChange={(e) => setSearch(e.target.value)} />
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{titleCase(s)}</option>)}
          </select>
          <select value={risk} onChange={(e) => setRisk(e.target.value)}>
            <option value="">All risk levels</option>
            {["LOW", "MEDIUM", "HIGH"].map((r) => <option key={r}>{r}</option>)}
          </select>
        </div>
        <ErrorBox message={error} onRetry={load} />
        {!rows ? <Loading /> : rows.length === 0 ? <Empty title="No shipments match" text="Try clearing the filters or create a new shipment." /> : (
          <div className="table-wrap">
            <table className="table clickable">
              <thead>
                <tr><th>ID</th><th>Route</th><th>Distance</th><th>Traffic</th><th>Weather</th><th>Vehicle</th><th>Promised</th><th>Predicted</th><th>Risk</th><th>Status</th><th /></tr>
              </thead>
              <tbody>
                {rows.map((s) => (
                  <tr key={s.id} onClick={() => navigate(`/shipments/${s.shipment_id}`)}>
                    <td className="strong">{s.shipment_id}</td>
                    <td>{s.source} → {s.destination}</td>
                    <td>{s.distance_km} km</td>
                    <td>{titleCase(s.traffic_level)}</td>
                    <td>{titleCase(s.weather_condition)}</td>
                    <td>{titleCase(s.vehicle_type)}</td>
                    <td>{formatMinutes(s.promised_delivery_minutes)}</td>
                    <td>{formatMinutes(s.predicted_delivery_minutes)}</td>
                    <td><RiskBadge level={s.risk_level} /></td>
                    <td><StatusBadge status={s.current_status} /></td>
                    <td className="row-actions" onClick={(e) => e.stopPropagation()}>
                      <button className="btn btn-small" onClick={() => setModal({ mode: "edit", shipment: s })}>Edit</button>
                      <button className="btn btn-small btn-danger" onClick={() => setToDelete(s)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {modal && (
        <Modal title={modal.mode === "create" ? "New shipment" : `Edit ${modal.shipment.shipment_id}`} onClose={() => setModal(null)}>
          <ShipmentForm shipment={modal.shipment} onCancel={() => setModal(null)} onSaved={() => { setModal(null); load(); }} />
        </Modal>
      )}
      {toDelete && (
        <Modal title="Delete shipment" onClose={() => setToDelete(null)}>
          <p>Delete shipment <strong>{toDelete.shipment_id}</strong> and its prediction history? This cannot be undone.</p>
          <div className="form-actions">
            <button className="btn" onClick={() => setToDelete(null)}>Cancel</button>
            <button className="btn btn-danger" onClick={confirmDelete}>Delete</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
