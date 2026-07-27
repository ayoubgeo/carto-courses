#!/usr/bin/env python3
"""
Global GeoAI Course Generator
--------------------------------

Generates GeoAI courses using Google Gemini and injects
the generated content into a reusable HTML template.

Supported domains include:

- GeoAI
- Remote Sensing
- GIS
- Climate Change
- Environmental Science
- Urban Science
- Smart Cities
- Agriculture
- Food Security
- Disaster Risk
- Public Health
- Digital Health
- Global Health
- Environmental Health
- Spatial Epidemiology
- Digital Epidemiology
- Health Geography
- Healthcare Accessibility
- One Health
- AI and Machine Learning
- Spatial Data Science

The generator supports:

- Global courses
- Country-level courses
- City-level courses
- Regional courses
- Continent-level courses
- Watershed studies
- Coastal studies
- Mountain studies

The existing course_progress.json is preserved.
Existing courses are NOT regenerated.
The generator continues from next_index.

Requires:
    GEMINI_API_KEY environment variable
"""


import os
import re
import json
import datetime
import urllib.request
import urllib.error


# ============================================================
# CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Current Gemini model
GEMINI_MODEL = "gemini-2.5-flash"

TOPICS_FILE = "topics.txt"
PROGRESS_FILE = "course_progress.json"
TEMPLATE_FILE = "template.html"
INDEX_FILE = "geoaicourses.html"
COURSES_DIR = "courses"


# ============================================================
# DEFAULT COURSE CONFIGURATION
# ============================================================

# These values are used when topics.txt contains only a topic.
# You can change them or use courses_config.json for full control.

DEFAULT_REGION = "Global"

DEFAULT_DOMAIN = "GeoAI"

DEFAULT_METHOD = (
    "Remote Sensing + GIS + Google Earth Engine "
    "+ AI where scientifically appropriate"
)

DEFAULT_DIFFICULTY = "Intermediate"

DEFAULT_AUDIENCE = (
    "Master's students and early-career researchers "
    "in Geography, GIS, Remote Sensing, Environmental "
    "Science, Urban Science, Public Health, Digital Health, "
    "and related fields"
)


# ============================================================
# LOGGING
# ============================================================

def log(msg):

    print(
        f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}",
        flush=True
    )


# ============================================================
# PROGRESS MANAGEMENT
# ============================================================

def load_progress():

    if os.path.exists(PROGRESS_FILE):

        with open(
            PROGRESS_FILE,
            encoding="utf-8"
        ) as f:

            return json.load(f)

    return {
        "next_index": 0,
        "generated": []
    }


def save_progress(progress):

    with open(
        PROGRESS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            progress,
            f,
            indent=2,
            ensure_ascii=False
        )


# ============================================================
# TOPIC LOADING
# ============================================================

def load_topics():

    if not os.path.exists(TOPICS_FILE):

        raise FileNotFoundError(
            f"{TOPICS_FILE} not found."
        )

    with open(
        TOPICS_FILE,
        encoding="utf-8"
    ) as f:

        return [
            line.strip()
            for line in f
            if line.strip()
            and not line.startswith("#")
        ]


# ============================================================
# OPTIONAL COURSE CONFIGURATION
# ============================================================

def load_course_config():

    """
    Optional configuration file.

    If courses_config.json exists, it can contain:

    [
        {
            "topic": "Dengue Risk Mapping",
            "region": "Southeast Asia",
            "domain": "Public Health",
            "method": "Remote Sensing + Climate Data + AI",
            "difficulty": "Advanced",
            "audience": "Master students in Public Health and GeoAI"
        }
    ]

    If the file does not exist, topics.txt is used.
    """

    config_file = "courses_config.json"

    if not os.path.exists(config_file):

        return None

    try:

        with open(
            config_file,
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, list):

            raise ValueError(
                "courses_config.json must contain a JSON list."
            )

        return data

    except Exception as e:

        raise RuntimeError(
            f"Could not load {config_file}: {e}"
        ) from e


# ============================================================
# GET COURSE CONFIGURATION
# ============================================================

def get_course_config(
    index,
    topics
):

    config = load_course_config()

    # --------------------------------------------------------
    # If courses_config.json exists
    # --------------------------------------------------------

    if config is not None:

        if index >= len(config):

            raise IndexError(
                "Course index exceeds courses_config.json."
            )

        item = config[index]

        return {

            "topic": item.get(
                "topic",
                "GeoAI Course"
            ),

            "region": item.get(
                "region",
                DEFAULT_REGION
            ),

            "domain": item.get(
                "domain",
                DEFAULT_DOMAIN
            ),

            "method": item.get(
                "method",
                DEFAULT_METHOD
            ),

            "difficulty": item.get(
                "difficulty",
                DEFAULT_DIFFICULTY
            ),

            "audience": item.get(
                "audience",
                DEFAULT_AUDIENCE
            )
        }

    # --------------------------------------------------------
    # Otherwise use topics.txt
    # --------------------------------------------------------

    if index >= len(topics):

        raise IndexError(
            "Course index exceeds topics.txt."
        )

    return {

        "topic": topics[index],

        "region": DEFAULT_REGION,

        "domain": DEFAULT_DOMAIN,

        "method": DEFAULT_METHOD,

        "difficulty": DEFAULT_DIFFICULTY,

        "audience": DEFAULT_AUDIENCE
    }


