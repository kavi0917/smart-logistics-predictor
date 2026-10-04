import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";
import Layout from "./components/Layout.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Shipments from "./pages/Shipments.jsx";
import ShipmentDetail from "./pages/ShipmentDetail.jsx";
import Predictions from "./pages/Predictions.jsx";
import Alerts from "./pages/Alerts.jsx";
import Analytics from "./pages/Analytics.jsx";
import WhatIf from "./pages/WhatIf.jsx";
import Settings from "./pages/Settings.jsx";

export function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/shipments" element={<Shipments />} />
        <Route path="/shipments/:id" element={<ShipmentDetail />} />
        <Route path="/predictions" element={<Predictions />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/what-if" element={<WhatIf />} />
        <Route path="/settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
