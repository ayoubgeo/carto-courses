#!/usr/bin/env python3
"""
Token-efficient GeoAI Course Generator
- Calls Claude for JSON content only (not full HTML) -- ~1500 tokens vs 8000
- Injects content into template.html
- Saves final HTML to courses/ folder
- Updates geoaicourses.html with a new card
"""

import os
import re
import json
import datetime
import urllib.request

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
TOPICS_FILE   = "topics.txt"
PROGRESS_FILE = "course_progress.json"
TEMPLATE_FILE = "template.html"
INDEX_FILE    = "geoaicourses.html"
COURSES_DIR   = "courses"


def log(msg):
    print(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}")


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"next_index": 0, "generated": []}


def save_progress(p):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(p, f, indent=2)


def load_topics():
    with open(TOPICS_FILE) as f:
        return [l.strip() for l in f if l.strip() and not l.startswith("#")]


def call_claude(prompt):
    api_key = ANTHROPIC_API_KEY  # variable name kept same, holds Gemini key
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": 4000,
            "temperature": 0.7
        }
    }).encode()
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
            return data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"API error {e.code}: {body}")


def build_prompt(topic, course_number):
    return f"""You are a GeoAI course content writer. Return ONLY valid JSON, no markdown, no explanation.

Generate content for a GeoAI course on: "{topic}"
Course number: {course_number}
Study area: North Morocco (Rif Mountains and Middle Atlas) unless topic requires elsewhere.
Audience: Master students, beginners in GEE and remote sensing.

Return this exact JSON structure:
{{
  "title": "short course title",
  "subtitle": "one sentence description for beginners",
  "duration": "~2 hours",
  "level": "Master - Climate Change and GeoAI",
  "region": "North Morocco",
  "color_theme": "green OR teal OR orange OR purple OR blue",
  "gee_dataset": "exact GEE asset ID",
  "dataset_name": "human readable dataset name",
  "tags": ["tag1", "tag2", "tag3"],
  "key_terms": [
    {{"term": "TERM", "full_name": "Full Name", "definition": "simple beginner explanation"}}
  ],
  "toc": ["Section 1", "Section 2", "Section 3", "Section 4", "Section 5", "Section 6", "Section 7", "Section 8", "Section 9", "Section 10"],
  "intro_paragraph": "2-3 sentence introduction for beginners",
  "deepseek_prompt": "the main DeepSeek prompt with exact dataset IDs, band names, dates, desired outputs",
  "code_block_1": {{
    "label": "label",
    "code": "30-50 lines of working GEE JavaScript",
    "explanation": "beginner explanation of every function used"
  }},
  "code_block_2": {{
    "label": "label",
    "code": "working GEE JavaScript continuation block",
    "explanation": "beginner explanation"
  }},
  "exercises": [
    {{"title": "Exercise A title", "steps": ["step 1", "step 2"]}},
    {{"title": "Exercise B title", "steps": ["step 1", "step 2"]}},
    {{"title": "Exercise C title", "steps": ["step 1", "step 2"]}},
    {{"title": "Exercise D title", "steps": ["step 1", "step 2"]}}
  ],
  "export_code": "Export.image.toDrive GEE code block",
  "card_description": "2 sentence description for the course index card"
}}

Rules: real GEE dataset IDs only, working GEE JavaScript only, at least 12 key_terms, no em dashes.
Return ONLY the JSON."""


