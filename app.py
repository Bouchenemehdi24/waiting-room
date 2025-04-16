import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime, timedelta
import sqlite3
from tkinter.font import Font
from accounting import AccountingManager # Removed FinancialReport
# Updated import to include new classes and exceptions
from database import DatabaseManager, DatabaseError, DatabaseOperationError, DatabaseConnectionError
from reports_manager import ReportsManager # Corrected import path
from reports_tab import ReportsTab # Added import for the new tab class
import logging
from logging_config import setup_logging
import locale
import json  # Add at the top of app.py

from babel.dates import format_date
from tkcalendar import DateEntry

try:
    locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')  # Set French locale
except:
    try:
        locale.setlocale(locale.LC_ALL, 'fr_FR')
    except:
        pass  # If French locale is not available, use system default

try:
    from PIL import Image, ImageTk
except ImportError:
    messagebox.showwarning("Information", "Pour une meilleure interface, installez PIL: pip install Pillow")
    Image = None

# Simple tooltip class for Tkinter widgets
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        import logging
        if self.tipwindow or not self.text:
            return
        widget_type = type(self.widget).__name__
        has_bbox = hasattr(self.widget, "bbox")
        x = y = cy = 0
        if has_bbox:
            try:
                x, y, _, cy = self.widget.bbox("insert")
            except Exception as e:
                logging.getLogger("UserAction").warning(
                    f"Tooltip bbox('insert') failed for widget type {widget_type}: {e}"
                )
                x, y, cy = 0, 0, 0
        else:
            x, y, cy = 0, 0, 0
        x = x + self.widget.winfo_rootx() + 20
        y = y + self.widget.winfo_rooty() + cy + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=4, ipady=2)

    def hide_tip(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

class ServiceSettingsDialog:
    # Keep original functionality, but saving will be handled by the main app based on role
    def __init__(self, parent, services):
        self.top = tk.Toplevel(parent)
        self.top.title("Paramètres des services")
        self.top.geometry("400x500")
        self.services = services.copy()
        self.original_services = services.copy()  # Keep original for comparison
        self.create_widgets()

        # Make dialog modal
        self.top.transient(parent)
        self.top.grab_set()

        # Add closing confirmation
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        # Service list frame
        list_frame = ttk.LabelFrame(self.top, text="Services disponibles", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Services list with sorting
        self.services_list = ttk.Treeview(list_frame,
                                        columns=("service", "price"),
                                        show="headings",
                                        height=10)
        self.services_list.heading("service", text="Service", command=lambda: self.sort_services("service"))
        self.services_list.heading("price", text="Prix (DA)", command=lambda: self.sort_services("price"))

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.services_list.yview)
        self.services_list.configure(yscrollcommand=scrollbar.set)

        self.services_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Selection event
        self.services_list.bind('<<TreeviewSelect>>', self.on_select)
        # Inline editing event
        self.services_list.bind('<Double-1>', self.on_treeview_double_click)

        # Add/Edit frame
        edit_frame = ttk.LabelFrame(self.top, text="Ajouter/Modifier un service", padding="10")
        edit_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(edit_frame, text="Service:").grid(row=0, column=0, padx=5, pady=5)
        self.service_entry = ttk.Entry(edit_frame)
        self.service_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(edit_frame, text="Prix (DA):").grid(row=1, column=0, padx=5, pady=5)
        vcmd = (self.top.register(self.validate_price), '%P')
        self.price_entry = ttk.Entry(edit_frame, validate='key', validatecommand=vcmd)
        self.price_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        edit_frame.columnconfigure(1, weight=1)

        # Buttons frame
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Ajouter/Modifier",
                  command=self.add_update_service).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Supprimer",
                  command=self.delete_service).pack(side=tk.LEFT, padx=5)
        # Changed "Enregistrer" to "OK" - saving happens in main app
        ttk.Button(btn_frame, text="OK",
                  command=self.save_changes).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.on_closing).pack(side=tk.RIGHT, padx=5)

        self.update_service_list()

        # Tooltips
        Tooltip(self.services_list, "Double-click a cell to edit the service name or price.")
        Tooltip(self.service_entry, "Enter the name of the service.")
        Tooltip(self.price_entry, "Enter the price in DA (must be a positive integer).")
        Tooltip(btn_frame.winfo_children()[0], "Add or update the service in the list.")
        Tooltip(btn_frame.winfo_children()[1], "Delete the selected service from the list.")
        Tooltip(btn_frame.winfo_children()[2], "Save changes and close the dialog.")
        Tooltip(btn_frame.winfo_children()[3], "Cancel and close the dialog without saving.")

        # For inline editing
        self._edit_entry = None
        self._edit_column = None
        self._edit_item = None

    def on_treeview_double_click(self, event):
        # Identify the row and column
        region = self.services_list.identify("region", event.x, event.y)
        if region != "cell":
            return
        row_id = self.services_list.identify_row(event.y)
        col_id = self.services_list.identify_column(event.x)
        if not row_id or not col_id:
            return

        col = int(col_id.replace("#", "")) - 1
        if col not in (0, 1):
            return  # Only allow editing service or price

        # Get cell bbox
        bbox = self.services_list.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, width, height = bbox

        # Get current value
        values = self.services_list.item(row_id, "values")
        current_value = values[col]

        # Create entry widget
        if self._edit_entry:
            self._edit_entry.destroy()
        self._edit_entry = tk.Entry(self.services_list)
        self._edit_entry.insert(0, current_value)
        self._edit_entry.place(x=x, y=y, width=width, height=height)
        self._edit_entry.focus_set()
        self._edit_column = col
        self._edit_item = row_id

        def on_confirm(event=None):
            new_value = self._edit_entry.get().strip()
            service, price = values
            if col == 0:
                # Editing service name
                if not new_value:
                    messagebox.showerror("Erreur", "Le nom du service est obligatoire", parent=self.top)
                    return
                if new_value != service and new_value.lower() in (s.lower() for s in self.services if s != service):
                    messagebox.showerror("Erreur", "Ce service existe déjà", parent=self.top)
                    return
                # Update key in dict
                self.services[new_value] = self.services.pop(service)
                self.update_service_list()
            else:
                # Editing price
                try:
                    price_val = int(new_value)
                    if price_val < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror("Erreur", "Le prix doit être un nombre positif", parent=self.top)
                    return
                self.services[service] = price_val
                self.update_service_list()
            self._edit_entry.destroy()
            self._edit_entry = None
            self._edit_column = None
            self._edit_item = None

        def on_cancel(event=None):
            if self._edit_entry:
                self._edit_entry.destroy()
                self._edit_entry = None
                self._edit_column = None
                self._edit_item = None

        self._edit_entry.bind("<Return>", on_confirm)
        self._edit_entry.bind("<FocusOut>", on_cancel)
        self._edit_entry.bind("<Escape>", on_cancel)

    def validate_price(self, value):
        """Validate price input to allow only positive integers"""
        if value == "":
            return True
        try:
            price = int(value)
            return price >= 0
        except ValueError:
            return False

    def sort_services(self, column):
        """Sort services list by column"""
        items = [(self.services_list.set(item, column), item)
                for item in self.services_list.get_children("")]

        items.sort(reverse=getattr(self, f"sort_{column}_reverse", False))
        setattr(self, f"sort_{column}_reverse", not getattr(self, f"sort_{column}_reverse", False))

        for index, (_, item) in enumerate(items):
            self.services_list.move(item, "", index)

    def on_select(self, event):
        """Handle service selection"""
        selection = self.services_list.selection()
        if selection:
            item = self.services_list.item(selection[0])
            service, price = item["values"]
            self.service_entry.delete(0, tk.END)
            self.service_entry.insert(0, service)
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, str(price))

    def update_service_list(self):
        """Update services list with current data"""
        self.services_list.delete(*self.services_list.get_children())
        for service, price in sorted(self.services.items()):
            self.services_list.insert("", tk.END, values=(service, price))

    def add_update_service(self):
        """Add or update a service in the dialog's internal list"""
        service = self.service_entry.get().strip()
        price = self.price_entry.get().strip()

        if not service or not price:
            messagebox.showerror("Erreur", "Le service et le prix sont obligatoires", parent=self.top)
            return

        try:
            price = int(price)
            if price < 0:
                raise ValueError("Prix négatif")
        except ValueError:
            messagebox.showerror("Erreur", "Le prix doit être un nombre positif", parent=self.top)
            return

        # Check for duplicate service names (case-insensitive)
        existing_services = {s.lower(): s for s in self.services.keys()}
        if service.lower() in existing_services and existing_services[service.lower()] != service:
            messagebox.showerror("Erreur", "Ce service existe déjà", parent=self.top)
            return

        self.services[service] = price
        self.update_service_list()
        self.service_entry.delete(0, tk.END)
        self.price_entry.delete(0, tk.END)

    def delete_service(self):
        """Delete selected service from the dialog's internal list"""
        selection = self.services_list.selection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un service à supprimer", parent=self.top)
            return

        service = self.services_list.item(selection[0])["values"][0]
        if messagebox.askyesno("Confirmation",
                             f"Voulez-vous vraiment supprimer le service '{service}'?", parent=self.top):
            del self.services[service]
            self.update_service_list()
            self.service_entry.delete(0, tk.END)
            self.price_entry.delete(0, tk.END)

    def has_changes(self):
        """Check if there are unsaved changes"""
        return self.services != self.original_services

    def on_closing(self):
        """Handle dialog closing"""
        if self.has_changes():
            if messagebox.askyesno("Confirmation",
                                 "Des modifications non sauvegardées existent. "
                                 "Voulez-vous vraiment quitter sans sauvegarder?", parent=self.top):
                # Don't update self.services, just close
                self.top.destroy()
        else:
            self.top.destroy()

    def save_changes(self):
        """Closes the dialog, saving is handled by the caller."""
        # No confirmation needed here as saving is external
        self.top.destroy()


