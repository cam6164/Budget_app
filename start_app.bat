@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PYTHON_CMD="
py -3.12 -c "import sys" >nul 2>nul && set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD py -3.11 -c "import sys" >nul 2>nul && set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD py -c "import sys" >nul 2>nul && set "PYTHON_CMD=py"
if not defined PYTHON_CMD python -c "import sys" >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python312\python.exe" set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe""
if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python311\python.exe" set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python311\python.exe""
if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python314\python.exe" set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python314\python.exe""
if not defined PYTHON_CMD if exist "%LocalAppData%\Programs\Python\Python313\python.exe" set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python313\python.exe""

if not defined PYTHON_CMD (
    echo Python n’est pas installé. Installe Python 3.11 ou 3.12 puis relance l’application.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Création de l’environnement Python local...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 goto :erreur
)

echo Vérification des dépendances...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto :erreur

echo Lancement de Suivi budget et finances...
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto :erreur
exit /b 0

:erreur
echo.
echo Une erreur a empêché le lancement de l’application.
echo Consulte le message ci-dessus, puis appuie sur une touche pour fermer cette fenêtre.
pause
exit /b 1
