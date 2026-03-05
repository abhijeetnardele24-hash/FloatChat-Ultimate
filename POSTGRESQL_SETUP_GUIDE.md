# PostgreSQL Setup Guide for FloatChat
## Native Windows Installation (No Docker)

### **Step 1: Download and Install PostgreSQL 16**

1. **Download**: https://www.postgresql.org/download/windows/
2. **Run installer** with these settings:
   - Password for `postgres` user: `admin1234` (remember this)
   - Port: `5432` (default)
   - Install components: PostgreSQL Server, pgAdmin 4, Stack Builder
   - Locale: Default (C)

### **Step 2: Create FloatChat Database**

Open **pgAdmin 4** (installed with PostgreSQL) and run this SQL:

```sql
-- Create user and database
CREATE USER floatchat_user WITH PASSWORD '1234';
CREATE DATABASE floatchat OWNER floatchat_user;
GRANT ALL PRIVILEGES ON DATABASE floatchat TO floatchat_user;

-- Connect to floatchat database and run schema
-- (Use the file: backend/init-db.sql)
```

### **Step 3: Apply Database Schema**

```powershell
# Navigate to project directory
cd "C:\Users\Abhijeet Nardele\OneDrive\Desktop\Edi project\floatchat-ultimate"

# Apply schema (replace with your postgres password if different)
psql -U floatchat_user -d floatchat -f backend/init-db.sql
```

### **Step 4: Update Environment Variables**

Create/update `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg2://floatchat_user:1234@localhost:5432/floatchat
GROQ_API_KEY=gsk_****************************  # Add your real key in backend/.env only
GROQ_MODEL=llama-3.3-70b-versatile
```

### **Step 5: Verify Installation**

```powershell
# Test database connection
python backend/test_smoke_api.py

# Should show: "database: connected"
```

### **Troubleshooting**

- **"psql not recognized"**: Add PostgreSQL bin to PATH or use full path
- **Connection refused**: Make sure PostgreSQL service is running
- **Permission denied**: Check username/password in connection string

### **Services Status**

After setup, you should have:
- ✅ **PostgreSQL**: Running on port 5432
- ✅ **Backend**: Can connect to database
- ✅ **Data Ready**: Schema applied, ready for ARGO ingestion

---

**Next**: Run ARGO data ingestion to populate the database with real ocean data.