# ============================================================
# GEMINI API
# ============================================================

def call_gemini(prompt):

    if not GEMINI_API_KEY:

        raise ValueError(
            "GEMINI_API_KEY environment variable "
            "is not set."
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{GEMINI_MODEL}:generateContent"
        f"?key={GEMINI_API_KEY}"
    )

    payload = {

        "contents": [

            {

                "parts": [

                    {
                        "text": prompt
                    }

                ]

            }

        ],

        "generationConfig": {

            "maxOutputTokens": 8000,

            "temperature": 0.7,

            "responseMimeType": "application/json"

        }

    }

    data = json.dumps(
        payload
    ).encode(
        "utf-8"
    )

    req = urllib.request.Request(

        url,

        data=data,

        method="POST"

    )

    req.add_header(
        "Content-Type",
        "application/json"
    )

    try:

        with urllib.request.urlopen(
            req,
            timeout=180
        ) as resp:

            response_body = (
                resp
                .read()
                .decode("utf-8")
            )

            response_data = json.loads(
                response_body
            )

            candidates = response_data.get(
                "candidates",
                []
            )

            if not candidates:

                raise RuntimeError(
                    "Gemini returned no candidates.\n"
                    f"Response: {response_body}"
                )

            content = candidates[0].get(
                "content",
                {}
            )

            parts = content.get(
                "parts",
                []
            )

            if not parts:

                raise RuntimeError(
                    "Gemini returned no content parts.\n"
                    f"Response: {response_body}"
                )

            text = parts[0].get(
                "text",
                ""
            )

            if not text:

                raise RuntimeError(
                    "Gemini returned empty text."
                )

            return text

    except urllib.error.HTTPError as e:

        body = e.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"Gemini API error {e.code}: {body}"
        ) from e

    except urllib.error.URLError as e:

        raise RuntimeError(
            f"Network error while calling Gemini API: {e}"
        ) from e


# ============================================================
# COURSE PROMPT
# ============================================================

