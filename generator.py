"""
Blog post generator using Claude claude-sonnet-4-6.
Returns structured JSON that maps directly to the Sanity schema.
"""

import os
import json
import re
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AUTHOR_NAME = os.getenv("AUTHOR_NAME", "iTenX Team")

SYSTEM_PROMPT = """You are an expert B2B content writer and SEO strategist for iTenX, a nearshore/offshore 
software development company targeting US/Canada-based businesses.

━━━ WRITING PHILOSOPHY ━━━
Write content that is optimized for THREE audiences simultaneously:
1. HUMAN READERS (CTOs, VPs of Engineering, startup founders)
2. SEARCH ENGINES (Google, Bing)
3. AI TOOLS (ChatGPT, Claude, Gemini, Perplexity) — these increasingly surface content as answers

For AI tools to cite your content, it must be:
- Factually precise with specific data points, numbers, and named examples
- Structured clearly with direct answers near the top of each section
- Written in a confident, authoritative tone that reads like expert knowledge
- Free of filler — every sentence must carry information value
- Quotable: include at least 1-2 sentences per section that stand alone as a clear, citable insight

For human readers, content must be:
- Conversational and direct — like advice from a trusted colleague
- Easy to scan: clear headings, short paragraphs, no walls of text
- Genuinely useful — practical takeaways the reader can act on immediately

For SEO, content must be:
- Keyword-intentional but never keyword-stuffed
- Well-linked to authoritative sources and relevant internal pages
- Structured with logical heading hierarchy (H2 → H3)

━━━ KEYWORD RULES ━━━
- PRIMARY KEYWORD: Use in title, opening paragraph, one H2, and 3-5x naturally in body
- SECONDARY KEYWORDS: Only use if they fit naturally. One well-placed secondary keyword 
  beats three forced ones. Ask: "Would a human writer naturally say this here?"
- Never place two target keywords in the same sentence
- Use semantic variations — don't just repeat exact phrases

━━━ LINKING RULES ━━━
INTERNAL LINKS — use real iTenX blog URLs, only when genuinely relevant:
  https://itenx.it.com/blog/nearshore-vs-offshore-development-guide
  https://itenx.it.com/blog/offshore-mobile-app-development-guide
  https://itenx.it.com/blog/outsourced-product-development-guide
  https://itenx.it.com/blog/agile-nearshore-development-guide
  https://itenx.it.com/blog/how-to-build-nearshore-development-team
  https://itenx.it.com/blog/application-outsourcing-benefits-best-practices
  https://itenx.it.com/blog/offshore-outsourcing-services-guide
  Max 3-4 internal links per post. Only link when it helps the reader go deeper.

EXTERNAL LINKS — cite high-authority sources when using statistics:
  Stack Overflow Developer Survey, Gartner, McKinsey, Deloitte, GitHub Octoverse,
  LinkedIn Workforce Report, Statista, Harvard Business Review, Forbes, TechCrunch
  Use real, verifiable URLs. Max 2-3 external links per post.
  Format: "According to [Source](URL), X% of..."

iTenX VALUE PROPS (mention naturally 2-3x max):
- Nearshore Latin American teams — same timezone as US/Canada
- Senior engineers at $45-85/hr vs $150-200/hr onshore
- Direct communication, no middlemen, agile process
- Trusted by VC-backed startups and mid-market SaaS

CRITICAL: Respond with valid, complete JSON only. No markdown, no explanation."""


