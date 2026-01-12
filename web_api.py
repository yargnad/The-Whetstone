"""
The Whetstone - Web API Server
Phase 3 Implementation

FastAPI backend providing REST API + SSE streaming for the Web UI.
Run with: python web_api.py
"""

import os
import asyncio
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from pydantic import BaseModel

from core import PhilosopherCore
from scheduler_service import SocraticScheduler
from symposium import Symposium

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Shared State ---
core: Optional[PhilosopherCore] = None
scheduler: Optional[SocraticScheduler] = None
active_symposium: Optional[Symposium] = None

# --- Persona Scan State ---
class ScanStatus:
    def __init__(self):
        self.is_running = False
        self.start_time = None
        self.end_time = None
        self.success = False
        self.error = None
        self.mode = "shallow"
        self.persona_count = 0
        self.output = ""
        self.lock = asyncio.Lock()

scan_state = ScanStatus()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize core services on startup."""
    global core, scheduler
    logger.info("[API] Starting Whetstone Web API...")
    
    core = PhilosopherCore()
    scheduler = SocraticScheduler(core)
    scheduler.start()
    
    logger.info("[API] Core and Scheduler initialized.")
    yield
    
    # Cleanup
    scheduler.stop()
    logger.info("[API] Shutdown complete.")


app = FastAPI(
    title="The Whetstone API",
    description="REST API for The Whetstone philosophical AI assistant",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Request/Response Models ---

class ChatRequest(BaseModel):
    message: str
    persona_id: Optional[str] = None


class PersonaSelectRequest(BaseModel):
    persona_name: str


class SettingsRequest(BaseModel):
    enabled: bool


class SchedulerTaskRequest(BaseModel):
    name: str
    interval_minutes: int
    action_type: str = "toast"
    persona_name: str = "Random"
    topic: str = ""


class ModelSelectRequest(BaseModel):
    model_name: str


class PersonaConfigRequest(BaseModel):
    preamble: str


class SymposiumStartRequest(BaseModel):
    persona_a: str
    persona_b: str
    topic: str


# --- Routes ---

@app.get("/")
async def serve_index():
    """Serve the main HTML page."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"error": "Frontend not found. Ensure static/index.html exists."}, status_code=404)


@app.get("/api/status")
async def get_status():
    """System health and info."""
    return {
        "status": "ok",
        "backend": core.backend.name if core and core.backend else "not initialized",
        "persona_count": len(core.get_valid_personas()) if core else 0,
        "current_persona": core.current_persona.get("name") if core and core.current_persona else None,
        "deep_mode": core.deep_mode if core else False,
        "clarity_mode": core.clarity_mode if core else False,
        "logging_enabled": core.db.logging_enabled if core else False,
        "scheduler_running": scheduler.running if scheduler else False,
        "scheduled_tasks": len(scheduler.tasks) if scheduler else 0
    }


@app.get("/api/personas")
async def list_personas():
    """List all valid personas."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    personas = core.get_valid_personas()
    return {
        "personas": [
            {
                "name": p.get("name", "Unknown"),
                "description": p.get("description", ""),
                "library_filter": p.get("library_filter", [])
            }
            for p in personas
        ],
        "current": core.current_persona.get("name") if core.current_persona else None
    }


@app.post("/api/personas/select")
async def select_persona(request: PersonaSelectRequest):
    """Set the current persona by name."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    personas = core.get_valid_personas()
    persona = next((p for p in personas if p.get("name") == request.persona_name), None)
    
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{request.persona_name}' not found")
    
    core.set_persona(persona)
    return {"success": True, "persona": persona.get("name")}


def find_persona(name: str):
    """Find a persona by key or display name."""
    # Try direct key access
    if name in core.personas:
        return core.personas[name], name
    
    # Try lowercase key
    if name.lower() in core.personas:
        return core.personas[name.lower()], name.lower()
    
    # Try matching by 'name' field
    for key, p in core.personas.items():
        if p.get("name") == name:
            return p, key
            
    return None, None


