import re

with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add "Download Updated Excel" button in header
header_btn_old = '<button \n            onClick={() => setShowIngest(!showIngest)}'
header_btn_new = '''<a 
            href={`${apiUrl}/api/export/golden`}
            download="golden_records.xlsx"
            className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition inline-block"
          >
            Download Updated Excel
          </a>
          <button 
            onClick={() => setShowIngest(!showIngest)}'''
content = content.replace(header_btn_old, header_btn_new)

# 2. Add Drag and Drop to File Uploader
drag_drop_old = '''<div className="flex items-center space-x-4">
                <input 
                  type="file" 
                  accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                  onChange={(e) => setFileToUpload(e.target.files ? e.target.files[0] : null)}
                  className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />'''
drag_drop_new = '''<div 
                className="flex flex-col items-center justify-center space-y-4 border-2 border-dashed border-slate-300 rounded-lg p-8 bg-white hover:bg-slate-50 transition"
                onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                    setFileToUpload(e.dataTransfer.files[0]);
                  }
                }}
              >
                <div className="text-center">
                  <p className="text-sm text-slate-600 font-medium">{fileToUpload ? fileToUpload.name : "Drag & drop an Excel or CSV file here"}</p>
                  <p className="text-xs text-slate-400 mt-1">or click below to browse</p>
                </div>
                <input 
                  type="file" 
                  accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                  onChange={(e) => setFileToUpload(e.target.files ? e.target.files[0] : null)}
                  className="text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </div>
              <div className="flex items-center space-x-4 mt-4">'''
content = content.replace(drag_drop_old, drag_drop_new)

# Fix missing closing div for the flex container if needed
# Wait, replacing `flex items-center space-x-4` with two divs... I need to make sure I don't break the JSX tree.
# The original was:
# <div className="flex items-center space-x-4">
#   <input ... />
#   <button ... />
# </div>
# The replacement makes it:
# <div drag-drop ...> <input /> </div>
# <div flex space-x-4 mt-4> <button /> ... wait, the button needs to be in this new div.
# Yes, because I replaced just the opening tag and the input. The button and closing div are untouched. So the tree is valid.

# 3. Diff View for JSON payload
diff_view_old = '''<div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-900 p-2 rounded border border-slate-700 overflow-x-auto">
                          <div className="text-slate-500 font-medium mb-1">Existing Payload</div>
                          <pre className="text-slate-300">{JSON.stringify(rootCause.existing_payload, null, 2)}</pre>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-700 overflow-x-auto">
                          <div className="text-slate-500 font-medium mb-1">Incoming Payload</div>
                          <pre className="text-blue-300">{JSON.stringify(rootCause.incoming_payload, null, 2)}</pre>
                        </div>
                      </div>'''

diff_view_new = '''<div className="grid grid-cols-2 gap-2 text-xs">
                        <div className="bg-slate-900 p-2 rounded border border-slate-700 overflow-x-auto">
                          <div className="text-slate-500 font-medium mb-2 pb-1 border-b border-slate-700 flex items-center justify-between">
                            <span>Existing (Unupdated)</span>
                            <span className="bg-rose-900/50 text-rose-400 px-1.5 py-0.5 rounded text-[10px]">Old</span>
                          </div>
                          <div className="space-y-1 font-mono">
                            {Object.entries(rootCause.existing_payload || {}).map(([k, v]) => {
                              const inV = rootCause.incoming_payload?.[k];
                              const isDiff = inV !== undefined && v !== inV;
                              return (
                                <div key={k} className={`${isDiff ? 'bg-rose-900/30 -mx-2 px-2 border-l-2 border-rose-500 text-rose-300' : 'text-slate-300'}`}>
                                  <span className="text-slate-500">{k}:</span> {JSON.stringify(v)}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                        <div className="bg-slate-900 p-2 rounded border border-slate-700 overflow-x-auto">
                          <div className="text-slate-500 font-medium mb-2 pb-1 border-b border-slate-700 flex items-center justify-between">
                            <span>Incoming (Updated)</span>
                            <span className="bg-emerald-900/50 text-emerald-400 px-1.5 py-0.5 rounded text-[10px]">New</span>
                          </div>
                          <div className="space-y-1 font-mono">
                            {Object.entries(rootCause.incoming_payload || {}).map(([k, v]) => {
                              const exV = rootCause.existing_payload?.[k];
                              const isDiff = exV !== undefined && v !== exV;
                              return (
                                <div key={k} className={`${isDiff ? 'bg-emerald-900/30 -mx-2 px-2 border-l-2 border-emerald-500 text-emerald-300' : 'text-slate-300'}`}>
                                  <span className="text-slate-500">{k}:</span> {JSON.stringify(v)}
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </div>'''
content = content.replace(diff_view_old, diff_view_new)

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
