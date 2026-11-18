import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  Activity,
  AlertTriangle,
  Clock3,
  FilePlus2,
  Link2,
  Plus,
  RefreshCw,
  Search,
  Shield,
  X,
} from "lucide-react";
import api from "../lib/api";

type Priority = "low" | "medium" | "high" | "critical";
type Status = "open" | "in_progress" | "closed";

interface Investigation {
  id: string;
  organization_id: string;
  employee_id: string | null;
  title: string;
  description: string | null;
  status: Status;
  priority: Priority;
  assigned_to: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
  closed_at: string | null;
}

interface Employee {
  id: string;
  full_name: string;
  employee_code: string;
  is_active: boolean;
}

interface Alert {
  id: string;
  title: string;
  severity: string;
  risk_score: number;
  status: string;
}

interface LinkedAlert {
  investigation_id: string;
  alert_id: string;
  linked_at: string;
  linked_by: string | null;
}

interface AuditEntry {
  id: string;
  investigation_id: string;
  actor_id: string | null;
  action: string;
  details: Record<string, unknown>;
  created_at: string;
}

const LIMIT = 200;

const priorityStyles: Record<Priority, string> = {
  low: "border-slate-500/20 bg-slate-500/10 text-slate-300",
  medium: "border-blue-500/20 bg-blue-500/10 text-blue-300",
  high: "border-amber-500/20 bg-amber-500/10 text-amber-300",
  critical: "border-red-500/20 bg-red-500/10 text-red-300",
};

