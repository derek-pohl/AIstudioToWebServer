@echo off
echo ================================================
echo AI Studio Automated API Server - Setup
echo ================================================
echo.
echo This script will help you set up the automated system.
echo.
echo Prerequisites:
echo - Python 3.8+ installed
echo - Git (optional, for cloning)
echo.
pause
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
echo.
echo Installing Playwright browsers...
python -m playwright install
echo.
echo Running configuration setup...
python setup.py
echo.
echo ================================================
echo Setup complete!
echo ================================================
echo.
echo To start the server, run: python api_server.py
echo.
pause