THEMES = {
    "green":  {"cls":"forest",       "bg":"linear-gradient(135deg,#052e16,#166534,#15803d)", "cta":"#4ade80", "tag":"background:rgba(34,197,94,0.1);color:#4ade80;border:1px solid rgba(34,197,94,0.2)",  "hbg":"#1B4332","acc":"#52B788","lm":"#B7E4C7"},
    "teal":   {"cls":"flood",        "bg":"linear-gradient(135deg,#0c4a6e,#0891b2,#14b8a6)", "cta":"#2dd4bf", "tag":"background:rgba(20,184,166,0.12);color:#2dd4bf;border:1px solid rgba(20,184,166,0.3)","hbg":"#0F4C5C","acc":"#14b8a6","lm":"#99f6e4"},
    "orange": {"cls":"colab",        "bg":"linear-gradient(135deg,#7c2d12,#9a3412,#c2410c)", "cta":"#f97316", "tag":"background:rgba(249,115,22,0.1);color:#f97316;border:1px solid rgba(249,115,22,0.2)", "hbg":"#7c2d12","acc":"#f97316","lm":"#fed7aa"},
    "purple": {"cls":"geoai",        "bg":"linear-gradient(135deg,#312e81,#4c1d95,#581c87)", "cta":"#8b5cf6", "tag":"background:rgba(139,92,246,0.1);color:#8b5cf6;border:1px solid rgba(139,92,246,0.2)", "hbg":"#312e81","acc":"#8b5cf6","lm":"#ddd6fe"},
    "blue":   {"cls":"randomforest", "bg":"linear-gradient(135deg,#164e63,#0891b2,#06b6d4)", "cta":"#22d3ee", "tag":"background:rgba(6,182,212,0.1);color:#22d3ee;border:1px solid rgba(6,182,212,0.2)",  "hbg":"#164e63","acc":"#06b6d4","lm":"#a5f3fc"},
}


def inject(content, t, course_number):
    with open(TEMPLATE_FILE, encoding="utf-8") as f:
        html = f.read()

    terms_rows = "".join(
        f"<tr><td><strong>{k['term']}</strong></td><td>{k['full_name']}</td><td>{k['definition']}</td></tr>"
        for k in content.get("key_terms", [])
    )
    toc_items = "".join(f"<li>{i}</li>" for i in content.get("toc", []))
    tags_html = "".join(f'<span class="card-tag">{tag}</span>' for tag in content.get("tags", []))
    exercises_html = "".join(
        f'<div class="xr"><h4>{ex["title"]}</h4><ol>{"".join(f"<li>{s}</li>" for s in ex["steps"])}</ol></div>'
        for ex in content.get("exercises", [])
    )

    for k, v in {
        "{{COURSE_NUMBER}}":  str(course_number),
        "{{TITLE}}":          content.get("title", ""),
        "{{SUBTITLE}}":       content.get("subtitle", ""),
        "{{DURATION}}":       content.get("duration", "~2 hours"),
        "{{LEVEL}}":          content.get("level", "Master"),
        "{{REGION}}":         content.get("region", "North Morocco"),
        "{{HEADER_BG}}":      t["hbg"],
        "{{ACCENT}}":         t["acc"],
        "{{LIME}}":           t["lm"],
        "{{GEE_DATASET}}":    content.get("gee_dataset", ""),
        "{{DATASET_NAME}}":   content.get("dataset_name", ""),
        "{{TAGS_HTML}}":      tags_html,
        "{{INTRO}}":          content.get("intro_paragraph", ""),
        "{{KEY_TERMS_ROWS}}": terms_rows,
        "{{TOC_ITEMS}}":      toc_items,
        "{{DEEPSEEK_PROMPT}}":content.get("deepseek_prompt", ""),
        "{{CODE1_LABEL}}":    content.get("code_block_1", {}).get("label", ""),
        "{{CODE1}}":          content.get("code_block_1", {}).get("code", ""),
        "{{CODE1_EXPLAIN}}":  content.get("code_block_1", {}).get("explanation", ""),
        "{{CODE2_LABEL}}":    content.get("code_block_2", {}).get("label", ""),
        "{{CODE2}}":          content.get("code_block_2", {}).get("code", ""),
        "{{CODE2_EXPLAIN}}":  content.get("code_block_2", {}).get("explanation", ""),
        "{{EXERCISES}}":      exercises_html,
        "{{EXPORT_CODE}}":    content.get("export_code", ""),
    }.items():
        html = html.replace(k, v)

    return html