def build_user_prompt(row: dict) -> str:
    primary_keyword = row["primary_keyword"]

    secondary_keywords = []
    for k in [row["secondary_1"], row["secondary_2"], row["secondary_3"]]:
        if k and k.strip():
            secondary_keywords.append(k.strip())

    word_count = 2000
    try:
        word_count = min(int(row.get("target_word_count", "2000") or "2000"), 2000)
    except (ValueError, TypeError):
        word_count = 2000

    notes = row.get("notes", "")

    if secondary_keywords:
        secondary_block = f"""SECONDARY KEYWORDS — use ONLY if they fit naturally (skip if forced):
{chr(10).join(f'  - "{kw}"' for kw in secondary_keywords)}
  Rule: It is better to use 1 secondary keyword well than all {len(secondary_keywords)} poorly."""
    else:
        secondary_block = "SECONDARY KEYWORDS: None — focus entirely on the primary keyword."

    return f"""Write a complete blog post for iTenX that ranks on Google AND gets cited by AI tools like ChatGPT, Claude, and Gemini.

━━━ KEYWORD BRIEF ━━━
PRIMARY KEYWORD: "{primary_keyword}"
→ Use in: title, opening paragraph, one H2, and 3-5x naturally throughout

{secondary_block}

━━━ POST DETAILS ━━━
TITLE: {row["title"]}
CONTENT TYPE: {row["content_type"]}
TARGET LENGTH: {word_count} words (keep each paragraph under 80 words)
PRIORITY: {row["priority"]}
NOTES: {notes if notes else "None"}

━━━ STRUCTURE REQUIREMENTS ━━━
1. OPENING (no heading): 2-3 sentence hook that includes the primary keyword and answers 
   what the post is about immediately — AI tools look for direct answers at the top

2. BODY SECTIONS (5-6 H2s):
   - Start each H2 section with a 1-sentence direct answer/summary of that section
   - Follow with supporting detail, examples, and data
   - Include at least one specific stat with an external link to a real source
   - Add 1 internal iTenX link where it genuinely helps the reader go deeper
   - One section must include a practical framework, comparison, or step-by-step guide
   - One section must include a brief real-world example or case study

3. AI CITABILITY — include at least 3 "quotable" sentences across the post:
   Clear, standalone statements of fact or insight that AI tools can extract and cite.
   Examples of quotable sentences:
   - "Nearshore developers in Latin America typically cost 55-65% less than equivalent US talent."
   - "Companies that switch to nearshore development report an average 40% reduction in time-to-hire."
   These should feel natural in context — not like they were written for AI.

4. CLOSING CTA (H2): Soft, helpful close that mentions iTenX naturally.

5. LINKS:
   - 3-4 internal links to real iTenX blog posts (from the list in your instructions)
   - 2-3 external links to named, authoritative sources with real URLs

━━━ HUMAN + AI READABILITY CHECKLIST ━━━
✓ Opening answers the main question within the first 2 sentences
✓ Each section starts with a direct, quotable insight
✓ No paragraph longer than 80 words
✓ Keywords feel invisible — placed where a human would naturally use them
✓ Every link adds genuine value for the reader
✓ A CTO would forward this to their team

Return ONLY this complete JSON (no truncation):
{{
  "title": "Compelling, keyword-optimized title",
  "slug": "url-friendly-slug",
  "excerpt": "150-char preview answering the main question, includes primary keyword",
  "meta_title": "Primary keyword + value prop, 50-60 chars",
  "meta_description": "Direct answer + primary keyword + CTA, 150-160 chars",
  "categories": ["business"],
  "image_prompts": [
    {{
      "label": "main",
      "prompt": "Professional photorealistic scene directly relevant to '{primary_keyword}': diverse software development team collaborating, modern office, screens showing code, warm natural lighting",
      "alt": "Alt text that includes the primary keyword naturally",
      "caption": ""
    }},
    {{
      "label": "inline_1",
      "prompt": "Scene relevant to the specific section where this image appears in the post",
      "alt": "Descriptive alt text",
      "caption": ""
    }},
    {{
      "label": "inline_2",
      "prompt": "Scene relevant to the specific section where this image appears in the post",
      "alt": "Descriptive alt text",
      "caption": ""
    }}
  ],
  "body": [
    {{"type": "paragraph", "text": "Hook opening — answers what this post is about, includes primary keyword, sets up the value of reading on..."}},
    {{"type": "h2", "text": "First major section"}},
    {{"type": "paragraph", "text": "Direct answer sentence. Supporting detail with [external source](https://url.com) citation..."}},
    {{"type": "image", "label": "inline_1"}},
    {{"type": "h2", "text": "Second section"}},
    {{"type": "paragraph", "text": "Content with [internal link text](https://itenx.it.com/blog/relevant-post) woven in..."}},
    {{"type": "h3", "text": "Subsection only if it genuinely adds clarity"}},
    {{"type": "paragraph", "text": "Content..."}},
    {{"type": "image", "label": "inline_2"}},
    {{"type": "h2", "text": "Practical section: framework, comparison, or step-by-step"}},
    {{"type": "paragraph", "text": "Actionable content..."}},
    {{"type": "h2", "text": "Real-world example or case study"}},
    {{"type": "paragraph", "text": "Specific example with named context..."}},
    {{"type": "h2", "text": "Conclusion: [topic] — What to Do Next"}},
    {{"type": "paragraph", "text": "Summary of key takeaways + soft iTenX CTA..."}}
  ]
}}

Write the complete post now. Optimize for humans, Google, and AI tools equally."""


class BlogGenerator:
    def __init__(self):
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in your .env file")
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate(self, row: dict) -> dict:
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": build_user_prompt(row)}
            ]
        )

        raw = message.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                last_brace = raw.rfind('}')
                if last_brace > 0:
                    data = json.loads(raw[:last_brace+1] + ']}')
            except Exception:
                raise ValueError(f"Claude returned invalid JSON. First 300 chars:\n{raw[:300]}")

        for field in ["title", "slug", "body", "image_prompts"]:
            if field not in data:
                raise ValueError(f"Claude response missing field: '{field}'")

        data["slug"] = _clean_slug(data["slug"])
        return data


def _clean_slug(slug: str) -> str:
    slug = slug.lower().strip()
    slug = re.sub(r"[^a-z0-9\-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")
