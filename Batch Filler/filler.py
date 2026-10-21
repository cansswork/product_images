import os
import csv
import requests
from urllib.parse import quote

# ----------------- CONFIGURATION -----------------
# 1. Your TMDb API Key (Free from https://www.themoviedb.org/settings/api)
TMDB_API_KEY = "YOUR_TMDB_API_KEY_HERE"

# 2. Your GitHub details
GITHUB_USER = "cansswork"
GITHUB_REPO = "product_images"
BRANCH = "main"
GITHUB_PHOTO_FOLDER = "Product Photos"

# 3. Local Photos Path
LOCAL_PHOTOS_PATH = r"C:\Users\jmc\Pictures\Business\Working\Product Photos"

# 4. CSV Files
TEMPLATE_CSV = "eBay-draft-listing-template-Oct-21-2026-10-16-58.csv"
OUTPUT_CSV = "eBay_Drafts_Populated.csv"
# --------------------------------------------------

BASE_URL = f"https://raw.githubusercontent.com/cansswork/product_images/tree/main/Product%20Photos"

def fetch_movie_details(folder_name):
    """
    Fetches metadata from TMDb API based on folder name.
    """
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key=ca03904e30a235ac4163573a513f96c1&query={quote(folder_name)}"
    try:
        response = requests.get(search_url).json()
        results = response.get('results', [])
        
        if not results:
            print(f"[!] No metadata found on TMDb for: {folder_name}")
            return None

        movie_id = results[0]['id']
        
        # Fetch detailed movie info
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=ca03904e30a235ac4163573a513f96c1&append_to_response=credits"
        data = requests.get(details_url).json()

        # Extract values
        orig_title = data.get('original_title', folder_name)
        title = data.get('title', folder_name)
        combined_title = f"{orig_title} / {title}" if orig_title != title else title
        
        release_date = data.get('release_date', '')
        year = release_date.split('-')[0] if release_date else 'N/A'
        
        runtime = f"Approx. {data.get('runtime', 0)} mins" if data.get('runtime') else "N/A"
        
        # Original Language mapping
        lang_code = data.get('original_language', '')
        lang_map = {'ja': 'Japanese', 'en': 'English', 'zh': 'Chinese', 'ko': 'Korean', 'fr': 'French'}
        language = lang_map.get(lang_code, lang_code.upper())

        # Production Country
        countries = data.get('production_countries', [])
        country = countries[0]['name'] if countries else 'Japan'

        # Main Genre
        genres = data.get('genres', [])
        genre = genres[0]['name'] if genres else 'Cult'

        # Cast (Top 3)
        cast = [member['name'] for member in data.get('credits', {}).get('cast', [])[:3]]
        cast_str = " · ".join(cast) if cast else 'N/A'

        # Crew (Director)
        crew = data.get('credits', {}).get('crew', [])
        directors = [member['name'] for member in crew if member.get('job') == 'Director']
        director_str = ", ".join(directors) if directors else 'N/A'

        return {
            "title": combined_title,
            "year": year,
            "runtime": runtime,
            "language": language,
            "country": country,
            "genre": genre,
            "actors": cast_str,
            "director": director_str,
            "rating": "NR" if not data.get('adult') else "R"
        }
    except Exception as e:
        print(f"[!] Error fetching metadata for {folder_name}: {e}")
        return None

def generate_ebay_csv():
    if not os.path.exists(LOCAL_PHOTOS_PATH):
        print(f"Error: Local directory '{LOCAL_PHOTOS_PATH}' does not exist.")
        return

    header_lines = []
    with open(TEMPLATE_CSV, 'r', encoding='utf-8') as f:
        for _ in range(4):
            header_lines.append(f.readline())
        columns_line = f.readline()

    columns = [col.strip('"').strip() for col in columns_line.strip().split(',')]
    
    new_rows = []
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

    for folder_name in sorted(os.listdir(LOCAL_PHOTOS_PATH)):
        folder_full_path = os.path.join(LOCAL_PHOTOS_PATH, folder_name)
        
        if os.path.isdir(folder_full_path):
            print(f"[*] Processing: {folder_name}...")
            
            # Fetch metadata automatically
            meta = fetch_movie_details(folder_name)
            
            # Collect photos
            image_files = sorted([
                f for f in os.listdir(folder_full_path)
                if os.path.splitext(f)[1].lower() in valid_extensions
            ])
            
            image_urls = [
                f"{BASE_URL}/{quote(folder_name)}/{quote(img_file)}"
                for img_file in image_files
            ]
            combined_photo_urls = "|".join(image_urls)

            # Assign fetched meta or default fallbacks
            m_title = meta['title'] if meta else folder_name
            m_year = meta['year'] if meta else ""
            m_runtime = meta['runtime'] if meta else ""
            m_lang = meta['language'] if meta else "Japanese"
            m_country = meta['country'] if meta else "Japan"
            m_genre = meta['genre'] if meta else "Cult, Horror"
            m_actors = meta['actors'] if meta else ""
            m_director = meta['director'] if meta else ""
            m_rating = meta['rating'] if meta else "NR"

            row = {
                "Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Draft",
                "Custom label (SKU)": "",
                "Category ID": "11232",  # DVDs & Blu-ray Discs
                "Title": folder_name,
                "UPC": "Does not apply",
                "Price": "15.00",
                "Quantity": "1",
                "Item photo URL": combined_photo_urls,
                "Condition ID": "1000",   # Brand New
                "Description": f"<p><b>{folder_name}</b></p>",
                "Format": "FixedPrice",

                # --- AUTO-POPULATED ITEM SPECIFICS ---
                "C:Media Type": "DVD",
                "C:Video Format": "NTSC",
                "C:Region Code": "0 (Region-Free)",
                "C:Aspect Ratio": "16x9 (Widescreen)",  # Standard DVD aspect ratio
                "C:Runtime": m_runtime,
                "C:Language": m_lang,
                "C:Subtitles": "English (Optional)",
                "C:Condition": "Brand New",
                "C:Product Origin": "Philippines",
                "C:Movie/TV Title": m_title,
                "C:Release Year": m_year,
                "C:Country/Region of Manufacture": m_country,
                "C:Rating": m_rating,
                "C:Genre": m_genre,
                "C:Actor": m_actors,
                "C:Director": m_director
            }
            new_rows.append(row)

    all_columns = list(columns)
    for r in new_rows:
        for key in r.keys():
            if key not in all_columns:
                all_columns.append(key)

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        for h in header_lines:
            f.write(h)
        
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        for r in new_rows:
            writer.writerow({col: r.get(col, "") for col in all_columns})

    print(f"\n[✓] Done! Generated '{OUTPUT_CSV}' with full metadata and image URLs.")

if __name__ == "__main__":
    generate_ebay_csv()
