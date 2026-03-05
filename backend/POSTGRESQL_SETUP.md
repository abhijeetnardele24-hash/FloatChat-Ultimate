# PostgreSQL Setup Instructions for FloatChat Ultimate

## 🎯 Quick Setup Guide

### Step 1: Run the Database Setup Script

1. **Open the backend folder:**
   ```
   cd c:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate\backend
   ```

2. **Run the setup script:**
   ```
   .\setup-database.bat
   ```

3. **Enter your PostgreSQL password** when prompted
   - This is the password you set when you installed PostgreSQL
   - The script will create:
     - User: `floatchat_user`
     - Database: `floatchat`
     - All tables, indexes, and views

### Step 2: Restart the Backend

After the database is set up:

```bash
# Stop the current backend (Ctrl+C)
cd c:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate\backend
python main.py
```

**Note:** Use `main.py` (not `main_local.py`) for PostgreSQL

### Step 3: Test the Multi-LLM System

```bash
# Test providers
Invoke-WebRequest -Uri "http://localhost:8000/api/chat/providers" -UseBasicParsing | Select-Object -ExpandProperty Content

# Test Ollama chat
$body = @{ message = "How many floats are there?" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

# Test Gemini chat
$body = @{ message = "What causes ocean currents?"; provider = "gemini" } | ConvertTo-Json
Invoke-WebRequest -Uri "http://localhost:8000/api/chat" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
```

---

## 🔧 What Was Fixed

### 1. Gemini Model Issue ✅
- **Problem:** API key only had access to preview models
- **Solution:** Updated to use `models/deep-research-pro-preview-12-2025`
- **File:** `backend/llm/gemini_engine.py`

### 2. Ollama Model Name ✅
- **Problem:** Was set to `llama2` but you have `mistral` installed
- **Solution:** Updated to `mistral`
- **File:** `backend/.env`

### 3. PostgreSQL Setup ✅
- **Created:** `setup-database.bat` - Automated setup script
- **Creates:** User, database, tables, indexes, views
- **Runs:** `init-db.sql` + `db-enhancements.sql`

---

## 📊 Expected Results

### After Running setup-database.bat:

```
========================================
Database setup complete!
========================================

Database: floatchat
User: floatchat_user
Password: floatchat_password_dev
```

### After Starting Backend (main.py):

```
INFO: Gemini engine initialized with model: models/deep-research-pro-preview-12-2025
INFO: Ollama engine initialized
INFO: ARGO filter router loaded successfully
INFO: Application startup complete
INFO: Uvicorn running on http://0.0.0.0:8000
```

### Provider Health Check:

```json
{
  "providers": ["ollama", "gemini"],
  "health": {
    "ollama": {"available": true, "status": "healthy"},
    "gemini": {"available": true, "status": "healthy"}
  }
}
```

---

## ⚠️ Troubleshooting

### If setup-database.bat fails:

**Error: "User already exists"**
- The user was already created
- Skip to Step 2 in the script manually

**Error: "Database already exists"**
- The database was already created
- Just run the SQL files manually:
  ```bash
  & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U floatchat_user -d floatchat -f init-db.sql
  & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U floatchat_user -d floatchat -f db-enhancements.sql
  ```

### If backend fails to start:

**Error: "could not connect to server"**
- Make sure PostgreSQL service is running
- Check Windows Services → PostgreSQL

**Error: "database does not exist"**
- Run `setup-database.bat` first

---

## 🎯 Next Steps After Setup

1. **Test the chat** - Try both Ollama and Gemini
2. **Check the API docs** - Visit http://localhost:8000/docs
3. **Continue to Phase C** - ARGO data pipeline
4. **Add Mapbox** - Real interactive maps

---

## 📝 Configuration Summary

**Database:**
- Host: localhost
- Port: 5432
- Database: floatchat
- User: floatchat_user
- Password: floatchat_password_dev

**LLMs:**
- Ollama: mistral (local, private)
- Gemini: deep-research-pro-preview (cloud, general knowledge)

**Backend:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Mode: PostgreSQL (production-ready)
