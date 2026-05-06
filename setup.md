# Backend Setup

This document explains how to set up and run the backend in a Python virtual environment on Windows.

## 1. Open Terminal

1. Open a terminal or PowerShell window.
2. Change directory to the backend folder:

```powershell
cd C:\Users\varu9\OneDrive\Desktop\Projects\ps3\backend
```

## 2. Create a Virtual Environment

Create a virtual environment named `venv`:

```powershell
python -m venv venv
```

If your system uses `python3`, run:

```powershell
python3 -m venv venv
```

## 3. Activate the Virtual Environment

Activate the environment with:

```powershell
venv\Scripts\Activate.ps1
```

If you see an execution policy error, run this command first in PowerShell as administrator or temporarily for the current session:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again:

```powershell
venv\Scripts\Activate.ps1
```

## 4. Install Requirements

Install the required Python packages:

```powershell
pip install -r requirements.txt
```

## 5. Verify Installation

Check that the packages installed correctly:

```powershell
pip list
```

## 6. Use the Backend

After activation, run backend scripts from the `backend` directory. For example:

```powershell
python data_pipeline/engine/main.py
```

> Keep the virtual environment activated while working on the backend. When done, deactivate it with:

```powershell
deactivate
```
