"use client";

import { useEffect, useState } from "react";

interface KPI {
  total_rows_processed: number;
  duplicates_detected: number;
  auto_repaired: number;
  quarantined_pending_review: number;
  false_block_rate: string;
}

interface Batch {
  id: string;
  source: string;
  status: string;
  total_rows: number;
  created_at: string;
}

interface Duplicate {
  id: number;
  type: string;
  confidence: number;
  batch_id: string;
  incoming_row_id: number;
  decision: string | null;
  decision_status: string | null;
  decision_id: number | null;
}

interface RootCause {
  flag_id: number;
  duplicate_type: string;
  lineage: { step: string; source: string };
  incoming_payload: any;
  existing_payload: any;
  decision: { action: string; reason: string; status: string };
}

export default function Home() {
  const [kpis, setKpis] = useState<KPI | null>(null);
  const [batches, setBatches] = useState<Batch[]>([]);
  const [duplicates, setDuplicates] = useState<Duplicate[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  
  const [selectedDuplicate, setSelectedDuplicate] = useState<number | null>(null);
  const [rootCause, setRootCause] = useState<RootCause | null>(null);
  const [rcLoading, setRcLoading] = useState(false);
  const [showIngest, setShowIngest] = useState(false);
  const [ingestMode, setIngestMode] = useState<"json" | "file">("json");
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [showIngest, setShowIngest] = useState(false);
  const [customPayload, setCustomPayload] = useState(
    JSON.stringify([
      {
        "customer_id": "CUST-999",
        "order_date": "2026-09-22",
        "customer_name": "Presentation Test User",
        "amount": 100.00,
        "event_timestamp": "2026-09-22T12:00:00Z",
        "source_system": "WEB_STORE",
        "source_rank": 2
      }
    ], null, 2)
  );

  const handleCustomIngest = async () => {
    try {
      const rows = JSON.parse(customPayload);
      const res = await fetch(`${apiUrl}/api/batches/ingest`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          batch_id: `manual-batch-${Date.now()}`,
          source_system: "MANUAL_UI",
          entity_name: "customer_orders",
          rows: Array.isArray(rows) ? rows : [rows]
        })
      });
      if (res.ok) {
        setShowIngest(false);
        fetchData();
      } else {
        alert("Backend rejected the payload. Check console.");
      }
    } catch (err) {
      alert("Invalid JSON format");
    }
  };


  // For local development, assume backend runs on 8000
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchData = async () => {
    setLoading(true);
    try {
      const [kpiRes, batchesRes, dupsRes] = await Promise.all([
        fetch(`${apiUrl}/api/kpis`),
        fetch(`${apiUrl}/api/batches`),
        fetch(`${apiUrl}/api/duplicates`)
      ]);
      if (kpiRes.ok) setKpis(await kpiRes.json());
      if (batchesRes.ok) setBatches(await batchesRes.json());
      if (dupsRes.ok) setDuplicates(await dupsRes.json());
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSeed = async () => {
    try {
      await fetch(`${apiUrl}/api/seed`, { method: 'POST' });
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const viewRootCause = async (id: number) => {
    setSelectedDuplicate(id);
    setRcLoading(true);
    setRootCause(null);
    try {
      const res = await fetch(`${apiUrl}/api/duplicates/${id}/root-cause`);
      if (res.ok) {
        setRootCause(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setRcLoading(false);
    }
  };

  const resolveQuarantine = async (decisionId: number, action: string) => {
    try {
      const res = await fetch(`${apiUrl}/api/quarantine/${decisionId}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      if (res.ok) {
        setSelectedDuplicate(null);
        setRootCause(null);
        fetchData();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const quarantined = duplicates.filter(d => d.decision_status === "PENDING_REVIEW");

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8 font-sans">
      <div className="flex justify-between items-center border-b pb-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Merge Diagnostics & Repair</h1>
          <p className="text-sm text-slate-500">Duplicate-Safe Incremental Merge Platform </p>
        </div>
        <div className="space-x-3">
          <button 
            onClick={() => setShowIngest(!showIngest)}
            className="bg-slate-100 border border-slate-300 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded text-sm font-medium transition"
          >
            + Custom Ingestion
          </button>
          <button 
            onClick={handleSeed}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition"
          >
            Seed Demo Data
          </button>
        </div>
      </div>

      
      {showIngest && (
        <div className="bg-slate-50 border border-slate-200 rounded p-4 shadow-inner space-y-4">
          <div className="flex justify-between items-center border-b pb-2">
            <h3 className="font-semibold text-slate-800 text-sm">Advanced Ingestion Modules</h3>
            <div className="space-x-2">
              <button 
                onClick={() => setIngestMode("json")}
                className={`text-xs px-3 py-1 rounded transition ${ingestMode === "json" ? "bg-slate-800 text-white" : "bg-slate-200 text-slate-600 hover:bg-slate-300"}`}
              >JSON Editor</button>
              <button 
                onClick={() => setIngestMode("file")}
                className={`text-xs px-3 py-1 rounded transition ${ingestMode === "file" ? "bg-slate-800 text-white" : "bg-slate-200 text-slate-600 hover:bg-slate-300"}`}
              >Excel / CSV Upload</button>
            </div>
          </div>
          
          {ingestMode === "json" && (
            <div>
              <p className="text-xs text-slate-500 mb-2">Paste raw JSON rows here to simulate an incoming batch.</p>
              <textarea 
                className="w-full h-40 bg-white border border-slate-300 rounded p-3 text-xs font-mono text-slate-700 focus:outline-none focus:border-blue-500"
                value={customPayload}
                onChange={(e) => setCustomPayload(e.target.value)}
              ></textarea>
              <div className="mt-3 flex justify-end">
                <button onClick={handleCustomIngest} className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded text-sm font-medium transition">
                  Submit JSON Batch
                </button>
              </div>
            </div>
          )}

          {ingestMode === "file" && (
            <div className="py-4">
              <p className="text-xs text-slate-500 mb-4">Upload an Excel (.xlsx, .xls) or CSV file. The columns should map to your entity schema (e.g. customer_id, order_date, amount, event_timestamp).</p>
              
              <div className="flex items-center space-x-4">
                <input 
                  type="file" 
                  accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                  onChange={(e) => setFileToUpload(e.target.files ? e.target.files[0] : null)}
                  className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <button 
                  onClick={async () => {
                    if (!fileToUpload) return alert("Please select a file first");
                    setUploading(true);
                    const formData = new FormData();
                    formData.append("file", fileToUpload);
                    formData.append("source_system", "EXCEL_UPLOAD");
                    formData.append("entity_name", "customer_orders");
                    
                    try {
                      const res = await fetch(`${apiUrl}/api/batches/upload`, {
                        method: 'POST',
                        body: formData
                      });
                      if (res.ok) {
                        alert("File ingested and processed successfully!");
                        setFileToUpload(null);
                        fetchData();
                      } else {
                        const data = await res.json();
                        alert(`Error: ${data.detail || "Unknown error"}`);
                      }
                    } catch (err) {
                      alert("Upload failed.");
                    } finally {
                      setUploading(false);
                    }
                  }}
                  disabled={!fileToUpload || uploading}
                  className="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-6 py-2 rounded text-sm font-medium transition"
                >
                  {uploading ? "Uploading..." : "Upload & Process"}
                </button>
              </div>
            </div>
          )}
        </div>
      )}


      {loading ? (
        <div className="text-sm text-slate-500">Loading dashboard data...</div>
      ) : (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-5 gap-4">
            <div className="bg-white border rounded p-4 shadow-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide">Processed Rows</div>
              <div className="text-2xl font-semibold mt-1">{kpis?.total_rows_processed || 0}</div>
            </div>
            <div className="bg-white border rounded p-4 shadow-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide">Duplicates Detected</div>
              <div className="text-2xl font-semibold mt-1 text-amber-600">{kpis?.duplicates_detected || 0}</div>
            </div>
            <div className="bg-white border rounded p-4 shadow-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide">Auto-Repaired</div>
              <div className="text-2xl font-semibold mt-1 text-emerald-600">{kpis?.auto_repaired || 0}</div>
            </div>
            <div className="bg-white border rounded p-4 shadow-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide">Quarantined</div>
              <div className="text-2xl font-semibold mt-1 text-rose-600">{kpis?.quarantined_pending_review || 0}</div>
            </div>
            <div className="bg-white border rounded p-4 shadow-sm">
              <div className="text-xs text-slate-500 uppercase tracking-wide">False Block Rate</div>
              <div className="text-2xl font-semibold mt-1">{kpis?.false_block_rate || "0%"}</div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-8">
            <div className="col-span-2 space-y-8">
              {/* Quarantined Queue */}
              <div className="bg-white border rounded shadow-sm">
                <div className="bg-rose-50 border-b border-rose-100 p-4">
                  <h3 className="font-semibold text-rose-800">Quarantine Review Queue</h3>
                  <p className="text-xs text-rose-600">These rows require manual approval because rules could not resolve the conflict.</p>
                </div>
                <div className="p-0">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50 text-slate-500 border-b">
                      <tr>
                        <th className="p-3 font-medium">Flag ID</th>
                        <th className="p-3 font-medium">Type</th>
                        <th className="p-3 font-medium">Batch</th>
                        <th className="p-3 font-medium">Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {quarantined.length === 0 ? (
                        <tr><td colSpan={4} className="p-4 text-center text-slate-500">No pending quarantined rows.</td></tr>
                      ) : quarantined.map(d => (
                        <tr key={d.id} className="border-b hover:bg-slate-50">
                          <td className="p-3 font-mono">{d.id}</td>
                          <td className="p-3">
                            <span className="bg-rose-100 text-rose-700 px-2 py-1 rounded text-xs">{d.type}</span>
                          </td>
                          <td className="p-3 text-slate-600 font-mono text-xs">{d.batch_id}</td>
                          <td className="p-3">
                            <button onClick={() => viewRootCause(d.id)} className="text-blue-600 hover:underline text-xs font-medium">Review & Resolve</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Batches Table */}
              <div className="bg-white border rounded shadow-sm">
                <div className="p-4 border-b">
                  <h3 className="font-semibold text-slate-800">Recent Batches</h3>
                </div>
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-500 border-b">
                    <tr>
                      <th className="p-3 font-medium">Batch ID</th>
                      <th className="p-3 font-medium">Source</th>
                      <th className="p-3 font-medium">Status</th>
                      <th className="p-3 font-medium">Rows</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.map(b => (
                      <tr key={b.id} className="border-b">
                        <td className="p-3 font-mono text-xs text-slate-600">{b.id}</td>
                        <td className="p-3 text-slate-600">{b.source}</td>
                        <td className="p-3">
                          <span className="bg-emerald-100 text-emerald-700 px-2 py-1 rounded text-xs">{b.status}</span>
                        </td>
                        <td className="p-3">{b.total_rows}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="col-span-1 space-y-6">
              {/* Root Cause Panel */}
              <div className="bg-slate-800 text-white border-slate-700 rounded shadow-md overflow-hidden">
                <div className="p-4 border-b border-slate-700 bg-slate-900">
                  <h3 className="font-semibold text-slate-100">Root-Cause Diagnostics</h3>
                  <p className="text-xs text-slate-400">Click a quarantined row or duplicate to inspect.</p>
                </div>
                <div className="p-4 min-h-[300px]">
                  {!selectedDuplicate ? (
                    <div className="text-center text-slate-500 text-sm py-12">No record selected.</div>
                  ) : rcLoading ? (
                    <div className="text-center text-slate-400 text-sm py-12 animate-pulse">Loading diagnostics...</div>
                  ) : rootCause ? (
                    <div className="space-y-4 text-sm">
                      <div>
                        <div className="text-xs text-slate-400 uppercase tracking-wide">Conflict Type</div>
                        <div className="font-medium text-amber-400">{rootCause.duplicate_type}</div>
                      </div>
                      
                      <div className="bg-slate-900 p-3 rounded border border-slate-700 text-xs">
                        <div className="text-slate-400 mb-1">Lineage Step: <span className="text-slate-200">{rootCause.lineage.step}</span></div>
                        <div className="text-slate-400">Source: <span className="text-slate-200">{rootCause.lineage.source}</span></div>
                      </div>

                      {rootCause.decision.status === "PENDING_REVIEW" && (
                        <div className="bg-rose-900/40 border border-rose-800 p-3 rounded">
                          <div className="text-rose-300 font-semibold mb-1 text-xs uppercase">Engine Reason</div>
                          <div className="text-slate-200 text-xs">{rootCause.decision.reason}</div>
                        </div>
                      )}

                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-900 p-2 rounded border border-slate-700 overflow-x-auto">
                          <div className="text-slate-500 font-medium mb-1">Existing Payload</div>
                          <pre className="text-slate-300">{JSON.stringify(rootCause.existing_payload, null, 2)}</pre>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-700 overflow-x-auto">
                          <div className="text-slate-500 font-medium mb-1">Incoming Payload</div>
                          <pre className="text-blue-300">{JSON.stringify(rootCause.incoming_payload, null, 2)}</pre>
                        </div>
                      </div>

                      {rootCause.decision.status === "PENDING_REVIEW" && (
                        <div className="pt-4 border-t border-slate-700 flex space-x-2">
                          <button 
                            onClick={() => resolveQuarantine(rootCause.decision.action === 'QUARANTINED' ? (duplicates.find(d => d.id === rootCause.flag_id)?.decision_id || 0) : 0, "KEEP_EXISTING")}
                            className="flex-1 bg-slate-700 hover:bg-slate-600 text-white py-2 rounded text-xs font-medium"
                          >
                            Reject (Keep)
                          </button>
                          <button 
                            onClick={() => resolveQuarantine(duplicates.find(d => d.id === rootCause.flag_id)?.decision_id || 0, "APPROVE_INCOMING")}
                            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white py-2 rounded text-xs font-medium"
                          >
                            Approve
                          </button>
                        </div>
                      )}
                      
                      {rootCause.decision.status !== "PENDING_REVIEW" && (
                        <div className="pt-4 border-t border-slate-700">
                          <div className="text-emerald-400 font-semibold mb-1 text-xs uppercase">Resolved: {rootCause.decision.status}</div>
                          <div className="text-slate-300 text-xs">{rootCause.decision.reason || rootCause.decision.action}</div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center text-rose-400 text-sm py-12">Failed to load root cause.</div>
                  )}
                </div>
              </div>
              
              {/* All Duplicates Table - Mini */}
              <div className="bg-white border rounded shadow-sm">
                <div className="p-3 border-b">
                  <h3 className="font-semibold text-slate-800 text-sm">All Detected Conflicts</h3>
                </div>
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-500 sticky top-0">
                      <tr>
                        <th className="p-2 font-medium">Type</th>
                        <th className="p-2 font-medium">Status</th>
                        <th className="p-2 font-medium"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {duplicates.map(d => (
                        <tr key={d.id} className="border-b hover:bg-slate-50">
                          <td className="p-2 truncate max-w-[100px]">{d.type}</td>
                          <td className="p-2">
                            <span className={`px-1.5 py-0.5 rounded ${
                              d.decision_status === 'AUTO_RESOLVED' ? 'bg-emerald-100 text-emerald-700' :
                              d.decision_status === 'PENDING_REVIEW' ? 'bg-rose-100 text-rose-700' :
                              'bg-blue-100 text-blue-700'
                            }`}>
                              {d.decision_status}
                            </span>
                          </td>
                          <td className="p-2">
                            <button onClick={() => viewRootCause(d.id)} className="text-blue-600 hover:underline">View</button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          </div>
        </>
      )}
    </div>
  );
}