def build_card(content, t, filename, course_number):
    tags_html = "\n".join(
        f'<span class="card-tag" style="{t["tag"]}">{tag}</span>'
        for tag in content.get("tags", [])
    )
    delay = 0.1 + (course_number % 6) * 0.15
    ds = content.get("gee_dataset", "...")[:35]
    title_short = content['title'][:28].lower().replace(' ','-')
    return f"""
            <a href="https://carto.ma/{filename}" class="course-card {t['cls']} animate-in">
                <div class="card-visual">
                    <div class="card-visual-bg"></div>
                    <div class="card-decoration">
                        <div class="dots"><span class="dot"></span><span class="dot"></span><span class="dot"></span></div>
                        <div class="code-line"><span class="comment">// {title_short}</span></div>
                        <div class="code-line"><span class="keyword">var</span> ds = <span class="func">ee.Image</span>(<span class="string">'{ds}'</span>)</div>
                        <div class="code-line"><span class="func">Map.addLayer</span>(ds, vis, <span class="string">'{content['title'][:18]}'</span>)</div>
                        <div class="code-line"><span class="comment">// DeepSeek generated</span></div>
                    </div>
                </div>
                <div class="card-body">
                    <div class="card-tags">{tags_html}</div>
                    <h2 class="card-title">{content['title']}</h2>
                    <p class="card-desc">{content.get('card_description','')}</p>
                    <div class="card-meta">
                        <div class="card-meta-item">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"/></svg>
                            Free Course
                        </div>
                        <div class="card-meta-item">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                            {content.get('duration','~2 hours')}
                        </div>
                        <span class="card-cta" style="color:{t['cta']}">Start Learning
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7"/></svg>
                        </span>
                    </div>
                </div>
            </a>"""


def update_index(card_html):
    if not os.path.exists(INDEX_FILE):
        log(f"WARNING: {INDEX_FILE} not found.")
        return
    with open(INDEX_FILE, encoding="utf-8") as f:
        html = f.read()
    marker = "<!-- Coming soon -->"
    if marker in html:
        html = html.replace(marker, card_html + "\n\n        " + marker)
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(html)
        log("Index updated.")
    else:
        log("WARNING: marker not found in index.")


def main():
    log("=" * 55)
    log("GeoAI Course Generator - template injection mode")

    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not set.")

    progress = load_progress()
    topics = load_topics()

    if progress["next_index"] >= len(topics):
        log("All topics done. Add more to topics.txt.")
        return

    topic = topics[progress["next_index"]]
    course_number = 5 + progress["next_index"]
    log(f"Course {course_number:02d}: {topic}")

    # Call Claude for JSON content only
    log("Calling API...")
    raw = call_claude(build_prompt(topic, course_number))
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"```$", "", raw.strip())
    content = json.loads(raw)
    log(f"Title: {content['title']}")

    # Theme and filename
    t = THEMES.get(content.get("color_theme", "blue"), THEMES["blue"])
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", topic.lower()).strip("_")[:40]
    filename = f"Course{course_number:02d}_{slug}.html"

    # Inject into template and save
    os.makedirs(COURSES_DIR, exist_ok=True)
    html = inject(content, t, course_number)
    out = os.path.join(COURSES_DIR, filename)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    log(f"Saved: {out}")

    # Update index
    update_index(build_card(content, t, filename, course_number))

    # Save progress
    progress["generated"].append({
        "index": progress["next_index"],
        "topic": topic,
        "filename": filename,
        "title": content["title"],
        "date": datetime.datetime.now().isoformat()
    })
    progress["next_index"] += 1
    save_progress(progress)

    nxt = topics[progress["next_index"]] if progress["next_index"] < len(topics) else "END"
    log(f"Next topic: {nxt}")
    log("=" * 55)


if __name__ == "__main__":
    main()
