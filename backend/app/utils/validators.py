import ipaddress
import re
import urllib.parse
import uuid
from typing import Optional, Tuple

# Allowed domains by platform
ALLOWED_INSTAGRAM_DOMAINS = {"instagram.com", "www.instagram.com", "m.instagram.com"}
ALLOWED_YOUTUBE_DOMAINS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
ALLOWED_FACEBOOK_DOMAINS = {"facebook.com", "www.facebook.com", "m.facebook.com", "web.facebook.com", "fb.watch"}

# Union of all allowed domains
ALLOWED_ALL_DOMAINS = ALLOWED_INSTAGRAM_DOMAINS | ALLOWED_YOUTUBE_DOMAINS | ALLOWED_FACEBOOK_DOMAINS

# Legacy alias for backward compatibility
ALLOWED_DOMAINS = ALLOWED_INSTAGRAM_DOMAINS

# Regex pattern for Instagram Reel shortcode (handles /reel/CODE/ or /reels/CODE/)
REEL_URL_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.)?instagram\.com\/reels?\/([A-Za-z0-9_-]+)",
    re.IGNORECASE
)

# Regex pattern for general Instagram posts/videos
INSTAGRAM_POST_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.)?instagram\.com\/(?:reels?|p|tv)\/([A-Za-z0-9_-]+)",
    re.IGNORECASE
)

# Regex patterns for YouTube
YOUTUBE_WATCH_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.|music\.)?youtube\.com\/watch\?(?:.*&)?v=([A-Za-z0-9_-]{11})",
    re.IGNORECASE
)
YOUTUBE_SHORTS_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.)?youtube\.com\/shorts\/([A-Za-z0-9_-]{11})",
    re.IGNORECASE
)
YOUTUBE_SHORT_LINK_REGEX = re.compile(
    r"^https?:\/\/youtu\.be\/([A-Za-z0-9_-]{11})",
    re.IGNORECASE
)
YOUTUBE_EMBED_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.)?youtube\.com\/embed\/([A-Za-z0-9_-]{11})",
    re.IGNORECASE
)

# Regex patterns for Facebook
FACEBOOK_REEL_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.|web\.)?facebook\.com\/reel\/([0-9A-Za-z_-]+)",
    re.IGNORECASE
)
FACEBOOK_WATCH_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.|web\.)?facebook\.com\/watch\/?\?(?:.*&)?v=([0-9]+)",
    re.IGNORECASE
)
FACEBOOK_VIDEO_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.|web\.)?facebook\.com\/(?:[A-Za-z0-9_.-]+)\/videos\/([0-9]+)",
    re.IGNORECASE
)
FACEBOOK_FBWATCH_REGEX = re.compile(
    r"^https?:\/\/fb\.watch\/([0-9A-Za-z_-]+)",
    re.IGNORECASE
)
FACEBOOK_SHARE_REGEX = re.compile(
    r"^https?:\/\/(?:www\.|m\.|web\.)?facebook\.com\/share\/[rv]\/([0-9A-Za-z_-]+)",
    re.IGNORECASE
)

# UUID4 validation regex
UUID_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE
)


class ValidationError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def is_private_ip(hostname: str) -> bool:
    """Checks whether the hostname is an IP address pointing to localhost or private network."""
    if hostname.lower() in {"localhost", "localhost.localdomain", "127.0.0.1", "::1", "0.0.0.0"}:
        return True
    try:
        ip = ipaddress.ip_address(hostname.strip("[]"))
        return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast
    except ValueError:
        return False


def detect_platform_from_url(url: str) -> Optional[str]:
    """Detects which platform a URL belongs to based on hostname."""
    if not url or not isinstance(url, str):
        return None
    try:
        parsed = urllib.parse.urlparse(url.strip())
        hostname = (parsed.hostname or "").lower()
        if hostname in ALLOWED_INSTAGRAM_DOMAINS:
            return "instagram"
        if hostname in ALLOWED_YOUTUBE_DOMAINS:
            return "youtube"
        if hostname in ALLOWED_FACEBOOK_DOMAINS:
            return "facebook"
    except Exception:
        pass
    return None


def validate_and_normalize_reel_url(url: str) -> Tuple[str, str]:
    """
    Validates that a URL is a legitimate public Instagram Reel URL.
    Maintained for full backward compatibility with existing tests and endpoints.
    """
    if not url or not isinstance(url, str):
        raise ValidationError("Please enter a valid public Instagram Reel URL.")
    
    url = url.strip()
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        raise ValidationError("Malformed URL. Please check the Reel link.")
    
    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("Invalid URL scheme. Only HTTPS Instagram URLs are accepted.")
    
    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValidationError("Invalid URL: missing host.")
    
    if is_private_ip(hostname):
        raise ValidationError("Access to private/local network addresses is strictly prohibited.")
    
    if hostname not in ALLOWED_INSTAGRAM_DOMAINS:
        raise ValidationError("Unsupported domain. Only official Instagram Reel links are supported.")
    
    match = REEL_URL_REGEX.match(url)
    if not match:
        raise ValidationError(
            "Please enter a valid public Instagram Reel URL (e.g. https://www.instagram.com/reel/Daf2gF3vCzS/)."
        )
    
    shortcode = match.group(1)
    if not shortcode or len(shortcode) < 3:
        raise ValidationError("Invalid Instagram Reel identifier.")
    
    normalized_url = f"https://www.instagram.com/reel/{shortcode}/"
    return normalized_url, shortcode


