"""
QR Code Generator for T-Shirt Distribution System
Reads the Google Sheet, generates a QR code PNG for each participant.
Each QR encodes a short deterministic token derived from their profile URL.
"""

import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from sheets_db import SheetsDB, generate_token
from PIL import Image, ImageDraw, ImageFont


QR_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "qrcodes")


def ensure_dir():
    """Create the output directory if it doesn't exist."""
    os.makedirs(QR_OUTPUT_DIR, exist_ok=True)


def generate_qr_for_person(token_id: str, name: str, tshirt_size: str, email: str):
    """Generate a single QR code PNG with the person's name as a label."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(token_id)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="#1a1a2e", back_color="white").convert("RGB")
    qr_w, qr_h = qr_img.size

    # Create a labeled image with name and size below the QR
    label_height = 80
    final_img = Image.new("RGB", (qr_w, qr_h + label_height), "white")
    final_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(final_img)

    # Use a basic font (works cross-platform)
    try:
        font_name = ImageFont.truetype("arial.ttf", 18)
        font_size_label = ImageFont.truetype("arial.ttf", 22)
    except IOError:
        font_name = ImageFont.load_default()
        font_size_label = font_name

    # Draw name
    name_text = name if len(name) <= 30 else name[:27] + "..."
    name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text(
        ((qr_w - name_w) // 2, qr_h + 8),
        name_text,
        fill="#1a1a2e",
        font=font_name,
    )

    # Draw t-shirt size
    size_text = f"Size: {tshirt_size}"
    size_bbox = draw.textbbox((0, 0), size_text, font=font_size_label)
    size_w = size_bbox[2] - size_bbox[0]
    draw.text(
        ((qr_w - size_w) // 2, qr_h + 38),
        size_text,
        fill="#4285F4",
        font=font_size_label,
    )

    # Save
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in name).strip()
    filename = f"{token_id}_{safe_name}.png"
    filepath = os.path.join(QR_OUTPUT_DIR, filename)
    final_img.save(filepath)
    return filepath


def main():
    """Generate QR codes for all participants in the Google Sheet."""
    ensure_dir()

    print("🔗 Connecting to Google Sheets...")
    db = SheetsDB()
    records = db.get_all_records()

    print(f"📋 Found {len(records)} participants. Generating QR codes...\n")

    generated = 0
    skipped = 0

    for record in records:
        token = record["token_id"]
        name = record["name"]
        size = record["tshirt_size"]
        email = record.get("email", "")

        if not name:
            print(f"  ⚠️  Skipping empty name (token: {token})")
            skipped += 1
            continue

        filepath = generate_qr_for_person(token, name, size, email)
        print(f"  ✅ {name:<30} | Size: {size:<4} | Token: {token} | → {os.path.basename(filepath)}")
        generated += 1

    print(f"\n{'='*60}")
    print(f"✅ Generated: {generated} QR codes")
    print(f"⚠️  Skipped:   {skipped}")
    print(f"📁 Output:    {os.path.abspath(QR_OUTPUT_DIR)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
