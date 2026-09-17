from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys
import os
import unicodedata
import re


# =========================================================
# INPUT
# =========================================================

if len(sys.argv) < 2:
    raise ValueError("Headlines input नहीं मिला")

headlines_text = sys.argv[1]

headlines = [
    line.strip()
    for line in headlines_text.split("\n")
    if line.strip()
][:10]


# =========================================================
# BACKGROUND
# =========================================================

BACKGROUND = "veena news background.jpg"

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(
        f"Background image not found: {BACKGROUND}"
    )


# =========================================================
# CANVAS
# =========================================================

WIDTH = 1200
HEIGHT = 800

background = Image.open(
    BACKGROUND
).convert("RGB")

background = ImageOps.contain(
    background,
    (WIDTH, HEIGHT),
    method=Image.Resampling.LANCZOS
)

canvas = Image.new(
    "RGB",
    (WIDTH, HEIGHT),
    "white"
)

bg_x = (WIDTH - background.width) // 2
bg_y = (HEIGHT - background.height) // 2

canvas.paste(
    background,
    (bg_x, bg_y)
)

draw = ImageDraw.Draw(canvas)


# =========================================================
# FONT PATHS
# =========================================================

HINDI_FONT_PATH = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Regular.ttf"
)

HINDI_BOLD_PATH = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Bold.ttf"
)

ENGLISH_FONT_PATH = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans.ttf"
)

ENGLISH_BOLD_PATH = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


# =========================================================
# FONT FUNCTION
# =========================================================

def get_font(path, size):
    return ImageFont.truetype(
        path,
        size
    )


# =========================================================
# COLORS
# =========================================================

WHITE = (255, 255, 255)

BLACK = (15, 20, 30)

RED = (218, 20, 28)

BLUE = (10, 48, 125)

LINE_COLOR = (205, 210, 218)


# =========================================================
# CHARACTER CHECK
# =========================================================

def is_hindi(char):

    code = ord(char)

    return (
        0x0900 <= code <= 0x097F
    )


def is_english(char):

    return (
        "A" <= char <= "Z"
        or
        "a" <= char <= "z"
    )


def is_number(char):

    return (
        "0" <= char <= "9"
    )


def is_allowed_punctuation(char):

    return char in (
        " ",
        ".",
        ",",
        "।",
        "!",
        "?",
        ":",
        ";",
        "-",
        "–",
        "—",
        "(",
        ")",
        "/",
        "%",
        "₹",
        "'",
        '"',
        "+",
        "&",
        "@",
        "#",
        "'",
        "*"
    )


# =========================================================
# TEXT CLEANER
# =========================================================

def clean_headline(text):

    text = unicodedata.normalize(
        "NFC",
        text
    )

    cleaned = []

    for char in text:

        if (
            is_hindi(char)
            or
            is_english(char)
            or
            is_number(char)
            or
            is_allowed_punctuation(char)
        ):

            cleaned.append(char)

        else:

            # Unsupported character को हटाएँ
            # ताकि □□□ दिखाई न दें
            cleaned.append(" ")

    result = "".join(cleaned)

    # Multiple spaces हटाएँ
    result = re.sub(
        r"\s+",
        " ",
        result
    )

    return result.strip()


# =========================================================
# CLEAN ALL HEADLINES
# =========================================================

cleaned_headlines = []

for headline in headlines:

    cleaned = clean_headline(
        headline
    )

    if cleaned:
        cleaned_headlines.append(
            cleaned
        )

headlines = cleaned_headlines[:10]


# =========================================================
# MAIN WHITE PANEL
# =========================================================

PANEL_LEFT = 30
PANEL_TOP = 165
PANEL_RIGHT = 1170
PANEL_BOTTOM = 770

draw.rounded_rectangle(
    [
        PANEL_LEFT,
        PANEL_TOP,
        PANEL_RIGHT,
        PANEL_BOTTOM
    ],
    radius=8,
    fill=WHITE
)


# =========================================================
# RED TITLE BANNER
# =========================================================

BANNER_LEFT = 190
BANNER_TOP = 155
BANNER_RIGHT = 1010
BANNER_BOTTOM = 255

