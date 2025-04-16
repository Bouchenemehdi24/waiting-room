import json
import os
from database import DatabaseManager

def migrate_data():
    db = DatabaseManager()
    
    # Migrate services
    if os.path.exists("services.json"):
        with open("services.json", "r") as f:
            services = json.load(f)
            with db.get_connection() as conn:
                cursor = conn.cursor()
                for name, price in services.items():
                    cursor.execute(
                        "INSERT OR IGNORE INTO services (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                conn.commit()
    
    # Migrate patient records
    if os.path.exists("patient_records.json"):
        with open("patient_records.json", "r") as f:
            records = json.load(f)
            
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                for name, data in records.items():
                    # Add patient
                    patient_id = db.add_patient(name)
                    
                    # Add visits
                    for visit in data["visits"]:
                        cursor.execute("""
                            INSERT INTO visits 
                            (patient_id, date, arrived_at, called_at, checkout_at, total_paid)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            patient_id,
                            visit["date"],
                            visit.get("arrived_at"),
                            visit.get("called_at"),
                            visit.get("checkout_at"),
                            visit.get("total_paid", 0)
                        ))
                        
                        visit_id = cursor.lastrowid
                        
                        # Add visit services
                        if "services" in visit:
                            for service_name in visit["services"]:
                                cursor.execute(
                                    "SELECT service_id FROM services WHERE name = ?",
                                    (service_name,)
                                )
                                service_id = cursor.fetchone()[0]
                                
                                cursor.execute("""
                                    INSERT INTO visit_services (visit_id, service_id)
                                    VALUES (?, ?)
                                """, (visit_id, service_id))
                
                conn.commit()

if __name__ == "__main__":
    migrate_data()
    print("Migration completed successfully!")
