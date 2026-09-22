with open('backend/app/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

import_replacement = """from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import json"""

content = content.replace('from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks', import_replacement)

upload_endpoint = """
@app.post("/api/batches/upload")
async def upload_batch(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...),
    source_system: str = Form("EXCEL_UPLOAD"),
    entity_name: str = Form("customer_orders"),
    db: Session = Depends(get_db)
):
    # Check if entity is registered
    registry = db.query(KeyRegistry).filter(KeyRegistry.entity_name == entity_name).first()
    if not registry:
        raise HTTPException(status_code=400, detail="Entity not registered")

    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")

    # Clean DataFrame (handle NaNs)
    df = df.fillna("")
    
    # Optional: convert specific columns or let the engine handle string matching
    # Convert back to dict
    rows = df.to_dict(orient="records")
    
    import hashlib
    def compute_hash(p: dict, keys: list[str]) -> str:
        key_vals = [str(p.get(k, '')).strip().lower() for k in keys]
        return hashlib.sha256("|".join(key_vals).encode('utf-8')).hexdigest()

    import time
    batch_id = f"upload-batch-{int(time.time())}"
    batch = IncomingBatch(id=batch_id, source_system=source_system, status="INGESTED", total_rows=len(rows))
    db.add(batch)
    
    for row_data in rows:
        h = compute_hash(row_data, registry.composite_keys)
        db.add(IncomingRow(batch_id=batch.id, entity_name=entity_name, payload=row_data, composite_key_hash=h))
        
    db.commit()
    
    # Process immediately
    process_batch(batch.id, db)
    return {"message": f"Successfully processed {len(rows)} rows from {file.filename}", "batch_id": batch.id}
"""

content += upload_endpoint

with open('backend/app/main.py', 'w', encoding='utf-8') as f:
    f.write(content)