const statusStyles: Record<Status, string> = {
  open: "border-blue-500/20 bg-blue-500/10 text-blue-300",
  in_progress: "border-violet-500/20 bg-violet-500/10 text-violet-300",
  closed: "border-zinc-500/20 bg-zinc-500/10 text-zinc-400",
};

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Unknown date"
    : date.toLocaleString([], {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
}

function getErrorMessage(error: unknown) {
  if (
    typeof error === "object" &&
    error !== null &&
    "response" in error
  ) {
    const response = (error as {
      response?: { data?: { detail?: string } };
    }).response;

    if (response?.data?.detail) return response.data.detail;
  }

  return "Something went wrong. Please try again.";
}

function Badge({
  children,
  className,
}: {
  children: ReactNode;
  className: string;
}) {
  return (
    <span
      className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${className}`}
    >
      {children}
    </span>
  );
}

function FieldLabel({ children }: { children: ReactNode }) {
  return (
    <label className="mb-2 block text-sm font-medium text-zinc-300">
      {children}
    </label>
  );
}

const inputClass =
  "w-full rounded-lg border border-white/10 bg-[#09090b] px-3 py-2.5 text-sm text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-indigo-500";

export default function Investigations() {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [linkedAlerts, setLinkedAlerts] = useState<LinkedAlert[]>([]);
  const [audit, setAudit] = useState<AuditEntry[]>([]);

  const [selected, setSelected] = useState<Investigation | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);

  const [createForm, setCreateForm] = useState({
    title: "",
    description: "",
    employee_id: "",
    assigned_to: "",
    priority: "medium" as Priority,
  });

  const [editForm, setEditForm] = useState({
    title: "",
    description: "",
    assigned_to: "",
    priority: "medium" as Priority,
    status: "open" as Status,
  });

  const [alertToLink, setAlertToLink] = useState("");

  async function loadPage() {
    setLoading(true);
    setError("");

    try {
      const [investigationResponse, employeeResponse, alertResponse] =
        await Promise.all([
          api.get<Investigation[]>("/investigations", {
            params: { limit: LIMIT, offset: 0 },
          }),
          api.get<Employee[]>("/employees", {
            params: { limit: LIMIT, offset: 0 },
          }),
          api.get<Alert[]>("/alerts", {
            params: { limit: LIMIT, offset: 0 },
          }),
        ]);

      setInvestigations(investigationResponse.data);
      setEmployees(employeeResponse.data);
      setAlerts(alertResponse.data);

      if (selected) {
        const updated = investigationResponse.data.find(
          (item) => item.id === selected.id
        );

        if (updated) {
          setSelected(updated);
          await loadDetails(updated.id);
        } else {
          setSelected(null);
        }
      }
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadDetails(id: string) {
    setDetailLoading(true);

    try {
      const [linkedResponse, auditResponse] = await Promise.all([
        api.get<LinkedAlert[]>(`/investigations/${id}/alerts`),
        api.get<AuditEntry[]>(`/investigations/${id}/audit`, {
          params: { limit: 100, offset: 0 },
        }),
      ]);

      setLinkedAlerts(linkedResponse.data);
      setAudit(auditResponse.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    void loadPage();
  }, []);

  async function selectInvestigation(item: Investigation) {
    setSelected(item);
    setError("");
    setSuccess("");
    setShowEdit(false);
    setLinkedAlerts([]);
    setAudit([]);

    await loadDetails(item.id);
  }

  async function createInvestigation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload = {
        title: createForm.title.trim(),
        description: createForm.description.trim() || null,
        employee_id: createForm.employee_id || null,
        assigned_to: createForm.assigned_to.trim() || null,
        priority: createForm.priority,
      };

      const response = await api.post<Investigation>(
        "/investigations",
        payload
      );

      setInvestigations((previous) => [
        response.data,
        ...previous,
      ]);

      setShowCreate(false);
      setCreateForm({
        title: "",
        description: "",
        employee_id: "",
        assigned_to: "",
        priority: "medium",
      });

      setSuccess("Investigation created successfully.");
      await selectInvestigation(response.data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  function openEditForm() {
    if (!selected || selected.status === "closed") return;

    setEditForm({
      title: selected.title,
      description: selected.description || "",
      assigned_to: selected.assigned_to || "",
      priority: selected.priority,
      status: selected.status,
    });

    setShowEdit(true);
  }

  async function updateInvestigation(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload = {
        title: editForm.title.trim(),
        description: editForm.description.trim() || null,
        assigned_to: editForm.assigned_to.trim() || null,
        priority: editForm.priority,
        status: editForm.status,
      };

      const response = await api.patch<Investigation>(
        `/investigations/${selected.id}`,
        payload
      );

      setSelected(response.data);
      setInvestigations((previous) =>
        previous.map((item) =>
          item.id === response.data.id ? response.data : item
        )
      );

      setShowEdit(false);
      setSuccess("Investigation updated successfully.");
      await loadDetails(response.data.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function linkAlert(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selected || !alertToLink) return;

    setSaving(true);
    setError("");
    setSuccess("");

    try {
      await api.post(`/investigations/${selected.id}/alerts`, {
        alert_id: alertToLink,
      });

      setAlertToLink("");
      setSuccess("Alert linked to investigation.");
      await loadDetails(selected.id);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  const filteredInvestigations = useMemo(() => {
    return investigations.filter((item) => {
      const matchesStatus =
        statusFilter === "all" || item.status === statusFilter;

      const query = search.toLowerCase();

      const matchesSearch =
        item.title.toLowerCase().includes(query) ||
        item.id.toLowerCase().includes(query);

      return matchesStatus && matchesSearch;
    });
  }, [investigations, statusFilter, search]);

  const employeeMap = useMemo(
    () => new Map(employees.map((item) => [item.id, item])),
    [employees]
  );

  const alertMap = useMemo(
    () => new Map(alerts.map((item) => [item.id, item])),
    [alerts]
  );

  const availableAlerts = alerts.filter(
    (alert) =>
      !linkedAlerts.some((linked) => linked.alert_id === alert.id)
  );

  const openCount = investigations.filter(
    (item) => item.status === "open"
  ).length;

  const inProgressCount = investigations.filter(
    (item) => item.status === "in_progress"
  ).length;

  const closedCount = investigations.filter(
    (item) => item.status === "closed"
  ).length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Shield className="text-indigo-400" size={23} />
            <h1 className="text-2xl font-bold text-white">
              Investigations
            </h1>
          </div>
          <p className="mt-2 text-sm text-zinc-500">
            Manage security cases, investigate alerts and review audit activity.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => void loadPage()}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2.5 text-sm text-zinc-300 transition hover:bg-white/5 disabled:opacity-50"
          >
            <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
            Refresh
          </button>

          <button
            onClick={() => {
              setError("");
              setSuccess("");
              setShowCreate(true);
            }}
            className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-indigo-500"
          >
            <Plus size={17} />
            New Investigation
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          {
            label: "Open",
            value: openCount,
            icon: AlertTriangle,
            color: "text-blue-400",
          },
          {
            label: "In Progress",
            value: inProgressCount,
            icon: Activity,
            color: "text-violet-400",
          },
          {
            label: "Closed",
            value: closedCount,
            icon: Clock3,
            color: "text-zinc-400",
          },
        ].map((stat) => (
          <div
            key={stat.label}
            className="rounded-xl border border-white/10 bg-[#111114] p-5"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm text-zinc-500">{stat.label}</p>
              <stat.icon size={19} className={stat.color} />
            </div>
            <p className="mt-3 text-3xl font-bold text-white">
              {stat.value}
            </p>
            <p className="mt-1 text-xs text-zinc-600">
              From the latest {LIMIT} loaded records maximum
            </p>
          </div>
        ))}
      </div>

      {error && (
        <div className="flex items-start justify-between gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
          <span>{error}</span>
          <button onClick={() => setError("")}>
            <X size={16} />
          </button>
        </div>
      )}

      {success && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3 text-sm text-emerald-400">
          <span>{success}</span>
          <button onClick={() => setSuccess("")}>
            <X size={16} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <section className="overflow-hidden rounded-xl border border-white/10 bg-[#111114]">
          <div className="border-b border-white/10 p-4">
            <h2 className="font-semibold text-white">
              Investigation Cases
            </h2>

            <div className="mt-4 flex flex-col gap-3 sm:flex-row">
              <div className="relative flex-1">
                <Search
                  size={16}
                  className="absolute left-3 top-3 text-zinc-500"
                />
                <input
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search investigations..."
                  className={`${inputClass} pl-9`}
                />
              </div>

              <select
                value={statusFilter}
                onChange={(event) => setStatusFilter(event.target.value)}
                className={`${inputClass} sm:w-40`}
              >
                <option value="all">All statuses</option>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="closed">Closed</option>
              </select>
            </div>
          </div>

          <div className="max-h-[650px] overflow-y-auto">
            {loading ? (
              <div className="p-10 text-center text-sm text-zinc-500">
                Loading investigations...
              </div>
            ) : filteredInvestigations.length === 0 ? (
              <div className="p-10 text-center">
                <FilePlus2
                  size={30}
                  className="mx-auto text-zinc-600"
                />
                <p className="mt-3 text-sm font-medium text-zinc-300">
                  No investigations found
                </p>
                <p className="mt-1 text-xs text-zinc-600">
                  Create a new case or change your filters.
                </p>
              </div>
            ) : (
              filteredInvestigations.map((item) => {
                const employee = item.employee_id
                  ? employeeMap.get(item.employee_id)
                  : null;

                const isSelected = selected?.id === item.id;

                return (
                  <button
                    key={item.id}
                    onClick={() => void selectInvestigation(item)}
                    className={`w-full border-b border-white/5 p-4 text-left transition hover:bg-white/[0.035] ${
                      isSelected
                        ? "border-l-2 border-l-indigo-500 bg-indigo-500/[0.07]"
                        : "border-l-2 border-l-transparent"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-zinc-100">
                          {item.title}
                        </p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {employee?.full_name || "No employee linked"}
                        </p>
                      </div>

                      <Badge className={priorityStyles[item.priority]}>
                        {item.priority}
                      </Badge>
                    </div>

                    <div className="mt-3 flex items-center justify-between">
                      <Badge className={statusStyles[item.status]}>
                        {item.status.replace("_", " ")}
                      </Badge>

                      <span className="text-xs text-zinc-600">
                        {formatDate(item.created_at)}
                      </span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </section>

        <section className="min-w-0 rounded-xl border border-white/10 bg-[#111114]">
          {!selected ? (
            <div className="flex min-h-[440px] flex-col items-center justify-center p-8 text-center">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-indigo-500/10 text-indigo-400">
                <Shield size={27} />
              </div>
              <h2 className="mt-4 font-semibold text-white">
                Investigation Details
              </h2>
              <p className="mt-2 max-w-xs text-sm text-zinc-500">
                Select an investigation to view its details, linked alerts and audit history.
              </p>
            </div>
          ) : (
            <div>
              <div className="flex flex-col justify-between gap-3 border-b border-white/10 p-5 sm:flex-row">
                <div className="min-w-0">
                  <p className="text-xs font-medium uppercase tracking-wider text-zinc-600">
                    Investigation
                  </p>
                  <h2 className="mt-2 break-words text-lg font-semibold text-white">
                    {selected.title}
                  </h2>
                  <p className="mt-1 break-all text-xs text-zinc-600">
                    ID: {selected.id}
                  </p>
                </div>

                {selected.status !== "closed" && (
                  <button
                    onClick={openEditForm}
                    className="h-fit rounded-lg border border-white/10 px-3 py-2 text-sm text-zinc-300 hover:bg-white/5"
                  >
                    Edit Case
                  </button>
                )}
              </div>

              <div className="space-y-6 p-5">
                <div className="flex flex-wrap gap-2">
                  <Badge className={priorityStyles[selected.priority]}>
                    {selected.priority} priority
                  </Badge>
                  <Badge className={statusStyles[selected.status]}>
                    {selected.status.replace("_", " ")}
                  </Badge>
                </div>

                <div>
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-600">
                    Description
                  </p>
                  <p className="whitespace-pre-wrap text-sm leading-6 text-zinc-300">
                    {selected.description || "No description provided."}
                  </p>
                </div>

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <p className="text-xs text-zinc-600">Employee</p>
                    <p className="mt-1 text-sm text-zinc-200">
                      {selected.employee_id
                        ? employeeMap.get(selected.employee_id)?.full_name ||
                          "Employee not in loaded records"
                        : "Not assigned"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-zinc-600">Assignee ID</p>
                    <p className="mt-1 break-all text-sm text-zinc-200">
                      {selected.assigned_to || "Unassigned"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-zinc-600">Created</p>
                    <p className="mt-1 text-sm text-zinc-200">
                      {formatDate(selected.created_at)}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-zinc-600">Last Updated</p>
                    <p className="mt-1 text-sm text-zinc-200">
                      {formatDate(selected.updated_at)}
                    </p>
                  </div>
                </div>

                <div className="border-t border-white/10 pt-5">
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="font-semibold text-white">
                      Linked Security Alerts
                    </h3>
                    <Badge className="bg-indigo-500/10 text-indigo-300 border-indigo-500/20">
                      {linkedAlerts.length} linked
                    </Badge>
                  </div>

                  {linkedAlerts.length === 0 ? (
                    <p className="rounded-lg border border-dashed border-white/10 p-4 text-center text-sm text-zinc-600">
                      No alerts linked to this investigation.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {linkedAlerts.map((link) => {
                        const alert = alertMap.get(link.alert_id);

                        return (
                          <div
                            key={link.alert_id}
                            className="rounded-lg border border-white/10 bg-black/20 p-3"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <p className="break-all text-sm font-medium text-zinc-200">
                                {alert?.title || link.alert_id}
                              </p>
                              {alert && (
                                <Badge className={priorityStyles[
                                  (alert.severity.toLowerCase() in priorityStyles
                                    ? alert.severity.toLowerCase()
                                    : "medium") as Priority
                                ]}>
                                  {alert.severity}
                                </Badge>
                              )}
                            </div>
                            <p className="mt-1 text-xs text-zinc-600">
                              {alert
                                ? `Risk score: ${alert.risk_score} Â· Status: ${alert.status}`
                                : "Alert details are not in the latest loaded alert records"}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {selected.status !== "closed" && (
                    <form
                      onSubmit={linkAlert}
                      className="mt-3 flex flex-col gap-2 sm:flex-row"
                    >
                      <select
                        required
                        value={alertToLink}
                        onChange={(event) => setAlertToLink(event.target.value)}
                        className={`${inputClass} flex-1`}
                      >
                        <option value="">Select an alert to link</option>
                        {availableAlerts.map((alert) => (
                          <option key={alert.id} value={alert.id}>
                            {alert.title} ({alert.severity})
                          </option>
                        ))}
                      </select>

                      <button
                        type="submit"
                        disabled={saving || !alertToLink}
                        className="inline-flex items-center justify-center gap-2 rounded-lg border border-indigo-500/30 bg-indigo-500/10 px-3 py-2 text-sm text-indigo-300 hover:bg-indigo-500/20 disabled:opacity-50"
                      >
                        <Link2 size={15} />
                        Link Alert
                      </button>
                    </form>
                  )}

                  {selected.status === "closed" && (
                    <p className="mt-3 text-xs text-zinc-600">
                      Closed investigations cannot accept new alerts.
                    </p>
                  )}
                </div>

                <div className="border-t border-white/10 pt-5">
                  <div className="mb-4 flex items-center gap-2">
                    <Activity size={17} className="text-indigo-400" />
                    <h3 className="font-semibold text-white">
                      Audit History
                    </h3>
                  </div>

                  {detailLoading ? (
                    <p className="text-sm text-zinc-500">
                      Loading audit history...
                    </p>
                  ) : audit.length === 0 ? (
                    <p className="text-sm text-zinc-600">
                      No audit entries found.
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {audit.map((entry) => (
                        <div
                          key={entry.id}
                          className="relative border-l border-white/10 pb-1 pl-4"
                        >
                          <span className="absolute -left-[5px] top-1 h-2 w-2 rounded-full bg-indigo-400" />
                          <p className="text-sm font-medium text-zinc-200">
                            {entry.action.replaceAll("_", " ")}
                          </p>
                          <p className="mt-1 break-all text-xs text-zinc-600">
                            {formatDate(entry.created_at)}
                          </p>
                          <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words rounded-lg bg-black/30 p-3 text-xs text-zinc-400">
                            {JSON.stringify(entry.details, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm">
          <div className="my-auto w-full max-w-xl rounded-2xl border border-white/10 bg-[#151519] shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 p-5">
              <div>
                <h2 className="font-semibold text-white">
                  Create Investigation
                </h2>
                <p className="mt-1 text-xs text-zinc-500">
                  Open a new security investigation case.
                </p>
              </div>
              <button
                onClick={() => setShowCreate(false)}
                className="text-zinc-500 hover:text-white"
              >
                <X size={19} />
              </button>
            </div>

            <form onSubmit={createInvestigation} className="space-y-4 p-5">
              <div>
                <FieldLabel>Investigation Title *</FieldLabel>
                <input
                  required
                  minLength={3}
                  maxLength={255}
                  value={createForm.title}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      title: event.target.value,
                    })
                  }
                  placeholder="e.g. Unusual bulk data downloads"
                  className={inputClass}
                />
              </div>

              <div>
                <FieldLabel>Description</FieldLabel>
                <textarea
                  rows={3}
                  value={createForm.description}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      description: event.target.value,
                    })
                  }
                  placeholder="Describe the security concern..."
                  className={inputClass}
                />
              </div>

              <div>
                <FieldLabel>Employee (Optional)</FieldLabel>
                <select
                  value={createForm.employee_id}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      employee_id: event.target.value,
                    })
                  }
                  className={inputClass}
                >
                  <option value="">No employee linked</option>
                  {employees
                    .filter((employee) => employee.is_active)
                    .map((employee) => (
                      <option key={employee.id} value={employee.id}>
                        {employee.full_name} Â· {employee.employee_code}
                      </option>
                    ))}
                </select>
              </div>

              <div>
                <FieldLabel>Assignee User ID (Optional)</FieldLabel>
                <input
                  value={createForm.assigned_to}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      assigned_to: event.target.value,
                    })
                  }
                  placeholder="Paste an active admin or analyst UUID"
                  className={inputClass}
                />
                <p className="mt-1 text-xs text-zinc-600">
                  Must belong to an active admin or analyst in your organization.
                </p>
              </div>

              <div>
                <FieldLabel>Priority</FieldLabel>
                <select
                  value={createForm.priority}
                  onChange={(event) =>
                    setCreateForm({
                      ...createForm,
                      priority: event.target.value as Priority,
                    })
                  }
                  className={inputClass}
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 border-t border-white/10 pt-4">
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="rounded-lg border border-white/10 px-4 py-2.5 text-sm text-zinc-300 hover:bg-white/5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {saving ? "Creating..." : "Create Investigation"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showEdit && selected && (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm">
          <div className="my-auto w-full max-w-xl rounded-2xl border border-white/10 bg-[#151519] shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 p-5">
              <h2 className="font-semibold text-white">
                Update Investigation
              </h2>
              <button
                onClick={() => setShowEdit(false)}
                className="text-zinc-500 hover:text-white"
              >
                <X size={19} />
              </button>
            </div>

            <form onSubmit={updateInvestigation} className="space-y-4 p-5">
              <div>
                <FieldLabel>Title</FieldLabel>
                <input
                  required
                  minLength={3}
                  maxLength={255}
                  value={editForm.title}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      title: event.target.value,
                    })
                  }
                  className={inputClass}
                />
              </div>

              <div>
                <FieldLabel>Description</FieldLabel>
                <textarea
                  rows={3}
                  value={editForm.description}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      description: event.target.value,
                    })
                  }
                  className={inputClass}
                />
              </div>

              <div>
                <FieldLabel>Assignee User ID (Optional)</FieldLabel>
                <input
                  value={editForm.assigned_to}
                  onChange={(event) =>
                    setEditForm({
                      ...editForm,
                      assigned_to: event.target.value,
                    })
                  }
                  placeholder="Active admin or analyst UUID"
                  className={inputClass}
                />
              </div>

              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div>
                  <FieldLabel>Priority</FieldLabel>
                  <select
                    value={editForm.priority}
                    onChange={(event) =>
                      setEditForm({
                        ...editForm,
                        priority: event.target.value as Priority,
                      })
                    }
                    className={inputClass}
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>

                <div>
                  <FieldLabel>Status</FieldLabel>
                  <select
                    value={editForm.status}
                    onChange={(event) =>
                      setEditForm({
                        ...editForm,
                        status: event.target.value as Status,
                      })
                    }
                    className={inputClass}
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>

              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-amber-300">
                Closing a case prevents further editing and alert linking.
              </div>

              <div className="flex justify-end gap-2 border-t border-white/10 pt-4">
                <button
                  type="button"
                  onClick={() => setShowEdit(false)}
                  className="rounded-lg border border-white/10 px-4 py-2.5 text-sm text-zinc-300 hover:bg-white/5"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className="rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
                >
                  {saving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}