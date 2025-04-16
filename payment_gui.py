import tkinter as tk
from tkinter import ttk

class PaymentGUI:
    def __init__(self, root):
        self.window = tk.Toplevel(root)
        self.window.title("Payment Interface")
        self.window.geometry("800x600")

        # Create main container
        main_frame = ttk.Frame(self.window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

# Removed appointment type selection frame ("Type de Rendez-vous")

        # Add radio buttons for appointment type
# Removed appointment type selection, pricing, and related UI

        # Create scrollable transaction area
        transaction_frame = ttk.LabelFrame(main_frame, text="Détails de Transaction")
        transaction_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Add scrollbar and canvas
        canvas = tk.Canvas(transaction_frame)
        scrollbar = ttk.Scrollbar(transaction_frame, orient=tk.VERTICAL, command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Button frame at the bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # Payment buttons
        self.cash_btn = ttk.Button(button_frame, text="Paiement en Espèces", width=20)
        self.cash_btn.pack(side=tk.LEFT, padx=5)

        self.card_btn = ttk.Button(button_frame, text="Paiement par Carte", width=20)
        self.card_btn.pack(side=tk.LEFT, padx=5)

        self.cancel_btn = ttk.Button(button_frame, text="Annuler", width=15)
        self.cancel_btn.pack(side=tk.RIGHT, padx=5)

        # Pack scrollbar and canvas
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Initialize price display
        self.update_price()

# Removed appointment-related methods: update_price, get_appointment_type, get_current_price
    def add_transaction_item(self, item_text):
        ttk.Label(self.scrollable_frame, text=item_text).pack(pady=2, padx=5, anchor="w")

    def set_button_commands(self, cash_cmd, card_cmd, cancel_cmd):
        self.cash_btn.config(command=cash_cmd)
        self.card_btn.config(command=card_cmd)
        self.cancel_btn.config(command=cancel_cmd)
