import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import ttkbootstrap as ttkb  # Import ttkbootstrap with alias to differentiate
from ttkbootstrap import Style
from datetime import datetime, time, timedelta
import json
import os
import csv
import logging
import calendar

# ============================
# Configuration and Constants
# ============================

DATA_FILE = "dtr_records.json"
LOG_FILE = "dtr_app.log"

# Conversion dictionaries based on provided tables
MINUTES_TO_DAY = {
    0: 0.0, 1: 0.002, 2: 0.004, 3: 0.005, 4: 0.006, 5: 0.008,
    6: 0.010, 7: 0.012, 8: 0.013, 9: 0.015, 10: 0.017,
    11: 0.019, 12: 0.021, 13: 0.023, 14: 0.025, 15: 0.027,
    16: 0.029, 17: 0.031, 18: 0.033, 19: 0.035, 20: 0.037,
    21: 0.038, 22: 0.040, 23: 0.042, 24: 0.044, 25: 0.046,
    26: 0.048, 27: 0.050, 28: 0.052, 29: 0.054, 30: 0.056,
    31: 0.065, 32: 0.067, 33: 0.069, 34: 0.071, 35: 0.073,
    36: 0.075, 37: 0.077, 38: 0.079, 39: 0.081, 40: 0.083,
    41: 0.085, 42: 0.087, 43: 0.090, 44: 0.092, 45: 0.094,
    46: 0.096, 47: 0.098, 48: 0.100, 49: 0.102, 50: 0.104,
    51: 0.106, 52: 0.108, 53: 0.110, 54: 0.112, 55: 0.115,
    56: 0.117, 57: 0.119, 58: 0.121, 59: 0.123, 60: 0.125
}

HOURS_TO_DAY = {
    1: 0.125, 2: 0.250, 3: 0.375, 4: 0.500,
    5: 0.625, 6: 0.750, 7: 0.875, 8: 1.000
}

# Allowed time configurations per weekday
ALLOWED_TIMES = {
    "Monday": {
        "supposed_time_in": time(8, 00)
    },
    "Tuesday": {
        "supposed_time_in": time(8, 30)
    },
    "Wednesday": {
        "supposed_time_in": time(8, 30)
    },
    "Thursday": {
        "supposed_time_in": time(8, 30)
    },
    "Friday": {
        "supposed_time_in": time(8, 30)
    }
}

# ============================
# Utility Functions
# ============================

def convert_time_diff_to_day_fraction(hours, minutes):
    """
    Convert hours/minutes difference into a fraction of a day.
    Caps hours to an 8-hour maximum (1 full day).
    Looks up the fraction from the dictionaries; if out of range,
    uses boundary values as needed.
    """
    hours = max(0, min(hours, 8))
    minutes = max(0, min(minutes, 60))
    day_fraction = HOURS_TO_DAY.get(hours, 0.0) + MINUTES_TO_DAY.get(minutes, 0.0)
    return round(day_fraction, 3)

def setup_logging():
    """
    Configure logging for the application.
    """
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

