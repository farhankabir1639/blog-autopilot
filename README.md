# 🚀 Blog Autopilot

Automate your entire blog pipeline — from keyword research to published post — using Google Sheets, Claude AI, and Sanity CMS.

**One command. One blog post. Zero manual writing.**

---

## What It Does

Blog Autopilot reads a row from your Google Sheets content strategy, generates a full SEO-optimized blog post using Claude, and publishes it directly to your Sanity CMS as a draft — ready for your final review.

```
Google Sheets → Claude AI → Sanity CMS
(keywords)      (content)    (published draft)
```

Each run:
1. Picks the next pending row from your Google Sheet
2. Reads the keyword, title, word count, priority, and content notes
3. Generates a complete, structured blog post via Claude API
4. Converts the content to Sanity Portable Text
5. Publishes it as a draft in Sanity Studio
6. Marks the row as "Done" in the sheet

---

## Project Structure

```
blog_autopilot/
├── main.py              # Entry point — run this
├── sheets_client.py     # Reads from Google Sheets, marks rows Done
├── generator.py         # Sends data to Claude → returns structured blog JSON
├── portable_text.py     # Converts blog JSON → Sanity Portable Text format
├── sanity_client.py     # Uploads to Sanity CMS via API
├── image_gen.py         # (Optional) Image generation module
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variable template
└── .gitignore
```

---

## Prerequisites

- Python 3.8+
- A [Google Cloud](https://console.cloud.google.com/) project with Sheets API enabled
- An [Anthropic](https://console.anthropic.com/) account
- A [Sanity](https://www.sanity.io/) project with a blog schema

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/farhankabir1639/blog-autopilot.git
cd blog-autopilot
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
SANITY_TOKEN=your_sanity_api_token
SANITY_PROJECT_ID=your_sanity_project_id
SANITY_DATASET=production
SHEET_ID=your_google_sheet_id
```

### 4. Set up Google Sheets authentication

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable the **Google Sheets API** and **Google Drive API**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Choose **Desktop App**, download the JSON file
6. Rename it to `credentials.json` and place it in the project root
7. On first run, a browser window will open asking you to authorize — do that once and a `token.pickle` will be saved for future runs

### 5. Set up your Google Sheet

Your sheet should have these columns (in order):

| # | title | primary_keyword | secondary_keyword_1 | secondary_keyword_2 | secondary_keyword_3 | priority | content_type | est. monthly traffic | target_word_count | notes | | status |
|---|-------|----------------|----|----|----|----|----|----|----|----|---|---|

- Leave `status` blank for rows that should be processed
- The script will set it to `Done` after publishing

---

## Usage

```bash
python main.py
```

Each run processes **one row** and publishes it as a draft in Sanity Studio. Run it again to process the next row.

After publishing, go to your Sanity Studio to:
- Review the generated content
- Add images manually
- Publish when ready

---

## Customization

The blog generation prompt lives in `generator.py`. You can customize:
- **Brand voice** — adjust the system prompt to match your company's tone
- **Blog structure** — modify the content template sections
- **Internal links** — add your own site's URLs for internal linking
- **Word count targets** — controlled per row in the sheet

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `invalid_grant: Bad Request` | Delete `token.pickle` and re-run to re-authenticate |
| `401 Unauthorized` (Sanity) | Regenerate your Sanity API token with Editor permissions |
| Sheet not found | Double-check your `SHEET_ID` in `.env` |
| Post published but no images | Add images manually in Sanity Studio — image uploads are handled separately |

---

## Contributing

PRs welcome! If you adapt this for a different CMS (WordPress, Contentful, etc.) or add new features, feel free to open a pull request.

---

## License

MIT — free to use, modify, and distribute.