draw.rounded_rectangle(
    [
        BANNER_LEFT,
        BANNER_TOP,
        BANNER_RIGHT,
        BANNER_BOTTOM
    ],
    radius=18,
    fill=RED
)


# =========================================================
# LEFT BLUE ACCENT
# =========================================================

draw.polygon(
    [
        (155, 170),
        (178, 170),
        (155, 235),
        (132, 235)
    ],
    fill=BLUE
)

draw.polygon(
    [
        (182, 170),
        (205, 170),
        (182, 235),
        (159, 235)
    ],
    fill=BLUE
)


# =========================================================
# RIGHT BLUE ACCENT
# =========================================================

draw.polygon(
    [
        (1015, 170),
        (1038, 170),
        (1060, 235),
        (1037, 235)
    ],
    fill=BLUE
)

draw.polygon(
    [
        (1042, 170),
        (1065, 170),
        (1087, 235),
        (1064, 235)
    ],
    fill=BLUE
)


# =========================================================
# TITLE
# =========================================================

title_font = get_font(
    HINDI_BOLD_PATH,
    54
)

title = "आज की 10 बड़ी खबरें"

title_box = draw.textbbox(
    (0, 0),
    title,
    font=title_font
)

title_width = (
    title_box[2]
    - title_box[0]
)

title_height = (
    title_box[3]
    - title_box[1]
)

title_x = (
    (BANNER_LEFT + BANNER_RIGHT)
    // 2
    - title_width // 2
)

title_y = (
    (BANNER_TOP + BANNER_BOTTOM)
    // 2
    - title_height // 2
    - 4
)

draw.text(
    (
        title_x,
        title_y
    ),
    title,
    fill=WHITE,
    font=title_font
)


# =========================================================
# HEADLINE AREA
# =========================================================

NUMBER_CENTER_X = 105

TEXT_X = 145

TEXT_RIGHT = 1135

START_Y = 275

END_Y = 680

ROW_HEIGHT = (
    END_Y - START_Y
) / 10


# =========================================================
# FONT SELECTION
# =========================================================

def get_character_font(
    char,
    size
):

    if is_hindi(char):

        return get_font(
            HINDI_FONT_PATH,
            size
        )

    return get_font(
        ENGLISH_FONT_PATH,
        size
    )


# =========================================================
# DRAW MIXED LANGUAGE TEXT
# =========================================================

def draw_mixed_text(
    xy,
    text,
    size,
    fill
):

    x, y = xy

    current_font_type = None

    current_text = ""

    current_x = x

    for char in text:

        if is_hindi(char):

            font_type = "hindi"

        else:

            font_type = "english"

        if (
            current_font_type is not None
            and
            font_type != current_font_type
        ):

            if current_text:

                if current_font_type == "hindi":

                    current_font = get_font(
                        HINDI_FONT_PATH,
                        size
                    )

                else:

                    current_font = get_font(
                        ENGLISH_FONT_PATH,
                        size
                    )

                draw.text(
                    (
                        current_x,
                        y
                    ),
                    current_text,
                    font=current_font,
                    fill=fill
                )

                box = draw.textbbox(
                    (
                        current_x,
                        y
                    ),
                    current_text,
                    font=current_font
                )

                current_x = box[2]

            current_text = ""

        current_text += char

        current_font_type = font_type


    # आखिरी text
    if current_text:

        if current_font_type == "hindi":

            current_font = get_font(
                HINDI_FONT_PATH,
                size
            )

        else:

            current_font = get_font(
                ENGLISH_FONT_PATH,
                size
            )

        draw.text(
            (
                current_x,
                y
            ),
            current_text,
            font=current_font,
            fill=fill
        )


# =========================================================
# MEASURE MIXED TEXT
# =========================================================

def mixed_text_width(
    text,
    size
):

    width = 0

    for char in text:

        if is_hindi(char):

            current_font = get_font(
                HINDI_FONT_PATH,
                size
            )

        else:

            current_font = get_font(
                ENGLISH_FONT_PATH,
                size
            )

        box = draw.textbbox(
            (0, 0),
            char,
            font=current_font
        )

        width += (
            box[2]
            - box[0]
        )

    return width


# =========================================================
# WRAP HEADLINE
# =========================================================

