with open('backend/app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

export_endpoint = """
from fastapi.responses import StreamingResponse

@app.get("/api/export/golden")
def export_golden_records(db: Session = Depends(get_db)):
    records = db.query(MainGoldenRecord).all()
    
    # Flatten the payload into standard columns
    data = []
    for r in records:
        row_data = r.payload.copy()
        row_data["_golden_id"] = r.id
        row_data["_winning_source"] = r.winning_source
        row_data["_merged_at"] = r.merged_at.isoformat() if r.merged_at else None
        data.append(row_data)
        
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    # Write to Excel
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Golden Records")
        
    output.seek(0)
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        headers={"Content-Disposition": "attachment; filename=golden_records.xlsx"}
    )
"""

if "/api/export/golden" not in content:
    content += export_endpoint
    with open('backend/app/main.py', 'w', encoding='utf-8') as f:
        f.write(content)
