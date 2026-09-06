"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { analytics, api, DashboardStats } from "@/lib/api";

const statCards = (s: DashboardStats) => [
  { label: "Documents indexed", value: s.total_documents, accent: "border-violet" },
  { label: "Active workflows", value: `${s.active_workflows}/${s.total_workflows}`, accent: "border-cyan" },
  { label: "Successful runs", value: s.successful_runs, accent: "border-mint" },
  { label: "Failed runs", value: s.failed_runs, accent: "border-coral" },
];

type HealthDetail = {
  status: string;
  database: string;
  cache: string;
  scheduler: string;
  ai_providers: { claude: string; gemini: string };
  google_sign_in: string;
};

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [health, setHealth] = useState<HealthDetail | null>(null);

  useEffect(() => {
    analytics.dashboard().then((res) => setStats(res.data)).catch(() => setStats(null));
    api.get<HealthDetail>("/health/detailed").then((res) => setHealth(res.data)).catch(() => setHealth(null));
  }, []);

  return (
    <div>
      <h1 className="font-display text-3xl text-ink mb-1">Overview</h1>
      <p className="text-slatetext mb-8">Everything happening across your documents and automations.</p>

      {stats && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {statCards(stats).map((c) => (
              <div key={c.label} className={`card p-5 border-l-4 ${c.accent}`}>
                <p className="text-sm text-slatetext mb-1">{c.label}</p>
                <p className="font-display text-3xl text-ink">{c.value}</p>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-[2fr_1fr] gap-4">
            <div className="card p-6">
              <h2 className="font-medium text-ink mb-4">Workflow runs - last 7 days</h2>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={stats.runs_last_7_days}>
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" fill="#6C4CF1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card p-6">
              <h2 className="font-medium text-ink mb-4">System status</h2>
              {health ? (
                <div className="space-y-3 text-sm">
                  {[
                    { label: "Database", value: health.database, good: health.database === "connected" },
                    { label: "Cache", value: health.cache, good: true },
                    { label: "Scheduler", value: health.scheduler, good: health.scheduler === "running" },
                    { label: "Claude", value: health.ai_providers.claude, good: health.ai_providers.claude === "configured" },
                    { label: "Gemini", value: health.ai_providers.gemini, good: health.ai_providers.gemini === "configured" },
                    { label: "Google Sign-In", value: health.google_sign_in, good: health.google_sign_in === "configured" },
                  ].map((row) => (
                    <div key={row.label} className="flex items-center justify-between">
                      <span className="text-slatetext">{row.label}</span>
                      <span className={`flex items-center gap-2 ${row.good ? "text-mint" : "text-slatetext"}`}>
                        <span className={`h-1.5 w-1.5 rounded-full ${row.good ? "bg-mint" : "bg-mist"}`} />
                        {row.value}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slatetext">Checking system status...</p>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
