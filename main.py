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
    0: 0.0, 1: 0.002, 2: 0.004, 3: 0.006, 4: 0.008, 5: 0.010,
    6: 0.012, 7: 0.015, 8: 0.017, 9: 0.019, 10: 0.021,
    11: 0.023, 12: 0.025, 13: 0.027, 14: 0.029, 15: 0.031,
    16: 0.033, 17: 0.035, 18: 0.037, 19: 0.040, 20: 0.042,
    21: 0.044, 22: 0.046, 23: 0.048, 24: 0.050, 25: 0.052,
    26: 0.054, 27: 0.056, 28: 0.058, 29: 0.060, 30: 0.062,
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

ALLOWED_TIMES = {
    "Monday": {
        "supposed_time_in": time(8, 0)   # 8:00 AM for Monday
    },
    "Tuesday": {
        "supposed_time_in": time(8, 30)  # 8:30 AM for Tue
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

def convert_time_diff_to_day_fraction(hours, minutes):
    """
    Convert hours/minutes difference into a fraction of a day (up to 8 hours).
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

# ---------------------
#     Tooltip Class
# ---------------------
class Tooltip:
    """
    A custom tooltip class for Tkinter widgets that displays above the cursor.
    """
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.move)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def move(self, event):
        self.x = event.x_root
        self.y = event.y_root

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

        # Create the tooltip window
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)  # Remove window decorations
        tw.wm_geometry(f"+{self.x}+{self.y - 20}")  # Position above the cursor (20 px above)

        # Add the label with the tooltip text
        label = ttk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("tahoma", "8", "normal"),
            foreground="#000000"  # Set font color explicitly to black
        )
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None


# ---------------------
#  TimePicker Dialog
# ---------------------
class TimePickerDialog:
    """
    A dialog for selecting time (Hour, Minute, AM/PM) with dropdowns (Combobox).
    Removed overrideredirect so the OS window decorations (including X) are shown.
    """
    def __init__(self, parent, initial_time=None, title="Select Time"):
        self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title(title)

        # Make the dialog modal-like
        self.top.grab_set()

        # Keep it on top in fullscreen mode
        self.top.transient(self.parent)
        self.top.lift()

        self.selected_time = None

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

        # Hour
        ttk.Label(self.top, text="Hour:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.hour_var = tk.StringVar(value=str(hour).zfill(2))
        self.hour_combo = ttk.Combobox(
            self.top,
            textvariable=self.hour_var,
            values=[f"{h:02d}" for h in range(1, 13)],  # 01..12
            state="readonly",
            width=5
        )
        self.hour_combo.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Minute
        ttk.Label(self.top, text="Minute:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.minute_var = tk.StringVar(value=f"{minute:02}")
        self.minute_combo = ttk.Combobox(
            self.top,
            textvariable=self.minute_var,
            values=[f"{m:02d}" for m in range(0, 60)],  # 00..59
            state="readonly",
            width=5
        )
        self.minute_combo.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # AM/PM
        ttk.Label(self.top, text="AM/PM:").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.ampm_var = tk.StringVar(value=ampm)
        self.ampm_combo = ttk.Combobox(
            self.top,
            textvariable=self.ampm_var,
            values=["AM", "PM"],
            state="readonly",
            width=3
        )
        self.ampm_combo.grid(row=2, column=1, padx=10, pady=5, sticky="w")
        self.ampm_combo.current(0 if ampm == "AM" else 1)

        # Buttons
        button_frame = ttk.Frame(self.top)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="OK", command=self.on_ok).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

        self.center_dialog()
        self.top.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def center_dialog(self):
        """
        Center the Toplevel over the parent window.
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
            messagebox.showerror("Invalid Input", "Please enter a valid time.", parent=self.top)

    def on_cancel(self):
        self.top.destroy()

    def show(self):
        self.top.wait_window()
        return self.selected_time


# ---------------------------
#  DailyTimeRecordApp Class
# ---------------------------
class DailyTimeRecordApp:
    """
    The main application class for the Daily Time Record Calculator.
    """
    def __init__(self, master):
        self.master = master
        master.title("Daily Time Record")

        icon_path = "icon.ico"
        if os.path.exists(icon_path):
            master.iconbitmap(icon_path)
        else:
            logging.warning("Icon file not found. Default icon will be used.")

        # <-- CHANGE: Store normal geometry for toggling fullscreen
        self.normal_geometry = None

        master.resizable(True, True)

        # Initialize ttkbootstrap Style
        self.style = Style(theme='flatly')
        self.current_theme = 'flatly'

        # Initialize records
        self.records = self.load_records()
        # Holds the *filtered* records for display in the treeview
        self.current_records = []

        # By default, we display only for the selected date.
        self.search_active = False  # If a date range search is active, this is True.

        self.selected_date = datetime.now().date()
        self.current_day = self.selected_date.strftime("%A")

        self.morning_check = tk.BooleanVar(value=True)
        self.afternoon_check = tk.BooleanVar(value=True)

        # Create the menubar early
        self.menubar = tk.Menu(self.master)
        self.master.config(menu=self.menubar)

        # Apply the initial theme style
        self.apply_apple_calculator_light_style()

        # Setup GUI components
        self.setup_menu()            # Populate the menubar
        self.setup_header()
        self.setup_time_inputs()
        self.setup_controls()
        self.setup_history()

        self.center_window()
        self.update_supposed_time_in_label()
        self.update_supposed_time_out_label()

        # Add key bindings for date navigation
        self.bind_shortcut_keys()

        # Initially populate the tree only with the selected date's records
        self.populate_history_for_selected_date()

    # ------------------------------------------------------------------------
    # ADDITION: Single or Double-click highlight function
    # ------------------------------------------------------------------------
    def highlight_on_click(self, event):
        """
        Automatically highlight the entire text in an Entry on single/double click.
        We use a short .after(...) so that the default click behavior doesn't overwrite it.
        """
        widget = event.widget
        widget.after(1, lambda: widget.select_range(0, 'end'))

    # ---------------------------------------------------------
    #               NEW SHORTCUT KEY BINDINGS
    # ---------------------------------------------------------
    def bind_shortcut_keys(self):
        # Day navigation
        self.master.bind("<Control-Right>", self.increment_day)
        self.master.bind("<Control-Left>", self.decrement_day)

        # Month navigation
        self.master.bind("<Control-Shift-Right>", self.increment_month)
        self.master.bind("<Control-Shift-Left>", self.decrement_month)

        # Year navigation (using SHIFT+CTRL+ALT)
        self.master.bind("<Control-Alt-Shift-Right>", self.increment_year)
        self.master.bind("<Control-Alt-Shift-Left>", self.decrement_year)

    def increment_day(self, event):
        new_date = self.selected_date + timedelta(days=1)
        self.set_selected_date(new_date)

    def decrement_day(self, event):
        new_date = self.selected_date - timedelta(days=1)
        self.set_selected_date(new_date)

    def increment_month(self, event):
        year = self.selected_date.year
        month = self.selected_date.month
        day = self.selected_date.day

        new_month = month + 1
        new_year = year
        if new_month > 12:
            new_month = 1
            new_year += 1

        # Clamp the day if it exceeds the number of days in the new month
        num_days = calendar.monthrange(new_year, new_month)[1]
        new_day = min(day, num_days)

        new_date = datetime(new_year, new_month, new_day).date()
        self.set_selected_date(new_date)

    def decrement_month(self, event):
        year = self.selected_date.year
        month = self.selected_date.month
        day = self.selected_date.day

        new_month = month - 1
        new_year = year
        if new_month < 1:
            new_month = 12
            new_year -= 1

        # Clamp the day if it exceeds the number of days in the new month
        num_days = calendar.monthrange(new_year, new_month)[1]
        new_day = min(day, num_days)

        new_date = datetime(new_year, new_month, new_day).date()
        self.set_selected_date(new_date)

    def increment_year(self, event):
        year = self.selected_date.year
        month = self.selected_date.month
        day = self.selected_date.day

        new_year = year + 1
        # clamp day to new year's month last day if needed
        num_days = calendar.monthrange(new_year, month)[1]
        new_day = min(day, num_days)

        new_date = datetime(new_year, month, new_day).date()
        self.set_selected_date(new_date)

    def decrement_year(self, event):
        year = self.selected_date.year
        month = self.selected_date.month
        day = self.selected_date.day

        new_year = year - 1
        # clamp day
        num_days = calendar.monthrange(new_year, month)[1]
        new_day = min(day, num_days)

        new_date = datetime(new_year, month, new_day).date()
        self.set_selected_date(new_date)

    def set_selected_date(self, new_date):
        """Helper to set the selected_date, update the combos, and trigger refresh."""
        self.selected_date = new_date
        self.search_active = False  # going back to single date display
        # Update combos to reflect new date
        self.year_var.set(str(self.selected_date.year))
        self.month_var.set(calendar.month_name[self.selected_date.month])
        self.day_var.set(str(self.selected_date.day))
        # This will also call on_date_change, which refreshes everything
        self.on_date_change(None)

    # ---------------------------------------------------------
    #   A method to show only the currently selected date's records
    # ---------------------------------------------------------
    def populate_history_for_selected_date(self):
        date_str = self.selected_date.strftime("%Y-%m-%d")
        filtered = [r for r in self.records if r["date"] == date_str]
        self.current_records = filtered
        self.populate_history(filtered)

    # ---------------------------------------------------------
    #   For "Reset" button => revert to the selected date's data
    # ---------------------------------------------------------
    def reset_history(self):
        self.search_active = False
        self.populate_history_for_selected_date()

    # ---------------------------------------------------------
    #   Overridden populate_history method
    #   (If no record list is given, we use self.current_records)
    # ---------------------------------------------------------
    def populate_history(self, records=None):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if records is None:
            records = self.current_records

        for record in records:
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

    def select_all_records(self):
        """
        Selects all records in the history Treeview.
        """
        for child in self.history_tree.get_children():
            self.history_tree.selection_add(child)

    # ------------------------------------------------------------------------
    # THEME & STYLE CODE
    # ------------------------------------------------------------------------
    def apply_apple_calculator_light_style(self):
        """
        Apple Calculator–inspired LIGHT mode (no menubar recreation).
        """
        BG_LIGHT = "#FFFFFF"
        BG_FRAME = "#F2F2F2"
        FG_TEXT = "#000000"
        BTN_GRAY = "#D0D0D0"
        BTN_ORANGE = "#FF9500"
        BTN_HOVER_GRAY = "#C0C0C0"
        BTN_HOVER_ORANGE = "#FFB340"

        self.master.configure(bg=BG_LIGHT)

        self.style.configure("TFrame", background=BG_LIGHT)
        self.style.configure("TLabelFrame", background=BG_FRAME, foreground=FG_TEXT)
        self.style.configure("TLabelframe.Label", background=BG_FRAME, foreground=FG_TEXT)
        self.style.configure("TLabel", background=BG_LIGHT, foreground=FG_TEXT)

        # Buttons
        self.style.configure(
            "Calc.TButton",
            background=BTN_GRAY,
            foreground=FG_TEXT,
            bordercolor=BTN_GRAY,
            focusthickness=0,
            relief="flat",
            font=("Helvetica", 10)
        )
        self.style.map(
            "Calc.TButton",
            background=[("active", BTN_HOVER_GRAY), ("pressed", BTN_HOVER_GRAY)]
        )

        self.style.configure(
            "CalcPrimary.TButton",
            background=BTN_ORANGE,
            foreground="#FFFFFF",
            bordercolor=BTN_ORANGE,
            focusthickness=0,
            relief="flat",
            font=("Helvetica", 10)
        )
        self.style.map(
            "CalcPrimary.TButton",
            background=[("active", BTN_HOVER_ORANGE), ("pressed", BTN_HOVER_ORANGE)]
        )

        # Checkbutton, Combobox
        self.style.configure("TCheckbutton", background=BG_LIGHT, foreground=FG_TEXT)
        self.style.configure(
            "TCombobox",
            fieldbackground="#FFFFFF",
            foreground=FG_TEXT
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", "#FFFFFF")],
            selectforeground=[("readonly", FG_TEXT)],
            selectbackground=[("readonly", "#FFFFFF")]
        )

        # Treeview
        self.style.configure(
            "Treeview",
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground=FG_TEXT,
            rowheight=25
        )
        self.style.configure(
            "Treeview.Heading",
            background=BG_FRAME,
            foreground=FG_TEXT
        )

        self.style.configure("Vertical.TScrollbar", background=BG_FRAME)
        self.style.configure("TEntry", foreground=FG_TEXT, fieldbackground="#FFFFFF")

        self.menubar.config(bg=BG_LIGHT, fg=FG_TEXT, activebackground=BG_FRAME, activeforeground=FG_TEXT)
        self.master.option_add("*foreground", "black")

    def apply_apple_calculator_dark_style(self):
        """
        Apply custom styles for dark themes ('superhero' or 'darkly').
        """
        if self.current_theme == "superhero":
            BG_DARK = "#2E2E2E"
            BG_FRAME = "#3C3C3C"
            FG_TEXT = "#FFFFFF"
            BTN_GRAY = "#505050"
            BTN_ORANGE = "#FF9500"
            BTN_HOVER_GRAY = "#626262"
            BTN_HOVER_ORANGE = "#FFA040"
        elif self.current_theme == "darkly":
            BG_DARK = "#343A40"
            BG_FRAME = "#495057"
            FG_TEXT = "#FFFFFF"
            BTN_GRAY = "#6C757D"
            BTN_ORANGE = "#FFC107"
            BTN_HOVER_GRAY = "#5A6268"
            BTN_HOVER_ORANGE = "#FFCA2C"
        else:
            BG_DARK = "#333333"
            BG_FRAME = "#444444"
            FG_TEXT = "#FFFFFF"
            BTN_GRAY = "#555555"
            BTN_ORANGE = "#FF9500"
            BTN_HOVER_GRAY = "#666666"
            BTN_HOVER_ORANGE = "#FFA040"

        self.master.configure(bg=BG_DARK)
        self.style.configure("TFrame", background=BG_DARK)
        self.style.configure("TLabelFrame", background=BG_FRAME, foreground=FG_TEXT)
        self.style.configure("TLabelframe.Label", background=BG_FRAME, foreground=FG_TEXT)
        self.style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT)

        # Buttons
        self.style.configure(
            "Calc.TButton",
            background=BTN_GRAY,
            foreground=FG_TEXT,
            bordercolor=BTN_GRAY,
            focusthickness=0,
            relief="flat",
            font=("Helvetica", 10)
        )
        self.style.map(
            "Calc.TButton",
            background=[("active", BTN_HOVER_GRAY), ("pressed", BTN_HOVER_GRAY)],
            foreground=[("active", FG_TEXT)]
        )

        self.style.configure(
            "CalcPrimary.TButton",
            background=BTN_ORANGE,
            foreground="#FFFFFF",
            bordercolor=BTN_ORANGE,
            focusthickness=0,
            relief="flat",
            font=("Helvetica", 10)
        )
        self.style.map(
            "CalcPrimary.TButton",
            background=[("active", BTN_HOVER_ORANGE), ("pressed", BTN_HOVER_ORANGE)],
            foreground=[("active", "#FFFFFF")]
        )

        self.style.configure("TCheckbutton", background=BG_DARK, foreground=FG_TEXT)
        self.style.configure("TCombobox", fieldbackground=BG_FRAME, foreground=FG_TEXT)
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", BG_FRAME)],
            selectforeground=[("readonly", FG_TEXT)],
            selectbackground=[("readonly", BG_FRAME)]
        )

        self.style.configure(
            "Treeview",
            background=BG_DARK,
            fieldbackground=BG_DARK,
            foreground=FG_TEXT,
            rowheight=25
        )
        self.style.configure(
            "Treeview.Heading",
            background=BG_FRAME,
            foreground=FG_TEXT
        )

        self.style.configure("Vertical.TScrollbar", background=BG_FRAME)
        self.style.configure("TEntry", foreground=FG_TEXT, fieldbackground=BG_FRAME)

        self.menubar.config(bg=BG_DARK, fg="white", activebackground=BG_FRAME, activeforeground="white")
        self.master.option_add("*foreground", "white")

    def update_label_colors(self):
        """
        Updates the colors of the main labels for Late/Undertime, etc.
        """
        if self.current_theme == "flatly":  # Light mode
            text_color = "#000000"
        else:  # Dark mode
            text_color = "#FFFFFF"

        self.label_morning_late.config(foreground=text_color)
        self.label_morning_late_deduction.config(foreground=text_color)
        self.label_afternoon_undertime.config(foreground=text_color)
        self.label_afternoon_undertime_deduction.config(foreground=text_color)
        self.label_day.config(foreground=text_color)
        self.label_supposed_time_in.config(foreground=text_color)
        self.label_supposed_time_out.config(foreground=text_color)
        self.label_deductions.config(foreground=text_color)

    def refresh_all_widget_colors(self):
        """
        Re-apply correct foreground colors to all relevant Entry/Combobox
        after a theme switch, preserving 'red' for invalid input.
        """
        normal_color = "black" if self.current_theme == 'flatly' else "white"

        def refresh_entry(widget):
            current_fg = widget.cget("foreground")
            if current_fg != 'red':
                widget.configure(foreground=normal_color)

        def refresh_combo(widget):
            widget.configure(foreground=normal_color)

        # Morning entries
        refresh_entry(self.morning_actual_time_in_hour_entry)
        refresh_entry(self.morning_actual_time_in_minute_entry)
        refresh_combo(self.morning_actual_time_in_ampm_combo)

        # Afternoon entries
        refresh_entry(self.afternoon_actual_time_out_hour_entry)
        refresh_entry(self.afternoon_actual_time_out_minute_entry)
        refresh_combo(self.afternoon_actual_time_out_ampm_combo)

    def change_theme(self, theme_name):
        """
        Switch between 'Light Mode' (flatly) and 'Dark Mode' (superhero or darkly).
        """
        self.current_theme = theme_name
        try:
            self.style.theme_use(theme_name)
        except tk.TclError:
            messagebox.showerror("Theme Error", f"Theme '{theme_name}' is not available.", parent=self.master)
            logging.error(f"Attempted to use unavailable theme: {theme_name}")
            return

        if theme_name == "flatly":
            self.apply_apple_calculator_light_style()
        elif theme_name in ["superhero", "darkly"]:
            self.apply_apple_calculator_dark_style()
        else:
            pass

        self.update_label_colors()
        self.refresh_all_widget_colors()
        logging.info(f"Theme changed to {theme_name} mode.")

    # ------------------------------------------------------------------------
    # GUI SETUP
    # ------------------------------------------------------------------------
    def center_window(self):
        """
        Center the main application window on the screen.
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
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)
        Tooltip(file_menu, "File operations")

        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help_dialog)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        Tooltip(help_menu, "Help and information")

        if self.current_theme == "flatly":
            self.menubar.config(bg="#FFFFFF", fg="#000000", activebackground="#F2F2F2", activeforeground="#000000")
        else:
            self.menubar.config(bg="#2E2E2E", fg="#FFFFFF", activebackground="#3C3C3C", activeforeground="#FFFFFF")

    def setup_header(self):
        header_frame = ttkb.Frame(self.master)
        header_frame.pack(fill="x", pady=10, padx=10)

        labels_frame = ttk.Frame(header_frame)
        labels_frame.pack(side="left", fill="x", expand=True)

        date_selection_frame = ttk.Frame(labels_frame)
        date_selection_frame.pack(pady=5, anchor="w")

        ttk.Label(date_selection_frame, text="Year:").grid(row=0, column=0, padx=5, pady=2, sticky="e")
        self.year_var = tk.StringVar()
        self.year_combo = ttk.Combobox(
            date_selection_frame,
            textvariable=self.year_var,
            values=[str(year) for year in range(1900, 2126)],  # 1900-2125
            state="readonly",
            width=5
        )
        self.year_combo.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.year_combo.set(str(self.selected_date.year))
        self.year_combo.bind("<<ComboboxSelected>>", self.update_days)

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

        self.label_day = ttk.Label(labels_frame, text=f"Day: {self.current_day}", font=("Helvetica", 16))
        self.label_day.pack(pady=5, anchor="w")

        theme_buttons_frame = ttkb.Frame(header_frame)
        theme_buttons_frame.pack(side="right", anchor="e")

        self.button_light_mode = ttkb.Button(
            theme_buttons_frame,
            text="Light Mode",
            command=lambda: self.change_theme("flatly"),
            style="Calc.TButton"
        )
        self.button_light_mode.pack(side="left", padx=5)
        Tooltip(self.button_light_mode, "Switch to Light Mode")

        self.button_dark_mode = ttkb.Button(
            theme_buttons_frame,
            text="Dark Mode",
            command=lambda: self.change_theme("superhero"),
            style="Calc.TButton"
        )
        self.button_dark_mode.pack(side="left", padx=5)
        Tooltip(self.button_dark_mode, "Switch to Dark Mode")

        self.fullscreen = False
        self.button_fullscreen = ttkb.Button(
            theme_buttons_frame, text="Full Screen",
            command=self.toggle_fullscreen,
            style="Calc.TButton"
        )
        self.button_fullscreen.pack(side="left", padx=5)
        Tooltip(self.button_fullscreen, "Toggle Full Screen Mode")

    def setup_time_inputs(self):
        self.frame_morning = ttkb.LabelFrame(self.master, text="Morning", padding=10)
        self.frame_morning.pack(padx=10, pady=10, fill="x", expand=True)

        self.morning_checkbox = ttk.Checkbutton(
            self.frame_morning,
            text="Include Morning",
            variable=self.morning_check,
            command=self.on_morning_check_toggle
        )
        self.morning_checkbox.pack(anchor="w", pady=5, padx=5)
        Tooltip(self.morning_checkbox, "Check if you worked in the morning")

        left_morning_frame = ttkb.Frame(self.frame_morning)
        left_morning_frame.pack(side="left", fill="x", expand=True)

        self.label_supposed_time_in = ttk.Label(left_morning_frame, text="Supposed Time In: --:-- --", font=("Helvetica", 12))
        self.label_supposed_time_in.pack(anchor="w", pady=(0, 5))

        self.create_actual_time_input(left_morning_frame, "Actual Time In:", "morning_actual_time_in")

        self.button_clear_morning = ttkb.Button(
            left_morning_frame, text="Clear Morning",
            command=self.clear_morning, style="Calc.TButton"
        )
        self.button_clear_morning.pack(anchor="w", pady=5)
        Tooltip(self.button_clear_morning, "Clear Morning Inputs")

        right_morning_frame = ttkb.Frame(self.frame_morning)
        right_morning_frame.pack(side="right", anchor="center", padx=10)

        self.label_morning_late = ttk.Label(
            right_morning_frame,
            text="Late: 0 minutes",
            font=("Helvetica", 13, "bold"),
            foreground="#000000"
        )
        self.label_morning_late.pack(anchor="center", pady=5)

        self.label_morning_late_deduction = ttk.Label(
            right_morning_frame,
            text="Late Deduction: 0.000",
            font=("Helvetica", 13, "bold"),
            foreground="#000000"
        )
        self.label_morning_late_deduction.pack(anchor="center", pady=5)

        self.frame_afternoon = ttkb.LabelFrame(self.master, text="Afternoon", padding=10)
        self.frame_afternoon.pack(padx=10, pady=10, fill="x", expand=True)

        self.afternoon_checkbox = ttk.Checkbutton(
            self.frame_afternoon,
            text="Include Afternoon",
            variable=self.afternoon_check,
            command=self.on_afternoon_check_toggle
        )
        self.afternoon_checkbox.pack(anchor="w", pady=5, padx=5)
        Tooltip(self.afternoon_checkbox, "Check if you worked in the afternoon")

        left_afternoon_frame = ttkb.Frame(self.frame_afternoon)
        left_afternoon_frame.pack(side="left", fill="x", expand=True)

        self.label_supposed_time_out = ttk.Label(left_afternoon_frame, text="Supposed Time Out: --:-- --", font=("Helvetica", 12))
        self.label_supposed_time_out.pack(anchor="w", pady=(0, 5))

        self.create_actual_time_input(left_afternoon_frame, "Actual Time Out:", "afternoon_actual_time_out")

        self.button_clear_afternoon = ttkb.Button(
            left_afternoon_frame, text="Clear Afternoon",
            command=self.clear_afternoon, style="Calc.TButton"
        )
        self.button_clear_afternoon.pack(anchor="w", pady=5)
        Tooltip(self.button_clear_afternoon, "Clear Afternoon Inputs")

        right_afternoon_frame = ttkb.Frame(self.frame_afternoon)
        right_afternoon_frame.pack(side="right", anchor="center", padx=10)

        self.label_afternoon_undertime = ttk.Label(
            right_afternoon_frame,
            text="Undertime: 0 minutes",
            font=("Helvetica", 13, "bold"),
            foreground="#000000"
        )
        self.label_afternoon_undertime.pack(anchor="center", pady=5)

        self.label_afternoon_undertime_deduction = ttk.Label(
            right_afternoon_frame,
            text="Undertime Deduction: 0.000",
            font=("Helvetica", 13, "bold"),
            foreground="#000000"
        )
        self.label_afternoon_undertime_deduction.pack(anchor="center", pady=5)

        self.on_morning_check_toggle()
        self.on_afternoon_check_toggle()

    def setup_controls(self):
        controls_frame = ttkb.Frame(self.master)
        controls_frame.pack(pady=10)

        controls_frame.columnconfigure(0, weight=1)
        controls_frame.columnconfigure(1, weight=1)
        controls_frame.columnconfigure(2, weight=1)

        self.button_calculate = ttkb.Button(
            controls_frame,
            text="Calculate Deductions",
            command=self.calculate_deductions,
            style="CalcPrimary.TButton"
        )
        self.button_calculate.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        Tooltip(self.button_calculate, "Calculate deduction points based on input times")

        self.button_save = ttkb.Button(
            controls_frame,
            text="Save Record",
            command=self.save_record,
            style="Calc.TButton"
        )
        self.button_save.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        Tooltip(self.button_save, "Save the current day's record")

        self.button_export = ttkb.Button(
            controls_frame,
            text="Export History",
            command=self.export_history,
            style="Calc.TButton"
        )
        self.button_export.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        Tooltip(self.button_export, "Export deduction history to CSV")

        self.label_deductions = ttk.Label(self.master, text="Total Deduction Points: 0.000", font=("Helvetica", 16, "bold"))
        self.label_deductions.pack(pady=20)

    def setup_history(self):
        history_frame = ttkb.LabelFrame(self.master, text="Deduction History", padding=10)
        history_frame.pack(padx=10, pady=10, fill="both", expand=True)

        search_frame = ttk.Frame(history_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="From Year:").pack(side="left", padx=5)
        self.search_from_year_var = tk.StringVar()
        self.search_from_year = ttk.Combobox(
            search_frame,
            textvariable=self.search_from_year_var,
            values=[str(year) for year in range(1900, 2126)],
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

        ttk.Label(search_frame, text="To Year:").pack(side="left", padx=5)
        self.search_to_year_var = tk.StringVar()
        self.search_to_year = ttk.Combobox(
            search_frame,
            textvariable=self.search_to_year_var,
            values=[str(year) for year in range(1900, 2126)],
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

        self.button_search = ttkb.Button(search_frame, text="Search", command=self.search_history, style="Calc.TButton")
        self.button_search.pack(side="left", padx=5)
        Tooltip(self.button_search, "Search records within the selected date range")

        self.button_reset = ttkb.Button(search_frame, text="Reset", command=self.reset_history, style="Calc.TButton")
        self.button_reset.pack(side="left", padx=5)
        Tooltip(self.button_reset, "Reset to the currently selected date's records")

        self.button_select_all = ttkb.Button(search_frame, text="Select All", command=self.select_all_records, style="Calc.TButton")
        self.button_select_all.pack(side="left", padx=5)
        Tooltip(self.button_select_all, "Select all rows in the history")

        self.button_delete = ttkb.Button(search_frame, text="Delete", command=self.delete_record, style="Calc.TButton")
        self.button_delete.pack(side="left", padx=5)
        Tooltip(self.button_delete, "Delete selected record(s)")

        self.history_tree = ttk.Treeview(
            history_frame,
            columns=(
                "Date",
                "Morning Actual Time In",
                "Supposed Time In",
                "Late Minutes",
                "Afternoon Actual Time Out",
                "Supposed Time Out",
                "Undertime Minutes",
                "Deduction Points"
            ),
            show='headings',
            selectmode="extended"
        )

        self.history_tree.heading("Date", text="Date", command=lambda: self.sort_by_column("Date"))
        self.history_tree.heading("Morning Actual Time In", text="Actual Time In", command=lambda: self.sort_by_column("Morning Actual Time In"))
        self.history_tree.heading("Supposed Time In", text="Supposed Time In", command=lambda: self.sort_by_column("Supposed Time In"))
        self.history_tree.heading("Late Minutes", text="Late (min)", command=lambda: self.sort_by_column("Late Minutes"))
        self.history_tree.heading("Afternoon Actual Time Out", text="Actual Time Out", command=lambda: self.sort_by_column("Afternoon Actual Time Out"))
        self.history_tree.heading("Supposed Time Out", text="Supposed Time Out", command=lambda: self.sort_by_column("Supposed Time Out"))
        self.history_tree.heading("Undertime Minutes", text="Undertime (min)", command=lambda: self.sort_by_column("Undertime Minutes"))
        self.history_tree.heading("Deduction Points", text="Deduction Points", command=lambda: self.sort_by_column("Deduction Points"))

        self.history_tree.pack(fill="both", expand=True, side="left")

        self.history_tree.column("Date", width=100, anchor="center")
        self.history_tree.column("Morning Actual Time In", width=120, anchor="center")
        self.history_tree.column("Supposed Time In", width=120, anchor="center")
        self.history_tree.column("Late Minutes", width=100, anchor="center")
        self.history_tree.column("Afternoon Actual Time Out", width=120, anchor="center")
        self.history_tree.column("Supposed Time Out", width=120, anchor="center")
        self.history_tree.column("Undertime Minutes", width=120, anchor="center")
        self.history_tree.column("Deduction Points", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview, style="Vertical.TScrollbar")
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.history_tree.bind("<Delete>", lambda e: self.delete_record())
        self.history_tree.bind("<Control-a>", lambda e: self.select_all_records())
        self.history_tree.bind("<Control-A>", lambda e: self.select_all_records())
        self.history_tree.bind("<Button-3>", self.show_context_menu)

        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Edit Record", command=self.edit_record)
        self.context_menu.add_command(label="Delete Record", command=self.delete_record)

        self.sort_states = {
            "Date": False,
            "Morning Actual Time In": False,
            "Supposed Time In": False,
            "Late Minutes": False,
            "Afternoon Actual Time Out": False,
            "Supposed Time Out": False,
            "Undertime Minutes": False,
            "Deduction Points": False
        }

    # ------------------------------------------------------------------------
    # TIME INPUT LOGIC
    # ------------------------------------------------------------------------
    def on_morning_check_toggle(self):
        state = "normal" if self.morning_check.get() else "disabled"
        if not self.morning_check.get():
            self.morning_actual_time_in_hour_var.set('00')
            self.morning_actual_time_in_minute_var.set('00')
            self.morning_actual_time_in_ampm_var.set('AM')
            self.label_supposed_time_in.config(text="Supposed Time In: --:-- --")
        else:
            self.update_supposed_time_in_label()

        self.morning_actual_time_in_hour_entry.config(state=state)
        self.morning_actual_time_in_minute_entry.config(state=state)
        self.morning_actual_time_in_ampm_combo.config(state=state)
        self.morning_actual_time_in_button.config(state=state)
        self.button_clear_morning.config(state=state)

        self.update_supposed_time_out_label()

    def on_afternoon_check_toggle(self):
        state = "normal" if self.afternoon_check.get() else "disabled"
        if not self.afternoon_check.get():
            self.afternoon_actual_time_out_hour_var.set('00')
            self.afternoon_actual_time_out_minute_var.set('00')
            self.afternoon_actual_time_out_ampm_var.set('PM')
            self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")
        else:
            self.update_supposed_time_out_label()

        self.afternoon_actual_time_out_hour_entry.config(state=state)
        self.afternoon_actual_time_out_minute_entry.config(state=state)
        self.afternoon_actual_time_out_ampm_combo.config(state=state)
        self.afternoon_actual_time_out_button.config(state=state)
        self.button_clear_afternoon.config(state=state)

    def update_supposed_time_in_label(self):
        self.current_day = self.selected_date.strftime("%A")
        if self.morning_check.get():
            st = ALLOWED_TIMES.get(self.current_day, {}).get("supposed_time_in")
            sup_in_str = st.strftime("%I:%M %p") if st else "--:-- --"
            self.label_supposed_time_in.config(text=f"Supposed Time In: {sup_in_str}")
        else:
            self.label_supposed_time_in.config(text="Supposed Time In: --:-- --")

    def update_supposed_time_out_label(self):
        day_name = self.selected_date.strftime("%A")

        if not self.afternoon_check.get():
            self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")
            return

        if self.morning_check.get():
            # Both morning & afternoon => flexi (we'll clamp in calculate_deductions)
            self.label_supposed_time_out.config(
                text="Supposed Time Out: (Flexi - Will be determined on Calculate)"
            )
        else:
            # Only afternoon
            # Based on the new swap:
            if day_name == "Monday":
                sto = time(17, 0).strftime("%I:%M %p")      # Monday: 5:00 PM
            else:
                sto = time(17, 30).strftime("%I:%M %p")     # Tue-Fri: 5:30 PM
            self.label_supposed_time_out.config(text=f"Supposed Time Out: {sto}")

    def on_date_change(self, event):
        try:
            widget = event.widget if event else None
            if widget in [self.year_combo, self.month_combo, self.day_combo]:
                year = int(self.year_var.get())
                month = list(calendar.month_name).index(self.month_var.get())
                day = int(self.day_var.get())
                self.selected_date = datetime(year, month, day).date()
                self.search_active = False
            elif widget in [self.search_from_year, self.search_from_month, self.search_from_day,
                            self.search_to_year, self.search_to_month, self.search_to_day]:
                # This is related to the search combos. We won't change self.selected_date here.
                pass

            self.current_day = self.selected_date.strftime("%A")
            self.label_day.config(text=f"Day: {self.current_day}")

            self.update_supposed_time_in_label()
            self.update_supposed_time_out_label()

            self.label_morning_late.config(text="Late: 0 minutes")
            self.label_morning_late_deduction.config(text="Late Deduction: 0.000")
            self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
            self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
            self.label_deductions.config(text="Total Deduction Points: 0.000")

            if not self.search_active:
                self.populate_history_for_selected_date()

            logging.info(f"Date changed to {self.selected_date}")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid date selected.\n{e}", parent=self.master)
            logging.error(f"Error on date change: {e}")

    def update_days(self, event):
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

    def create_actual_time_input(self, parent, label_text, attr_name):
        frame = ttkb.Frame(parent)
        frame.pack(fill="x", pady=5)

        label = ttk.Label(frame, text=label_text, width=20)
        label.pack(side="left", padx=5)

        hour_var = tk.StringVar(value='00')
        hour_entry = ttk.Entry(frame, textvariable=hour_var, width=3, justify='center', style="TEntry")
        hour_entry.pack(side="left", padx=(0, 2))
        Tooltip(hour_entry, "Enter hours (01-12)")
        self.register_time_validation(hour_entry, hour_var, part='hour')

        # Auto-highlight on click/double-click
        hour_entry.bind("<Button-1>", self.highlight_on_click, add="+")
        hour_entry.bind("<Double-Button-1>", self.highlight_on_click, add="+")

        colon_label = ttk.Label(frame, text=":", width=1)
        colon_label.pack(side="left")

        minute_var = tk.StringVar(value='00')
        minute_entry = ttk.Entry(frame, textvariable=minute_var, width=3, justify='center', style="TEntry")
        minute_entry.pack(side="left", padx=(2, 5))
        Tooltip(minute_entry, "Enter minutes (00-59)")
        self.register_time_validation(minute_entry, minute_var, part='minute')

        # Auto-highlight on click/double-click
        minute_entry.bind("<Button-1>", self.highlight_on_click, add="+")
        minute_entry.bind("<Double-Button-1>", self.highlight_on_click, add="+")

        ampm_var = tk.StringVar(value="AM")
        if attr_name == "afternoon_actual_time_out":
            # Condition #1: Default PM for afternoon time out
            ampm_var.set("PM")

        ampm_combo = ttk.Combobox(frame, textvariable=ampm_var, values=["AM", "PM"], state="readonly", width=3)
        ampm_combo.pack(side="left", padx=(0, 5))
        Tooltip(ampm_combo, "Select AM or PM")

        time_button = ttkb.Button(frame, text="Select Time", command=lambda: self.open_time_picker(attr_name), style="Calc.TButton")
        time_button.pack(side="left", padx=2)
        Tooltip(time_button, "Open time picker")

        setattr(self, f'{attr_name}_hour_var', hour_var)
        setattr(self, f'{attr_name}_minute_var', minute_var)
        setattr(self, f'{attr_name}_ampm_var', ampm_var)

        setattr(self, f'{attr_name}_hour_entry', hour_entry)
        setattr(self, f'{attr_name}_minute_entry', minute_entry)
        setattr(self, f'{attr_name}_ampm_combo', ampm_combo)
        setattr(self, f'{attr_name}_button', time_button)

        hour_entry.bind("<KeyRelease>", self.create_time_input_key_release(hour_var, part='hour'))
        minute_entry.bind("<KeyRelease>", self.create_time_input_key_release(minute_var, part='minute'))
        hour_entry.bind("<Return>", self.enter_key_pressed)
        minute_entry.bind("<Return>", self.enter_key_pressed)
        ampm_combo.bind("<Return>", self.enter_key_pressed)
        time_button.bind("<Return>", self.enter_key_pressed)

    def register_time_validation(self, entry, var, part='hour'):
        def validate(*args):
            value = var.get()
            if part == 'hour':
                try:
                    if not (1 <= int(value) <= 12):
                        self.apply_error_style(entry)
                    else:
                        self.apply_normal_style(entry)
                except ValueError:
                    self.apply_error_style(entry)
            elif part == 'minute':
                try:
                    if not (0 <= int(value) <= 59):
                        self.apply_error_style(entry)
                    else:
                        self.apply_normal_style(entry)
                except ValueError:
                    self.apply_error_style(entry)
        var.trace_add('write', validate)

    def apply_error_style(self, widget):
        widget.configure(foreground="red")

    def apply_normal_style(self, widget):
        if self.current_theme == 'flatly':
            widget.configure(foreground="black")
        else:
            widget.configure(foreground="white")

    def create_time_input_key_release(self, var, part='hour'):
        def on_key_release(event):
            current_text = var.get().strip().upper()
            new_text = ''.join(filter(str.isdigit, current_text))
            if len(new_text) > 2:
                new_text = new_text[:2]
            var.set(new_text)
        return on_key_release

    def open_time_picker(self, attr_name):
        hour_var = getattr(self, f'{attr_name}_hour_var')
        minute_var = getattr(self, f'{attr_name}_minute_var')
        ampm_var = getattr(self, f'{attr_name}_ampm_var')

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
            hour_12 = selected_time.hour % 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            minute = selected_time.minute
            ampm = "PM" if selected_time.hour >= 12 else "AM"

            hour_var.set(f"{hour_12:02}")
            minute_var.set(f"{minute:02}")
            ampm_var.set(ampm)

    def parse_time_input(self, attr_name):
        hour_var = getattr(self, f'{attr_name}_hour_var')
        minute_var = getattr(self, f'{attr_name}_minute_var')
        ampm_var = getattr(self, f'{attr_name}_ampm_var')

        time_str = f"{hour_var.get()}:{minute_var.get()} {ampm_var.get()}"
        try:
            return datetime.strptime(time_str, "%I:%M %p").time()
        except ValueError:
            return None

    def calculate_time_difference(self, earlier_time, later_time):
        dt1 = datetime.combine(self.selected_date, earlier_time)
        dt2 = datetime.combine(self.selected_date, later_time)
        delta_minutes = (dt2 - dt1).total_seconds() // 60
        return int(delta_minutes)

    def calculate_deductions(self):
        total_late_deduction = 0.0
        total_undertime_deduction = 0.0

        # -------------------------------
        #   Handle Morning (Late)
        # -------------------------------
        if self.morning_check.get():
            morning_actual_time_in = self.parse_time_input("morning_actual_time_in")
            if not morning_actual_time_in:
                messagebox.showerror("Input Error", "Please enter a valid Actual Time In (Morning) or uncheck it.",
                                     parent=self.master)
                logging.warning("Invalid Actual Time In for Morning.")
                return

            # Suppose Time In from label
            supposed_time_in_str = self.label_supposed_time_in.cget("text").split(": ", 1)[1]
            try:
                supposed_time_in = datetime.strptime(supposed_time_in_str, "%I:%M %p").time()
            except ValueError:
                supposed_time_in = None

            if not supposed_time_in:
                messagebox.showerror("Error", "Supposed Time In is not set for the selected day.", parent=self.master)
                logging.error("Supposed Time In is not set.")
                return

            late_minutes_raw = self.calculate_time_difference(supposed_time_in, morning_actual_time_in)
            late_minutes = max(0, late_minutes_raw)
            self.label_morning_late.config(text=f"Late: {late_minutes} minutes")

            late_deduction = convert_time_diff_to_day_fraction(
                late_minutes // 60,
                late_minutes % 60
            )
            self.label_morning_late_deduction.config(text=f"Late Deduction: {late_deduction:.3f}")
            total_late_deduction = late_deduction
        else:
            self.label_morning_late.config(text="Late: 0 minutes")
            self.label_morning_late_deduction.config(text="Late Deduction: 0.000")

        # -------------------------------
        #  Determine Supposed Time Out (Flexi scenario clamp)
        # -------------------------------
        day_name = self.current_day

        supposed_time_out = None

        if self.morning_check.get() and self.afternoon_check.get():
            # FLEXI: In your original code, we do in_minutes + 540 => clamp
            morning_in = self.parse_time_input("morning_actual_time_in")
            if not morning_in:
                return

            in_minutes = morning_in.hour * 60 + morning_in.minute
            # Original clamp: 7:30 => 450, 8:30 => 510
            if in_minutes < 450:
                in_minutes = 450
            elif in_minutes > 510:
                in_minutes = 510

            # 9 hours after
            out_minutes = in_minutes + 540

            # NEW: If Monday => clamp 16:30 (990) to 17:00 (1020)
            # Otherwise => clamp 16:30 (990) to 17:30 (1050)
            if day_name == "Monday":
                if out_minutes < 990:
                    out_minutes = 990
                elif out_minutes > 1020:
                    out_minutes = 1020
            else:
                if out_minutes < 990:
                    out_minutes = 990
                elif out_minutes > 1050:
                    out_minutes = 1050

            out_hour = out_minutes // 60
            out_minute = out_minutes % 60
            supposed_time_out = time(out_hour, out_minute)
            self.label_supposed_time_out.config(
                text=f"Supposed Time Out: {supposed_time_out.strftime('%I:%M %p')}"
            )

        elif not self.morning_check.get() and self.afternoon_check.get():
            # Only afternoon
            # If Monday => 5:00 PM, else => 5:30 PM
            if day_name == "Monday":
                supposed_time_out = time(17, 0)  # 5:00 PM
            else:
                supposed_time_out = time(17, 30) # 5:30 PM

            self.label_supposed_time_out.config(
                text=f"Supposed Time Out: {supposed_time_out.strftime('%I:%M %p')}"
            )

        else:
            self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")

        # -------------------------------
        #   Handle Afternoon (Undertime)
        # -------------------------------
        if self.afternoon_check.get():
            afternoon_actual_time_out = self.parse_time_input("afternoon_actual_time_out")
            if not afternoon_actual_time_out:
                messagebox.showerror("Input Error", "Please enter a valid Actual Time Out (Afternoon) or uncheck it.",
                                     parent=self.master)
                logging.warning("Invalid Actual Time Out for Afternoon.")
                return

            if supposed_time_out:
                undertime_raw = self.calculate_time_difference(afternoon_actual_time_out, supposed_time_out)
                undertime_minutes = max(0, undertime_raw)
            else:
                undertime_minutes = 0

            self.label_afternoon_undertime.config(text=f"Undertime: {undertime_minutes} minutes")

            undertime_deduction = convert_time_diff_to_day_fraction(
                undertime_minutes // 60,
                undertime_minutes % 60
            )
            self.label_afternoon_undertime_deduction.config(text=f"Undertime Deduction: {undertime_deduction:.3f}")
            total_undertime_deduction = undertime_deduction
        else:
            self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
            self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")

        # half-day check
        half_day_absences = 0
        if not self.morning_check.get():
            half_day_absences += 1
        if not self.afternoon_check.get():
            half_day_absences += 1

        half_day_deduction = half_day_absences * 0.5
        total_deduction = round(total_late_deduction + total_undertime_deduction + half_day_deduction, 3)
        self.label_deductions.config(text=f"Total Deduction Points: {total_deduction:.3f}")

        logging.info(
            f"Calculated Deductions. Late: {total_late_deduction}, "
            f"Undertime: {total_undertime_deduction}, "
            f"Half-day(s): {half_day_absences * 0.5}, "
            f"Total: {total_deduction}"
        )

    def enter_key_pressed(self, event):
        self.calculate_deductions()

    def clear_morning(self):
        self.morning_actual_time_in_hour_var.set('00')
        self.morning_actual_time_in_minute_var.set('00')
        self.morning_actual_time_in_ampm_var.set('AM')

        self.label_morning_late.config(text="Late: 0 minutes")
        self.label_morning_late_deduction.config(text="Late Deduction: 0.000")
        self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")
        self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
        self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
        self.label_deductions.config(text="Total Deduction Points: 0.000")

        logging.info("Cleared Morning inputs.")

    def clear_afternoon(self):
        self.afternoon_actual_time_out_hour_var.set('00')
        self.afternoon_actual_time_out_minute_var.set('00')
        self.afternoon_actual_time_out_ampm_var.set('PM')

        self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
        self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
        self.label_deductions.config(text="Total Deduction Points: 0.000")

        logging.info("Cleared Afternoon inputs.")

    # <-- CHANGE: Store & restore geometry on toggling fullscreen
    def toggle_fullscreen(self):
        if not self.fullscreen:
            self.normal_geometry = self.master.geometry()
            self.master.attributes("-fullscreen", True)
            self.fullscreen = True
            self.button_fullscreen.config(text="Windowed Mode")
            logging.info("Entered full-screen mode.")
        else:
            self.master.attributes("-fullscreen", False)
            if self.normal_geometry:
                self.master.geometry(self.normal_geometry)
            self.fullscreen = False
            self.button_fullscreen.config(text="Full Screen")
            logging.info("Exited full-screen mode.")

    # ------------------------------------------------------------------------
    # SAVE / LOAD / EXPORT
    # ------------------------------------------------------------------------
    def save_record(self):
        try:
            deduction_text = self.label_deductions.cget("text").split(":")[1].strip()
            deduction_points = float(deduction_text)
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Unable to parse deduction points.", parent=self.master)
            logging.error("Failed to parse deduction points for saving.")
            return

        date_str = self.selected_date.strftime("%Y-%m-%d")

        if self.morning_check.get():
            morning_time_in = (
                getattr(self, 'morning_actual_time_in_hour_var').get().zfill(2) + ":" +
                getattr(self, 'morning_actual_time_in_minute_var').get().zfill(2) + " " +
                getattr(self, 'morning_actual_time_in_ampm_var').get()
            )
        else:
            morning_time_in = "--:-- --"

        supposed_time_in = self.label_supposed_time_in.cget("text").split(": ", 1)[1]

        if self.afternoon_check.get():
            afternoon_time_out = (
                getattr(self, 'afternoon_actual_time_out_hour_var').get().zfill(2) + ":" +
                getattr(self, 'afternoon_actual_time_out_minute_var').get().zfill(2) + " " +
                getattr(self, 'afternoon_actual_time_out_ampm_var').get()
            )
        else:
            afternoon_time_out = "--:-- --"

        supposed_time_out = self.label_supposed_time_out.cget("text").split(": ", 1)[1]

        late_minutes = 0
        if self.morning_check.get():
            late_minutes_str = self.label_morning_late.cget("text").split(":")[1].strip().split()[0]
            late_minutes = int(late_minutes_str)

        undertime_minutes = 0
        if self.afternoon_check.get():
            undertime_minutes_str = self.label_afternoon_undertime.cget("text").split(":")[1].strip().split()[0]
            undertime_minutes = int(undertime_minutes_str)

        new_record = {
            "date": date_str,
            "morning_actual_time_in": morning_time_in,
            "supposed_time_in": supposed_time_in,
            "late_minutes": late_minutes,
            "afternoon_actual_time_out": afternoon_time_out,
            "supposed_time_out": supposed_time_out,
            "undertime_minutes": undertime_minutes,
            "deduction_points": deduction_points
        }

        existing_records = [record for record in self.records if record["date"] == date_str]
        if existing_records:
            add_record = messagebox.askyesno(
                "Add Record",
                f"A record for {date_str} already exists.\nDo you want to add another record for this date?",
                parent=self.master
            )
            if not add_record:
                logging.info(f"User chose not to add another record for {date_str}.")
                return

        self.records.insert(0, new_record)

        self.save_records_to_file()

        messagebox.showinfo(
            "Success",
            f"Record for {date_str} saved successfully.",
            parent=self.master
        )
        logging.info(f"Record saved for {date_str}: {deduction_points} points.")

        # After saving, re-filter and show the new data for the selected date
        self.populate_history_for_selected_date()

    def export_history(self):
        if not self.records:
            messagebox.showinfo("No Data", "There are no records to export.", parent=self.master)
            logging.info("Export attempted with no records.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save History as CSV"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
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
                for record in sorted(self.records, key=lambda x: x["date"], reverse=True):
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
            messagebox.showinfo("Export Successful", f"History exported to {file_path}", parent=self.master)
            logging.info(f"History exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred while exporting:\n{e}", parent=self.master)
            logging.error(f"Failed to export history: {e}")

    # ------------------------------------------------------------------------
    # HISTORY & CONTEXT MENUS
    # ------------------------------------------------------------------------
    def show_context_menu(self, event):
        selected_item = self.history_tree.identify_row(event.y)
        if selected_item:
            self.history_tree.selection_set(selected_item)
            self.context_menu.post(event.x_root, event.y_root)

    def edit_record(self):
        selected_items = self.history_tree.selection()
        if len(selected_items) == 0:
            messagebox.showwarning("No Selection", "Please select a record to edit.", parent=self.master)
            logging.warning("Edit attempted without selecting a record.")
            return
        if len(selected_items) > 1:
            messagebox.showinfo("Edit Record", "Please select only one record at a time to edit.", parent=self.master)
            return

        item = selected_items[0]
        values = self.history_tree.item(item, 'values')
        date_str = values[0]
        morning_in_str = values[1]
        afternoon_out_str = values[4]

        record_index = None
        for i, record in enumerate(self.records):
            if (record["date"] == date_str and
                record["morning_actual_time_in"] == morning_in_str and
                record["afternoon_actual_time_out"] == afternoon_out_str):
                record_index = i
                break

        if record_index is None:
            messagebox.showerror("Error", "Selected record not found.", parent=self.master)
            return

        record_to_edit = self.records[record_index]
        EditRecordDialog(self.master, record_to_edit, self.save_edited_record)

    def save_edited_record(self, updated_record):
        self.recalc_single_record(updated_record)
        self.save_records_to_file()
        if self.search_active:
            self.current_records = [r for r in self.records if r in self.current_records or r["date"] == r["date"]]
            self.populate_history(self.current_records)
        else:
            self.populate_history_for_selected_date()

        messagebox.showinfo("Success", f"Record for {updated_record['date']} updated successfully.", parent=self.master)
        logging.info(f"Record updated for {updated_record['date']} with new times.")

    def recalc_single_record(self, record):
        date_str = record["date"]
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_name = dt.strftime("%A")

        morning_in_str = record["morning_actual_time_in"]
        if morning_in_str and morning_in_str != "--:-- --":
            morning_time = self.str_to_time(morning_in_str)

            st = ALLOWED_TIMES.get(day_name, {}).get("supposed_time_in")
            if st:
                record["supposed_time_in"] = st.strftime("%I:%M %p")
            else:
                record["supposed_time_in"] = "--:-- --"

            late_minutes = 0
            if morning_time and st:
                late_raw = self.calculate_time_difference(st, morning_time)
                late_minutes = max(0, late_raw)
            record["late_minutes"] = late_minutes
        else:
            record["morning_actual_time_in"] = "--:-- --"
            record["supposed_time_in"] = "--:-- --"
            record["late_minutes"] = 0

        after_str = record["afternoon_actual_time_out"]
        if after_str and after_str != "--:-- --":
            afternoon_time = self.str_to_time(after_str)
        else:
            afternoon_time = None

        # FLEXI check if both are present
        if record["morning_actual_time_in"] != "--:-- --" and afternoon_time:
            morning_time = self.str_to_time(record["morning_actual_time_in"])
            if morning_time:
                in_minutes = morning_time.hour * 60 + morning_time.minute
                if in_minutes < 450:
                    in_minutes = 450
                elif in_minutes > 510:
                    in_minutes = 510
                out_minutes = in_minutes + 540

                # Monday => clamp 16:30..17:00, else => 16:30..17:30
                if day_name == "Monday":
                    if out_minutes < 990:
                        out_minutes = 990
                    elif out_minutes > 1020:
                        out_minutes = 1020
                else:
                    if out_minutes < 990:
                        out_minutes = 990
                    elif out_minutes > 1050:
                        out_minutes = 1050

                out_h = out_minutes // 60
                out_m = out_minutes % 60
                sup_time_out = time(out_h, out_m)
                record["supposed_time_out"] = sup_time_out.strftime("%I:%M %p")
            else:
                record["supposed_time_out"] = "--:-- --"
        elif record["morning_actual_time_in"] == "--:-- --" and afternoon_time:
            # Only afternoon
            if day_name == "Monday":
                record["supposed_time_out"] = time(17, 0).strftime("%I:%M %p")
            else:
                record["supposed_time_out"] = time(17, 30).strftime("%I:%M %p")
        else:
            record["supposed_time_out"] = "--:-- --"

        undertime_minutes = 0
        if afternoon_time and record["supposed_time_out"] != "--:-- --":
            sup_out_time = self.str_to_time(record["supposed_time_out"])
            undertime_raw = self.calculate_time_difference(afternoon_time, sup_out_time)
            undertime_minutes = max(0, undertime_raw)
        record["undertime_minutes"] = undertime_minutes

        # half-day
        half_days = 0
        if record["morning_actual_time_in"] == "--:-- --":
            half_days += 1
        if record["afternoon_actual_time_out"] == "--:-- --":
            half_days += 1
        half_day_deduction = half_days * 0.5

        late_ded = convert_time_diff_to_day_fraction(
            record["late_minutes"] // 60, record["late_minutes"] % 60
        )
        undertime_ded = convert_time_diff_to_day_fraction(
            record["undertime_minutes"] // 60, record["undertime_minutes"] % 60
        )
        record["deduction_points"] = round(late_ded + undertime_ded + half_day_deduction, 3)

    def str_to_time(self, time_str):
        try:
            return datetime.strptime(time_str, "%I:%M %p").time()
        except:
            return None

    def delete_record(self):
        selected_items = self.history_tree.selection()
        if not selected_items:
            messagebox.showwarning("No Selection", "Please select a record to delete.", parent=self.master)
            logging.warning("Delete attempted without selecting a record.")
            return

        num_selected = len(selected_items)
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the selected {num_selected} record(s)?",
            parent=self.master
        )
        if not confirm:
            return

        to_delete = []
        for item in selected_items:
            values = self.history_tree.item(item, 'values')
            date_str = values[0]
            morning_in_str = values[1]
            afternoon_out_str = values[4]
            idx_to_remove = None
            for i, record in enumerate(self.records):
                if (record["date"] == date_str and
                    record["morning_actual_time_in"] == morning_in_str and
                    record["afternoon_actual_time_out"] == afternoon_out_str):
                    idx_to_remove = i
                    break
            if idx_to_remove is not None:
                to_delete.append(idx_to_remove)

        for idx in sorted(to_delete, reverse=True):
            self.records.pop(idx)

        self.save_records_to_file()

        if self.search_active:
            self.search_history()  # Re-run the search
        else:
            self.populate_history_for_selected_date()

        messagebox.showinfo("Deleted", f"Selected record(s) have been deleted.", parent=self.master)
        logging.info(f"Deleted {num_selected} record(s).")

    def search_history(self):
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
                messagebox.showerror("Invalid Range", "From date cannot be after To date.", parent=self.master)
                logging.warning("Invalid search date range.")
                return

            filtered_records = [
                record for record in self.records
                if from_date <= datetime.strptime(record["date"], "%Y-%m-%d").date() <= to_date
            ]
            self.current_records = filtered_records
            self.search_active = True
            self.populate_history(filtered_records)
            logging.info(f"Searched records from {from_date} to {to_date}.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please ensure all search dates are selected correctly.\n{e}",
                                 parent=self.master)
            logging.error(f"Error in search input: {e}")

    def load_records(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    data = json.load(f)

                if isinstance(data, list):
                    valid_records = []
                    for record in data:
                        if isinstance(record, dict) and "date" in record and "deduction_points" in record:
                            record.setdefault("morning_actual_time_in", "--:-- --")
                            record.setdefault("supposed_time_in", "--:-- --")
                            record.setdefault("late_minutes", 0)
                            record.setdefault("afternoon_actual_time_out", "--:-- --")
                            record.setdefault("supposed_time_out", "--:-- --")
                            record.setdefault("undertime_minutes", 0)
                            valid_records.append(record)
                    return valid_records
                elif isinstance(data, dict):
                    # old format => transform
                    records = []
                    for date_str, ded_val in data.items():
                        records.append({
                            "date": date_str,
                            "morning_actual_time_in": "--:-- --",
                            "supposed_time_in": "--:-- --",
                            "late_minutes": 0,
                            "afternoon_actual_time_out": "--:-- --",
                            "supposed_time_out": "--:-- --",
                            "undertime_minutes": 0,
                            "deduction_points": ded_val
                        })
                    with open(DATA_FILE, 'w') as fw:
                        json.dump(records, fw, indent=4)
                    return records
                else:
                    logging.warning("Unknown data format. Starting empty.")
                    return []
            except json.JSONDecodeError as e:
                messagebox.showerror("Error", f"Failed to load records: {e}", parent=self.master)
                logging.error(f"JSON decode error: {e}")
                return []
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while loading records:\n{e}", parent=self.master)
                logging.error(f"Error loading records: {e}")
                return []
        else:
            logging.info("No existing records found. Starting fresh.")
            return []

    def save_records_to_file(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.records, f, indent=4)
            logging.info("Records saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save records: {e}", parent=self.master)
            logging.error(f"Error saving records: {e}")

    def sort_by_column(self, col):
        self.sort_states[col] = not self.sort_states[col]
        reverse = self.sort_states[col]

        if col == "Late Minutes":
            key_func = lambda x: float(x["late_minutes"])
        elif col == "Undertime Minutes":
            key_func = lambda x: float(x["undertime_minutes"])
        elif col == "Deduction Points":
            key_func = lambda x: float(x["deduction_points"])
        elif col == "Date":
            key_func = lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
        elif col == "Morning Actual Time In":
            key_func = lambda x: x["morning_actual_time_in"]
        elif col == "Supposed Time In":
            key_func = lambda x: x["supposed_time_in"]
        elif col == "Afternoon Actual Time Out":
            key_func = lambda x: x["afternoon_actual_time_out"]
        elif col == "Supposed Time Out":
            key_func = lambda x: x["supposed_time_out"]
        else:
            key_func = lambda x: x["date"]  # fallback

        self.current_records.sort(key=key_func, reverse=reverse)
        self.populate_history(self.current_records)

    # ------------------------------------------------------------------------
    # ADDED: More recommended features in the help tabs
    # ------------------------------------------------------------------------
    def show_help_dialog(self):
        help_window = tk.Toplevel(self.master)
        help_window.title("How to Use - Daily Time Record")

        help_window.transient(self.master)
        help_window.lift()

        help_window.grab_set()
        help_window.geometry("700x550")
        self.center_child_window(help_window)

        notebook = ttk.Notebook(help_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # -----------------
        #  Tab: OVERVIEW
        # -----------------
        tab_overview = ttk.Frame(notebook)
        notebook.add(tab_overview, text="Overview")

        overview_content = """Daily Time Record (DTR) Application - Overview

