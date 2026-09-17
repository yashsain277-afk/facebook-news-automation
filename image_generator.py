from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys
import os
import unicodedata


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


# Background को पूरा canvas में fit करें
# इससे logo वाला हिस्सा अनावश्यक रूप से crop नहीं होगा।

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
# FONTS
# =========================================================

HINDI_BOLD = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Bold.ttf"
)

HINDI_REGULAR = (
    "/usr/share/fonts/truetype/noto/"
    "NotoSansDevanagari-Regular.ttf"
)

ENGLISH_BOLD = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)


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
# CLEAN TEXT
# =========================================================

def clean_headline(text):

    text = unicodedata.normalize(
        "NFC",
        text
    )

    output = []

    for char in text:

        code = ord(char)

        # Hindi / Devanagari
        if 0x0900 <= code <= 0x097F:
            output.append(char)
            continue

        # English
        if (
            65 <= code <= 90
            or 97 <= code <= 122
        ):
            output.append(char)
            continue

        # Numbers
        if 48 <= code <= 57:
            output.append(char)
            continue

        # Common punctuation
        if char in (
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
            "@"
        ):
            output.append(char)
            continue

        # Unsupported character
        output.append(" ")

    result = "".join(output)

    result = " ".join(
        result.split()
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
# MAIN WHITE NEWS PANEL
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
# BLUE LEFT ACCENT
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
# BLUE RIGHT ACCENT
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
    HINDI_BOLD,
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
# TEXT WIDTH
# =========================================================

def text_width(
    text,
    current_font
):

    box = draw.textbbox(
        (0, 0),
        text,
        font=current_font
    )

    return (
        box[2]
        - box[0]
    )


# =========================================================
# WRAP TEXT
# =========================================================

def wrap_text(
    text,
    current_font,
    max_width
):

    words = text.split()

    lines = []

    current_line = ""

    for word in words:

        test_line = (
            word
            if not current_line
            else current_line + " " + word
        )

        if text_width(
            test_line,
            current_font
        ) <= max_width:

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
# BEST FONT SIZE
# =========================================================

def fit_headline(text):

    max_width = (
        TEXT_RIGHT - TEXT_X
    )

    # बड़ा font पहले
    for size in (
        25,
        24,
        23,
        22,
        21,
        20,
        19
    ):

        current_font = get_font(
            HINDI_REGULAR,
            size
        )

        lines = wrap_text(
            text,
            current_font,
            max_width
        )

        if len(lines) <= 2:
            return lines, current_font


    # बहुत लंबी headline
    current_font = get_font(
        HINDI_REGULAR,
        19
    )

    lines = wrap_text(
        text,
        current_font,
        max_width
    )


    # Maximum 2 lines
    if len(lines) > 2:

        lines = lines[:2]

        last_line = lines[1]

        # दूसरी line को width के अंदर रखें
        while (
            text_width(
                last_line + "...",
                current_font
            ) > max_width
            and len(last_line) > 5
        ):

            last_line = last_line[:-1]

        lines[1] = (
            last_line.rstrip()
            + "..."
        )


    return lines, current_font


# =========================================================
# DRAW HEADLINES
# =========================================================

for index, headline in enumerate(
    headlines,
    start=1
):

    # -----------------------------------------
    # Row position
    # -----------------------------------------

    y = START_Y + int(
        (index - 1)
        * ROW_HEIGHT
    )


    # -----------------------------------------
    # RED NUMBER CIRCLE
    # -----------------------------------------

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


    # -----------------------------------------
    # NUMBER
    # -----------------------------------------

    number_font = get_font(
        ENGLISH_BOLD,
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


    # -----------------------------------------
    # HEADLINE
    # -----------------------------------------

    lines, headline_font = fit_headline(
        headline
    )

    line_y = y - 2

    for line in lines:

        draw.text(
            (
                TEXT_X,
                line_y
            ),
            line,
            fill=BLACK,
            font=headline_font
        )

        line_y += 24


    # -----------------------------------------
    # DIVIDER
    # -----------------------------------------

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
# FOOTER - VEENA NEWS
# =========================================================

footer_font = get_font(
    ENGLISH_BOLD,
    25
)

draw.text(
    (70, 720),
    "Veena News",
    fill=BLUE,
    font=footer_font
)


# =========================================================
# FOOTER HASHTAGS
# =========================================================

hashtag_font = get_font(
    ENGLISH_BOLD,
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
# SAVE IMAGE
# =========================================================

canvas.save(
    "news_image.jpg",
    quality=95,
    optimize=True
)


# =========================================================
# OUTPUT
# =========================================================

print(
    "News image created with "
    f"{len(headlines)} headlines."
)
