---
name: Txt2PDF Prompt Exports
description: Converts structured text files into professional PDFs with headers, footers, clickable URLs, logos, and macOS Finder labels.
---

# Txt2PDF Skill

This skill provides a robust mechanism for converting text prompts or structured documents into formatted PDF files. It includes support for:
-   **Image Headers**: Centered logos (e.g., HubSpot).
-   **Clickable Footers**: Embedded URLs and resources.
-   **Content Cleaning**: Removing unwanted artifacts like long underscore dividers.
-   **Finder Labeling**: Automatically applying color labels (Orange, Green, etc.) to generated files.

## Usage

### Prerequisites
-   Python 3.x
-   `fpdf2` and `Pillow` libraries installed.

### Commands
You can run the core generation script located in `scripts/txt2pdf.py`.

```bash
python3 scripts/txt2pdf.py --input "my_prompts.txt" --prefix "HUBSPOT_" --label "orange"
```

## Structure
-   `scripts/txt2pdf.py`: The core conversion logic.
-   `resources/`: Place your header images (e.g., `hubspot_logo.png`) here.

## Customization
The script can be easily modified to change:
-   Font styles and sizes.
-   Header/Footer content.
-   Label color indices.
