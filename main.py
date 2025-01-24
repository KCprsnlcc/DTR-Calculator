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

HALF_DAY_TIMES = {
    "Monday":  time(8, 15),
    "Tuesday": time(8, 30),
    "Wednesday": time(8, 30),
    "Thursday": time(8, 30),
    "Friday": time(8, 30)
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
        tw.wm_geometry(f"+{self.x}+{self.y - 20}")  # Position above the cursor (20 pixels above)

        # Add the label with the tooltip text
        label = ttk.Label(
            tw, text=self.text, justify=tk.LEFT,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1,
            font=("tahoma", "8", "normal")
        )
        label.pack(ipadx=1)

    def hidetip(self):
        if self.tipwindow:
            self.tipwindow.destroy()
        self.tipwindow = None


class TimePickerDialog:
    """
    A dialog for selecting time (Hour, Minute, AM/PM) with dropdowns (Combobox).
    """
    def __init__(self, parent, initial_time=None, title="Select Time"):
        self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title(title)
        self.top.grab_set()  # Make the dialog modal
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

        master.resizable(True, True)

        # Keep an initial bootstrap theme to load styles; we override later:
        self.style = Style(theme='flatly')
        self.current_theme = 'flatly'

        self.records = self.load_records()
        self.current_records = list(self.records)

        self.selected_date = datetime.now().date()
        self.current_day = self.selected_date.strftime("%A")

        self.morning_check = tk.BooleanVar(value=True)
        self.afternoon_check = tk.BooleanVar(value=True)

        # By default, let's assume user starts in "Light" theme:
        self.apply_apple_calculator_light_style()

        self.setup_menu()
        self.setup_header()
        self.setup_time_inputs()
        self.setup_controls()
        self.setup_history()

        self.center_window()
        self.update_supposed_time_in_label()

    # ------------------------------------------------------------------------
    # APPLE CALCULATOR STYLE: We define two separate styles:
    # 1) Light style (White background, black text, etc.)
    # 2) Dark style (Dark gray background, white text, etc.) + override dark blue => white
    # ------------------------------------------------------------------------
    def apply_apple_calculator_light_style(self):
        """
        Apple Calculator–inspired LIGHT mode:
         - White background
         - Black text
         - Light grays for frames & buttons
         - Orange highlight for primary button
        """
        # Colors
        BG_LIGHT = "#FFFFFF"      # main background (white)
        BG_FRAME = "#F2F2F2"      # lighter gray for frames
        FG_TEXT = "#000000"       # black text
        BTN_GRAY = "#D0D0D0"      # normal button background
        BTN_ORANGE = "#FF9500"    # primary highlight (orange)
        BTN_HOVER_GRAY = "#C0C0C0"
        BTN_HOVER_ORANGE = "#FFB340"

        # Root window
        self.master.configure(bg=BG_LIGHT)

        # Frame and LabelFrame
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
            font=("Helvetica", 10, "bold")
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
            font=("Helvetica", 10, "bold")
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

        # Scrollbar
        self.style.configure("Vertical.TScrollbar", background=BG_FRAME)

        # Entries: text in black, background white
        self.style.configure(
            "TEntry",
            foreground=FG_TEXT,
            fieldbackground="#FFFFFF"
        )

        # (Optional) Menu bar overrides in Light
        self.master.option_add('*Menu.tearOff', False)
        # Force black foreground in text-based widgets if needed
        self.master.option_add("*foreground", "black")

    def apply_apple_calculator_dark_style(self):
        """
        Apple Calculator–inspired DARK mode:
         - Dark gray backgrounds
         - White text
         - Gray buttons
         - Orange highlight for primary button
         - Override any default "dark blue" so text is white
        """
        BG_DARK = "#333333"
        BG_FRAME = "#3C3C3C"
        FG_TEXT = "#FFFFFF"
        BTN_GRAY = "#505050"
        BTN_ORANGE = "#FF9500"
        BTN_HOVER_GRAY = "#626262"
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
            font=("Helvetica", 10, "bold")
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
            font=("Helvetica", 10, "bold")
        )
        self.style.map(
            "CalcPrimary.TButton",
            background=[("active", BTN_HOVER_ORANGE), ("pressed", BTN_HOVER_ORANGE)],
            foreground=[("active", "#FFFFFF")]
        )

        # Checkbutton, Combobox
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

        # Entries: text in white, background = BG_FRAME or dark
        self.style.configure(
            "TEntry",
            foreground=FG_TEXT,
            fieldbackground=BG_FRAME
        )

        # Force any possible link or accent text to white
        self.master.option_add("*foreground", "white")

        # Also override the menubar text color (if possible)
        menubar = tk.Menu(self.master, bg=BG_DARK, fg="white", activebackground=BG_DARK, activeforeground="white")
        self.master.configure(menu=menubar)

    def update_label_colors(self):
        """
        Updates the colors of labels for Late and Undertime calculations based on the theme.
        """
        if self.current_theme == "flatly":  # Light mode
            text_color = "#000000"  # Black
        else:  # Dark mode
            text_color = "#FFFFFF"  # White

        # Update the foreground color of the labels
        self.label_morning_late.config(foreground=text_color)
        self.label_morning_late_deduction.config(foreground=text_color)
        self.label_afternoon_undertime.config(foreground=text_color)
        self.label_afternoon_undertime_deduction.config(foreground=text_color)

    def change_theme(self, theme_name):
        """
        Switch between 'Light Mode' and 'Dark Mode' – using Apple Calculator color palettes.
        """
        self.current_theme = theme_name
        if theme_name == "flatly":
            # Light Mode
            self.style.theme_use("flatly")
            self.apply_apple_calculator_light_style()
            logging.info("Theme changed to Light Mode (Apple Calculator style).")
        else:
            # Dark Mode
            self.style.theme_use("darkly")
            self.apply_apple_calculator_dark_style()
            logging.info("Theme changed to Dark Mode (Apple Calculator style).")

        # Update label colors based on the theme
        self.update_label_colors()

    # ------------------------------------------------------------------------
    # Remaining code below with minimal modifications to incorporate new styles
    # ------------------------------------------------------------------------

    def center_window(self):
        self.master.update_idletasks()
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        window_width = self.master.winfo_width()
        window_height = self.master.winfo_height()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.master.geometry(f"+{x}+{y}")

    def setup_menu(self):
        menubar = tk.Menu(self.master)
        self.master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.master.quit)
        Tooltip(file_menu, "File operations")

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Use", command=self.show_help_dialog)
        help_menu.add_command(label="About", command=self.show_about_dialog)
        Tooltip(help_menu, "Help and information")

    def setup_header(self):
        header_frame = ttkb.Frame(self.master)
        header_frame.pack(fill="x", pady=10, padx=10)

        labels_frame = ttk.Frame(header_frame)
        labels_frame.pack(side="left", fill="x", expand=True)

        date_selection_frame = ttk.Frame(labels_frame)
        date_selection_frame.pack(pady=5, anchor="w")

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

        self.label_day = ttk.Label(labels_frame, text=f"Day: {self.current_day}", font=("Inter", 16))
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

        self.label_supposed_time_in = ttk.Label(left_morning_frame, text="Supposed Time In: --:-- --", font=("Inter", 12))
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
            font=("Inter", 13, "bold"),
            foreground="#000000"
        )
        self.label_morning_late.pack(anchor="center", pady=5)

        self.label_morning_late_deduction = ttk.Label(
            right_morning_frame,
            text="Late Deduction: 0.000",
            font=("Inter", 13, "bold"),
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

        self.label_supposed_time_out = ttk.Label(left_afternoon_frame, text="Supposed Time Out: --:-- --", font=("Inter", 12))
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
            font=("Inter", 13, "bold"),
            foreground="#000000"
        )
        self.label_afternoon_undertime.pack(anchor="center", pady=5)

        self.label_afternoon_undertime_deduction = ttk.Label(
            right_afternoon_frame,
            text="Undertime Deduction: 0.000",
            font=("Inter", 13, "bold"),
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

        self.label_deductions = ttk.Label(self.master, text="Total Deduction Points: 0.000", font=("Inter", 16, "bold"))
        self.label_deductions.pack(pady=20)

    def setup_history(self):
        history_frame = ttkb.LabelFrame(self.master, text="Deduction History", padding=10)
        history_frame.pack(padx=10, pady=10, fill="both", expand=True)

        search_frame = ttk.Frame(history_frame)
        search_frame.pack(fill="x", pady=5)

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

        self.button_search = ttkb.Button(search_frame, text="Search", command=self.search_history, style="Calc.TButton")
        self.button_search.pack(side="left", padx=5)
        Tooltip(self.button_search, "Search records within the selected date range")

        self.button_reset = ttkb.Button(search_frame, text="Reset", command=lambda: self.populate_history(None), style="Calc.TButton")
        self.button_reset.pack(side="left", padx=5)
        Tooltip(self.button_reset, "Reset search filters")

        self.button_select_all = ttkb.Button(search_frame, text="Select All", command=self.select_all_records, style="Calc.TButton")
        self.button_select_all.pack(side="left", padx=5)
        Tooltip(self.button_select_all, "Select all rows in the history")

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

        self.history_tree.pack(fill="both", expand=True)

        self.history_tree.column("Date", width=100, anchor="center")
        self.history_tree.column("Morning Actual Time In", width=120, anchor="center")
        self.history_tree.column("Supposed Time In", width=120, anchor="center")
        self.history_tree.column("Late Minutes", width=100, anchor="center")
        self.history_tree.column("Afternoon Actual Time Out", width=120, anchor="center")
        self.history_tree.column("Supposed Time Out", width=120, anchor="center")
        self.history_tree.column("Undertime Minutes", width=120, anchor="center")
        self.history_tree.column("Deduction Points", width=120, anchor="center")

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.history_tree.bind("<Delete>", lambda e: self.delete_record())
        self.history_tree.bind("<Button-3>", self.show_context_menu)
        self.context_menu = tk.Menu(self.master, tearoff=0)
        self.context_menu.add_command(label="Edit Record", command=self.edit_record)
        self.context_menu.add_command(label="Delete Record", command=self.delete_record)

        self.sort_states = {
            "Date": False,
            "Morning Actual Time In": True,
            "Supposed Time In": True,
            "Late Minutes": True,
            "Afternoon Actual Time Out": True,
            "Supposed Time Out": True,
            "Undertime Minutes": True,
            "Deduction Points": True
        }

        self.populate_history()

    def sort_by_column(self, column_name):
        ascending = self.sort_states[column_name]
        self.sort_states[column_name] = not ascending

        def parse_date(val):
            try:
                return datetime.strptime(val, "%Y-%m-%d").date()
            except:
                return datetime.min.date()

        def parse_time(val):
            if val.strip() == "--:-- --":
                return time.min
            try:
                return datetime.strptime(val, "%I:%M %p").time()
            except:
                return time.min

        def parse_int(val):
            try:
                return int(val)
            except:
                return 0

        def parse_float(val):
            try:
                return float(val)
            except:
                return 0.0

        if column_name == "Date":
            key_func = lambda r: parse_date(r["date"])
        elif column_name == "Morning Actual Time In":
            key_func = lambda r: parse_time(r.get("morning_actual_time_in", "--:-- --"))
        elif column_name == "Supposed Time In":
            key_func = lambda r: parse_time(r.get("supposed_time_in", "--:-- --"))
        elif column_name == "Late Minutes":
            key_func = lambda r: parse_int(r.get("late_minutes", 0))
        elif column_name == "Afternoon Actual Time Out":
            key_func = lambda r: parse_time(r.get("afternoon_actual_time_out", "--:-- --"))
        elif column_name == "Supposed Time Out":
            key_func = lambda r: parse_time(r.get("supposed_time_out", "--:-- --"))
        elif column_name == "Undertime Minutes":
            key_func = lambda r: parse_int(r.get("undertime_minutes", 0))
        elif column_name == "Deduction Points":
            key_func = lambda r: parse_float(r.get("deduction_points", 0))
        else:
            key_func = lambda r: r

        self.current_records.sort(key=key_func, reverse=not ascending)
        self.populate_history(self.current_records)

    def select_all_records(self):
        for child in self.history_tree.get_children():
            self.history_tree.selection_add(child)

    def on_morning_check_toggle(self):
        state = "normal" if self.morning_check.get() else "disabled"
        if state == "disabled":
            getattr(self, 'morning_actual_time_in_hour_var').set('00')
            getattr(self, 'morning_actual_time_in_minute_var').set('00')
        self.morning_actual_time_in_hour_entry.config(state=state)
        self.morning_actual_time_in_minute_entry.config(state=state)
        self.morning_actual_time_in_ampm_combo.config(state=state)
        self.morning_actual_time_in_button.config(state=state)
        self.button_clear_morning.config(state=state)
        self.update_supposed_time_in_label()

    def on_afternoon_check_toggle(self):
        state = "normal" if self.afternoon_check.get() else "disabled"
        if state == "disabled":
            getattr(self, 'afternoon_actual_time_out_hour_var').set('00')
            getattr(self, 'afternoon_actual_time_out_minute_var').set('00')
        self.afternoon_actual_time_out_hour_entry.config(state=state)
        self.afternoon_actual_time_out_minute_entry.config(state=state)
        self.afternoon_actual_time_out_ampm_combo.config(state=state)
        self.afternoon_actual_time_out_button.config(state=state)
        self.button_clear_afternoon.config(state=state)

    def update_supposed_time_in_label(self):
        self.current_day = self.selected_date.strftime("%A")
        if self.morning_check.get() and self.afternoon_check.get():
            st = ALLOWED_TIMES.get(self.current_day, {}).get("supposed_time_in")
            sup_in_str = st.strftime("%I:%M %p") if st else "--:-- --"
        elif self.morning_check.get() and not self.afternoon_check.get():
            st = HALF_DAY_TIMES.get(self.current_day)
            sup_in_str = st.strftime("%I:%M %p") if st else "--:-- --"
        elif not self.morning_check.get() and self.afternoon_check.get():
            st = HALF_DAY_TIMES.get(self.current_day)
            sup_in_str = st.strftime("%I:%M %p") if st else "--:-- --"
        else:
            sup_in_str = "--:-- --"

        self.label_supposed_time_in.config(text=f"Supposed Time In: {sup_in_str}")

    def on_date_change(self, event):
        try:
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

            self.update_supposed_time_in_label()
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

        colon_label = ttk.Label(frame, text=":", width=1)
        colon_label.pack(side="left")

        minute_var = tk.StringVar(value='00')
        minute_entry = ttk.Entry(frame, textvariable=minute_var, width=3, justify='center', style="TEntry")
        minute_entry.pack(side="left", padx=(2, 5))
        Tooltip(minute_entry, "Enter minutes (00-59)")
        self.register_time_validation(minute_entry, minute_var, part='minute')

        ampm_var = tk.StringVar(value="AM")
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
                # valid hours: 01..12
                try:
                    if not (1 <= int(value) <= 12):
                        entry.config(foreground='red')
                    else:
                        entry.config(foreground='black' if self.current_theme == 'flatly' else 'white')
                except ValueError:
                    entry.config(foreground='red')
            elif part == 'minute':
                # valid minutes: 00..59
                try:
                    if not (0 <= int(value) <= 59):
                        entry.config(foreground='red')
                    else:
                        entry.config(foreground='black' if self.current_theme == 'flatly' else 'white')
                except ValueError:
                    entry.config(foreground='red')

        var.trace_add('write', validate)

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

        # Morning
        if self.morning_check.get():
            morning_actual_time_in = self.parse_time_input("morning_actual_time_in")
            if not morning_actual_time_in:
                messagebox.showerror("Input Error", "Please enter a valid Actual Time In (Morning) or uncheck it.")
                logging.warning("Invalid Actual Time In for Morning.")
                return

            supposed_time_in_str = self.label_supposed_time_in.cget("text").split(": ", 1)[1]
            try:
                supposed_time_in = datetime.strptime(supposed_time_in_str, "%I:%M %p").time()
            except ValueError:
                supposed_time_in = None

            if not supposed_time_in:
                messagebox.showerror("Error", "Supposed Time In is not set for the selected day.")
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

            # Flexi logic for Suppose Time Out
            day_name = self.current_day
            hour_min = morning_actual_time_in.hour * 60 + morning_actual_time_in.minute

            if day_name == "Monday":
                if hour_min <= 450:  # 7:30am => 450
                    supposed_time_out = time(16, 30)
                else:
                    supposed_time_out = time(17, 0)
            else:
                if hour_min <= 450:
                    supposed_time_out = time(16, 30)
                elif hour_min <= 480:
                    supposed_time_out = time(17, 0)
                else:
                    supposed_time_out = time(17, 30)

            self.label_supposed_time_out.config(
                text=f"Supposed Time Out: {supposed_time_out.strftime('%I:%M %p')}"
            )
        else:
            self.label_morning_late.config(text="Late: 0 minutes")
            self.label_morning_late_deduction.config(text="Late Deduction: 0.000")
            supposed_time_out = None
            self.label_supposed_time_out.config(text="Supposed Time Out: --:-- --")

        # Afternoon
        if self.afternoon_check.get():
            afternoon_actual_time_out = self.parse_time_input("afternoon_actual_time_out")
            if not afternoon_actual_time_out:
                messagebox.showerror("Input Error", "Please enter a valid Actual Time Out (Afternoon) or uncheck it.")
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
        getattr(self, 'afternoon_actual_time_out_hour_var').set('00')
        getattr(self, 'afternoon_actual_time_out_minute_var').set('00')
        getattr(self, 'afternoon_actual_time_out_ampm_var').set('PM')

        self.label_afternoon_undertime.config(text="Undertime: 0 minutes")
        self.label_afternoon_undertime_deduction.config(text="Undertime Deduction: 0.000")
        self.label_deductions.config(text="Total Deduction Points: 0.000")

        logging.info("Cleared Afternoon inputs.")

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        self.master.attributes("-fullscreen", self.fullscreen)
        if self.fullscreen:
            self.button_fullscreen.config(text="Windowed Mode")
            logging.info("Entered full-screen mode.")
        else:
            self.button_fullscreen.config(text="Full Screen")
            logging.info("Exited full-screen mode.")

    def save_record(self):
        try:
            deduction_text = self.label_deductions.cget("text").split(":")[1].strip()
            deduction_points = float(deduction_text)
        except (IndexError, ValueError):
            messagebox.showerror("Error", "Unable to parse deduction points.")
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
                f"A record for {date_str} already exists.\nDo you want to add another record for this date?"
            )
            if not add_record:
                logging.info(f"User chose not to add another record for {date_str}.")
                return

        self.records.append(new_record)
        self.save_records_to_file()
        messagebox.showinfo("Success", f"Record for {date_str} saved successfully.")
        logging.info(f"Record saved for {date_str}: {deduction_points} points.")

        self.current_records = list(self.records)
        self.populate_history()

    def export_history(self):
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

    def show_context_menu(self, event):
        selected_item = self.history_tree.identify_row(event.y)
        if selected_item:
            self.history_tree.selection_set(selected_item)
            self.context_menu.post(event.x_root, event.y_root)

    def edit_record(self):
        selected_items = self.history_tree.selection()
        if len(selected_items) == 0:
            messagebox.showwarning("No Selection", "Please select a record to edit.")
            logging.warning("Edit attempted without selecting a record.")
            return
        if len(selected_items) > 1:
            messagebox.showinfo("Edit Record", "Please select only one record at a time to edit.")
            return

        item = selected_items[0]
        values = self.history_tree.item(item, 'values')
        date_str = values[0]
        morning_in_str = values[1]
        afternoon_out_str = values[4]

        record_index = None
        for i, record in enumerate(self.records):
            if record["date"] == date_str and record["morning_actual_time_in"] == morning_in_str \
               and record["afternoon_actual_time_out"] == afternoon_out_str:
                record_index = i
                break

        if record_index is None:
            messagebox.showerror("Error", "Selected record not found.")
            return

        record_to_edit = self.records[record_index]
        EditRecordDialog(self.master, record_to_edit, self.save_edited_record)

    def save_edited_record(self, updated_record):
        self.recalc_single_record(updated_record)
        self.save_records_to_file()
        self.current_records = list(self.records)
        self.populate_history()
        messagebox.showinfo("Success", f"Record for {updated_record['date']} updated successfully.")
        logging.info(f"Record updated for {updated_record['date']} with new times.")

    def recalc_single_record(self, record):
        date_str = record["date"]
        dt = datetime.strptime(date_str, "%Y-%m-%d").date()
        day_name = dt.strftime("%A")

        morning_in_str = record["morning_actual_time_in"]
        if morning_in_str and morning_in_str != "--:-- --":
            morning_time = self.str_to_time(morning_in_str)
            record["supposed_time_in"] = ALLOWED_TIMES.get(day_name, {}).get("supposed_time_in", "--:-- --").strftime("%I:%M %p") \
                if ALLOWED_TIMES.get(day_name, {}).get("supposed_time_in", None) else "--:-- --"

            try:
                sup_in = datetime.strptime(record["supposed_time_in"], "%I:%M %p").time()
            except:
                sup_in = None

            if sup_in:
                late_raw = self.calculate_time_difference(sup_in, morning_time)
                late_minutes = max(0, late_raw)
            else:
                late_minutes = 0
            record["late_minutes"] = late_minutes

            hour_min = morning_time.hour * 60 + morning_time.minute
            if day_name == "Monday":
                if hour_min <= 450:
                    s_out = time(16, 30)
                else:
                    s_out = time(17, 0)
            else:
                if hour_min <= 450:
                    s_out = time(16, 30)
                elif hour_min <= 480:
                    s_out = time(17, 0)
                else:
                    s_out = time(17, 30)
            record["supposed_time_out"] = s_out.strftime("%I:%M %p")
        else:
            record["morning_actual_time_in"] = "--:-- --"
            record["supposed_time_in"] = "--:-- --"
            record["late_minutes"] = 0
            record["supposed_time_out"] = "--:-- --"

        afternoon_out_str = record["afternoon_actual_time_out"]
        if afternoon_out_str and afternoon_out_str != "--:-- --":
            afternoon_time = self.str_to_time(afternoon_out_str)
            if record["supposed_time_out"] and record["supposed_time_out"] != "--:-- --":
                sup_out_time = datetime.strptime(record["supposed_time_out"], "%I:%M %p").time()
                undertime_raw = self.calculate_time_difference(afternoon_time, sup_out_time)
                undertime_minutes = max(0, undertime_raw)
            else:
                undertime_minutes = 0
            record["undertime_minutes"] = undertime_minutes
        else:
            record["afternoon_actual_time_out"] = "--:-- --"
            record["undertime_minutes"] = 0

        morning_absent = (record["morning_actual_time_in"] == "--:-- --")
        afternoon_absent = (record["afternoon_actual_time_out"] == "--:-- --")
        half_days = 0
        if morning_absent: half_days += 1
        if afternoon_absent: half_days += 1
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
            messagebox.showwarning("No Selection", "Please select a record to delete.")
            logging.warning("Delete attempted without selecting a record.")
            return

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete the selected {len(selected_items)} record(s)?"
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
        self.current_records = list(self.records)
        self.populate_history()
        messagebox.showinfo("Deleted", "Selected record(s) have been deleted.")
        logging.info("Selected record(s) deleted.")

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
                messagebox.showerror("Invalid Range", "From date cannot be after To date.")
                logging.warning("Invalid search date range.")
                return

            filtered_records = [
                record for record in self.records
                if from_date <= datetime.strptime(record["date"], "%Y-%m-%d").date() <= to_date
            ]
            self.current_records = filtered_records
            self.populate_history(filtered_records)
            logging.info(f"Searched records from {from_date} to {to_date}.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", f"Please ensure all search dates are selected correctly.\n{e}")
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
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self.records, f, indent=4)
            logging.info("Records saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save records: {e}")
            logging.error(f"Error saving records: {e}")

    def populate_history(self, records=None):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        if records is None:
            records = self.current_records

        # Default sort by date descending if user hasn't sorted columns:
        if records == self.current_records and not any(self.sort_states.values()):
            records = sorted(records, key=lambda x: x["date"], reverse=True)

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

    def show_help_dialog(self):
        help_window = tk.Toplevel(self.master)
        help_window.title("How to Use - Daily Time Record")
        help_window.grab_set()
        help_window.geometry("700x500")
        self.center_child_window(help_window)

        notebook = ttk.Notebook(help_window)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

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