def wrap_headline(
    text,
    size,
    max_width
):

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            word
            if not current_line
            else current_line
            + " "
            + word
        )

        width = mixed_text_width(
            test_line,
            size
        )

        if width <= max_width:

            current_line = test_line

        else:

            if current_line:

                lines.append(
                    current_line
                )

            current_line = word

    if current_line:

        lines.append(
            current_line
        )

    return lines


# =========================================================
# FIT HEADLINE
# =========================================================

def fit_headline(text):

    max_width = (
        TEXT_RIGHT - TEXT_X
    )

    # बड़े से छोटे font तक
    for size in (
        24,
        23,
        22,
        21,
        20,
        19,
        18
    ):

        lines = wrap_headline(
            text,
            size,
            max_width
        )

        if len(lines) <= 1:

            return lines, size

        if len(lines) == 2:

            return lines, size


    # बहुत लंबी headline
    size = 18

    lines = wrap_headline(
        text,
        size,
        max_width
    )

    if len(lines) > 2:

        lines = lines[:2]

        last_line = lines[1]

        while (
            mixed_text_width(
                last_line + "...",
                size
            ) > max_width
            and
            len(last_line) > 5
        ):

            last_line = last_line[:-1]

        lines[1] = (
            last_line.rstrip()
            + "..."
        )

    return lines, size


# =========================================================
# DRAW 10 HEADLINES
# =========================================================

for index, headline in enumerate(
    headlines,
    start=1
):

    y = START_Y + int(
        (index - 1)
        * ROW_HEIGHT
    )


    # =====================================================
    # RED NUMBER CIRCLE
    # =====================================================

    radius = 23

    circle_center_x = NUMBER_CENTER_X

    circle_center_y = (
        y + 20
    )

    draw.ellipse(
        [
            circle_center_x - radius,
            circle_center_y - radius,
            circle_center_x + radius,
            circle_center_y + radius
        ],
        fill=RED
    )


    # =====================================================
    # NUMBER
    # =====================================================

    number_font = get_font(
        ENGLISH_BOLD_PATH,
        23
    )

    number = str(index)

    number_box = draw.textbbox(
        (0, 0),
        number,
        font=number_font
    )

    number_width = (
        number_box[2]
        - number_box[0]
    )

    number_height = (
        number_box[3]
        - number_box[1]
    )

    draw.text(
        (
            circle_center_x
            - number_width // 2,
            circle_center_y
            - number_height // 2
            - 3
        ),
        number,
        fill=WHITE,
        font=number_font
    )


    # =====================================================
    # HEADLINE
    # =====================================================

    lines, font_size = fit_headline(
        headline
    )

    line_y = y - 2

    for line in lines:

        draw_mixed_text(
            (
                TEXT_X,
                line_y
            ),
            line,
            font_size,
            BLACK
        )

        line_y += (
            font_size + 4
        )


    # =====================================================
    # DIVIDER
    # =====================================================

    divider_y = (
        y
        + int(ROW_HEIGHT)
        - 3
    )

    draw.line(
        [
            (145, divider_y),
            (1140, divider_y)
        ],
        fill=LINE_COLOR,
        width=1
    )


# =========================================================
# FOOTER LINE
# =========================================================

draw.line(
    [
        (70, 705),
        (1130, 705)
    ],
    fill=BLUE,
    width=3
)


# =========================================================
# FOOTER
# =========================================================

footer_font = get_font(
    ENGLISH_BOLD_PATH,
    25
)

draw.text(
    (70, 720),
    "Veena News",
    fill=BLUE,
    font=footer_font
)


# =========================================================
# HASHTAGS
# =========================================================

hashtag_font = get_font(
    ENGLISH_BOLD_PATH,
    19
)

hashtags = (
    "#VeenaNews   "
    "#HindiNews   "
    "#News"
)

hashtag_box = draw.textbbox(
    (0, 0),
    hashtags,
    font=hashtag_font
)

hashtag_width = (
    hashtag_box[2]
    - hashtag_box[0]
)

draw.text(
    (
        1130 - hashtag_width,
        725
    ),
    hashtags,
    fill=BLUE,
    font=hashtag_font
)


# =========================================================
# SAVE
# =========================================================

canvas.save(
    "news_image.jpg",
    quality=95,
    optimize=True
)


print(
    "News image created with "
    f"{len(headlines)} headlines."
)
