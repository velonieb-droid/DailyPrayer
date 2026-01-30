import os
import io
import json
import random
import hashlib
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont

# -------------------------------------------------
# CONFIG
# -------------------------------------------------

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")

IMAGE_SIZE = (1080, 1080)
FONT_PATH = "fonts/PlayfairDisplay-Regular.ttf"

HISTORY_FILE = "prayer_history.txt"

# -------------------------------------------------
# PRAYER BUILDING BLOCKS
# -------------------------------------------------

OPENINGS = {
    "morning": [
        "Panginoon, salamat po sa bagong umaga.",
        "Ama naming Diyos, salamat po sa liwanag ng araw."
    ],
    "evening": [
        "Ama naming Diyos, salamat po sa araw na ito.",
        "Panginoon, sa pagtatapos ng araw na ito, kami po ay nagpapasalamat."
    ]
}

PETITIONS = {
    "guidance": [
        "Patnubayan Ninyo ang aking mga hakbang sa buong araw.",
        "Gabayan Ninyo ako sa bawat desisyong aking haharapin."
    ],
    "peace": [
        "Punuin Ninyo ang aking puso ng kapayapaan.",
        "Ibigay Ninyo sa akin ang katahimikan ng loob."
    ],
    "strength": [
        "Bigyan Ninyo ako ng lakas at tibay ng loob.",
        "Palakasin Ninyo ako sa aking mga gawain."
    ],
    "rest": [
        "Sa aking pamamahinga, iniaalay ko sa Inyo ang aking pagod.",
        "Ipinagkakatiwala ko sa Inyo ang lahat ng aking alalahanin."
    ]
}

TRUST_LINES = [
    "Sa Inyo po ako lubos na nagtitiwala.",
    "Ikaw po ang aking sandigan sa lahat ng oras."
]

CLOSINGS = [
    "Amen.",
    "Ito po ang aming panalangin. Amen."
]

# -------------------------------------------------
# VERSE LOADER
# -------------------------------------------------

def load_verse(time_of_day: str) -> dict:
    with open("prayers/verses.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return random.choice(data[time_of_day])


# -------------------------------------------------
# PRAYER GENERATOR
# -------------------------------------------------

def generate_prayer(verse_data: dict, time_of_day: str) -> str:
    lines = []

    lines.append(random.choice(OPENINGS[time_of_day]))

    theme = verse_data.get("theme", "guidance")
    lines.append(random.choice(PETITIONS.get(theme, PETITIONS["guidance"])))

    lines.append(random.choice(TRUST_LINES))
    lines.append(random.choice(CLOSINGS))

    return "\n".join(lines)


# -------------------------------------------------
# NO-REPEAT LOGIC
# -------------------------------------------------

def prayer_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def already_used(prayer_text: str) -> bool:
    if not os.path.exists(HISTORY_FILE):
        return False

    h = prayer_hash(prayer_text)

    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        used = f.read().splitlines()

    return h in used


def save_prayer(prayer_text: str):
    h = prayer_hash(prayer_text)
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(h + "\n")


# -------------------------------------------------
# PEXELS IMAGE FETCH
# -------------------------------------------------

def fetch_image(query: str) -> Image.Image:
    headers = {
        "Authorization": PEXELS_API_KEY
    }

    url = "https://api.pexels.com/v1/search"
    params = {
        "query": query,
        "per_page": 1,
        "orientation": "square"
    }

    r = requests.get(url, headers=headers, params=params, timeout=30)
    r.raise_for_status()

    data = r.json()

    if not data["photos"]:
        raise RuntimeError("No image returned from Pexels.")

    img_url = data["photos"][0]["src"]["large"]

    img_data = requests.get(img_url, timeout=30).content

    return Image.open(io.BytesIO(img_data)).convert("RGB").resize(IMAGE_SIZE)


# -------------------------------------------------
# IMAGE COMPOSER
# -------------------------------------------------

def compose_image(image: Image.Image, verse_text: str, prayer: str) -> str:
    base = image.convert("RGBA")

    overlay = Image.new("RGBA", IMAGE_SIZE, (0, 0, 0, 120))
    base = Image.alpha_composite(base, overlay)

    draw = ImageDraw.Draw(base)

    verse_font = ImageFont.truetype(FONT_PATH, 46)
    prayer_font = ImageFont.truetype(FONT_PATH, 34)

    x = 80
    y = 140

    # --- verse (top)
    draw.text((x, y), verse_text, fill="white", font=verse_font)
    y += 90

    # --- prayer (body)
    for line in prayer.split("\n"):
        draw.text((x, y), line, fill="white", font=prayer_font)
        y += 48

    output_file = "output.png"
    base.convert("RGB").save(output_file, quality=95)

    return output_file


# -------------------------------------------------
# FACEBOOK POST
# -------------------------------------------------

def post_to_facebook(image_path: str, caption: str):

    url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}/photos"

    with open(image_path, "rb") as img:
        r = requests.post(
            url,
            files={"source": img},
            data={
                "caption": caption,
                "access_token": FB_PAGE_TOKEN
            },
            timeout=60
        )

    if r.status_code != 200:
        raise RuntimeError(f"Facebook post failed: {r.text}")


# -------------------------------------------------
# MAIN ORCHESTRATOR
# -------------------------------------------------

def main():

    now = datetime.now()
    time_of_day = "morning" if now.hour < 12 else "evening"

    # 1. Load verse (DATA only, not AI)
    verse_data = load_verse(time_of_day)

    # 2. Generate prayer (with no-repeat protection)
    prayer = None
    for _ in range(12):
        candidate = generate_prayer(verse_data, time_of_day)
        if not already_used(candidate):
            prayer = candidate
            break

    if prayer is None:
        prayer = generate_prayer(verse_data, time_of_day)

    save_prayer(prayer)

    # 3. Caption
    caption = (
        f"{verse_data['text']} ({verse_data['reference']})\n\n"
        f"{prayer}"
    )

    # 4. Image
    query = "sunrise nature peaceful light" if time_of_day == "morning" \
        else "sunset calm night sky peaceful"

    image = fetch_image(query)

    output_file = compose_image(
        image=image,
        verse_text=verse_data["text"],
        prayer=prayer
    )

    # 5. Post
    post_to_facebook(output_file, caption)

    print("Done.")


# -------------------------------------------------

if __name__ == "__main__":
    main()
