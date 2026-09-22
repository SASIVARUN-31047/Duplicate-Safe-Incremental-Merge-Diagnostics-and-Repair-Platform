with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

state_logic = """  const [rcLoading, setRcLoading] = useState(false);
  const [showIngest, setShowIngest] = useState(false);
  const [ingestMode, setIngestMode] = useState<"json" | "file">("json");
  const [fileToUpload, setFileToUpload] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);"""

content = content.replace('  const [rcLoading, setRcLoading] = useState(false);', state_logic)

# Replace the ingest panel
old_panel_start = '{showIngest && ('
old_panel_end = 'Submit Batch to Engine\n            </button>\n          </div>\n        </div>\n      )}\n'

new_panel = """{showIngest && (
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
"""

import re
# Regex to match the old block
# Since the exact text spans multiple lines, we can use re.sub with re.DOTALL
content = re.sub(r'\{showIngest && \(\s*<div className="bg-slate-50.*?</button>\s*</div>\s*</div>\s*\)\}', new_panel, content, flags=re.DOTALL)

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
