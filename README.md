# PDFlip - PDF Annotation Flipper & Mirroring Tool

A Python tool for flipping PDF annotations horizontally and vertically (mirroring), with precise preservation of position and shape.

## Features

- Flip/mirror PDF annotations horizontally and/or vertically
- Supports multiple annotation types:
  - Lines and arrows (including diagonal line flipping)
  - Polygons and polylines
  - Highlights, underlines, and strikethroughs
  - Ink annotations (freehand drawing)
  - Text annotations
- Preserves annotation properties while flipping:
  - Colors
  - Line styles
  - Line endings
  - Text alignment
  - Rotation

## Installation

### Requirements

- Python 3.6+
- pikepdf library

```bash
pip install pikepdf
```

## Usage

### Basic Usage

```bash
python pdf_annotation_flip.py input.pdf
```

This will create a file named `flipped_input.pdf` with all annotations horizontally flipped.

### Command Line Options

```bash
python pdf_annotation_flip.py input.pdf [options]
```

Options:
- `-o, --output`: Specify output file path (default: `flipped_<input_filename>.pdf`)
- `--horizontal`: Flip horizontally (default: True)
- `--vertical`: Flip vertically (default: False)
- `--no-horizontal`: Disable horizontal flipping

### Examples

Flip vertically only:
```bash
python pdf_annotation_flip.py input.pdf --no-horizontal --vertical
```

Flip both horizontally and vertically:
```bash
python pdf_annotation_flip.py input.pdf --horizontal --vertical
```

Custom output file:
```bash
python pdf_annotation_flip.py input.pdf -o output.pdf
```

## Technical Details

### How Flipping Works

1. **Coordinate Transformation**: The tool applies mathematical transformations to flip annotation coordinates:
   - Horizontal flip: `x → width - x`
   - Vertical flip: `y → height - y`

2. **Point Order Handling**: For multi-point annotations (polygons, polylines, ink), the tool reverses point order to maintain proper visual appearance during flipping.

3. **Line Direction Correction**: For diagonal lines, the tool correctly calculates new angles and may swap endpoints to achieve proper flipping.

4. **Text Handling**: For text annotations, alignment and rotation are adjusted appropriately when flipped.

5. **Appearance Stream Removal**: The tool deletes appearance streams (AP) to force PDF viewers to re-render flipped annotations based on the new coordinates.

### Supported Annotation Types for Flipping

- `/Line`: Lines and arrows (with correct diagonal flipping)
- `/Polygon`: Closed shapes
- `/PolyLine`: Open paths
- `/Square`, `/Circle`: Rectangle and circle shapes
- `/Highlight`, `/Underline`, `/StrikeOut`: Text markup
- `/Ink`: Freehand drawing
- `/FreeText`, `/Text`, `/Stamp`: Text annotations

## Limitations

- Some complex annotations with custom appearances might not flip perfectly
- The tool does not modify the contents of the PDF document itself, only flips the annotations

## Troubleshooting

- If flipped annotations don't appear correctly in the PDF, try opening it in a different PDF viewer
- Some PDF viewers might cache appearances - close and reopen the file to see flipped changes
- If annotations disappear after flipping, make sure the PDF doesn't have restrictions on editing

## License

This software is provided as-is under the MIT License. Feel free to use and modify it as needed.

## Acknowledgments

This PDF flipping tool uses the excellent [pikepdf](https://github.com/pikepdf/pikepdf) library, a Python wrapper around the QPDF library. 