# GRIT Interview Hub — Streamlit Prototype

## 1. Requirements
- Python 3.10 or newer
- VS Code
- Internet connection for installing Streamlit

## 2. Open in VS Code
1. Extract this ZIP.
2. Open the `grit_interview_hub` folder in VS Code.
3. Open Terminal → New Terminal.

## 3. Create and activate a virtual environment

### Windows PowerShell
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

## 4. Install dependencies
```bash
pip install -r requirements.txt
```

## 5. Run
```bash
streamlit run app.py
```
Streamlit opens the app in your browser. The SQLite database `grit_interviews.db` is created automatically in the same folder.

## 6. Demo walkthrough
1. **Student**: Select Aarav Kumar. See a confirmed booking. Select Diya Sharma to see a passed interview and awarded badge. Select Ishaan Reddy to see the retake state. Select Meera Nair to see ineligibility due to attendance.
2. **Interviewer**: Select an interviewer, publish a future slot, open the daily schedule, and record Pass / Fail / Retake for a scheduled interview.
3. **Interview Team**: Review eligible students who booked / have not booked, edit demo eligibility, and test the malpractice action. A previously awarded badge becomes nullified while the interview record remains.
4. Refresh the browser to demonstrate that records persist in SQLite.

## 7. Reset demo data
Stop Streamlit, delete `grit_interviews.db`, then run the app again. The database and sample records will be recreated.

## 8. Prototype limitations
This is an assessment prototype, not a production deployment. It uses a role selector instead of real authentication, local SQLite instead of a hosted database, and on-screen messages instead of email/WhatsApp notifications. Production should add secure authentication, RBAC, timezone handling, transactional booking with database constraints, notification delivery, rescheduling approvals, retention policies, and comprehensive audit logging.
