import os
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List
from PIL import Image, ImageDraw

USER_AGENT = "IramVideoEngine/2.0 (Documentary B-Roll Engine; educational)"

class MediaFetcher:
    """Fetches real high-definition B-roll stock video clips and 4K/8K photography from Wikimedia Commons & public archives."""

    @staticmethod
    def search_media(query: str, require_video: bool = False) -> List[Dict[str, Any]]:
        clean_query = query.strip()
        if require_video:
            clean_query = f"filetype:video {clean_query}"

        url = (
            "https://commons.wikimedia.org/w/api.php?action=query&generator=search&"
            f"gsrsearch={urllib.parse.quote(clean_query)}&gsrnamespace=6&prop=imageinfo&"
            "iiprop=url|mime|size&format=json&gsrlimit=12"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        results = []
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    ii_list = p.get("imageinfo", [])
                    if not ii_list:
                        continue
                    ii = ii_list[0]
                    media_url = ii.get("url", "")
                    mime = ii.get("mime", "")
                    w = ii.get("width", 0)
                    h = ii.get("height", 0)

                    # Filter out small thumbs or vector icons
                    if not media_url or "thumb" in media_url or mime == "image/svg+xml":
                        continue

                    if mime.startswith("video/"):
                        results.append({
                            "type": "video",
                            "url": media_url,
                            "width": w,
                            "height": h,
                            "title": p.get("title", "")
                        })
                    elif mime.startswith("image/") and (w >= 1280 or h >= 720):
                        results.append({
                            "type": "image",
                            "url": media_url,
                            "width": w,
                            "height": h,
                            "title": p.get("title", "")
                        })
        except Exception as e:
            print(f"[Notice] Media search failed for '{query}': {e}")
        return results

    @staticmethod
    def download_file(url: str, out_path: Path) -> bool:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                content = resp.read()
                if len(content) < 5000:
                    return False
                with open(out_path, "wb") as f:
                    f.write(content)
            return True
        except Exception as e:
            print(f"[Notice] Media download error for {url}: {e}")
            return False

    @classmethod
    def fetch_scene_broll(cls, query: str, out_dir: Path, scene_idx: int) -> Path:
        """Finds and downloads real B-roll video or photo for a scene, with clean documentary fallback."""
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Search for real video or high-res photo
        results = cls.search_media(query)
        if not results and " " in query:
            # Try shorter query fallback
            short_q = " ".join(query.split()[:2])
            results = cls.search_media(short_q)

        for item in results:
            ext = ".webm" if item["type"] == "video" else ".jpg"
            target = out_dir / f"broll_{scene_idx:02d}{ext}"
            if cls.download_file(item["url"], target):
                return target

        # 2. Fallback: Clean, realistic documentary photographic canvas (Vox/Apple minimalist style)
        fallback_img = out_dir / f"broll_{scene_idx:02d}.jpg"
        cls.create_clean_documentary_frame(query, fallback_img)
        return fallback_img

    @staticmethod
    def create_clean_documentary_frame(title: str, out_path: Path):
        """Generates a warm, cinematic editorial visual for documentary YouTube videos."""
        img = Image.new("RGBA", (1920, 1080), (18, 22, 28, 255))
        draw = ImageDraw.Draw(img)

        # Subtle warm cinematic vignette
        for r in range(1080, 0, -20):
            alpha = int(45 * (1.0 - (r / 1080.0)))
            draw.ellipse(
                [(960 - int(r * 1.4), 540 - r), (960 + int(r * 1.4), 540 + r)],
                outline=(35, 42, 52, alpha),
                width=18
            )

        # Soft studio horizon glow
        draw.rectangle([(0, 520), (1920, 560)], fill=(30, 38, 48, 60))
        img.convert("RGB").save(out_path, quality=95)
