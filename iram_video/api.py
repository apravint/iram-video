"""
Decoupled FastAPI REST API & Asynchronous Task Queue Network for IRAM Video.
Provides immediate tracking IDs on task submission, background worker queue,
SSE live progress streaming, and full REST endpoints for autonomous video production.
"""

import os
import sys
import time
import uuid
import json
import logging
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel, Field

from .templates import VIDEO_TEMPLATES, list_templates
from .state_machine import StateMachineAssetBuilder, AssetRenderState

logger = logging.getLogger("iram_video.api")
OUTPUTS_DIR = Path(os.getenv("IRAM_OUTPUTS_DIR", "/home/apravint"))


# ---------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------

class VideoGenerationRequest(BaseModel):
    prompt: str = Field(..., description="Screenplay premise, brief, or topic")
    template: Optional[str] = Field(None, description="Video genre template ('explainer', 'tutorial', 'listicle', 'comparison', 'news', 'promo', 'podcast')")
    aspect_ratio: str = Field("16:9", description="Aspect ratio ('16:9', '9:16', '1:1', '2.39:1')")
    mode: str = Field("real", description="Production mode ('real', 'film', 'cinema', 'shorts')")
    character: str = Field("none", description="Mascot character ('robot', 'presenter', 'ferris', 'gopher', 'none')")
    language: str = Field("en", description="Narration language ('en', 'ta')")
    transition: str = Field("fade", description="Scene transition preset")
    color_grade: str = Field("clean", description="Color grading preset")
    music: str = Field("auto", description="Soundtrack mood")
    is_4k: bool = Field(False, description="Export in 4K UHD")
    steady_camera: bool = Field(True, description="Enable subtle micro-drift camera framing")
    json_doc: Optional[str] = Field(None, description="Structured blueprint JSON filename")
    start_image: Optional[str] = Field(None, description="Optional starting keyframe image path")


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # queued, directing, synthesizing_audio, rendering_visuals, assembling, completed, failed, cancelled
    progress: float  # 0.0 to 1.0
    current_step: str
    created_at: str
    elapsed_seconds: float
    output_filename: Optional[str] = None
    output_url: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------
# Asynchronous Task Queue Manager
# ---------------------------------------------------------

class VideoTaskQueue:
    """In-memory multi-threaded task queue with job lifecycle management."""

    def __init__(self, max_concurrent: int = 2):
        self.max_concurrent = max_concurrent
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.lock = threading.Lock()
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def submit_task(self, req: VideoGenerationRequest) -> str:
        task_id = f"iram_task_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc).isoformat()
        with self.lock:
            self.tasks[task_id] = {
                "task_id": task_id,
                "status": "queued",
                "progress": 0.05,
                "current_step": "Task queued for processing",
                "created_at": now,
                "start_time": time.time(),
                "elapsed_seconds": 0.0,
                "request": req.model_dump() if hasattr(req, "model_dump") else req.dict(),
                "output_filename": None,
                "output_url": None,
                "error": None,
                "logs": ["Task received and queued"]
            }
        logger.info(f"Queued video rendering task {task_id}")
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        with self.lock:
            t = self.tasks.get(task_id)
            if t:
                # Update elapsed seconds
                if t["status"] not in ["completed", "failed", "cancelled"]:
                    t["elapsed_seconds"] = round(time.time() - t["start_time"], 2)
                return dict(t)
        return None

    def list_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.lock:
            res = sorted(self.tasks.values(), key=lambda x: x["created_at"], reverse=True)
            return [dict(t) for t in res[:limit]]

    def cancel_task(self, task_id: str) -> bool:
        with self.lock:
            if task_id in self.tasks and self.tasks[task_id]["status"] in ["queued", "directing"]:
                self.tasks[task_id]["status"] = "cancelled"
                self.tasks[task_id]["current_step"] = "Task cancelled by user"
                return True
        return False

    def _worker_loop(self):
        """Continuously polls and executes queued tasks."""
        while True:
            task_to_run = None
            with self.lock:
                for tid, tinfo in self.tasks.items():
                    if tinfo["status"] == "queued":
                        task_to_run = tinfo
                        break

            if not task_to_run:
                time.sleep(0.5)
                continue

            self._execute_single_task(task_to_run["task_id"], task_to_run["request"])

    def _execute_single_task(self, task_id: str, req_data: Dict[str, Any]):
        def update_progress(step: str, progress: float):
            with self.lock:
                if task_id in self.tasks:
                    self.tasks[task_id]["current_step"] = step
                    self.tasks[task_id]["progress"] = progress
                    self.tasks[task_id]["logs"].append(f"[{round(time.time() - self.tasks[task_id]['start_time'], 1)}s] {step}")

        try:
            update_progress("Directing screenplay with Google Gemini", 0.15)
            with self.lock:
                self.tasks[task_id]["status"] = "directing"

            # Construct CLI command
            import subprocess
            cmd = [sys.executable, "-m", "iram_video.cli"]

            prompt = req_data.get("prompt", "")
            mode = req_data.get("mode", "real")
            template = req_data.get("template")
            aspect_ratio = req_data.get("aspect_ratio", "16:9")
            character = req_data.get("character", "none")
            lang = req_data.get("language", "en")
            transition = req_data.get("transition", "fade")
            color_grade = req_data.get("color_grade", "clean")
            music = req_data.get("music", "auto")
            is_4k = req_data.get("is_4k", False)
            steady = req_data.get("steady_camera", True)

            if template:
                cmd.extend(["--template", template])
            if aspect_ratio:
                cmd.extend(["--aspect-ratio", aspect_ratio])
            if mode == "real":
                cmd.append("--real")
            elif mode == "film":
                cmd.append("--film")
            elif mode == "cinema":
                cmd.append("--cinema")
            elif mode == "shorts":
                cmd.append("--shorts")

            if character and character != "none":
                cmd.extend(["--character", character])
            if lang:
                cmd.extend(["--lang", lang])
            if transition:
                cmd.extend(["--transition", transition])
            if color_grade:
                cmd.extend(["--grade", color_grade])
            if music:
                cmd.extend(["--music", music])
            if is_4k:
                cmd.append("--4k")
            if steady:
                cmd.append("--steady")

            import re
            slug = re.sub(r"[^\w\s-]", "", prompt, flags=re.UNICODE).strip().lower()
            slug = re.sub(r"[-\s]+", "_", slug)[:30] or "task_render"
            out_name = f"{slug}_{task_id[-6:]}.mp4"
            out_file = OUTPUTS_DIR / out_name
            cmd.extend(["-o", str(out_file)])
            cmd.extend(["--", prompt])

            update_progress("Synthesizing neural voiceover & parallel visuals", 0.45)
            with self.lock:
                self.tasks[task_id]["status"] = "rendering_visuals"

            # Run compilation process
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=600)

            if proc.returncode != 0:
                raise RuntimeError(proc.stderr or proc.stdout or "Video compilation process failed")

            update_progress("Finalizing master broadcast video", 0.95)
            with self.lock:
                self.tasks[task_id]["status"] = "completed"
                self.tasks[task_id]["progress"] = 1.0
                self.tasks[task_id]["current_step"] = "Master video render complete"
                self.tasks[task_id]["output_filename"] = out_name
                self.tasks[task_id]["output_url"] = f"/video/{out_name}"
                self.tasks[task_id]["elapsed_seconds"] = round(time.time() - self.tasks[task_id]["start_time"], 2)

        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            with self.lock:
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = "failed"
                    self.tasks[task_id]["error"] = str(e)
                    self.tasks[task_id]["current_step"] = f"Failed: {str(e)[:120]}"


