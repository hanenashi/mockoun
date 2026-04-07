@echo off
echo === Mockoun + MurkyPond Setup ===

echo [1/4] Creating Python virtual environment...
python -m venv venv

echo [2/4] Activating virtual environment...
call venv\Scripts\activate

echo [3/4] Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo [4/4] Installing Playwright Chromium browser...
playwright install chromium

echo ===================================
echo Setup complete! 
echo Make sure your .env and serviceAccountKey.json are in this folder.
echo You can now run the environment using run.bat
echo ===================================
pause