import re

with open('app/seed.py', 'r', encoding='utf-8') as f:
    content = f.read()

random_seed_logic = """
    import random
    import string
    from datetime import timedelta

    print("Seeding additional random data...")
    sources = ["CRM_PRIMARY", "WEB_STORE", "POS_LEGACY", "PARTNER_EXTRACT", "MOBILE_APP"]
    
    # Pre-seed some golden records to create conflicts
    golden_customers = []
    for i in range(1, 21): # 20 golden records
        cust_id = f"CUST-2{i:03d}"
        golden_customers.append(cust_id)
        payload = {
            "customer_id": cust_id,
            "order_date": "2026-09-22",
            "customer_name": f"Random User {i}",
            "amount": round(random.uniform(50, 500), 2),
            "event_timestamp": "2026-09-22T08:00:00Z",
            "source_system": "CRM_PRIMARY",
            "source_rank": 1
        }
        h = compute_composite_hash(payload, registry_config.composite_keys)
        db.add(MainGoldenRecord(
            entity_name="customer_orders",
            composite_key_hash=h,
            payload=payload,
            last_event_time=datetime.fromisoformat("2026-09-22T08:00:00+00:00"),
            winning_source="CRM_PRIMARY"
        ))
    db.commit()

    for batch_num in range(5, 15):
        batch = IncomingBatch(
            id=f"batch-20260922-{batch_num:03d}",
            source_system=random.choice(sources),
            status="INGESTED",
            total_rows=random.randint(5, 15)
        )
        db.add(batch)
        db.commit()

        for r in range(batch.total_rows):
            is_conflict = random.random() < 0.6  # 60% chance of conflict
            
            if is_conflict:
                cust_id = random.choice(golden_customers)
                order_date = "2026-09-22"
            else:
                cust_id = f"CUST-3{batch_num:03d}{r:02d}"
                order_date = "2026-09-22"

            source = batch.source_system
            rank = 1 if source == "CRM_PRIMARY" else (2 if source == "WEB_STORE" else (3 if source == "POS_LEGACY" else 99))
            
            # 20% exact, 20% late, 40% rank/source, 20% unranked quarantine
            scenario = random.random()
            
            # Helper to extract a number for the name safely
            try:
                user_num = int(cust_id.split('-')[-1])
            except:
                user_num = 99
                
            if is_conflict and scenario < 0.2:
                # exact duplicate payload
                payload = {
                    "customer_id": cust_id,
                    "order_date": order_date,
                    "customer_name": f"Random User {user_num}",
                    "amount": 150.00,
                    "event_timestamp": "2026-09-22T08:00:00Z",
                    "source_system": "CRM_PRIMARY",
                    "source_rank": 1
                }
            elif is_conflict and scenario < 0.4:
                # late arrival
                payload = {
                    "customer_id": cust_id,
                    "order_date": order_date,
                    "customer_name": f"Random User {user_num}",
                    "amount": round(random.uniform(50, 500), 2),
                    "event_timestamp": "2026-09-22T07:00:00Z", # older
                    "source_system": source,
                    "source_rank": rank
                }
            elif is_conflict and scenario < 0.8:
                # standard conflict
                payload = {
                    "customer_id": cust_id,
                    "order_date": order_date,
                    "customer_name": f"Random User {user_num}",
                    "amount": round(random.uniform(50, 500), 2),
                    "event_timestamp": "2026-09-22T09:00:00Z", # newer
                    "source_system": source,
                    "source_rank": rank
                }
            else:
                # quarantine or new record
                payload = {
                    "customer_id": cust_id,
                    "order_date": order_date,
                    "customer_name": f"Random User {user_num}",
                    "amount": round(random.uniform(50, 500), 2),
                    "event_timestamp": "2026-09-22T10:00:00Z",
                    "source_system": "UNKNOWN_SYS",
                    "source_rank": 99
                }

            h = compute_composite_hash(payload, registry_config.composite_keys)
            db.add(IncomingRow(batch_id=batch.id, entity_name="customer_orders", payload=payload, composite_key_hash=h))
        
        db.commit()
    print("Random data seeded successfully.")
"""

target = 'print("Seeded synthetic test batches (Exact Duplicate, Late Arrival, Source Conflict, Ambiguous Quarantine).")'
content = content.replace(target, target + "\n" + random_seed_logic)

with open('app/seed.py', 'w', encoding='utf-8') as f:
    f.write(content)
