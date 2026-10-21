import os
import csv
from urllib.parse import quote

# ----------------- CONFIGURATION -----------------
# 1. Your GitHub raw images base URL
# Replace "YourUsername" and "YourRepo" with your actual GitHub details:
GITHUB_USER = "YourUsername"
GITHUB_REPO = "YourRepo"
BRANCH = "main"

# The path on GitHub inside your repo (from your screenshot, it's inside "Product Photos")
GITHUB_PHOTO_FOLDER = "Product Photos"

# 2. Path to your local folder containing the product subfolders
LOCAL_PHOTOS_PATH = r"C:\path\to\your\Product Photos"

# 3. CSV File Names
TEMPLATE_CSV = "eBay-draft-listing-template-Oct-21-2026-10-16-58.csv"
OUTPUT_CSV = "eBay_Drafts_Populated.csv"
# --------------------------------------------------

# Construct the base GitHub URL
# Raw GitHub URL structure: https://raw.githubusercontent.com/USER/REPO/BRANCH/Product%20Photos/
BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{quote(GITHUB_PHOTO_FOLDER)}"

def generate_ebay_csv():
    if not os.path.exists(LOCAL_PHOTOS_PATH):
        print(f"Error: Local directory '{LOCAL_PHOTOS_PATH}' does not exist.")
        return

    # Read the header lines from the eBay draft template to preserve eBay metadata
    header_lines = []
    with open(TEMPLATE_CSV, 'r', encoding='utf-8') as f:
        for _ in range(4):
            header_lines.append(f.readline())
        columns_line = f.readline()
        # Get sample row format if exists
        sample_row = f.readline()

    # Parse headers
    columns = [col.strip('"').strip() for col in columns_line.strip().split(',')]
    
    # Process product folders
    new_rows = []
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

    # Iterate through folders inside 'Product Photos'
    for folder_name in sorted(os.listdir(LOCAL_PHOTOS_PATH)):
        folder_full_path = os.path.join(LOCAL_PHOTOS_PATH, folder_name)
        
        if os.path.isdir(folder_full_path):
            # 1. Product Title is the Folder Name
            title = folder_name
            
            # 2. Collect image files sorted numerically (01.jpg, 02.jpg, etc.)
            image_files = sorted([
                f for f in os.listdir(folder_full_path)
                if os.path.splitext(f)[1].lower() in valid_extensions
            ])
            
            # 3. Combine multiple image URLs separated by vertical pipes (|) for eBay
            # eBay supports up to 12 photo URLs joined with '|' in the "Item photo URL" column
            image_urls = [
                f"{BASE_URL}/{quote(folder_name)}/{quote(img_file)}"
                for img_file in image_files
            ]
            combined_photo_urls = "|".join(image_urls)

            # Create entry matching eBay schema
            row = {
                "Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Draft",
                "Custom label (SKU)": "",
                "Category ID": "11232",  # Default category or update as needed
                "Title": title,
                "UPC": "",
                "Price": "10",            # Default placeholder price
                "Quantity": "1",          # Default quantity
                "Item photo URL": combined_photo_urls,
                "Condition ID": "NEW",    # or 1000
                "Description": f"<p>{title}</p>",
                "Format": "FixedPrice"
            }
            new_rows.append(row)

    # Write the populated file preserving eBay header comments (#INFO)
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        # Write top 4 #INFO metadata lines
        for h in header_lines:
            f.write(h)
        
        # Write CSV field names and rows
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for r in new_rows:
            # Map values into correct header columns
            writer.writerow({col: r.get(col, "") for col in columns})

    print(f"Successfully generated '{OUTPUT_CSV}' with {len(new_rows)} product listings!")

if __name__ == "__main__":
    generate_ebay_csv()