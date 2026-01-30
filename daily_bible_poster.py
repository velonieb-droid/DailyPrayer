import os
import json
import io
import random
import datetime
import textwrap
import requests
from PIL import Image, ImageDraw, ImageFont

# -------------------------
# ENV CONFIG
# -------------------------
FB_PAGE_ID = os.getenv("FB_PAGE_ID")
FB_ACCESS_TOKEN = os.getenv("FB_PAGE_ACCESS_TOKEN")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

FONT_PATH = "fonts/Roboto-Bold.ttf"
OUTPUT_IMAGE = "daily_verse.png"

IMAGE_TOPICS = [
    "peaceful nature",
    "mountain sunrise",
    "calm sky",
    "forest light",
    "quiet ocean"
]

# -------------------------
# VERSE ROTATION
# -------------------------
def get_today_reference():
    with open("verses.json", "r") as f:
        verses = json.load(f)

    if not verses:
        raise ValueError("Verse list is empty")

    index = datetime.date.today().toordinal()
    return verses[index % len(verses)]

def get_bible_verse(reference):
    response = requests.get(f"https://bible-api.com/{reference}")
    response.raise_for_status()
    data = response.json()
    return data["text"].strip(), data["reference"]

# -------------------------
# IMAGE HANDLING
# -------------------------
def get_background_image():
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        query = random.choice(IMAGE_TOPICS)

        res = requests.get(
            "https://api.pexels.com/v1/search",
            headers=headers,
            params={"query": query, "per_page": 10}
        )
        res.raise_for_status()

        photo = random.choice(res.json()["photos"])
        img_data = requests.get(photo["src"]["large"]).content
        return Image.open(io.BytesIO(img_data)).convert("RGBA")

    except Exception:
        return Image.open("fallback.jpg").convert("RGBA")

def apply_dark_overlay(img, opacity=120):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, opacity))
    return Image.alpha_composite(img, overlay)

def create_image(verse_text, reference):
    img = get_background_image().resize((1080, 1080))
    img = apply_dark_overlay(img)

    draw = ImageDraw.Draw(img)
    font_verse = ImageFont.truetype(FONT_PATH, 50)
    font_ref = ImageFont.truetype(FONT_PATH, 36)

    margin = 140
    wrapped = textwrap.fill(verse_text, 28)

    verse_box = draw.multiline_textbbox((0, 0), wrapped, font=font_verse, spacing=12)
    ref_box = draw.textbbox((0, 0), reference, font=font_ref)

    total_height = (verse_box[3] - verse_box[1]) + 40 + (ref_box[3] - ref_box[1])
    y = (img.height - total_height) // 2

    # Shadow
    draw.multiline_text(
        (margin + 2, y + 2),
        wrapped,
        font=font_verse,
        fill=(0, 0, 0, 160),
        spacing=12,
        align="center"
    )

    # Main text
    draw.multiline_text(
        (margin, y),
        wrapped,
        font=font_verse,
        fill="white",
        spacing=12,
        align="center"
    )

    y += (verse_box[3] - verse_box[1]) + 40

    draw.text(
        (margin, y),
        f"— {reference}",
        font=font_ref,
        fill=(220, 220, 220)
    )

    img.save(OUTPUT_IMAGE)
    return OUTPUT_IMAGE

# -------------------------
# FACEBOOK POST
# -------------------------
def post_to_facebook(image_path, caption):
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    payload = {
        "caption": caption,
        "access_token": FB_ACCESS_TOKEN
    }

    with open(image_path, "rb") as img:
        files = {"source": img}
        response = requests.post(url, data=payload, files=files)

    print("====== FACEBOOK DEBUG ======")
    print("STATUS CODE:", response.status_code)
    print("RESPONSE TEXT:", response.text)
    print("============================")

# -------------------------
# MAIN
# -------------------------
def main():
    reference = get_today_reference()
    verse, ref = get_bible_verse(reference)

    image = create_image(verse, ref)
    caption = f"{ref}\n\n#DailyBibleVerse #Faith #Hope"
    post_to_facebook(image, caption)

if __name__ == "__main__":
    main()

