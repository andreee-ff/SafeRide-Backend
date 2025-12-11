# SafeRide Backend Startup Script

Write-Host "Starting SafeRide Backend..." -ForegroundColor Green

# 1. Check Database Configuration and Start Docker if needed
if (Test-Path ".env") {
    $envContent = Get-Content ".env" | Out-String
    # Check if uncommented postgresql config is present
    if ($envContent -match "(?m)^DATABASE_URL=postgresql") {
        Write-Host "PostgreSQL configuration detected. Checking Docker..." -ForegroundColor Yellow
        
        # Check if Docker is available
        if (Get-Command "docker" -ErrorAction SilentlyContinue) {
            # Check if container exists
            $containerStatus = docker container inspect -f '{{.State.Status}}' saferide_postgres 2>$null
            
            if ($LASTEXITCODE -ne 0) {
                 # Container doesn't exist, create it
                 Write-Host "Creating and starting PostgreSQL container (saferide_postgres)..." -ForegroundColor Yellow
                 docker run --name saferide_postgres -e POSTGRES_USER=saferide_user -e POSTGRES_PASSWORD=yourpass -e POSTGRES_DB=saferide_db -p 5432:5432 -d postgres:16
            } elseif ($containerStatus -ne "running") {
                 # Container exists but stopped
                 Write-Host "Starting existing PostgreSQL container..." -ForegroundColor Yellow
                 docker start saferide_postgres
            } else {
                 Write-Host "PostgreSQL container is already running." -ForegroundColor Green
            }
        } else {
            Write-Host "Warning: Docker command not found or Docker Desktop is not running." -ForegroundColor Red
            Write-Host "Please start Docker manually." -ForegroundColor Red
        }
    }
}

# 2. Activate virtual environment
if (Test-Path ".\venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Error: Virtual environment not found in .\venv" -ForegroundColor Red
    exit 1
}

# 3. Start the server
Write-Host "Starting Uvicorn server on http://localhost:8000" -ForegroundColor Cyan
python -m uvicorn app.main:create_app --reload --host 0.0.0.0 --port 8000