@app.get("/api/personas/{persona_name}")
async def get_persona_detail(persona_name: str):
    """Get detailed information about a specific persona."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    persona, key = find_persona(persona_name)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")
    
    # Get custom preamble from DB
    custom_preamble = core.db.get_setting(f"persona_preamble_{persona.get('name')}", "")
    
    return {
        "name": persona.get("name"),
        "description": persona.get("description", ""),
        "prompt": persona.get("prompt", ""),
        "library_filter": persona.get("library_filter", []),
        "custom_preamble": custom_preamble,
        "key": key
    }


@app.post("/api/personas/{persona_name}/config")
async def update_persona_config(persona_name: str, request: PersonaConfigRequest):
    """Update custom configuration for a specific persona."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    persona, _ = find_persona(persona_name)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")
    
    # Save to DB using the formal name as the key for better consistency
    core.db.set_setting(f"persona_preamble_{persona.get('name')}", request.preamble)
    return {"success": True, "persona": persona.get("name")}


@app.get("/api/personas/{persona_name}/export")
async def export_persona_codex(persona_name: str):
    """Export a single persona as a CODEX file."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    persona, _ = find_persona(persona_name)
    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{persona_name}' not found")
    
    try:
        import json
        from fastapi.responses import Response
        
        # Get custom preamble if it exists
        custom_preamble = core.db.get_setting(f"persona_preamble_{persona.get('name')}", "")
        
        # Create CODEX structure
        codex_data = {
            "format": "codex/persona",
            "version": "1.0",
            "metadata": {
                "name": persona.get("name"),
                "description": persona.get("description", ""),
                "created": "manual_export"
            },
            "layers": {
                "core": {
                    "system_prompt": persona.get("prompt", ""),
                    "custom_preamble": custom_preamble,
                    "library_filter": persona.get("library_filter", [])
                }
            }
        }
        
        # Convert to JSON
        codex_json = json.dumps(codex_data, indent=2)
        
        # Return as downloadable file
        return Response(
            content=codex_json,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{persona.get("name")}.codex"'
            }
        )
    except Exception as e:
        logger.error(f"Export failed for {persona_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@app.get("/api/personas/export-all")
async def export_all_personas_codex():
    """Export all personas as a ZIP archive of CODEX files."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    try:
        import json
        import io
        import zipfile
        from fastapi.responses import StreamingResponse
        
        personas = core.get_valid_personas()
        if not personas:
            raise HTTPException(status_code=404, detail="No personas found")
        
        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for persona in personas:
                # Get custom preamble if it exists
                custom_preamble = core.db.get_setting(f"persona_preamble_{persona.get('name')}", "")
                
                # Create CODEX structure for this persona
                codex_data = {
                    "format": "codex/persona",
                    "version": "1.0",
                    "metadata": {
                        "name": persona.get("name"),
                        "description": persona.get("description", ""),
                        "created": "manual_export"
                    },
                    "layers": {
                        "core": {
                            "system_prompt": persona.get("prompt", ""),
                            "custom_preamble": custom_preamble,
                            "library_filter": persona.get("library_filter", [])
                        }
                    }
                }
                
                # Add to ZIP
                codex_json = json.dumps(codex_data, indent=2)
                filename = f"{persona.get('name')}.codex"
                zip_file.writestr(filename, codex_json)
        
        # Seek to beginning of buffer
        zip_buffer.seek(0)
        
        # Return as streaming response
        return StreamingResponse(
            io.BytesIO(zip_buffer.read()),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="whetstone_personas.zip"'
            }
        )
    except Exception as e:
        logger.error(f"Export all failed: {e}")
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")



