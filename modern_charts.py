import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import logging
import seaborn as sns
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class ModernChart:
    """Base class for modern chart implementations with enhanced UI"""
    def __init__(self, frame, title="Chart", figsize=(10, 6), dpi=100):
        self.frame = frame
        self.title = title
        self.figsize = figsize
        self.dpi = dpi
        self.logger = logging.getLogger(__name__)
        
        # Modern color palette
        self.colors = ['#3498db', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c', '#34495e']
        
        # Configure matplotlib styling
        plt.style.use('seaborn-v0_8-whitegrid')  # Modern clean style
        plt.rcParams['font.family'] = 'DejaVu Sans'
        plt.rcParams['axes.prop_cycle'] = plt.cycler(color=self.colors)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['figure.titlesize'] = 16
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        
        # Create the figure
        self.figure = Figure(figsize=self.figsize, dpi=self.dpi)
        self.ax = self.figure.add_subplot(111)
        
        # Create a frame for chart controls
        self.controls_frame = tk.Frame(self.frame)
        self.controls_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        # Create a frame for the chart
        self.chart_frame = tk.Frame(self.frame)
        self.chart_frame.pack(side='top', fill='both', expand=True, padx=5, pady=5)
        
    def create_chart(self):
        """Base method to create and display the chart"""
        try:
            # Draw the chart (to be implemented by subclasses)
            self._draw_chart()
            
            # Embed the chart in the frame
            self._embed_chart()
            
            # Add controls (to be implemented by subclasses)
            self._add_controls()
            
            return True
        except Exception as e:
            self.logger.error(f"Chart creation error: {str(e)}")
            return False
    
    def _draw_chart(self):
        """Draw the chart (to be implemented by subclasses)"""
        raise NotImplementedError("Subclasses must implement _draw_chart()")
    
    def _add_controls(self):
        """Add controls to the chart (to be implemented by subclasses)"""
        # Default implementation adds a title label
        title_label = tk.Label(self.controls_frame, text=self.title, font=("Helvetica", 14, "bold"))
        title_label.pack(side='left', padx=5, pady=5)
    
    def _embed_chart(self):
        """Embed the chart in the frame with modern styling"""
        try:
            # Create canvas with improved styling
            self.canvas = FigureCanvasTkAgg(self.figure, master=self.chart_frame)
            
            # Draw the canvas first
            self.canvas.draw()
            
            # Create a frame for the canvas with a subtle border
            canvas_frame = tk.Frame(self.chart_frame, bd=1, relief=tk.GROOVE)
            canvas_frame.pack(fill='both', expand=True, padx=2, pady=2)
            
            # Pack the canvas widget with improved layout
            canvas_widget = self.canvas.get_tk_widget()
            canvas_widget.pack(in_=canvas_frame, side='top', fill='both', expand=True)
            
            # Add toolbar with navigation options
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar_frame = tk.Frame(self.chart_frame)
            toolbar_frame.pack(side='bottom', fill='x')
            toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            toolbar.update()
            
            return canvas_widget
        except Exception as e:
            self.logger.error(f"Chart embedding error: {str(e)}")
            return None
    
    def update_chart(self, data):
        """Update the chart with new data"""
        try:
            # Clear the current axes
            self.ax.clear()
            
            # Update the chart (to be implemented by subclasses)
            self._draw_chart(data)
            
            # Redraw the canvas
            self.canvas.draw()
            
            return True
        except Exception as e:
            self.logger.error(f"Chart update error: {str(e)}")
            return False


class PatternsChart(ModernChart):
    """Modern implementation of the patterns chart with enhanced UI"""
    def __init__(self, frame, data=None, title="Patterns Chart"):
        super().__init__(frame, title=title)
        self.data = data
    
    def _draw_chart(self):
        """Draw the patterns chart with the provided data"""
        if not self.data:
            self.ax.text(0.5, 0.5, "No data available", 
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=self.ax.transAxes,
                        fontsize=14)
            return
        
        # Example implementation - replace with actual data processing
        x = [1, 2, 3, 4, 5]
        y = [10, 15, 7, 12, 9]
        
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
    
    def _add_controls(self):
        """Add controls specific to the patterns chart"""
        # Call the parent method to add the title
        super()._add_controls()
        
        # Add a refresh button
        refresh_button = ttk.Button(self.controls_frame, text="Refresh", 
                                  command=self.refresh_data)
        refresh_button.pack(side='right', padx=5, pady=5)
        
        # Add a time period selector
        period_label = ttk.Label(self.controls_frame, text="Period:")
        period_label.pack(side='right', padx=5, pady=5)
        
        period_values = ["Day", "Week", "Month", "Year"]
        self.period_var = tk.StringVar(value=period_values[0])
        period_combo = ttk.Combobox(self.controls_frame, 
                                  textvariable=self.period_var,
                                  values=period_values,
                                  width=10,
                                  state="readonly")
        period_combo.pack(side='right', padx=5, pady=5)
        period_combo.bind("<<ComboboxSelected>>", self.on_period_change)
    
    def refresh_data(self):
        """Refresh the chart data"""
        # This would typically fetch new data and update the chart
        self.logger.info("Refreshing chart data...")
        # For demonstration, we'll just update with random data
        import random
        new_data = [random.randint(5, 20) for _ in range(5)]
        self.update_chart(new_data)
    
    def on_period_change(self, event):
        """Handle period change event"""
        period = self.period_var.get()
        self.logger.info(f"Period changed to {period}")
        # This would typically fetch data for the new period and update the chart
        self.refresh_data()
    
    def update_chart(self, data):
        """Update the chart with new data"""
        self.data = data
        super().update_chart(data)


# Example of how to use the modern chart classes
def create_demo_chart(parent_frame):
    """Create a demo chart to showcase the modern UI"""
    # Create a frame for the chart
    chart_frame = ttk.Frame(parent_frame)
    chart_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    # Create and display the chart
    chart = PatternsChart(chart_frame, title="Sample Patterns")
    chart.create_chart()
    
    return chart