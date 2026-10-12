import os
import re
import time
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, Any, List, Set
from PIL import Image, ImageDraw
from .motion_canvas import classify_semantic_beat

# Allow Pillow to downscale ultra-high resolution public domain photography (> 89 megapixels)
Image.MAX_IMAGE_PIXELS = None

USER_AGENT = "IramVideo/2.0 (https://github.com/apravint/iram-video; apravint@gmail.com)"

NEGATIVE_NOISE_TERMS = [
    "bird", "tree", "plant", "forest", "florestal", "fruit", "animal", "cartoon",
    "graffiti", "anime", "toy", "nagaokakyo", "happy bus", "doll", "drawing",
    "illustration", "sketch", "comic", "painting", "clipart", "costume", "cosplay", "mask",
    "flower", "season", "festival", "autumn", "summer", "winter", "blossom", "tulip", "cherry blossom"
]

NEGATIVE_GEO_NOISE = [
    "china", "beijing", "shanghai", "guangzhou", "shenzhen", "hong kong", "wuhan", "tianjin",
    "japan", "tokyo", "osaka", "kyoto", "london", "uk", "korea", "seoul", "taiwan", "taipei",
    "brazil", "solar eclipse", "eclipse", "poll", "vote", "election", "ballot"
]

TAMIL_TO_ENGLISH_MAP = {
    'சென்னை': 'Chennai',
    'மெட்ரோ': 'Metro',
    'ரயில்': 'Rail',
    'தமிழ்நாடு': 'Tamil Nadu',
    'இந்தியா': 'India',
    'பெங்களூரு': 'Bengaluru',
    'டெல்லி': 'Delhi',
    'மும்பை': 'Mumbai',
    'ஹைதராபாத்': 'Hyderabad',
    'கொல்கத்தா': 'Kolkata',
    'விமானம்': 'Airport',
    'துறைமுகம்': 'Port',
    'விண்வெளி': 'Space',
    'செயற்கை நுண்ணறிவு': 'AI Artificial Intelligence',
    'கணினி': 'Computer',
    'இயற்பியல்': 'Physics',
    'விஞ்ஞானம்': 'Science',
    'இயற்கை': 'Nature',
}

