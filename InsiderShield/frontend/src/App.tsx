import Employees from "./pages/Employees";
import { useEffect, useState, type FormEvent } from "react";
import axios from "axios";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  ClipboardList,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  Mail,
  RefreshCw,
  Shield,
  ShieldAlert,
  Users,
  Zap,
} from "lucide-react";
import api from "./lib/api";
import ThreatDetection from "./pages/ThreatDetection";
import Investigations from "./pages/Investigations";
import ActivityEvents from "./pages/ActivityEvents";

const API_URL = "http://localhost:8000/api/v1";
const LIMIT = 200;

interface User {
  id: string;
  organization_id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

interface Employee {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  department: string | null;
  job_title: string | null;
  is_active: boolean;
}

interface RiskScore {
  id: string;
  employee_id: string;
  risk_score: number;
  risk_level: string;
  contributing_factors: Record<string, unknown>;
  last_calculated_at: string;
}

interface Alert {
  id: string;
  employee_id: string;
  risk_score: number;
  severity: string;
  status: string;
  title: string;
  description: string;
  detection_count: number;
  created_at: string;
}

interface Investigation {
  id: string;
  employee_id: string | null;
  title: string;
  status: string;
  priority: string;
  created_at: string;
}

interface ActivityEvent {
  id: string;
  employee_id: string;
  event_type: string;
  source: string;
  occurred_at: string;
}

interface DashboardData {
  employees: Employee[];
  risks: RiskScore[];
  alerts: Alert[];
  investigations: Investigation[];
  events: ActivityEvent[];
}

function LoginPage({
  onLogin,
}: {
  onLogin: (data: LoginResponse) => void;
}) {
  const [organizationSlug, setOrganizationSlug] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const response = await axios.post<LoginResponse>(
        `${API_URL}/auth/login`,
        {
          organization_slug: organizationSlug,
          email,
          password,
        }
      );

      onLogin(response.data);
    } catch (err) {
      if (axios.isAxiosError(err)) {
        setError(
          err.response?.data?.detail ||
            "Unable to log in. Check your credentials and try again."
        );
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#09090b] px-5 text-zinc-100">
      <div className="w-full max-w-md">
        <div className="mb-9 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-indigo-500/15 text-indigo-400">
            <Shield size={34} />
          </div>
          <h1 className="text-3xl font-bold tracking-tight">InsiderShield</h1>
          <p className="mt-2 text-sm text-zinc-500">
            AI-Powered Insider Threat Intelligence
          </p>
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#111114] p-7 shadow-2xl">
          <h2 className="text-xl font-semibold">Welcome back</h2>
          <p className="mt-2 text-sm text-zinc-500">
            Sign in to your security operations workspace.
          </p>

          <form onSubmit={handleSubmit} className="mt-7 space-y-5">
            <div>
              <label className="mb-2 block text-sm text-zinc-300">
                Organization slug
              </label>
              <input
                required
                value={organizationSlug}
                onChange={(e) => setOrganizationSlug(e.target.value)}
                placeholder="your-organization-slug"
                className="w-full rounded-lg border border-white/10 bg-black/30 px-4 py-3 text-sm outline-none transition focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="mb-2 block text-sm text-zinc-300">
                Email address
              </label>
              <div className="relative">
                <Mail
                  size={17}
                  className="absolute left-3 top-3.5 text-zinc-500"
                />
                <input
                  required
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@example.com"
                  className="w-full rounded-lg border border-white/10 bg-black/30 py-3 pl-10 pr-4 text-sm outline-none transition focus:border-indigo-500"
                />
              </div>
            </div>

            <div>
              <label className="mb-2 block text-sm text-zinc-300">
                Password
              </label>
              <div className="relative">
                <LockKeyhole
                  size={17}
                  className="absolute left-3 top-3.5 text-zinc-500"
                />
                <input
                  required
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full rounded-lg border border-white/10 bg-black/30 py-3 pl-10 pr-4 text-sm outline-none transition focus:border-indigo-500"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 py-3 font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Signing in..." : "Sign in to InsiderShield"}
            </button>
          </form>

          <p className="mt-6 text-center text-xs text-zinc-600">
            Secured access Â· InsiderShield Security Operations
          </p>
        </div>
      </div>
    </div>
  );
}

