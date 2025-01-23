import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import ttkbootstrap as ttkb  # Import ttkbootstrap with alias to differentiate
from ttkbootstrap import Style
from datetime import datetime, time
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

# Time conversion dictionaries
MINUTES_TO_DAY = {i: round(0.002 * i, 3) for i in range(61)}
HOURS_TO_DAY = {i: round(0.125 * i, 3) for i in range(1, 9)}

# Allowed time configurations per weekday
ALLOWED_TIMES = {
    "Monday": {
        "morning_in": time(8, 15),
        "morning_out": time(12, 1),
        "afternoon_in": time(13, 0),
        "afternoon_out": time(17, 30)
    },
    "Tuesday": {
        "morning_in": time(8, 30),
        "morning_out": time(12, 1),
        "afternoon_in": time(13, 0),
        "afternoon_out": time(17, 30)
    },
    "Wednesday": {
        "morning_in": time(8, 30),
        "morning_out": time(12, 1),
        "afternoon_in": time(13, 0),
        "afternoon_out": time(17, 30)
    },
    "Thursday": {
        "morning_in": time(8, 30),
        "morning_out": time(12, 1),
        "afternoon_in": time(13, 0),
        "afternoon_out": time(17, 30)
    },
    "Friday": {
        "morning_in": time(8, 30),
        "morning_out": time(12, 1),
        "afternoon_in": time(13, 0),
        "afternoon_out": time(17, 30)
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
        # Calculate position
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 20
        # Create tooltip window
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{x}+{y}")
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
    """
    def __init__(self, parent, initial_time=None, title="Select Time"):
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

        # Set a fixed size and center the window
        window_width = 800
        window_height = 900
        master.geometry(f"{window_width}x{window_height}")
        master.resizable(False, False)
        self.center_window(window_width, window_height)

        # Initialize style with ttkbootstrap
        self.style = Style(theme='flatly')  # default to 'flatly' (light theme)
        self.current_theme = 'flatly'

        # Load existing records
        self.records = self.load_records()

        # Current Date and Day
        self.selected_date = datetime.now().date()
        self.current_day = self.selected_date.strftime("%A")

        # Setup UI Components
        self.setup_header()
        self.setup_time_inputs()
        self.setup_controls()
        self.setup_history()

    # ----------------------------
    # Window Setup Methods
    # ----------------------------

    def center_window(self, width, height):
        """
        Center the window on the screen.
        """
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.master.geometry(f"{width}x{height}+{x}+{y}")

    def setup_header(self):
        """
        Setup the header section with Date Selection and Day Label.
        """
        header_frame = ttkb.Frame(self.master)
        header_frame.pack(fill="x", pady=10, padx=10)

        # Labels frame (left side) using standard ttk
        labels_frame = ttk.Frame(header_frame)
        labels_frame.pack(side="left")

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
        self.year_combo.grid(row=0, column=1, padx=5, pady=2)
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
        self.month_combo.grid(row=0, column=3, padx=5, pady=2)
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
        self.day_combo.grid(row=0, column=5, padx=5, pady=2)
        self.day_combo.set(str(self.selected_date.day))
        self.day_combo.bind("<<ComboboxSelected>>", self.on_date_change)

        Tooltip(self.year_combo, "Select Year")
        Tooltip(self.month_combo, "Select Month")
        Tooltip(self.day_combo, "Select Day")

        # Label for Day of the Week
        self.label_day = ttk.Label(labels_frame, text=f"Day: {self.current_day}", font=("Arial", 16))
        self.label_day.pack(pady=5, anchor="w")

        # Theme Toggle Buttons (right side) using ttkbootstrap
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

    def setup_time_inputs(self):
        """
        Setup the Morning and Afternoon time input sections.
        """
        # Frame for Morning Inputs using ttkbootstrap
        self.frame_morning = ttkb.LabelFrame(self.master, text="Morning", padding=10)
        self.frame_morning.pack(padx=10, pady=10, fill="x")

        self.create_time_input(self.frame_morning, "Time In:", "morning_in")
        self.create_time_input(self.frame_morning, "Time Out:", "morning_out")

        # Frame for Afternoon Inputs using ttkbootstrap
        self.frame_afternoon = ttkb.LabelFrame(self.master, text="Afternoon", padding=10)
        self.frame_afternoon.pack(padx=10, pady=10, fill="x")

        self.create_time_input(self.frame_afternoon, "Time In:", "afternoon_in")
        self.create_time_input(self.frame_afternoon, "Time Out:", "afternoon_out")

    def setup_controls(self):
        """
        Setup controls such as Half Day checkbox, Calculate button, Deduction display, Save, and Export buttons.
        """
        # Half Day Checkbox using standard ttk
        self.half_day_var = tk.IntVar()
        self.checkbox_half_day = ttk.Checkbutton(
            self.master,
            text="Half Day",
            variable=self.half_day_var,
            command=self.toggle_half_day
        )
        self.checkbox_half_day.pack(pady=10)
        Tooltip(self.checkbox_half_day, "Check if it's a half day")

        # Control Buttons Frame using ttkbootstrap
        controls_frame = ttkb.Frame(self.master)
        controls_frame.pack(pady=10)

        # Calculate Button
        self.button_calculate = ttkb.Button(
            controls_frame,
            text="Calculate Deductions",
            command=self.calculate_deductions,
            bootstyle="success"
        )
        self.button_calculate.pack(side="left", padx=5)
        Tooltip(self.button_calculate, "Calculate deduction points based on input times")

        # Save Record Button
        self.button_save = ttkb.Button(
            controls_frame,
            text="Save Record",
            command=self.save_record,
            bootstyle="info"
        )
        self.button_save.pack(side="left", padx=5)
        Tooltip(self.button_save, "Save the current day's record")

        # Export History Button
        self.button_export = ttkb.Button(
            controls_frame,
            text="Export History",
            command=self.export_history,
            bootstyle="warning"
        )
        self.button_export.pack(side="left", padx=5)
        Tooltip(self.button_export, "Export deduction history to CSV")

        # Deduction Points Display using standard ttk
        self.label_deductions = ttk.Label(self.master, text="Total Deduction Points: 0.000", font=("Arial", 14))
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
        self.history_tree = ttk.Treeview(history_frame, columns=("Date", "Deduction Points"), show='headings', selectmode="browse")
        self.history_tree.heading("Date", text="Date")
        self.history_tree.heading("Deduction Points", text="Deduction Points")
        self.history_tree.pack(fill="both", expand=True)

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

    def create_time_input(self, parent, label_text, attr_name):
        """
        Create a time input section with label, entry, and select button.
        """
        frame = ttkb.Frame(parent)
        frame.pack(fill="x", pady=5)

        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side="left", padx=5)

        # Entry to display and input time using standard ttk
        time_var = tk.StringVar(value='--:-- --')
        time_entry = ttk.Entry(frame, textvariable=time_var, width=10)
        time_entry.pack(side="left", padx=2)
        Tooltip(time_entry, "Enter time manually or click 'Select Time' to choose.")

        def open_time_picker():
            current_time_str = time_var.get()
            try:
                current_time = datetime.strptime(current_time_str, "%I:%M %p").time()
            except ValueError:
                current_time = None  # If invalid or default, start with None
            picker = TimePickerDialog(self.master, initial_time=current_time, title=f"Select {label_text.strip(':')}")
            selected_time = picker.show()
            if selected_time:
                time_var.set(selected_time.strftime("%I:%M %p"))

        # Button to open Time Picker Dialog using ttkbootstrap
        time_button = ttkb.Button(frame, text="Select Time", command=open_time_picker)
        time_button.pack(side="left", padx=2)
        Tooltip(time_button, "Open time picker")

        # Set attributes for later access
        setattr(self, f'{attr_name}_var', time_var)

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

    def parse_time(self, time_var):
        """
        Parse time from the time entry.
        """
        time_str = time_var.get()
        try:
            return datetime.strptime(time_str, "%I:%M %p").time()
        except ValueError:
            return None

    def calculate_deductions(self):
        """
        Calculate deduction points based on input times and half-day selection.
        """
        # Get inputs
        morning_in = self.parse_time(self.morning_in_var) if hasattr(self, 'morning_in_var') else None
        morning_out = self.parse_time(self.morning_out_var) if hasattr(self, 'morning_out_var') else None
        afternoon_in = self.parse_time(self.afternoon_in_var) if hasattr(self, 'afternoon_in_var') else None
        afternoon_out = self.parse_time(self.afternoon_out_var) if hasattr(self, 'afternoon_out_var') else None
        half_day = self.half_day_var.get()

        # Validation
        if not half_day:
            if not all([morning_in, morning_out, afternoon_in, afternoon_out]):
                messagebox.showerror("Input Error", "Please fill all time fields or select Half Day.")
                logging.warning("Incomplete time fields for full day.")
                return
        else:
            morning_filled = (morning_in and morning_out)
            afternoon_filled = (afternoon_in and afternoon_out)
            if not (morning_filled or afternoon_filled):
                messagebox.showerror("Input Error", "For Half Day, fill either Morning or Afternoon fields.")
                logging.warning("No time fields filled for half day.")
                return

        total_deduction = 0.0

        # Define allowed times
        allowed = ALLOWED_TIMES.get(self.current_day)
        if not allowed:
            messagebox.showinfo("Info", "Today is not a working day.")
            self.label_deductions.config(text="Total Deduction Points: 0.000")
            logging.info(f"Non-working day selected: {self.current_day}")
            return

        def compute_time_diff(later_time, earlier_time):
            delta = datetime.combine(datetime.today(), later_time) - datetime.combine(datetime.today(), earlier_time)
            minutes_diff = delta.seconds // 60
            h = minutes_diff // 60
            m = minutes_diff % 60
            return convert_time_diff_to_day_fraction(h, m)

        if not half_day:
            # Morning Lateness
            if morning_in > allowed["morning_in"]:
                deduction = compute_time_diff(morning_in, allowed["morning_in"])
                total_deduction += deduction
                logging.info(f"Morning lateness: {deduction} points")

            # Morning Undertime
            if morning_out < allowed["morning_out"]:
                deduction = compute_time_diff(allowed["morning_out"], morning_out)
                total_deduction += deduction
                logging.info(f"Morning undertime: {deduction} points")

            # Afternoon Lateness
            if afternoon_in > allowed["afternoon_in"]:
                deduction = compute_time_diff(afternoon_in, allowed["afternoon_in"])
                total_deduction += deduction
                logging.info(f"Afternoon lateness: {deduction} points")

            # Afternoon Undertime
            if afternoon_out < allowed["afternoon_out"]:
                deduction = compute_time_diff(allowed["afternoon_out"], afternoon_out)
                total_deduction += deduction
                logging.info(f"Afternoon undertime: {deduction} points")
        else:
            # Half Day logic
            if morning_in and morning_out:
                # Morning Lateness and Undertime
                if morning_in > allowed["morning_in"]:
                    deduction = compute_time_diff(morning_in, allowed["morning_in"])
                    total_deduction += deduction
                    logging.info(f"Half Day Morning lateness: {deduction} points")
                if morning_out < allowed["morning_out"]:
                    deduction = compute_time_diff(allowed["morning_out"], morning_out)
                    total_deduction += deduction
                    logging.info(f"Half Day Morning undertime: {deduction} points")

                # Deduct 4 hours for absent in the afternoon
                total_deduction += HOURS_TO_DAY.get(4, 0.5)
                logging.info(f"Half Day afternoon absence: {HOURS_TO_DAY.get(4, 0.5)} points")
            elif afternoon_in and afternoon_out:
                # Afternoon Lateness and Undertime
                if afternoon_in > allowed["afternoon_in"]:
                    deduction = compute_time_diff(afternoon_in, allowed["afternoon_in"])
                    total_deduction += deduction
                    logging.info(f"Half Day Afternoon lateness: {deduction} points")
                if afternoon_out < allowed["afternoon_out"]:
                    deduction = compute_time_diff(allowed["afternoon_out"], afternoon_out)
                    total_deduction += deduction
                    logging.info(f"Half Day Afternoon undertime: {deduction} points")

                # Deduct 4 hours for absent in the morning
                total_deduction += HOURS_TO_DAY.get(4, 0.5)
                logging.info(f"Half Day morning absence: {HOURS_TO_DAY.get(4, 0.5)} points")

        total_deduction = round(total_deduction, 3)
        self.label_deductions.config(text=f"Total Deduction Points: {total_deduction}")
        logging.info(f"Total deduction calculated: {total_deduction} points")

    def toggle_half_day(self):
        """
        Toggle the Half Day selection.
        """
        if self.half_day_var.get():
            logging.info("Half Day selected.")
            # Optionally, disable one set of time inputs or provide additional UI cues
            # For simplicity, logic is handled during calculation
        else:
            logging.info("Full Day selected.")
            # Re-enable all time inputs if they were disabled
            # Currently, no disabling is implemented

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
            messagebox.showinfo("No Deductions", "No deductions to save for today.")
            logging.info("No deductions to save.")
            return

        date_str = self.selected_date.strftime("%Y-%m-%d")

        # Create a new record
        new_record = {
            "date": date_str,
            "deduction_points": deduction_points
        }

        # Check for existing records on the same date
        existing_records = [record for record in self.records if record["date"] == date_str]
        if existing_records:
            add_record = messagebox.askyesno("Add Record",
                                             f"A record for {date_str} already exists.\nDo you want to add another record for this date?")
            if not add_record:
                logging.info(f"User chose not to add another record for {date_str}.")
                return

        # Append the new record
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
                writer.writerow(["Date", "Deduction Points"])
                for record in sorted(self.records, key=lambda x: x["date"]):
                    writer.writerow([record["date"], record["deduction_points"]])
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

        date_str, current_deduction = self.history_tree.item(selected_item, 'values')
        # Find the first matching record
        for record in self.records:
            if record["date"] == date_str and str(record["deduction_points"]) == current_deduction:
                break
        else:
            messagebox.showerror("Error", "Selected record not found.")
            logging.error("Selected record not found during edit.")
            return

        new_deduction = simpledialog.askfloat("Edit Deduction",
                                              f"Enter new deduction points for {date_str}:",
                                              initialvalue=float(current_deduction),
                                              minvalue=0.0)
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

        date_str, deduction = self.history_tree.item(selected_item, 'values')
        confirm = messagebox.askyesno("Confirm Deletion",
                                      f"Are you sure you want to delete the record for {date_str} with {deduction} deduction points?")
        if confirm:
            # Find and remove the specific record
            for i, record in enumerate(self.records):
                if record["date"] == date_str and str(record["deduction_points"]) == deduction:
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

            filtered_records = [record for record in self.records
                                if from_date <= datetime.strptime(record["date"], "%Y-%m-%d").date() <= to_date]

            self.populate_history(filtered_records)
            logging.info(f"Searched records from {from_date} to {to_date}.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please ensure all search dates are selected correctly.\n{e}")
            logging.error(f"Error in search input: {e}")

    # ----------------------------
    # File Handling Methods
    # ----------------------------

    def load_records(self):
        """
        Load records from the JSON data file.
        Ensures that records are a list of dictionaries with 'date' and 'deduction_points'.
        If the existing data is a dictionary, it converts it to the new format.
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
        Save records to the JSON data file.
        Ensures that records are saved as a list of dictionaries.
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
            self.history_tree.insert("", "end", values=(record["date"], record["deduction_points"]))
        logging.info("History populated in Treeview.")

    # ----------------------------
    # Theme Management Methods
    # ----------------------------

    def change_theme(self, theme_name):
        """
        Change the application's theme.
        """
        self.style.theme_use(theme_name)
        self.current_theme = theme_name
        logging.info(f"Theme changed to {theme_name}.")

# ============================
# Application Entry Point
# ============================

def main():
    """
    The main entry point for the application.
    """
    setup_logging()
    logging.info("Application started.")
    root = tk.Tk()
    app = DailyTimeRecordApp(root)
    root.mainloop()
    logging.info("Application closed.")

if __name__ == "__main__":
    main()