def build_prompt(
    topic,
    course_number,
    region=DEFAULT_REGION,
    domain=DEFAULT_DOMAIN,
    method=DEFAULT_METHOD,
    difficulty=DEFAULT_DIFFICULTY,
    audience=DEFAULT_AUDIENCE
):

    return f"""
You are an expert GeoAI educator, geospatial data scientist,
remote sensing specialist, Google Earth Engine instructor,
and interdisciplinary researcher.

You create high-quality practical courses for a global
GeoAI education platform.

============================================================
COURSE INFORMATION
============================================================

Course number:
{course_number}

Course topic:
{topic}

Geographic study region:
{region}

Primary domain:
{domain}

Preferred methodology:
{method}

Difficulty:
{difficulty}

Target audience:
{audience}

============================================================
GLOBAL COURSE ADAPTATION
============================================================

The course topic and geographic region are variables.

Adapt EVERYTHING to the selected topic and region, including:

- Course title
- Introduction
- Learning objectives
- Dataset selection
- Spatial context
- Temporal period
- Google Earth Engine code
- AI or machine learning methods
- Exercises
- Examples
- DeepSeek prompt
- Export workflow
- Limitations
- Ethical considerations

Do not assume that the course is about Morocco.

Do not automatically use North Morocco.

Do not automatically use the Rif Mountains.

Do not automatically use the Middle Atlas.

If the region is "Global", select datasets and examples
that are appropriate for global-scale analysis.

If the region is a country, select data appropriate for
that country.

If the region is a city, focus on urban-scale analysis.

If the region is a continent, use continent-scale datasets.

If the region is a watershed, use hydrological context.

If the region is coastal, include coastal and marine context
when relevant.

If the region is mountainous, consider elevation,
terrain, climate, and topography when relevant.

============================================================
SUPPORTED GEOAI DOMAINS
============================================================

The platform supports courses in:

- GeoAI
- GIS
- Remote Sensing
- Spatial Data Science
- Artificial Intelligence
- Machine Learning
- Deep Learning
- Climate Change
- Climate Science
- Environmental Science
- Environmental Monitoring
- Disaster Risk Reduction
- Natural Hazards
- Urban Science
- Smart Cities
- Urban Planning
- Agriculture
- Food Security
- Forestry
- Biodiversity
- Ecosystem Monitoring
- Water Resources
- Coastal Management
- Public Health
- Global Health
- Digital Health
- Environmental Health
- Urban Health
- Spatial Epidemiology
- Digital Epidemiology
- Health Geography
- Healthcare Accessibility
- Disease Surveillance
- One Health

Use only the domains relevant to the selected topic.

Do not force unrelated technologies into the course.

============================================================
PUBLIC HEALTH AND DIGITAL HEALTH
============================================================

When the topic relates to public health, global health,
digital health, environmental health, urban health,
spatial epidemiology, or digital epidemiology, adapt
the course accordingly.

Possible applications include:

- Disease mapping
- Spatial epidemiology
- Environmental exposure
- Air pollution and respiratory health
- Heat exposure and health
- Climate-sensitive diseases
- Vector-borne disease risk
- Flooding and health
- Healthcare accessibility
- Healthcare facility mapping
- Population vulnerability
- Urban health surveillance
- Digital epidemiology
- Google Trends health analysis
- Mobility and disease spread
- Remote sensing for public health
- AI-based health risk prediction
- Environmental determinants of health
- One Health

For health-related courses, clearly distinguish between:

- Environmental exposure
- Health outcome
- Risk factor
- Vulnerability
- Population
- Health risk prediction
- Causal inference

Do not claim that satellite data directly measure disease
incidence unless actual validated health data are available.

For example:

Satellite-derived temperature may represent heat exposure.

Satellite-derived air quality may represent environmental
pollution exposure.

Land cover may represent environmental context.

Population density may represent population exposure.

Healthcare facility locations may represent accessibility.

These variables are NOT automatically direct measurements
of disease.

When health outcomes are required, clearly identify whether
the data represent:

- Disease incidence
- Disease prevalence
- Mortality
- Hospital admissions
- Emergency visits
- Syndromic surveillance
- Self-reported symptoms
- Healthcare utilization

If health outcome data are unavailable, focus on:

- Environmental exposure
- Vulnerability
- Health risk proxies
- Population-level indicators

Clearly state this limitation.

============================================================
DIGITAL HEALTH AND DIGITAL EPIDEMIOLOGY
============================================================

Digital health courses may integrate:

- Google Trends
- Search behavior
- Mobility data
- Smartphone data
- Wearable sensor data
- IoT environmental sensors
- Digital health records
- Open health datasets
- Environmental monitoring
- Remote sensing

When using digital health data:

1. Explain spatial resolution.
2. Explain temporal resolution.
3. Explain sampling bias.
4. Explain representativeness.
5. Explain privacy risks.
6. Explain ethical considerations.
7. Distinguish correlation from causation.

If Google Trends is used:

Clearly explain that search interest represents
information-seeking behavior.

Google Trends is NOT equivalent to confirmed disease incidence.

If mobility data are used:

Explain that mobility represents population movement
and should not automatically be interpreted as
individual-level behavior.

If wearable or sensor data are used:

Explain measurement uncertainty, data quality,
privacy, and representativeness.

============================================================
PUBLIC HEALTH GEOAI WORKFLOW
============================================================

When relevant, use this workflow:

1. Define the public health question.
2. Define the population.
3. Define the geographic unit.
4. Identify health outcomes or exposures.
5. Identify environmental determinants.
6. Identify socioeconomic determinants.
7. Acquire geospatial datasets.
8. Harmonize spatial data.
9. Harmonize temporal data.
10. Calculate exposure or risk indicators.
11. Integrate health and environmental data.
12. Perform spatial analysis.
13. Apply AI or machine learning if justified.
14. Validate results.
15. Map and communicate findings.
16. Discuss uncertainty.
17. Discuss limitations.
18. Discuss ethics and privacy.

============================================================
HEALTH DATA SOURCES
============================================================

When health data are required, prefer reputable sources such as:

- WHO
- World Health Organization
- World Bank
- IHME
- Our World in Data
- HDX
- National health ministries
- Public health agencies
- Demographic and Health Surveys
- Open government health portals
- Public epidemiological datasets

Never invent health datasets.

If health data are not available in Google Earth Engine,
separate:

1. GEE environmental analysis.
2. External health data integration.

Explain how external health data can be joined using:

- Coordinates
- Administrative boundaries
- Spatial grids
- Geographic identifiers
- Time periods

============================================================
HEALTH ETHICS AND PRIVACY
============================================================

Health-related courses must consider:

- Privacy
- Data protection
- Geographic re-identification
- Sensitive health information
- Individual-level versus population-level data
- Algorithmic bias
- Fairness
- Data representativeness
- Responsible AI
- Informed consent where applicable

Do not use personally identifiable health information.

Do not generate maps that expose individual-level
sensitive health information.

Prefer aggregated results using:

- Administrative regions
- Census areas
- Health districts
- Regular spatial grids

============================================================
DATASET REQUIREMENTS
============================================================

Use real, publicly available Google Earth Engine datasets.

The dataset must:

1. Exist in the Google Earth Engine Data Catalog.
2. Use the correct dataset ID.
3. Use valid band names.
4. Match the selected topic.
5. Match the selected region.
6. Have appropriate temporal coverage.
7. Be appropriate for the requested spatial scale.

Possible datasets include:

- Sentinel-1
- Sentinel-2
- Landsat
- MODIS
- VIIRS
- ERA5
- CHIRPS
- Dynamic World
- WorldCover
- SRTM
- ALOS
- GEDI
- GHSL
- Sentinel-5P
- Other verified GEE datasets

Never invent dataset IDs.

Never invent band names.

If multiple datasets are required,
include all relevant datasets.

============================================================
GEOAI AND MACHINE LEARNING
============================================================

Use AI or machine learning only when scientifically justified.

Possible methods include:

- Random Forest
- Gradient Boosting
- Classification
- Regression
- Clustering
- Change Detection
- Deep Learning
- Spatial Prediction
- Time-Series Analysis
- Anomaly Detection

For machine learning workflows, clearly identify:

- Target variable
- Predictor variables
- Training data
- Validation data
- Sampling strategy
- Spatial resolution
- Temporal resolution
- Evaluation metrics

For health prediction models, discuss:

- Spatial autocorrelation
- Temporal leakage
- Sampling bias
- Confounding
- Model uncertainty
- Generalizability
- External validation

Do not claim that a model diagnoses individuals unless
the course specifically concerns validated clinical
diagnostic applications and suitable clinical data exist.

============================================================
GEE CODE REQUIREMENTS
============================================================

All Google Earth Engine JavaScript must be:

- Valid GEE Code Editor JavaScript.
- Executable with minimal modification.
- Based on real GEE datasets.
- Based on valid band names.
- Appropriate for the selected region.
- Appropriate for the selected topic.

Include when relevant:

1. Study area definition.
2. Dataset loading.
3. Date filtering.
4. Cloud filtering.
5. Quality filtering.
6. Preprocessing.
7. Feature extraction.
8. Spectral indices.
9. Environmental indicators.
10. Visualization.
11. Spatial analysis.
12. Machine learning when appropriate.
13. Validation.
14. Export.

Do not generate fake GEE functions.

Do not invent asset IDs.

Avoid requiring users to upload custom assets.

If a custom boundary is necessary,
clearly identify it as a placeholder.

============================================================
DEEPSEEK PROMPT
============================================================

Create a detailed prompt students can use with DeepSeek
or another AI coding assistant.

The prompt must include:

- Exact GEE dataset IDs.
- Exact band names.
- Study region.
- Dates.
- Analysis method.
- Expected outputs.
- Visualization requirements.
- Export requirements.

The prompt must instruct the AI assistant to:

- Generate valid GEE JavaScript.
- Use only real GEE datasets.
- Use valid band names.
- Avoid inventing functions.
- Explain every major processing step.
- Explain limitations.

============================================================
COURSE STRUCTURE
============================================================

Create a coherent learning progression.

Possible structure:

1. Introduction to the problem.
2. GeoAI concepts.
3. Data discovery.
4. Study area definition.
5. Data preprocessing.
6. Feature extraction.
7. Spatial analysis.
8. AI or machine learning.
9. Visualization.
10. Interpretation.
11. Practical exercises.
12. Export and reproducibility.

Adapt the structure when necessary.

============================================================
OUTPUT FORMAT
============================================================

Return ONLY valid JSON.

Do not use Markdown.

Do not use ```json.

Do not include explanations outside the JSON.

Return exactly this structure:

{{
  "title": "short professional course title",

  "subtitle":
    "one sentence description for beginners",

  "duration":
    "~2 hours",

  "level":
    "{difficulty}",

  "region":
    "{region}",

  "domain":
    "{domain}",

  "method":
    "{method}",

  "color_theme":
    "green OR teal OR orange OR purple OR blue",

  "gee_dataset":
    "primary exact GEE dataset ID",

  "dataset_name":
    "human readable primary dataset name",

  "additional_datasets": [
    {{
      "dataset_id":
        "exact GEE dataset ID",

      "name":
        "dataset name",

      "purpose":
        "why this dataset is used"
    }}
  ],

  "tags": [
    "tag1",
    "tag2",
    "tag3"
  ],

  "key_terms": [
    {{
      "term":
        "TERM",

      "full_name":
        "Full Name",

      "definition":
        "simple beginner explanation"
    }}
  ],

  "toc": [
    "Section 1",
    "Section 2",
    "Section 3",
    "Section 4",
    "Section 5",
    "Section 6",
    "Section 7",
    "Section 8",
    "Section 9",
    "Section 10"
  ],

  "intro_paragraph":
    "2-3 sentence introduction explaining the real-world problem, geographic context, and GeoAI approach",

  "learning_objectives": [
    "Learning objective 1",
    "Learning objective 2",
    "Learning objective 3",
    "Learning objective 4",
    "Learning objective 5"
  ],

  "deepseek_prompt":
    "detailed prompt for generating or improving GEE code for this exact course",

  "code_block_1": {{
    "label":
      "Initial data preparation and visualization",

    "code":
      "30-50 lines of working GEE JavaScript",

    "explanation":
      "beginner-friendly explanation of every important function and processing step"
  }},

  "code_block_2": {{
    "label":
      "Advanced analysis or GeoAI workflow",

    "code":
      "working GEE JavaScript continuation block",

    "explanation":
      "beginner-friendly explanation of the analysis or workflow"
  }},

  "exercises": [
    {{
      "title":
        "Exercise A title",

      "steps": [
        "step 1",
        "step 2",
        "step 3"
      ]
    }},

    {{
      "title":
        "Exercise B title",

      "steps": [
        "step 1",
        "step 2",
        "step 3"
      ]
    }},

    {{
      "title":
        "Exercise C title",

      "steps": [
        "step 1",
        "step 2",
        "step 3"
      ]
    }},

    {{
      "title":
        "Exercise D title",

      "steps": [
        "step 1",
        "step 2",
        "step 3"
      ]
    }}
  ],

  "export_code":
    "working GEE Export.image.toDrive or appropriate export code",

  "card_description":
    "2 sentence description for the course index card"
}}

============================================================
FINAL QUALITY RULES
============================================================

1. Return ONLY valid JSON.
2. Do not use Markdown.
3. Do not use em dashes.
4. Include at least 12 key_terms.
5. Use real GEE dataset IDs only.
6. Use valid GEE band names only.
7. Use working GEE JavaScript.
8. Adapt everything to the selected topic.
9. Adapt everything to the selected region.
10. Do not assume the study area is Morocco.
11. Do not assume the study area is North Africa.
12. Do not invent datasets.
13. Do not invent bands.
14. Do not invent GEE functions.
15. Make the course scientifically accurate.
16. Make the course practical.
17. Make the course reproducible.
18. Use AI only when scientifically justified.
19. Make the content appropriate for the selected difficulty.
20. Ensure code and explanations match the selected topic.
21. Ensure all dates match the datasets.
22. Ensure the spatial scale is computationally realistic.
23. Clearly distinguish correlation from causation in health courses.
24. Clearly explain limitations in health-related analysis.
25. Include privacy and ethical considerations when health data are used.
26. Ensure all generated content is internally consistent.
"""
    