This version includes:
- Half-Day checking
- Flexi Time Out logic
- Multi-selection for deletion
- Single-record editing
- Column sorting on click
- Press 'Delete' key to remove selected row(s)
- Press 'Ctrl + A' to select all records
- Time Picker dialogs
- Light/Dark theme toggle
- Fullscreen toggle
- Keyboard shortcuts for changing the selected date:
   * Ctrl + Right Arrow  => Next Day
   * Ctrl + Left Arrow   => Previous Day
   * Ctrl + Shift + Right Arrow => Next Month
   * Ctrl + Shift + Left Arrow  => Previous Month
   * Ctrl + Shift + Alt + Right Arrow => Next Year
   * Ctrl + Shift + Alt + Left Arrow  => Previous Year
"""
        label_overview = tk.Text(tab_overview, wrap="word", font=("Helvetica", 12),
                                 bg=help_window.cget("bg"), borderwidth=0)
        label_overview.insert("1.0", overview_content)
        label_overview.config(state="disabled")
        label_overview.pack(fill="both", expand=True, padx=10, pady=10)

        # --------------------------
        #  Tab: STEP-BY-STEP GUIDE
        # --------------------------
        tab_guide = ttk.Frame(notebook)
        notebook.add(tab_guide, text="Step-by-Step Guide")

        guide_content = """Step-by-Step Guide

