"""
Sanity CMS client.
Handles image asset uploads and blog post document creation via Sanity's REST API.
"""

import os
import re
import uuid
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from portable_text import blocks_to_portable_text

load_dotenv()

SANITY_PROJECT_ID = os.getenv("SANITY_PROJECT_ID", "3gmx9o2y")
SANITY_DATASET    = os.getenv("SANITY_DATASET",    "production")
SANITY_TOKEN      = os.getenv("SANITY_TOKEN")
AUTHOR_NAME       = os.getenv("AUTHOR_NAME", "iTenX Team")
API_VERSION       = "2021-06-07"

VALID_CATEGORIES = {
    "technology", "engineering", "ai-ml", "design", "business", "industry"
}


class SanityClient:
    def __init__(self):
        if not SANITY_TOKEN:
            raise ValueError("SANITY_TOKEN is not set in your .env file")
        self.project_id = SANITY_PROJECT_ID
        self.dataset    = SANITY_DATASET
        self.base_url   = f"https://{self.project_id}.api.sanity.io/v{API_VERSION}"
        self.headers    = {
            "Authorization": f"Bearer {SANITY_TOKEN}",
            "Content-Type":  "application/json",
        }

    # ──────────────────────────────────────────────────────────────────────
    # Image upload
    # ──────────────────────────────────────────────────────────────────────

    def upload_image(self, image_bytes: bytes | None, filename: str) -> str | None:
        """
        Upload raw image bytes to Sanity Assets.
        Returns the asset _id string, or None if image_bytes is None (skipped).
        """
        if image_bytes is None:
            return None

        safe_name = re.sub(r"[^a-z0-9\-_]", "-", filename.lower()) + ".png"
        url = f"https://{self.project_id}.api.sanity.io/v{API_VERSION}/assets/images/{self.dataset}"

        upload_headers = {
            "Authorization": f"Bearer {self.SANITY_TOKEN if hasattr(self, 'SANITY_TOKEN') else SANITY_TOKEN}",
            "Content-Type":  "image/png",
        }
        # Re-use self.headers auth but override content type
        upload_headers = {
            "Authorization": self.headers["Authorization"],
            "Content-Type":  "image/png",
        }

        params = {"filename": safe_name}
        response = requests.post(url, headers=upload_headers, params=params, data=image_bytes, timeout=60)

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Sanity image upload failed ({response.status_code}): {response.text[:300]}"
            )

        asset = response.json().get("document", {})
        asset_id = asset.get("_id")
        if not asset_id:
            raise RuntimeError(f"Sanity image upload response missing _id: {response.text[:200]}")

        return asset_id

    # ──────────────────────────────────────────────────────────────────────
    # Document creation
    # ──────────────────────────────────────────────────────────────────────

    def publish_post(self, blog_data: dict, uploaded_images: list) -> str:
        """
        Create and publish a blog post document in Sanity.
        Returns the new document _id.
        """
        doc_id = f"post-{uuid.uuid4().hex[:16]}"

        # Build image lookup by label
        image_lookup = {img["label"]: img for img in uploaded_images if img["asset_id"]}

        # ── Body (Portable Text) ──────────────────────────────────────────
        body_blocks = blocks_to_portable_text(blog_data["body"], image_lookup)

        # ── Main Image ───────────────────────────────────────────────────
        main_image_asset = image_lookup.get("main")
        main_image = None
        if main_image_asset:
            main_image = {
                "_type": "image",
                "asset": {
                    "_type": "reference",
                    "_ref":  main_image_asset["asset_id"],
                },
                "alt": main_image_asset.get("alt", blog_data.get("title", "")),
            }

        # ── Categories ───────────────────────────────────────────────────
        categories = [
            c for c in blog_data.get("categories", ["technology"])
            if c in VALID_CATEGORIES
        ]
        if not categories:
            categories = ["technology"]

        # ── Build document ───────────────────────────────────────────────
        document = {
            "_id":   doc_id,
            "_type": "post",
            "title": blog_data["title"],
            "slug": {
                "_type": "slug",
                "current": blog_data["slug"],
            },
            "author": {
                "name": AUTHOR_NAME,
            },
            "categories":  categories,
            "publishedAt": datetime.now(timezone.utc).isoformat(),
            "excerpt":     blog_data.get("excerpt", "")[:200],
            "body":        body_blocks,
            "seo": {
                "metaTitle":       blog_data.get("meta_title", blog_data["title"])[:60],
                "metaDescription": blog_data.get("meta_description", blog_data.get("excerpt", ""))[:160],
            },
        }

        if main_image:
            document["mainImage"] = main_image

        # ── Mutate (create) ───────────────────────────────────────────────
        mutation_url = f"{self.base_url}/data/mutate/{self.dataset}"
        payload = {
            "mutations": [
                {"createOrReplace": document}
            ]
        }

        response = requests.post(mutation_url, headers=self.headers, json=payload, timeout=60)

        if response.status_code not in (200, 201):
            raise RuntimeError(
                f"Sanity mutation failed ({response.status_code}): {response.text[:400]}"
            )

        result = response.json()
        results = result.get("results", [])
        if not results:
            raise RuntimeError(f"Sanity mutation returned no results: {result}")

        return results[0].get("id", doc_id)
