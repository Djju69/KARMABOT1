@echo off
SETLOCAL

echo === Starting deployment process...

:: 1. Validate configuration
echo.
echo [1/4] Validating configuration...
python validate_config.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Configuration validation failed
    exit /b 1
)

:: 2. Fix common issues
echo.
echo [2/4] Fixing common issues...
python fix_deployment.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to fix common issues
    exit /b 1
)

:: 3. Install dependencies
echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install dependencies
    exit /b 1
)

:: 4. Run tests
echo.
echo [4/4] Running tests...
python -m pytest tests/ -v
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some tests failed, but continuing with deployment...
)

echo.
echo === Deployment preparation complete!
echo.
echo To deploy to Railway, run these commands:
echo 1. git add .
echo 2. git commit -m "Prepare for deployment"
echo 3. git push origin main
echo 4. railway up

exit /b 0
