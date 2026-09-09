import fitz  # PyMuPDF
import json
import os
import re
import time
from collections import Counter
import pandas as pd
import joblib

def detect_headers_and_footers(doc, line_threshold=0.4):
    """
    Detects repeating text that is likely a header or footer based on
    frequency and position on the page. This is a critical first step.
    """
    page_count = len(doc)
    if page_count < 4: return set()

    text_counts = Counter()
    # Scan the middle half of the document to avoid title and reference pages
    start_page = page_count // 4
    end_page = page_count - start_page

    for page_num in range(start_page, end_page):
        page = doc[page_num]
        page_height = page.rect.height
        blocks = page.get_text("blocks")
        for b in blocks:
            # Check a wider vertical area: top 20% and bottom 15% of the page
            if b[1] < page_height * 0.20 or b[3] > page_height * 0.85:
                line_text = b[4].strip().replace('\n', ' ')
                if 5 < len(line_text) < 100 and not line_text.endswith('.'):
                    text_counts[line_text] += 1
    
    ignore_set = set()
    # Lower the threshold to catch text that appears on 40% of scanned pages
    min_occurrences = (end_page - start_page) * line_threshold
    for text, count in text_counts.items():
        if count >= min_occurrences:
            ignore_set.add(text)
            
    print(f"INFO: Detected {len(ignore_set)} repeating lines to ignore as headers/footers.")
    return ignore_set

def is_line_in_table(line_bbox, page_table_areas):
    """Checks if a line's bounding box is inside any of a page's table areas."""
    if not page_table_areas:
        return False
    
    l_x0, l_y0, l_x1, l_y1 = line_bbox
    for t_bbox in page_table_areas:
        t_x0, t_y0, t_x1, t_y1 = t_bbox
        # Check for containment. A line is in a table if its bbox is inside the table's bbox.
        if l_x0 >= t_x0 and l_y0 >= t_y0 and l_x1 <= t_x1 and l_y1 <= t_y1:
            return True
    return False

def get_dominant_style(line):
    """
    Determines the most common (dominant) style in a line of text.
    This is more robust than just checking the first span.
    """
    if not line["spans"]:
        return (10, False) # Default style

    style_counts = Counter()
    for span in line["spans"]:
        # More robust check for bold fonts
        is_bold = bool(re.search(r'bold|black|heavy', span["font"], re.IGNORECASE))
        style = (round(span["size"]), is_bold)
        # We weigh the style by the length of the text in the span
        style_counts[style] += len(span["text"].strip())
    
    # Return the most common style
    return style_counts.most_common(1)[0][0]

def is_mostly_uppercase(s):
    """
    Checks if a string is predominantly uppercase. More robust than isupper().
    """
    letters = [char for char in s if char.isalpha()]
    if not letters:
        return False
    uppercase_letters = [char for char in letters if char.isupper()]
    return (len(uppercase_letters) / len(letters)) > 0.8

def get_page_layout(page, threshold=0.3):
    """
    Analyzes the layout of a page to determine if it is single or multi-column.
    Returns the number of detected columns (1 or 2).
    """
    page_width = page.rect.width
    midpoint = page_width / 2
    
    blocks = page.get_text("blocks")
    if not blocks:
        return 1 # Default to 1 column if no text

    left_blocks = 0
    right_blocks = 0
    
    for b in blocks:
        if b[2] < midpoint: # Block ends before midpoint
            left_blocks += 1
        elif b[0] > midpoint: # Block starts after midpoint
            right_blocks += 1

    total_sided_blocks = left_blocks + right_blocks
    if total_sided_blocks == 0:
        return 1

    # Heuristic: If there are a significant number of blocks on both sides, it's a 2-column layout.
    if (left_blocks > 0 and right_blocks > 0):
        if (left_blocks / total_sided_blocks > threshold) and (right_blocks / total_sided_blocks > threshold):
            return 2
    
    return 1

