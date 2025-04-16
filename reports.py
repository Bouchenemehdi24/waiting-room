from datetime import datetime, timedelta
import logging

class ReportsManager:
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)

    def get_financial_report(self, start_date=None, end_date=None):
        """Get financial report for a date range."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            params = []
            date_filter = ""
            
            if start_date and end_date:
                date_filter = "WHERE date(v.checkout_at) BETWEEN ? AND ?"
                params = [start_date, end_date]
            
            try:
                cursor.execute(f"""
                    SELECT 
                        date(v.checkout_at) as visit_date,
                        COUNT(DISTINCT v.visit_id) as total_visits,
                        SUM(v.total_paid) as daily_total,
                        GROUP_CONCAT(DISTINCT s.name) as services
                    FROM visits v
                    LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                    LEFT JOIN services s ON vs.service_id = s.service_id
                    {date_filter}
                    GROUP BY date(v.checkout_at)
                    ORDER BY visit_date DESC
                """, params)
                return cursor.fetchall()
            except Exception as e:
                self.logger.error(f"Error executing financial report query: {str(e)}")
                raise

    def search_patients(self, query, include_visits=True):
        """Enhanced patient search."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            search_term = f"%{query}%"
            
            if include_visits:
                cursor.execute("""
                    SELECT 
                        p.name,
                        COUNT(v.visit_id) as visit_count,
                        MAX(v.checkout_at) as last_visit,
                        SUM(v.total_paid) as total_spent
                    FROM patients p
                    LEFT JOIN visits v ON p.patient_id = v.patient_id
                    WHERE p.name LIKE ?
                    GROUP BY p.patient_id
                    ORDER BY p.name
                """, (search_term,))
            else:
                cursor.execute("""
                    SELECT name
                    FROM patients
                    WHERE name LIKE ?
                    ORDER BY name
                """, (search_term,))
            
            return cursor.fetchall()

    def get_analytics(self):
        """Get various analytics about the practice."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                WITH wait_times AS (
                    SELECT 
                        strftime('%H', arrived_at) as hour,
                        AVG((julianday(called_at) - julianday(arrived_at)) * 24 * 60) as avg_wait_time,
                        AVG((julianday(checkout_at) - julianday(called_at)) * 24 * 60) as avg_consultation_time,
                        COUNT(*) as visit_count
                    FROM visits
                    WHERE called_at IS NOT NULL
                    GROUP BY strftime('%H', arrived_at)
                )
                SELECT 
                    hour,
                    round(avg_wait_time, 1) as avg_wait_mins,
                    round(avg_consultation_time, 1) as avg_consultation_mins,
                    visit_count
                FROM wait_times
                ORDER BY visit_count DESC
            """)
            return cursor.fetchall()

    def get_performance_metrics(self):
        """Get detailed performance metrics."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m', checkout_at) as month,
                    COUNT(DISTINCT patient_id) as unique_patients,
                    COUNT(*) as total_visits,
                    AVG(total_paid) as avg_revenue,
                    SUM(total_paid) as total_revenue,
                    AVG((julianday(checkout_at) - julianday(called_at)) * 24 * 60) as avg_visit_duration
                FROM visits
                WHERE checkout_at IS NOT NULL
                GROUP BY strftime('%Y-%m', checkout_at)
                ORDER BY month DESC
                LIMIT 12
            """)
            return cursor.fetchall()

    def get_services_summary(self):
        """Returns a summary of services provided."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        s.name as service_name,
                        COUNT(vs.visit_id) as count,
                        SUM(s.price) as total_revenue
                    FROM services s
                    LEFT JOIN visit_services vs ON s.service_id = vs.service_id
                    GROUP BY s.service_id, s.name
                    ORDER BY count DESC, total_revenue DESC
                """)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error getting services summary: {str(e)}")
            return []
