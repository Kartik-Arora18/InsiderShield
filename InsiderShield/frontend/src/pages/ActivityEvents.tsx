
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Activity,
  CalendarClock,
  ChevronLeft,
  ChevronRight,
  Clock3,
  RefreshCw,
  Search,
  Shield,
  UserRound,
  X,
} from "lucide-react";
import api from "../lib/api";

interface ActivityEvent {
  id: string;
  organization_id: string;
  employee_id: string;
  idempotency_key: string;
  event_type: string;
  source: string;
  occurred_at: string;
  event_data: Record<string, unknown>;
  received_at: string;
}

interface Employee {
  id: string;
  full_name: string;
  employee_code: string;
  is_active: boolean;
}

const PAGE_SIZE = 50;

function formatDate(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Unknown date"
    : date.toLocaleString([], {
        dateStyle: "medium",
        timeStyle: "short",
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

  return "Unable to load activity events. Please try again.";
}

function shortId(value: string) {
  return `${value.slice(0, 8)}...${value.slice(-4)}`;
}

function eventStyle(eventType: string) {
  const value = eventType.toLowerCase();

  if (value.includes("download") || value.includes("export")) {
    return "border-amber-500/20 bg-amber-500/10 text-amber-300";
  }

  if (value.includes("login") || value.includes("auth")) {
    return "border-blue-500/20 bg-blue-500/10 text-blue-300";
  }

  if (value.includes("delete") || value.includes("remove")) {
    return "border-red-500/20 bg-red-500/10 text-red-300";
  }

  return "border-indigo-500/20 bg-indigo-500/10 text-indigo-300";
}

export default function ActivityEvents() {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [selected, setSelected] = useState<ActivityEvent | null>(null);

  const [employeeFilter, setEmployeeFilter] = useState("");
  const [search, setSearch] = useState("");
  const [offset, setOffset] = useState(0);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadEvents = useCallback(async () => {
    setLoading(true);
    setError("");

    try {
      const [eventResponse, employeeResponse] = await Promise.all([
        api.get<ActivityEvent[]>("/events", {
          params: {
            limit: PAGE_SIZE,
            offset,
            ...(employeeFilter ? { employee_id: employeeFilter } : {}),
          },
        }),
        api.get<Employee[]>("/employees", {
          params: { limit: 200, offset: 0 },
        }),
      ]);

      setEvents(eventResponse.data);
      setEmployees(employeeResponse.data);

      setSelected((current) =>
        current
          ? eventResponse.data.find((event) => event.id === current.id) ?? null
          : null
      );
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [offset, employeeFilter]);

  useEffect(() => {
    void loadEvents();
  }, [loadEvents]);

  const employeeMap = useMemo(
    () => new Map(employees.map((employee) => [employee.id, employee])),
    [employees]
  );

  const filteredEvents = useMemo(() => {
    const query = search.trim().toLowerCase();

    if (!query) return events;

    return events.filter((event) => {
      const employee = employeeMap.get(event.employee_id);

      return (
        event.event_type.toLowerCase().includes(query) ||
        event.source.toLowerCase().includes(query) ||
        event.employee_id.toLowerCase().includes(query) ||
        (employee?.full_name.toLowerCase().includes(query) ?? false) ||
        (employee?.employee_code.toLowerCase().includes(query) ?? false) ||
        event.id.toLowerCase().includes(query)
      );
    });
  }, [events, employeeMap, search]);

  const uniqueTypes = new Set(events.map((event) => event.event_type)).size;
  const uniqueEmployees = new Set(events.map((event) => event.employee_id)).size;

  function changeEmployee(value: string) {
    setEmployeeFilter(value);
    setOffset(0);
    setSelected(null);
  }

  function changePage(direction: "previous" | "next") {
    setSelected(null);
    setOffset((current) =>
      direction === "previous"
        ? Math.max(0, current - PAGE_SIZE)
        : current + PAGE_SIZE
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="text-indigo-400" size={23} />
            <h1 className="text-2xl font-bold text-white">Activity Events</h1>
          </div>
          <p className="mt-2 text-sm text-zinc-500">
            Explore employee activity records received by InsiderShield.
          </p>
        </div>

        <button
          onClick={() => void loadEvents()}
          disabled={loading}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-white/10 px-3 py-2.5 text-sm text-zinc-300 transition hover:bg-white/5 disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
          <span>{error}</span>
          <button onClick={() => setError("")} aria-label="Dismiss error">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          {
            label: "Events Loaded",
            value: events.length,
            icon: Activity,
            color: "text-indigo-400",
          },
          {
            label: "Event Types",
            value: uniqueTypes,
            icon: CalendarClock,
            color: "text-blue-400",
          },
          {
            label: "Employees Active in Events",
            value: uniqueEmployees,
            icon: UserRound,
            color: "text-emerald-400",
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
              {loading ? "—" : stat.value.toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-zinc-600">
              Current page of event records
            </p>
          </div>
        ))}
      </div>

      <section className="overflow-hidden rounded-xl border border-white/10 bg-[#111114]">
        <div className="border-b border-white/10 p-4">
          <div className="flex flex-col gap-3 lg:flex-row">
            <div className="relative flex-1">
              <Search
                size={16}
                className="absolute left-3 top-3 text-zinc-500"
              />
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Search event type, source, employee or ID..."
                className="w-full rounded-lg border border-white/10 bg-[#09090b] py-2.5 pl-9 pr-3 text-sm text-zinc-100 outline-none placeholder:text-zinc-600 focus:border-indigo-500"
              />
            </div>

            <select
              value={employeeFilter}
              onChange={(event) => changeEmployee(event.target.value)}
              className="w-full rounded-lg border border-white/10 bg-[#09090b] px-3 py-2.5 text-sm text-zinc-300 outline-none focus:border-indigo-500 lg:w-64"
            >
              <option value="">All employees</option>
              {employees.map((employee) => (
                <option key={employee.id} value={employee.id}>
                  {employee.full_name} ({employee.employee_code})
                </option>
              ))}
            </select>
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-zinc-500">
              Showing {filteredEvents.length} matching events on this page
            </p>
            <p className="text-xs text-zinc-600">
              Latest events first · Maximum {PAGE_SIZE} per page
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="bg-white/[0.02] text-xs text-zinc-500">
              <tr>
                <th className="px-5 py-4">Event Type</th>
                <th className="px-5 py-4">Employee</th>
                <th className="px-5 py-4">Source</th>
                <th className="px-5 py-4">Occurred At</th>
                <th className="px-5 py-4">Received At</th>
                <th className="px-5 py-4">Details</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-12 text-center text-zinc-500"
                  >
                    Loading activity events...
                  </td>
                </tr>
              ) : filteredEvents.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-14 text-center">
                    <Activity size={28} className="mx-auto text-zinc-600" />
                    <p className="mt-3 font-medium text-zinc-300">
                      No activity events found
                    </p>
                    <p className="mt-1 text-xs text-zinc-600">
                      Try changing your search or employee filter.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredEvents.map((event) => {
                  const employee = employeeMap.get(event.employee_id);

                  return (
                    <tr
                      key={event.id}
                      className={`transition hover:bg-white/[0.025] ${
                        selected?.id === event.id ? "bg-indigo-500/[0.06]" : ""
                      }`}
                    >
                      <td className="px-5 py-4">
                        <span
                          className={`inline-flex rounded-full border px-2.5 py-1 text-xs font-medium ${eventStyle(
                            event.event_type
                          )}`}
                        >
                          {event.event_type}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <p className="font-medium text-zinc-200">
                          {employee?.full_name || "Unknown employee"}
                        </p>
                        <p className="mt-1 text-xs text-zinc-600">
                          {employee?.employee_code || shortId(event.employee_id)}
                        </p>
                      </td>

                      <td className="px-5 py-4 text-zinc-400">{event.source}</td>

                      <td className="px-5 py-4 text-xs text-zinc-400">
                        {formatDate(event.occurred_at)}
                      </td>

                      <td className="px-5 py-4 text-xs text-zinc-500">
                        {formatDate(event.received_at)}
                      </td>

                      <td className="px-5 py-4">
                        <button
                          onClick={() =>
                            setSelected((current) =>
                              current?.id === event.id ? null : event
                            )
                          }
                          className="rounded-lg border border-white/10 px-3 py-1.5 text-xs text-indigo-300 transition hover:bg-indigo-500/10"
                        >
                          {selected?.id === event.id ? "Selected" : "Inspect"}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-white/10 p-4">
          <span className="text-xs text-zinc-500">
            Records {offset + 1}–{offset + events.length}
          </span>

          <div className="flex gap-2">
            <button
              onClick={() => changePage("previous")}
              disabled={offset === 0 || loading}
              className="inline-flex items-center gap-1 rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-300 hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-30"
            >
              <ChevronLeft size={15} />
              Previous
            </button>

            <button
              onClick={() => changePage("next")}
              disabled={loading || events.length < PAGE_SIZE}
              className="inline-flex items-center gap-1 rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-300 hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-30"
            >
              Next
              <ChevronRight size={15} />
            </button>
          </div>
        </div>
      </section>

      {selected && (
        <section className="overflow-hidden rounded-xl border border-indigo-500/20 bg-[#111114]">
          <div className="flex flex-col justify-between gap-3 border-b border-white/10 p-5 sm:flex-row sm:items-center">
            <div>
              <div className="flex items-center gap-2">
                <Shield size={17} className="text-indigo-400" />
                <h2 className="font-semibold text-white">Event Details</h2>
              </div>
              <p className="mt-1 break-all text-xs text-zinc-600">
                Event ID: {selected.id}
              </p>
            </div>

            <button
              onClick={() => setSelected(null)}
              className="flex items-center gap-2 self-start rounded-lg border border-white/10 px-3 py-2 text-xs text-zinc-400 hover:text-white sm:self-auto"
            >
              <X size={14} />
              Close Details
            </button>
          </div>

          <div className="grid gap-5 p-5 lg:grid-cols-2">
            <div className="space-y-4">
              <div>
                <p className="text-xs text-zinc-600">Event Type</p>
                <p className="mt-1 text-sm font-medium text-zinc-200">
                  {selected.event_type}
                </p>
              </div>

              <div>
                <p className="text-xs text-zinc-600">Employee</p>
                <p className="mt-1 text-sm text-zinc-200">
                  {employeeMap.get(selected.employee_id)?.full_name ||
                    "Unknown employee"}
                </p>
                <p className="mt-1 break-all text-xs text-zinc-600">
                  {selected.employee_id}
                </p>
              </div>

              <div>
                <p className="text-xs text-zinc-600">Source</p>
                <p className="mt-1 text-sm text-zinc-200">{selected.source}</p>
              </div>

              <div>
                <p className="text-xs text-zinc-600">Idempotency Key</p>
                <p className="mt-1 break-all text-xs text-zinc-400">
                  {selected.idempotency_key}
                </p>
              </div>

              <div>
                <p className="text-xs text-zinc-600">Timestamps</p>
                <p className="mt-2 flex items-center gap-2 text-sm text-zinc-300">
                  <Clock3 size={14} className="text-indigo-400" />
                  Occurred: {formatDate(selected.occurred_at)}
                </p>
                <p className="mt-2 flex items-center gap-2 text-sm text-zinc-300">
                  <CalendarClock size={14} className="text-indigo-400" />
                  Received: {formatDate(selected.received_at)}
                </p>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Event Data (JSON)
              </p>
              <pre className="max-h-[400px] overflow-auto rounded-lg border border-white/10 bg-black/30 p-4 text-xs leading-6 text-emerald-300">
                {JSON.stringify(selected.event_data, null, 2)}
              </pre>
            </div>
          </div>
        </section>
      )}

      <div className="flex items-start gap-3 rounded-xl border border-white/10 bg-[#111114] p-4">
        <Activity size={18} className="mt-0.5 shrink-0 text-indigo-400" />
        <p className="text-xs leading-5 text-zinc-500">
          Activity events are read-only in this interface. Records are
          retrieved from your organization-scoped backend API and displayed
          newest first. Search operates on the currently loaded page.
        </p>
      </div>
    </div>
  );
}
