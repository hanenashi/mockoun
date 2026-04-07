@echo off
echo === Starting Mockoun Environment ===

echo Activating virtual environment...
call venv\Scripts\activate

echo [0/3] Running Environment Bridge...
python bridge.py

echo [1/3] Starting Mockoun Server (Backend) on port 5000...
start "Mockoun Backend" cmd /k "call venv\Scripts\activate && python app.py"

echo [2/3] Starting Frontend UI Server on port 8000...
start "Mockoun Frontend" cmd /k "python -m http.server 8000"

echo Waiting for servers to boot...
timeout /t 3 /nobreak >nul

echo Opening GUI in your default browser...
start http://localhost:8000

echo [3/3] Launching MurkyPond Harvester...
python harvester.py

echo ===================================
echo Harvester script finished. 
echo You can close the other server windows when you are done.
echo ===================================
pause