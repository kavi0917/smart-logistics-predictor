import React, { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import api, { errorMessage } from "../api.js";
import { Card, Empty, ErrorBox, Loading, RiskBadge, StatCard } from "../components/ui.jsx";
import { RISK_COLORS, STATUS_COLORS, formatDateTime, titleCase } from "../utils.js";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [perf, setPerf] = useState([]);
  const [acc, setAcc] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [s, p, a, al] = await Promise.all([
        api.get("/api/dashboard/summary"),
        api.get("/api/analytics/performance", { params: { days: 30 } }),
        api.get("/api/analytics/prediction-accuracy", { params: { limit: 20 } }),
        api.get("/api/alerts", { params: { unread_only: true } }),
      ]);
      setData(s.data);
      setPerf(p.data.map((d) => ({ ...d, label: d.date.slice(5) })));
      setAcc(a.data);
      setAlerts(al.data.slice(0, 5));
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const markRead = async (id) => {
    await api.patch(`/api/alerts/${id}/read`);
    load();
  };

  if (error) return <ErrorBox message={error} onRetry={load} />;
  if (!data) return <Loading />;

  const statusData = Object.entries(data.status_distribution).map(([name, value]) => ({ name, value })).filter((d) => d.value > 0);
  const riskData = Object.entries(data.risk_distribution).map(([name, value]) => ({ name, value }));
  const perfData = perf.filter((d) => d.completed > 0);

  return (
    <div>
      <div className="page-head"><h1>Operations Dashboard</h1><button className="btn" onClick={load}>Refresh</button></div>

      <div className="stat-grid">
        <StatCard label="Total shipments" value={data.total_shipments} />
        <StatCard label="Active shipments" value={data.active_shipments} hint="Pending + in transit" />
        <StatCard label="Delivered" value={data.delivered_shipments} hint={`${data.delayed_shipments} delivered late`} />
        <StatCard label="On-time shipments" value={data.on_time_shipments} hint={`${data.on_time_percentage}% of completed`} tone="good" />
        <StatCard label="At-risk (active)" value={data.at_risk_shipments} hint="Medium or high risk" tone="warn" />
        <StatCard label="High-risk (active)" value={data.high_risk_shipments} hint={`${data.unread_alerts} unread alerts`} tone="bad" />
        <StatCard label="Avg ETA error" value={`${data.average_prediction_error} min`} hint="Predicted vs actual" />
        <StatCard label="On-time prediction" value={`${data.on_time_prediction_accuracy}%`} hint="On-time/late call was right" tone="good" />
      </div>

      <div className="grid-2">
        <Card title="Shipment status distribution">
          <div className="chart">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90} paddingAngle={2} label={(d) => d.value}>
                  {statusData.map((d) => <Cell key={d.name} fill={STATUS_COLORS[d.name]} />)}
                </Pie>
                <Tooltip formatter={(v, n) => [v, titleCase(n)]} />
                <Legend formatter={titleCase} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card title="Risk distribution (latest prediction)">
          <div className="chart">
            <ResponsiveContainer>
              <BarChart data={riskData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip />
                <Bar dataKey="value" name="Shipments" radius={[4, 4, 0, 0]}>
                  {riskData.map((d) => <Cell key={d.name} fill={RISK_COLORS[d.name]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Predicted vs actual delivery time (latest 20 delivered)">
          {acc && acc.points.length ? (
            <div className="chart">
              <ResponsiveContainer>
                <LineChart data={acc.points}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="shipment_code" tick={{ fontSize: 10 }} /><YAxis unit="m" /><Tooltip /><Legend />
                  <Line type="linear" dataKey="predicted" name="Predicted" stroke="#2563eb" strokeWidth={2} dot={false} />
                  <Line type="linear" dataKey="actual" name="Actual" stroke="#f59e0b" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty title="No completed shipments yet" text="Record actual delivery times to compare predictions." />}
        </Card>
        <Card title="Average prediction error by day (minutes)">
          {perfData.length ? (
            <div className="chart">
              <ResponsiveContainer>
                <BarChart data={perfData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} /><YAxis /><Tooltip />
                  <Bar dataKey="average_prediction_error" name="Avg error (min)" fill="#64748b" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty />}
        </Card>
      </div>

      <div className="grid-2">
        <Card title="Delivery performance over time (last 30 days)">
          {perfData.length ? (
            <div className="chart">
              <ResponsiveContainer>
                <BarChart data={perfData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} /><YAxis allowDecimals={false} /><Tooltip /><Legend />
                  <Bar dataKey="on_time" name="On time" stackId="a" fill="#15803d" />
                  <Bar dataKey="late" name="Late" stackId="a" fill="#dc2626" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty />}
        </Card>
        <Card title="High-risk alerts" actions={<Link to="/alerts" className="link">View all</Link>}>
          {alerts.length === 0 ? <Empty title="No unread alerts" text="High-risk shipments will appear here." /> : (
            <ul className="alert-list">
              {alerts.map((a) => (
                <li key={a.id}>
                  <div>
                    <Link to={`/shipments/${a.shipment_code}`} className="link strong">{a.shipment_code}</Link> <RiskBadge level={a.risk_level} />
                    <p>{a.message}</p>
                    <small className="muted">{a.reason} · {formatDateTime(a.created_at)}</small>
                  </div>
                  <button className="btn btn-small" onClick={() => markRead(a.id)}>Mark read</button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}
