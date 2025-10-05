# 🎨 Frontend Web UI Guide

## 🎉 **Your Web Interface is Ready!**

I've created a beautiful, user-friendly web interface for your personal finance application.

---

## 🚀 **How to Access**

### **Start the Server:**

```bash
cd /Users/mmultra21/Documents/retro21_finance
source venv/bin/activate
python test_api_server.py
```

### **Open in Browser:**

**Main Interface:** http://127.0.0.1:8000/

**API Docs:** http://127.0.0.1:8000/docs

---

## 📱 **Features Overview**

### **1. Overview Tab** 📊
- **Financial snapshot** at a glance
- Total Income, Expenses, Savings
- Savings Rate calculation
- Clean, card-based layout

**What you can do:**
- View your current financial status
- Refresh data with one click
- See key metrics instantly

### **2. AI Narratives Tab** 🤖
- **Generate natural language** financial insights
- Choose from multiple templates
- Input your financial data
- Get AI-powered summaries

**What you can do:**
- Select a narrative template (Monthly Summary, Spending Insight, Budget Progress)
- Enter your financial data (income, expenses, savings, categories)
- Click "Generate Narrative" to get AI-written insights
- View token usage and generation metadata

**Requirements:**
- LLM server must be running (either real Hermes or mock server)

### **3. Forms Tab** 📄
- View available tax forms
- See which forms can be auto-filled
- Quick access to form filling features

**What you can do:**
- Browse available forms (IRS-433A, Budget Worksheet, etc.)
- Refresh forms list
- Prepare for automated form filling

### **4. Import Data Tab** 📥
- **Upload CSV files** from your bank
- Import transactions automatically
- Support for multiple banks

**What you can do:**
- Select your bank from dropdown
- Upload a CSV file with transactions
- See import results (how many transactions imported)

---

## 🎨 **User Interface Features**

### **Status Indicators**
Top-right corner shows:
- **🟢 API Online** - Backend server is running
- **🟢 LLM Online** - AI server is available
- **🔴 Offline** - Service not available

### **Responsive Design**
- Works on desktop, tablet, and mobile
- Clean, modern interface
- Gradient purple theme
- Card-based layout

### **Interactive Elements**
- Tab-based navigation
- Hover effects on buttons
- Real-time status updates
- Error notifications

---

## 💡 **How to Use**

### **Complete Workflow Example:**

#### **Step 1: Start Both Servers**

```bash
# Terminal 1 - LLM Server (optional)
python mock_hermes_server.py
# OR for real Hermes:
# ./run_hermes3.sh

# Terminal 2 - API Server
python test_api_server.py
```

#### **Step 2: Open the Web UI**

Open your browser to: **http://127.0.0.1:8000/**

#### **Step 3: Check Status**

Look at the top-right corner:
- Both indicators should be **🟢 Green** (Online)
- If red, check that servers are running

#### **Step 4: Generate a Narrative**

1. Click **"AI Narratives"** tab
2. Select template: **"MONTHLY_SUMMARY"**
3. Fill in your data:
   - Total Income: `$5,000`
   - Total Expenses: `$3,200`
   - Net Savings: `$1,800`
   - Top Category: `Housing`
4. Click **"✨ Generate Narrative"**
5. Read the AI-generated summary!

#### **Step 5: Import Transactions (Future)**

1. Click **"Import Data"** tab
2. Select your bank
3. Upload CSV file
4. View import results

---

## 🛠️ **Technical Details**

### **Files Created:**

```
frontend/
├── index.html              # Main HTML page
├── static/
    ├── css/
    │   └── style.css       # Stylesheet
    └── js/
        └── app.js          # JavaScript functionality
```

### **Technologies Used:**

- **Frontend:** Vanilla HTML/CSS/JavaScript (no frameworks needed!)
- **API Calls:** Fetch API for REST communication
- **Styling:** Modern CSS with gradients, flexbox, grid
- **Backend:** FastAPI serving both API and static files

### **API Endpoints Used:**

- `GET /health` - Check API status
- `GET /narrate/templates` - Load narrative templates
- `POST /narrate` - Generate AI narratives
- `GET /forms/available` - List available forms
- `POST /ingest/csv` - Import CSV transactions (future)

---

## 🎯 **What Works Right Now**

✅ **Working:**
- Beautiful UI loads at http://127.0.0.1:8000/
- Status indicators show server health
- Navigate between tabs
- Load narrative templates
- Generate AI narratives (with LLM running)
- View available forms
- Responsive design

⚠️ **Limited (Sample Data):**
- Overview tab shows sample data
- Real transaction import requires full database setup

---

## 🚀 **Next Steps to Enhance**

### **Add Real Data:**
To connect to actual database:
1. Install DuckDB: `pip install duckdb pandas`
2. Initialize database: `python init_database.py`
3. Import real transactions via CSV upload

### **Add More Features:**
- Transaction history table
- Charts and graphs (add Chart.js)
- Budget tracking
- Category breakdown pie charts
- Monthly trends

### **Customize:**
- Edit `frontend/static/css/style.css` for colors/styles
- Modify `frontend/static/js/app.js` for functionality
- Update `frontend/index.html` for layout changes

---

## 📸 **What You'll See**

When you open http://127.0.0.1:8000/:

```
╔════════════════════════════════════════════╗
║  💰 Personal Finance Dashboard             ║
║  🟢 API Online  🟢 LLM Online             ║
╠════════════════════════════════════════════╣
║ [Overview] [AI Narratives] [Forms] [Import]║
╠════════════════════════════════════════════╣
║                                            ║
║  📊 Financial Overview                     ║
║                                            ║
║  ┌─────────┐ ┌──────────┐ ┌────────────┐ ║
║  │ Income  │ │ Expenses │ │  Savings   │ ║
║  │ $5,250  │ │ $3,848   │ │  $1,402    │ ║
║  └─────────┘ └──────────┘ └────────────┘ ║
║                                            ║
║  [Refresh Data]                            ║
╚════════════════════════════════════════════╝
```

---

## ❓ **Troubleshooting**

### **Problem: Page won't load**
```bash
# Check if server is running
curl http://127.0.0.1:8000/

# Restart server
python test_api_server.py
```

### **Problem: LLM status shows red**
```bash
# Start LLM server
python mock_hermes_server.py

# Or real Hermes
./run_hermes3.sh
```

### **Problem: Narrative generation fails**
- Make sure LLM status is 🟢 Green
- Check that you selected a template
- Verify data is filled in
- Check browser console for errors (F12)

### **Problem: Styles look broken**
```bash
# Verify files exist
ls -la frontend/static/css/style.css
ls -la frontend/static/js/app.js

# Check browser console (F12) for 404 errors
```

---

## 🎨 **Customization**

### **Change Colors:**

Edit `frontend/static/css/style.css`:

```css
:root {
    --primary: #2563eb;      /* Change to your color */
    --primary-dark: #1e40af; /* Darker shade */
}
```

### **Add Your Logo:**

Edit `frontend/index.html`:

```html
<h1>
    <img src="/static/logo.png" alt="Logo">
    Personal Finance Dashboard
</h1>
```

### **Modify Templates:**

Edit `test_api_server.py` to add more narrative templates in the `get_narrative_templates()` function.

---

## 📚 **Summary**

You now have a **complete web-based interface** for your personal finance application!

**To use it:**
1. Start the server: `python test_api_server.py`
2. Open browser: http://127.0.0.1:8000/
3. Enjoy your beautiful finance dashboard!

**All files are in:**
- `/Users/mmultra21/Documents/retro21_finance/frontend/`

Happy budgeting! 💰✨
