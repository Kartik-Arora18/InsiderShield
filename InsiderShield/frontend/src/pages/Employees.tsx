
import { useEffect, useMemo, useState } from "react";
import {
  Users,
  Search,
  RefreshCw,
  ShieldAlert,
  UserCheck,
  UserX,
} from "lucide-react";
import api from "../lib/api";

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
  last_calculated_at: string;
}

export default function Employees() {
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [risks, setRisks] = useState<RiskScore[]>([]);
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("all");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadEmployees() {
    setLoading(true);
    setError("");

    try {
      const [employeeResponse, riskResponse] = await Promise.all([
        api.get<Employee[]>("/employees", {
          params: { limit: 200, offset: 0 },
        }),
        api.get<RiskScore[]>("/risk-scores", {
          params: { limit: 200, offset: 0 },
        }),
      ]);

      setEmployees(employeeResponse.data);
      setRisks(riskResponse.data);
    } catch (err) {
      console.error("Employee loading failed:", err);
      setError("Unable to load employee data. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadEmployees();
  }, []);

  const riskMap = useMemo(
    () => new Map(risks.map((risk) => [risk.employee_id, risk])),
    [risks]
  );

  const departments = useMemo(
    () =>
      Array.from(
        new Set(
          employees
            .map((employee) => employee.department)
            .filter((value): value is string => Boolean(value))
        )
      ).sort(),
    [employees]
  );

  const filteredEmployees = employees.filter((employee) => {
    const query = search.trim().toLowerCase();

    const matchesSearch =
      !query ||
      [
        employee.full_name,
        employee.employee_code,
        employee.email,
        employee.department || "",
        employee.job_title || "",
      ].some((value) => value.toLowerCase().includes(query));

    const matchesDepartment =
      department === "all" || employee.department === department;

    const matchesStatus =
      status === "all" ||
      (status === "active" && employee.is_active) ||
      (status === "inactive" && !employee.is_active);

    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const activeCount = employees.filter((e) => e.is_active).length;
  const inactiveCount = employees.length - activeCount;

  const highRiskCount = employees.filter((employee) => {
    const risk = riskMap.get(employee.id);
    return (
      risk &&
      ["high", "critical"].includes(risk.risk_level.toLowerCase())
    );
  }).length;

  function riskStyle(level?: string) {
    switch (level?.toLowerCase()) {
      case "critical":
        return "bg-red-500/10 text-red-400";
      case "high":
        return "bg-orange-500/10 text-orange-400";
      case "medium":
        return "bg-amber-500/10 text-amber-400";
      case "low":
        return "bg-emerald-500/10 text-emerald-400";
      default:
        return "bg-zinc-500/10 text-zinc-400";
    }
  }

  return (
    <div className="space-y-7">
      <section className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <Users size={25} className="text-indigo-400" />
            <h2 className="text-2xl font-semibold">Employees</h2>
          </div>
          <p className="mt-2 text-sm text-zinc-500">
            Monitor employee profiles and individual insider threat risk.
          </p>
        </div>

        <button
          onClick={loadEmployees}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-lg border border-white/10 px-4 py-2.5 text-sm text-zinc-300 hover:bg-white/5 disabled:opacity-50"
        >
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </section>

      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-300">
          {error}
        </div>
      )}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Employees Loaded",
            value: employees.length,
            icon: Users,
            color: "text-indigo-400",
          },
          {
            label: "Active Employees",
            value: activeCount,
            icon: UserCheck,
            color: "text-emerald-400",
          },
          {
            label: "Inactive Employees",
            value: inactiveCount,
            icon: UserX,
            color: "text-zinc-400",
          },
          {
            label: "High / Critical Risk",
            value: highRiskCount,
            icon: ShieldAlert,
            color: "text-red-400",
          },
        ].map((item) => (
          <div
            key={item.label}
            className="rounded-xl border border-white/10 bg-[#111114] p-5"
          >
            <div className="flex items-center justify-between">
              <p className="text-sm text-zinc-500">{item.label}</p>
              <item.icon size={20} className={item.color} />
            </div>
            <p className={`mt-5 text-3xl font-semibold ${item.color}`}>
              {loading ? "—" : item.value}
            </p>
            <p className="mt-2 text-xs text-zinc-600">
              Latest 200 records maximum
            </p>
          </div>
        ))}
      </section>

      <section className="rounded-xl border border-white/10 bg-[#111114] p-5">
        <div className="grid gap-4 md:grid-cols-[1fr_200px_180px]">
          <div className="relative">
            <Search
              size={17}
              className="absolute left-3 top-3.5 text-zinc-500"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search name, employee ID, email..."
              className="w-full rounded-lg border border-white/10 bg-black/30 py-3 pl-10 pr-4 text-sm outline-none focus:border-indigo-500"
            />
          </div>

          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="rounded-lg border border-white/10 bg-[#09090b] px-4 py-3 text-sm text-zinc-300 outline-none focus:border-indigo-500"
          >
            <option value="all">All departments</option>
            {departments.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>

          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="rounded-lg border border-white/10 bg-[#09090b] px-4 py-3 text-sm text-zinc-300 outline-none focus:border-indigo-500"
          >
            <option value="all">All employees</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-white/10 bg-[#111114]">
        <div className="border-b border-white/10 p-5">
          <h3 className="font-semibold">Employee Directory</h3>
          <p className="mt-1 text-xs text-zinc-500">
            Employee profiles and associated risk intelligence.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="bg-white/[0.02] text-xs text-zinc-500">
              <tr>
                <th className="px-5 py-4">Employee</th>
                <th className="px-5 py-4">Employee ID</th>
                <th className="px-5 py-4">Department</th>
                <th className="px-5 py-4">Risk Score</th>
                <th className="px-5 py-4">Risk Level</th>
                <th className="px-5 py-4">Status</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-white/5">
              {loading && (
                <tr>
                  <td colSpan={6} className="px-5 py-12 text-center text-zinc-500">
                    Loading employee records...
                  </td>
                </tr>
              )}

              {!loading &&
                filteredEmployees.map((employee) => {
                  const risk = riskMap.get(employee.id);

                  return (
                    <tr key={employee.id} className="hover:bg-white/[0.03]">
                      <td className="px-5 py-4">
                        <p className="font-medium">{employee.full_name}</p>
                        <p className="mt-1 text-xs text-zinc-500">
                          {employee.email}
                        </p>
                      </td>

                      <td className="px-5 py-4 text-zinc-400">
                        {employee.employee_code}
                      </td>

                      <td className="px-5 py-4 text-zinc-400">
                        {employee.department || "—"}
                      </td>

                      <td className="px-5 py-4 font-semibold">
                        {risk
                          ? Number(risk.risk_score).toFixed(1)
                          : "—"}
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`rounded-md px-2.5 py-1 text-xs capitalize ${riskStyle(risk?.risk_level)}`}
                        >
                          {risk?.risk_level || "Not assessed"}
                        </span>
                      </td>

                      <td className="px-5 py-4">
                        <span
                          className={`rounded-md px-2.5 py-1 text-xs ${
                            employee.is_active
                              ? "bg-emerald-500/10 text-emerald-400"
                              : "bg-zinc-500/10 text-zinc-400"
                          }`}
                        >
                          {employee.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                    </tr>
                  );
                })}

              {!loading && filteredEmployees.length === 0 && (
                <tr>
                  <td
                    colSpan={6}
                    className="px-5 py-12 text-center text-zinc-500"
                  >
                    No employees match your search or filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="border-t border-white/10 px-5 py-4 text-xs text-zinc-500">
          Showing {loading ? "—" : filteredEmployees.length} of{" "}
          {loading ? "—" : employees.length} loaded employees.
        </div>
      </section>
    </div>
  );
}