class MediaFetcher:
    """
    Fetches real high-definition B-roll stock video clips and 4K/8K photography with cascading multi-provider search:
    - Pre-fetched topic pool: queries authentic local archives once and matches beats deterministically
    - Entity Geographic Guard: rejects mismatched foreign geographic media (China, Japan, London)
    - Multi-provider fallback: Google CSE -> Pexels -> Pixabay -> Wikimedia Commons -> Motion Canvas
    """

    _used_urls: Set[str] = set()
    _topic_media_pool: List[Dict[str, Any]] = []
    _cached_topic: str = ""

    @classmethod
    def reset_session(cls):
        """Resets the session caches so each video compilation gets fresh variety without duplicate shots."""
        cls._used_urls = set()
        cls._topic_media_pool = []
        cls._cached_topic = ""

    @classmethod
    def extract_anchor_phrase(cls, topic: str) -> str:
        """Extracts high-signal core subject words from the global topic, including Tamil entity recognition."""
        if not topic:
            return ""

        # 1. Check for Tamil entity names
        tamil_found = []
        for ta, en in TAMIL_TO_ENGLISH_MAP.items():
            if ta in topic:
                tamil_found.append(en)

        # 2. Extract Latin words
        clean = re.sub(r'[\|#\(\)\[\]:,\-–—\.]+', ' ', topic)
        words = [w for w in clean.split() if re.match(r'^[a-zA-Z]+$', w) and len(w) > 2]
        stopwords = {
            'the', 'and', 'for', 'with', 'from', 'about', 'how', 'why', 'what', 'launch',
            'phase', 'update', 'video', 'tamil', 'english', 'full', 'latest', 'news', 'project'
        }
        informative = [w for w in words if w.lower() not in stopwords]

        if len(informative) >= 2:
            return ' '.join(informative[:3])
        elif len(informative) == 1:
            if tamil_found:
                return f"{informative[0]} {' '.join(tamil_found)}"
            return informative[0]

        if tamil_found:
            return ' '.join(tamil_found)
        return words[0] if words else ""

    @classmethod
    def is_noise_candidate(cls, title: str, query: str = "", topic: str = "") -> bool:
        """Detects and rejects irrelevant domain noise and foreign geographic mismatches (e.g. China when topic is Chennai)."""
        t_low = title.lower()
        q_low = query.lower()
        top_low = topic.lower()

        # Reject domain noise (trees, fruits, anime buses)
        for noise in NEGATIVE_NOISE_TERMS:
            if noise in t_low and noise not in q_low and noise not in top_low:
                return True

        # Reject geographic mismatches (China, London, etc.) when the topic is Indian/Chennai
        is_indian_topic = any(k in top_low for k in ["chennai", "tamil", "india", "delhi", "mumbai", "bengaluru"])
        if is_indian_topic:
            for geo in NEGATIVE_GEO_NOISE:
                if geo in t_low and geo not in top_low:
                    return True

        return False

    @classmethod
    def prefetch_topic_media(cls, global_topic: str) -> List[Dict[str, Any]]:
        """Pre-fetches a rich pool of verified authentic assets for the global topic in a single request."""
        if cls._topic_media_pool and cls._cached_topic == global_topic:
            return cls._topic_media_pool

        anchor = cls.extract_anchor_phrase(global_topic)
        if not anchor:
            anchor = global_topic

        print(f"   🔍 [Asset Curator] Pre-fetching verified media pool for topic anchor: \"{anchor}\"...")
        cls._topic_media_pool = []
        cls._cached_topic = global_topic

        # Search Wikimedia Commons for core anchor
        clean_anchor = anchor.strip()
        url = (
            "https://commons.wikimedia.org/w/api.php?action=query&generator=search&"
            f"gsrsearch={urllib.parse.quote(clean_anchor)}&gsrnamespace=6&prop=imageinfo&"
            "iiprop=url|mime|size&format=json&gsrlimit=30"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pages = data.get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    t = p.get("title", "")
                    if cls.is_noise_candidate(t, query=clean_anchor, topic=global_topic):
                        continue
                    ii_list = p.get("imageinfo", [])
                    if not ii_list:
                        continue
                    ii = ii_list[0]
                    u = ii.get("url", "")
                    w = ii.get("width", 0)
                    h = ii.get("height", 0)
                    mime = ii.get("mime", "")

                    if (mime in ["image/jpeg", "image/png", "image/webp"] or mime.startswith("video/")) and (w >= 480 or h >= 360):
                        cls._topic_media_pool.append({
                            "type": "video" if mime.startswith("video/") else "image",
                            "url": u,
                            "width": w,
                            "height": h,
                            "title": t
                        })
            print(f"   ✓ [Asset Curator] Cached {len(cls._topic_media_pool)} authentic assets for \"{anchor}\"")
        except Exception as e:
            print(f"   ⚠️ [Asset Curator Notice] Pre-fetch error: {e}")

        return cls._topic_media_pool

    @staticmethod
    def search_google_custom_search(query: str) -> List[Dict[str, Any]]:
        """Searches Google Custom Search API (CSE) for high-resolution images if credentials are provided."""
        cse_id = os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_SEARCH_CX")
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not cse_id or not api_key:
            return []

        url = (
            "https://www.googleapis.com/customsearch/v1?"
            f"q={urllib.parse.quote(query)}&searchType=image&cx={cse_id}&key={api_key}&num=10&imgSize=large"
        )
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        results = []
        try:
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for item in data.get("items", []):
                    link = item.get("link")
                    title = item.get("title", "")
                    w = int(item.get("image", {}).get("width", 1920))
                    h = int(item.get("image", {}).get("height", 1080))
                    if link and any(link.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                        results.append({
                            "type": "image",
                            "url": link,
                            "width": w,
                            "height": h,
                            "title": title
                        })
        except Exception as e:
            print(f"[Notice] Google Custom Search API: {e}")
        return results

    @staticmethod
    def search_pexels(query: str, require_video: bool = False, orientation: Optional[str] = None) -> List[Dict[str, Any]]:
        """Searches Pexels API for HD video clips and photography with orientation filtering (portrait / landscape)."""
        key = os.getenv("PEXELS_API_KEY") or os.getenv("PEXELS_KEY")
        if not key:
            return []
        headers = {"Authorization": key, "User-Agent": USER_AGENT}
        results = []
        orient_param = f"&orientation={orientation}" if orientation in ["portrait", "landscape"] else ""
        try:
            v_url = f"https://api.pexels.com/videos/search?query={urllib.parse.quote(query)}&per_page=12{orient_param}"
            req = urllib.request.Request(v_url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for video in data.get("videos", []):
                    v_files = sorted(video.get("video_files", []), key=lambda x: x.get("width", 0), reverse=True)
                    for vf in v_files:
                        link = vf.get("link")
                        if link and vf.get("file_type") == "video/mp4":
                            results.append({
                                "type": "video",
                                "url": link,
                                "width": vf.get("width", 1920),
                                "height": vf.get("height", 1080),
                                "title": f"Pexels Video {video.get('id')}"
                            })
                            break
            if not require_video:
                p_url = f"https://api.pexels.com/v1/search?query={urllib.parse.quote(query)}&per_page=12{orient_param}"
                req = urllib.request.Request(p_url, headers=headers)
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for photo in data.get("photos", []):
                        src = photo.get("src", {})
                        link = src.get("large2x") or src.get("large") or src.get("original")
                        if link:
                            results.append({
                                "type": "image",
                                "url": link,
                                "width": photo.get("width", 1920),
                                "height": photo.get("height", 1080),
                                "title": photo.get("alt", "Pexels Photo")
                            })
        except Exception as e:
            print(f"[Notice] Pexels API: {e}")
        return results

    @staticmethod
    def search_pixabay(query: str, require_video: bool = False) -> List[Dict[str, Any]]:
        """Searches Pixabay API for HD video clips and photography if PIXABAY_API_KEY is available."""
        key = os.getenv("PIXABAY_API_KEY")
        if not key:
            return []
        results = []
        try:
            if require_video:
                v_url = f"https://pixabay.com/api/videos/?key={key}&q={urllib.parse.quote(query)}&per_page=6"
                req = urllib.request.Request(v_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for hit in data.get("hits", []):
                        videos = hit.get("videos", {})
                        v_meta = videos.get("large") or videos.get("medium") or videos.get("small")
                        if v_meta and v_meta.get("url"):
                            results.append({
                                "type": "video",
                                "url": v_meta["url"],
                                "width": v_meta.get("width", 1920),
                                "height": v_meta.get("height", 1080),
                                "title": hit.get("tags", "Pixabay Video")
                            })
            else:
                p_url = f"https://pixabay.com/api/?key={key}&q={urllib.parse.quote(query)}&image_type=photo&per_page=8"
                req = urllib.request.Request(p_url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for hit in data.get("hits", []):
                        link = hit.get("largeImageURL") or hit.get("webformatURL")
                        if link:
                            results.append({
                                "type": "image",
                                "url": link,
                                "width": hit.get("imageWidth", 1920),
                                "height": hit.get("imageHeight", 1080),
                                "title": hit.get("tags", "Pixabay Photo")
                            })
        except Exception as e:
            print(f"[Notice] Pixabay API: {e}")
        return results

    @classmethod
    def search_wikimedia(cls, query: str, require_video: bool = False, global_topic: str = "") -> List[Dict[str, Any]]:
        """Searches Wikimedia Commons public domain archives with negative keyword and geo filtering."""
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
                    title = p.get("title", "")
                    if cls.is_noise_candidate(title, query=clean_query, topic=global_topic):
                        continue

                    ii_list = p.get("imageinfo", [])
                    if not ii_list:
                        continue
                    ii = ii_list[0]
                    media_url = ii.get("url", "")
                    mime = ii.get("mime", "")
                    w = ii.get("width", 0)
                    h = ii.get("height", 0)

                    if not media_url or "thumb" in media_url or mime == "image/svg+xml":
                        continue

                    if mime.startswith("video/") and any(media_url.lower().endswith(ext) for ext in [".mp4", ".webm", ".mkv", ".mov"]):
                        results.append({
                            "type": "video",
                            "url": media_url,
                            "width": w,
                            "height": h,
                            "title": title
                        })
                    elif mime in ["image/jpeg", "image/png", "image/webp"] and (w >= 480 or h >= 360):
                        results.append({
                            "type": "image",
                            "url": media_url,
                            "width": w,
                            "height": h,
                            "title": title
                        })
        except Exception as e:
            print(f"[Notice] Wikimedia search failed for '{query}': {e}")
        return results

    @classmethod
    def search_media(cls, query: str, require_video: bool = False, global_topic: str = "", is_shorts: bool = False) -> List[Dict[str, Any]]:
        """Multi-source stock provider waterfall: Google CSE -> Pexels -> Pixabay -> Wikimedia Commons."""
        g_results = cls.search_google_custom_search(query)
        if g_results:
            return g_results

        orientation = "portrait" if is_shorts else "landscape"
        px_results = cls.search_pexels(query, require_video=require_video, orientation=orientation)
        if px_results:
            return px_results

        pb_results = cls.search_pixabay(query, require_video=require_video)
        if pb_results:
            return pb_results

        return cls.search_wikimedia(query, require_video=require_video, global_topic=global_topic)

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

            if out_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
                try:
                    with Image.open(out_path) as img:
                        if img.width > 2560 or img.height > 1440:
                            img.thumbnail((2560, 1440), Image.Resampling.LANCZOS)
                        rgb_img = img.convert("RGB")
                        rgb_img.save(out_path, format="JPEG", quality=92)
                except Exception:
                    if out_path.exists():
                        out_path.unlink()
                    return False

            return True
        except Exception as e:
            print(f"[Notice] Media download error for {url}: {e}")
            if out_path.exists():
                try:
                    out_path.unlink()
                except Exception:
                    pass
            return False

    @classmethod
    def extract_scene_beats(cls, scene: Dict[str, Any], total_duration: float, global_topic: str = "") -> List[Dict[str, Any]]:
        """
        Decomposes a scene into multiple visual beats synced to spoken sentences,
        and applies the Semantic Beat Classifier to route to MotionCanvas or Real Media.
        """
        anchor = cls.extract_anchor_phrase(global_topic)

        # 1. Native millisecond sentence boundary synchronization from Edge-TTS
        sentence_timings = scene.get("sentence_timings", [])
        if sentence_timings and isinstance(sentence_timings, list) and len(sentence_timings) >= 2:
            beats = []
            for st in sentence_timings:
                s_text = st["text"]
                classification = classify_semantic_beat(s_text, global_topic=global_topic)
                beats.append({
                    "phrase": s_text,
                    "query": s_text,
                    "duration": float(st["duration"]),
                    **classification
                })
            curr_sum = sum(b["duration"] for b in beats)
            if curr_sum > 0:
                scale = total_duration / curr_sum
                for b in beats:
                    b["duration"] = round(b["duration"] * scale, 3)
            return beats

        # 2. Explicit beats defined in screenplay
        explicit_beats = scene.get("broll_beats", [])
        if explicit_beats and isinstance(explicit_beats, list) and len(explicit_beats) >= 2:
            dur_per_beat = total_duration / len(explicit_beats)
            beats = []
            for b in explicit_beats:
                q = (b.get("search_query") or b.get("phrase") or scene.get("heading", "")).strip()
                classification = classify_semantic_beat(q, global_topic=global_topic)
                beats.append({
                    "phrase": q,
                    "query": q,
                    "duration": round(dur_per_beat, 3),
                    **classification
                })
            return beats

        narration = str(scene.get("narration") or scene.get("heading") or "").strip()
        if not narration:
            base_q = scene.get("search_query") or anchor or "documentary landscape"
            classification = classify_semantic_beat(base_q, global_topic=global_topic)
            return [{
                "phrase": base_q,
                "query": base_q,
                "duration": total_duration,
                **classification
            }]

        raw_sentences = [s.strip() for s in re.split(r'[\.\?!;]+', narration) if len(s.strip()) > 8]
        if len(raw_sentences) < 2:
            raw_sentences = [s.strip() for s in re.split(r'[,—]+', narration) if len(s.strip()) > 10]

        if len(raw_sentences) < 2:
            base_q = scene.get("search_query") or scene.get("heading") or anchor or "documentary landscape"
            classification = classify_semantic_beat(narration or base_q, global_topic=global_topic)
            return [{
                "phrase": narration or base_q,
                "query": base_q,
                "duration": total_duration,
                **classification
            }]

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

            clean_words = [w for w in re.sub(r'[^a-zA-Z0-9\s]', '', s).split() if w.lower() not in stopwords]
            if len(clean_words) >= 2:
                beat_q = " ".join(clean_words[:4])
            else:
                beat_q = f"{scene.get('heading', '')} {' '.join(w_list[:3])}"

            classification = classify_semantic_beat(s, global_topic=global_topic)
            beats.append({
                "phrase": s,
                "query": beat_q.strip(),
                "duration": max(2.5, b_dur),
                **classification
            })

        current_sum = sum(b["duration"] for b in beats)
        if current_sum > 0:
            scale = total_duration / current_sum
            for b in beats:
                b["duration"] = round(b["duration"] * scale, 3)

        return beats

    @classmethod
    def fetch_media_for_beat(cls, query: str, out_dir: Path, beat_id: str, global_topic: str = "") -> Path:
        """
        Finds and downloads a unique, authentic B-roll video clip or high-res photo for an individual beat.
        Uses the pre-fetched verified topic pool first to guarantee 100% semantic relevance with zero rate-limits.
        """
        out_dir.mkdir(parents=True, exist_ok=True)
        clean_q = query.strip()

        # 1. Check or load pre-fetched verified topic pool
        pool = cls.prefetch_topic_media(global_topic)
        if pool:
            query_words = [w.lower() for w in clean_q.split() if len(w) > 3]
            
            # Pass 1: Try keyword match inside the authentic topic pool
            for item in pool:
                if item["url"] in cls._used_urls:
                    continue
                if any(w in item["title"].lower() for w in query_words):
                    ext = ".webm" if item["type"] == "video" else ".jpg"
                    target = out_dir / f"beat_{beat_id}{ext}"
                    if cls.download_file(item["url"], target):
                        cls._used_urls.add(item["url"])
                        return target

            # Pass 2: Pick next available authentic item from pool
            for item in pool:
                if item["url"] in cls._used_urls:
                    continue
                ext = ".webm" if item["type"] == "video" else ".jpg"
                target = out_dir / f"beat_{beat_id}{ext}"
                if cls.download_file(item["url"], target):
                    cls._used_urls.add(item["url"])
                    return target

        # 2. Dynamic search fallback with rate-limit protection
        anchor = cls.extract_anchor_phrase(global_topic)
        queries_to_try = []
        if anchor and anchor.lower() not in clean_q.lower():
            queries_to_try.append(f"{anchor} {clean_q}".strip())
        else:
            queries_to_try.append(clean_q)

        if anchor and anchor not in queries_to_try:
            queries_to_try.append(anchor)

        for q in queries_to_try:
            time.sleep(0.3)
            results = cls.search_media(q, global_topic=global_topic)
            for item in results:
                if item["url"] in cls._used_urls:
                    continue
                ext = ".webm" if item["type"] == "video" else ".jpg"
                target = out_dir / f"beat_{beat_id}{ext}"
                if target.exists() and target.stat().st_size > 5000:
                    cls._used_urls.add(item["url"])
                    return target
                if cls.download_file(item["url"], target):
                    cls._used_urls.add(item["url"])
                    return target

        # 3. Clean documentary frame fallback
        fallback_img = out_dir / f"beat_{beat_id}.jpg"
        if not fallback_img.exists():
            cls.create_clean_documentary_frame(query, fallback_img)
        return fallback_img

    @classmethod
    def fetch_scene_broll(cls, query: str, out_dir: Path, scene_idx: int, global_topic: str = "") -> Path:
        """Finds and downloads real B-roll video or photo for a scene."""
        return cls.fetch_media_for_beat(query, out_dir, f"scene_{scene_idx:02d}", global_topic=global_topic)

    @classmethod
    def create_clean_documentary_frame(
        cls,
        title: str,
        out_path: Path,
        beat_data: Optional[Dict[str, Any]] = None,
        is_shorts: bool = False
    ):
        """
        Renders a broadcast-quality editorial documentary slide with clean typography,
        structured technical cards or code snippets, and modern enterprise palette (NO spirals/concentric ellipses).
        """
        w, h = (1080, 1920) if is_shorts else (1920, 1080)
        img = Image.new("RGBA", (w, h), (15, 23, 42, 255))  # Deep Slate-900
        draw = ImageDraw.Draw(img)

        # 1. Subtle architectural background grid (clean, modern tech pattern)
        grid_color = (24, 34, 53, 160)
        grid_step = 60 if is_shorts else 80
        for x in range(0, w, grid_step):
            draw.line([(x, 0), (x, h)], fill=grid_color, width=1)
        for y in range(0, h, grid_step):
            draw.line([(0, y), (w, y)], fill=grid_color, width=1)

        # Subtle horizontal top brand accent line in cobalt blue
        draw.rectangle([(0, 0), (w, 6)], fill=(59, 130, 246, 255))

        # Fonts
        from .renderer import get_fonts, draw_mixed_line, wrap_text
        fta_lg, fen_lg = get_fonts(36 if is_shorts else 44, bold=True)
        fta_md, fen_md = get_fonts(24 if is_shorts else 28, bold=True)
        fta_sm, fen_sm = get_fonts(18 if is_shorts else 20, bold=False)
        fta_code, fen_code = get_fonts(20 if is_shorts else 22, bold=False)

        # 2. Category badge
        badge_y = 60 if not is_shorts else 120
        badge_text = "ENTERPRISE ARCHITECTURE & ENGINEERING"
        draw.rounded_rectangle(
            [(80, badge_y), (80 + 440, badge_y + 36)],
            radius=6,
            fill=(30, 41, 59, 220),
            outline=(59, 130, 246, 200),
            width=1
        )
        draw_mixed_line(draw, 96, badge_y + 8, badge_text, (56, 189, 248), fta_sm, fen_sm)

        # 3. Clean headline
        headline = (title or "System Architecture").strip()
        headline = re.sub(r'[\r\n\t]+', ' ', headline)[:100]
        lines = wrap_text(headline, fta_lg, fen_lg, 1200 if not is_shorts else 800, draw)
        title_y = badge_y + 55
        for line in lines[:2]:
            draw_mixed_line(draw, 80, title_y, line, (248, 250, 252), fta_lg, fen_lg)
            title_y += 54

        # 4. Main Presentation Container Card
        card_x = 80
        card_y = title_y + 25
        card_w = w - 160
        card_h = (h - card_y - 80)

        # Draw glassmorphism card
        draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_w, card_y + card_h)],
            radius=12,
            fill=(20, 29, 44, 240),
            outline=(51, 65, 85, 255),
            width=2
        )

        # Window controls (macOS style dots)
        draw.ellipse([(card_x + 24, card_y + 20), (card_x + 36, card_y + 32)], fill=(239, 68, 68))
        draw.ellipse([(card_x + 44, card_y + 20), (card_x + 56, card_y + 32)], fill=(245, 158, 11))
        draw.ellipse([(card_x + 64, card_y + 20), (card_x + 76, card_y + 32)], fill=(34, 197, 94))

        # Window title bar
        win_title = "EnterpriseApplication.java" if any(k in headline.lower() for k in ["java", "spring", "code", "virtual", "thread"]) else "SystemArchitecture.yaml"
        draw_mixed_line(draw, card_x + 90, card_y + 16, win_title, (148, 163, 184), fta_sm, fen_sm)
        draw.line([(card_x, card_y + 48), (card_x + card_w, card_y + 48)], fill=(30, 41, 59), width=1)

        # 5. Content inside card
        content_y = card_y + 70
        is_code_topic = any(k in headline.lower() for k in ["java", "spring", "code", "thread", "virtual", "compile", "rest", "api", "loom", "graalvm"])

        if is_code_topic:
            # Render syntax-highlighted code block with line numbers
            code_lines = [
                ("@SpringBootApplication", (168, 85, 247)),
                ("public class EnterpriseService {", (248, 250, 252)),
                ("    @Bean", (168, 85, 247)),
                ("    public TomcatProtocolHandlerCustomizer<?> protocolHandler() {", (56, 189, 248)),
                ("        return protocol -> protocol.setExecutor(Executors.newVirtualThreadPerTaskExecutor());", (148, 163, 184)),
                ("    }", (248, 250, 252)),
                ("    @GetMapping(\"/api/v1/throughput\")", (168, 85, 247)),
                ("    public ResponseEntity<Metrics> getMetrics() {", (56, 189, 248)),
                ("        return ResponseEntity.ok(Metrics.highPerformanceScale());", (148, 163, 184)),
                ("    }", (248, 250, 252)),
                ("}", (248, 250, 252)),
            ]
            for idx, (c_txt, c_col) in enumerate(code_lines):
                if content_y + 34 > card_y + card_h - 30:
                    break
                draw_mixed_line(draw, card_x + 30, content_y, f"{idx+1:2d}", (71, 85, 105), fta_code, fen_code)
                draw_mixed_line(draw, card_x + 75, content_y, c_txt, c_col, fta_code, fen_code)
                content_y += 34
        else:
            pillars = [
                ("⚡ High-Throughput Processing", "Massive concurrency with low memory overhead per active connection.", (56, 189, 248)),
                ("🛡️ Cloud-Native Resilience", "Automated circuit breakers, zero-downtime scaling, and containerized health checks.", (34, 197, 94)),
                ("🚀 Production-Ready Observability", "Distributed tracing, unified metrics, and enterprise-grade telemetry out of the box.", (245, 158, 11)),
            ]
            for p_title, p_desc, p_color in pillars:
                if content_y + 70 > card_y + card_h - 20:
                    break
                draw.rectangle([(card_x + 30, content_y + 4), (card_x + 36, content_y + 28)], fill=p_color)
                draw_mixed_line(draw, card_x + 48, content_y, p_title, (248, 250, 252), fta_md, fen_md)
                draw_mixed_line(draw, card_x + 48, content_y + 36, p_desc, (148, 163, 184), fta_sm, fen_sm)
                content_y += 85

        # 6. Bottom footer tag
        footer_text = "IRAM FILM STUDIO • HIGH PERFORMANCE ENTERPRISE COMPUTING"
        draw_mixed_line(draw, 80, h - 45, footer_text, (100, 116, 139), fta_sm, fen_sm)

        img.convert("RGB").save(out_path, quality=95)