@app.post("/api/personas/scan")
async def scan_personas(deep: bool = False):
    """
    Trigger a persona scan in the background.
    """
    if scan_state.is_running:
        return {"success": False, "message": "Scan already in progress"}
    
    async with scan_state.lock:
        if scan_state.is_running:
            return {"success": False, "message": "Scan already in progress"}
        
        scan_state.is_running = True
        scan_state.start_time = asyncio.get_event_loop().time()
        scan_state.mode = "deep" if deep else "shallow"
        scan_state.success = False
        scan_state.error = None
        scan_state.output = ""
    
    # Run in background
    asyncio.create_task(run_scan_task(deep))
    
    return {
        "success": True,
        "message": f"{scan_state.mode.capitalize()} scan started in background"
    }

async def run_scan_task(deep: bool):
    """Background task for persona scanning."""
    import subprocess
    import sys
    
    script_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "generate_personas.py"
    )
    
    cmd = [sys.executable, script_path]
    if deep:
        cmd.append("--deep")
        
    try:
        # Run subprocess in a thread to not block the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: subprocess.run(
                cmd,
                cwd=os.path.dirname(script_path),
                capture_output=True,
                text=True,
                timeout=300 # 5 minute timeout for background task
            )
        )
        
        # Refresh personas in core
        if core:
            core.refresh_data()
            
        async with scan_state.lock:
            scan_state.is_running = False
            scan_state.end_time = asyncio.get_event_loop().time()
            scan_state.success = True
            scan_state.persona_count = len(core.get_valid_personas()) if core else 0
            scan_state.output = result.stdout[-1000:] if result.stdout else ""
            
    except Exception as e:
        logger.error(f"[API] Persona scan failed: {e}")
        async with scan_state.lock:
            scan_state.is_running = False
            scan_state.end_time = asyncio.get_event_loop().time()
            scan_state.success = False
            scan_state.error = str(e)

@app.get("/api/personas/scan/status")
async def get_scan_status():
    """Get the status of the current or last persona scan."""
    return {
        "is_running": scan_state.is_running,
        "mode": scan_state.mode,
        "success": scan_state.success,
        "error": scan_state.error,
        "persona_count": scan_state.persona_count,
        "output": scan_state.output,
        "duration": (scan_state.end_time - scan_state.start_time) if scan_state.end_time else 
                    (asyncio.get_event_loop().time() - scan_state.start_time) if scan_state.start_time else 0
    }


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Send a message and get AI response via Server-Sent Events.
    Streams tokens as they are generated.
    """
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    if not core.current_persona:
        raise HTTPException(status_code=400, detail="No persona selected. Call /api/personas/select first.")
    
    async def generate():
        try:
            # Run the blocking generator in a thread pool
            loop = asyncio.get_event_loop()
            
            def get_tokens():
                return list(core.chat(request.message))
            
            # Get all tokens (core.chat is a generator)
            # We need to stream them, so we'll iterate
            for token in core.chat(request.message):
                # SSE data field cannot contain raw newlines
                # Encode them as literal \n so client can decode
                encoded_token = token.replace('\n', '\\n')
                yield {"event": "token", "data": encoded_token}
                await asyncio.sleep(0)  # Yield control
            
            yield {"event": "done", "data": "[DONE]"}
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            yield {"event": "error", "data": str(e)}
    
    return EventSourceResponse(generate())


@app.get("/api/history")
async def get_history(limit: int = 50):
    """Get recent chat history from the database."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    history = core.db.get_history(limit=limit)
    return {"history": history}


@app.post("/api/settings/deep-mode")
async def toggle_deep_mode(request: SettingsRequest):
    """Toggle deep mode (longer responses)."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    core.set_deep_mode(request.enabled)
    return {"deep_mode": core.deep_mode}


@app.post("/api/settings/logging")
async def toggle_logging(request: SettingsRequest):
    """Toggle database logging (privacy control)."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    core.set_logging(request.enabled)
    return {"logging_enabled": core.db.logging_enabled}


