# 💸 Smart Expense Tracker with Chatbot & Analysis

A personal finance management web app built using Flask. It allows users to track income and expenses, analyze spending via visualizations, and ask queries through a smart financial chatbot.

---

## 🔧 Features

- ✅ Signup/Login with wallet integration  
- ✅ Add, view, delete income & expense transactions  
- ✅ Filter and sort by type, category, or date  
- ✅ Sidebar navigation (Add, Chatbot, Analysis)  
- ✅ Data visualizations (Pie/Bar Charts of expenses)  
- ✅ 🤖 Chatbot using HuggingFace's QA model (`deepset/roberta-base-squad2`)  
- ✅ Clean black UI theme with sidebar design  

---

## 🛠 Tech Stack

- **Backend:** Flask, SQLAlchemy, Flask-Login  
- **Frontend:** HTML, Bootstrap 5, Jinja2  
- **Database:** SQLite  
- **ML Model:** HuggingFace Transformers (QA pipeline)  
- **Visualization:** Matplotlib  
- **Styling:** Custom CSS (Dark Theme)

---

## 💻 Installation

```bash
git clone https://github.com/sathanya/expense-tracker.git
cd expense-tracker
pip install -r requirements.txt
python app.py
