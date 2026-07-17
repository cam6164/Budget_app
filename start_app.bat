@echo off
setlocal EnableExtensions
cd /d "%~dp0"

rem Reutiliser en priorite l'environnement virtuel deja cree.
if /I "%~1"=="--check-python" goto :detect_python
if not exist ".venv\Scripts\python.exe" goto :detect_python
".venv\Scripts\python.exe" -c "import sys" >nul 2>&1
if not errorlevel 1 goto :dependencies
echo L'environnement Python local semble endommage. Tentative de reparation...

:detect_python
set "PYTHON_EXE="
set "PYTHON_ARGS="

py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 goto :use_py312

py -3.11 -c "import sys" >nul 2>&1
if not errorlevel 1 goto :use_py311

py -c "import sys" >nul 2>&1
if not errorlevel 1 goto :use_py

python -c "import sys" >nul 2>&1
if not errorlevel 1 goto :use_python

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" goto :use_local312
if exist "%LocalAppData%\Programs\Python\Python311\python.exe" goto :use_local311
if exist "%LocalAppData%\Programs\Python\Python314\python.exe" goto :use_local314
if exist "%LocalAppData%\Programs\Python\Python313\python.exe" goto :use_local313

echo Python n'est pas installe. Installe Python 3.11 ou 3.12 puis relance l'application.
echo.
pause
exit /b 1

:use_py312
set "PYTHON_EXE=py"
set "PYTHON_ARGS=-3.12"
goto :create_venv

:use_py311
set "PYTHON_EXE=py"
set "PYTHON_ARGS=-3.11"
goto :create_venv

:use_py
set "PYTHON_EXE=py"
goto :create_venv

:use_python
set "PYTHON_EXE=python"
goto :create_venv

:use_local312
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
goto :create_venv

:use_local311
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python311\python.exe"
goto :create_venv

:use_local314
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python314\python.exe"
goto :create_venv

:use_local313
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python313\python.exe"
goto :create_venv

:create_venv
if /I "%~1"=="--check-python" goto :check_python
echo Creation de l'environnement Python local...
"%PYTHON_EXE%" %PYTHON_ARGS% -m venv .venv
if errorlevel 1 goto :error

:dependencies
if /I "%~1"=="--check" goto :check

echo Verification des dependances...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :error

echo Arret des anciennes instances de Budget_app...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop_existing_streamlit.ps1" -Port 8501
if errorlevel 1 goto :error

echo Lancement de Suivi budget et finances...
".venv\Scripts\python.exe" -m streamlit run app.py --server.port=8501 --server.fileWatcherType=poll
if errorlevel 1 goto :error
exit /b 0

:check
".venv\Scripts\python.exe" -c "import importlib.util, streamlit, pandas, plotly, openpyxl; assert importlib.util.find_spec('st_aggrid'); print('Verification du lanceur reussie.')"
if errorlevel 1 goto :error
exit /b 0

:check_python
"%PYTHON_EXE%" %PYTHON_ARGS% -c "import sys; print('Python detecte :', sys.executable)"
if errorlevel 1 goto :error
exit /b 0

:error
echo.
echo Une erreur a empeche le lancement de l'application.
echo Consulte le message ci-dessus, puis appuie sur une touche pour fermer cette fenetre.
pause
exit /b 1
