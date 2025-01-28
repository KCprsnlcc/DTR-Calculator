# Daily Time Record (DTR) Calculator

A user-friendly desktop application to track daily work times, calculate deduction points based on lateness and undertime, and maintain a history of records for easy management.

## 🛠️ **Features**

- **🗓️ Date Selection**
  - Easily select a date using dropdown menus for year, month, and day.
  - Automatically displays the selected day of the week.

- **⏰ Time Entry**
  - Record **Morning** and **Afternoon** in/out times with AM/PM selection.
  - Utilize a built-in time picker for accurate time selection.
  - Validate time inputs with real-time feedback.

- **🎯 Accurate Calculations**
  - Detect lateness and undertime based on predefined schedules.
  - Calculate deduction points and display work durations.
  - Support for half-day absences.
  - Flexi Time Out logic to adjust supposed time out based on actual time in.

- **💾 Save Records**
  - Store daily deductions in a structured JSON format.
  - Prevent duplicate records for the same date with user confirmation.

- **📜 History Management**
  - View all saved records in a detailed and sortable table.
  - Multi-selection for batch deletion.
  - Single-record editing with automatic recalculations.
  - Search records within a specified date range.

- **📂 Export to CSV**
  - Export history for external analysis or backups.

- **🌗 Theme Switching**
  - Choose between **Light Mode** and **Dark Mode** for better accessibility.
  - Automatic adjustment of text and background colors based on the selected theme.

- **🖥️ Full-Screen Mode**
  - Work in a distraction-free, full-screen environment.

- **📖 Help & Documentation**
  - Access detailed instructions on using the application via a built-in Help menu.

- **🔒 Data Integrity**
  - Robust error handling and input validation to ensure data accuracy.
  - Logging of application activities for troubleshooting and audit purposes.

## 🚀 **Installation**

1. **Clone the Repository**
   ```bash
   git clone https://github.com/KCprsnlcc/DTR-Calculator.git
   ```

2. **Navigate to the Project Directory**
   ```bash
   cd DTR-Calculator
   ```

3. **Set Up a Python Virtual Environment (Optional but Recommended)**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the Application**
   ```bash
   python main.py
   ```

## 📝 **Usage**

### **1. Launch the Application**
Run the application using the command:
```bash
python main.py
```
The application window will open and center itself on your screen.

### **2. Select Date**
- Use the dropdown menus at the top to select the **Year**, **Month**, and **Day**.
- The selected day of the week will be displayed automatically.

### **3. Enter Times**
- **Morning Section:**
  - Check **"Include Morning"** if you worked in the morning.
  - Enter **Actual Time In** using the fields or the **"Select Time"** button.
  
- **Afternoon Section:**
  - Check **"Include Afternoon"** if you worked in the afternoon.
  - Enter **Actual Time Out** using the fields or the **"Select Time"** button.

### **4. Calculate Deductions**
Click **"Calculate Deductions"** to:
- View lateness, undertime, and work durations.
- See total deduction points for the day.

### **5. Save Records**
Click **"Save Record"** to store the calculated deductions. Records are saved in a JSON file (`dtr_records.json`) for later access.

### **6. View History**
- Review past records in the **Deduction History** table.
- **Edit Record:** Right-click on a record and select **"Edit Record"** to modify actual times. The application will automatically recalculate deductions.
- **Delete Record(s):** Select one or multiple records and press the **"Delete"** key or right-click and choose **"Delete Record"**.

### **7. Export History**
Export all records to a CSV file using the **"Export History"** button for external analysis or backups.

### **8. Customize Themes**
- Switch between **Light Mode** and **Dark Mode** using the respective buttons at the top.
- The application will adjust colors for optimal readability based on the selected theme.

### **9. Use Full-Screen Mode**
Click **"Full Screen"** to expand the application to full screen for a distraction-free workspace. Click again to toggle back to windowed mode.

### **10. Access Help**
Navigate to the **Help** menu to access:
- **How to Use:** Detailed instructions on using the application.
- **About:** Information about the application, contributors, and contact details.

## 📂 **Folder Structure**

```
DTR-Calculator/
│
├── build/                  # Build outputs
│   └── DTR Calculator      # Application build folder
│
├── dist/                   # Distribution folder
│   └── DTR Calculator      # Application distribution folder
│
├── .gitignore              # Git ignore file
├── DTR Calculator.spec     # PyInstaller spec file
├── README.md               # Documentation
├── dtr_app.log             # Application log
├── dtr_records.json        # Saved records
├── icon.ico                # Application icon
├── main.py                 # Main application file
└── requirements.txt        # Python dependencies
```

## 📦 **Dependencies**

This project requires the following Python packages:

- `ttkbootstrap`: For modern GUI design.
- `tkinter`: Python's standard GUI toolkit (usually included with Python).
- `pandas`: For CSV export functionality.
- `json`: For saving records.
- `datetime`: For handling date and time operations.
- `logging`: For application logging.
- `calendar`: For date-related functionalities.

Install all dependencies with:
```bash
pip install -r requirements.txt
```

### **`requirements.txt`**
```plaintext
ttkbootstrap
pandas
```

*Note: `tkinter`, `json`, `datetime`, `logging`, and `calendar` are part of Python's standard library and do not need to be installed separately.*

## 🤝 **Contributing**

We welcome contributions! Here's how you can help:

1. **Fork the Repository**
   Click the "Fork" button on the top-right corner of this page.

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/KCprsnlcc/DTR-Calculator.git
   ```

3. **Create a Branch**
   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Changes**
   Improve the application or fix bugs.

5. **Test Your Changes**
   Ensure everything works as expected.

6. **Commit Your Changes**
   ```bash
   git commit -m "Add your commit message here"
   ```

7. **Push Your Branch**
   ```bash
   git push origin feature/YourFeatureName
   ```

8. **Open a Pull Request**
   Navigate to the original repository and submit your pull request.

## 📝 **License**

This project is licensed under the **License**. See the [License](LICENSE.md) file for details.

## 🎉 **Acknowledgements**

- **Python Community** for the amazing resources and support.
- **ttkbootstrap** contributors for enhancing Tkinter's aesthetics.
- **Contributors** for their efforts in improving the application.

## 📞 **Contact**

For any questions or support, please contact:

**Khadaffe Abubakar Sulaiman**  
**Email**: [kcpersonalacc@gmail.com](mailto:kcpersonalacc@gmail.com)  
**GitHub**: [KCprsnlcc](https://github.com/KCprsnlcc)

---

## 🔧 **Troubleshooting**

- **Application Fails to Launch**
  - Ensure all dependencies are installed correctly.
  - Check if Python is added to your system's PATH.

- **Cannot Save Records**
  - Verify that the application has write permissions to the directory.
  - Ensure that `dtr_records.json` is not open in another program.

- **Theme Not Changing**
  - Restart the application to apply theme changes.
  - Ensure that the selected theme is supported.

For further assistance, please open an issue on the [GitHub repository](https://github.com/KCprsnlcc/DTR-Calculator/issues).

---

## 🛠️ **Future Improvements**

- **Biometric Integration**
  - Integrate fingerprint or facial recognition for secure time tracking.

- **Cloud Syncing**
  - Sync records across multiple devices using cloud storage solutions.

- **Mobile Application**
  - Develop a mobile version for on-the-go time tracking.

- **Advanced Reporting**
  - Generate detailed reports and visualizations of work patterns.

---

Thank you for using the **Daily Time Record (DTR) Calculator**! We hope it helps you manage your time.