# ============================================================
# COLOR THEMES
# ============================================================

THEMES = {

    "green": {
        "cls": "forest",
        "bg": "linear-gradient(135deg,#052e16,#166534,#15803d)",
        "cta": "#4ade80",
        "tag": (
            "background:rgba(34,197,94,0.1);"
            "color:#4ade80;"
            "border:1px solid rgba(34,197,94,0.2)"
        ),
        "hbg": "#1B4332",
        "acc": "#52B788",
        "lm": "#B7E4C7"
    },

    "teal": {
        "cls": "flood",
        "bg": "linear-gradient(135deg,#0c4a6e,#0891b2,#14b8a6)",
        "cta": "#2dd4bf",
        "tag": (
            "background:rgba(20,184,166,0.12);"
            "color:#2dd4bf;"
            "border:1px solid rgba(20,184,166,0.3)"
        ),
        "hbg": "#0F4C5C",
        "acc": "#14b8a6",
        "lm": "#99f6e4"
    },

    "orange": {
        "cls": "colab",
        "bg": "linear-gradient(135deg,#7c2d12,#9a3412,#c2410c)",
        "cta": "#f97316",
        "tag": (
            "background:rgba(249,115,22,0.1);"
            "color:#f97316;"
            "border:1px solid rgba(249,115,22,0.2)"
        ),
        "hbg": "#7c2d12",
        "acc": "#f97316",
        "lm": "#fed7aa"
    },

    "purple": {
        "cls": "geoai",
        "bg": "linear-gradient(135deg,#312e81,#4c1d95,#581c87)",
        "cta": "#8b5cf6",
        "tag": (
            "background:rgba(139,92,246,0.1);"
            "color:#8b5cf6;"
            "border:1px solid rgba(139,92,246,0.2)"
        ),
        "hbg": "#312e81",
        "acc": "#8b5cf6",
        "lm": "#ddd6fe"
    },

    "blue": {
        "cls": "randomforest",
        "bg": "linear-gradient(135deg,#164e63,#0891b2,#06b6d4)",
        "cta": "#22d3ee",
        "tag": (
            "background:rgba(6,182,212,0.1);"
            "color:#22d3ee;"
            "border:1px solid rgba(6,182,212,0.2)"
        ),
        "hbg": "#164e63",
        "acc": "#06b6d4",
        "lm": "#a5f3fc"
    }
}