function formatTime(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";

  return date.toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function severityClass(severity: string) {
  const value = severity.toLowerCase();

  if (value === "critical") return "bg-red-500/10 text-red-400";
  if (value === "high") return "bg-orange-500/10 text-orange-400";
  if (value === "medium") return "bg-amber-500/10 text-amber-400";

  return "bg-emerald-500/10 text-emerald-400";
}

function Dashboard({
  user,
  onLogout,
}: {
  user: User;
  onLogout: () => void;
}) {
  const [activePage, setActivePage] = useState("Overview");
  const [data, setData] = useState<DashboardData>({
    employees: [],
    risks: [],
    alerts: [],
    investigations: [],
    events: [],
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [employees, risks, alerts, investigations, events] =
        await Promise.all([
          api.get<Employee[]>("/employees", {
            params: { limit: LIMIT, offset: 0 },
          }),
          api.get<RiskScore[]>("/risk-scores", {
            params: { limit: LIMIT, offset: 0 },
          }),
          api.get<Alert[]>("/alerts", {
            params: { limit: LIMIT, offset: 0 },
          }),
          api.get<Investigation[]>("/investigations", {
            params: { limit: LIMIT, offset: 0 },
          }),
          api.get<ActivityEvent[]>("/events", {
            params: { limit: LIMIT, offset: 0 },
          }),
        ]);

      setData({
        employees: employees.data,
        risks: risks.data,
        alerts: alerts.data,
        investigations: investigations.data,
        events: events.data,
      });
    } catch (err) {
      console.error("Dashboard loading failed:", err);
      setError(
        axios.isAxiosError(err)
          ? err.response?.data?.detail || "Unable to load dashboard data."
          : "An unexpected error occurred while loading dashboard data."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  const activeAlerts = data.alerts.filter(
    (alert) =>
      alert.status.toLowerCase() === "open" ||
      alert.status.toLowerCase() === "acknowledged"
  );

  const openInvestigations = data.investigations.filter(
    (item) =>
      item.status.toLowerCase() === "open" ||
      item.status.toLowerCase() === "in_progress"
  );

  const employeeMap = new Map(
    data.employees.map((employee) => [employee.id, employee])
  );

  const riskGroups = [
    {
      label: "Critical",
      color: "bg-red-500",
      levels: ["critical"],
    },
    {
      label: "High",
      color: "bg-orange-400",
      levels: ["high"],
    },
    {
      label: "Medium",
      color: "bg-amber-400",
      levels: ["medium"],
    },
    {
      label: "Low",
      color: "bg-emerald-400",
      levels: ["low"],
    },
  ];

  const totalRiskRecords = data.risks.length;

  const riskDistribution = riskGroups.map((group) => {
    const count = data.risks.filter((risk) =>
      group.levels.includes(risk.risk_level.toLowerCase())
    ).length;

    return {
      ...group,
      count,
      percentage:
        totalRiskRecords > 0
          ? Math.round((count / totalRiskRecords) * 100)
          : 0,
    };
  });

  const lastSevenDays = Array.from({ length: 7 }, (_, index) => {
    const date = new Date();
    date.setHours(0, 0, 0, 0);
    date.setDate(date.getDate() - (6 - index));

    const nextDate = new Date(date);
    nextDate.setDate(nextDate.getDate() + 1);

    const count = data.events.filter((event) => {
      const eventDate = new Date(event.occurred_at);
      return eventDate >= date && eventDate < nextDate;
    }).length;

    return {
      label: date.toLocaleDateString([], { weekday: "short" }),
      count,
    };
  });

  const maxEvents = Math.max(
    ...lastSevenDays.map((day) => day.count),
    1
  );

  const stats = [
    {
      label: "Employees Loaded",
      value: data.employees.length,
      subtitle: `Latest ${LIMIT} records maximum`,
      icon: Users,
      color: "text-blue-400",
      bg: "bg-blue-400/10",
    },
    {
      label: "Active Threats",
      value: activeAlerts.length,
      subtitle: "Open and acknowledged alerts loaded",
      icon: ShieldAlert,
      color: "text-red-400",
      bg: "bg-red-400/10",
    },
    {
      label: "Open Investigations",
      value: openInvestigations.length,
      subtitle: "Open and in-progress records loaded",
      icon: ClipboardList,
      color: "text-amber-400",
      bg: "bg-amber-400/10",
    },
    {
      label: "Events Retrieved",
      value: data.events.length,
      subtitle: `Latest ${LIMIT} records maximum`,
      icon: Activity,
      color: "text-emerald-400",
      bg: "bg-emerald-400/10",
    },
  ];

  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-white/10 bg-[#0d0d10] lg:flex lg:flex-col">
        <div className="flex h-20 items-center gap-3 border-b border-white/10 px-6">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/15 text-indigo-400">
            <Shield size={23} />
          </div>
          <div>
            <h1 className="text-lg font-bold">InsiderShield</h1>
            <p className="text-xs text-zinc-500">
              Insider Threat Intelligence
            </p>
          </div>
        </div>

        <div className="px-4 py-6">
          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
            Workspace
          </p>
          <nav className="space-y-1">
            {[
              { name: "Overview", icon: LayoutDashboard },
              { name: "Threat Detection", icon: ShieldAlert },
              { name: "Employees", icon: Users },
              { name: "Investigations", icon: ClipboardList },
              { name: "Activity Events", icon: Activity },
            ].map((item) => (
              <button
                key={item.name}
                onClick={() => setActivePage(item.name)}
                className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 text-sm transition ${
                  activePage === item.name
                    ? "bg-indigo-500/15 font-medium text-indigo-300"
                    : "text-zinc-400 hover:bg-white/5 hover:text-white"
                }`}
              >
                <item.icon size={18} />
                {item.name}
              </button>
            ))}
          </nav>
        </div>

        <div className="mt-auto border-t border-white/10 p-4">
          <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
            <div className="mb-2 flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-medium text-emerald-400">
                System Operational
              </span>
            </div>
            <p className="text-xs text-zinc-500">
              Dashboard connected to backend services.
            </p>
          </div>

          <div className="mt-4 flex items-center gap-3 px-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-500/20 text-sm font-semibold text-indigo-300">
              {user.full_name.slice(0, 2).toUpperCase()}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">
                {user.full_name}
              </p>
              <p className="text-xs capitalize text-zinc-500">
                {user.role}
              </p>
            </div>
            <button
              onClick={onLogout}
              title="Log out"
              className="text-zinc-500 hover:text-white"
            >
              <LogOut size={17} />
            </button>
          </div>
        </div>
      </aside>

      <main className="lg:pl-64">
        <header className="sticky top-0 z-10 flex h-20 items-center justify-between border-b border-white/10 bg-[#09090b]/90 px-5 backdrop-blur-xl md:px-8">
          <div>
            <p className="text-xs text-zinc-500">
              Security Operations / {activePage}
            </p>
            <h2 className="mt-1 text-lg font-semibold">
              {activePage === "Overview" ? "Security Dashboard" : activePage}
            </h2>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden text-sm text-zinc-400 sm:block">
              {user.email}
            </span>
            <button
              onClick={loadDashboard}
              disabled={loading}
              title="Refresh dashboard"
              className="rounded-lg border border-white/10 p-2 text-zinc-400 transition hover:text-white disabled:opacity-50"
            >
              <RefreshCw
                size={17}
                className={loading ? "animate-spin" : ""}
              />
            </button>
            <button
              onClick={onLogout}
              className="flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-zinc-400 hover:text-white"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>

        <div className="space-y-7 p-5 md:p-8">
          {activePage === "Threat Detection" ? (
  <ThreatDetection userRole={user.role} />
) : activePage === "Employees" ? (
  <Employees />
) : activePage === "Investigations" ? (
  <Investigations />
) : activePage === "Activity Events" ? (
  <ActivityEvents />
) : activePage === "Overview" ? (
  <>
          <section>
            <h2 className="text-2xl font-semibold">Security Overview</h2>
            <p className="mt-2 text-sm text-zinc-500">
              Monitor insider activity, detect anomalies, and investigate threats.
            </p>
          </section>

          {error && (
            <div className="flex items-start gap-3 rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
              <AlertTriangle size={19} className="mt-0.5 shrink-0" />
              <div>
                <p className="font-medium">Dashboard data could not be loaded</p>
                <p className="mt-1 text-red-300/80">{error}</p>
                <button
                  onClick={loadDashboard}
                  className="mt-3 underline underline-offset-4"
                >
                  Try again
                </button>
              </div>
            </div>
          )}

          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {stats.map((stat) => (
              <div
                key={stat.label}
                className="rounded-xl border border-white/10 bg-[#111114] p-5"
              >
                <div className="flex items-center justify-between">
                  <p className="text-sm text-zinc-500">{stat.label}</p>
                  <div className={`rounded-lg p-2 ${stat.bg} ${stat.color}`}>
                    <stat.icon size={19} />
                  </div>
                </div>
                <p className="mt-5 text-3xl font-semibold">
                  {loading ? "â€”" : stat.value.toLocaleString()}
                </p>
                <p className="mt-2 text-xs text-zinc-500">
                  {stat.subtitle}
                </p>
              </div>
            ))}
          </section>

          <section className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
            <div className="rounded-xl border border-white/10 bg-[#111114] p-5">
              <h3 className="font-semibold">Threat Activity</h3>
              <p className="mt-1 text-xs text-zinc-500">
                Events received per day Â· Last 7 days
              </p>

              <div className="mt-8 flex h-48 items-end gap-3">
                {lastSevenDays.map((day) => (
                  <div
                    key={day.label}
                    className="flex h-full flex-1 flex-col items-center justify-end gap-2"
                  >
                    <span className="text-xs text-zinc-500">
                      {loading ? "â€”" : day.count}
                    </span>
                    <div className="flex h-full w-full items-end">
                      <div
                        className="w-full rounded-t-sm bg-indigo-500/70 transition-all"
                        style={{
                          height: loading
                            ? "0%"
                            : `${(day.count / maxEvents) * 100}%`,
                          minHeight:
                            !loading && day.count > 0 ? "5px" : "0",
                        }}
                      />
                    </div>
                    <span className="text-xs text-zinc-500">
                      {day.label}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-white/10 bg-[#111114] p-5">
              <h3 className="font-semibold">Risk Distribution</h3>
              <p className="mt-1 text-xs text-zinc-500">
                Based on loaded employee risk scores
              </p>

              <div className="mt-7 space-y-6">
                {riskDistribution.map((risk) => (
                  <div key={risk.label}>
                    <div className="mb-2 flex justify-between text-sm">
                      <span>{risk.label}</span>
                      <span className="text-zinc-500">
                        {loading ? "â€”" : `${risk.percentage}% (${risk.count})`}
                      </span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-white/5">
                      <div
                        className={`h-full ${risk.color} transition-all`}
                        style={{
                          width: loading ? "0%" : `${risk.percentage}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}

                {!loading && totalRiskRecords === 0 && (
                  <p className="text-sm text-zinc-500">
                    No risk scores available yet.
                  </p>
                )}
              </div>
            </div>
          </section>

          <section className="overflow-hidden rounded-xl border border-white/10 bg-[#111114]">
            <div className="border-b border-white/10 p-5">
              <h3 className="font-semibold">Recent Security Alerts</h3>
              <p className="mt-1 text-xs text-zinc-500">
                Latest alerts returned by the backend
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full min-w-[650px] text-left text-sm">
                <thead className="bg-white/[0.02] text-xs text-zinc-500">
                  <tr>
                    <th className="px-5 py-4">Employee</th>
                    <th className="px-5 py-4">Alert</th>
                    <th className="px-5 py-4">Status</th>
                    <th className="px-5 py-4">Severity</th>
                    <th className="px-5 py-4">Detected</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-white/5">
                  {!loading &&
                    data.alerts.slice(0, 8).map((alert) => {
                      const employee = employeeMap.get(alert.employee_id);

                      return (
                        <tr key={alert.id}>
                          <td className="px-5 py-4 font-medium">
                            {employee?.full_name || "Unknown employee"}
                          </td>
                          <td className="max-w-xs px-5 py-4 text-zinc-400">
                            <p className="truncate">{alert.title}</p>
                          </td>
                          <td className="px-5 py-4 capitalize text-zinc-400">
                            {alert.status.replace("_", " ")}
                          </td>
                          <td className="px-5 py-4">
                            <span
                              className={`rounded-md px-2.5 py-1 text-xs ${severityClass(alert.severity)}`}
                            >
                              {alert.severity}
                            </span>
                          </td>
                          <td className="px-5 py-4 text-xs text-zinc-500">
                            {formatTime(alert.created_at)}
                          </td>
                        </tr>
                      );
                    })}

                  {!loading && data.alerts.length === 0 && (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-5 py-10 text-center text-zinc-500"
                      >
                        No security alerts found.
                      </td>
                    </tr>
                  )}

                  {loading && (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-5 py-10 text-center text-zinc-500"
                      >
                        Loading security alerts...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-2">
            <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-[#111114] p-5">
              <BrainCircuit size={25} className="text-indigo-400" />
              <div>
                <h3 className="font-medium">AI Detection Engine</h3>
                <p className="mt-1 text-xs text-zinc-500">
                  Anomaly detection pipeline
                </p>
              </div>
              <span className="ml-auto flex items-center gap-1 text-xs text-emerald-400">
                <CheckCircle2 size={14} /> Ready
              </span>
            </div>

            <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-[#111114] p-5">
              <Zap size={25} className="text-amber-400" />
              <div>
                <h3 className="font-medium">Event Processing</h3>
                <p className="mt-1 text-xs text-zinc-500">
                  Background event processing
                </p>
              </div>
              <span className="ml-auto flex items-center gap-1 text-xs text-emerald-400">
                <CheckCircle2 size={14} /> Ready
              </span>
            </div>
          </section>

          <footer className="border-t border-white/10 pt-5 text-xs text-zinc-600">
            InsiderShield Â· AI-Powered Insider Threat Detection Â· Live backend data
            <span className="block mt-1">
              Dashboard metrics reflect the latest {LIMIT} records returned per API.
            </span>
          </footer>
            </>
          ) : (
            <div className="rounded-xl border border-white/10 bg-[#111114] p-8">
              <h2 className="text-xl font-semibold">{activePage}</h2>
              <p className="mt-2 text-sm text-zinc-500">
                This module will be connected to the backend in the next development step.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function App() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const savedUser = localStorage.getItem("insidershield_user");
    const savedToken = localStorage.getItem("insidershield_token");

    if (savedUser && savedToken) {
      try {
        setUser(JSON.parse(savedUser) as User);
      } catch {
        localStorage.removeItem("insidershield_user");
        localStorage.removeItem("insidershield_token");
      }
    }
  }, []);

  function handleLogin(data: LoginResponse) {
    localStorage.setItem("insidershield_token", data.access_token);
    localStorage.setItem("insidershield_user", JSON.stringify(data.user));
    setUser(data.user);
  }

  function handleLogout() {
    localStorage.removeItem("insidershield_token");
    localStorage.removeItem("insidershield_user");
    setUser(null);
  }

  return user ? (
    <Dashboard user={user} onLogout={handleLogout} />
  ) : (
    <LoginPage onLogin={handleLogin} />
  );
}

export default App;
