@echo off
REM Démarrer le backend FastAPI
cd "c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\afor-emploi-backend"
start "Backend FastAPI" python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

REM Attendre 3 secondes
timeout /t 3 /nobreak

REM Démarrer le frontend React
cd "c:\Users\OUATTARA AFOR\Desktop\The Box\Web\Emploi\afor-emploi-v2"
start "Frontend React" cmd /k npm run dev

echo.
echo ========================================
echo Serveurs démarrés:
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5173
echo ========================================
pause
