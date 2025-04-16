import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import logging

class ModernUITheme:
    """
    A theme manager class that provides consistent modern styling for the application.
    This class handles styling for both Tkinter widgets and matplotlib charts.
    """
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Modern color palette
        self.primary_color = '#3498db'  # Blue
        self.secondary_color = '#2ecc71'  # Green
        self.accent_color = '#e74c3c'  # Red
        self.background_color = '#f9f9f9'  # Light gray
        self.text_color = '#2c3e50'  # Dark blue/gray
        
        # Chart colors
        self.chart_colors = [
            self.primary_color,
            self.secondary_color,
            self.accent_color,
            '#f1c40f',  # Yellow
            '#9b59b6',  # Purple
            '#1abc9c',  # Turquoise
            '#34495e'   # Dark gray
        ]
        
        # Font configurations
        self.title_font = ("Helvetica", 14, "bold")
        self.header_font = ("Helvetica", 12, "bold")
        self.text_font = ("Helvetica", 10)
        self.small_font = ("Helvetica", 9)
        
    def apply_to_window(self, window):
        """
        Apply the theme to a tkinter window and its children
        """
        try:
            # Configure the window
            window.configure(background=self.background_color)
            
            # Configure ttk styles
            style = ttk.Style(window)
            
            # Configure common elements
            style.configure('TFrame', background=self.background_color)
            style.configure('TLabel', background=self.background_color, foreground=self.text_color)
            style.configure('TButton', background=self.primary_color, foreground='white')
            style.map('TButton', 
                     background=[('active', self.secondary_color), ('disabled', '#cccccc')],
                     foreground=[('disabled', '#999999')])
            
            # Configure entry fields
            style.configure('TEntry', fieldbackground='white', foreground=self.text_color)
            
            # Configure comboboxes
            style.configure('TCombobox', fieldbackground='white', background=self.background_color)
            
            # Configure notebooks (tabs)
            style.configure('TNotebook', background=self.background_color)
            style.configure('TNotebook.Tab', background=self.background_color, 
                          foreground=self.text_color, padding=[10, 2])
            style.map('TNotebook.Tab',
                     background=[('selected', self.primary_color)],
                     foreground=[('selected', 'white')])
            
            # Configure treeviews (tables)
            style.configure('Treeview', 
                          background='white',
                          foreground=self.text_color,
                          rowheight=25,
                          fieldbackground='white')
            style.map('Treeview',
                     background=[('selected', self.primary_color)],
                     foreground=[('selected', 'white')])
            style.configure('Treeview.Heading', 
                          background=self.background_color,
                          foreground=self.text_color,
                          font=self.header_font)
            
            self.logger.info("Applied modern UI theme to window")
            return True
        except Exception as e:
            self.logger.error(f"Error applying theme: {str(e)}")
            return False
    
    def configure_matplotlib(self):
        """
        Configure matplotlib to use the theme's styling
        """
        try:
            # Use a clean, modern style
            plt.style.use('seaborn-v0_8-whitegrid')
            
            # Set font family
            plt.rcParams['font.family'] = 'DejaVu Sans'
            
            # Set colors
            plt.rcParams['axes.prop_cycle'] = plt.cycler(color=self.chart_colors)
            
            # Set font sizes
            plt.rcParams['font.size'] = 10
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['figure.titlesize'] = 16
            plt.rcParams['axes.labelsize'] = 12
            plt.rcParams['xtick.labelsize'] = 10
            plt.rcParams['ytick.labelsize'] = 10
            
            # Set grid style
            plt.rcParams['grid.alpha'] = 0.3
            plt.rcParams['grid.linestyle'] = '--'
            
            # Set figure background
            plt.rcParams['figure.facecolor'] = 'white'
            plt.rcParams['axes.facecolor'] = 'white'
            
            self.logger.info("Configured matplotlib with modern styling")
            return True
        except Exception as e:
            self.logger.error(f"Error configuring matplotlib: {str(e)}")
            return False
    
    def create_custom_widget(self, parent, widget_type, **kwargs):
        """
        Create a custom styled widget
        """
        try:
            # Set default styling based on widget type
            if widget_type == 'button':
                # Create a custom styled button
                button = tk.Button(parent, 
                                 bg=self.primary_color,
                                 fg='white',
                                 activebackground=self.secondary_color,
                                 activeforeground='white',
                                 relief=tk.RAISED,
                                 borderwidth=1,
                                 padx=10,
                                 pady=5,
                                 font=self.text_font,
                                 **kwargs)
                return button
                
            elif widget_type == 'label':
                # Create a custom styled label
                label = tk.Label(parent,
                               bg=self.background_color,
                               fg=self.text_color,
                               font=self.text_font,
                               **kwargs)
                return label
                
            elif widget_type == 'entry':
                # Create a custom styled entry
                entry = tk.Entry(parent,
                               bg='white',
                               fg=self.text_color,
                               insertbackground=self.text_color,  # Cursor color
                               relief=tk.SOLID,
                               borderwidth=1,
                               **kwargs)
                return entry
                
            elif widget_type == 'frame':
                # Create a custom styled frame
                frame = tk.Frame(parent,
                               bg=self.background_color,
                               relief=kwargs.pop('relief', tk.FLAT),
                               borderwidth=kwargs.pop('borderwidth', 0),
                               **kwargs)
                return frame
                
            else:
                self.logger.warning(f"Unknown widget type: {widget_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating custom widget: {str(e)}")
            return None

    def create_card_frame(self, parent, title=None, **kwargs):
        """
        Create a modern card-like frame with optional title
        """
        try:
            # Create the main card frame
            card = tk.Frame(parent,
                          bg='white',
                          relief=tk.RAISED,
                          borderwidth=1,
                          padx=15,
                          pady=15,
                          **kwargs)
            
            # If title is provided, add a title label
            if title:
                title_label = tk.Label(card,
                                     text=title,
                                     bg='white',
                                     fg=self.text_color,
                                     font=self.header_font)
                title_label.pack(anchor='w', pady=(0, 10))
            
            return card
        except Exception as e:
            self.logger.error(f"Error creating card frame: {str(e)}")
            return None

# Create a global theme instance for easy access
theme = ModernUITheme()