# iTenX Blog Automation

Reads one pending row from your Google Sheet → generates a full blog post with Claude → creates images with Gemini Imagen → publishes directly to your Sanity CMS.

---

## How It Works

```
Google Sheets (1 pending row)
        ↓
Claude claude-sonnet-4-6 (generate full blog JSON)
        ↓
Gemini Imagen 3 (generate 5-6 images per post)
        ↓
Sanity CMS (upload images + publish blog document)
        ↓
Google Sheets (mark row as "Done — [doc_id]")
```

---

## Setup (one-time, ~15 minutes)

### Step 1 — Install Python dependencies

```bash
cd blog_automation
pip install -r requirements.txt
```

> Requires Python 3.10+. Check with `python --version`.

---

### Step 2 — Get your API keys

**Anthropic (Claude)**
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy it into `.env` as `ANTHROPIC_API_KEY`

**Google Gemini (Imagen)**
1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key
3. Copy it into `.env` as `GEMINI_API_KEY`

> ⚠️ Imagen 3 requires a **paid** Google AI Studio account (free tier doesn't include image generation). If you hit a 403 error, see "Gemini Troubleshooting" below.

**Sanity Write Token**
1. Go to https://sanity.io/manage → select your iTenX project
2. Click **API** → **Tokens** → **Add API token**
3. Name it "Blog Automation", set role to **Editor**
4. Copy the token into `.env` as `SANITY_TOKEN`

---

### Step 3 — Google Sheets service account

This lets the script read/write your Google Sheet without logging in manually.

1. Go to https://console.cloud.google.com
2. Create a new project (or use an existing one)
3. Enable **Google Sheets API** and **Google Drive API**
   - Search "Sheets API" → Enable
   - Search "Drive API" → Enable
4. Go to **IAM & Admin** → **Service Accounts** → **Create Service Account**
   - Name: `blog-automation`
   - Role: `Editor` (or just `Viewer` + share the sheet manually)
5. Once created, click the service account → **Keys** → **Add Key** → **JSON**
6. Download the JSON file and place it in the `blog_automation/` folder as `credentials.json`
7. **Share your Google Sheet** with the service account email (looks like `blog-automation@your-project.iam.gserviceaccount.com`) — give it **Editor** access

---

### Step 4 — Configure `.env`

```bash
cp .env.example .env
```

Fill in all values in `.env`:

```
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
SANITY_PROJECT_ID=3gmx9o2y
SANITY_DATASET=production
SANITY_TOKEN=sk...
SHEET_ID=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms   ← your sheet ID
GOOGLE_CREDENTIALS_FILE=credentials.json
AUTHOR_NAME=iTenX Team
```

Your **Sheet ID** is in the URL of your Google Sheet:
`https://docs.google.com/spreadsheets/d/**YOUR_SHEET_ID_HERE**/edit`

---

### Step 5 — Add a "Status" column to your sheet

The script handles this automatically — it will add a `Status` header to column L on first run.

Alternatively, manually add a **Status** column header in row 1, column L of your sheet tab.

---

## Running the automation

```bash
cd blog_automation
python main.py
```

The script will:
1. Find the **first row** where Status is empty
2. Generate the blog post (takes ~30-60 seconds for Claude)
3. Generate images (takes ~20-40 seconds for Gemini)
4. Upload everything to Sanity
5. Mark the row as `Done — [doc_id]`

**To process the next post**, just run it again. Each run handles one row.

---

## After publishing

Your blog post will appear in Sanity Studio as a **draft**. Review it at:

```
https://your-studio-url/desk/post
```

From there you can:
- Review and edit the content
- Check all images loaded correctly
- Publish or schedule the post

---

## Gemini Imagen Troubleshooting

If Gemini image generation fails, the script will still publish the blog post — just without images. You'll see a warning in the console.

**Common errors:**

| Error | Fix |
|---|---|
| `403 Forbidden` | Imagen 3 requires billing enabled in Google Cloud. Enable it at console.cloud.google.com |
| `404 Not Found` | Model name may have changed. Check https://ai.google.dev/models |
| `429 Rate Limited` | You hit the quota. Wait a minute and re-run |

**Alternative: Use Vertex AI instead of Google AI Studio**

If you have a Google Cloud project with Vertex AI enabled, change `image_gen.py`:

```python
# Replace the URL with:
url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_GCP_PROJECT/locations/us-central1/publishers/google/models/imagen-3.0-generate-002:predict"

# And add your GCP auth token instead of API key
```

---

## Customizing the blog prompt

The prompt Claude receives is defined in `generator.py` in the `build_user_prompt()` function and `SYSTEM_PROMPT` constant.

You can customize:
- **SYSTEM_PROMPT** — iTenX brand voice, writing style, value propositions
- **build_user_prompt()** — specific requirements, word count, image count, etc.

---

## File structure

```
blog_automation/
├── main.py              # Run this — orchestrates everything
├── sheets_client.py     # Google Sheets read/write
├── generator.py         # Claude blog generation
├── image_gen.py         # Gemini Imagen generation
├── sanity_client.py     # Sanity upload & publish
├── portable_text.py     # JSON → Sanity Portable Text converter
├── requirements.txt     # Python dependencies
├── .env.example         # Copy to .env and fill in
├── credentials.json     # Your Google service account key (you add this)
└── README.md            # This file
```