@app.post("/api/settings/clarity-mode")
async def toggle_clarity_mode(request: SettingsRequest):
    """Toggle clarity mode (accessible language without jargon)."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    core.set_clarity_mode(request.enabled)
    return {"clarity_mode": core.clarity_mode}


@app.post("/api/settings/ultra-privacy")
async def toggle_ultra_privacy(request: SettingsRequest):
    """Toggle Ultra-Privacy Mode (disables all logging and restoration)."""
    if not core: raise HTTPException(status_code=503, detail="Core")
    core.ultra_privacy_mode = request.enabled
    core.db.set_setting("ultra_privacy_mode", request.enabled)
    return {"ultra_privacy_mode": core.ultra_privacy_mode}


@app.post("/api/settings/journey-memory")
async def toggle_journey_memory(request: SettingsRequest):
    """Toggle Journey Memory (session restoration)."""
    if not core: raise HTTPException(status_code=503, detail="Core")
    core.journey_memory_enabled = request.enabled
    core.db.set_setting("journey_memory_enabled", request.enabled)
    return {"journey_memory_enabled": core.journey_memory_enabled}


@app.post("/api/settings/default-persona")
async def set_default_persona(request: PersonaSelectRequest):
    """Set the current persona as the default for future sessions."""
    if not core: raise HTTPException(status_code=503, detail="Core")
    core.db.set_setting("current_persona", request.persona_name)
    return {"success": True, "default_persona": request.persona_name}


@app.post("/api/settings/default-model")
async def set_default_model(request: ModelSelectRequest):
    """Set the current model as the default for future sessions."""
    if not core: raise HTTPException(status_code=503, detail="Core")
    core.db.set_setting("default_model", request.model_name)
    return {"success": True, "default_model": request.model_name}


@app.post("/api/memory/summarize")
async def trigger_summarization():
    """Manually trigger session summarization (e.g., on exit)."""
    if not core: raise HTTPException(status_code=503, detail="Core")
    core.summarize_and_store_session()
    return {"success": True}
        
    
# --- Model Endpoints ---

@app.get("/api/models")
async def list_models():
    """List available Ollama models."""
    import requests
    try:
        # Query Ollama for available models
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = [m.get("name", "") for m in data.get("models", [])]
            current_model = None
            if core and core.backend:
                current_model = getattr(core.backend, 'model', None)
            return {
                "models": models,
                "current": current_model
            }
        else:
            return {"models": [], "current": None, "error": "Could not fetch models"}
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        return {"models": [], "current": None, "error": str(e)}


@app.post("/api/models/select")
async def select_model(request: ModelSelectRequest):
    """Switch to a different Ollama model."""
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    try:
        from backends import OllamaBackend
        # Create new backend with selected model
        core.backend = OllamaBackend(model=request.model_name)
        
        # Verify it's available
        if not core.backend.is_available():
            raise HTTPException(status_code=400, detail=f"Model '{request.model_name}' is not available")
        
        logger.info(f"[API] Switched to model: {request.model_name}")
        return {"success": True, "model": request.model_name}
    except Exception as e:
        logger.error(f"Failed to switch model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Scheduler Endpoints ---

@app.get("/api/scheduler")
async def list_scheduled_tasks():
    """List all scheduled tasks."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    return {
        "running": scheduler.running,
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "interval_minutes": t.interval_minutes,
                "action_type": t.action_type,
                "persona_name": t.persona_name,
                "topic": t.topic,
                "enabled": t.enabled
            }
            for t in scheduler.tasks
        ]
    }


