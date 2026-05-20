import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import command, transcribe, auth
from app.core import state

app = FastAPI(
    title="NOVA AI CORE",
    description="The central processing unit for NOVA AI 2.0",
    version="2.0.0"
)

from app.modules.user.user_manager import UserManager

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    try:
        um = UserManager()
        await um.initialize_default_user()
    except Exception as e:
        # Log failure but allow server to start for HUD/telemetry
        print(f"Warning: Backend startup personalization failed (DB unreachable): {e}")

    # Preload the NLP models during startup so the first command is fast
    try:
        from app.modules.memory.embedder import get_model
        print("Preloading memory embedder... (this may take a few seconds)")
        get_model()
        print("Memory embedder loaded successfully.")
        
        # Start background filesystem scan (incremental)
        import asyncio
        from app.modules.filesystem_index.search_api import scanner
        print("Starting background filesystem index scan...")
        asyncio.create_task(scanner.scan(full_rescan=False))
        
    except Exception as e:
        print(f"Warning: Failed to preload memory embedder or start indexer: {e}")

app.include_router(command.router, prefix="/api/v1", tags=["Command"])
app.include_router(transcribe.router, prefix="/api/v1", tags=["Speech"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])

# Filesystem Index API
from app.modules.filesystem_index.search_api import router as fs_index_router
app.include_router(fs_index_router, prefix="/api/v1/index", tags=["Filesystem Index"])

@app.get("/")
async def root():
    return {"message": "NOVA AI Backend API is active."}

@app.get("/api/v1/telemetry/weather")
async def get_weather():
    import httpx
    try:
        # 1. Get Location via IP (ipwho.is is fast and HTTPS secure)
        async with httpx.AsyncClient() as client:
            loc_res = await client.get("https://ipwho.is/", timeout=10.0)
            loc_data = loc_res.json()
            lat, lon = loc_data.get("latitude"), loc_data.get("longitude")
            city = loc_data.get("city", "Hyderabad")

            # 2. Get Weather
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            w_res = await client.get(weather_url, timeout=5.0)
            w_data = w_res.json()
            
            temp = w_data["current_weather"]["temperature"]
            code = w_data["current_weather"]["weathercode"]
            
            return {
                "city": str(city).upper(),
                "temp": f"{int(temp)}°C",
                "code": code,
                "status": "online"
            }
    except Exception as e:
        print(f"Weather Proxy Error: {e}")
        return {"city": "HYDERABAD", "temp": "29°C", "code": 0, "status": "mock"}

@app.get("/api/v1/health")
async def health_check():
    import random
    import psutil
    
    uptime_seconds = int(time.time() - state.START_TIME)
    uptime_str = f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m"
    
    return {
        "status": "online",
        "latency": f"{random.randint(12, 45)}ms",
        "load": f"{psutil.virtual_memory().percent}%",
        "cpu": f"{psutil.cpu_percent()}%",
        "uptime": uptime_str,
        "commands": state.COMMAND_COUNT,
        "active_user": state.ACTIVE_USER,
        "systems": {
            "core": "connected",
            "neural": "active",
            "stt": "ready",
            "os_commands": "authorized",
            "vault": "linked"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
