#!/usr/bin/env python3
"""
iTenX Blog Automation
Reads one pending row from Google Sheets → generates blog post with Claude
→ publishes to Sanity CMS (images added manually in Sanity Studio)
"""

import sys
from sheets_client import SheetsClient
from generator import BlogGenerator
from sanity_client import SanityClient


def main():
    print("\n🚀 iTenX Blog Automation Starting...\n")

    # ── 1. Fetch next pending row from Google Sheets ───────────────────────
    sheets = SheetsClient()
    row = sheets.get_next_pending_row()

    if not row:
        print("✅ No pending rows found. All posts are done!")
        sys.exit(0)

    print(f"📋 Processing row {row['row_index']}: \"{row['title']}\"")
    print(f"   Primary Keyword : {row['primary_keyword']}")
    print(f"   Secondary 1     : {row['secondary_1'] or 'None'}")
    print(f"   Secondary 2     : {row['secondary_2'] or 'None'}")
    print(f"   Secondary 3     : {row['secondary_3'] or 'None'}")
    print(f"   Target Words    : {row['target_word_count']}")
    print(f"   Priority        : {row['priority']}")
    print()

    # ── 2. Generate blog post with Claude ──────────────────────────────────
    print("✍️  Generating blog post with Claude...")
    generator = BlogGenerator()
    blog_data = generator.generate(row)
    print(f"   ✅ Blog generated — {blog_data['title']}")
    print()

    # ── 3. Publish to Sanity (no images — add manually in Studio) ──────────
    print("📤 Publishing to Sanity...")
    sanity = SanityClient()
    doc_id = sanity.publish_post(blog_data, uploaded_images=[])
    print(f"   ✅ Published! Document ID: {doc_id}")
    print()

    # ── 4. Mark row as Done in Google Sheets ──────────────────────────────
    sheets.mark_done(row["row_index"], doc_id)
    print(f"✅ Row {row['row_index']} marked as Done in Google Sheets\n")

    print("=" * 60)
    print(f"🎉 Blog post published successfully!")
    print(f"   Title  : {blog_data['title']}")
    print(f"   Slug   : {blog_data['slug']}")
    print(f"   Doc ID : {doc_id}")
    print(f"   Studio : https://3gmx9o2y.sanity.studio/desk/post;{doc_id}")
    print()
    print("📸 Don't forget to add images manually in Sanity Studio!")
    print("=" * 60)


if __name__ == "__main__":
    main()
