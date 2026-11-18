
import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  RefreshCw,
  Search,
  ShieldAlert,
  X,
} from "lucide-react";
import api from "../lib/api";

interface Alert {
  id: string;
  employee_id: string;
  risk_score: number;
  severity: string;
  status: string;
  title: string;
  description: string | null;
  detection_count: number;
  contributing_factors: Record<string, unknown>;
  created_at: string;
}

interface Employee {
  id: string;
  full_name: string;
  employee_code: string;
  department: string | null;
  email: string;
}

type StatusFilter = "all" | "open" | "acknowledged" | "resolved";
type SeverityFilter = "all" | "critical" | "high" | "medium" | "low";

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return "Unknown";

  return date.toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function severityStyle(severity: string) {
  switch (severity.toLowerCase()) {
    case "critical":
      return "bg-red-500/10 text-red-400 border-red-500/20";
    case "high":
      return "bg-orange-500/10 text-orange-400 border-orange-500/20";
    case "medium":
      return "bg-amber-500/10 text-amber-400 border-amber-500/20";
    default:
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
  }
}

function statusStyle(status: string) {
  switch (status.toLowerCase()) {
    case "open":
      return "bg-red-500/10 text-red-400";
    case "acknowledged":
      return "bg-amber-500/10 text-amber-400";
    default:
      return "bg-emerald-500/10 text-emerald-400";
  }
}