def process_pdf(pdf_path, ml_output_path=None):
    """
    Processes a PDF using a hybrid ML and rule-based filtering approach.
    """
    doc = fitz.open(pdf_path)
    ignored_texts = detect_headers_and_footers(doc)
    
    table_areas = {}
    for page_num, page in enumerate(doc):
        tables = page.find_tables()
        if tables.tables:
            table_areas[page_num] = [t.bbox for t in tables]
    
    if table_areas:
        print(f"INFO: Detected tables on pages: {list(table_areas.keys())}")
        
    all_lines = []
    style_counts = Counter()
    page_heights = {}
    
    for page_num, page in enumerate(doc):
        page_width = page.rect.width
        page_heights[page_num] = page.rect.height
        page_table_bboxes = table_areas.get(page_num, [])
        
        num_columns = get_page_layout(page)
        page_midpoint = page_width / 2

        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    if not line["spans"]: continue

                    if is_line_in_table(line["bbox"], page_table_bboxes):
                        continue

                    line_text = "".join(span["text"] for span in line["spans"]).strip()
                    if not line_text or line_text in ignored_texts: continue

                    is_date = False
                    text_lower = line_text.lower()
                    if re.search(r'\b\d{4}\b', text_lower):
                        if any(month in text_lower for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                            if len(line_text.split()) <= 4:
                                is_date = True
                    if is_date:
                        continue

                    if re.match(r'^Page \d+\s*of\s*\d+$', line_text, re.I): 
                        continue

                    style = get_dominant_style(line)
                    style_counts[style] += 1

                    line_center_x = (line["bbox"][0] + line["bbox"][2]) / 2
                    column_index = 0
                    if num_columns == 2 and line_center_x > page_midpoint:
                        column_index = 1

                    # Create a single entry for the entire line
                    all_lines.append({
                        "page": page_num,
                        "text": line_text,
                        "style": style,
                        "is_bold": style[1],
                        "size": style[0],
                        "x0": line["bbox"][0],
                        "y0": line["bbox"][1],
                        "x1": line["bbox"][2],
                        "y1": line["bbox"][3],
                        "column": column_index,
                        "id": f"{page_num}-{line['bbox'][1]}",
                    })

    if not all_lines:
        return {"title": "", "outline": []}
    
    # --- TITLE IDENTIFICATION (remains mostly the same) ---
    page_0_height = page_heights.get(0, 1000)
    page_0_lines_top_half = sorted(
        [line for line in all_lines if line["page"] == 0 and line["y0"] < page_0_height / 2],
        key=lambda x: (x["column"], x["y0"])
    )

    doc_title = ""
    title_line_ids = set()
    title_breaker_keywords = ["summary", "background", "introduction", "table of contents", "abstract", "keywords"]
    author_affiliation_keywords = ["department", "university", "college", "institute", "@"]

    # if page_0_lines_top_half:
    #     try:
    #         max_size_page_0 = max(line["size"] for line in page_0_lines_top_half)
    #         first_potential_title_lines = [line for line in page_0_lines_top_half if line["size"] == max_size_page_0]
    #         if not first_potential_title_lines:
    #             raise ValueError("No lines found to be part of the title.")

    #         first_title_line = first_potential_title_lines[0]
    #         start_index = page_0_lines_top_half.index(first_title_line)
            
    #         title_lines_text = []
    #         last_line = None

    #         for i in range(start_index, len(page_0_lines_top_half)):
    #             current_line = page_0_lines_top_half[i]
    #             current_text_lower = current_line["text"].lower()

    #             if last_line:
    #                 if abs(current_line["y0"] - last_line["y0"]) > last_line["size"] * 2.5: break
    #                 if current_line["size"] < first_title_line["size"] * 0.7: break
    #                 if re.match(r"^(chapter|section|part|appendix|\d+(\.\d+)*\.?)\s", current_text_lower, re.I): break
    #                 if any(keyword in current_text_lower for keyword in title_breaker_keywords): break
    #                 if any(keyword in current_text_lower for keyword in author_affiliation_keywords): break
    #                 if re.match(r"^[•●*+-]\s*", current_line["text"]): break

    #             title_lines_text.append(current_line["text"])
    #             title_line_ids.add(current_line["id"])
    #             last_line = current_line
            
    #         doc_title = " ".join(title_lines_text)

    #     except (ValueError, IndexError):
    #         doc_title = ""
    if page_0_lines_top_half:
        try:
            sizes = [line["size"] for line in page_0_lines_top_half]
            max_size_page_0 = max(sizes)
            min_size_page_0 = min(sizes)

            # Check if all fonts are basically same size (difference <1pt)
            if max_size_page_0 - min_size_page_0 < 1:
                # fallback: find first bold & centered line (centered = x0 + x1 ≈ center of page)
                page_width = doc[0].rect.width
                center_x = page_width / 2
                centered_bold_lines = [
                    line for line in page_0_lines_top_half
                    if line["is_bold"] and abs((line["x0"] + line["x1"]) / 2 - center_x) < page_width * 0.1
                ]
                if centered_bold_lines:
                    # pick first, limit to max 2 lines
                    title_lines_text = [centered_bold_lines[0]["text"]]
                    title_line_ids.add(centered_bold_lines[0]["id"])
                    if len(centered_bold_lines) > 1:
                        title_lines_text.append(centered_bold_lines[1]["text"])
                        title_line_ids.add(centered_bold_lines[1]["id"])
                    doc_title = " ".join(title_lines_text)
                else:
                    doc_title = ""
            else:
                # normal path: use biggest font lines
                first_potential_title_lines = [line for line in page_0_lines_top_half if line["size"] == max_size_page_0]
                if not first_potential_title_lines:
                    raise ValueError("No lines found to be part of the title.")

                first_title_line = first_potential_title_lines[0]
                start_index = page_0_lines_top_half.index(first_title_line)

                title_lines_text = []
                last_line = None

                for i in range(start_index, len(page_0_lines_top_half)):
                    current_line = page_0_lines_top_half[i]
                    current_text_lower = current_line["text"].lower()

                    # break if too long title (more than 2 lines)
                    if len(title_lines_text) >= 2:
                        break
                    if last_line:
                        if abs(current_line["y0"] - last_line["y0"]) > last_line["size"] * 2.5: break
                        if current_line["size"] < first_title_line["size"] * 0.7: break
                        if re.match(r"^(chapter|section|part|appendix|\d+(\.\d+)*\.?)\s", current_text_lower, re.I): break
                        if any(keyword in current_text_lower for keyword in title_breaker_keywords): break
                        if any(keyword in current_text_lower for keyword in author_affiliation_keywords): break
                        if re.match(r"^[•●*+-]\s*", current_line["text"]): break

                    title_lines_text.append(current_line["text"])
                    title_line_ids.add(current_line["id"])
                    last_line = current_line

                doc_title = " ".join(title_lines_text)

        except (ValueError, IndexError):
            doc_title = ""


    if title_line_ids:
        print(f"INFO: Identified title: '{doc_title}'. Excluding {len(title_line_ids)} lines from heading analysis.")
        all_lines = [line for line in all_lines if line['id'] not in title_line_ids]

    # --- HEADING IDENTIFICATION (NEW LOGIC) ---

    # 1. Determine the main body style of the document
    non_bold_styles = [s for s, c in style_counts.items() if not s[1]]
    if not non_bold_styles:
        body_style = style_counts.most_common(1)[0][0] if style_counts else (10, False)
    else:
        body_style = Counter({s: style_counts[s] for s in non_bold_styles}).most_common(1)[0][0]
    print(f"INFO: Deduced body text style: {body_style} (size, is_bold)")

    # 2. **NEW**: Check if page 0 contains any paragraph text
    page_0_has_paragraphs = any(line['page'] == 0 and line['style'] == body_style for line in all_lines)
    if not page_0_has_paragraphs:
        print("INFO: Page 0 has no paragraph text. It will be ignored for heading extraction.")

    # 3. Filter for initial heading candidates based on style and simple heuristics
    initial_candidates = []
    for line in all_lines:
        # **NEW**: Skip page 0 if it's determined to be a cover page
        if not page_0_has_paragraphs and line['page'] == 0:
            continue
            
        # A heading must be stylistically distinct from the body text
        is_stylistically_distinct = (line['size'] > body_style[0]) or (line['is_bold'] and not body_style[1])
        if not is_stylistically_distinct:
            continue

        # Basic text filters
        text = line['text']
        if not (3 < len(text) < 250): continue
        if len(text.split()) > 25: continue # Exclude long lines
        if re.fullmatch(r"[\d\W_]+", text): continue # Exclude lines with only numbers/symbols
        if text.endswith(('.', ',', ';')) and len(text.split()) > 15: continue
        
        initial_candidates.append(line)

    # 4. **NEW**: Dynamically determine heading levels based on sorted styles
    if not initial_candidates:
        return {"title": doc_title, "outline": []}

    # Get all unique styles from our candidates
    heading_styles = sorted(
        list(set(c['style'] for c in initial_candidates)),
        key=lambda s: (-s[0], -s[1])  # Sort by size (desc), then by bold status (True first)
    )

    # Create a map from a style to its hierarchical level (H1, H2, etc.)
    style_to_level_map = {style: f"H{i+1}" for i, style in enumerate(heading_styles)}
    
    print("INFO: Detected heading style hierarchy:")
    for style, level in style_to_level_map.items():
        print(f"  - {level}: {style}")

    # 5. Assign levels to all candidates
    refined_headings = []
    for cand in initial_candidates:
        cand['level'] = style_to_level_map.get(cand['style'])
        if cand['level']:
             refined_headings.append(cand)
             
    # --- POST-PROCESSING (Merging and Final Filtering) ---
    sorted_headings = sorted(refined_headings, key=lambda x: (x['page'], x['column'], x['y0']))
    
    outline = []
    i = 0
    in_references_section = False
    
    while i < len(sorted_headings):
        current_heading = sorted_headings[i]
        j = i + 1
        # Merge consecutive lines that are part of the same heading
        while j < len(sorted_headings):
            prev_line = sorted_headings[j-1]
            next_line = sorted_headings[j]

            # Merge if lines are close, on the same page/column, and have the same style
            if (next_line["page"] == current_heading["page"] and
                next_line["column"] == current_heading["column"] and
                next_line["style"] == current_heading["style"] and
                abs(next_line["y0"] - prev_line["y1"]) < current_heading["size"] * 0.5):
                
                # Don't merge if the next line looks like a new numbered item
                if not re.match(r"^\d+(\.\d+)*\.?\s", next_line["text"]):
                    current_heading["text"] += " " + next_line["text"]
                    current_heading["y1"] = next_line["y1"] # Update bbox
                    j += 1
                else:
                    break
            else:
                break
        
        text = current_heading["text"].strip()
        text_lower = text.lower()
        is_rejected = False

        if any(keyword in text_lower for keyword in ["references", "bibliography"]):
            in_references_section = True
        
        # In reference section, only allow Appendix or new numbered sections
        if in_references_section and not any(keyword in text_lower for keyword in ["references", "bibliography"]):
            if not re.match(r"^(Appendix [A-Z]|\d+(\.\d+)*)\s", text):
                is_rejected = True

        if re.search(r'original research article|section:|doi:|inclusion criteria|exclusion criteria', text_lower):
            is_rejected = True

        if not is_rejected:
            outline.append({"level": current_heading["level"], "text": text, "page": current_heading["page"]})
        
        i = j

    return {"title": doc_title, "outline": outline}


def process_all_pdfs(input_dir, output_dir):
    """
    Processes all PDF files in a given directory.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)
            print(f"--- Processing {filename} ---")
            start_time = time.time()
            
            base_filename = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, base_filename + ".json")
            
            output_data = process_pdf(pdf_path)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=4)
            end_time = time.time()
            print(f"--- Finished {filename} in {end_time - start_time:.2f} seconds. ---")


# Example usage:
# process_all_pdfs('path/to/your/pdfs', 'path/to/your/output')