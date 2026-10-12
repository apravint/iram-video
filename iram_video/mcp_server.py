"""
Model Context Protocol (MCP) Server for IRAM Video.
Inspired by gyoridavid/short-video-maker MCP server architecture.
Exposes IRAM Video creation, B-roll search, scene extension, and soundscape design
as native tools over standard JSON-RPC 2.0 stdio protocol.
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from .soundscape import SoundscapeAdvisor
from .b_roll import MediaFetcher
from .ai_video import AIVideoEngine
from .motion_canvas import MotionCanvas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", stream=sys.stderr)

TOOLS_METADATA = [
    {
        "name": "create_video",
        "description": "Generates a complete broadcast-quality video or YouTube Short with voiceover, B-roll, score, and optional kinetic subtitles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "The topic, premise, or screenplay brief."},
                "is_shorts": {"type": "boolean", "default": False, "description": "True for 9:16 vertical video (YouTube Shorts, Reels, TikTok); False for 16:9."},
                "is_real": {"type": "boolean", "default": True, "description": "True for real YouTube documentary with verified B-roll and acoustic score."},
                "music": {"type": "string", "default": "documentary", "description": "Music mood ('documentary', 'acoustic', 'tech', 'ambient', 'trailer')."},
                "steady_camera": {"type": "boolean", "default": True, "description": "Subtle steady-cam micro-drift framing (zero dizzying pans)."},
                "output_path": {"type": "string", "description": "Destination file path for the output MP4."}
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "extend_video",
        "description": "Continuously extends an existing video clip into a multi-scene film using keyframe seeding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "previous_video": {"type": "string", "description": "Absolute path to the existing MP4 video clip."},
                "prompt": {"type": "string", "description": "Description of the next narrative scene."},
                "output_path": {"type": "string", "description": "Destination path for the extended video."},
                "duration": {"type": "number", "default": 4.0, "description": "Duration of the extension in seconds."}
            },
            "required": ["previous_video", "prompt", "output_path"]
        }
    },
    {
        "name": "suggest_soundscape",
        "description": "Designs a Hollywood-grade musical score and audio foley soundscape tailored to a video scene description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scene_prompt": {"type": "string", "description": "Description of the visual scene or narrative action."}
            },
            "required": ["scene_prompt"]
        }
    },
    {
        "name": "search_stock_broll",
        "description": "Searches curated HD stock video clips and photography across Wikimedia Commons and Pexels with orientation filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search keyword or entity name."},
                "orientation": {"type": "string", "enum": ["portrait", "landscape"], "default": "landscape", "description": "Target video orientation."},
                "require_video": {"type": "boolean", "default": True, "description": "True to prioritize MP4 video clips over still photos."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "render_metric_card",
        "description": "Programmatically renders a sleek 30 FPS animated infographic counter card video clip.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {"type": "number", "description": "The target metric number to animate count-up."},
                "unit": {"type": "string", "description": "Unit label (e.g. 'KM', '%', 'CRORE', 'MS')."},
                "headline": {"type": "string", "description": "Metric headline or label."},
                "subheadline": {"type": "string", "default": "", "description": "Contextual subheadline."},
                "out_path": {"type": "string", "description": "Destination MP4 file path."},
                "duration": {"type": "number", "default": 4.0, "description": "Clip duration in seconds."},
                "is_shorts": {"type": "boolean", "default": False, "description": "Render in 9:16 vertical shorts aspect ratio."}
            },
            "required": ["number", "unit", "headline", "out_path"]
        }
    }
]

class MCPServer:
    """Standard Model Context Protocol (MCP) JSON-RPC 2.0 Server."""

    def __init__(self):
        self.running = True

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "iram-video",
                        "version": "2.0.0"
                    }
                }
            }
        elif method == "notifications/initialized":
            return None
        elif method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": TOOLS_METADATA}
            }
        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})
            try:
                res_content = self.execute_tool(tool_name, args)
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(res_content, indent=2)}]
                    }
                }
            except Exception as e:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "isError": True,
                        "content": [{"type": "text", "text": f"Error executing {tool_name}: {str(e)}"}]
                    }
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"}
            }

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name == "suggest_soundscape":
            return SoundscapeAdvisor.design_soundscape(args["scene_prompt"])

        elif tool_name == "search_stock_broll":
            query = args["query"]
            orientation = args.get("orientation", "landscape")
            req_vid = args.get("require_video", True)
            results = MediaFetcher.search_pexels(query, require_video=req_vid, orientation=orientation)
            if not results:
                results = MediaFetcher.search_wikimedia(query, require_video=req_vid)
            return results[:6]

        elif tool_name == "render_metric_card":
            beat = {
                "metric_number": args["number"],
                "metric_unit": args["unit"],
                "metric_label_en": args["headline"],
                "phrase": args.get("subheadline", "")
            }
            out_p = Path(args["out_path"])
            dur = float(args.get("duration", 4.0))
            is_sh = bool(args.get("is_shorts", False))
            MotionCanvas.render_metric_card(beat, out_p, duration=dur, is_shorts=is_sh)
            return {"status": "ok", "out_path": str(out_p), "duration": dur}

        elif tool_name == "extend_video":
            prev_v = Path(args["previous_video"])
            out_p = Path(args["output_path"])
            prompt = args["prompt"]
            dur = float(args.get("duration", 4.0))
            is_sh = bool(args.get("is_shorts", False))
            res = AIVideoEngine.extend_video(prev_v, prompt, out_p, duration=dur, is_shorts=is_sh)
            return {"status": "ok", "out_path": str(res)}

        elif tool_name == "create_video":
            import subprocess
            prompt = args["prompt"]
            out_p = args.get("output_path", "/tmp/mcp_generated_video.mp4")
            cmd = ["python3", "-m", "iram_video.cli", prompt, "-o", out_p]
            if args.get("is_shorts"):
                cmd.append("--shorts")
            if args.get("is_real", True):
                cmd.append("--real")
            if args.get("music"):
                cmd.extend(["--music", args["music"]])
            if args.get("steady_camera", True):
                cmd.append("--steady")
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return {
                "status": "ok" if proc.returncode == 0 else "error",
                "output_video": out_p,
                "stdout": proc.stdout[-500:],
                "stderr": proc.stderr[-500:] if proc.returncode != 0 else ""
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def run_stdio(self):
        """Runs the JSON-RPC stdio event loop."""
        logging.info("IRAM Video MCP Server listening on stdio...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()

def main():
    server = MCPServer()
    server.run_stdio()

if __name__ == "__main__":
    main()
