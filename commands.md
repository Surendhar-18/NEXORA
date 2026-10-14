To run **NEXORA** completely (both the FastAPI backend and the React + Vite frontend), open two separate terminal windows in your project root:

---

### Terminal 1 — Backend (FastAPI + Uvicorn)

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

* **API Server:** `http://127.0.0.1:8000`
* **Interactive API Docs (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Alternative Docs (ReDoc):** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### Terminal 2 — Frontend (React + Vite)

```powershell
cd frontend
npm run dev
```

* **Web Application UI:** [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

### Initial Setup & Installation (If running for the first time)

If you haven't installed dependencies yet:

1. **Python Dependencies:**
   ```powershell
   pip install -r backend/requirements.txt
   ```
2. **Frontend Dependencies:**
   ```powershell
   cd frontend
   npm install
   ```

---

### Running Automated Verification & Tests

* **Run Backend Automated Test Suite:**
  ```powershell
  pytest tests/ -v
  ```
* **Verify Frontend Type Checking & Production Build:**
  ```powershell
  cd frontend
  npm run build
  ```