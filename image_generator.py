from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys
import os
import unicodedata


# =========================================================
# INPUT
# =========================================================

headlines_text = sys.argv[1]

raw_headlines = [
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

background = ImageOps.fit(
    background,
    (WIDTH, HEIGHT),
    method=Image.Resampling.LANCZOS,
    centering=(0.5, 0.5)
)

canvas = background.copy()
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
# SAFE UNICODE CLEANING
# =========================================================

def clean_headline(text):

    # Unicode normalization
    text = unicodedata.normalize(
        "NFC",
        text
    )

    cleaned = []

    for char in text:

        code = ord(char)

        # -----------------------------------------
        # Devanagari
        # -----------------------------------------

        if 0x0900 <= code <= 0x097F:
            cleaned.append(char)
            continue

        # -----------------------------------------
        # English A-Z / a-z
        # -----------------------------------------

        if (
            65 <= code <= 90
            or 97 <= code <= 122
        ):
            cleaned.append(char)
            continue

        # -----------------------------------------
        # Numbers
        # -----------------------------------------

        if 48 <= code <= 57:
            cleaned.append(char)
            continue

        # -----------------------------------------
        # Common punctuation
        # -----------------------------------------

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
        ):
            cleaned.append(char)
            continue

        # -----------------------------------------
        # Everything else removed
        # -----------------------------------------

        cleaned.append(" ")

    result = "".join(cleaned)

    # Multiple spaces remove
    result = " ".join(
        result.split()
    )

    return result.strip()


# =========================================================
# CLEAN HEADLINES
# =========================================================

headlines = []

for headline in raw_headlines:

    cleaned = clean_headline(
        headline
    )

    if cleaned:
        headlines.append(cleaned)

headlines = headlines[:10]


# =========================================================
# TITLE
# =========================================================

title_font = get_font(
    HINDI_BOLD,
    30
)

draw.text(
    (70, 268),
    "आज की 10 बड़ी खबरें",
    fill="black",
    font=title_font
)


# =========================================================
# HEADLINE AREA
# =========================================================

NUMBER_X = 52
TEXT_X = 100

MAX_WIDTH = 1030

START_Y = 314

AVAILABLE_HEIGHT = 360

ROW_HEIGHT = (
    AVAILABLE_HEIGHT / 10
)


# =========================================================
# TEXT WIDTH
# =========================================================

def get_text_width(
    text,
    current_font
):

    box = draw.textbbox(
        (0, 0),
        text,
        font=current_font
    )

    return box[2] - box[0]


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

    current = ""

    for word in words:

        test = (
            word
            if not current
            else current + " " + word
        )

        if get_text_width(
            test,
            current_font
        ) <= max_width:

            current = test

        else:

            if current:
                lines.append(
                    current
                )

            current = word

    if current:
        lines.append(
            current
        )

    return lines


# =========================================================
# FIND BEST FONT SIZE
# =========================================================

def fit_headline(text):

    # बड़े से छोटे font तक try करें
    for size in (
        21,
        20,
        19,
        18,
        17,
        16
    ):

        current_font = get_font(
            HINDI_REGULAR,
            size
        )

        lines = wrap_text(
            text,
            current_font,
            MAX_WIDTH
        )

        # Maximum 2 lines
        if len(lines) <= 2:
            return lines, current_font

    # बहुत ज्यादा लंबी headline
    current_font = get_font(
        HINDI_REGULAR,
        16
    )

    lines = wrap_text(
        text,
        current_font,
        MAX_WIDTH
    )

    if len(lines) > 2:

        lines = lines[:2]

        last = lines[1]

        while (
            get_text_width(
                last + "...",
                current_font
            ) > MAX_WIDTH
            and len(last) > 5
        ):

            last = last[:-1]

        lines[1] = (
            last.rstrip()
            + "..."
        )

    return lines, current_font


# =========================================================
# DRAW 10 HEADLINES
# =========================================================

for index, headline in enumerate(
    headlines,
    start=1
):

    # -----------------------------------------
    # Position
    # -----------------------------------------

    y = START_Y + int(
        (index - 1)
        * ROW_HEIGHT
    )

    # -----------------------------------------
    # Number
    # -----------------------------------------

    number_font = get_font(
        ENGLISH_BOLD,
        17
    )

    draw.text(
        (
            NUMBER_X,
            y + 1
        ),
        f"{index}.",
        fill="black",
        font=number_font
    )

    # -----------------------------------------
    # Headline font + wrapping
    # -----------------------------------------

    lines, headline_font = fit_headline(
        headline
    )

    # -----------------------------------------
    # Draw headline
    # -----------------------------------------

    line_y = y

    for line in lines:

        draw.text(
            (
                TEXT_X,
                line_y
            ),
            line,
            fill="black",
            font=headline_font
        )

        line_y += 17

    # -----------------------------------------
    # Divider
    # -----------------------------------------

    divider_y = (
        y
        + int(ROW_HEIGHT)
        - 2
    )

    draw.line(
        [
            (50, divider_y),
            (1150, divider_y)
        ],
        fill="gray",
        width=1
    )


# =========================================================
# FOOTER
# =========================================================

footer_font = get_font(
    ENGLISH_BOLD,
    16
)

draw.text(
    (45, 690),
    "Veena News",
    fill="black",
    font=footer_font
)


# =========================================================
# SAVE
# =========================================================

canvas.save(
    "news_image.jpg",
    quality=95,
    optimize=True
)


# =========================================================
# RESULT
# =========================================================

print(
    "News image created with "
    f"{len(headlines)} headlines."
)
