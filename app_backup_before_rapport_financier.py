import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import logging

class DoctorsWaitingRoomApp:
    def __init__(self, root):
        self.root = root
        self.logger = logging.getLogger(__name__)
        # Initialize other components here (sidebar, main UI, etc.)

    def get_hourly_visits(self):
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        strftime('%H', arrived_at) as hour,
                        COUNT(*) as count
                    FROM visits
                    WHERE date(arrived_at) = date('now')
                    GROUP BY hour
                    ORDER BY hour
                """)
                results = cursor.fetchall()
                
                # Initialize arrays with numeric hours
                hours = list(range(8, 19))  # 8am to 18pm (6pm)
                counts = [0] * len(hours)
                
                # Fill in actual counts
                for row in results:
                    hour = int(row['hour'])
                    if 8 <= hour <= 18:  # Only count hours within business hours
                        counts[hour - 8] = row['count']  # Offset by 8 to match array index
                        
                return hours, counts
        except Exception as e:
            self.logger.warning(f"Error getting hourly visits: {str(e)}")
            return [], []

    def load_visits_by_period(self, tree, start_date, end_date):
        """Load visits in the given date range into treeview"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT
                        v.arrived_at,
                        p.name,
                        GROUP_CONCAT(s.name) as services,
                        (strftime('%s', v.checkout_at) - strftime('%s', v.called_at))/60.0 as duration,
                        v.total_paid,
                        CASE
                            WHEN v.checkout_at IS NOT NULL THEN 'Terminé'
                            WHEN v.called_at IS NOT NULL THEN 'En consultation'
                            ELSE 'En attente'
                        END as status
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                    LEFT JOIN services s ON vs.service_id = s.service_id
                    WHERE date(v.arrived_at) >= ? AND date(v.arrived_at) <= ?
                    GROUP BY v.visit_id
                    ORDER BY v.arrived_at DESC
                """, (start_date, end_date))
                
                tree.delete(*tree.get_children())
                for row in cursor.fetchall():
                    arrival = datetime.strptime(row['arrived_at'], "%Y-%m-%d %H:%M:%S")
                    duration = f"{int(row['duration'])} min" if row['duration'] else "N/A"
                    services = row['services'] if row['services'] else "Aucun"
                    payment = f"{row['total_paid']} DA" if row['total_paid'] else "N/A"
                    
                    tree.insert("", "end", values=(
                        arrival.strftime("%Y-%m-%d"),
                        arrival.strftime("%H:%M"),
                        row['name'],
                        services,
                        duration,
                        payment,
                        row['status']
                    ))
        except Exception as e:
            self.logger.exception("Error loading visits for period")
        # Removed open_booking_dialog (appointment booking functionality)
        # Removed obsolete wait_window call for dialog, as dialog is no longer used in this function.

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    try:
        logger.info("Starting application...")
        root = tk.Tk()
        app = DoctorsWaitingRoomApp(root)
        root.mainloop()
    except Exception as e:
        logger.exception("Unhandled exception occurred")
        messagebox.showerror("Erreur Critique", 
                           "Une erreur inattendue s'est produite. "
                           "L'application va se fermer.")
        raise