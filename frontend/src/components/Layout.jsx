import React, { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import api from "../api.js";
import { useAuth } from "../auth.jsx";

const NAV = [
  ["/dashboard", "Dashboard"],
  ["/shipments", "Shipments"],
  ["/predictions", "Predictions"],
  ["/alerts", "Alerts"],
  ["/analytics", "Analytics"],
  ["/what-if", "What-If Simulation"],
  ["/settings", "Settings"],
];

export default function Layout() {
  const { email, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const location = useLocation();

  useEffect(() => {
    setOpen(false);
    api.get("/api/alerts", { params: { unread_only: true } })
      .then((r) => setUnread(r.data.length))
      .catch(() => {});
  }, [location.pathname]);

  return (
    <div className="app-shell">
      <button className="menu-toggle" onClick={() => setOpen(!open)} aria-label="Toggle navigation">☰</button>
      <aside className={`sidebar ${open ? "open" : ""}`}>
        <div className="brand">
          <span className="brand-mark">▮▮▶</span>
          <div>
            <div className="brand-name">Smart Logistics</div>
            <div className="brand-sub">Delivery Prediction</div>
          </div>
        </div>
        <nav>
          {NAV.map(([to, label]) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`}>
              {label}
              {to === "/alerts" && unread > 0 && <span className="nav-count">{unread}</span>}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-foot">
          <div className="user-line" title={email}>{email}</div>
          <button className="btn btn-ghost" onClick={logout}>Sign out</button>
        </div>
      </aside>
      <main className="content"><Outlet /></main>
    </div>
  );
}