1. Select the Date (top-left) or use keyboard shortcuts (Ctrl/Shift/Alt + Arrow) to navigate quickly.
2. Check 'Morning' if you worked in the morning; uncheck if absent.
3. Check 'Afternoon' if you worked in the afternoon; uncheck if absent.
4. Enter Actual Time In / Out or click 'Select Time'.
5. Click 'Calculate Deductions' to see Late/Undertime/Total points.
6. Click 'Save Record' to store it (multiple records per date allowed if you confirm).
7. Click 'Export History' => CSV to export all saved data.
8. In the History section:
   - The default view shows only the currently selected date's records.
   - Use the date range filter to see multiple dates, then press 'Search'.
   - 'Reset' reverts back to showing only the currently selected date's records.
   - You can multi-select rows with Ctrl+Click or Shift+Click,
     then press 'Delete' key or right-click => 'Delete Record'.
   - Right-click => 'Edit Record' modifies times and automatically recalculates
   - Press 'Ctrl + A' to select all records.
   - Click column headers to toggle ascending/descending sort.
   - Single/Double-click the time fields to highlight them for quick editing.
"""
        label_guide = tk.Text(tab_guide, wrap="word", font=("Helvetica", 12),
                              bg=help_window.cget("bg"), borderwidth=0)
        label_guide.insert("1.0", guide_content)
        label_guide.config(state="disabled")
        label_guide.pack(fill="both", expand=True, padx=10, pady=10)

        # -------------------
        #  Tab: FAQs
        # -------------------
        tab_faqs = ttk.Frame(notebook)
        notebook.add(tab_faqs, text="FAQs")

        faqs_content = """Frequently Asked Questions (FAQs)

