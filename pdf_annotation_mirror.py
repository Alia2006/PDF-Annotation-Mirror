import pikepdf
import argparse
import os
import sys
import math
from decimal import Decimal

def flip_annotations(input_pdf, output_pdf, horizontal=True, vertical=False):
    """
    Flip annotations in a PDF file
    
    Parameters:
        input_pdf: Path to the input PDF file
        output_pdf: Path to the output PDF file
        horizontal: Whether to flip horizontally (default: True)
        vertical: Whether to flip vertically (default: False)
    """
    try:
        # Open PDF file
        pdf = pikepdf.open(input_pdf)
        processed = 0
        
        # Iterate through all pages
        for page_num, page in enumerate(pdf.pages):
            # Get page dimensions
            mediabox = page.MediaBox
            width = float(mediabox[2])
            height = float(mediabox[3])
            print(f"Page {page_num+1} dimensions: width {width}, height {height}")
            
            # Check if page has annotations
            if '/Annots' not in page:
                print(f"Page {page_num+1} has no annotations")
                continue
            
            # Get all annotations on the page
            annots = page.Annots
            if annots is None:
                print(f"Page {page_num+1} annotation list is empty")
                continue

            # Iterate through all annotations
            for i, annot_ref in enumerate(annots):
                try:
                    print(f"\nProcessing annotation #{i+1}")
                    
                    # Get annotation type
                    subtype = "Unknown"
                    if '/Subtype' in annot_ref:
                        subtype = str(annot_ref.Subtype)
                        print(f"Annotation type: {subtype}")
                    
                    # Delete AP (appearance stream), to force PDF viewer to re-render the annotation
                    if '/AP' in annot_ref:
                        print("Deleting AP appearance stream, forcing re-rendering")
                        del annot_ref.AP
                    
                    # 1. Rectangle area - almost all annotations have Rect attribute
                    if '/Rect' in annot_ref:
                        rect = annot_ref.Rect
                        x1, y1, x2, y2 = (float(rect[0]), float(rect[1]), 
                                           float(rect[2]), float(rect[3]))
                        
                        print(f"Original rectangle: ({x1}, {y1}, {x2}, {y2})")
                        
                        # Simple coordinate flipping
                        if horizontal:
                            x1, x2 = width - x1, width - x2
                        if vertical:
                            y1, y2 = height - y1, height - y2
                        
                        # Ensure coordinates are in order
                        if x1 > x2:
                            x1, x2 = x2, x1
                        if y1 > y2:
                            y1, y2 = y2, y1
                        
                        print(f"Flipped rectangle: ({x1}, {y1}, {x2}, {y2})")
                        
                        annot_ref.Rect = pikepdf.Array([
                            Decimal(str(x1)), Decimal(str(y1)),
                            Decimal(str(x2)), Decimal(str(y2))
                        ])
                    
                    # 2. Line annotation
                    if subtype == '/Line' and '/L' in annot_ref:
                        points = annot_ref.L
                        x1, y1, x2, y2 = (float(points[0]), float(points[1]),
                                           float(points[2]), float(points[3]))
                        
                        print(f"Original line: from ({x1}, {y1}) to ({x2}, {y2})")
                        
                        # Calculate original line angle and length
                        orig_dx = x2 - x1
                        orig_dy = y2 - y1
                        orig_angle = math.degrees(math.atan2(orig_dy, orig_dx))
                        print(f"Original line angle: {orig_angle:.2f} degrees")
                        
                        # Only flip coordinates, don't swap endpoints
                        if horizontal:
                            x1 = width - x1
                            x2 = width - x2
                        if vertical:
                            y1 = height - y1
                            y2 = height - y2
                        
                        # Calculate angle after flipping
                        new_dx = x2 - x1
                        new_dy = y2 - y1
                        new_angle = math.degrees(math.atan2(new_dy, new_dx))
                        print(f"Angle after coordinate flipping: {new_angle:.2f} degrees")
                        
                        # Check if angle is correctly flipped
                        if horizontal and not vertical:
                            expected_angle = 180 - orig_angle
                        elif vertical and not horizontal:
                            expected_angle = -orig_angle
                        elif horizontal and vertical:
                            expected_angle = 180 + orig_angle
                        else:
                            expected_angle = orig_angle
                        
                        # Normalize angle to [-180, 180] range
                        expected_angle = ((expected_angle + 180) % 360) - 180
                        print(f"Expected flipped angle: {expected_angle:.2f} degrees")
                        
                        # If angle doesn't match expectation, swap endpoints
                        angle_diff = abs((new_angle - expected_angle + 180) % 360 - 180)
                        if angle_diff > 10:  # Allow 10 degree error
                            print("Angle doesn't match expectation, swapping endpoints")
                            x1, x2 = x2, x1
                            y1, y2 = y2, y1
                            
                            # Recheck angle
                            final_dx = x2 - x1
                            final_dy = y2 - y1
                            final_angle = math.degrees(math.atan2(final_dy, final_dx))
                            print(f"Angle after swapping endpoints: {final_angle:.2f} degrees")
                        
                        print(f"Flipped line: from ({x1}, {y1}) to ({x2}, {y2})")
                        
                        # Update line coordinates
                        annot_ref.L = pikepdf.Array([
                            Decimal(str(x1)), Decimal(str(y1)),
                            Decimal(str(x2)), Decimal(str(y2))
                        ])
                        
                        # Handle line ending styles
                        if '/LE' in annot_ref and len(annot_ref.LE) == 2:
                            print("Swapping line ending styles")
                            annot_ref.LE = pikepdf.Array([annot_ref.LE[1], annot_ref.LE[0]])

                    # 3. Polygon/Polyline annotations
                    if subtype in ['/Polygon', '/PolyLine'] and '/Vertices' in annot_ref:
                        vertices = annot_ref.Vertices
                        print("Processing polygon/polyline")
                        
                        # Extract all points
                        original_points = []
                        for j in range(0, len(vertices), 2):
                            if j + 1 < len(vertices):
                                x = float(vertices[j])
                                y = float(vertices[j + 1])
                                original_points.append((x, y))
                        
                        print(f"Original vertex count: {len(original_points)}")
                        
                        # Create a copy for flipping
                        flipped_points = []
                        
                        # Apply coordinate flipping
                        for x, y in original_points:
                            new_x, new_y = x, y
                            if horizontal:
                                new_x = width - x
                            if vertical:
                                new_y = height - y
                            flipped_points.append((new_x, new_y))
                        
                        # Determine if point sequence should be reversed to maintain shape
                        # Single-direction flipping (horizontal or vertical only) needs point reversal
                        if (horizontal != vertical) and len(original_points) > 2:  # Only reverse if more than 2 points
                            print("Single-direction flip, reversing point sequence")
                            flipped_points.reverse()
                        
                        # Output point changes for checking
                        if len(original_points) <= 10:  # Avoid excessive output
                            print("Original point sequence:")
                            for idx, (x, y) in enumerate(original_points):
                                print(f"  Point {idx+1}: ({x:.2f}, {y:.2f})")
                            
                            print("Flipped point sequence:")
                            for idx, (x, y) in enumerate(flipped_points):
                                print(f"  Point {idx+1}: ({x:.2f}, {y:.2f})")
                        
                        # Convert back to array format
                        new_vertices = pikepdf.Array()
                        for x, y in flipped_points:
                            new_vertices.append(Decimal(str(x)))
                            new_vertices.append(Decimal(str(y)))
                        
                        annot_ref.Vertices = new_vertices
                        print("Polygon/polyline flipping completed")
                        
                        # Handle polygon border endpoint styles, if any
                        if '/BE' in annot_ref:
                            print("Note: This polygon has border endpoint styles, may need additional processing")
                    
                    # 4. Highlight/underline annotations
                    if '/QuadPoints' in annot_ref:
                        quad_points = annot_ref.QuadPoints
                        new_quad_points = pikepdf.Array()
                        print("Processing highlight/underline annotations")
                        
                        # Process quadrilateral points
                        for j in range(0, len(quad_points), 8):
                            if j + 7 < len(quad_points):
                                quad = []
                                for k in range(0, 8, 2):
                                    x = float(quad_points[j+k])
                                    y = float(quad_points[j+k+1])
                                    quad.append((x, y))
                                
                                print(f"Original quadrilateral: {quad}")
                                
                                # Apply coordinate flipping
                                flipped_quad = []
                                for x, y in quad:
                                    new_x, new_y = x, y
                                    if horizontal:
                                        new_x = width - x
                                    if vertical:
                                        new_y = height - y
                                    flipped_quad.append((new_x, new_y))
                                
                                # Adjust point order for single-direction flipping
                                if horizontal != vertical:
                                    # Point order is typically: top-left, top-right, bottom-left, bottom-right
                                    # After horizontal flip should be: top-right, top-left, bottom-right, bottom-left
                                    print("Single-direction flip, adjusting quadrilateral point order")
                                    flipped_quad = [flipped_quad[1], flipped_quad[0], 
                                                   flipped_quad[3], flipped_quad[2]]
                                
                                print(f"Flipped quadrilateral: {flipped_quad}")
                                
                                # Add points to new array
                                for x, y in flipped_quad:
                                    new_quad_points.append(Decimal(str(x)))
                                    new_quad_points.append(Decimal(str(y)))
                        
                        annot_ref.QuadPoints = new_quad_points
                        print("Quadrilateral points flipping completed")
                    
                    # 5. Ink annotations
                    if subtype == '/Ink' and '/InkList' in annot_ref:
                        ink_list = annot_ref.InkList
                        new_ink_list = pikepdf.Array()
                        print("Processing ink annotation")
                        
                        for stroke_idx, stroke in enumerate(ink_list):
                            points = []
                            # Extract coordinates
                            for j in range(0, len(stroke), 2):
                                if j + 1 < len(stroke):
                                    x = float(stroke[j])
                                    y = float(stroke[j + 1])
                                    points.append((x, y))
                            
                            print(f"Ink stroke #{stroke_idx+1}, point count: {len(points)}")
                            
                            # Apply coordinate flipping
                            flipped_points = []
                            for x, y in points:
                                new_x, new_y = x, y
                                if horizontal:
                                    new_x = width - x
                                if vertical:
                                    new_y = height - y
                                flipped_points.append((new_x, new_y))
                            
                            # Reverse point sequence for single-direction flip
                            if (horizontal != vertical) and len(points) > 2:
                                print("Single-direction flip, reversing ink point sequence")
                                flipped_points.reverse()
                            
                            # Create new array
                            new_stroke = pikepdf.Array()
                            for x, y in flipped_points:
                                new_stroke.append(Decimal(str(x)))
                                new_stroke.append(Decimal(str(y)))
                            
                            new_ink_list.append(new_stroke)
                        
                        annot_ref.InkList = new_ink_list
                        print("Ink annotation flipping completed")
                    
                    # 6. Special handling for text annotations
                    if subtype in ['/FreeText', '/Text', '/Stamp']:
                        print("Processing text/free text/stamp annotation")
                        
                        # Handle rotation angle
                        if '/Rotate' in annot_ref:
                            old_rotation = int(annot_ref.Rotate)
                            new_rotation = old_rotation
                            
                            if horizontal and not vertical:
                                new_rotation = (360 - old_rotation) % 360
                            elif vertical and not horizontal:
                                new_rotation = (180 - old_rotation) % 360
                            elif horizontal and vertical:
                                new_rotation = (180 + old_rotation) % 360
                            
                            print(f"Rotation angle: {old_rotation}° -> {new_rotation}°")
                            annot_ref.Rotate = new_rotation
                        
                        # Handle text alignment
                        if '/Q' in annot_ref:
                            old_align = int(annot_ref.Q)
                            new_align = old_align
                            
                            # 0=left, 1=center, 2=right
                            if horizontal and old_align in [0, 2]:
                                new_align = 2 if old_align == 0 else 0
                                print(f"Text alignment: {old_align} -> {new_align}")
                                annot_ref.Q = new_align
                    
                    processed += 1
                    
                except Exception as e:
                    print(f"Error processing annotation: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Save the modified PDF
        pdf.save(output_pdf)
        pdf.close()
        print(f"Processed {processed} annotations, saved to {output_pdf}")
        return True
        
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        return False

def update_rect_for_line(annot, x1, y1, x2, y2):
    """Update the rectangle boundary for a line annotation"""
    if '/Rect' in annot:
        # Add some padding
        padding = 1.0
        min_x = min(x1, x2) - padding
        max_x = max(x1, x2) + padding
        min_y = min(y1, y2) - padding
        max_y = max(y1, y2) + padding
        
        annot.Rect = pikepdf.Array([
            Decimal(str(min_x)), Decimal(str(min_y)),
            Decimal(str(max_x)), Decimal(str(max_y))
        ])
        print(f"Updated rectangle boundary: [{min_x}, {min_y}, {max_x}, {max_y}]")

def flip_annotation(annot, width, height, horizontal, vertical):
    """Flip all types of annotations"""
    
    # 1. Rectangle area
    if '/Rect' in annot:
        rect = annot.Rect
        x0, y0, x1, y1 = (float(rect[0]), float(rect[1]), 
                          float(rect[2]), float(rect[3]))
        
        if horizontal:
            x0, x1 = width - x0, width - x1
        if vertical:
            y0, y1 = height - y0, height - y1
        
        # Ensure coordinates are in order
        xmin, xmax = min(x0, x1), max(x0, x1)
        ymin, ymax = min(y0, y1), max(y0, y1)
        
        annot.Rect = pikepdf.Array([
            Decimal(str(xmin)), Decimal(str(ymin)),
            Decimal(str(xmax)), Decimal(str(ymax))
        ])
    
    # 2. Line annotation (handled separately through specialized functions)
    if '/L' in annot and str(annot.Subtype) != '/Line':
        points = annot.L
        x1, y1, x2, y2 = (float(points[0]), float(points[1]),
                           float(points[2]), float(points[3]))
        
        if horizontal:
            x1, x2 = width - x1, width - x2
        if vertical:
            y1, y2 = height - y1, height - y2
        
        annot.L = pikepdf.Array([
            Decimal(str(x1)), Decimal(str(y1)),
            Decimal(str(x2)), Decimal(str(y2))
        ])
    
    # 3. Polygon/Polyline annotation
    if '/Vertices' in annot:
        vertices = annot.Vertices
        
        # Group vertices into (x,y) pairs
        points = []
        for i in range(0, len(vertices), 2):
            if i + 1 < len(vertices):
                x = float(vertices[i])
                y = float(vertices[i + 1])
                points.append((x, y))
        
        # Flip coordinates
        flipped_points = []
        for x, y in points:
            new_x, new_y = x, y
            if horizontal:
                new_x = width - x  # Horizontal flip
            if vertical:
                new_y = height - y  # Vertical flip
            flipped_points.append((new_x, new_y))
        
        # For polygon, point order is important
        # If both horizontal and vertical flip, or no flip, maintain original order
        # If only horizontal or only vertical flip, reverse the point order
        if (horizontal and not vertical) or (vertical and not horizontal):
            flipped_points.reverse()  # Reverse point order
        
        # Convert back to array format
        new_vertices = pikepdf.Array()
        for x, y in flipped_points:
            new_vertices.append(Decimal(str(x)))
            new_vertices.append(Decimal(str(y)))
        
        annot.Vertices = new_vertices
    
    # 4. Highlight/underline/strikethrough annotations
    if '/QuadPoints' in annot:
        quad_points = annot.QuadPoints
        new_quad_points = pikepdf.Array()
        
        # Process every 8 values as a quadrilateral
        for i in range(0, len(quad_points), 8):
            if i + 7 < len(quad_points):
                points = []
                for j in range(0, 8, 2):
                    x = float(quad_points[i+j])
                    y = float(quad_points[i+j+1])
                    points.append((x, y))
                
                # Apply flipping transformation
                flipped_points = []
                for x, y in points:
                    new_x, new_y = x, y
                    if horizontal:
                        new_x = width - x
                    if vertical:
                        new_y = height - y
                    flipped_points.append((new_x, new_y))
                
                # Adjust point order for single-direction flips
                if (horizontal != vertical):
                    # Swap points to maintain proper appearance
                    flipped_points = [flipped_points[1], flipped_points[0], 
                                      flipped_points[3], flipped_points[2]]
                
                # Add to new array
                for x, y in flipped_points:
                    new_quad_points.append(Decimal(str(x)))
                    new_quad_points.append(Decimal(str(y)))
        
        annot.QuadPoints = new_quad_points
    
    # 5. Ink annotations
    if '/InkList' in annot:
        ink_list = annot.InkList
        new_ink_list = pikepdf.Array()
        
        for stroke in ink_list:
            new_stroke = pikepdf.Array()
            
            # Each stroke is a sequence of (x,y) coordinates
            points = []
            for i in range(0, len(stroke), 2):
                if i + 1 < len(stroke):
                    x = float(stroke[i])
                    y = float(stroke[i + 1])
                    points.append((x, y))
            
            # If single-direction flip, reverse point order
            if (horizontal != vertical):
                points.reverse()
            
            # Apply coordinate flipping
            for x, y in points:
                if horizontal:
                    x = width - x
                if vertical:
                    y = height - y
                new_stroke.append(Decimal(str(x)))
                new_stroke.append(Decimal(str(y)))
            
            new_ink_list.append(new_stroke)
        
        annot.InkList = new_ink_list
    
    # 6. Text rotation
    if '/Rotate' in annot:
        rotation = int(annot.Rotate)
        
        if horizontal and not vertical:
            rotation = (360 - rotation) % 360
        elif vertical and not horizontal:
            rotation = (180 - rotation) % 360
        elif horizontal and vertical:
            rotation = (180 + rotation) % 360
        
        annot.Rotate = rotation

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Flip annotations in PDF files")
    parser.add_argument("input_pdf", help="Path to input PDF file")
    parser.add_argument("-o", "--output", help="Path to output PDF file (default: 'flipped_<original_name>.pdf')")
    parser.add_argument("--horizontal", action="store_true", default=True, help="Flip horizontally (default)")
    parser.add_argument("--vertical", action="store_true", help="Flip vertically")
    parser.add_argument("--no-horizontal", dest="horizontal", action="store_false", help="Don't flip horizontally")
    
    args = parser.parse_args()
    
    if not args.output:
        base_name = os.path.basename(args.input_pdf)
        name, ext = os.path.splitext(base_name)
        args.output = f"flipped_{name}{ext}"
    
    try:
        success = flip_annotations(args.input_pdf, args.output, args.horizontal, args.vertical)
        
        if success:
            print(f"Execution successful, results saved to {args.output}")
        else:
            print("Execution failed, please check error messages.")
    except Exception as e:
        import traceback
        print(f"Program execution error: {e}")
        traceback.print_exc()
        sys.exit(1) 