class Tooltip:
    """
    A custom tooltip class for Tkinter widgets.
    """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(500, self.showtip)

    def unschedule(self):
        id_ = self.id
        self.id = None
        if id_:
            self.widget.after_cancel(id_)

    def showtip(self, event=None):
        if self.tipwindow or not self.text:
            return
        # Calculate position relative to parent
        parent = self.widget.winfo_toplevel()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()

        # Tooltip dimensions
        self.widget.update_idletasks()
        tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry("+%d+%d" % (parent_x + parent_width//2, parent_y + parent_height//2))

        # Create label inside tooltip window
        label = ttk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("tahoma", "8", "normal")
        )
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

# ============================
# Dialog Classes
# ============================

class TimePickerDialog:
    """
    A dialog for selecting time (Hour, Minute, AM/PM).
    Modified to handle separate hour and minute entries with a fixed colon.
    """
    def __init__(self, parent, initial_time=None, title="Select Time"):
        self.parent = parent  # Keep a reference to the parent
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.grab_set()  # Make the dialog modal
        self.selected_time = None

        # Determine initial time
        if initial_time:
            hour_24 = initial_time.hour
            minute = initial_time.minute
            ampm = "PM" if hour_24 >= 12 else "AM"
            hour = hour_24 % 12
            hour = 12 if hour == 0 else hour
        else:
            hour = 12
            minute = 0
            ampm = "AM"

        # Hour selection
        ttk.Label(self.top, text="Hour:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.hour_var = tk.StringVar(value=str(hour))
        self.hour_spin = ttk.Spinbox(self.top, from_=1, to=12, textvariable=self.hour_var, width=5, state="readonly")
        self.hour_spin.grid(row=0, column=1, padx=10, pady=5)

        # Minute selection
        ttk.Label(self.top, text="Minute:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.minute_var = tk.StringVar(value=f"{minute:02}")
        self.minute_spin = ttk.Spinbox(self.top, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f", state="readonly")
        self.minute_spin.grid(row=1, column=1, padx=10, pady=5)

        # AM/PM selection
        ttk.Label(self.top, text="AM/PM:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ampm_var = tk.StringVar(value=ampm)
        self.ampm_combo = ttk.Combobox(self.top, textvariable=self.ampm_var, values=["AM", "PM"], state="readonly", width=3)
        self.ampm_combo.grid(row=2, column=1, padx=10, pady=5)
        self.ampm_combo.current(0 if ampm == "AM" else 1)

        # Buttons
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

        # Center the dialog relative to parent
        self.center_dialog()

        # Bind events for manual editing
        self.top.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_dialog(self):
        """
        Center the dialog on the parent window.
        """
        self.parent.update_idletasks()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        self.top.update_idletasks()
        dialog_width = self.top.winfo_width()
        dialog_height = self.top.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (dialog_width // 2)
        pos_y = parent_y + (parent_height // 2) - (dialog_height // 2)

        self.top.geometry(f"+{pos_x}+{pos_y}")

    def on_ok(self):
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            ampm = self.ampm_var.get()

            if ampm == "PM" and hour != 12:
                hour += 12
            elif ampm == "AM" and hour == 12:
                hour = 0

            self.selected_time = time(hour, minute)
            self.top.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid time.")

    def on_cancel(self):
        self.top.destroy()

    def show(self):
        self.top.wait_window()
        return self.selected_time

# ============================
# Main Application Class
# ============================

class DailyTimeRecordApp:
    """
    The main application class for the Daily Time Record Calculator.
    """
    def __init__(self, master):
        self.master = master
        master.title("Daily Time Record")

        # Add the icon to the Tkinter window (if available)
        icon_path = "icon.ico"
        if os.path.exists(icon_path):
            master.iconbitmap(icon_path)
        else:
            logging.warning("Icon file not found. Default icon will be used.")

        # Allow window to be resizable
        master.resizable(True, True)

        # Initialize style with ttkbootstrap
        self.style = Style(theme='flatly')  # Default to 'flatly' (light theme)
        self.current_theme = 'flatly'

        # Load existing records
        self.records = self.load_records()

        # Current Date and Day (auto-set from system date)
        self.selected_date = datetime.now().date()
        self.current_day = self.selected_date.strftime("%A")

        # Setup UI Components
        self.setup_menu()
        self.setup_header()
        self.setup_time_inputs()
        self.setup_controls()
        self.setup_history()

        # Center the window
        self.center_window()

        # -----------------------------
        # Automatically set Supposed Time In on startup
        # based on the current weekday
        # -----------------------------
        supposed_time_in = ALLOWED_TIMES.get(self.current_day, {}).get("supposed_time_in")
        if supposed_time_in:
            self.label_supposed_time_in.config(text=f"Supposed Time In: {supposed_time_in.strftime('%I:%M %p')}")
        else:
            self.label_supposed_time_in.config(text="Supposed Time In: --:-- --")

        # If needed, you can also set the "Supposed Time Out" but by design,
        # it is usually calculated after inputting the Actual Time In + 8 hours.

        # (No welcome dialog anymore, as requested.)

    # ----------------------------
    # Window Setup Methods
    # ----------------------------

    def center_window(self):
        """
        Center the window on the screen.
        """
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.master.geometry(f"+{x}+{y}")

    def setup_menu(self):
        """
        Setup the menu bar with File and Help menus.
        """
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)
        Tooltip(file_menu, "File operations")

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help_dialog)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        Tooltip(help_menu, "Help and information")

    def setup_header(self):
        """
        Setup the header section with Date Selection, Day Label, and Full-Screen Toggle.
        """
        header_frame = ttkb.Frame(self.master)
        header_frame.pack(fill="x", pady=10, padx=10)

        # Labels frame (left side) using standard ttk
        labels_frame = ttk.Frame(header_frame)
        labels_frame.pack(side="left", fill="x", expand=True)

        # Custom Date Selection using Comboboxes
        date_selection_frame = ttk.Frame(labels_frame)
        date_selection_frame.pack(pady=5, anchor="w")

        # Year Combobox
        ttk.Label(date_selection_frame, text="Year:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        current_year = datetime.now().year
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(
            date_selection_frame,
            textvariable=self.year_var,
            values=[str(year) for year in range(current_year - 5, current_year + 6)],
            state="readonly",
            width=5
        )
        self.year_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.year_combo.set(str(self.selected_date.year))
        self.year_combo.bind("<<ComboboxSelected>>", self.update_days)

        # Month Combobox
        ttk.Label(date_selection_frame, text="Month:").grid(row=0, column=2, padx=5, pady=2, sticky="e")
        self.month_var = tk.StringVar()
        self.month_combo = ttk.Combobox(
            date_selection_frame,
            textvariable=self.month_var,
            values=[calendar.month_name[i] for i in range(1, 13)],
            state="readonly",
            width=10
        )
        self.month_combo.grid(row=0, column=3, padx=5, pady=2, sticky="w")
        self.month_combo.set(calendar.month_name[self.selected_date.month])
        self.month_combo.bind("<<ComboboxSelected>>", self.update_days)

        # Day Combobox
        ttk.Label(date_selection_frame, text="Day:").grid(row=0, column=4, padx=5, pady=2, sticky="e")
        self.day_var = tk.StringVar()
        self.day_combo = ttk.Combobox(
            date_selection_frame,
            textvariable=self.day_var,
            values=[str(day) for day in range(1, 32)],
            state="readonly",
            width=3
        )
        self.day_combo.grid(row=0, column=5, padx=5, pady=2, sticky="w")
        self.day_combo.set(str(self.selected_date.day))
        self.day_combo.bind("<<ComboboxSelected>>", self.on_date_change)

        Tooltip(self.year_combo, "Select Year")
        Tooltip(self.month_combo, "Select Month")
        Tooltip(self.day_combo, "Select Day")

        # Label for Day of the Week
        self.label_day = ttk.Label(labels_frame, text=f"Day: {self.current_day}", font=("Inter", 16))
        self.label_day.pack(pady=5, anchor="w")

        # Theme and Full-Screen Toggle Buttons (right side) using ttkbootstrap
        theme_buttons_frame = ttkb.Frame(header_frame)
        theme_buttons_frame.pack(side="right", anchor="e")

        self.button_light_mode = ttkb.Button(theme_buttons_frame, text="Light Mode",
                                             command=lambda: self.change_theme("flatly"))
        self.button_light_mode.pack(side="left", padx=5)
        Tooltip(self.button_light_mode, "Switch to Light Mode")

        self.button_dark_mode = ttkb.Button(theme_buttons_frame, text="Dark Mode",
                                            command=lambda: self.change_theme("superhero"))
        self.button_dark_mode.pack(side="left", padx=5)
        Tooltip(self.button_dark_mode, "Switch to Dark Mode")

        # Full-Screen Toggle Button
        self.fullscreen = False
        self.button_fullscreen = ttkb.Button(theme_buttons_frame, text="Full Screen",
                                             command=self.toggle_fullscreen)
        self.button_fullscreen.pack(side="left", padx=5)
        Tooltip(self.button_fullscreen, "Toggle Full Screen Mode")

    def setup_time_inputs(self):
        """
        Setup the Morning and Afternoon time input sections.
        Enhanced to display Late/Undertime and their Deduction in a more visible location on the right.
        """
        # Frame for Morning Inputs using ttkbootstrap
        self.frame_morning = ttkb.LabelFrame(self.master, text="Morning", padding=10)
        self.frame_morning.pack(padx=10, pady=10, fill="x", expand=True)

        # Left side: labels & time input
        left_morning_frame = ttkb.Frame(self.frame_morning)
        left_morning_frame.pack(side="left", fill="x", expand=True)

        # Supposed Time In Label
        self.label_supposed_time_in = ttk.Label(left_morning_frame, text="Supposed Time In: --:-- --", font=("Inter", 12))
        self.label_supposed_time_in.pack(anchor="w", pady=(0, 5))

        # Actual Time In Input
        self.create_actual_time_input(left_morning_frame, "Actual Time In:", "morning_actual_time_in")

        # Clear Button for Morning (still on left)
        self.button_clear_morning = ttkb.Button(left_morning_frame, text="Clear Morning",
                                                command=self.clear_morning)
        self.button_clear_morning.pack(anchor="w", pady=5)
        Tooltip(self.button_clear_morning, "Clear Morning Inputs")

        # Right side: Late minutes & Late Deduction
        right_morning_frame = ttkb.Frame(self.frame_morning)
        right_morning_frame.pack(side="right", anchor="center", padx=10)

        # Enhanced "Late: 0 minutes" label
        self.label_morning_late = ttk.Label(
            right_morning_frame,
            text="Late: 0 minutes",
            font=("Inter", 13, "bold"),
            foreground="#000000"  # A distinct color for visibility
        )
        self.label_morning_late.pack(anchor="center", pady=5)

        # Additional "Late Deduction" label
        self.label_morning_late_deduction = ttk.Label(
            right_morning_frame,
            text="Late Deduction: 0.000",
            font=("Inter", 13, "bold"),
            foreground="#000000"
        )
        self.label_morning_late_deduction.pack(anchor="center", pady=5)

        # Frame for Afternoon Inputs using ttkbootstrap
        self.frame_afternoon = ttkb.LabelFrame(self.master, text="Afternoon", padding=10)
        self.frame_afternoon.pack(padx=10, pady=10, fill="x", expand=True)

        # Left side: labels & time input
        left_afternoon_frame = ttkb.Frame(self.frame_afternoon)
        left_afternoon_frame.pack(side="left", fill="x", expand=True)

        # Supposed Time Out Label
        self.label_supposed_time_out = ttk.Label(left_afternoon_frame, text="Supposed Time Out: --:-- --", font=("Inter", 12))
        self.label_supposed_time_out.pack(anchor="w", pady=(0, 5))

        # Actual Time Out Input
        self.create_actual_time_input(left_afternoon_frame, "Actual Time Out:", "afternoon_actual_time_out")

        # Clear Button for Afternoon
        self.button_clear_afternoon = ttkb.Button(left_afternoon_frame, text="Clear Afternoon",
                                                  command=self.clear_afternoon)
        self.button_clear_afternoon.pack(anchor="w", pady=5)
        Tooltip(self.button_clear_afternoon, "Clear Afternoon Inputs")

        # Right side: Undertime minutes & Undertime Deduction
        right_afternoon_frame = ttkb.Frame(self.frame_afternoon)
        right_afternoon_frame.pack(side="right", anchor="center", padx=10)

        # Enhanced "Undertime: 0 minutes" label
        self.label_afternoon_undertime = ttk.Label(
            right_afternoon_frame,
            text="Undertime: 0 minutes",
            font=("Inter", 13, "bold"),
            foreground="#000000"
        )
        self.label_afternoon_undertime.pack(anchor="center", pady=5)

        # Additional "Undertime Deduction" label
        self.label_afternoon_undertime_deduction = ttk.Label(
            right_afternoon_frame,
            text="Undertime Deduction: 0.000",
            font=("Inter", 13, "bold"),
            foreground="#000000"
        )
        self.label_afternoon_undertime_deduction.pack(anchor="center", pady=5)

    def setup_controls(self):
        """
        Setup controls such as Calculate button, Deduction display, Save, and Export buttons.
        """
        # Control Buttons Frame using ttkbootstrap
        controls_frame = ttkb.Frame(self.master)
        controls_frame.pack(pady=10)

        # Configure grid to be responsive
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)

        # Calculate Button
        self.button_calculate = ttkb.Button(
            controls_frame,
            text="Calculate Deductions",
            command=self.calculate_deductions,
            bootstyle="success"
        )
        self.button_calculate.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        Tooltip(self.button_calculate, "Calculate deduction points based on input times")

        # Save Record Button
        self.button_save = ttkb.Button(
            controls_frame,
            text="Save Record",
            command=self.save_record,
            bootstyle="info"
        )
        self.button_save.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        Tooltip(self.button_save, "Save the current day's record")

        # Export History Button
        self.button_export = ttkb.Button(
            controls_frame,
            text="Export History",
            command=self.export_history,
            bootstyle="warning"
        )
        self.button_export.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        Tooltip(self.button_export, "Export deduction history to CSV")

        # Deduction Points Display using standard ttk
        self.label_deductions = ttk.Label(self.master, text="Total Deduction Points: 0.000", font=("Inter", 16, "bold"))
        self.label_deductions.pack(pady=20)

    def setup_history(self):
        """
        Setup the Deduction History Treeview.
        """
        history_frame = ttkb.LabelFrame(self.master, text="Deduction History", padding=10)
        history_frame.pack(padx=10, pady=10, fill="both", expand=True)

        # Search and Filter Frame using standard ttk
        search_frame = ttk.Frame(history_frame)
        search_frame.pack(fill="x", pady=5)

        # Custom Date Selection for Search - From Date
        ttk.Label(search_frame, text="From Year:").pack(side="left", padx=5)
        current_year = datetime.now().year
        self.search_from_year_var = tk.StringVar()
        self.search_from_year = ttk.Combobox(
            search_frame,
            textvariable=self.search_from_year_var,
            values=[str(year) for year in range(current_year - 5, current_year + 6)],
            state="readonly",
            width=5
        )
        self.search_from_year.pack(side="left", padx=5)
        self.search_from_year.set(str(self.selected_date.year))
        self.search_from_year.bind("<<ComboboxSelected>>", self.update_search_from_days)

        ttk.Label(search_frame, text="From Month:").pack(side="left", padx=5)
        self.search_from_month_var = tk.StringVar()
        self.search_from_month = ttk.Combobox(
            search_frame,
            textvariable=self.search_from_month_var,
            values=[calendar.month_name[i] for i in range(1, 13)],
            state="readonly",
            width=10
        )
        self.search_from_month.pack(side="left", padx=5)
        self.search_from_month.set(calendar.month_name[self.selected_date.month])
        self.search_from_month.bind("<<ComboboxSelected>>", self.update_search_from_days)

        ttk.Label(search_frame, text="From Day:").pack(side="left", padx=5)
        self.search_from_day_var = tk.StringVar()
        self.search_from_day = ttk.Combobox(
            search_frame,
            textvariable=self.search_from_day_var,
            values=[str(day) for day in range(1, 32)],
            state="readonly",
            width=3
        )
        self.search_from_day.pack(side="left", padx=5)
        self.search_from_day.set(str(self.selected_date.day))
        self.search_from_day.bind("<<ComboboxSelected>>", self.on_date_change)

        # Custom Date Selection for Search - To Date
        ttk.Label(search_frame, text="To Year:").pack(side="left", padx=5)
        self.search_to_year_var = tk.StringVar()
        self.search_to_year = ttk.Combobox(
            search_frame,
            textvariable=self.search_to_year_var,
            values=[str(year) for year in range(current_year - 5, current_year + 6)],
            state="readonly",
            width=5
        )
        self.search_to_year.pack(side="left", padx=5)
        self.search_to_year.set(str(self.selected_date.year))
        self.search_to_year.bind("<<ComboboxSelected>>", self.update_search_to_days)

        ttk.Label(search_frame, text="To Month:").pack(side="left", padx=5)
        self.search_to_month_var = tk.StringVar()
        self.search_to_month = ttk.Combobox(
            search_frame,
            textvariable=self.search_to_month_var,
            values=[calendar.month_name[i] for i in range(1, 13)],
            state="readonly",
            width=10
        )
        self.search_to_month.pack(side="left", padx=5)
        self.search_to_month.set(calendar.month_name[self.selected_date.month])
        self.search_to_month.bind("<<ComboboxSelected>>", self.update_search_to_days)

        ttk.Label(search_frame, text="To Day:").pack(side="left", padx=5)
        self.search_to_day_var = tk.StringVar()
        self.search_to_day = ttk.Combobox(
            search_frame,
            textvariable=self.search_to_day_var,
            values=[str(day) for day in range(1, 32)],
            state="readonly",
            width=3
        )
        self.search_to_day.pack(side="left", padx=5)
        self.search_to_day.set(str(self.selected_date.day))
        self.search_to_day.bind("<<ComboboxSelected>>", self.on_date_change)

        Tooltip(self.search_from_year, "Select From Year")
        Tooltip(self.search_from_month, "Select From Month")
        Tooltip(self.search_from_day, "Select From Day")
        Tooltip(self.search_to_year, "Select To Year")
        Tooltip(self.search_to_month, "Select To Month")
        Tooltip(self.search_to_day, "Select To Day")

        self.button_search = ttkb.Button(search_frame, text="Search", command=self.search_history)
        self.button_search.pack(side="left", padx=5)
        Tooltip(self.button_search, "Search records within the selected date range")

        self.button_reset = ttkb.Button(search_frame, text="Reset", command=self.populate_history)
        self.button_reset.pack(side="left", padx=5)
        Tooltip(self.button_reset, "Reset search filters")

        # Treeview for History using standard ttk
        self.history_tree = ttk.Treeview(
            history_frame,
            columns=(
                "Date", "Morning Actual Time In", "Supposed Time In", "Late Minutes",
                "Afternoon Actual Time Out", "Supposed Time Out", "Undertime Minutes",
                "Deduction Points"
            ),
            show='headings', 
            selectmode="browse"
        )
        self.history_tree.heading("Date", text="Date")
        self.history_tree.heading("Morning Actual Time In", text="Actual Time In")
        self.history_tree.heading("Supposed Time In", text="Supposed Time In")
        self.history_tree.heading("Late Minutes", text="Late (min)")
        self.history_tree.heading("Afternoon Actual Time Out", text="Actual Time Out")
        self.history_tree.heading("Supposed Time Out", text="Supposed Time Out")
        self.history_tree.heading("Undertime Minutes", text="Undertime (min)")
        self.history_tree.heading("Deduction Points", text="Deduction Points")
        self.history_tree.pack(fill="both", expand=True)

        # Adjust column widths
        self.history_tree.column("Date", width=100, anchor="center")
        self.history_tree.column("Morning Actual Time In", width=120, anchor="center")
        self.history_tree.column("Supposed Time In", width=120, anchor="center")
        self.history_tree.column("Late Minutes", width=100, anchor="center")
        self.history_tree.column("Afternoon Actual Time Out", width=120, anchor="center")
        self.history_tree.column("Supposed Time Out", width=120, anchor="center")
        self.history_tree.column("Undertime Minutes", width=120, anchor="center")
        self.history_tree.column("Deduction Points", width=120, anchor="center")

        # Scrollbar for Treeview
        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Context Menu for Treeview
        self.history_tree.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Edit Record", command=self.edit_record)
        self.context_menu.add_command(label="Delete Record", command=self.delete_record)

        self.populate_history()

    # ----------------------------
    # Helper Methods
    # ----------------------------

    def create_actual_time_input(self, parent, label_text, attr_name):
        """
        Create an actual time input section with label, fixed colon, separate hour and minute entries,
        AM/PM Combobox, and a button to open the Time Picker Dialog.
        """
        frame = ttkb.Frame(parent)
        frame.pack(fill="x", pady=5)

        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side="left", padx=5)

        # Hours Entry
        hour_var = tk.StringVar(value='00')
        hour_entry = ttk.Entry(frame, textvariable=hour_var, width=3, justify='center')
        hour_entry.pack(side="left", padx=(0, 2))
        Tooltip(hour_entry, "Enter hours (01-12)")
        self.register_time_validation(hour_entry, hour_var, part='hour')

        # Fixed Colon Label
        colon_label = ttk.Label(frame, text=":", width=1)
        colon_label.pack(side="left")

        # Minutes Entry
        minute_var = tk.StringVar(value='00')
        minute_entry = ttk.Entry(frame, textvariable=minute_var, width=3, justify='center')
        minute_entry.pack(side="left", padx=(2, 5))
        Tooltip(minute_entry, "Enter minutes (00-59)")
        self.register_time_validation(minute_entry, minute_var, part='minute')

        # AM/PM Combobox
        ampm_var = tk.StringVar(value="AM")
        ampm_combo = ttk.Combobox(frame, textvariable=ampm_var, values=["AM", "PM"], state="readonly", width=3)
        ampm_combo.pack(side="left", padx=(0, 5))
        ampm_combo.set("AM")
        Tooltip(ampm_combo, "Select AM or PM")

        # Button to open Time Picker Dialog
        time_button = ttkb.Button(frame, text="Select Time", command=lambda: self.open_time_picker(attr_name))
        time_button.pack(side="left", padx=2)
        Tooltip(time_button, "Open time picker")

        # Set attributes for later access
        setattr(self, f'{attr_name}_hour_var', hour_var)
        setattr(self, f'{attr_name}_minute_var', minute_var)
        setattr(self, f'{attr_name}_ampm_var', ampm_var)

        # Bind key release event for real-time editing
        hour_entry.bind("<KeyRelease>", self.create_time_input_key_release(hour_var, part='hour'))
        minute_entry.bind("<KeyRelease>", self.create_time_input_key_release(minute_var, part='minute'))

        # Bind Enter key to calculate deductions
        hour_entry.bind("<Return>", self.enter_key_pressed)
        minute_entry.bind("<Return>", self.enter_key_pressed)
        ampm_combo.bind("<Return>", self.enter_key_pressed)
        time_button.bind("<Return>", self.enter_key_pressed)

    def register_time_validation(self, entry, var, part='hour'):
        """
        Register validation for the time entry fields to ensure only valid input is allowed.
        """
        def validate(*args):
            value = var.get()
            if part == 'hour':
                if not value.isdigit() or not (1 <= int(value) <= 12):
                    entry.config(foreground='red')
                else:
                    entry.config(foreground='black')
            elif part == 'minute':
                if not value.isdigit() or not (0 <= int(value) <= 59):
                    entry.config(foreground='red')
                else:
                    entry.config(foreground='black')
        var.trace_add('write', validate)

    def create_time_input_key_release(self, var, part='hour'):
        """
        Create a key release handler for time input fields.
        Ensures only 2 digits are entered.
        """
        def on_key_release(event):
            current_text = var.get().strip().upper()
            if not current_text.isdigit():
                # Remove non-digit characters
                new_text = ''.join(filter(str.isdigit, current_text))
                var.set(new_text)
                return
            if len(current_text) > 2:
                # Limit to 2 digits
                var.set(current_text[:2])
        return on_key_release

    def open_time_picker(self, attr_name):
        """
        Open the TimePickerDialog and set the selected time to the corresponding entry fields,
        including the AM/PM Combobox.
        """
        hour_var = getattr(self, f'{attr_name}_hour_var')
        minute_var = getattr(self, f'{attr_name}_minute_var')
        ampm_var = getattr(self, f'{attr_name}_ampm_var')

        # Convert current entries to time object
        try:
            hour = int(hour_var.get())
            minute = int(minute_var.get())
            ampm = ampm_var.get()
            if ampm == "PM" and hour != 12:
                hour_24 = hour + 12
            elif ampm == "AM" and hour == 12:
                hour_24 = 0
            else:
                hour_24 = hour
            time_obj = time(hour_24, minute)
        except ValueError:
            time_obj = None

        picker = TimePickerDialog(self.master, initial_time=time_obj, title=f"Select {attr_name.replace('_', ' ').title()}")
        selected_time = picker.show()
        if selected_time:
            # Convert to 12-hour format with AM/PM
            hour_12 = selected_time.hour % 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            minute = selected_time.minute
            ampm = "PM" if selected_time.hour >= 12 else "AM"

            # Update the entries and AM/PM Combobox
            hour_var.set(f"{hour_12:02}")
            minute_var.set(f"{minute:02}")
            ampm_var.set(ampm)

    def on_date_change(self, event):
        """
        Callback when the date is changed in Date Selection Comboboxes.
        """
        try:
            # Determine which date selection was changed
            widget = event.widget
            if widget in [self.year_combo, self.month_combo, self.day_combo]:
                year = int(self.year_var.get())
                month = list(calendar.month_name).index(self.month_var.get())
                day = int(self.day_var.get())
            elif widget in [self.search_from_year, self.search_from_month, self.search_from_day]:
                year = int(self.search_from_year_var.get())
                month = list(calendar.month_name).index(self.search_from_month_var.get())
                day = int(self.search_from_day_var.get())
            elif widget in [self.search_to_year, self.search_to_month, self.search_to_day]:
                year = int(self.search_to_year_var.get())
                month = list(calendar.month_name).index(self.search_to_month_var.get())
                day = int(self.search_to_day_var.get())
            else:
                return

            self.selected_date = datetime(year, month, day).date()
            self.current_day = self.selected_date.strftime("%A")
            self.label_day.config(text=f"Day: {self.current_day}")

            # Update Supposed Time In based on the selected day
            supposed_time_in = ALLOWED_TIMES.get(self.current_day, {}).get("supposed_time_in")
            if supposed_time_in:
                self.label_supposed_time_in.config(text=f"Supposed Time In: {supposed_time_in.strftime('%I:%M %p')}")
            else:
                self.label_supposed_time_in.config(text="Supposed Time In: --:-- --")

            # Recompute or clear calculations
            self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")
            self.label_morning_late.config(text="Late: 0 minutes")
            self.label_morning_late_deduction.config(text="Late Deduction: 0.000")
            self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
            self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
            self.label_deductions.config(text="Total Deduction Points: 0.000")

            self.populate_history()
            logging.info(f"Date changed to {self.selected_date}")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date selected.\n{e}")
            logging.error(f"Error on date change: {e}")

    def update_days(self, event):
        """
        Update the days Combobox based on selected month and year.
        """
        try:
            year = int(self.year_var.get())
            month = list(calendar.month_name).index(self.month_var.get())
            num_days = calendar.monthrange(year, month)[1]
            days = [str(day) for day in range(1, num_days + 1)]
            self.day_combo['values'] = days
            if int(self.day_var.get()) > num_days:
                self.day_var.set(str(num_days))
        except Exception as e:
            logging.error(f"Error updating days: {e}")

    def update_search_from_days(self, event):
        """
        Update the 'From' days Combobox based on selected month and year in search.
        """
        try:
            year = int(self.search_from_year_var.get())
            month = list(calendar.month_name).index(self.search_from_month_var.get())
            num_days = calendar.monthrange(year, month)[1]
            days = [str(day) for day in range(1, num_days + 1)]
            self.search_from_day['values'] = days
            if int(self.search_from_day_var.get()) > num_days:
                self.search_from_day_var.set(str(num_days))
        except Exception as e:
            logging.error(f"Error updating search from days: {e}")

    def update_search_to_days(self, event):
        """
        Update the 'To' days Combobox based on selected month and year in search.
        """
        try:
            year = int(self.search_to_year_var.get())
            month = list(calendar.month_name).index(self.search_to_month_var.get())
            num_days = calendar.monthrange(year, month)[1]
            days = [str(day) for day in range(1, num_days + 1)]
            self.search_to_day['values'] = days
            if int(self.search_to_day_var.get()) > num_days:
                self.search_to_day_var.set(str(num_days))
        except Exception as e:
            logging.error(f"Error updating search to days: {e}")

    def parse_time_input(self, attr_name):
        """
        Parse time from the time entry fields.
        Combines hours, minutes, and AM/PM from separate entries.
        """
        hour_var = getattr(self, f'{attr_name}_hour_var')
        minute_var = getattr(self, f'{attr_name}_minute_var')
        ampm_var = getattr(self, f'{attr_name}_ampm_var')

        time_str = f"{hour_var.get()}:{minute_var.get()} {ampm_var.get()}"
        try:
            return datetime.strptime(time_str, "%I:%M %p").time()
        except ValueError:
            return None

    def calculate_time_difference(self, earlier_time, later_time):
        """
        Returns the difference in minutes (int) between two times:
        (later_time - earlier_time). If the difference is negative,
        it will be a negative int. The caller decides whether to clamp to 0.
        """
        dt1 = datetime.combine(self.selected_date, earlier_time)
        dt2 = datetime.combine(self.selected_date, later_time)
        delta_minutes = (dt2 - dt1).total_seconds() // 60
        return int(delta_minutes)

    def calculate_deductions(self):
        """
        Calculate deduction points based on input times.
        Now calculates Late Minutes (Morning) and Undertime Minutes (Afternoon).
        Corrects negative differences to 0 for Late/Undertime.
        """
        # Parse Actual Time In
        morning_actual_time_in = self.parse_time_input("morning_actual_time_in")
        if not morning_actual_time_in:
            messagebox.showerror("Input Error", "Please enter a valid Actual Time In for Morning.")
            logging.warning("Invalid Actual Time In for Morning.")
            return

        # Get Supposed Time In
        supposed_time_in_str = self.label_supposed_time_in.cget("text").split(": ", 1)[1]
        try:
            supposed_time_in = datetime.strptime(supposed_time_in_str, "%I:%M %p").time()
        except ValueError:
            supposed_time_in = None

        if not supposed_time_in:
            messagebox.showerror("Error", "Supposed Time In is not set for the selected day.")
            logging.error("Supposed Time In is not set.")
            return

        # Calculate raw late minutes
        late_minutes_raw = self.calculate_time_difference(supposed_time_in, morning_actual_time_in)
        # If negative or zero => not late
        late_minutes_display = max(0, late_minutes_raw)
        self.label_morning_late.config(text=f"Late: {late_minutes_display} minutes")

        # Late Deduction (in fraction of day)
        late_deduction = convert_time_diff_to_day_fraction(late_minutes_display // 60, late_minutes_display % 60)
        self.label_morning_late_deduction.config(text=f"Late Deduction: {late_deduction:.3f}")

        # Calculate Supposed Time Out (Actual Time In + 8 hours)
        morning_datetime = datetime.combine(self.selected_date, morning_actual_time_in)
        supposed_time_out_datetime = morning_datetime + timedelta(hours=8)
        supposed_time_out = supposed_time_out_datetime.time()
        self.label_supposed_time_out.config(text=f"Supposed Time Out: {supposed_time_out.strftime('%I:%M %p')}")

        # Parse Actual Time Out
        afternoon_actual_time_out = self.parse_time_input("afternoon_actual_time_out")

        # If no afternoon time out is provided, set undertime to 0
        if afternoon_actual_time_out:
            # Calculate raw undertime minutes = (supposed_time_out - actual_time_out)
            undertime_minutes_raw = self.calculate_time_difference(afternoon_actual_time_out, supposed_time_out)
            # We want a positive difference only if actual_time_out is earlier => so reverse:
            # Correct approach: difference = supposed_time_out - actual_time_out
            # But we are calling (afternoon_actual_time_out, supposed_time_out),
            # so if user is out later => negative => clamp to 0
            undertime_minutes_display = max(0, self.calculate_time_difference(afternoon_actual_time_out, supposed_time_out))
        else:
            undertime_minutes_display = 0

        self.label_afternoon_undertime.config(text=f"Undertime: {undertime_minutes_display} minutes")

        # Undertime Deduction
        undertime_deduction = convert_time_diff_to_day_fraction(
            undertime_minutes_display // 60, 
            undertime_minutes_display % 60
        )
        self.label_afternoon_undertime_deduction.config(text=f"Undertime Deduction: {undertime_deduction:.3f}")

        # Calculate Total Deduction Points
        total_deduction = round(late_deduction + undertime_deduction, 3)
        self.label_deductions.config(text=f"Total Deduction Points: {total_deduction}")
        logging.info(
            f"Calculated Deductions - Late: {late_minutes_display} min => {late_deduction}, "
            f"Undertime: {undertime_minutes_display} min => {undertime_deduction}, "
            f"Total: {total_deduction}."
        )

    def clear_morning(self):
        """
        Clear the Morning inputs and related displays.
        """
        getattr(self, 'morning_actual_time_in_hour_var').set('00')
        getattr(self, 'morning_actual_time_in_minute_var').set('00')
        getattr(self, 'morning_actual_time_in_ampm_var').set('AM')
        self.label_morning_late.config(text="Late: 0 minutes")
        self.label_morning_late_deduction.config(text="Late Deduction: 0.000")
        self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")
        self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
        self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
        self.label_deductions.config(text="Total Deduction Points: 0.000")
        logging.info("Cleared Morning inputs.")

    def clear_afternoon(self):
        """
        Clear the Afternoon inputs and related displays.
        """
        getattr(self, 'afternoon_actual_time_out_hour_var').set('00')
        getattr(self, 'afternoon_actual_time_out_minute_var').set('00')
        getattr(self, 'afternoon_actual_time_out_ampm_var').set('PM')
        self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
        self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
        self.label_deductions.config(text="Total Deduction Points: 0.000")
        logging.info("Cleared Afternoon inputs.")

    def toggle_fullscreen(self):
        """
        Toggle full-screen mode.
        """
        self.fullscreen = not self.fullscreen
        self.master.attributes("-fullscreen", self.fullscreen)
        if self.fullscreen:
            self.button_fullscreen.config(text="Windowed Mode")
            logging.info("Entered full-screen mode.")
        else:
            self.button_fullscreen.config(text="Full Screen")
            logging.info("Exited full-screen mode.")

    def save_record(self):
        """
        Save the current day's deduction record.
        """
        deduction_text = self.label_deductions.cget("text")
        try:
            deduction_points = float(deduction_text.split(":")[1].strip())
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Unable to parse deduction points.")
            logging.error("Failed to parse deduction points for saving.")
            return

        if deduction_points == 0.0:
            # It's possible the user wants to save 0.0 deduction, but the old logic
            # was to check if it's worth saving. We'll keep the prompt as is.
            messagebox.showinfo("No Deductions", "No deductions to save for today.")
            logging.info("No deductions to save.")
            return

        date_str = self.selected_date.strftime("%Y-%m-%d")

        # Retrieve additional fields
        morning_time_in = (
            getattr(self, 'morning_actual_time_in_hour_var').get().zfill(2) + ":" +
            getattr(self, 'morning_actual_time_in_minute_var').get().zfill(2) + " " +
            getattr(self, 'morning_actual_time_in_ampm_var').get()
        )
        supposed_time_in = self.label_supposed_time_in.cget("text").split(": ", 1)[1]

        supposed_time_out = self.label_supposed_time_out.cget("text").split(": ", 1)[1]

        afternoon_actual_time_out = (
            getattr(self, 'afternoon_actual_time_out_hour_var').get().zfill(2) + ":" +
            getattr(self, 'afternoon_actual_time_out_minute_var').get().zfill(2) + " " +
            getattr(self, 'afternoon_actual_time_out_ampm_var').get()
        )

        late_minutes = int(self.label_morning_late.cget("text").split(":")[1].strip().split()[0])
        undertime_minutes = int(self.label_afternoon_undertime.cget("text").split(":")[1].strip().split()[0])

        new_record = {
            "date": date_str,
            "morning_actual_time_in": morning_time_in,
            "supposed_time_in": supposed_time_in,
            "late_minutes": late_minutes,
            "afternoon_actual_time_out": afternoon_actual_time_out,
            "supposed_time_out": supposed_time_out,
            "undertime_minutes": undertime_minutes,
            "deduction_points": deduction_points
        }

        # Check for existing records on the same date
        existing_records = [record for record in self.records if record["date"] == date_str]
        if existing_records:
            add_record = messagebox.askyesno(
                "Add Record",
                f"A record for {date_str} already exists.\nDo you want to add another record for this date?"
            )
            if not add_record:
                logging.info(f"User chose not to add another record for {date_str}.")
                return

        self.records.append(new_record)
        self.save_records_to_file()
        messagebox.showinfo("Success", f"Record for {date_str} saved successfully.")
        logging.info(f"Record saved for {date_str}: {deduction_points} points.")
        self.populate_history()

    def export_history(self):
        """
        Export the deduction history to a CSV file.
        """
        if not self.records:
            messagebox.showinfo("No Data", "There are no records to export.")
            logging.info("Export attempted with no records.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save History as CSV"
        )
        if not file_path:
            return  # User cancelled the save dialog

        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                # Write header
                writer.writerow([
                    "Date",
                    "Morning Actual Time In",
                    "Supposed Time In",
                    "Late Minutes",
                    "Afternoon Actual Time Out",
                    "Supposed Time Out",
                    "Undertime Minutes",
                    "Deduction Points"
                ])
                for record in sorted(self.records, key=lambda x: x["date"]):
                    writer.writerow([
                        record["date"],
                        record.get("morning_actual_time_in", "--:-- --"),
                        record.get("supposed_time_in", "--:-- --"),
                        record.get("late_minutes", 0),
                        record.get("afternoon_actual_time_out", "--:-- --"),
                        record.get("supposed_time_out", "--:-- --"),
                        record.get("undertime_minutes", 0),
                        record["deduction_points"]
                    ])
            messagebox.showinfo("Export Successful", f"History exported to {file_path}")
            logging.info(f"History exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred while exporting:\n{e}")
            logging.error(f"Failed to export history: {e}")

    def edit_record(self):
        """
        Edit the selected record from the history.
        """
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a record to edit.")
            logging.warning("Edit attempted without selecting a record.")
            return

        values = self.history_tree.item(selected_item, 'values')
        date_str = values[0]
        current_deduction = float(values[7])

        # Find the matching record (assumes unique date & deduction points)
        for record in self.records:
            if record["date"] == date_str and record["deduction_points"] == current_deduction:
                break
        else:
            messagebox.showerror("Error", "Selected record not found.")
            logging.error("Selected record not found during edit.")
            return

        # Prompt user to edit deduction points
        new_deduction = simpledialog.askfloat(
            "Edit Deduction",
            f"Enter new deduction points for {date_str}:",
            initialvalue=float(current_deduction),
            minvalue=0.0
        )
        if new_deduction is not None:
            record["deduction_points"] = round(new_deduction, 3)
            self.save_records_to_file()
            self.populate_history()
            messagebox.showinfo("Success", f"Record for {date_str} updated successfully.")
            logging.info(f"Record updated for {date_str}: {new_deduction} points.")

    def delete_record(self):
        """
        Delete the selected record from the history.
        """
        selected_item = self.history_tree.selection()
        if not selected_item:
            messagebox.showwarning("No Selection", "Please select a record to delete.")
            logging.warning("Delete attempted without selecting a record.")
            return

        values = self.history_tree.item(selected_item, 'values')
        date_str = values[0]
        deduction = float(values[7])

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the record for {date_str} with {deduction} deduction points?"
        )
        if confirm:
            for i, record in enumerate(self.records):
                if record["date"] == date_str and record["deduction_points"] == deduction:
                    del self.records[i]
                    break
            else:
                messagebox.showerror("Error", "Selected record not found.")
                logging.error("Selected record not found during deletion.")
                return

            self.save_records_to_file()
            self.populate_history()
            messagebox.showinfo("Deleted", f"Record for {date_str} has been deleted.")
            logging.info(f"Record deleted for {date_str}.")

    def show_context_menu(self, event):
        """
        Show context menu on right-click in the history Treeview.
        """
        selected_item = self.history_tree.identify_row(event.y)
        if selected_item:
            self.history_tree.selection_set(selected_item)
            self.context_menu.post(event.x_root, event.y_root)

    def search_history(self):
        """
        Search records within the selected date range.
        """
        try:
            from_year = int(self.search_from_year_var.get())
            from_month = list(calendar.month_name).index(self.search_from_month_var.get())
            from_day = int(self.search_from_day_var.get())
            from_date = datetime(from_year, from_month, from_day).date()

            to_year = int(self.search_to_year_var.get())
            to_month = list(calendar.month_name).index(self.search_to_month_var.get())
            to_day = int(self.search_to_day_var.get())
            to_date = datetime(to_year, to_month, to_day).date()

            if from_date > to_date:
                messagebox.showerror("Invalid Range", "From date cannot be after To date.")
                logging.warning("Invalid search date range.")
                return

            filtered_records = [
                record for record in self.records
                if from_date <= datetime.strptime(record["date"], "%Y-%m-%d").date() <= to_date
            ]
            self.populate_history(filtered_records)
            logging.info(f"Searched records from {from_date} to {to_date}.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please ensure all search dates are selected correctly.\n{e}")
            logging.error(f"Error in search input: {e}")

    def enter_key_pressed(self, event):
        """
        Event handler for Enter key press to trigger calculation.
        """
        self.calculate_deductions()

    # ----------------------------
    # File Handling Methods
    # ----------------------------

    def load_records(self):
        """
        Load records from the JSON data file.
        Ensures that records are a list of dictionaries with 'date' and 'deduction_points' (plus extras).
        """
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)

                if isinstance(data, dict):
                    # Convert dict to list of dicts
                    records = [{"date": date, "deduction_points": ded} for date, ded in data.items()]
                    self.records = records
                    self.save_records_to_file()  # Save the converted data
                    logging.info("Converted existing records from dict to list format.")
                elif isinstance(data, list):
                    # Validate each record
                    valid_records = []
                    for record in data:
                        if isinstance(record, dict) and "date" in record and "deduction_points" in record:
                            # Ensure required fields are present
                            record.setdefault("morning_actual_time_in", "--:-- --")
                            record.setdefault("supposed_time_in", "--:-- --")
                            record.setdefault("late_minutes", 0)
                            record.setdefault("afternoon_actual_time_out", "--:-- --")
                            record.setdefault("supposed_time_out", "--:-- --")
                            record.setdefault("undertime_minutes", 0)
                            valid_records.append(record)
                        else:
                            logging.warning(f"Ignored invalid record format: {record}")
                    self.records = valid_records
                    logging.info("Loaded records as list of dictionaries.")
                else:
                    self.records = []
                    logging.warning("Unknown data format. Starting with empty records.")

                return self.records
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Failed to load records: {e}")
                logging.error(f"JSON decode error: {e}")
                return []
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while loading records:\n{e}")
                logging.error(f"Error loading records: {e}")
                return []
        else:
            logging.info("No existing records found. Starting fresh.")
            return []

    def save_records_to_file(self):
        """
        Save records to the JSON data file (list of dictionaries format).
        """
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.records, f, indent=4)
            logging.info("Records saved successfully as list of dictionaries.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save records: {e}")
            logging.error(f"Error saving records: {e}")

    # ----------------------------
    # History Management Methods
    # ----------------------------

    def populate_history(self, records=None):
        """
        Populate the history Treeview with records.
        If records is None, use all records.
        """
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        records_to_show = records if records is not None else self.records

        for record in sorted(records_to_show, key=lambda x: x["date"]):
            self.history_tree.insert("", "end", values=(
                record["date"],
                record.get("morning_actual_time_in", "--:-- --"),
                record.get("supposed_time_in", "--:-- --"),
                record.get("late_minutes", 0),
                record.get("afternoon_actual_time_out", "--:-- --"),
                record.get("supposed_time_out", "--:-- --"),
                record.get("undertime_minutes", 0),
                record["deduction_points"]
            ))
        logging.info("History populated in Treeview.")

    # ----------------------------
    # Theme Management Methods
    # ----------------------------

    def change_theme(self, theme_name):
        """
        Change the application's theme.
        Adjust font colors based on the selected theme.
        """
        self.style.theme_use(theme_name)
        self.current_theme = theme_name
        logging.info(f"Theme changed to {theme_name}.")

        # Adjust font colors based on theme
        if theme_name in ['superhero', 'darkly', 'cyborg', 'slate']:
            self.set_dark_mode_fonts()
        else:
            self.set_light_mode_fonts()

    def set_dark_mode_fonts(self):
        """
        Set font colors to white for better visibility in dark modes.
        """
        for widget in self.master.winfo_children():
            self.set_widget_foreground(widget, 'white')

    def set_light_mode_fonts(self):
        """
        Set font colors to default (black) for light modes.
        """
        for widget in self.master.winfo_children():
            self.set_widget_foreground(widget, 'black')

    def set_widget_foreground(self, widget, color):
        """
        Recursively set the foreground color of labels and other text widgets.
        """
        if isinstance(widget, ttk.Label) or isinstance(widget, tk.Label):
            widget.config(foreground=color)
        for child in widget.winfo_children():
            self.set_widget_foreground(child, color)

    # ----------------------------
    # Help and About Dialogs
    # ----------------------------

    def show_help_dialog(self):
        """
        Display the How to Use dialog with enhanced design and detailed information.
        """
        help_window = tk.Toplevel(self.master)
        help_window.title("How to Use - Daily Time Record")
        help_window.grab_set()  # Make the dialog modal

        help_window.geometry("700x500")
        self.center_child_window(help_window)

        notebook = ttk.Notebook(help_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 1: Overview
        tab_overview = ttk.Frame(notebook)
        notebook.add(tab_overview, text="Overview")

        overview_content = """\
Daily Time Record (DTR) Application - Overview

The DTR application is designed to help you efficiently track your daily work hours, 
calculate deductions based on lateness and undertime, and maintain a comprehensive 
history of your records. This tool provides essential functionalities to streamline 
the time-logging process.

Key Features:
- Date Selection: Easily select dates to log your time records.
- Time Entry: Input your morning and afternoon check-in/out times.
- Deduction Calculation: Automatically calculate deductions for late/undertime.
- Record Saving and Exporting: Save your records and export them as CSV.
- Theme Customization: Switch between light and dark modes for convenience.
- Full-Screen Mode: Toggle full-screen mode as desired.
"""
        label_overview = tk.Text(tab_overview, wrap="word", font=("Inter", 12), bg=help_window.cget("bg"), borderwidth=0)
        label_overview.insert("1.0", overview_content)
        label_overview.config(state="disabled")
        label_overview.pack(fill="both", expand=True, padx=10, pady=10)

        # Tab 2: Step-by-Step Guide
        tab_guide = ttk.Frame(notebook)
        notebook.add(tab_guide, text="Step-by-Step Guide")

        guide_content = """\
Step-by-Step Guide

1. Selecting a Date:
   - Use the dropdowns at the top to select the desired year, month, and day.
   - The application will display the corresponding day of the week 
     and update the "Supposed Time In" automatically.

2. Entering Time Records:
   - Morning:
     - Supposed Time In: Automatically displayed based on the selected weekday.
     - Actual Time In: Enter your actual check-in time using the provided fields or the time picker.
   - Afternoon:
     - Supposed Time Out: Automatically calculated as Actual Time In + 8 hours.
     - Actual Time Out: Enter your actual check-out time.

3. Calculating Deductions:
   - Click "Calculate Deductions" or press Enter.
   - The application displays the Late/Undertime minutes and corresponding fraction-of-a-day deduction.

4. Saving and Exporting:
   - Click "Save Record" to store your daily entry. You can add multiple records for the same date if needed.
   - Click "Export History" to export all records to a CSV file.

5. Viewing and Managing History:
   - Use the "Deduction History" section to see all records. 
   - Right-click on a record to "Edit" or "Delete."
   - Use the search filters at the top to narrow down date ranges.

6. Customizing Appearance:
   - Switch between "Light Mode" and "Dark Mode" using the top-right buttons.
   - Use "Full Screen" to toggle between windowed and full-screen mode.
"""
        label_guide = tk.Text(tab_guide, wrap="word", font=("Inter", 12), bg=help_window.cget("bg"), borderwidth=0)
        label_guide.insert("1.0", guide_content)
        label_guide.config(state="disabled")
        label_guide.pack(fill="both", expand=True, padx=10, pady=10)

        # More tabs (FAQs, Tips, etc.) can follow similarly...

        # Adjust font colors based on current theme
        if self.current_theme in ['superhero', 'darkly', 'cyborg', 'slate']:
            label_overview.config(fg="white")
            label_guide.config(fg="white")
        else:
            label_overview.config(fg="black")
            label_guide.config(fg="black")

    def show_about_dialog(self):
        """
        Display the About dialog with enhanced design and detailed information.
        """
        about_window = tk.Toplevel(self.master)
        about_window.title("About - Daily Time Record")
        about_window.grab_set()  # Make the dialog modal

        about_window.geometry("500x400")
        self.center_child_window(about_window)

        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill="both", expand=True)

        about_content = """\
Daily Time Record (DTR) Application

Version: 2.0
Release Date: January 24, 2025

Developed By: KCprsnlcc

Purpose:
This application simplifies tracking daily work hours, 
calculating deductions for lateness/undertime, 
and maintaining a comprehensive record history.

Acknowledgments:
- Tkinter and ttkbootstrap for UI components.
- Open-source community for continuous support.

Contact Information:
Email: kcpersonalacc@gmail.com
GitHub: https://github.com/KCprsnlcc
Facebook: https://facebook.com/Daff.Sulaiman/

Disclaimer:
While every effort has been made to ensure reliability, 
the developers are not liable for discrepancies arising from use.
Users are encouraged to back up data regularly.
"""
        label_about = tk.Text(frame, wrap="word", font=("Inter", 12), bg=about_window.cget("bg"), borderwidth=0)
        label_about.insert("1.0", about_content)
        label_about.config(state="disabled")
        label_about.pack(fill="both", expand=True)

        if self.current_theme in ['superhero', 'darkly', 'cyborg', 'slate']:
            label_about.config(fg="white")
        else:
            label_about.config(fg="black")

    def center_child_window(self, child):
        """
        Center a child window relative to the main application window.
        """
        self.master.update_idletasks()
        parent_x = self.master.winfo_rootx()
        parent_y = self.master.winfo_rooty()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()

        child.update_idletasks()
        child_width = child.winfo_width()
        child_height = child.winfo_height()

        pos_x = parent_x + (parent_width // 2) - (child_width // 2)
        pos_y = parent_y + (parent_height // 2) - (child_height // 2)
        child.geometry(f"+{pos_x}+{pos_y}")

# ============================
# Application Entry Point
# ============================

def main():
    setup_logging()
    logging.info("Application started.")
    root = tk.Tk()
    app = DailyTimeRecordApp(root)
    root.mainloop()
    logging.info("Application closed.")

if __name__ == "__main__":
    main()