Q: Why does the Deduction History only show the selected date by default?
A: This design helps focus on the current day's data. You can still use date range filters to see more dates.

Q: How do I quickly jump to next/previous days, months, or years?
A: Use the keyboard shortcuts:
   * Ctrl + Right/Left => Next/Previous Day
   * Ctrl + Shift + Right/Left => Next/Previous Month
   * Ctrl + Shift + Alt + Right/Left => Next/Previous Year

Q: How do I reset the search?
A: Click the 'Reset' button. This will revert the table to showing only the currently selected date's records.

Q: What if I forget to check Morning or Afternoon?
A: The system assumes half-day absence for any unchecked portion, adding 0.5 to the deduction.

Q: Can I add multiple records for the same date?
A: Yes, you'll be prompted with a confirmation if a record already exists for that date.

Q: How do I edit or delete a record?
A: Right-click on a record in the Deduction History or select it and press 'Delete'. You can also choose 'Edit Record' to modify times.

Q: How does sorting work?
A: Click the column header to sort ascending/descending for that column. Repeat click to toggle the order.

Q: Does the application remember my data after closing?
A: Yes, data is stored in JSON (dtr_records.json). Keep it safe to avoid losing records.

Q: Can I see all records at once?
A: Enter a broad date range in the search fields (e.g., 1900 to 2125) and click 'Search' to see all.