# ============================================================
# HTML INJECTION
# ============================================================

def inject(
    content,
    theme,
    course_number
):

    with open(
        TEMPLATE_FILE,
        encoding="utf-8"
    ) as f:

        html = f.read()

    # --------------------------------------------------------
    # Key terms
    # --------------------------------------------------------

    terms_rows = "".join(

        (
            f"<tr>"
            f"<td><strong>{k.get('term', '')}</strong></td>"
            f"<td>{k.get('full_name', '')}</td>"
            f"<td>{k.get('definition', '')}</td>"
            f"</tr>"
        )

        for k in content.get(
            "key_terms",
            []
        )
    )

    # --------------------------------------------------------
    # Table of contents
    # --------------------------------------------------------

    toc_items = "".join(

        f"<li>{item}</li>"

        for item in content.get(
            "toc",
            []
        )
    )

    # --------------------------------------------------------
    # Tags
    # --------------------------------------------------------

    tags_html = "".join(

        f'<span class="card-tag">{tag}</span>'

        for tag in content.get(
            "tags",
            []
        )
    )

    # --------------------------------------------------------
    # Exercises
    # --------------------------------------------------------

    exercises_html = ""

    for exercise in content.get(
        "exercises",
        []
    ):

        steps_html = "".join(

            f"<li>{step}</li>"

            for step in exercise.get(
                "steps",
                []
            )
        )

        exercises_html += (

            f'<div class="xr">'

            f'<h4>'
            f'{exercise.get("title", "")}'
            f'</h4>'

            f'<ol>'
            f'{steps_html}'
            f'</ol>'

            f'</div>'

        )

    # --------------------------------------------------------
    # Additional datasets
    # --------------------------------------------------------

    additional_datasets = content.get(
        "additional_datasets",
        []
    )

    additional_dataset_text = "\n".join(

        f"{d.get('dataset_id', '')} - "
        f"{d.get('name', '')}: "
        f"{d.get('purpose', '')}"

        for d in additional_datasets
    )

    # --------------------------------------------------------
    # Replacements
    # --------------------------------------------------------

    replacements = {

        "{{COURSE_NUMBER}}":
            str(course_number),

        "{{TITLE}}":
            content.get(
                "title",
                ""
            ),

        "{{SUBTITLE}}":
            content.get(
                "subtitle",
                ""
            ),

        "{{DURATION}}":
            content.get(
                "duration",
                "~2 hours"
            ),

        "{{LEVEL}}":
            content.get(
                "level",
                "Master"
            ),

        "{{REGION}}":
            content.get(
                "region",
                "Global"
            ),

        "{{HEADER_BG}}":
            theme["hbg"],

        "{{ACCENT}}":
            theme["acc"],

        "{{LIME}}":
            theme["lm"],

        "{{GEE_DATASET}}":
            content.get(
                "gee_dataset",
                ""
            ),

        "{{DATASET_NAME}}":
            content.get(
                "dataset_name",
                ""
            ),

        "{{TAGS_HTML}}":
            tags_html,

        "{{INTRO}}":
            content.get(
                "intro_paragraph",
                ""
            ),

        "{{KEY_TERMS_ROWS}}":
            terms_rows,

        "{{TOC_ITEMS}}":
            toc_items,

        "{{DEEPSEEK_PROMPT}}":
            content.get(
                "deepseek_prompt",
                ""
            ),

        "{{CODE1_LABEL}}":
            content.get(
                "code_block_1",
                {}
            ).get(
                "label",
                ""
            ),

        "{{CODE1}}":
            content.get(
                "code_block_1",
                {}
            ).get(
                "code",
                ""
            ),

        "{{CODE1_EXPLAIN}}":
            content.get(
                "code_block_1",
                {}
            ).get(
                "explanation",
                ""
            ),

        "{{CODE2_LABEL}}":
            content.get(
                "code_block_2",
                {}
            ).get(
                "label",
                ""
            ),

        "{{CODE2}}":
            content.get(
                "code_block_2",
                {}
            ).get(
                "code",
                ""
            ),

        "{{CODE2_EXPLAIN}}":
            content.get(
                "code_block_2",
                {}
            ).get(
                "explanation",
                ""
            ),

        "{{EXERCISES}}":
            exercises_html,

        "{{EXPORT_CODE}}":
            content.get(
                "export_code",
                ""
            ),

        "{{ADDITIONAL_DATASETS}}":
            additional_dataset_text

    }

    # --------------------------------------------------------
    # Replace placeholders
    # --------------------------------------------------------

    for placeholder, value in replacements.items():

        html = html.replace(
            placeholder,
            str(value)
        )

    return html


