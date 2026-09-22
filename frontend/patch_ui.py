import re

with open('src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

state_logic = """  const [rcLoading, setRcLoading] = useState(false);
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
"""

content = content.replace('  const [rcLoading, setRcLoading] = useState(false);', state_logic)

header_buttons = """        <div className="space-x-3">
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
        </div>"""

old_header_button = """        <button 
          onClick={handleSeed}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded text-sm font-medium transition"
        >
          Seed Demo Data
        </button>"""

content = content.replace(old_header_button, header_buttons)

ingest_panel = """
      {showIngest && (
        <div className="bg-slate-50 border border-slate-200 rounded p-4 shadow-inner">
          <h3 className="font-semibold text-slate-800 mb-2 text-sm">Live Custom Ingestion (JSON Array)</h3>
          <p className="text-xs text-slate-500 mb-3">
            Paste raw JSON rows here to simulate an incoming batch during your presentation. The engine will instantly parse it, check for duplicates against the golden records, and appear in the tables below.
          </p>
          <textarea 
            className="w-full h-48 bg-white border border-slate-300 rounded p-3 text-xs font-mono text-slate-700 focus:outline-none focus:border-blue-500"
            value={customPayload}
            onChange={(e) => setCustomPayload(e.target.value)}
          ></textarea>
          <div className="mt-3 flex justify-end">
            <button 
              onClick={handleCustomIngest}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2 rounded text-sm font-medium transition"
            >
              Submit Batch to Engine
            </button>
          </div>
        </div>
      )}
"""

content = content.replace('{loading ? (', ingest_panel + '\n      {loading ? (')

with open('src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