export default function ThreatDetection({ userRole }: { userRole: string }) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [severityFilter, setSeverityFilter] =
    useState<SeverityFilter>("all");
  const [search, setSearch] = useState("");
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const canUpdate = ["admin", "analyst"].includes(userRole.toLowerCase());

  async function loadAlerts() {
    setLoading(true);
    setError("");

    try {
      const params: Record<string, string | number> = {
        limit: 200,
        offset: 0,
      };

      if (statusFilter !== "all") {
        params.status = statusFilter;
      }

      if (severityFilter !== "all") {
        params.severity = severityFilter;
      }

      const [alertResponse, employeeResponse] = await Promise.all([
        api.get<Alert[]>("/alerts", { params }),
        api.get<Employee[]>("/employees", {
          params: { limit: 200, offset: 0 },
        }),
      ]);

      setAlerts(alertResponse.data);
      setEmployees(employeeResponse.data);

      if (selectedAlert) {
        const updated = alertResponse.data.find(
          (alert) => alert.id === selectedAlert.id
        );
        setSelectedAlert(updated || null);
      }
    } catch (err) {
      console.error("Threat detection loading failed:", err);
      setError(
        "Unable to load alerts. Please check the backend connection and try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, severityFilter]);

  const employeeMap = useMemo(
    () => new Map(employees.map((employee) => [employee.id, employee])),
    [employees]
  );

  const filteredAlerts = alerts.filter((alert) => {
    const employee = employeeMap.get(alert.employee_id);
    const query = search.trim().toLowerCase();

    if (!query) return true;

    return [
      alert.title,
      alert.description || "",
      alert.severity,
      alert.status,
      employee?.full_name || "",
      employee?.employee_code || "",
      employee?.email || "",
    ].some((value) => value.toLowerCase().includes(query));
  });

  const counts = {
    total: alerts.length,
    open: alerts.filter((a) => a.status === "open").length,
    acknowledged: alerts.filter((a) => a.status === "acknowledged").length,
    resolved: alerts.filter((a) => a.status === "resolved").length,
  };

  async function updateStatus(alert: Alert, nextStatus: string) {
    if (!canUpdate || updatingId) return;

    setUpdatingId(alert.id);
    setError("");
    setNotice("");

    try {
      const response = await api.patch<Alert>(
        `/alerts/${alert.id}/status`,
        { status: nextStatus }
      );

      setAlerts((current) =>
        current.map((item) =>
          item.id === alert.id ? response.data : item
        )
      );

      setSelectedAlert(response.data);
      setNotice(`Alert successfully ${nextStatus}.`);
    } catch (err: any) {
      console.error("Alert status update failed:", err);

      setError(
        err.response?.data?.detail ||
          "Unable to update alert status. Please try again."
      );
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="text-indigo-400" size={25} />
            <h2 className="text-2xl font-semibold">Threat Detection</h2>
          </div>
          <p className="mt-2 text-sm text-zinc-500">
            Review, investigate and manage detected insider threats.
          </p>
        </div>

        <button
          onClick={loadAlerts}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-lg border border-white/10 px-4 py-2.5 text-sm text-zinc-300 transition hover:bg-white/5 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh alerts
        </button>
      </section>

      {error && (
        <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          <AlertTriangle size={18} />
          {error}
        </div>
      )}

      {notice && (
        <div className="flex items-center justify-between rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-300">
          <span className="flex items-center gap-2">
            <CheckCircle2 size={17} />
            {notice}
          </span>
          <button onClick={() => setNotice("")} aria-label="Dismiss">
            <X size={16} />
          </button>
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Alerts Loaded",
            value: counts.total,
            color: "text-indigo-400",
          },
          {
            label: "Open",
            value: counts.open,
            color: "text-red-400",
          },
          {
            label: "Acknowledged",
            value: counts.acknowledged,
            color: "text-amber-400",
          },
          {
            label: "Resolved",
            value: counts.resolved,
            color: "text-emerald-400",
          },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-white/10 bg-[#111114] p-5"
          >
            <p className="text-sm text-zinc-500">{item.label}</p>
            <p className={`mt-4 text-3xl font-semibold ${item.color}`}>
              {loading ? "—" : item.value}
            </p>
            <p className="mt-2 text-xs text-zinc-600">
              Latest 200 matching records maximum
            </p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-white/10 bg-[#111114] p-5">
        <div className="grid gap-4 md:grid-cols-[1fr_190px_190px]">
          <div className="relative">
            <Search
              size={17}
              className="absolute left-3 top-3.5 text-zinc-500"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search employee, alert or activity..."
              className="w-full rounded-lg border border-white/10 bg-black/30 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500"
            />
          </div>

          <div className="relative">
            <select
              value={statusFilter}
              onChange={(e) =>
                setStatusFilter(e.target.value as StatusFilter)
              }
              className="w-full appearance-none rounded-lg border border-white/10 bg-[#09090b] px-4 py-3 pr-9 text-sm text-zinc-300 outline-none focus:border-indigo-500"
            >
              <option value="all">All statuses</option>
              <option value="open">Open</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="resolved">Resolved</option>
            </select>
            <ChevronDown
              size={15}
              className="pointer-events-none absolute right-3 top-3.5 text-zinc-500"
            />
          </div>

          <div className="relative">
            <select
              value={severityFilter}
              onChange={(e) =>
                setSeverityFilter(e.target.value as SeverityFilter)
              }
              className="w-full appearance-none rounded-lg border border-white/10 bg-[#09090b] px-4 py-3 pr-9 text-sm text-zinc-300 outline-none focus:border-indigo-500"
            >
              <option value="all">All severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <ChevronDown
              size={15}
              className="pointer-events-none absolute right-3 top-3.5 text-zinc-500"
            />
          </div>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-white/10 bg-[#111114]">
        <div className="border-b border-white/10 p-5">
          <h3 className="font-semibold">Security Alert Queue</h3>
          <p className="mt-1 text-xs text-zinc-500">
            Select an alert to inspect its details and contributing factors.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="bg-white/[0.02] text-xs text-zinc-500">
              <tr>
                <th className="px-5 py-4">Employee</th>
                <th className="px-5 py-4">Alert</th>
                <th className="px-5 py-4">Risk score</th>
                <th className="px-5 py-4">Severity</th>
                <th className="px-5 py-4">Status</th>
                <th className="px-5 py-4">Detected</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/5">
              {loading && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-zinc-500">
                    Loading security alerts...
                  </td>
                </tr>
              )}

              {!loading &&
                filteredAlerts.map((alert) => {
                  const employee = employeeMap.get(alert.employee_id);

                  return (
                    <tr
                      key={alert.id}
                      onClick={() => setSelectedAlert(alert)}
                      className={`cursor-pointer transition hover:bg-white/[0.03] ${
                        selectedAlert?.id === alert.id
                          ? "bg-indigo-500/[0.07]"
                          : ""
                      }`}
                    >
                      <td className="px-5 py-4">
                        <p className="font-medium">
                          {employee?.full_name || "Unknown employee"}
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {employee?.department || "Department unavailable"}
                        </p>
                      </td>

                      <td className="max-w-xs px-5 py-4">
                        <p className="truncate text-zinc-300">
                          {alert.title}
                        </p>
                      </td>

                      <td className="px-5 py-4 font-semibold">
                        {Number(alert.risk_score).toFixed(1)}
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`rounded-md border px-2.5 py-1 text-xs capitalize ${severityStyle(alert.severity)}`}
                        >
                          {alert.severity}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`rounded-md px-2.5 py-1 text-xs capitalize ${statusStyle(alert.status)}`}
                        >
                          {alert.status}
                        </span>
                      </td>

                      <td className="px-5 py-4 text-xs text-zinc-500">
                        {formatDate(alert.created_at)}
                      </td>
                    </tr>
                  );
                })}

              {!loading && filteredAlerts.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-12 text-center text-zinc-500"
                  >
                    No alerts match the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {selectedAlert && (
        <section className="rounded-xl border border-indigo-500/20 bg-[#111114] p-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
                Alert details
              </p>
              <h3 className="mt-2 text-lg font-semibold">
                {selectedAlert.title}
              </h3>
            </div>
            <button
              onClick={() => setSelectedAlert(null)}
              className="rounded-lg p-2 text-zinc-500 hover:bg-white/5 hover:text-white"
              aria-label="Close alert details"
            >
              <X size={18} />
            </button>
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div>
              <p className="text-xs text-zinc-500">Employee</p>
              <p className="mt-1 text-sm">
                {employeeMap.get(selectedAlert.employee_id)?.full_name ||
                  "Unknown employee"}
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500">Risk score</p>
              <p className="mt-1 text-sm font-semibold">
                {Number(selectedAlert.risk_score).toFixed(2)} / 100
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500">Detection count</p>
              <p className="mt-1 text-sm">
                {selectedAlert.detection_count}
              </p>
            </div>
            <div>
              <p className="text-xs text-zinc-500">Detected at</p>
              <p className="mt-1 text-sm">
                {formatDate(selectedAlert.created_at)}
              </p>
            </div>
          </div>

          {selectedAlert.description && (
            <div className="mt-5">
              <p className="text-xs text-zinc-500">Description</p>
              <p className="mt-2 text-sm leading-6 text-zinc-300">
                {selectedAlert.description}
              </p>
            </div>
          )}

          <div className="mt-5">
            <p className="text-sm font-medium">Contributing factors</p>
            <pre className="mt-3 max-h-64 overflow-auto rounded-lg border border-white/10 bg-black/30 p-4 text-xs leading-6 text-zinc-300">
              {JSON.stringify(
                selectedAlert.contributing_factors || {},
                null,
                2
              )}
            </pre>
          </div>

          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-5">
            <p className="text-xs text-zinc-500">
              Current status:{" "}
              <span className="capitalize text-zinc-300">
                {selectedAlert.status}
              </span>
            </p>

            {canUpdate && (
              <div className="flex flex-wrap gap-3">
                {selectedAlert.status === "open" && (
                  <button
                    onClick={() =>
                      updateStatus(selectedAlert, "acknowledged")
                    }
                    disabled={updatingId === selectedAlert.id}
                    className="rounded-lg bg-amber-500/15 px-4 py-2.5 text-sm font-medium text-amber-300 transition hover:bg-amber-500/25 disabled:opacity-50"
                  >
                    {updatingId === selectedAlert.id
                      ? "Updating..."
                      : "Acknowledge alert"}
                  </button>
                )}

                {selectedAlert.status === "acknowledged" && (
                  <button
                    onClick={() =>
                      updateStatus(selectedAlert, "resolved")
                    }
                    disabled={updatingId === selectedAlert.id}
                    className="rounded-lg bg-emerald-500/15 px-4 py-2.5 text-sm font-medium text-emerald-300 transition hover:bg-emerald-500/25 disabled:opacity-50"
                  >
                    {updatingId === selectedAlert.id
                      ? "Updating..."
                      : "Resolve alert"}
                  </button>
                )}

                {selectedAlert.status === "resolved" && (
                  <span className="flex items-center gap-2 text-sm text-emerald-400">
                    <CheckCircle2 size={17} />
                    Alert resolved
                  </span>
                )}
              </div>
            )}

            {!canUpdate && (
              <p className="text-xs text-zinc-500">
                Your role has read-only access to alert management.
              </p>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
