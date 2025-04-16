import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime, timedelta
from tkcalendar import DateEntry
import locale

# Ensure French locale is set for date formatting if possible
try:
    locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR')
    except locale.Error:
        print("French locale not available, using system default for dates.")

class ReportsTab:
    def __init__(self, parent, reports_manager):
        self.parent = parent
        self.reports_manager = reports_manager
        self.setup_ui()

    def setup_ui(self):
        # Main frame for the reports tab
        main_frame = ttk.Frame(self.parent, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Configuration Frame ---
        config_frame = ttk.LabelFrame(main_frame, text="Configuration du Rapport", padding="15") # Increased padding
        config_frame.pack(fill=tk.X, pady=(0, 10))
        config_frame.columnconfigure(1, weight=1) # Allow middle column to expand

        # Report Type Selection
        ttk.Label(config_frame, text="Type de Rapport:").grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.E) # Right align label
        self.report_type_var = tk.StringVar(value="financial")
        financial_radio = ttk.Radiobutton(config_frame, text="Financier", variable=self.report_type_var, value="financial", command=self.generate_report)
        patient_radio = ttk.Radiobutton(config_frame, text="Nombre de Patients", variable=self.report_type_var, value="patient", command=self.generate_report)
        # Use a frame for radio buttons to keep them together horizontally
        report_type_frame = ttk.Frame(config_frame)
        report_type_frame.grid(row=0, column=1, columnspan=3, padx=5, pady=5, sticky=tk.W)
        # Use grid within the frame
        financial_radio.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        patient_radio.grid(row=0, column=1, sticky=tk.W)

        # Date Range Selection
        ttk.Label(config_frame, text="Période:").grid(row=1, column=0, padx=(0, 5), pady=5, sticky=tk.E) # Right align label
        self.date_range_var = tk.StringVar(value="today")

        date_options_frame = ttk.Frame(config_frame)
        date_options_frame.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5) # Use grid and sticky W

        # Use grid for date radio buttons within their frame
        ttk.Radiobutton(date_options_frame, text="Aujourd'hui", variable=self.date_range_var, value="today", command=self.toggle_date_entries).grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Radiobutton(date_options_frame, text="Hier", variable=self.date_range_var, value="yesterday", command=self.toggle_date_entries).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(date_options_frame, text="Semaine Précédente", variable=self.date_range_var, value="last_week", command=self.toggle_date_entries).grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Radiobutton(date_options_frame, text="Personnalisée", variable=self.date_range_var, value="custom", command=self.toggle_date_entries).grid(row=0, column=3, sticky=tk.W, padx=5)

        # --- Custom Date Sub-Frame --- (Defined but not placed initially)
        self.custom_date_frame = ttk.Frame(config_frame)
        # Custom Date Entries (initially disabled, inside the sub-frame)
        ttk.Label(self.custom_date_frame, text="De:").grid(row=0, column=0, padx=(0, 2), pady=5, sticky=tk.E)
        self.start_date_entry = DateEntry(self.custom_date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/MM/yyyy', locale='fr_FR')
        self.start_date_entry.grid(row=0, column=1, padx=(0, 10), pady=5, sticky=tk.W) # Added padding
        self.start_date_entry.config(state='disabled')
        self.start_date_entry.bind("<<DateEntrySelected>>", lambda event: self.generate_report() if self.date_range_var.get() == 'custom' else None)

        ttk.Label(self.custom_date_frame, text="À:").grid(row=0, column=2, padx=(10, 2), pady=5, sticky=tk.E) # Added padding
        self.end_date_entry = DateEntry(self.custom_date_frame, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/MM/yyyy', locale='fr_FR')
        self.end_date_entry.grid(row=0, column=3, padx=(0, 5), pady=5, sticky=tk.W)
        self.end_date_entry.config(state='disabled')
        self.end_date_entry.bind("<<DateEntrySelected>>", lambda event: self.generate_report() if self.date_range_var.get() == 'custom' else None)

        # Generate Report Button (Centered)
        self.generate_btn = ttk.Button(config_frame, text="Générer Rapport", command=self.generate_report)
        self.generate_btn.grid(row=3, column=0, columnspan=4, pady=15) # Increased pady, centered by spanning

        # --- Results Frame ---
        results_frame = ttk.LabelFrame(main_frame, text="Résultats", padding="10")
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, height=15, font=('Courier New', 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.results_text.config(state='disabled') # Make read-only initially

        # Initial report generation
        self.generate_report()

    def toggle_date_entries(self):
        """Show/hide and enable/disable custom date entries based on selection."""
        if self.date_range_var.get() == "custom":
            # Place the custom date frame in the grid
            self.custom_date_frame.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=(5,0))
            self.start_date_entry.config(state='normal')
            self.end_date_entry.config(state='normal')
            # Don't auto-generate report when 'custom' is selected initially
        else:
            # Remove the custom date frame from the grid
            self.custom_date_frame.grid_forget()
            self.start_date_entry.config(state='disabled')
            self.end_date_entry.config(state='disabled')
            self.generate_report() # Generate report for predefined ranges

    def get_date_range(self):
        """Calculate start and end dates based on selection."""
        today = datetime.now().date()
        range_type = self.date_range_var.get()

        if range_type == "today":
            start_date = today
            end_date = today
        elif range_type == "yesterday":
            start_date = today - timedelta(days=1)
            end_date = today - timedelta(days=1)
        elif range_type == "last_week":
            # Monday of last week to Sunday of last week
            start_of_this_week = today - timedelta(days=today.weekday())
            end_date = start_of_this_week - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
        elif range_type == "custom":
            try:
                start_date = self.start_date_entry.get_date()
                end_date = self.end_date_entry.get_date()
                if start_date > end_date:
                    tk.messagebox.showerror("Erreur de Date", "La date de début ne peut pas être après la date de fin.", parent=self.parent)
                    return None, None
            except Exception as e:
                tk.messagebox.showerror("Erreur de Date", f"Format de date invalide: {e}", parent=self.parent)
                return None, None
        else: # Default to today
            start_date = today
            end_date = today

        # Return dates in 'YYYY-MM-DD' format for SQL
        return start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')

    def generate_report(self):
        """Fetch data and display the selected report."""
        start_date, end_date = self.get_date_range()
        if start_date is None or end_date is None:
            return # Error handled in get_date_range

        report_type = self.report_type_var.get()
        report_content = f"Rapport: {report_type.capitalize()}\n"
        report_content += f"Période: {datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')} au {datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')}\n"
        report_content += "=" * 40 + "\n\n"

        try:
            if report_type == "financial":
                data = self.reports_manager.get_financial_summary(start_date, end_date)
                report_content += f"Revenu Total: {data.get('total_revenue', 0):,.2f} DA\n"
                report_content += f"Nombre Total de Visites Payantes: {data.get('total_visits', 0)}\n"
            elif report_type == "patient":
                data = self.reports_manager.get_patient_count(start_date, end_date)
                report_content += f"Nombre de Patients Uniques Vus: {data.get('unique_patients', 0)}\n"
            else:
                report_content += "Type de rapport non reconnu."

        except Exception as e:
            report_content += f"Erreur lors de la génération du rapport:\n{str(e)}"
            self.reports_manager.logger.exception("Error generating report")

        # Display results
        self.results_text.config(state='normal')
        self.results_text.delete(1.0, tk.END)
        self.results_text.insert(tk.END, report_content)
        self.results_text.config(state='disabled')

# Example usage (for testing purposes)
if __name__ == '__main__':
    # This requires a mock ReportsManager or a running DB connection setup
    class MockDbManager:
        @contextmanager
        def get_connection(self):
            # Mock connection if needed, or connect to a test DB
            conn = sqlite3.connect(':memory:') # In-memory DB for testing
            conn.row_factory = sqlite3.Row
            # Create necessary tables/data if needed for testing
            yield conn
            conn.close()

    class MockReportsManager:
        def __init__(self, db_manager):
            self.db = db_manager
            self.logger = logging.getLogger(__name__)

        def get_financial_summary(self, start_date, end_date):
            # Mock data
            print(f"Mock Financial Fetch: {start_date} to {end_date}")
            if start_date == '2025-04-13':
                 return {'total_revenue': 1500.50, 'total_visits': 5}
            elif start_date == '2025-04-12':
                 return {'total_revenue': 800.00, 'total_visits': 3}
            else:
                 return {'total_revenue': 5250.75, 'total_visits': 25}


        def get_patient_count(self, start_date, end_date):
             # Mock data
            print(f"Mock Patient Count Fetch: {start_date} to {end_date}")
            if start_date == '2025-04-13':
                return {'unique_patients': 4}
            elif start_date == '2025-04-12':
                return {'unique_patients': 2}
            else:
                return {'unique_patients': 20}

    root = tk.Tk()
    root.title("Test Rapports Tab")
    root.geometry("600x400")

    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO)

    mock_db = MockDbManager()
    mock_manager = MockReportsManager(mock_db)

    app = ReportsTab(root, mock_manager)
    root.mainloop()
