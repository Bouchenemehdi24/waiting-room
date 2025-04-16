"""
Example integration for adding a 'Rapport Financement' tab to the sidebar,
which opens the FinancialReport dialog from accounting.py.

Assumptions:
- You have a Sidebar instance called 'sidebar'.
- You have access to the main Tkinter root window or parent frame.
- You have access to transactions and reports_manager objects.

Insert this code where you set up your sidebar and main UI.
"""

import tkinter as tk
from sidebar import Sidebar
from accounting import FinancialReport

def open_financing_report():
    # Replace 'root', 'transactions', and 'reports_manager' with your actual objects
    FinancialReport(root, transactions, reports_manager)

root = tk.Tk()
sidebar = Sidebar(root)
sidebar.pack(side=tk.LEFT, fill=tk.Y)

# Add the new "Rapport Financement" button
sidebar.add_button("Rapport Financement", open_financing_report)

# ... rest of your main UI setup ...