Q: What if I want to revert to seeing only the selected date after searching?
A: Simply click 'Reset' or change the date manually (which also forces single-date mode again).
"""
        label_faqs = tk.Text(tab_faqs, wrap="word", font=("Helvetica", 12),
                             bg=help_window.cget("bg"), borderwidth=0)
        label_faqs.insert("1.0", faqs_content)
        label_faqs.config(state="disabled")
        label_faqs.pack(fill="both", expand=True, padx=10, pady=10)

        # Adjust text color based on theme
        if self.current_theme != 'flatly':  # dark theme
            label_overview.config(fg="white")
            label_guide.config(fg="white")
            label_faqs.config(fg="white")
        else:
            label_overview.config(fg="black")
            label_guide.config(fg="black")
            label_faqs.config(fg="black")

    def show_about_dialog(self):
        about_window = tk.Toplevel(self.master)
        about_window.title("About - Daily Time Record")

        about_window.transient(self.master)
        about_window.lift()

        about_window.grab_set()
        about_window.geometry("500x400")
        self.center_child_window(about_window)

        frame = ttk.Frame(about_window, padding=20)
        frame.pack(fill="both", expand=True)

        about_content = """Daily Time Record (DTR) Application

Enhanced with:
 - Half-Day Checking
 - Flexi Time Out
 - Multi-selection & Sorting
 - Simplified Record Editing
 - Time Picker for convenience
 - Light/Dark Mode toggle
 - Fullscreen toggle
 - Keyboard Shortcuts for Date Navigation

