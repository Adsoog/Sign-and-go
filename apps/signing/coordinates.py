from typing import Tuple


def convert_normalized_to_pdf_box(
    norm_x: float,
    norm_y: float,
    norm_width: float,
    norm_height: float,
    page_width_pts: float,
    page_height_pts: float,
) -> Tuple[float, float, float, float]:
    """
    Converts normalized coordinates (0.0 - 1.0, top-left origin as used by PDF.js)
    into standard PDF MediaBox points (bottom-left origin).
    
    Returns (x1, y1, x2, y2) where:
    x1: left coordinate
    y1: bottom coordinate
    x2: right coordinate
    y2: top coordinate
    """
    # Clamp inputs between 0 and 1
    norm_x = max(0.0, min(1.0, float(norm_x)))
    norm_y = max(0.0, min(1.0, float(norm_y)))
    norm_width = max(0.05, min(1.0 - norm_x, float(norm_width)))
    norm_height = max(0.03, min(1.0 - norm_y, float(norm_height)))

    x1 = norm_x * page_width_pts
    x2 = (norm_x + norm_width) * page_width_pts

    # Invert Y axis: PDF.js y=0 is TOP; PDF point y=0 is BOTTOM
    y2 = page_height_pts - (norm_y * page_height_pts)
    y1 = page_height_pts - ((norm_y + norm_height) * page_height_pts)

    # Ensure y1 < y2
    if y1 > y2:
        y1, y2 = y2, y1

    return (round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2))
