import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging
import seaborn as sns
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class PatternsChart:
    def __init__(self, frame, data=None, title="Patterns Chart"):
        self.frame = frame
        self.data = data
        self.title = title
        self.logger = logging.getLogger(__name__)
        
        # Modern color palette
        self.colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c']
        
        # Configure matplotlib styling
        plt.style.use('seaborn-v0_8-whitegrid')  # Modern clean style
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.prop_cycle'] = plt.cycler(color=self.colors)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['figure.titlesize'] = 16
        
        # Create the figure with modern styling
        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.figure.add_subplot(111)
        
        # Create a frame for chart controls
        self.controls_frame = tk.Frame(self.frame, bg='#f9f9f9')
        self.controls_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        # Add title label
        title_label = tk.Label(self.controls_frame, 
                             text=self.title, 
                             font=("Helvetica", 14, "bold"),
                             bg='#f9f9f9',
                             fg='#2c3e50')
        title_label.pack(side='left', padx=5, pady=5)
        
        # Add refresh button
        refresh_button = ttk.Button(self.controls_frame, text="Refresh", 
                                  command=self.refresh_data)
        refresh_button.pack(side='right', padx=5, pady=5)
    
    def create_chart(self):
        """Create and display the chart with modern styling"""
        try:
            # Draw the chart based on data
            self._draw_chart()
            
            # Create a frame for the chart with a subtle border
            chart_frame = tk.Frame(self.frame, bd=1, relief=tk.GROOVE, bg='white')
            chart_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Create canvas with improved styling
            canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
            
            # Draw the canvas first
            canvas.draw()
            
            # Pack the canvas widget with improved layout
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side='top', fill='both', expand=True)
            
            # Add toolbar with navigation options
            toolbar_frame = tk.Frame(self.frame, bg='#f9f9f9')
            toolbar_frame.pack(side='bottom', fill='x')
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            
            return canvas_widget
        except Exception as e:
            self.logger.error(f"Chart creation error: {str(e)}")
            return None
    
    def _draw_chart(self):
        """Draw the chart with the provided data"""
        if not self.data:
            self.ax.text(0.5, 0.5, "No data available", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14)
            return
        
        # Process and display data (example implementation)
        # This should be replaced with actual data processing logic
        x = range(len(self.data))
        y = self.data
        
        # Create bar chart with enhanced styling
        bars = self.ax.bar(x, y, color=self.colors[0], alpha=0.8)
        
        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            self.ax.text(bar.get_x() + bar.get_width()/2., height + 0.3,
                        f'{int(height)}', ha='center', va='bottom')
        
        # Customize appearance
        self.ax.set_title(self.title, pad=20)
        self.ax.set_xlabel('Category')
        self.ax.set_ylabel('Value')
        
        # Add grid for better readability
        self.ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        # Adjust layout
        self.figure.tight_layout()
    
    def refresh_data(self):
        """Refresh the chart data"""
        # This would typically fetch new data and update the chart
        self.logger.info("Refreshing chart data...")
        # For demonstration, we'll just update with random data
        import random
        self.data = [random.randint(5, 20) for _ in range(5)]
        self.update_chart()
    
    def update_chart(self):
        """Update the chart with new data"""
        try:
            # Clear the current axes
            self.ax.clear()
            
            # Redraw the chart
            self._draw_chart()
            
            # Update the figure
            self.figure.canvas.draw()
            
            return True
        except Exception as e:
            self.logger.error(f"Chart update error: {str(e)}")
            return False