Developer: KCprsnlcc
GitHub: https://github.com/KCprsnlcc

Disclaimer: Use at your own risk. Keep data backups.
"""
        label_about = tk.Text(frame, wrap="word", font=("Helvetica", 12),
                              bg=about_window.cget("bg"), borderwidth=0)
        label_about.insert("1.0", about_content)
        label_about.config(state="disabled")
        label_about.pack(fill="both", expand=True)

        if self.current_theme != 'flatly':
            label_about.config(fg="white")
        else:
            label_about.config(fg="black")

    def center_child_window(self, child):
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


# --------------------------------------------------------------
#   EDIT RECORD DIALOG CLASS
# --------------------------------------------------------------
class EditRecordDialog:
    """
    Dialog to edit the 'morning_actual_time_in' and 'afternoon_actual_time_out' fields only.
    """
    def __init__(self, parent, record_data, callback_on_save):
        self.parent = parent
        self.record_data = record_data
        self.callback_on_save = callback_on_save

        self.top = tk.Toplevel(parent)
        self.top.title("Edit Record")

        self.top.transient(self.parent)
        self.top.lift()
        self.top.grab_set()

        date_lbl = ttk.Label(self.top, text=f"Date: {record_data['date']}", font=("Helvetica", 12, "bold"))
        date_lbl.pack(pady=5, anchor="w")

        frame_morn = ttk.LabelFrame(self.top, text="Morning Actual Time In")
        frame_morn.pack(fill="x", expand=True, padx=10, pady=5)

        self.morning_var = tk.StringVar(value=record_data.get("morning_actual_time_in", "--:-- --"))
        self.morning_entry = ttk.Entry(frame_morn, textvariable=self.morning_var, width=20, style="TEntry")
        self.morning_entry.pack(side="left", padx=5, pady=5)
        # Highlight on click/double-click
        self.morning_entry.bind("<Button-1>", self.highlight_on_click, add="+")
        self.morning_entry.bind("<Double-Button-1>", self.highlight_on_click, add="+")

        self.btn_morning_picker = ttkb.Button(frame_morn, text="Pick Time",
                                              command=lambda: self.pick_time(self.morning_var), style="Calc.TButton")
        self.btn_morning_picker.pack(side="left", padx=5, pady=5)

        frame_after = ttk.LabelFrame(self.top, text="Afternoon Actual Time Out")
        frame_after.pack(fill="x", expand=True, padx=10, pady=5)

        self.afternoon_var = tk.StringVar(value=record_data.get("afternoon_actual_time_out", "--:-- --"))
        self.afternoon_entry = ttk.Entry(frame_after, textvariable=self.afternoon_var, width=20, style="TEntry")
        self.afternoon_entry.pack(side="left", padx=5, pady=5)
        # Highlight on click/double-click
        self.afternoon_entry.bind("<Button-1>", self.highlight_on_click, add="+")
        self.afternoon_entry.bind("<Double-Button-1>", self.highlight_on_click, add="+")

        self.btn_afternoon_picker = ttkb.Button(frame_after, text="Pick Time",
                                                command=lambda: self.pick_time(self.afternoon_var), style="Calc.TButton")
        self.btn_afternoon_picker.pack(side="left", padx=5, pady=5)

        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Save", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

        self.center_dialog()
        self.top.protocol("WM_DELETE_WINDOW", self.on_cancel)

    def highlight_on_click(self, event):
        widget = event.widget
        widget.after(1, lambda: widget.select_range(0, 'end'))

    def center_dialog(self):
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

    def pick_time(self, target_var):
        current_val = target_var.get().strip()
        time_obj = None
        if current_val != "--:-- --":
            try:
                time_obj = datetime.strptime(current_val, "%I:%M %p").time()
            except:
                pass

        picker = TimePickerDialog(self.top, initial_time=time_obj, title="Select Time")
        selected_time = picker.show()
        if selected_time:
            hour_12 = selected_time.hour % 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            minute = selected_time.minute
            ampm = "PM" if selected_time.hour >= 12 else "AM"
            target_var.set(f"{hour_12:02}:{minute:02} {ampm}")

    def on_save(self):
        self.record_data["morning_actual_time_in"] = self.morning_var.get().strip()
        self.record_data["afternoon_actual_time_out"] = self.afternoon_var.get().strip()
        self.callback_on_save(self.record_data)
        self.top.destroy()

    def on_cancel(self):
        self.top.destroy()


def main():
    setup_logging()
    logging.info("Application started.")
    root = tk.Tk()
    app = DailyTimeRecordApp(root)
    root.mainloop()
    logging.info("Application closed.")


if __name__ == "__main__":
    main()