Default sort: Date = newest first (descending).
Click each column header to toggle ascending/descending.
"""
        label_overview = tk.Text(tab_overview, wrap="word", font=("Inter", 12), bg=help_window.cget("bg"), borderwidth=0)
        label_overview.insert("1.0", overview_content)
        label_overview.config(state="disabled")
        label_overview.pack(fill="both", expand=True, padx=10, pady=10)

        tab_guide = ttk.Frame(notebook)
        notebook.add(tab_guide, text="Step-by-Step Guide")

        guide_content = """Step-by-Step Guide

1. Select the Date (top-left).
2. Check 'Morning' if you worked in the morning; uncheck if absent.
3. Check 'Afternoon' if you worked in the afternoon; uncheck if absent.
4. Enter Actual Time In / Out or click 'Select Time' to pick from a time picker.
5. Click 'Calculate Deductions' to see Late / Undertime / Total points.
6. Click 'Save Record' to store it.
7. 'Export History' => CSV.
8. In the History:
   - Multi-select rows with Ctrl+Click or Shift+Click
   - Press 'Delete' key or right-click => 'Delete Record' to remove them.
   - 'Edit Record' modifies Actual Time In/Out only; deductions auto-recalc.
   - Click column headers to toggle ascending/descending sort.
"""
        label_guide = tk.Text(tab_guide, wrap="word", font=("Inter", 12), bg=help_window.cget("bg"), borderwidth=0)
        label_guide.insert("1.0", guide_content)
        label_guide.config(state="disabled")
        label_guide.pack(fill="both", expand=True, padx=10, pady=10)

        if self.current_theme in ['superhero']:
            label_overview.config(fg="white")
            label_guide.config(fg="white")
        else:
            label_overview.config(fg="black")
            label_guide.config(fg="black")

    def show_about_dialog(self):
        about_window = tk.Toplevel(self.master)
        about_window.title("About - Daily Time Record")
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

Developed by: KCprsnlcc
GitHub: https://github.com/KCprsnlcc

Disclaimer: Use at your own risk. Keep data backups.
"""
        label_about = tk.Text(frame, wrap="word", font=("Inter", 12), bg=about_window.cget("bg"), borderwidth=0)
        label_about.insert("1.0", about_content)
        label_about.config(state="disabled")
        label_about.pack(fill="both", expand=True)

        if self.current_theme in ['superhero']:
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
        self.top.grab_set()

        date_lbl = ttk.Label(self.top, text=f"Date: {record_data['date']}", font=("Inter", 12, "bold"))
        date_lbl.pack(pady=5, anchor="w")

        frame_morn = ttk.LabelFrame(self.top, text="Morning Actual Time In")
        frame_morn.pack(fill="x", expand=True, padx=10, pady=5)

        self.morning_var = tk.StringVar(value=record_data.get("morning_actual_time_in", "--:-- --"))
        self.morning_entry = ttk.Entry(frame_morn, textvariable=self.morning_var, width=20, style="TEntry")
        self.morning_entry.pack(side="left", padx=5, pady=5)

        self.btn_morning_picker = ttk.Button(frame_morn, text="Pick Time",
                                             command=lambda: self.pick_time(self.morning_var))
        self.btn_morning_picker.pack(side="left", padx=5, pady=5)

        frame_after = ttk.LabelFrame(self.top, text="Afternoon Actual Time Out")
        frame_after.pack(fill="x", expand=True, padx=10, pady=5)

        self.afternoon_var = tk.StringVar(value=record_data.get("afternoon_actual_time_out", "--:-- --"))
        self.afternoon_entry = ttk.Entry(frame_after, textvariable=self.afternoon_var, width=20, style="TEntry")
        self.afternoon_entry.pack(side="left", padx=5, pady=5)

        self.btn_afternoon_picker = ttk.Button(frame_after, text="Pick Time",
                                               command=lambda: self.pick_time(self.afternoon_var))
        self.btn_afternoon_picker.pack(side="left", padx=5, pady=5)

        btn_frame = ttk.Frame(self.top)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Save", command=self.on_save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_cancel).pack(side="left", padx=5)

        self.center_dialog()
        self.top.protocol("WM_DELETE_WINDOW", self.on_cancel)

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