# ============================================================
# BUILD INDEX CARD
# ============================================================

def build_card(
    content,
    theme,
    filename,
    course_number
):

    tags_html = "\n".join(

        (
            f'<span class="card-tag" '
            f'style="{theme["tag"]}">'
            f'{tag}'
            f'</span>'
        )

        for tag in content.get(
            "tags",
            []
        )
    )

    title = content.get(
        "title",
        "GeoAI Course"
    )

    delay = (

        0.1
        + (
            course_number % 6
        ) * 0.15

    )

    dataset = content.get(
        "gee_dataset",
        "..."
    )[:35]

    title_short = (

        title[:28]
        .lower()
        .replace(
            " ",
            "-"
        )

    )

    return f"""
            <a href="https://carto.ma/{filename}"
               class="course-card {theme['cls']} animate-in"
               style="animation-delay:{delay}s">

                <div class="card-visual">

                    <div class="card-visual-bg"></div>

                    <div class="card-decoration">

                        <div class="dots">
                            <span class="dot"></span>
                            <span class="dot"></span>
                            <span class="dot"></span>
                        </div>

                        <div class="code-line">
                            <span class="comment">
                                // {title_short}
                            </span>
                        </div>

                        <div class="code-line">
                            <span class="keyword">var</span>
                            ds =
                            <span class="func">
                                ee.Image
                            </span>(
                            <span class="string">
                                '{dataset}'
                            </span>)
                        </div>

                        <div class="code-line">
                            <span class="func">
                                Map.addLayer
                            </span>(
                            ds,
                            vis,
                            <span class="string">
                                '{title[:18]}'
                            </span>)
                        </div>

                        <div class="code-line">
                            <span class="comment">
                                // AI-assisted GeoAI course
                            </span>
                        </div>

                    </div>

                </div>

                <div class="card-body">

                    <div class="card-tags">
                        {tags_html}
                    </div>

                    <h2 class="card-title">
                        {title}
                    </h2>

                    <p class="card-desc">
                        {content.get(
                            "card_description",
                            ""
                        )}
                    </p>

                    <div class="card-meta">

                        <div class="card-meta-item">

                            <svg xmlns="http://www.w3.org/2000/svg"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                                 stroke-width="2">

                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M12 6.253v13m0-13C10.832 5.477 9.246 5
                                    7.5 5S4.168 5.477 3 6.253v13C4.168
                                    18.477 5.754 18 7.5 18s3.332
                                    .477 4.5 1.253m0-13C13.168
                                    5.477 14.754 5 16.5 5c1.747
                                    0 3.332.477 4.5 1.253v13C19.832
                                    18.477 18.247 18 16.5 18c-1.746
                                    0-3.332.477-4.5 1.253"
                                />

                            </svg>

                            Free Course

                        </div>

                        <div class="card-meta-item">

                            <svg xmlns="http://www.w3.org/2000/svg"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                                 stroke-width="2">

                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M12 8v4l3 3m6-3a9 9
                                    0 11-18 0 9 9 0 0118 0z"
                                />

                            </svg>

                            {content.get(
                                "duration",
                                "~2 hours"
                            )}

                        </div>

                        <span class="card-cta"
                              style="color:{theme['cta']}">

                            Start Learning

                            <svg xmlns="http://www.w3.org/2000/svg"
                                 width="16"
                                 height="16"
                                 fill="none"
                                 viewBox="0 0 24 24"
                                 stroke="currentColor"
                                 stroke-width="2">

                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    d="M9 5l7 7-7 7"
                                />

                            </svg>

                        </span>

                    </div>

                </div>

            </a>
"""


