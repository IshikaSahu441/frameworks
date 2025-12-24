@echo off
echo ================================================================================
echo   Intelligent Real-Time Patient Flow Optimization System
echo   Activating Python 3.12 Environment
echo ================================================================================
echo.

call .venv312\Scripts\activate.bat

echo Environment activated: Python 3.12
echo.
echo Running complete project...
echo.

python execute_complete_project.py

pause