class PaymentDialog:
    def __init__(self, parent, patient, services_list):
        self.top = tk.Toplevel(parent)
        self.top.title("Paiement")
        self.top.geometry("400x600")

        self.patient = patient
        self.services_list = services_list
        self.selected_services = []
        self.total = 0
        self.service_vars = {}  # To store checkbox variables

        self.create_widgets()
        self.top.transient(parent)
        self.top.grab_set() # Make modal

    def create_widgets(self):
        # Header
        ttk.Label(self.top, text=f"Paiement pour: {self.patient}", style="Header.TLabel").pack(pady=10)

        # Services selection frame with scrollbar
        select_frame = ttk.LabelFrame(self.top, text="Sélectionner Services", padding="10")
        select_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create scrollable frame
        canvas = tk.Canvas(select_frame)
        scrollbar = ttk.Scrollbar(select_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Add checkboxes for each service
        if self.services_list:
            # Sort services by name for better organization
            sorted_services = dict(sorted(self.services_list.items()))
            for service, price in sorted_services.items():
                # Create frame for each service
                service_frame = ttk.Frame(scrollable_frame)
                service_frame.pack(fill=tk.X, pady=2)

                var = tk.BooleanVar()
                self.service_vars[service] = var

                cb = ttk.Checkbutton(service_frame,
                                   text=service,
                                   variable=var,
                                   command=self.calculate_total)
                cb.pack(side=tk.LEFT, padx=(5, 10))

                # Price label
                ttk.Label(service_frame,
                         text=f"{price} DA",
                         foreground='green').pack(side=tk.RIGHT, padx=5)
        else:
            ttk.Label(scrollable_frame,
                     text="Aucun service disponible",
                     foreground='red').pack(pady=10)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mousewheel scrolling
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        # Total frame
        self.total_frame = ttk.LabelFrame(self.top, text="Résumé", padding="10")
        self.total_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Buttons
        btn_frame = ttk.Frame(self.top, padding="10")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(btn_frame, text="Confirmer paiement",
                  command=self.confirm, style="Success.TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=self.cancel, style="Secondary.TButton").pack(side=tk.RIGHT, padx=5)

        # Initial calculation
        self.calculate_total()

    def calculate_total(self):
        for widget in self.total_frame.winfo_children():
            widget.destroy()

        self.selected_services = []
        self.total = 0

        for service, var in self.service_vars.items():
            if var.get():
                price = self.services_list[service]
                self.selected_services.append(service)
                self.total += price

                ttk.Label(self.total_frame, text=f"{service}:").pack(anchor=tk.W)
                ttk.Label(self.total_frame, text=f"{price} DA", style="Info.TLabel").pack(anchor=tk.E) # Use Info style

        ttk.Separator(self.total_frame, orient='horizontal').pack(fill='x', pady=5)
        ttk.Label(self.total_frame, text="Total:", style="Header.TLabel").pack(anchor=tk.W, pady=(5,0))
        ttk.Label(self.total_frame, text=f"{self.total} DA", style="Header.TLabel").pack(anchor=tk.E)

    def confirm(self):
        self.result = True
        self.top.destroy()

    def cancel(self):
        self.result = False
class PatientListDialog:
    # Needs reference to main app to pass user_id for actions
    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Liste des Patients")
        self.top.geometry("800x600")
        self.db = db
        self.create_widgets()
        self.load_patients()
        
    def create_widgets(self):
        # Main toolbar frame
        toolbar = ttk.Frame(self.top, padding="10")
        toolbar.pack(fill=tk.X)
        
        # Search section
        search_frame = ttk.LabelFrame(toolbar, text="Rechercher un patient", padding="5")
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search)
        
        # Action buttons (Removed "Nouveau RDV" button)
        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side=tk.RIGHT)
        
        # Create notebook for tabs (Removed Appointments tab)
        notebook = ttk.Notebook(self.top)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Patients tab
        patients_frame = ttk.Frame(notebook)
        notebook.add(patients_frame, text="Patients")
        
        self.create_patients_tab(patients_frame)
        
    def create_patients_tab(self, parent):
        # Move existing patient list code here (No changes needed here)
        list_frame = ttk.LabelFrame(parent, text="Patients", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('name', 'phone', 'visits', 'last_visit', 'total_spent') # Added 'phone' column
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Configure columns
        self.tree.heading('name', text='Nom du Patient')
        self.tree.heading('phone', text='Téléphone') # Added phone heading
        self.tree.heading('visits', text='Nombre de Visites')
        self.tree.heading('last_visit', text='Dernière Visite')
        self.tree.heading('total_spent', text='Total Payé')
        
        self.tree.column('name', width=200)
        self.tree.column('phone', width=120) # Added phone column width
        self.tree.column('visits', width=100, anchor='center')
        self.tree.column('last_visit', width=150)
        self.tree.column('total_spent', width=100, anchor='e')
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack list widgets
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double click handler removed
        # self.tree.bind('<Double-1>', self.on_double_click)
    
    # Removed create_appointments_tab, new_appointment, edit_appointment, cancel_appointment, update_appointments, on_double_click methods

    def on_search(self, event):
        """Handle search as user types."""
        query = self.search_entry.get().strip()
        if len(query) >= 2:  # Only search with 2 or more characters
            try:
                # Ensure database operations are INSIDE the 'with' block
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT 
                            p.name,
                            p.phone_number, -- Fetch phone number
                            COUNT(v.visit_id) as visit_count,
                            MAX(v.checkout_at) as last_visit,
                            SUM(v.total_paid) as total_spent
                        FROM patients p
                        LEFT JOIN visits v ON p.patient_id = v.patient_id
                        WHERE p.name LIKE ?
                        GROUP BY p.patient_id
                        ORDER BY p.name
                    """, (f"%{query}%",))
                    results = cursor.fetchall()

                    self.tree.delete(*self.tree.get_children())
                    for row in results:
                        last_visit = row['last_visit'] if row['last_visit'] else 'Jamais'
                        total_spent = f"{row['total_spent']} DA" if row['total_spent'] else '0 DA'
                        phone_number = row['phone_number'] if row['phone_number'] else '' # Handle NULL phone numbers
                        self.tree.insert("", "end", values=(
                            row['name'],
                            phone_number, # Add phone number to values
                            row['visit_count'],
                            last_visit,
                            total_spent
                        ))
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la recherche: {str(e)}")

    def load_patients(self):
        """Load initial patient list."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                # Ensure database operations are INSIDE the 'with' block
                cursor.execute("""
                    SELECT 
                        p.name,
                            p.phone_number, -- Fetch phone number
                            COUNT(v.visit_id) as visit_count,
                            MAX(v.checkout_at) as last_visit,
                            SUM(v.total_paid) as total_spent
                        FROM patients p
                        LEFT JOIN visits v ON p.patient_id = v.patient_id
                    GROUP BY p.patient_id
                    ORDER BY p.name
                """)
                results = cursor.fetchall()

                self.tree.delete(*self.tree.get_children())
                for row in results:
                    last_visit = row['last_visit'] if row['last_visit'] else 'Jamais'
                    total_spent = f"{row['total_spent']} DA" if row['total_spent'] else '0 DA'
                    phone_number = row['phone_number'] if row['phone_number'] else '' # Handle NULL phone numbers
                    self.tree.insert("", "end", values=(
                        row['name'],
                        phone_number, # Add phone number to values
                        row['visit_count'],
                        last_visit,
                        total_spent
                    ))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors du chargement des patients: {str(e)}")

class AutocompleteEntry(ttk.Entry):
    def __init__(self, parent, completevalues, **kwargs):
        super().__init__(parent, **kwargs)
        self.completevalues = completevalues
        self.var = self["textvariable"]
        if self.var == '':
            self.var = self["textvariable"] = tk.StringVar()
            
        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Return>", self.selection)
        self.listbox = None
        self.hideid = None

    def changed(self, *args):
        if self.hideid:
            self.after_cancel(self.hideid)
        self.hideid = self.after(300, self.update_list)

    def update_list(self):
        if not self.var.get():
            if self.listbox:
                self.listbox.destroy()
                self.listbox = None
            return
        
        if not self.listbox:
            self.listbox = tk.Listbox(width=self["width"], height=4)
            # Fix the bbox error by getting widget position instead
            x = self.winfo_x()
            y = self.winfo_y() + self.winfo_height()
            self.listbox.place(x=x, y=y, width=self.winfo_width())
            
        search = self.var.get().lower()
        self.listbox.delete(0, tk.END)
        for item in self.completevalues:
            if search in item.lower():
                self.listbox.insert(tk.END, item)

    def selection(self, event):
        if self.listbox and self.listbox.size() > 0:
            if self.listbox.curselection():
                self.var.set(self.listbox.get(self.listbox.curselection()))
            else:
                self.var.set(self.listbox.get(0))
            self.listbox.destroy()
            self.listbox = None
            return "break"

from sidebar import Sidebar

class LoginDialog:
    def __init__(self, parent, db):
        self.top = tk.Toplevel(parent)
        self.top.title("Connexion")
        self.db = db
        self.result = None
        
        # Center dialog
        window_width = 300
        window_height = 150
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.top, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Username
        ttk.Label(main_frame, text="Utilisateur:").grid(row=0, column=0, sticky=tk.W)
        self.username = ttk.Entry(main_frame)
        self.username.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Password
        ttk.Label(main_frame, text="Mot de passe:").grid(row=1, column=0, sticky=tk.W)
        self.password = ttk.Entry(main_frame, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Connexion", command=self.login).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        # Configure grid
        main_frame.columnconfigure(1, weight=1)
        
        # Bind enter key
        self.password.bind('<Return>', lambda e: self.login())
        
    def login(self):
        username = self.username.get().strip()
        password = self.password.get().strip()
        
        if not username or not password:
            messagebox.showerror("Erreur", "Veuillez remplir tous les champs", parent=self.top)
            return
            
        user = self.db.verify_user_credentials(username, password)
        if user:
            self.result = user
            self.top.destroy()
        else:
            messagebox.showerror("Erreur", "Identifiants incorrects", parent=self.top)
            self.password.delete(0, tk.END)
    
    def cancel(self):
        self.top.destroy()

class DoctorsWaitingRoomApp:
    def setup_styles(self):
        """Setup ttk styles for the application"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Primary.TButton",
                       background=self.colors['primary'],
                       foreground="white",
                       padding=(15, 10),
                       font=('Arial', 11, 'bold'),  # Fixed quote
                       relief="flat")

        style.configure("Secondary.TButton",
                       background=self.colors['secondary'],
                       foreground="white",
                       padding=(15, 10),
                       font=('Arial', 11),  # Fixed quote
                       relief="flat")

        style.configure("Success.TButton",
                       background=self.colors['success'],
                       foreground="white",
                       padding=(15, 10),
                       font=('Arial', 11, 'bold'),  # Fixed quote
                       relief="flat")

        style.configure("Card.TFrame",
                       background=self.colors['surface'],
                       relief="ridge",
                       borderwidth=2)

        style.configure("Header.TLabel",
                       font=('Arial', 18, 'bold'),
                       foreground=self.colors['primary'],
                       background=self.colors['surface'])

        style.configure("Info.TLabel",
                       font=('Arial', 13),
                       background=self.colors['surface'],
                       foreground=self.colors['text'])

        style.configure("TLabel",
                       background=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Arial', 11))

        style.configure("TEntry",
                       fieldbackground=self.colors['surface'],
                       foreground=self.colors['text'],
                       font=('Arial', 11))

        style.configure("StatCard.TFrame",
                       background=self.colors['surface'],
                       relief="raised",
                       borderwidth=1)
                       
        style.configure("StatIcon.TLabel",
                       background=self.colors['surface'],
                       foreground=self.colors['primary'])
                       
        style.configure("StatValue.TLabel",
                       background=self.colors['surface'],
                       foreground=self.colors['text'])
                       
        style.configure("StatTitle.TLabel",
                       background=self.colors['surface'],
                       foreground=self.colors['secondary'],
                       font=('Arial', 10))
                       
        style.configure("Dashboard.TButton",
                       padding=(15, 10),
                       font=('Arial', 11))

    def __init__(self, root):
        self.logger = logging.getLogger(__name__)
        self.root = root
        self.root.title("Cabinet Médical - Gestion")
        self.root.withdraw()  # Hide main window until login
        
        # Initialize colors first
        self.colors = {
            'primary': '#3B82F6',
            'secondary': '#64748B',
            'success': '#22C55E',
            'warning': '#F59E0B',
            'danger': '#EF4444',
            'background': '#F9FAFB',
            'surface': '#FFFFFF',
            'text': '#1E293B'
        }
        
        self.wait_colors = {
            'new': '#e3f2fd',      # Light blue
            'waiting': '#fff3e0',  # Light orange
            'long_wait': '#ffebee' # Light red
        }
        
        try:
            # Initialize database first
            self.db = DatabaseManager()
            
            # Check if any users exist, if not create default admin
            if not self.db.check_if_users_exist():
                self.db.add_user("admin", "admin123", "Doctor")
                messagebox.showinfo("Information", 
                    "Compte par défaut créé:\nUtilisateur: admin\nMot de passe: admin123")
            
            # Show login dialog
            self.show_login()
            
        except DatabaseError as e:
            self.logger.exception("Failed to initialize application")
            messagebox.showerror("Erreur Critique", 
                               "Impossible de démarrer l'application.")
            root.destroy()
            return
    
    def show_login(self):
        dialog = LoginDialog(self.root, self.db)
        self.root.wait_window(dialog.top)
        
        if dialog.result:
            self.current_user = dialog.result
            self.setup_application()
        else:
            self.root.destroy()
    
    def setup_application(self):
        """Initialize the main application after successful login"""
        self.root.deiconify()  # Show main window
        self.root.geometry("1200x800")
        self.root.configure(bg="#f5f6f7")
        self.search_results_listbox = None # Initialize search results listbox attribute
        
        # Initialize components
        self.accounting = AccountingManager()
        self.reports_manager = ReportsManager(self.db)
        self.waiting_queue = []
        self.visited_today = []
        self.with_doctor = None
        self.services = {}
        
        # Load data
        self.load_services()
        self.load_records()
        
        # Setup UI
        self.setup_styles()
        self.setup_ui()
        
        # Status bar with logged in user
        self.status_var = tk.StringVar(value=f"Connecté en tant que: {self.current_user['username']}")
        self.status_bar = ttk.Label(self.root, 
                                  textvariable=self.status_var,
                                  relief=tk.SUNKEN,
                                  padding=(10, 5))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Initial update and schedule periodic refresh (every 5 seconds)
        self.update_displays() # Run once immediately
        self.root.after(5000, self.schedule_next_update) # Start the update cycle

    def schedule_next_update(self):
        """Schedules the next call to update_displays."""
        self.update_displays()
        # Schedule the next update only if the root window still exists
        if self.root.winfo_exists():
            self.root.after(5000, self.schedule_next_update)

    def load_records(self):
        """Load today's records from database."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT p.name, v.* 
                    FROM patients p
                    JOIN visits v ON p.patient_id = v.patient_id
                    WHERE date(v.date) = date('now')
                    ORDER BY v.arrived_at ASC
                """)
                today_visits = cursor.fetchall()
                
                # Clear existing lists
                self.waiting_queue.clear()
                self.visited_today.clear()
                self.with_doctor = None
                
                for visit in today_visits:
                    name = visit["name"]
                    if not visit["called_at"]:
                        self.waiting_queue.append(name)
                    elif not visit["checkout_at"]:
                        self.with_doctor = name
                    else:
                        self.visited_today.append(name)
                        
                self.logger.info(f"Loaded {len(self.waiting_queue)} waiting patients")
                
        except Exception as e:
            self.logger.exception("Error loading records")
            messagebox.showerror("Erreur", 
                               "Impossible de charger les données du jour")

    def save_records(self):
        """Save patient records to file."""
        with open(self.records_file, 'w') as file:
            json.dump(self.records, file, indent=4)

    def load_services(self):
        """Load services from database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, price FROM services")
            services = cursor.fetchall()
            
            if not services:  # If no services exist, add defaults
                default_services = {
                    "Consultation": 500,
                    "Blood Test": 1000,
                    "X-Ray": 1500
                }
                for name, price in default_services.items():
                    cursor.execute(
                        "INSERT INTO services (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                conn.commit()
                self.services = default_services
            else:
                self.services = {row['name']: row['price'] for row in services}

    def save_services(self):
        """Save services to database by updating/inserting, avoiding deletion issues."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()

                # Get current services from DB
                cursor.execute("SELECT service_id, name, price FROM services")
                db_services = {row['name']: {'id': row['service_id'], 'price': row['price']} for row in cursor.fetchall()}

                # Get services from the dialog (self.services holds the state from the dialog)
                dialog_services = self.services

                # Identify services to add or update
                db_service_names = set(db_services.keys())
                dialog_service_names = set(dialog_services.keys())

                services_to_add = dialog_service_names - db_service_names
                services_to_update = db_service_names.intersection(dialog_service_names)
                # Note: We are intentionally NOT deleting services here to prevent FOREIGN KEY errors.
                # Services removed in the dialog will simply remain in the database but won't be shown
                # in the dialog next time unless re-added. A future improvement could be to mark them inactive.

                # Add new services
                for name in services_to_add:
                    price = dialog_services[name]
                    cursor.execute(
                        "INSERT INTO services (name, price) VALUES (?, ?)",
                        (name, price)
                    )
                    self.logger.info(f"Added service: {name} ({price} DA)")

                # Update existing services (only if price changed)
                for name in services_to_update:
                    db_price = db_services[name]['price']
                    dialog_price = dialog_services[name]
                    if db_price != dialog_price:
                        service_id = db_services[name]['id']
                        cursor.execute(
                            "UPDATE services SET price = ? WHERE service_id = ?",
                            (dialog_price, service_id)
                        )
                        self.logger.info(f"Updated service price: {name} to {dialog_price} DA")

                conn.commit()
                self.logger.info("Services saved successfully (updates/inserts only).")
                # Reload services into the app's memory after saving to reflect changes
                self.load_services()

        except (DatabaseError, sqlite3.Error) as e:
            self.logger.exception("Failed to save services")
            # Use self.root as parent for messagebox if available
            parent_window = self.root if hasattr(self, 'root') else None
            messagebox.showerror("Erreur", f"Impossible de sauvegarder les services:\n{e}", parent=parent_window)


    def show_settings(self):
        if self.current_user['role'] == 'Assistant':
            from tkinter import messagebox
            messagebox.showerror("Access Denied", "You do not have permission to access this tab.")
            return
        dialog = ServiceSettingsDialog(self.root, self.services)
        self.root.wait_window(dialog.top)
        self.services = dialog.services
        self.save_services()  # Now saves to database

    def setup_ui(self):
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Create sidebar
        self.sidebar = Sidebar(main_container, width=200)
        # Create top search bar frame
        search_bar_frame = ttk.Frame(main_container, padding=(0, 5, 0, 10)) # Add padding below
        search_bar_frame.pack(side=tk.TOP, fill=tk.X)

        self.global_search_var = tk.StringVar()
        self.global_search_entry = ttk.Entry(search_bar_frame,
                                             textvariable=self.global_search_var,
                                             width=50,
                                             font=('Arial', 11))
        self.global_search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.global_search_entry.insert(0, "Rechercher un patient...")
        self.global_search_entry.bind("<FocusIn>", self.clear_search_placeholder)
        self.global_search_entry.bind("<FocusOut>", self.restore_search_placeholder)
        self.global_search_entry.bind("<KeyRelease>", self.handle_global_search)
        self.global_search_entry.bind("<Down>", self.focus_search_results) # Navigate down to results

        # Create a frame to hold sidebar and content area below search bar
        lower_frame = ttk.Frame(main_container)
        lower_frame.pack(fill=tk.BOTH, expand=True)

        print("DEBUG: current_user role at sidebar creation:", self.current_user['role'])
        # Create sidebar (now inside lower_frame)
        self.sidebar = Sidebar(lower_frame, width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # Create main content area (now inside lower_frame)
        self.content_frame = ttk.Frame(lower_frame)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add sidebar buttons
        self.sidebar.add_button("Dashboard", self.show_dashboard)
        self.sidebar.add_button("Liste d'attente", self.show_waiting)
        self.sidebar.add_button("Patients", self.show_patient_management)
        # Removed "Rendez-vous" button

        # Add role-specific buttons
        user_role = self.current_user['role']

        if user_role == 'Admin':
            self.sidebar.add_button("User Management", self.show_user_management)
            self.sidebar.add_button("Rapports", self.show_reports)
            self.sidebar.add_button("Paramètres", self.show_settings)
        elif user_role == 'Doctor':
            # Doctor sees Rapports and Paramètres, but not User Management
            self.sidebar.add_button("Rapports", self.show_reports)
            self.sidebar.add_button("Paramètres", self.show_settings)
        elif user_role == 'Assistant':
            # Assistant sees none of these specific tabs
            pass
        else:
            # Handle potential unknown roles gracefully (optional)
            self.logger.warning(f"Unknown user role encountered: {user_role}")

        # Show initial view
        self.show_dashboard() # Show dashboard initially

    def show_user_management(self):
        import logging
        logging.getLogger("UserAction").info(f"User management accessed by role: {self.current_user['role']}")
        from user_management_dialog import UserManagementDialog
        UserManagementDialog(self.root, self.db)

    def clear_search_placeholder(self, event=None):
        if self.global_search_entry.get() == "Rechercher un patient...":
            self.global_search_entry.delete(0, tk.END)
            self.global_search_entry.config(foreground='black') # Or your default text color

    def restore_search_placeholder(self, event=None):
        if not self.global_search_entry.get():
            self.global_search_entry.insert(0, "Rechercher un patient...")
            self.global_search_entry.config(foreground='grey')
            # Use after to delay hiding, allows click on listbox
            self.root.after(200, self.hide_search_results)

    def handle_global_search(self, event=None):
        """Handle global search input."""
        query = self.global_search_var.get().strip()
        if query == "Rechercher un patient..." or len(query) < 2:
            self.hide_search_results()
            return

        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM patients WHERE name LIKE ? ORDER BY name LIMIT 10",
                    (f"%{query}%",)
                )
                results = [row['name'] for row in cursor.fetchall()]
                self.update_search_results(results)
        except Exception as e:
            self.logger.error(f"Global search error: {e}")
            self.hide_search_results()

    def update_search_results(self, results):
        """Create or update the search results listbox."""
        if not results:
            self.hide_search_results()
            return

        if not self.search_results_listbox:
            # Calculate position relative to the entry widget
            x = self.global_search_entry.winfo_rootx() - self.root.winfo_rootx()
            y = self.global_search_entry.winfo_rooty() - self.root.winfo_rooty() + self.global_search_entry.winfo_height()
            width = self.global_search_entry.winfo_width()

            self.search_results_listbox = tk.Listbox(self.root, # Place in root to overlay other widgets
                                                     width=self.global_search_entry['width'], # Match entry width
                                                     height=min(len(results), 6), # Limit height
                                                     font=('Arial', 10))
            self.search_results_listbox.place(x=x, y=y) # Use place for specific positioning
            self.search_results_listbox.bind("<<ListboxSelect>>", self.on_search_result_select)
            self.search_results_listbox.bind("<FocusOut>", self.hide_search_results) # Hide on focus out
            self.search_results_listbox.bind("<Escape>", self.hide_search_results) # Hide on Escape

        self.search_results_listbox.delete(0, tk.END)
        for item in results:
            self.search_results_listbox.insert(tk.END, item)

        # Ensure listbox is visible
        self.search_results_listbox.lift()

    def focus_search_results(self, event=None):
        """Move focus to the search results listbox if visible."""
        if self.search_results_listbox and self.search_results_listbox.winfo_viewable():
            self.search_results_listbox.focus_set()
            self.search_results_listbox.selection_set(0) # Select the first item

    def on_search_result_select(self, event=None):
        """Handle selection from the search results."""
        if not self.search_results_listbox or not self.search_results_listbox.curselection():
            return

        selected_index = self.search_results_listbox.curselection()[0]
        selected_patient = self.search_results_listbox.get(selected_index)

        self.global_search_var.set(selected_patient) # Update entry
        self.hide_search_results()
        self.global_search_entry.icursor(tk.END) # Move cursor to end

        # Open patient list and potentially pre-filter
        self.show_patient_list(search_term=selected_patient)

    def hide_search_results(self, event=None):
        """Destroy the search results listbox."""
        if self.search_results_listbox:
            self.search_results_listbox.destroy()
            self.search_results_listbox = None

    def clear_content(self):
        """Clear all widgets from content frame"""
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_content()
        dashboard = ttk.Frame(self.content_frame)
        dashboard.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Stats cards row
        stats_frame = ttk.Frame(dashboard)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        stats_frame.grid_columnconfigure((0,1,2,3), weight=1, pad=10)
        
        # Create stat cards with modern styling
        self.create_stat_card(stats_frame, 
            "Patients en attente", 
            len(self.waiting_queue),
            "⏰", 0) # Replaced unsupported emoji
        self.create_stat_card(stats_frame, 
            "Vus aujourd'hui", 
            len(self.visited_today),
            "✓", 1)
        self.create_stat_card(stats_frame, 
            "Temps moyen d'attente",
            self.calculate_avg_wait_time(),
            "⏱️", 2)
        self.create_stat_card(stats_frame,
            "Total des paiements",
            f"{self.calculate_total_payments()} DA",
            "(DA)", 3) # Replaced unsupported emoji with text
            
        # Quick actions section
        actions_frame = ttk.LabelFrame(dashboard, text="Actions rapides", padding="10")
        actions_frame.pack(fill=tk.X, pady=10)
        
        for i, (text, cmd, icon) in enumerate([
            ("Nouveau patient", self.show_patient_registration, "➕"),
            # Removed "Nouveau rendez-vous" quick action
            ("Liste d'attente", self.show_waiting, "★"),
            ("Rapports", self.show_reports, "■")
        ]):
            btn = ttk.Button(actions_frame, text=f"{icon} {text}", command=cmd, style="Dashboard.TButton")
            btn.pack(side=tk.LEFT, padx=5)

        # Today's visits with tabs
        notebook = ttk.Notebook(dashboard)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # List view tab
        list_frame = ttk.Frame(notebook)
        self.create_visits_list(list_frame)
        notebook.add(list_frame, text="Liste des visites")
        
        # Summary chart tab
        chart_frame = ttk.Frame(notebook)
        self.create_visits_chart(chart_frame)
        notebook.add(chart_frame, text="Résumé")

    def create_stat_card(self, parent, title, value, icon, column):
        """Create a modern statistics card"""
        card = ttk.Frame(parent, style="StatCard.TFrame")
        card.grid(row=0, column=column, padx=5, sticky="nsew")
        
        icon_label = ttk.Label(card, text=icon, 
                             font=('Arial', 24),
                             style="StatIcon.TLabel")
        icon_label.pack(pady=(10,0))
        
        value_label = ttk.Label(card, text=str(value),
                               font=('Arial', 20, 'bold'),
                               style="StatValue.TLabel")
        value_label.pack()
        
        title_label = ttk.Label(card, text=title,
                               style="StatTitle.TLabel")
        title_label.pack(pady=(0,10))

    def create_visits_list(self, parent):
        """Create enhanced visits list"""
        # Create treeview with better styling
        columns = ("time", "patient", "services", "duration", "payment", "status")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=12)
        
        # Configure columns with better formatting
        tree.heading("time", text="Heure")
        tree.heading("patient", text="Patient")
        tree.heading("services", text="Services")
        tree.heading("duration", text="Durée")
        tree.heading("payment", text="Paiement")
        tree.heading("status", text="Statut")
        
        tree.column("time", width=80)
        tree.column("patient", width=200)
        tree.column("services", width=250)
        tree.column("duration", width=80)
        tree.column("payment", width=100, anchor="e")
        tree.column("status", width=100)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Load and display data
        self.load_todays_visits(tree)

    def create_visits_chart(self, parent):
        """Create summary chart for today's visits"""
        try:
            import matplotlib.pyplot as plt
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            
            # Create figure and axis
            fig = Figure(figsize=(8, 4), dpi=100)
            ax = fig.add_subplot(111)
            
            # Get hourly visit data
            hours, counts = self.get_hourly_visits()
            
            # Create bar chart
            ax.bar(hours, counts, color=self.colors['primary'])
            ax.set_title("Visites par heure")
            ax.set_xlabel("Heure")
            ax.set_ylabel("Nombre de visites")
            
            # Embed in tkinter
            canvas = FigureCanvasTkAgg(fig, parent)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
        except ImportError:
            ttk.Label(parent, text="matplotlib requis pour afficher le graphique").pack()

    def show_waiting(self):
        """Show waiting list view"""
        self.clear_content()
        self.create_waiting_section(self.content_frame)
        # Force immediate update after creating waiting section
        self.root.after(10, self.update_displays)        

    def show_patient_management(self):
        self.clear_content()
        # Open patient list dialog in content frame instead of new window
        self.create_patient_section(self.content_frame)

    # Removed show_appointments method

    def show_reports(self):
        """Show the new reports tab"""
        if self.current_user['role'] == 'Assistant':
            from tkinter import messagebox
            messagebox.showerror("Access Denied", "You do not have permission to access this tab.")
            return
        self.clear_content()
        # Instantiate the new ReportsTab class
        ReportsTab(self.content_frame, self.reports_manager)

    def show_patient_registration(self):
        self.clear_content()
        reg_frame = ttk.Frame(self.content_frame)
        reg_frame.pack(fill=tk.BOTH, expand=True)
        self.create_patient_section(reg_frame)

    def update_displays(self):
        """Update all displays."""
        try:
            # Reload records to ensure data is fresh
            self.load_records()
            
            # Update current patient display with consultation time
            if hasattr(self, 'current_patient_label') and self.current_patient_label.winfo_exists():
                if self.with_doctor:
                    # Get consultation start time
                    with self.db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT v.called_at
                            FROM visits v
                            JOIN patients p ON v.patient_id = p.patient_id
                            WHERE p.name = ? AND v.checkout_at IS NULL
                            ORDER BY v.called_at DESC LIMIT 1
                        """, (self.with_doctor,))
                        result = cursor.fetchone()
                        if result and result['called_at']:
                            start_time = datetime.strptime(result['called_at'], "%Y-%m-%d %H:%M:%S")
                            elapsed = datetime.now() - start_time
                            minutes = int(elapsed.total_seconds() / 60)
                            self.consultation_time_label.config(
                                text=f"Durée: {minutes} min",
                                foreground=self.colors['success'] if minutes < 15 else self.colors['warning']
                            )
                    self.current_patient_label.config(
                        text=f"Patient Actuel: {self.with_doctor}",
                        foreground=self.colors['success']
                    )
                else:
                    self.current_patient_label.config(
                        text="Aucun patient",
                        foreground=self.colors['secondary']
                    )
                    self.consultation_time_label.config(
                        text="Durée: 0 min",
                        foreground=self.colors['secondary']
                    )
            
            # Update waiting list
            if hasattr(self, 'waiting_list') and self.waiting_list.winfo_exists():
                self.waiting_list.delete(0, tk.END)
                current_time = datetime.now()
                arrival_times = {} # Dictionary to store arrival times

                # Fetch arrival times for all waiting patients in one query
                if self.waiting_queue: # Only query if there are patients waiting
                    try:
                        with self.db.get_connection() as conn:
                            cursor = conn.cursor()
                            # Use placeholders for the list of names
                            placeholders = ','.join('?' * len(self.waiting_queue))
                            query = f"""
                                SELECT p.name, MAX(v.arrived_at) as last_arrival
                                FROM visits v
                                JOIN patients p ON v.patient_id = p.patient_id
                                WHERE p.name IN ({placeholders})
                                AND v.called_at IS NULL
                                AND date(v.date) = date('now') -- Ensure it's today's uncalled visit
                                GROUP BY p.name
                            """
                            cursor.execute(query, self.waiting_queue)
                            results = cursor.fetchall()
                            # Store arrival times keyed by patient name
                            arrival_times = {row['name']: row['last_arrival'] for row in results}
                    except Exception as e:
                        self.logger.error(f"Error fetching arrival times for waiting list: {e}")
                        # Handle error gracefully, maybe show basic list without times

                # Now iterate and use the fetched times
                for i, patient in enumerate(self.waiting_queue):
                    wait_time = 0
                    arrival_time_str = ""
                    arrival_str = arrival_times.get(patient) # Get time from dictionary

                    if arrival_str:
                        try:
                            # Ensure arrival_str is not None before parsing
                            arrival = datetime.strptime(arrival_str, "%Y-%m-%d %H:%M:%S")
                            wait_time = (current_time - arrival).total_seconds() / 60
                            arrival_time_str = arrival.strftime("%H:%M")
                        except (ValueError, TypeError) as e: # Catch TypeError if arrival_str is None
                            self.logger.warning(f"Invalid arrival time format or value for {patient}: {arrival_str} ({e})")
                            arrival_time_str = "N/A" # Indicate missing time

                    # Include arrival time in the display text
                    item_text = f"{i+1}. {patient} [{arrival_time_str}]"
                    if wait_time > 0:
                        item_text += f" (⏱️ {int(wait_time)}min)"
                    self.waiting_list.insert(tk.END, item_text)

                    # Color coding remains the same
                    if wait_time == 0:
                        self.waiting_list.itemconfig(i, {'bg': self.wait_colors['new']})
                    elif wait_time > 30:
                        self.waiting_list.itemconfig(i, {'bg': self.wait_colors['long_wait']})
                    else:
                        self.waiting_list.itemconfig(i, {'bg': self.wait_colors['waiting']})

            # Update visited list
            if hasattr(self, 'visited_list') and self.visited_list.winfo_exists():
                self.visited_list.delete(0, tk.END)
                for i, patient in enumerate(self.visited_today):
                    self.visited_list.insert(tk.END, f"✓ {patient}")

            # Update counts
            if hasattr(self, 'waiting_count') and self.waiting_count.winfo_exists():
                self.waiting_count.config(text=str(len(self.waiting_queue)))
            if hasattr(self, 'visited_count') and self.visited_count.winfo_exists():
                self.visited_count.config(text=str(len(self.visited_today)))

            # Update visited text display        
            if hasattr(self, 'visited_text') and self.visited_text.winfo_exists():
                self.update_visited_text()

            # Removed update for main_appointments_tree
        except tk.TclError as e:
            self.logger.debug(f"Widget update skipped - widget might have been destroyed: {str(e)}")
        except Exception as e:
            self.logger.exception("Error in update_displays")

    # Removed update_all_appointments method

    def show_patient_list(self):
        """Show patient list dialog and update displays safely"""
        try:
            dialog = PatientListDialog(self.root, self.db)
            self.root.wait_window(dialog.top)
            # Only update if window wasn't cancelled
            if dialog.top.winfo_exists():
                # Removed call to update_all_appointments
                self.root.after(100, self.update_displays) # Schedule basic update
        except Exception as e:
            self.logger.exception("Error showing patient list")
            messagebox.showerror("Erreur", 
                               "Une erreur est survenue lors de l'affichage de la liste des patients")

    # Removed create_appointments_panel, create_appointment_tree, update_appointment_displays methods

    def create_visited_panel(self, parent):
        # Move existing visited patients panel code here (No changes needed here)
        visited_card = ttk.Frame(parent, style="Card.TFrame")
        visited_card.pack(fill=tk.BOTH, expand=True)
        
        # Header with count
        header_frame = ttk.Frame(visited_card)
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(header_frame, 
                 text="Patients Vus Aujourd'hui", 
                 style="Header.TLabel").pack(side=tk.LEFT)
        self.visited_count = ttk.Label(header_frame, text="0", style="Info.TLabel")
        self.visited_count.pack(side=tk.RIGHT)
        
        # Create notebook for different views
        notebook = ttk.Notebook(visited_card)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # List view tab
        list_frame = ttk.Frame(notebook)
        self.visited_list = tk.Listbox(list_frame, 
                                     font=('Arial', 12),
                                     selectmode=tk.SINGLE,
                                     activestyle='none',
                                     bg=self.colors['surface'],
                                     fg=self.colors['text'])
        
        list_scroll = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                  command=self.visited_list.yview)
        self.visited_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.visited_list.config(yscrollcommand=list_scroll.set)
        
        # Detailed view tab
        details_frame = ttk.Frame(notebook)
        self.visited_text = scrolledtext.ScrolledText(details_frame, 
                                                    wrap=tk.WORD, 
                                                    height=10)
        self.visited_text.pack(fill=tk.BOTH, expand=True)
        
        # Add tabs to notebook
        notebook.add(list_frame, text="Liste")
        notebook.add(details_frame, text="Détails")
        
        # Initialize displays
        self.update_visited_text()
        
    def update_visited_text(self):
        """Update the visited patients text area with today's visits."""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT 
                        p.name,
                        v.checkout_at,
                        v.total_paid,
                        GROUP_CONCAT(s.name) as services
                    FROM visits v
                    JOIN patients p ON v.patient_id = p.patient_id
                    LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                    LEFT JOIN services s ON vs.service_id = s.service_id
                    WHERE date(v.checkout_at) = date('now')
                    GROUP BY v.visit_id
                    ORDER BY v.checkout_at DESC
                """)
                visits = cursor.fetchall()
                
                self.visited_text.config(state=tk.NORMAL)
                self.visited_text.delete(1.0, tk.END)
                
                headers = "Heure\tPatient\tServices\tPaiement\n"
                self.visited_text.insert(tk.END, headers)
                self.visited_text.insert(tk.END, "-" * 60 + "\n")
                
                for visit in visits:
                    checkout_time = datetime.strptime(visit['checkout_at'], "%Y-%m-%d %H:%M:%S")
                    services = visit['services'] if visit['services'] else "Aucun"
                    line = f"{checkout_time.strftime('%H:%M')}\t{visit['name']}\t{services}\t{visit['total_paid']} DA\n"
                    self.visited_text.insert(tk.END, line)
                    
                self.visited_text.config(state=tk.DISABLED)
        except Exception as e:
            self.logger.exception("Error updating visited patients list")
            messagebox.showerror("Erreur", "Impossible de mettre à jour la liste des patients vus")

    def get_existing_patients(self):
        """Get list of all patient names from database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM patients ORDER BY name")
            return [row['name'] for row in cursor.fetchall()]

    def create_patient_section(self, parent):
        # Actions card
        actions_card = ttk.Frame(parent, style="Card.TFrame")
        actions_card.pack(fill=tk.X, pady=10)
        
        ttk.Label(actions_card, text="Gérer les Patients", style="Header.TLabel").pack(pady=10)
        
        buttons_frame = ttk.Frame(actions_card)
        buttons_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(buttons_frame, 
                  text="Liste des Patients",
                  command=self.show_patient_list,
                  style="Primary.TButton").pack(fill=tk.X, pady=5)

    def create_waiting_section(self, parent):
        # Create main container for waiting section
        waiting_container = ttk.Frame(parent)
        waiting_container.pack(fill=tk.BOTH, expand=True)
        
        # Current patient card at top
        current_card = ttk.Frame(waiting_container, style="Card.TFrame")
        current_card.pack(fill=tk.X, pady=(0, 20))
        
        ttk.Label(current_card, text="Patient Actuel", style="Header.TLabel").pack(pady=10)
        
        self.current_patient_label = ttk.Label(current_card,
                                             text="Aucun patient",
                                             font=('Arial', 14, 'bold'),
                                             foreground=self.colors['primary'])
        self.current_patient_label.pack(pady=5)
        
        self.consultation_time_label = ttk.Label(current_card,
                                               text="Durée: 0 min",
                                               font=('Arial', 12),
                                               foreground=self.colors['secondary'])
        self.consultation_time_label.pack(pady=5)
        
        ttk.Button(current_card,
                  text="Traiter Paiement",
                  style="Success.TButton",
                  command=self.process_payment).pack(pady=10)
        
        # Waiting list section
        waiting_card = ttk.Frame(waiting_container, style="Card.TFrame")
        waiting_card.pack(fill=tk.BOTH, expand=True)
        
        # Header with count
        header_frame = ttk.Frame(waiting_card)
        header_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Label(header_frame, text="Liste d'Attente", style="Header.TLabel").pack(side=tk.LEFT)
        self.waiting_count = ttk.Label(header_frame, text="0", style="Info.TLabel")
        self.waiting_count.pack(side=tk.RIGHT)
        
        # Waiting list with scrollbar
        list_frame = ttk.Frame(waiting_card)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.waiting_list = tk.Listbox(list_frame, 
                                     font=('Arial', 12),
                                     selectmode=tk.SINGLE,
                                     activestyle='none',
                                     bg=self.colors['surface'],
                                     fg=self.colors['text'])
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                 command=self.waiting_list.yview)
        self.waiting_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.waiting_list.config(yscrollcommand=scrollbar.set)
        
        # Control buttons
        btn_frame = ttk.Frame(waiting_card)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Add new patient button
        ttk.Button(btn_frame,
                  text="➕ Nouveau Patient",
                  style="Primary.TButton",
                  command=self.add_new_patient_to_waiting).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame,
                  text="✆ Appeler le Patient",
                  style="Primary.TButton",
                  command=self.call_selected_patient).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame,
                  text="❌ Retirer Patient",
                  style="Secondary.TButton",
                  command=self.remove_from_waiting).pack(side=tk.LEFT, padx=5)

    def add_new_patient_to_waiting(self):
        """Add new patient directly to waiting list"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Ajouter à la Liste d'Attente")
        dialog.geometry("400x150")
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons for new or existing patient
        ttk.Button(frame, text="Nouveau Patient", 
                  command=lambda: self.show_new_patient_dialog(dialog),
                  style="Primary.TButton").pack(fill=tk.X, pady=5)
        ttk.Button(frame, text="Patient Existant",
                  command=lambda: self.show_patient_selection(dialog),
                  style="Secondary.TButton").pack(fill=tk.X, pady=5)
              
        ttk.Button(frame, text="Annuler", 
                  command=dialog.destroy).pack(fill=tk.X, pady=5)

    def show_new_patient_dialog(self, parent_dialog):
        """Show dialog for new patient entry"""
        parent_dialog.destroy()
        dialog = tk.Toplevel(self.root)
        dialog.title("Nouveau Patient")
        dialog.geometry("400x200") # Increased height for phone number
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Name Entry
        ttk.Label(frame, text="Nom du patient:").pack(anchor=tk.W)
        name_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        name_entry.pack(fill=tk.X, pady=(0, 10))
        name_entry.focus()
        
        # Phone Number Entry (Optional)
        ttk.Label(frame, text="Numéro de téléphone (Optionnel):").pack(anchor=tk.W)
        phone_entry = ttk.Entry(frame, width=30, font=('Arial', 12))
        phone_entry.pack(fill=tk.X, pady=(0, 10))
        
        def submit():
            name = name_entry.get().strip()
            phone_number = phone_entry.get().strip() or None # Get phone number, None if empty
            if name:
                # Pass phone number to register_patient_direct
                self.register_patient_direct(name, phone_number=phone_number) 
                dialog.destroy()
                
        name_entry.bind('<Return>', lambda e: phone_entry.focus()) # Move focus on Enter
        phone_entry.bind('<Return>', lambda e: submit()) # Submit on Enter from phone field
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(btn_frame, text="Ajouter", style="Primary.TButton",
                  command=submit).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Annuler",
                  command=dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def show_patient_selection(self, parent_dialog):
        """Show dialog for existing patient selection"""
        parent_dialog.destroy()
        dialog = PatientSelectionDialog(self.root, self.db)
        self.root.wait_window(dialog.top)
        if dialog.selected_patient:
            self.register_patient_direct(dialog.selected_patient) # Phone number is not available here, will be None by default

    def register_patient_direct(self, name, phone_number=None): # Added phone_number parameter
        """Register patient and add to waiting list directly"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id FROM patients WHERE name = ?", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    patient_id = existing['patient_id']
                    # Note: We might want to update the phone number for existing patients here,
                    # but for now, we only add it for new patients.
                else:
                    # Pass phone_number to db.add_patient
                    patient_id = self.db.add_patient(name, phone_number=phone_number) 
                
                # Pass the current user's ID from the login
                self.db.add_visit(patient_id, self.current_user['user_id'])
                conn.commit()
                
                self.waiting_queue.append(name)
                self.status_var.set(f"Patient {name} inscrit et ajouté à la liste d'attente.")
                self.update_displays()
                self.logger.info(f"Successfully added new patient to waiting list: {name}")
                
        except DatabaseError as e:
            self.logger.exception(f"Failed to register patient: {name}")
            messagebox.showerror("Erreur", 
                               "Impossible d'enregistrer le patient. "
                               "Veuillez réessayer plus tard.")

    def call_selected_patient(self):
        """Call selected patient from waiting list"""
        selection = self.waiting_list.curselection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient à appeler.")
            return

        if self.with_doctor:
            messagebox.showinfo("Information", 
                              f"Le médecin est actuellement avec {self.with_doctor}.")
            return

        idx = selection[0]
        patient = self.waiting_queue[idx]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            # Update visit status in database - now including user_id
            if self.db.update_patient_call(patient, now, self.current_user['user_id']):
                # Remove from waiting queue
                del self.waiting_queue[idx]
                self.with_doctor = patient
                self.status_var.set(f"Patient {patient} est maintenant avec le médecin.")
                self.update_displays()
            else:
                messagebox.showerror("Erreur", "Impossible de trouver la visite du patient")
                
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur de base de données: {e}")

    def register_patient(self, phone_number=None): # Added phone_number parameter (though not used by its original UI)
        # This method might be less used now, but updating for consistency
        name = self.name_entry.get().strip() 
        if not name:
            self.logger.warning("Attempted to register patient with empty name")
            messagebox.showerror("Erreur", "Le nom du patient est obligatoire.")
            return
        try:
            with self.db.get_connection() as conn:
                # Check if patient already exists
                cursor = conn.cursor()
                cursor.execute("SELECT patient_id FROM patients WHERE name = ?", (name,))
                existing = cursor.fetchone()
                
                if existing:
                    patient_id = existing['patient_id']
                else:
                    # Pass phone_number (will likely be None here)
                    patient_id = self.db.add_patient(name, phone_number=phone_number) 
                
                # Pass the current user's ID here as well
                self.db.add_visit(patient_id, self.current_user['user_id'])
                conn.commit()
                
                self.waiting_queue.append(name)
                self.status_var.set(f"Patient {name} inscrit et ajouté à la liste d'attente.")
                self.name_entry.delete(0, tk.END)
                self.update_displays()
                self.logger.info(f"Successfully registered patient: {name}")
        except DatabaseError as e:
            self.logger.exception(f"Failed to register patient: {name}")
            messagebox.showerror("Erreur", 
                               "Impossible d'enregistrer le patient. "
                               "Veuillez réessayer plus tard.")

    def get_patient_visits(self, patient_name):
        """Get all visits for a patient from database."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, GROUP_CONCAT(s.name) as service_names
                FROM visits v
                JOIN patients p ON v.patient_id = p.patient_id
                LEFT JOIN visit_services vs ON v.visit_id = vs.visit_id
                LEFT JOIN services s ON vs.service_id = s.service_id
                WHERE p.name = ?
                GROUP BY v.visit_id
                ORDER BY v.date DESC
            """, (patient_name,))
            return cursor.fetchall()

    def next_patient(self):
        if not self.waiting_queue:
            messagebox.showinfo("Information", "Aucun patient dans la liste d'attente.")
            return

        if self.with_doctor:
            messagebox.showinfo("Information", 
                              f"Le médecin est actuellement avec {self.with_doctor}.")
            return

        patient = self.waiting_queue.pop(0)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.process_payment()  # Simplified workflow - direct to payment
        try:
            # Update visit status in database - now including user_id
            if self.db.update_patient_call(patient, now, self.current_user['user_id']):
                self.with_doctor = patient
                self.status_var.set(f"Patient {patient} est maintenant avec le médecin.")
                self.update_displays()
            else:
                messagebox.showerror("Erreur", "Impossible de trouver la visite du patient")
                self.waiting_queue.insert(0, patient)  # Put patient back in queue
                
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur de base de données: {e}")
            self.waiting_queue.insert(0, patient)  # Put patient back in queue
            
    def checkout_patient(self):
        if not self.with_doctor:
            messagebox.showinfo("Information", "Aucun patient n'est avec le médecin.")
            return

        patient = self.with_doctor
        self.process_payment()  # Simplified workflow - direct to payment services

    def process_payment(self):
        if not self.with_doctor:
            messagebox.showinfo("Information", "Aucun patient n'est avec le médecin.")
            return

        patient = self.with_doctor
        
        try:
            # Get current visit from database
            current_visit = self.db.get_current_visit(patient)
            if not current_visit:
                messagebox.showerror("Erreur", "Impossible de trouver les détails de la visite actuelle")
                return
            
            # Show payment dialog with services list
            dialog = PaymentDialog(self.root, patient, self.services)
            self.root.wait_window(dialog.top)
            
            if hasattr(dialog, 'result') and dialog.result:
                # Get service IDs for selected services
                service_ids = [ 
                    self.db.get_service_id(service_name)
                    for service_name in dialog.selected_services
                ]
                
                # Update visit with checkout information
                self.db.update_visit_checkout(
                    current_visit['visit_id'],
                    dialog.total,
                    service_ids
                )
                
                # Add transaction to accounting
                self.accounting.add_transaction(
                    patient,
                    dialog.selected_services,
                    dialog.total
                )
                
                self.visited_today.append(patient)
                self.with_doctor = None
                self.status_var.set(
                    f"✓ Patient {patient} - Consultation terminée. "
                    f"Paiement: {dialog.total} DA"
                )
                self.update_displays()
        except sqlite3.Error as e:
            messagebox.showerror("Erreur", f"Erreur de base de données: {e}")

    def remove_from_waiting(self):
        """Remove selected patient from waiting list."""
        selection = self.waiting_list.curselection()
        if not selection:
            messagebox.showinfo("Information", "Veuillez sélectionner un patient à retirer.")
            return
        
        idx = selection[0]
        patient = self.waiting_queue[idx]
        
        if messagebox.askyesno("Confirmation", 
                             f"Voulez-vous vraiment retirer {patient} de la liste d'attente?"):
            try:
                # Remove from queue
                del self.waiting_queue[idx]
                
                # Update database to mark visit as cancelled
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # First get the visit_id                        
                    cursor.execute("""
                        SELECT v.visit_id 
                        FROM visits v
                        JOIN patients p ON v.patient_id = p.patient_id
                        WHERE p.name = ?
                        AND date(v.date) = date('now')
                        AND v.called_at IS NULL
                        ORDER BY v.arrived_at DESC LIMIT 1
                    """, (patient,))
                    result = cursor.fetchone()
                    
                    if result:
                        # Then update the visit
                        cursor.execute("""
                            UPDATE visits
                            SET checkout_at = ?,
                                called_at = ?,
                                total_paid = 0
                            WHERE visit_id = ?
                        """, (now, now, result['visit_id']))
                        conn.commit()
                self.status_var.set(f"Patient {patient} retiré de la liste d'attente")
                self.update_displays()
                self.logger.info(f"Removed patient from waiting list: {patient}")
            except Exception as e:
                self.logger.exception(f"Error removing patient from waiting list: {patient}")
                messagebox.showerror("Erreur",
                                   "Une erreur est survenue lors du retrait du patient.")

    def show_patient_list(self, search_term=None):
        """Show patient list dialog, optionally with a pre-filled search term."""
        dialog = PatientListDialog(self.root, self.db)

        # If a search term is provided, populate the dialog's search entry
        if search_term and hasattr(dialog, 'search_entry'):
            dialog.search_entry.insert(0, search_term)
            # Trigger the search function within the dialog
            dialog.on_search(None) # Pass None as event object

        self.root.wait_window(dialog.top)
        # Removed call to update_all_appointments
        self.update_displays()

    # Removed show_financial_report method as it's replaced by show_reports

    # Removed update_all_appointments method
    # Removed show_appointment_dialog method

    def calculate_avg_wait_time(self):
        """Calculate average waiting time for today's patients"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT AVG((strftime('%s', called_at) - strftime('%s', arrived_at)) / 60.0) as avg_wait
                    FROM visits 
                    WHERE date(arrived_at) = date('now')
                    AND called_at IS NOT NULL
                """)
                result = cursor.fetchone()
                avg_wait = result['avg_wait'] if result['avg_wait'] else 0
                return f"{int(avg_wait)} min"
        except Exception:
            return "N/A"



    def calculate_total_payments(self):
        """Calculate total payments for today"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT SUM(total_paid) as total
                    FROM visits 
                    WHERE date(checkout_at) = date('now')
                """)
                result = cursor.fetchone()
                return result['total'] if result['total'] else 0
        except Exception:
            return 0

    def get_hourly_visits(self):
        """Get hourly visit data for chart"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT CAST(strftime('%H', arrived_at) AS INTEGER) as hour,
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
                    hour = row['hour']
                    if 8 <= hour <= 18:  # Only count hours within business hours
                        counts[hour - 8] = row['count']  # Offset by 8 to match array index
                        
                return hours, counts
        except Exception as e:
            self.logger.warning(f"Error getting hourly visits: {str(e)}")
            return [], []

    def load_todays_visits(self, tree):
        """Load today's visits into treeview"""
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
                    WHERE date(v.arrived_at) = date('now')
                    GROUP BY v.visit_id
                    ORDER BY v.arrived_at DESC
                """)
                
                tree.delete(*tree.get_children())
                for row in cursor.fetchall():
                    arrival = datetime.strptime(row['arrived_at'], "%Y-%m-%d %H:%M:%S")
                    duration = f"{int(row['duration'])} min" if row['duration'] else "N/A"
                    services = row['services'] if row['services'] else "Aucun"
                    payment = f"{row['total_paid']} DA" if row['total_paid'] else "N/A"
                    
                    tree.insert("", "end", values=(
                        arrival.strftime("%H:%M"),
                        row['name'],
                        services,
                        duration,
                        payment,
                        row['status']
                    ))
        except Exception as e:
            self.logger.exception("Error loading today's visits")

if __name__ == "__main__":
    logger = setup_logging()
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