def validate_and_normalize_url(url: str, selected_platform: Optional[str] = "instagram") -> Tuple[str, str, str]:
    """
    Validates that a URL is a legitimate public URL for Instagram, YouTube, or Facebook.
    Protects against SSRF, arbitrary external domains, and malformed URLs.

    Returns:
        Tuple of (normalized_url, media_id, detected_platform)

    Raises:
        ValidationError with a clear user-facing message.
    """
    if not url or not isinstance(url, str):
        target = (selected_platform or "media").capitalize()
        raise ValidationError(f"Please enter a valid {target} URL.")

    url = url.strip()
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        raise ValidationError("Malformed URL. Please check the link.")

    if parsed.scheme not in {"http", "https"}:
        raise ValidationError("Invalid URL scheme. Only HTTP and HTTPS URLs are accepted.")

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        raise ValidationError("Invalid URL: missing host.")

    if is_private_ip(hostname):
        raise ValidationError("Access to private/local network addresses is strictly prohibited.")

    # Detect platform
    detected = detect_platform_from_url(url)
    if not detected:
        raise ValidationError("Unsupported domain. Supported platforms: Instagram, YouTube, and Facebook.")

    platform_choice = (selected_platform or "auto").strip().lower()
    if platform_choice not in {"auto", "instagram", "youtube", "facebook"}:
        platform_choice = "auto"

    # Enforce platform selection if explicit
    if platform_choice != "auto" and detected != platform_choice:
        raise ValidationError(
            f"The entered link is from {detected.capitalize()}, but you selected {platform_choice.capitalize()}. "
            f"Please switch to {detected.capitalize()} or enter a {platform_choice.capitalize()} link."
        )

    # 1. Instagram Validation
    if detected == "instagram":
        match = INSTAGRAM_POST_REGEX.match(url)
        if not match:
            raise ValidationError(
                "Please enter a valid public Instagram Reel, Post, or video URL (e.g. https://www.instagram.com/reel/Daf2gF3vCzS/ or https://www.instagram.com/p/...)."
            )
        shortcode = match.group(1)
        if not shortcode or len(shortcode) < 3:
            raise ValidationError("Invalid Instagram identifier.")
        post_type = "p" if "/p/" in url else ("tv" if "/tv/" in url else "reel")
        normalized_url = f"https://www.instagram.com/{post_type}/{shortcode}/"
        return normalized_url, shortcode, "instagram"

    # 2. YouTube Validation
    if detected == "youtube":
        media_id = None
        for regex in [YOUTUBE_WATCH_REGEX, YOUTUBE_SHORTS_REGEX, YOUTUBE_SHORT_LINK_REGEX, YOUTUBE_EMBED_REGEX]:
            m = regex.match(url)
            if m:
                media_id = m.group(1)
                break

        if not media_id:
            # Query parameter fallback for watch?v=...
            query_params = urllib.parse.parse_qs(parsed.query)
            if "v" in query_params and query_params["v"] and len(query_params["v"][0]) == 11:
                media_id = query_params["v"][0]

        if not media_id:
            raise ValidationError(
                "Please enter a valid public YouTube video or Shorts link (e.g. https://www.youtube.com/watch?v=... or https://youtu.be/...)."
            )

        normalized_url = f"https://www.youtube.com/watch?v={media_id}"
        return normalized_url, media_id, "youtube"

    # 3. Facebook Validation
    if detected == "facebook":
        media_id = None
        # Check standard Facebook patterns
        for regex in [FACEBOOK_REEL_REGEX, FACEBOOK_WATCH_REGEX, FACEBOOK_VIDEO_REGEX, FACEBOOK_FBWATCH_REGEX, FACEBOOK_SHARE_REGEX]:
            m = regex.match(url)
            if m:
                media_id = m.group(1)
                break

        if not media_id:
            query_params = urllib.parse.parse_qs(parsed.query)
            if "v" in query_params and query_params["v"]:
                media_id = query_params["v"][0]

        if not media_id:
            # Fallback: check if path contains /videos/ or /reel/
            if "/videos/" in parsed.path or "/reel/" in parsed.path or "/watch" in parsed.path:
                media_id = "fb_video"
            else:
                raise ValidationError(
                    "Please enter a valid public Facebook Reel or video link (e.g. https://www.facebook.com/reel/... or https://fb.watch/...)."
                )

        # For fb.watch or share links, keep clean URL without tracking params
        clean_url = urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
        if "/watch" in parsed.path and "v" in urllib.parse.parse_qs(parsed.query):
            v_val = urllib.parse.parse_qs(parsed.query)["v"][0]
            clean_url = f"https://www.facebook.com/watch/?v={v_val}"
        elif not clean_url.endswith("/"):
            clean_url += "/"

        return clean_url, str(media_id), "facebook"

    raise ValidationError("Unsupported platform.")


def validate_job_id(job_id: str) -> str:
    """Validates that a job_id is a valid UUID to prevent path traversal attacks."""
    if not job_id or not isinstance(job_id, str):
        raise ValidationError("Invalid job ID.")
    cleaned = job_id.strip()
    try:
        val = uuid.UUID(cleaned, version=4)
        return str(val)
    except (ValueError, AttributeError):
        raise ValidationError("Invalid job ID format.")
