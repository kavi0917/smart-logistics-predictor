import React, { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis } from "recharts";
import api, { errorMessage } from "../api.js";
import { Card, Empty, ErrorBox, Loading, StatCard } from "../components/ui.jsx";
import { RISK_COLORS } from "../utils.js";

export default function Analytics() {
  const [summary, setSummary] = useState(null);
  const [risk, setRisk] = useState(null);
  const [perf, setPerf] = useState([]);
  const [acc, setAcc] = useState(null);
  const [days, setDays] = useState(30);
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    Promise.all([
      api.get("/api/analytics/summary"),
      api.get("/api/analytics/risk-distribution"),
      api.get("/api/analytics/performance", { params: { days } }),
      api.get("/api/analytics/prediction-accuracy", { params: { limit: 60 } }),
    ]).then(([s, r, p, a]) => {
      setSummary(s.data);
      setRisk(Object.entries(r.data).map(([name, value]) => ({ name, value })));
      setPerf(p.data.map((d) => ({ ...d, label: d.date.slice(5) })));
      setAcc(a.data);
    }).catch((e) => setError(errorMessage(e)));
  }, [days]);

  if (error) return <ErrorBox message={error} />;
  if (!summary || !acc) return <Loading />;

  const perfData = perf.filter((d) => d.completed > 0);
  const maxVal = Math.max(1, ...acc.points.flatMap((p) => [p.predicted, p.actual]));

  return (
    <div>
      <div className="page-head">
        <h1>Analytics</h1>
        <select value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={7}>Last 7 days</option><option value={14}>Last 14 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option>
        </select>
      </div>
      <div className="stat-grid">
        <StatCard label="Mean absolute error" value={`${acc.mean_absolute_error} min`} hint={`${acc.evaluated_shipments} delivered shipments`} />
        <StatCard label="RMSE" value={`${acc.rmse} min`} />
        <StatCard label="Within 15 minutes" value={`${acc.within_15_minutes_pct}%`} hint="Predictions this close" tone="good" />
        <StatCard label="Within 10% of actual" value={`${acc.within_10_percent_pct}%`} tone="good" />
        <StatCard label="On-time call accuracy" value={`${acc.on_time_prediction_accuracy}%`} hint="Late/on-time predicted correctly" tone="good" />
        <StatCard label="Actual on-time rate" value={`${summary.on_time_percentage}%`} hint={`${summary.completed_shipments} completed`} />
      </div>

      <div className="grid-2">
        <Card title="Prediction accuracy: predicted vs actual (minutes)">
          {acc.points.length ? (
            <div className="chart">
              <ResponsiveContainer>
                <ScatterChart margin={{ left: 0, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" dataKey="predicted" name="Predicted" unit="m" domain={[0, "dataMax"]} />
                  <YAxis type="number" dataKey="actual" name="Actual" unit="m" domain={[0, "dataMax"]} />
                  <ZAxis range={[40, 40]} />
                  <Tooltip cursor={{ strokeDasharray: "3 3" }} />
                  <ReferenceLine segment={[{ x: 0, y: 0 }, { x: maxVal, y: maxVal }]} stroke="#94a3b8" strokeDasharray="5 5" label="perfect" />
                  <Scatter data={acc.points} fill="#2563eb" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty />}
          <p className="muted small">Points close to the dashed line are accurate predictions.</p>
        </Card>
        <Card title="Absolute error per delivered shipment (min)">
          {acc.points.length ? (
            <div className="chart">
              <ResponsiveContainer>
                <BarChart data={acc.points}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="shipment_code" tick={{ fontSize: 9 }} interval="preserveStartEnd" /><YAxis /><Tooltip />
                  <Bar dataKey="error" name="Error (min)" fill="#64748b" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty />}
        </Card>
      </div>

      <div className="grid-2">
        <Card title="On-time percentage by day">
          {perfData.length ? (
            <div className="chart">
              <ResponsiveContainer>
                <LineChart data={perfData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" tick={{ fontSize: 10 }} /><YAxis domain={[0, 100]} unit="%" /><Tooltip /><Legend />
                  <Line type="monotone" dataKey="on_time_percentage" name="On-time %" stroke="#15803d" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : <Empty title="No completed shipments in this period" />}
        </Card>
        <Card title="Current risk distribution">
          <div className="chart">
            <ResponsiveContainer>
              <BarChart data={risk}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip />
                <Bar dataKey="value" name="Shipments" radius={[4, 4, 0, 0]}>{risk.map((d) => <Cell key={d.name} fill={RISK_COLORS[d.name]} />)}</Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
