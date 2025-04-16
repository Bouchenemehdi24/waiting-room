import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import logging
import seaborn as sns
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import tkinter as tk
from tkinter import ttk

class EnhancedAnalytics:
    def __init__(self, reports_manager):
        self.reports_manager = reports_manager
        self.logger = logging.getLogger(__name__)
        
        # Use a basic style instead of seaborn
        plt.style.use('default')
        # Set font family to something common
        plt.rcParams['font.family'] = 'DejaVu Sans'
        
        # Set style for all charts
        self.colors = ['#2ecc71', '#3498db', '#e74c3c', '#f1c40f', '#9b59b6']
        plt.rcParams['axes.prop_cycle'] = plt.cycler(color=self.colors)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 12
        plt.rcParams['figure.titlesize'] = 14

    def create_revenue_chart(self, frame, data):
        """Create revenue chart with improved styling"""
        try:
            if not data:
                return None
                
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            dates = [row['visit_date'] for row in data]
            revenues = [float(row['daily_total'] or 0) for row in data]  # Handle None values
            
            # Plot bars
            bars = ax.bar(dates, revenues, color=self.colors[0])
            
            # Customize appearance
            ax.set_title('Revenus Journaliers', pad=20)
            ax.set_xlabel('Date')
            ax.set_ylabel('Revenu (DA)')
            
            # Rotate x-axis labels
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height):,}', ha='center', va='bottom')
            
            # Adjust layout
            fig.tight_layout()
            
            return self._embed_chart(frame, fig)
            
        except Exception as e:
            self.logger.error(f"Revenue chart creation error: {str(e)}")
            return None

    def create_visit_patterns_chart(self, frame, data):
        """Create visit patterns chart with improved styling"""
        try:
            if not data:
                return None
                
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            hours = [int(row[0]) for row in data]
            visits = [float(row[3] or 0) for row in data]  # Handle None values
            wait_times = [float(row[1] or 0) for row in data]  # Handle None values
            
            # Create double axis plot
            ax2 = ax.twinx()
            
            # Plot visits bars and wait time line
            bars = ax.bar(hours, visits, color=self.colors[0], alpha=0.7)
            line = ax2.plot(hours, wait_times, color=self.colors[1], linewidth=2, marker='o')
            
            # Customize appearance
            ax.set_title('Motifs de Visites par Heure', pad=20)
            ax.set_xlabel('Heure')
            ax.set_ylabel('Nombre de Visites')
            ax2.set_ylabel('Temps d\'Attente Moyen (min)')
            
            # Add legends with proper positioning
            ax.legend(['Visites'], loc='upper left')
            ax2.legend(['Temps d\'Attente'], loc='upper right')
            
            # Adjust layout
            fig.tight_layout()
            
            return self._embed_chart(frame, fig)
            
        except Exception as e:
            self.logger.error(f"Visit patterns chart error: {str(e)}")
            return None

    def create_services_chart(self, frame):
        """Create services distribution chart with improved styling"""
        try:
            data = self.reports_manager.get_services_summary()
            if not data:
                return None
                
            # Filter out zero values
            data = [d for d in data if d['count'] and d['count'] > 0]
            
            if not data:  # Check if we have any non-zero data
                return None
                
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            services = [row['service_name'] for row in data]
            counts = [row['count'] for row in data]
            
            # Create pie chart
            wedges, texts, autotexts = ax.pie(counts, labels=services, 
                                            autopct='%1.1f%%',
                                            colors=self.colors)
            
            # Customize appearance
            ax.set_title('Distribution des Services', pad=20)
            
            # Add legend with proper placement
            ax.legend(wedges, services,
                     title="Services",
                     loc="center left",
                     bbox_to_anchor=(1.1, 0, 0.5, 1))
            
            # Adjust layout with extra space for legend
            fig.set_tight_layout(False)
            fig.subplots_adjust(right=0.85)
            
            return self._embed_chart(frame, fig)
            
        except Exception as e:
            self.logger.error(f"Services chart creation error: {str(e)}")
            return None

    def _embed_chart(self, frame, fig):
        """Embed chart in frame and return the canvas widget with modern styling"""
        try:
            # Create a frame for the chart with a subtle border
            chart_frame = tk.Frame(frame, bd=1, relief=tk.GROOVE, bg='white')
            chart_frame.pack(fill='both', expand=True, padx=5, pady=5)
            
            # Create canvas with improved styling
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)
            
            # Draw the canvas
            canvas.draw()
            
            # Pack the canvas widget with improved layout
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(side='top', fill='both', expand=True)
            
            # Add toolbar with navigation options
            toolbar_frame = tk.Frame(frame, bg='#f9f9f9')
            toolbar_frame.pack(side='bottom', fill='x')
            toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
            toolbar.update()
            
            return canvas_widget
        except Exception as e:
            self.logger.error(f"Chart embedding error: {str(e)}")
            return None
