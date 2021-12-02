from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

TEMPLATE_PATH = "files/base_ticket.png"
FONT_PATH = "files/Roboto-Regular.ttf"
FONT_SIZE = 25

BLACK = (0, 0, 0, 255)
NAME_OFFSET = (200, 270)
EMAIL_OFFSET = (200, 300)

AVATAR_SIZE = 70
AVATAR_OFFSET = (30, 270)


def generate_ticket(name, email):
    base = Image.open(TEMPLATE_PATH).convert("RGBA")
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    draw = ImageDraw.Draw(base)
    draw.text(NAME_OFFSET, name, font=font, fill=BLACK)
    draw.text(EMAIL_OFFSET, email, font=font, fill=BLACK)

    response = requests.get(url=f"https://i.pravatar.cc/{AVATAR_SIZE}?u={email}")
    avatar_file = BytesIO(response.content)
    avatar = Image.open(avatar_file)

    base.paste(avatar, AVATAR_OFFSET)
    temp_file = BytesIO()

    base.save(temp_file, "png")
    temp_file.seek(0)

    return temp_file

generate_ticket("Вася", "art")