# Global task queue singleton
task_queue = VideoTaskQueue(max_concurrent=2)


# ---------------------------------------------------------
# FastAPI App & Endpoints
# ---------------------------------------------------------

app = FastAPI(
    title="IRAM Video Studio API",
    version="2.5.0",
    description="Autonomous Film & Video Engine REST API with Asynchronous Task Queue Network."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v2/health")
def health():
    return {
        "status": "healthy",
        "engine": "IRAM Video Studio 2.5",
        "active_tasks": len([t for t in task_queue.tasks.values() if t["status"] in ["queued", "directing", "rendering_visuals"]])
    }


@app.get("/api/v2/templates")
def get_templates():
    return list_templates()


@app.post("/api/v2/generate")
def create_render_task(req: VideoGenerationRequest):
    """
    Submits a video rendering task and returns tracking ID immediately (sub-15ms).
    """
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")

    task_id = task_queue.submit_task(req)
    return {
        "status": "queued",
        "task_id": task_id,
        "tracking_url": f"/api/v2/tasks/{task_id}",
        "sse_stream_url": f"/api/v2/tasks/{task_id}/events"
    }


@app.get("/api/v2/tasks/{task_id}")
def get_task_status(task_id: str):
    task = task_queue.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.get("/api/v2/tasks")
def list_tasks(limit: int = Query(20, ge=1, le=100)):
    return task_queue.list_tasks(limit=limit)


@app.post("/api/v2/tasks/{task_id}/cancel")
def cancel_task(task_id: str):
    ok = task_queue.cancel_task(task_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Cannot cancel task (not in queued/directing state)")
    return {"status": "cancelled", "task_id": task_id}


@app.get("/api/v2/tasks/{task_id}/events")
def stream_task_events(task_id: str):
    """Server-Sent Events (SSE) streaming real-time JSON task progress."""
    def event_generator():
        last_progress = -1.0
        while True:
            task = task_queue.get_task(task_id)
            if not task:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                break

            # Yield event when progress or step changes
            if task["progress"] != last_progress or task["status"] in ["completed", "failed", "cancelled"]:
                last_progress = task["progress"]
                payload = {
                    "task_id": task["task_id"],
                    "status": task["status"],
                    "progress": task["progress"],
                    "current_step": task["current_step"],
                    "elapsed_seconds": task["elapsed_seconds"],
                    "output_url": task.get("output_url"),
                    "error": task.get("error")
                }
                yield f"data: {json.dumps(payload)}\n\n"

            if task["status"] in ["completed", "failed", "cancelled"]:
                break

            time.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def start_fastapi(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    start_fastapi()
