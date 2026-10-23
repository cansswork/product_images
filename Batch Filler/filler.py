import os
import csv
import requests
from urllib.parse import quote

# ----------------- CONFIGURATION -----------------
TMDB_API_KEY = "ca03904e30a235ac4163573a513f96c1"
GITHUB_USER = "cansswork"
GITHUB_REPO = "product_images"
BRANCH = "main"
GITHUB_PHOTO_FOLDER = "Product Photos"

LOCAL_PHOTOS_PATH = r"C:\Users\jmc\Pictures\Business\Working\Product Photos"

TEMPLATE_CSV = "eBay-draft-listing-template-Oct-21-2026-10-16-58.csv"
OUTPUT_CSV = "eBay_Drafts_Populated.csv"
# --------------------------------------------------

BASE_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{quote(GITHUB_PHOTO_FOLDER)}"

def fetch_movie_details(folder_name):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={quote(folder_name)}"
    try:
        response = requests.get(search_url, timeout=10).json()
        results = response.get('results', [])
        
        movie_id = None
        
        if not results:
            print(f"\n[!] No metadata found on TMDb for folder: '{folder_name}'")
            manual_id = input("[*] Enter TMDb Movie ID manually (or press Enter to skip): ").strip()
            if manual_id.isdigit():
                movie_id = int(manual_id)
            else:
                return None

        elif len(results) == 1:
            movie_id = results[0]['id']

        else:
            # Multiple results found: prompt user to pick the right one
            print(f"\n[?] Multiple matches found for '{folder_name}':")
            max_choices = min(len(results), 5)  # Display up to top 5 choices
            for i in range(max_choices):
                item = results[i]
                title = item.get('title', 'Unknown')
                release_date = item.get('release_date', '')
                year = release_date.split('-')[0] if release_date else 'N/A'
                overview = item.get('overview', '')
                snippet = (overview[:60] + "...") if len(overview) > 60 else overview
                print(f"  [{i+1}] {title} ({year}) - {snippet}")
            print(f"  [{max_choices+1}] Enter TMDb Movie ID manually")
            print(f"  [0] Skip this title")

            choice = input(f"Select an option (1-{max_choices+1}, or 0 to skip): ").strip()
            
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= max_choices:
                    movie_id = results[idx - 1]['id']
                elif idx == max_choices + 1:
                    manual_id = input("[*] Enter TMDb Movie ID manually: ").strip()
                    if manual_id.isdigit():
                        movie_id = int(manual_id)
                    else:
                        return None
                else:
                    return None
            else:
                return None

        # Fetch detailed movie info using selected movie_id
        details_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
        data = requests.get(details_url, timeout=10).json()

        title = data.get('title', folder_name)
        
        release_date = data.get('release_date', '')
        year = release_date.split('-')[0] if release_date else 'N/A'
        
        try:
            year_int = int(year)
            aspect_ratio = "4:3 (Fullscreen)" if year_int < 1955 else "16x9 (Widescreen)"
        except:
            aspect_ratio = "16x9 (Widescreen)"

        runtime = f"Approx. {data.get('runtime', 0)} mins" if data.get('runtime') else "N/A"
        
        lang_code = data.get('original_language', '')
        lang_map = {'ja': 'Japanese', 'en': 'English', 'zh': 'Chinese', 'ko': 'Korean', 'fr': 'French'}
        language = lang_map.get(lang_code, lang_code.upper())

        countries = data.get('production_countries', [])
        country = countries[0]['name'] if countries else 'Japan'

        genres = data.get('genres', [])
        genre = genres[0]['name'] if genres else 'Cult'

        cast = [member['name'] for member in data.get('credits', {}).get('cast', [])[:3]]
        cast_str = " - ".join(cast) if cast else 'N/A'

        crew = data.get('credits', {}).get('crew', [])
        directors = [member['name'] for member in crew if member.get('job') == 'Director']
        director_str = ", ".join(directors) if directors else 'N/A'

        overview = data.get('overview', 'No synopsis available.')
        sentences = [s.strip() for s in overview.split('.') if s.strip()]
        short_synopsis = ". ".join(sentences[:2]) + "." if sentences else "No synopsis available."

        return {
            "title": title,
            "year": year,
            "aspect_ratio": aspect_ratio,
            "runtime": runtime,
            "language": language,
            "country": country,
            "genre": genre,
            "actors": cast_str,
            "director": director_str,
            "rating": "NR" if not data.get('adult') else "R",
            "synopsis": short_synopsis
        }
    except Exception as e:
        print(f"    [!] Error for {folder_name}: {e}")
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
            meta = fetch_movie_details(folder_name)
            
            image_files = sorted([
                f for f in os.listdir(folder_full_path)
                if os.path.splitext(f)[1].lower() in valid_extensions
            ])
            
            image_urls = [
                f"{BASE_URL}/{quote(folder_name)}/{quote(img_file)}"
                for img_file in image_files
            ]
            combined_photo_urls = "|".join(image_urls)

            m_title = meta['title'] if meta else folder_name
            m_year = meta['year'] if meta else ""
            m_aspect = meta['aspect_ratio'] if meta else "16x9 (Widescreen)"
            m_runtime = meta['runtime'] if meta else ""
            m_lang = meta['language'] if meta else "Japanese"
            m_country = meta['country'] if meta else "Japan"
            m_genre = meta['genre'] if meta else "Cult, Horror"
            m_actors = meta['actors'] if meta else ""
            m_director = meta['director'] if meta else ""
            m_rating = meta['rating'] if meta else "NR"
            m_synopsis = meta['synopsis'] if (meta and meta.get('synopsis')) else "No synopsis available."

            ebay_title = f"{folder_name} (DVD)"

            description_html = (
                f"<p><strong>Plot:</strong> <br /> <em>{m_synopsis}</em></p>"
                f"<p><strong>📀 Looking for a <em>hard-to-find</em> movie title? 📩&nbsp;</strong>Message us for a quick quote!</p>"
            )

            row = {
                "Action(SiteID=US|Country=US|Currency=USD|Version=1193|CC=UTF-8)": "Draft",
                "Custom label (SKU)": "",
                "Category ID": "11232",
                "Title": ebay_title,
                "UPC": "Does not apply",
                "Price": "15.00",
                "Quantity": "1",
                "Item photo URL": combined_photo_urls,
                "Condition ID": "1000",
                "Description": description_html,
                "Format": "FixedPrice",

                "C:Media Type": "DVD",
                "C:Video Format": "NTSC",
                "C:Region Code": "0 (Region-Free)",
                "C:Aspect Ratio": m_aspect,
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

    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
        for h in header_lines:
            f.write(h)
        
        writer = csv.DictWriter(f, fieldnames=all_columns)
        writer.writeheader()
        for r in new_rows:
            writer.writerow({col: r.get(col, "") for col in all_columns})

    print(f"\n[✓] Successfully generated '{OUTPUT_CSV}'!")

if __name__ == "__main__":
    generate_ebay_csv()
