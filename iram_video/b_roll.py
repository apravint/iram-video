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

            # Optimization: If downloaded image is gigantic (> 2560x1440), resize to 2560x1440
            # to prevent ffmpeg zoompan from decompressing 300-megapixel images every frame.
            if out_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                try:
                    with Image.open(out_path) as img:
                        if img.width > 2560 or img.height > 1440:
                            img.thumbnail((2560, 1440), Image.Resampling.LANCZOS)
                            rgb_img = img.convert("RGB")
                            rgb_img.save(out_path, format="JPEG", quality=92)
                except Exception:
                    pass

            return True
        except Exception as e:
            print(f"[Notice] Media download error for {url}: {e}")
            return False

    @staticmethod
    def extract_scene_beats(scene: Dict[str, Any], total_duration: float, global_topic: str = "") -> List[Dict[str, Any]]:
        """Decomposes a scene into multiple fast-paced visual beats (every 3 to 6 seconds) with exact search queries."""
        # 1. Use explicit broll_beats from screenplay if provided by Director
        explicit_beats = scene.get("broll_beats", [])
        if explicit_beats and isinstance(explicit_beats, list) and len(explicit_beats) >= 2:
            dur_per_beat = total_duration / len(explicit_beats)
            beats = []
            for b in explicit_beats:
                q = b.get("search_query") or b.get("phrase") or scene.get("heading", "")
                beats.append({"query": q.strip(), "duration": round(dur_per_beat, 3)})
            return beats

        # 2. Semantic sentence/clause splitter on narration
        import re
        narration = str(scene.get("narration") or scene.get("heading") or "").strip()
        if not narration:
            return [{"query": scene.get("search_query") or global_topic or "landscape", "duration": total_duration}]

        # Split on sentence boundaries and substantial clauses
        raw_sentences = [s.strip() for s in re.split(r'[\.\?!;]+', narration) if len(s.strip()) > 8]
        if len(raw_sentences) < 2:
            # Try splitting on commas/dashes for long sentences
            raw_sentences = [s.strip() for s in re.split(r'[,—]+', narration) if len(s.strip()) > 10]

        if len(raw_sentences) < 2:
            # Single sentence: return base query
            base_q = scene.get("search_query") or scene.get("heading") or global_topic or "documentary landscape"
            return [{"query": base_q, "duration": total_duration}]

        # Calculate proportional durations based on word count
        total_words = sum(max(1, len(s.split())) for s in raw_sentences)
        stopwords = {
            "in", "the", "an", "a", "from", "over", "to", "it", "its", "have", "has", "of",
            "and", "these", "that", "this", "with", "by", "for", "on", "at", "as", "is",
            "are", "was", "were", "been", "be", "we", "they", "our", "their", "into"
        }

        beats = []
        for s in raw_sentences:
            w_list = s.split()
            w_count = max(1, len(w_list))
            b_dur = (w_count / total_words) * total_duration

            # Extract 3-5 high-signal keywords
            clean_words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', s).split() if w.lower() not in stopwords]
            if len(clean_words) >= 2:
                beat_q = " ".join(clean_words[:4])
            else:
                beat_q = f"{scene.get('heading', '')} {' '.join(w_list[:3])}"

            beats.append({"query": beat_q.strip(), "duration": max(2.5, b_dur)})

        # Normalize durations to sum exactly to total_duration
        current_sum = sum(b["duration"] for b in beats)
        if current_sum > 0:
            scale = total_duration / current_sum
            for b in beats:
                b["duration"] = round(b["duration"] * scale, 3)

        return beats

    @classmethod
    def fetch_media_for_beat(cls, query: str, out_dir: Path, beat_id: str) -> Path:
        """Finds and downloads a unique real B-roll video clip or high-res photo for an individual beat."""
        out_dir.mkdir(parents=True, exist_ok=True)
        
        # Build search queries
        queries_to_try = [query]
        words = [w for w in query.split() if len(w) > 3]
        if len(words) >= 3:
            queries_to_try.append(" ".join(words[:3]))
        if len(words) >= 2:
            queries_to_try.append(" ".join(words[:2]))

        for q in queries_to_try:
            results = cls.search_media(q)
            for item in results:
                ext = ".webm" if item["type"] == "video" else ".jpg"
                target = out_dir / f"beat_{beat_id}{ext}"
                if target.exists() and target.stat().st_size > 5000:
                    return target
                if cls.download_file(item["url"], target):
                    return target

        # Fallback to clean documentary frame
        fallback_img = out_dir / f"beat_{beat_id}.jpg"
        if not fallback_img.exists():
            cls.create_clean_documentary_frame(query, fallback_img)
        return fallback_img

    @classmethod
    def fetch_scene_broll(cls, query: str, out_dir: Path, scene_idx: int) -> Path:
        """Finds and downloads real B-roll video or photo for a scene, with clean documentary fallback."""
        return cls.fetch_media_for_beat(query, out_dir, f"scene_{scene_idx:02d}")

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
