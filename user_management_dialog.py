import tkinter as tk
from tkinter import ttk, messagebox
import hashlib

class UserManagementDialog:
    def __init__(self, parent, db):
        self.db = db
        self.top = tk.Toplevel(parent)
        self.top.title("Add New User")
        self.top.geometry("350x250")
        self.top.resizable(False, False)

        ttk.Label(self.top, text="Username:").pack(pady=(15, 0))
        self.username_entry = ttk.Entry(self.top)
        self.username_entry.pack(fill=tk.X, padx=20)

        ttk.Label(self.top, text="Password:").pack(pady=(10, 0))
        self.password_entry = ttk.Entry(self.top, show="*")
        self.password_entry.pack(fill=tk.X, padx=20)

        ttk.Label(self.top, text="Role:").pack(pady=(10, 0))
        self.role_var = tk.StringVar()
        self.role_combo = ttk.Combobox(self.top, textvariable=self.role_var, state="readonly")
        # Updated roles to match the database schema
        self.role_combo["values"] = ("Admin", "Doctor", "Assistant") 
        self.role_combo.current(0) # Default to Admin
        self.role_combo.pack(fill=tk.X, padx=20)

        self.add_btn = ttk.Button(self.top, text="Add User", command=self.add_user)
        self.add_btn.pack(pady=20)

    def add_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()

        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields.", parent=self.top)
            return

        try:
            self.db.add_user(username, password, role)
            messagebox.showinfo("Success", f"User '{username}' added as {role}.", parent=self.top)
            self.top.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self.top)
