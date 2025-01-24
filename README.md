# **Daily Time Record (DTR) Application**

A user-friendly desktop application to track daily work times, calculate deduction points based on lateness and undertime, and maintain a history of records for easy management.

## **Features**
- 🗓️ **Date Selection**: Easily select a date using dropdown menus for year, month, and day.
- ⏰ **Time Entry**: Record **Morning** and **Afternoon** in/out times with AM/PM selection.
- 🎯 **Accurate Calculations**:
  - Detect lateness and undertime based on predefined schedules.
  - Calculate deduction points and display work durations.
- 💾 **Save Records**: Store daily deductions in a structured format.
- 📜 **History Management**:
  - View all saved records in a detailed table.
  - Edit or delete individual records as needed.
- 📂 **Export to CSV**: Export history for external analysis or backups.
- 🌗 **Theme Switching**: Choose between **Light Mode** and **Dark Mode** for better accessibility.
- 🖥️ **Full-Screen Mode**: Work in a distraction-free, full-screen environment.
- 📖 **Help & Documentation**: Access detailed instructions on using the application via a built-in Help menu.

---

## **Installation**

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/KCprsnlcc/DTR-Calculator.git
   ```
2. **Navigate to the Project Directory**:
   ```bash
   cd daily-time-record
   ```
3. **Set Up a Python Virtual Environment (Optional)**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
5. **Run the Application**:
   ```bash
   python main.py
   ```

---

## **Usage**

### **1. Launch the Application**
Run the application using the command:
```bash
python main.py
```
The application window will open and center itself on your screen.

### **2. Select Date**
Use the dropdown menus at the top to select the year, month, and day. The selected day of the week will be displayed automatically.

### **3. Enter Times**
- Fill in **Morning** and **Afternoon** in/out times using the provided fields or the time picker.
- Select **AM/PM** for each time entry.

### **4. Calculate Deductions**
Click **Calculate Deductions** to:
- View lateness, undertime, and work durations.
- See total deduction points for the day.

### **5. Save Records**
Click **Save Record** to store the calculated deductions. Records are saved in a JSON file for later access.

### **6. View History**
- Review past records in the **Deduction History** table.
- Right-click on a record to **Edit** or **Delete** it.

### **7. Export History**
Export all records to a CSV file using the **Export History** button.

### **8. Customize Themes**
- Switch between **Light Mode** and **Dark Mode** for better accessibility.
- Font colors automatically adjust for readability.

### **9. Use Full-Screen Mode**
Click **Full Screen** to expand the application to full screen. Use the same button to toggle back to windowed mode.

### **10. Get Help**
Access detailed instructions on using the application via the **Help** menu.

---


## **Folder Structure**
```
daily-time-record/
│
├── dtr_app.py              # Main application file
├── requirements.txt        # Python dependencies
├── dtr_records.json        # Saved records (auto-generated)
├── README.md               # Documentation
├── assets/                 # Images and other assets
└── logs/                   # Log files (auto-generated)
```

---

## **Dependencies**

This project requires the following Python packages:

- `ttkbootstrap`: For modern GUI design.
- `tkinter`: Python's standard GUI toolkit.
- `pandas`: For CSV export functionality.
- `json`: For saving records.
- `datetime`: For handling date and time operations.

Install all dependencies with:
```bash
pip install -r requirements.txt
```

---

## **Contributing**

We welcome contributions! Here's how you can help:

1. **Fork the Repository**: Click the "Fork" button on the top-right corner of this page.
2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/KCprsnlcc/DTR-Calculator.git
   ```
3. **Create a Branch**:
   ```bash
   git checkout -b main
   ```
4. **Make Changes**: Improve the application or fix bugs.
5. **Test Your Changes**: Ensure everything works as expected.
6. **Commit Your Changes**:
   ```bash
   git commit -m "Add your commit message here"
   ```
7. **Push Your Branch**:
   ```bash
   git push origin main
   ```
8. **Open a Pull Request**: Navigate to the original repository and submit your pull request.

---

## **License**

This project is licensed under the **License**. See the [LICENSE](LICENSE) file for details.

---

## **Acknowledgements**

- **Python Community** for the amazing resources and support.
- **Contributors** for their efforts in improving the application.

---

## **Contact**

For any questions or support, please contact:

**Khadaffe Abubakar Sulaiman**  
**Email**: kcpersonalacc@gmail.com
**GitHub**: [KCprsnlcc](https://github.com/KCprsnlcc)

---