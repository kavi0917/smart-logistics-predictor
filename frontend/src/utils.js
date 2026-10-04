export const TRAFFIC = ["LOW", "MEDIUM", "HIGH"];
export const WEATHER = ["CLEAR", "CLOUDY", "RAIN", "STORM"];
export const VEHICLES = ["VAN", "TRUCK", "BIKE", "TEMPO"];
export const STATUSES = ["PENDING", "IN_TRANSIT", "DELIVERED", "DELAYED", "CANCELLED"];
export const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

export const RISK_COLORS = { LOW: "#15803d", MEDIUM: "#d97706", HIGH: "#dc2626" };
export const STATUS_COLORS = { PENDING: "#64748b", IN_TRANSIT: "#2563eb", DELIVERED: "#15803d", DELAYED: "#dc2626", CANCELLED: "#94a3b8" };

/** 535 -> "8h 55m"; 45 -> "45m" */
export function formatMinutes(m) {
  if (m === null || m === undefined || Number.isNaN(Number(m))) return "-";
  const total = Math.round(Number(m));
  const h = Math.floor(total / 60);
  const mins = total % 60;
  return h ? `${h}h ${mins}m` : `${mins}m`;
}

export function formatDateTime(iso) {
  if (!iso) return "-";
  const d = new Date(iso);
  return d.toLocaleString(undefined, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function titleCase(s) {
  return (s || "").toLowerCase().replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export function percent(p) {
  if (p === null || p === undefined) return "-";
  return `${Math.round(p * 100)}%`;
}
