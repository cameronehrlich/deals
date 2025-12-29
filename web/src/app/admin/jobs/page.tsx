"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  RefreshCw,
  Loader2,
  CheckCircle2,
  XCircle,
  Clock,
  PlayCircle,
  Trash2,
  ArrowLeft,
  BarChart3,
  StopCircle,
} from "lucide-react";
import { api, Job, JobStats } from "@/lib/api";
import { cn } from "@/lib/utils";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "-";
  // API returns UTC timestamps without 'Z' suffix, so append it
  const utcDateStr = dateStr.endsWith("Z") ? dateStr : dateStr + "Z";
  const date = new Date(utcDateStr);
  return date.toLocaleString();
}

function formatDuration(startStr: string | null | undefined, endStr: string | null | undefined): string {
  if (!startStr) return "-";
  // API returns UTC timestamps without 'Z' suffix
  const startUtc = startStr.endsWith("Z") ? startStr : startStr + "Z";
  const start = new Date(startUtc);
  const end = endStr
    ? new Date(endStr.endsWith("Z") ? endStr : endStr + "Z")
    : new Date();
  const seconds = Math.round((end.getTime() - start.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

function StatusBadge({ status }: { status: string }) {
  const config = {
    pending: { icon: Clock, color: "bg-gray-100 text-gray-700", label: "Pending" },
    running: { icon: PlayCircle, color: "bg-blue-100 text-blue-700", label: "Running" },
    completed: { icon: CheckCircle2, color: "bg-green-100 text-green-700", label: "Completed" },
    failed: { icon: XCircle, color: "bg-red-100 text-red-700", label: "Failed" },
    cancelled: { icon: StopCircle, color: "bg-yellow-100 text-yellow-700", label: "Cancelled" },
  }[status] || { icon: Clock, color: "bg-gray-100 text-gray-700", label: status };

  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium", config.color)}>
      <Icon className="h-3 w-3" />
      {config.label}
    </span>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color
}: {
  label: string;
  value: number;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="card">
      <div className="flex items-center gap-3">
        <div className={cn("p-2 rounded-lg", color)}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{label}</p>
        </div>
      </div>
    </div>
  );
}

export default function AdminJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [stats, setStats] = useState<JobStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [jobList, jobStats] = await Promise.all([
        api.getJobs({ limit: 100 }),
        api.getJobStats(),
      ]);
      setJobs(jobList);
      setStats(jobStats);
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Auto-refresh when jobs are running
  useEffect(() => {
    if (autoRefresh && stats && (stats.pending > 0 || stats.running > 0)) {
      const interval = setInterval(fetchData, 3000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, stats, fetchData]);

  const handleCancelJob = async (jobId: string) => {
    try {
      setCancelling(jobId);
      await api.cancelJob(jobId);
      fetchData();
    } catch (err) {
      console.error("Failed to cancel job:", err);
    } finally {
      setCancelling(null);
    }
  };

  const handleCancelAll = async () => {
    if (!confirm("Cancel all pending jobs?")) return;
    try {
      setCancelling("all");
      await api.cancelJobsByType("enrich_market");
      fetchData();
    } catch (err) {
      console.error("Failed to cancel jobs:", err);
    } finally {
      setCancelling(null);
    }
  };

  const handleCleanup = async () => {
    if (!confirm("Delete completed/failed jobs older than 1 day?")) return;
    try {
      const response = await fetch("/api/jobs/cleanup?days=1", { method: "DELETE" });
      const data = await response.json();
      alert(`Deleted ${data.deleted} old jobs`);
      fetchData();
    } catch (err) {
      console.error("Failed to cleanup:", err);
    }
  };

  const filteredJobs = jobs.filter(job => {
    if (filter === "all") return true;
    return job.status === filter;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/markets" className="p-2 hover:bg-gray-100 rounded-lg">
            <ArrowLeft className="h-5 w-5 text-gray-500" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Job Queue</h1>
            <p className="text-sm text-gray-500">Monitor and manage background tasks</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 text-sm text-gray-600">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh
          </label>
          <button
            onClick={fetchData}
            className="btn-outline flex items-center gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <StatCard
            label="Pending"
            value={stats.pending}
            icon={Clock}
            color="bg-gray-100 text-gray-600"
          />
          <StatCard
            label="Running"
            value={stats.running}
            icon={PlayCircle}
            color="bg-blue-100 text-blue-600"
          />
          <StatCard
            label="Completed"
            value={stats.completed}
            icon={CheckCircle2}
            color="bg-green-100 text-green-600"
          />
          <StatCard
            label="Failed"
            value={stats.failed}
            icon={XCircle}
            color="bg-red-100 text-red-600"
          />
          <StatCard
            label="Total"
            value={stats.total}
            icon={BarChart3}
            color="bg-primary-100 text-primary-600"
          />
        </div>
      )}

      {/* Progress Bar (when jobs running) */}
      {stats && (stats.pending > 0 || stats.running > 0) && (
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span className="font-medium text-blue-900">Processing jobs...</span>
            </div>
            <span className="text-sm text-blue-700">
              {stats.completed} / {stats.total - stats.failed} completed
            </span>
          </div>
          <div className="h-2 bg-blue-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-300"
              style={{
                width: `${Math.round((stats.completed / (stats.total - stats.failed)) * 100)}%`
              }}
            />
          </div>
        </div>
      )}

      {/* Actions Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-500">Filter:</span>
          {["all", "pending", "running", "completed", "failed", "cancelled"].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={cn(
                "px-3 py-1 rounded-full text-sm font-medium transition-colors",
                filter === status
                  ? "bg-primary-100 text-primary-700"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {stats && stats.pending > 0 && (
            <button
              onClick={handleCancelAll}
              disabled={cancelling === "all"}
              className="btn-outline text-red-600 border-red-200 hover:bg-red-50 flex items-center gap-2"
            >
              {cancelling === "all" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <StopCircle className="h-4 w-4" />
              )}
              Cancel All Pending
            </button>
          )}
          <button
            onClick={handleCleanup}
            className="btn-outline flex items-center gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Cleanup Old Jobs
          </button>
        </div>
      </div>

      {/* Jobs Table */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Message</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Progress</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Duration</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredJobs.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <StatusBadge status={job.status} />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900">
                    {job.job_type.replace("_", " ")}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {String(job.payload.market_id || job.payload.property_id || "-")}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 max-w-xs truncate">
                    {job.error || job.message || "-"}
                  </td>
                  <td className="px-4 py-3">
                    {job.status === "running" && (
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-600"
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{job.progress}%</span>
                      </div>
                    )}
                    {job.status === "completed" && (
                      <span className="text-xs text-green-600">100%</span>
                    )}
                    {job.status !== "running" && job.status !== "completed" && (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatDuration(job.started_at, job.completed_at)}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {formatDate(job.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    {job.status === "pending" && (
                      <button
                        onClick={() => handleCancelJob(job.id)}
                        disabled={cancelling === job.id}
                        className="text-red-600 hover:text-red-800 p-1"
                        title="Cancel job"
                      >
                        {cancelling === job.id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <XCircle className="h-4 w-4" />
                        )}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filteredJobs.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-8 text-center text-gray-500">
                    No jobs found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Job ID footer */}
      <p className="text-xs text-gray-400 text-center">
        Showing {filteredJobs.length} of {jobs.length} jobs
      </p>
    </div>
  );
}