@app.post("/api/scheduler")
async def create_scheduled_task(request: SchedulerTaskRequest):
    """Create a new scheduled task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    task = scheduler.add_task(
        name=request.name,
        interval=request.interval_minutes,
        action=request.action_type,
        persona=request.persona_name,
        topic=request.topic
    )
    
    return {"success": True, "task_id": task.id}


@app.delete("/api/scheduler/{task_id}")
async def delete_scheduled_task(task_id: str):
    """Delete a scheduled task."""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    
    scheduler.remove_task(task_id)
    return {"success": True}


# --- Symposium Endpoints ---

@app.post("/api/symposium/start")
async def start_symposium(request: SymposiumStartRequest):
    """Start a new AI-to-AI debate (Symposium)."""
    global active_symposium
    
    if not core:
        raise HTTPException(status_code=503, detail="Core not initialized")
    
    # Get persona objects using robust lookup
    persona_a, _ = find_persona(request.persona_a)
    persona_b, _ = find_persona(request.persona_b)
    
    if not persona_a:
        raise HTTPException(status_code=400, detail=f"Persona A '{request.persona_a}' not found")
    if not persona_b:
        raise HTTPException(status_code=400, detail=f"Persona B '{request.persona_b}' not found")
    
    active_symposium = Symposium(core, persona_a, persona_b, request.topic)
    
    return {
        "success": True,
        "persona_a": persona_a["name"],
        "persona_b": persona_b["name"],
        "topic": request.topic
    }


@app.get("/api/symposium/next")
async def symposium_next_turn():
    """Get the next turn in the Symposium. Streams response via SSE."""
    global active_symposium
    
    if not active_symposium:
        raise HTTPException(status_code=400, detail="No active symposium. Call /api/symposium/start first.")
    
    if not active_symposium.is_active:
        raise HTTPException(status_code=400, detail="Symposium has ended.")
    
    async def generate():
        try:
            for event in active_symposium.next_turn():
                if event["type"] == "token":
                    # Encode newlines for SSE
                    encoded = event["content"].replace('\n', '\\n')
                    yield {
                        "event": "token", 
                        "data": encoded,
                        "id": event.get("speaker", "System")
                    }
                elif event["type"] == "complete":
                    yield {
                        "event": "complete",
                        "data": event["content"]["speaker"]
                    }
                await asyncio.sleep(0)
            
            yield {"event": "done", "data": "[DONE]"}
            
        except Exception as e:
            logger.error(f"Symposium error: {e}")
            yield {"event": "error", "data": str(e)}
    
    return EventSourceResponse(generate())


@app.post("/api/symposium/stop")
async def stop_symposium():
    """Stop the current Symposium."""
    global active_symposium
    
    if active_symposium:
        active_symposium.is_active = False
        transcript = active_symposium.history
        active_symposium = None
        return {"success": True, "turns": len(transcript)}
    
    return {"success": True, "turns": 0}


@app.get("/api/symposium/status")
async def symposium_status():
    """Get current Symposium status and history."""
    if not active_symposium:
        return {"active": False, "history": []}
    
    return {
        "active": active_symposium.is_active,
        "topic": active_symposium.topic,
        "persona_a": active_symposium.persona_a["name"],
        "persona_b": active_symposium.persona_b["name"],
        "turn_count": active_symposium.turn_count,
        "history": active_symposium.history
    }


class SymposiumInterjectRequest(BaseModel):
    message: str
    target: Optional[str] = None # 'a', 'b', or None


@app.post("/api/symposium/interject")
async def symposium_interject(request: SymposiumInterjectRequest):
    """Inject a moderator/user message into the symposium."""
    global active_symposium
    
    if not active_symposium:
        raise HTTPException(status_code=400, detail="No active symposium.")
    
    if not active_symposium.is_active:
        raise HTTPException(status_code=400, detail="Symposium has ended.")
    
    turn = active_symposium.interject(request.message, target=request.target)
    
    return {"success": True, "turn": turn}


# --- Main Entry Point ---

if __name__ == "__main__":
    import uvicorn
    
    # Ensure Ollama is running (reuse logic from philosopher_app)
    from philosopher_app import is_ollama_running, launch_ollama_server
    
    if os.getenv("WHETSTONE_BACKEND", "ollama") == "ollama":
        if not is_ollama_running():
            launch_ollama_server()
    
    print("\n" + "="*50)
    print("  THE WHETSTONE - Web Interface")
    print("  http://localhost:8080")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
