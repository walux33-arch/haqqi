@echo off
REM =====================================================
REM   H A Q Q I  -  H E T Z N E R   D E P L O Y
REM   Usage: deploy.bat <SERVER_IP>
REM   Example: deploy.bat 123.123.123.123
REM =====================================================
if "%1"=="" (
    echo Usage: deploy.bat ^<SERVER_IP^>
    exit /b 1
)

set SERVER=%1
set USER=root

echo.
echo === 1. Installing Docker on Hetzner VPS ===
plink -ssh %USER%@%SERVER% -t "curl -fsSL https://get.docker.com | sh"

echo.
echo === 2. Copying project files ===
pscp -r C:\Users\Laptop\Desktop\haqqi\ %USER%@%SERVER%:~/haqqi/

echo.
echo === 3. Deploying with Docker Compose ===
plink -ssh %USER%@%SERVER% -t "cd ~/haqqi && docker compose up -d --build"

echo.
echo === 4. Setup Nginx + SSL (Caddy) ===
plink -ssh %USER%@%SERVER% -t ^
    "docker run -d --name caddy ^
    -p 80:80 -p 443:443 ^
    -v caddy_data:/data ^
    -v $PWD/Caddyfile:/etc/caddy/Caddyfile ^
    caddy:latest"

echo.
echo === Done! ===
echo Server running at http://%SERVER%:8000
echo Set domain with: haqqi.ma ^<DNS A-record to %SERVER%^>
