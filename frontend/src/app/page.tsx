"use client";

import { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  service: string;
  timestamp: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Deployed Render backend URL default fallback
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://duplicate-safe-incremental-merge.onrender.com";

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiUrl}/health`);
      if (!res.ok) {
        throw new Error(`Backend returned status ${res.status}`);
      }
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to reach backend service");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900 mb-2">
          System Overview & Diagnostics
        </h2>
        <p className="text-sm text-slate-600 mb-4">
          Welcome to the Duplicate-Safe Incremental Merge Diagnostics and Repair Platform.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <div className="border border-slate-200 rounded-md p-4 bg-slate-50">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
              Frontend Service (Vercel)
            </h3>
            <div className="flex items-center space-x-2">
              <span className="h-3 w-3 rounded-full bg-emerald-500 inline-block"></span>
              <span className="text-sm font-medium text-slate-800">Operational</span>
            </div>
            <p className="text-xs text-slate-500 mt-1 font-mono">Next.js App Router + Tailwind CSS</p>
          </div>

          <div className="border border-slate-200 rounded-md p-4 bg-slate-50">
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Backend Service (Render)
              </h3>
              <button
                onClick={checkHealth}
                className="text-xs text-blue-600 hover:text-blue-800 underline font-medium"
              >
                Re-check
              </button>
            </div>

            {loading ? (
              <div className="flex items-center space-x-2">
                <span className="h-3 w-3 rounded-full bg-amber-400 animate-pulse inline-block"></span>
                <span className="text-sm font-medium text-slate-600">Connecting to Render backend...</span>
              </div>
            ) : error ? (
              <div>
                <div className="flex items-center space-x-2">
                  <span className="h-3 w-3 rounded-full bg-rose-500 inline-block"></span>
                  <span className="text-sm font-medium text-rose-700">Disconnected</span>
                </div>
                <p className="text-xs text-rose-600 mt-1">{error}</p>
                <p className="text-xs text-slate-500 mt-1 font-mono">Target: {apiUrl}/health</p>
              </div>
            ) : (
              <div>
                <div className="flex items-center space-x-2">
                  <span className="h-3 w-3 rounded-full bg-emerald-500 inline-block"></span>
                  <span className="text-sm font-medium text-emerald-800">Connected ({health?.status})</span>
                </div>
                <p className="text-xs text-slate-500 mt-1 font-mono">
                  Timestamp: {health?.timestamp}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg border border-slate-200 p-6 shadow-sm">
        <h3 className="text-sm font-semibold text-slate-900 mb-3">
          Architecture & Capstone Component Roadmap
        </h3>
        <ul className="space-y-2 text-xs text-slate-600">
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">1. Incoming Data Batch:</span>
            <span>FastAPI seed endpoints & SQLite batch tracking</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">2. Key Registry:</span>
            <span>Configurable composite keys & timestamp criteria</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">3. Duplicate Detection Engine:</span>
            <span>Batch vs Main table exact & conflict identification</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">4. Lineage Attribution:</span>
            <span>Transformation step & source tracking for duplicates</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">5. Repair Policy Engine:</span>
            <span>Deterministic ranking rules (Rank → Event-Time → Source Priority → Quarantine)</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">6 & 7. Merge & Review Pipeline:</span>
            <span>Auto-commit resolved rows & queue ambiguous rows for approval</span>
          </li>
          <li className="flex items-center space-x-2">
            <span className="font-semibold text-slate-800">8 & 9. Diagnostics Dashboard & Audit Log:</span>
            <span>Root-cause breakdown, audit trails, and KPI performance cards</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
