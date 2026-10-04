import React from "react";
import { titleCase } from "../utils.js";

export function RiskBadge({ level }) {
  if (!level) return <span className="badge badge-none">Not assessed</span>;
  return <span className={`badge badge-risk-${level.toLowerCase()}`}>{level}</span>;
}

export function StatusBadge({ status }) {
  return <span className={`badge badge-status-${(status || "").toLowerCase()}`}>{titleCase(status)}</span>;
}

export function StatCard({ label, value, hint, tone }) {
  return (
    <div className={`stat-card ${tone ? `tone-${tone}` : ""}`}>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {hint && <div className="stat-hint">{hint}</div>}
    </div>
  );
}

export function Card({ title, actions, children, className = "" }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-head">
          <h3>{title}</h3>
          <div>{actions}</div>
        </header>
      )}
      {children}
    </section>
  );
}

export function Loading({ text = "Loading..." }) {
  return <div className="state state-loading" role="status">{text}</div>;
}

export function Empty({ title = "Nothing here yet", text }) {
  return (
    <div className="state state-empty">
      <strong>{title}</strong>
      {text && <p>{text}</p>}
    </div>
  );
}

export function ErrorBox({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="error-box" role="alert">
      <span>{message}</span>
      {onRetry && <button className="btn btn-small" onClick={onRetry}>Retry</button>}
    </div>
  );
}

export function Modal({ title, onClose, children }) {
  return (
    <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={title}>
        <header className="modal-head">
          <h3>{title}</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Close">×</button>
        </header>
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
}

export function ProbabilityBar({ value }) {
  const pct = Math.round((value || 0) * 100);
  const tone = pct >= 75 ? "high" : pct >= 45 ? "medium" : "low";
  return (
    <div className="prob" title="Heuristic risk score, not a calibrated probability">
      <div className="prob-track"><div className={`prob-fill prob-${tone}`} style={{ width: `${pct}%` }} /></div>
      <span>{pct}%</span>
    </div>
  );
}

export function ReasonList({ reasons }) {
  if (!reasons || reasons.length === 0) return <p className="muted">No risk factors detected.</p>;
  return (
    <ul className="reasons">
      {reasons.map((r) => <li key={r}>{r}</li>)}
    </ul>
  );
}
