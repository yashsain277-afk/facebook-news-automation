from PIL import Image, ImageDraw, ImageFont, ImageOps
import sys
import os


# ==========================================
# INPUT
# ==========================================

headlines_text = sys.argv[1]

headlines = [
    line.strip()
    for line in headlines_text.split("\n")
    if line.strip()
][:10]


# ==========================================
# BACKGROUND
# ==========================================

BACKGROUND = "veena news background.jpg"

if not os.path.exists(BACKGROUND):
    raise FileNotFoundError(
        f"Background image not found: {BACKGROUND}"
    )


# ==========================================
# CANVAS
# ==========================================

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


# ==========================================
# FONTS
# ==========================================

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


def font(path, size):
    return ImageFont.truetype(
        path,
        size
    )


# ==========================================
# CLEAN HEADLINE
# ==========================================

def clean_headline(text):
    """
    Unsupported / strange Unicode characters
    को हटाता है।

    Hindi, English, numbers और सामान्य
    punctuation को रखा जाता है।
    """

    result = []

    for char in text:

        code = ord(char)

        # Hindi / Devanagari
        if 0x0900 <= code <= 0x097F:
            result.append(char)

        # Devanagari Extended
        elif 0xA8E0 <= code <= 0xA8FF:
            result.append(char)

        # English / numbers / normal ASCII
        elif 0x20 <= code <= 0x7E:
            result.append(char)

        # सामान्य punctuation
        elif char in (
            "।",
            ",",
            "!",
            "?",
            "-",
            "–",
            "—",
            ":",
            ";",
            "%",
            "(",
            ")",
            "/",
            "'",
            '"',
            "₹",
            ".",
        ):
            result.append(char)

        else:
            # Unsupported character हटाएं
            result.append(" ")

    cleaned = "".join(result)

    # Extra spaces हटाएं
    cleaned = " ".join(
        cleaned.split()
    )

    return cleaned.strip()


# ==========================================
# CLEAN ALL HEADLINES
# ==========================================

headlines = [
    clean_headline(headline)
    for headline in headlines
]

# Empty headlines हटाएं
headlines = [
    headline
    for headline in headlines
    if headline
][:10]


# ==========================================
# TITLE
# ==========================================

title_font = font(
    HINDI_BOLD,
    28
)

draw.text(
    (70, 270),
    "आज की 10 बड़ी खबरें",
    fill="black",
    font=title_font
)


# ==========================================
# HEADLINE SETTINGS
# ==========================================

NUMBER_X = 52

TEXT_X = 100

# Number के बाद available width
MAX_WIDTH = 1030

START_Y = 315

# Headlines के लिए कुल height
AVAILABLE_HEIGHT = 355

# 10 headlines
ROW_HEIGHT = AVAILABLE_HEIGHT / 10


# ==========================================
# TEXT WIDTH
# ==========================================

def text_width(
    text,
    current_font
):

    box = draw.textbbox(
        (0, 0),
        text,
        font=current_font
    )

    return box[2] - box[0]


# ==========================================
# WRAP HEADLINE
# ==========================================

def wrap_headline(
    text,
    font_size
):

    current_font = font(
        HINDI_REGULAR,
        font_size
    )

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
        ) <= MAX_WIDTH:

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

    return lines, current_font


# ==========================================
# DRAW HEADLINES
# ==========================================

for index, headline in enumerate(
    headlines,
    start=1
):

    # --------------------------------------
    # Font size automatically select करें
    # --------------------------------------

    lines, headline_font = wrap_headline(
        headline,
        20
    )

    if len(lines) > 2:

        lines, headline_font = wrap_headline(
            headline,
            18
        )

    if len(lines) > 2:

        lines, headline_font = wrap_headline(
            headline,
            16
        )

    # --------------------------------------
    # Maximum 2 lines
    # --------------------------------------

    if len(lines) > 2:

        lines = lines[:2]

        last_line = lines[1]

        # दूसरी line को width के अंदर रखें
        while (
            text_width(
                last_line + "...",
                headline_font
            ) > MAX_WIDTH
            and len(last_line) > 5
        ):

            last_line = last_line[:-1]

        lines[1] = (
            last_line.rstrip()
            + "..."
        )

    # --------------------------------------
    # Row position
    # --------------------------------------

    y = START_Y + int(
        (index - 1)
        * ROW_HEIGHT
    )

    # --------------------------------------
    # Number
    # --------------------------------------

    number_font = font(
        ENGLISH_BOLD,
        17
    )

    draw.text(
        (
            NUMBER_X,
            y
        ),
        f"{index}.",
        fill="black",
        font=number_font
    )

    # --------------------------------------
    # Headline
    # --------------------------------------

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

        line_y += 18

    # --------------------------------------
    # Divider
    # --------------------------------------

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


# ==========================================
# FOOTER
# ==========================================

footer_font = font(
    ENGLISH_BOLD,
    16
)

draw.text(
    (45, 690),
    "Veena News",
    fill="black",
    font=footer_font
)


# ==========================================
# SAVE IMAGE
# ==========================================

canvas.save(
    "news_image.jpg",
    quality=95,
    optimize=True
)


# ==========================================
# RESULT
# ==========================================

print(
    f"News image created with "
    f"{len(headlines)} headlines."
)