# ============================================================
# UPDATE INDEX
# ============================================================

def update_index(card_html):

    if not os.path.exists(
        INDEX_FILE
    ):

        log(
            f"WARNING: {INDEX_FILE} not found."
        )

        return

    with open(
        INDEX_FILE,
        encoding="utf-8"
    ) as f:

        html = f.read()

    marker = "<!-- Coming soon -->"

    if marker in html:

        html = html.replace(

            marker,

            card_html
            + "\n\n        "
            + marker,

            1

        )

        with open(
            INDEX_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(html)

        log(
            "Index updated."
        )

    else:

        log(
            "WARNING: "
            "marker not found in index."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    log(
        "=" * 60
    )

    log(
        "Global GeoAI Course Generator"
    )

    log(
        f"Gemini model: {GEMINI_MODEL}"
    )

    log(
        "Global topic + region + domain adaptation enabled"
    )

    # --------------------------------------------------------
    # API key
    # --------------------------------------------------------

    if not GEMINI_API_KEY:

        raise ValueError(
            "GEMINI_API_KEY is not set."
        )

    # --------------------------------------------------------
    # Load progress
    # --------------------------------------------------------

    progress = load_progress()

    # --------------------------------------------------------
    # Load topics
    # --------------------------------------------------------

    topics = load_topics()

    # --------------------------------------------------------
    # Current index
    # --------------------------------------------------------

    current_index = progress.get(
        "next_index",
        0
    )

    # --------------------------------------------------------
    # Check available topics
    # --------------------------------------------------------

    if current_index >= len(topics):

        log(
            "All topics in topics.txt are complete."
        )

        log(
            "Add more topics to continue."
        )

        return

    # --------------------------------------------------------
    # Get course configuration
    # --------------------------------------------------------

    course_config = get_course_config(
        current_index,
        topics
    )

    topic = course_config[
        "topic"
    ]

    region = course_config[
        "region"
    ]

    domain = course_config[
        "domain"
    ]

    method = course_config[
        "method"
    ]

    difficulty = course_config[
        "difficulty"
    ]

    audience = course_config[
        "audience"
    ]

    # --------------------------------------------------------
    # Course number
    #
    # Your existing progress starts at index 0 = Course 05.
    # Therefore:
    #
    # course_number = 5 + index
    #
    # With next_index = 18:
    # Course 23
    # --------------------------------------------------------

    course_number = (
        5
        + current_index
    )

    log(
        f"Course {course_number:02d}"
    )

    log(
        f"Topic: {topic}"
    )

    log(
        f"Region: {region}"
    )

    log(
        f"Domain: {domain}"
    )

    log(
        f"Method: {method}"
    )

    log(
        f"Difficulty: {difficulty}"
    )

    # --------------------------------------------------------
    # Build prompt
    # --------------------------------------------------------

    prompt = build_prompt(

        topic=topic,

        course_number=course_number,

        region=region,

        domain=domain,

        method=method,

        difficulty=difficulty,

        audience=audience

    )

    # --------------------------------------------------------
    # Call Gemini
    # --------------------------------------------------------

    log(
        "Calling Gemini API..."
    )

    raw = call_gemini(
        prompt
    )

    # --------------------------------------------------------
    # Clean response
    # --------------------------------------------------------

    raw = raw.strip()

    raw = re.sub(
        r"^```json\s*",
        "",
        raw,
        flags=re.IGNORECASE
    )

    raw = re.sub(
        r"^```\s*",
        "",
        raw
    )

    raw = re.sub(
        r"\s*```$",
        "",
        raw
    )

    raw = raw.strip()

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        content = json.loads(
            raw
        )

    except json.JSONDecodeError as e:

        log(
            "ERROR: Gemini returned invalid JSON."
        )

        log(
            f"JSON error: {e}"
        )

        log(
            "Raw response:"
        )

        print(
            raw
        )

        raise RuntimeError(
            "Gemini returned invalid JSON."
        ) from e

    # --------------------------------------------------------
    # Validate content
    # --------------------------------------------------------

    if not content.get(
        "title"
    ):

        raise RuntimeError(
            "Generated content has no title."
        )

    log(
        f"Generated title: "
        f"{content['title']}"
    )

    # --------------------------------------------------------
    # Theme
    # --------------------------------------------------------

    theme = THEMES.get(

        content.get(
            "color_theme",
            "blue"
        ),

        THEMES["blue"]

    )

    # --------------------------------------------------------
    # Filename
    # --------------------------------------------------------

    slug = re.sub(

        r"[^a-zA-Z0-9]+",

        "_",

        topic.lower()

    ).strip(
        "_"
    )[:40]

    filename = (

        f"Course{course_number:02d}_"
        f"{slug}.html"

    )

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    os.makedirs(

        COURSES_DIR,

        exist_ok=True

    )

    # --------------------------------------------------------
    # Inject into HTML template
    # --------------------------------------------------------

    html = inject(

        content,

        theme,

        course_number

    )

    # --------------------------------------------------------
    # Save course
    # --------------------------------------------------------

    output_file = os.path.join(

        COURSES_DIR,

        filename

    )

    with open(

        output_file,

        "w",

        encoding="utf-8"

    ) as f:

        f.write(
            html
        )

    log(
        f"Saved: {output_file}"
    )

    # --------------------------------------------------------
    # Update course index
    # --------------------------------------------------------

    card_html = build_card(

        content,

        theme,

        filename,

        course_number

    )

    update_index(
        card_html
    )

    # --------------------------------------------------------
    # Save progress
    # --------------------------------------------------------

    progress.setdefault(
        "generated",
        []
    )

    progress[
        "generated"
    ].append(

        {

            "index":
                current_index,

            "topic":
                topic,

            "filename":
                filename,

            "title":
                content[
                    "title"
                ],

            "date":
                datetime.datetime.now()
                .isoformat(),

            "region":
                region,

            "domain":
                domain

        }

    )

    progress[
        "next_index"
    ] = (

        current_index
        + 1

    )

    save_progress(
        progress
    )

    # --------------------------------------------------------
    # Next topic
    # --------------------------------------------------------

    next_index = progress[
        "next_index"
    ]

    if next_index < len(
        topics
    ):

        next_topic = topics[
            next_index
        ]

    else:

        next_topic = "END"

    log(
        f"Next topic: {next_topic}"
    )

    log(
        "=" * 60
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
