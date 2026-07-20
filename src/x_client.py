"""Publicación en X (API v2 vía tweepy, con imagen opcional). Respeta DRY_RUN."""
import os

import tweepy


def _client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_SECRET"],
    )


def _upload_media(image_path: str) -> str | None:
    """Sube la imagen con la API v1.1 (media upload) y devuelve el media_id."""
    try:
        auth = tweepy.OAuth1UserHandler(
            os.environ["X_API_KEY"], os.environ["X_API_SECRET"],
            os.environ["X_ACCESS_TOKEN"], os.environ["X_ACCESS_SECRET"],
        )
        api = tweepy.API(auth)
        media = api.media_upload(image_path)
        return str(media.media_id)
    except Exception:
        return None


def publish(text: str, image_path: str | None = None) -> str:
    """Publica un post (con imagen opcional). Devuelve el tweet id o 'dry-run'."""
    if os.getenv("DRY_RUN", "true").lower() == "true":
        return "dry-run"
    media_ids = None
    if image_path:
        mid = _upload_media(image_path)
        media_ids = [mid] if mid else None
    resp = _client().create_tweet(text=text, media_ids=media_ids)
    return str(resp.data["id"])
