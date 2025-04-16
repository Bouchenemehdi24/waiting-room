import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from database import DatabaseError # Import DatabaseError for handling exceptions

# Dialog for adding a new patient
class NewPatientDialog:
    def __init__(self, parent, db, on_success):
        self.top = tk.Toplevel(parent)
        self.top.title("Nouveau Patient")
        self.top.geometry("400x200")
        self.db = db
        self.on_success = on_success # Callback function after successful addition

        self.top.transient(parent)
        self.top.grab_set()

        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.top, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # Name Entry
        ttk.Label(frame, text="Nom du patient:").pack(anchor=tk.W)
        self.name_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.name_entry.pack(fill=tk.X, pady=(0, 10))
        self.name_entry.focus()

        # Phone Number Entry (Optional)
        ttk.Label(frame, text="Numéro de téléphone (Optionnel):").pack(anchor=tk.W)
        self.phone_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        self.phone_entry.pack(fill=tk.X, pady=(0, 10))

        # Bind Enter key for navigation/submission
        self.name_entry.bind('<Return>', lambda e: self.phone_entry.focus())
        self.phone_entry.bind('<Return>', lambda e: self.submit())

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))

        ttk.Button(btn_frame, text="Ajouter",
                  command=self.submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def submit(self):
        name = self.name_entry.get().strip()
        phone_number = self.phone_entry.get().strip() or None # Use None if empty

        if not name:
            messagebox.showerror("Erreur", "Le nom du patient est obligatoire.", parent=self.top)
            return

        try:
            # Attempt to add the patient via the database manager
            patient_id = self.db.add_patient(name, phone_number=phone_number)
            if patient_id:
                messagebox.showinfo("Succès", f"Patient '{name}' ajouté avec succès.", parent=self.top)
                self.on_success() # Call the success callback (e.g., reload patient list)
                self.top.destroy()
            # The db.add_patient method should raise DatabaseError for duplicates or other issues
        except DatabaseError as e:
            # Catch specific database errors (like duplicates)
            messagebox.showerror("Erreur", f"Impossible d'ajouter le patient:\n{e}", parent=self.top)
        except Exception as e:
            # Catch any other unexpected errors
            messagebox.showerror("Erreur Inattendue", f"Une erreur est survenue: {e}", parent=self.top)


class PatientListDialog:
    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Liste des Patients")
        self.top.geometry("800x600")
        self.db = db
        self.create_widgets()
        self.load_patients()
        
    def create_widgets(self):
        # Search section
        search_frame = ttk.LabelFrame(self.top, text="Rechercher un patient", padding="5")
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Patient list
        list_frame = ttk.LabelFrame(self.top, text="Patients", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('name', 'visits', 'last_visit', 'total_spent')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns
        self.tree.heading('name', text='Nom du Patient')
        self.tree.heading('visits', text='Nombre de Visites')
        self.tree.heading('last_visit', text='Dernière Visite')
        self.tree.heading('total_spent', text='Total Payé')
        
        self.tree.column('name', width=200)
        self.tree.column('visits', width=100, anchor='center')
        self.tree.column('last_visit', width=150)
        self.tree.column('total_spent', width=100, anchor='e')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add action buttons
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Voir Historique",
                  command=self.show_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Nouveau Patient",
                  command=self.open_new_patient_form).pack(side=tk.LEFT, padx=5) # Added New Patient button
        ttk.Button(btn_frame, text="Fermer",
                  command=self.top.destroy).pack(side=tk.RIGHT, padx=5)

    def open_new_patient_form(self):
        """Opens the dialog to add a new patient."""
        # Create and display the NewPatientDialog
        # Pass self.load_patients as the callback to refresh the list on success
        dialog = NewPatientDialog(self.top, self.db, self.load_patients)
        # Wait for the dialog to close before continuing
        self.top.wait_window(dialog.top)

    def load_patients(self):
        """Load all patients with their visit information"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        p.name,
                        COUNT(v.visit_id) as visit_count,
                        MAX(v.checkout_at) as last_visit,
                        SUM(v.total_paid) as total_spent
                    FROM patients p
                    LEFT JOIN visits v ON p.patient_id = v.patient_id
                    GROUP BY p.patient_id
                    ORDER BY p.name
                """)
                
                self.tree.delete(*self.tree.get_children())
                for row in cursor.fetchall():
                    last_visit = row['last_visit'] if row['last_visit'] else 'Jamais'
                    if last_visit != 'Jamais':
                        last_visit = datetime.strptime(last_visit, 
                            "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y")
                    total_spent = f"{row['total_spent']} DA" if row['total_spent'] else '0 DA'
                    
                    self.tree.insert('', 'end', values=(
                        row['name'],
                        row['visit_count'],
                        last_visit,
                        total_spent
                    ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des patients: {str(e)}")

    def on_search(self, event=None):
        """Filter patient list based on search text"""
        search_text = self.search_entry.get().strip().lower()
        
        # Show all items if search is empty
        if not search_text:
            self.load_patients()
            return
            
        # Hide non-matching items
        for item in self.tree.get_children():
            patient_name = self.tree.item(item)['values'][0].lower()
            if search_text in patient_name:
                self.tree.reattach(item, '', 'end')
            else:
                self.tree.detach(item)

    def show_history(self):
        """Show detailed history for selected patient"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient")
            return
            
        patient_name = self.tree.item(selection[0])['values'][0]
        
        # Create history window
        history = tk.Toplevel(self.top)
        history.title(f"Historique - {patient_name}")
        history.geometry("600x400")
        
        # Create history treeview
        columns = ('date', 'services', 'paid')
        tree = ttk.Treeview(history, columns=columns, show='headings')
        
        tree.heading('date', text='Date')
        tree.heading('services', text='Services')
        tree.heading('paid', text='Montant')
        
        tree.column('date', width=100)
        tree.column('services', width=300)
        tree.column('paid', width=100, anchor='e')
        
        scrollbar = ttk.Scrollbar(history, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load patient history
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        v.checkout_at,
                        GROUP_CONCAT(s.name) as services,
                        v.total_paid
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                    LEFT JOIN services s ON vs.service_id = s.service_id
                    WHERE p.name = ?
                    GROUP BY v.visit_id
                    ORDER BY v.checkout_at DESC
                """, (patient_name,))
                
                for row in cursor.fetchall():
                    if row['checkout_at']:
                        visit_date = datetime.strptime(
                            row['checkout_at'], 
                            "%Y-%m-%d %H:%M:%S"
                        ).strftime("%d/%m/%Y")
                        services = row['services'] if row['services'] else "Consultation"
                        tree.insert('', 'end', values=(
                            visit_date,
                            services,
                            f"{row['total_paid']} DA"
                        ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement de l'historique: {str(e)}")
