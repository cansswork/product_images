@echo off
echo ===================================
echo   Updating...
echo ===================================
echo.

:: Stage all changes
git add .

:: Ask for a custom commit message (or press Enter for default)
set /p msg="Enter commit message (Press Enter for default 'Update'): "
if "%msg%"=="" set msg=Update

:: Commit changes
git commit -m "%msg%"

:: Push to remote repository
git push

echo.
echo ===================================
echo   Done! Your code is updating.
echo ===================================
pause