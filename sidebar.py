import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
from tkinter import ttk

class Sidebar(ttk.Frame):
    def __init__(self, parent, width=200, **kwargs):
        super().__init__(parent, **kwargs)
        self.width = width
        self.buttons = {}
        self.selected = None
        self.setup_style()

        # Add logo at the top
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            try:
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((120, 120), Image.ANTIALIAS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = tk.Label(self, image=self.logo_photo, bg="white")
                logo_label.pack(pady=(10, 20))
            except Exception as e:
                print(f"Failed to load logo: {e}")
        else:
            logo_label = tk.Label(self, text="App", font=("Arial", 24, "bold"))
            logo_label.pack(pady=(10, 20))
        
    def setup_style(self):
        style = ttk.Style()
        style.configure(
            "Sidebar.TButton",
            padding=15,
            width=20,
            anchor="w"  # Left-align text
        )
        style.configure(
            "Sidebar.Selected.TButton",
            background="#3B82F6",
            foreground="white"
        )
        
    def add_button(self, text, command):
        btn = ttk.Button(
            self,
            text=text,
            style="Sidebar.TButton",
            command=lambda: self._handle_click(text, command)
        )
        btn.pack(fill=tk.X, padx=5, pady=2)
        self.buttons[text] = btn
        
    def _handle_click(self, text, command):
        # Deselect previous button
        if self.selected:
            self.buttons[self.selected].configure(style="Sidebar.TButton")
            
        # Select new button
        self.selected = text
        self.buttons[text].configure(style="Sidebar.Selected.TButton")
        
        # Execute command
        command()
