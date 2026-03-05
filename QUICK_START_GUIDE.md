# 🚀 FloatChat Ultimate - Quick Start Guide

## **STEP 1: Install PostgreSQL (5 minutes)**

### **Option A: Download Installer (Recommended)**
1. Go to: https://www.postgresql.org/download/windows/
2. Download **PostgreSQL 16** for Windows
3. Run installer with these settings:
   - Password for `postgres` user: `admin1234`
   - Port: `5432` (default)
   - Install all components

### **Option B: Chocolatey (if you have it)**
```powershell
choco install postgresql --params '/Password:admin1234'
```

## **STEP 2: Create Database**

1. Open **pgAdmin 4** (installed with PostgreSQL)
2. Connect to server with:
   - Username: `postgres`
   - Password: `admin1234`
3. Right-click on "Databases" → "Create" → "Database"
4. Name it: `floatchat`
5. Run this SQL in Query Tool:
```sql
CREATE USER floatchat_user WITH PASSWORD '1234';
GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;
```

## **STEP 3: Apply Database Schema**

```powershell
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate"
psql -U floatchat_user -d floatchat -f backend/init-db.sql
```
*(Enter password: `1234`)*

---

## **STEP 4: Start the Applications**

### **Start Backend (Terminal 1)**
```powershell
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate\backend"
python -m uvicorn main_local:app --reload --port 8000
```

### **Start Frontend (Terminal 2)**
```powershell
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate"
npm run dev
```

---

## **STEP 5: Test the Applications**

### **Frontend Testing**
1. Open: http://localhost:3000
2. Go to **Chat** page
3. Select **"Groq (Llama 3.3 70B)"** provider
4. Ask: "What are ARGO floats and how do they work?"
5. **Expected**: Detailed oceanographic explanation

### **Backend Testing**
1. Open: http://localhost:8000/docs
2. Try the `/api/chat` endpoint
3. Test with Groq provider

---

## **STEP 6: Run ARGO Data Ingestion (Optional)**

### **Small Test Batch (10 profiles)**
```powershell
cd backend
python data_ingestion/argo_ingestion.py --region global --start-date 2024-01-01 --max-profiles 10 --index-limit 200 --cache-dir data/argo --sleep-seconds 0.5
```

### **Full 5-Year Ingestion (Run Overnight)**
```powershell
cd backend
python data_ingestion/argo_ingestion.py --region global --start-date 2021-01-01 --end-date 2026-02-27 --max-profiles 50000 --index-limit 200000 --cache-dir data/argo --sleep-seconds 0.05
```

---

## **🎯 What You'll See After Setup:**

### **Working Features:**
- ✅ **Groq AI Chat** - Fast, intelligent oceanographic answers
- ✅ **Multi-LLM Support** - Groq, Gemini, OpenAI, Ollama
- ✅ **ARGO Data APIs** - Filter and explore ocean data
- ✅ **Visualizations** - Depth profiles and T-S diagrams
- ✅ **Authentication** - JWT-based login system
- ✅ **Workspaces** - Save research sessions

### **Test URLs:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Chat Interface**: http://localhost:3000/chat

---

## **🔧 Troubleshooting:**

### **PostgreSQL Issues:**
- **"Connection refused"**: Make sure PostgreSQL service is running
- **"Password authentication failed"**: Check username/password
- **"Database doesn't exist"**: Run the CREATE DATABASE command

### **Backend Issues:**
- **"Module not found"**: Run `pip install -r requirements.txt`
- **"Port already in use"**: Change port or kill existing process

### **Frontend Issues:**
- **"Module not found"**: Run `npm install`
- **"Port already in use"**: Run `npm run dev` on different port

---

## **🚀 Ready to Test!**

Once PostgreSQL is set up and both applications are running, you'll have a fully functional oceanographic AI platform with real-time access to Groq's Llama 3.3 70B model!
