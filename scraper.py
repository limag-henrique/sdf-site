import requests
from bs4 import BeautifulSoup
import json
import os
import re
import uuid

BASE_URL = "https://demonstracoes.fisica.ufmg.br/"
OUTPUT_FILE = "experiments.json"

CATEGORIES_MAPPING = {
    "1": "Mecânica",
    "2": "Mecânica dos Fluidos",
    "3": "Oscilações e Ondas",
    "4": "Termodinâmica",
    "5": "Eletricidade e Magnetismo",
    "6": "Óptica",
    "7": "Física Moderna",
    "8": "Astronomia e Astrofísica",
    "9": "Equipamentos"
}

def get_soup(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

IMAGE_DIR = "images"
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

def download_image(url, exp_code):
    try:
        if not url.startswith('http'):
            url = BASE_URL.rstrip('/') + url if url.startswith('/') else BASE_URL + url
        
        # Don't download UI logos
        if 'apoio/logos.png' in url or 'css/img' in url or 'logo' in url.lower():
            return None
            
        r = requests.get(url, stream=True, timeout=10)
        r.raise_for_status()
        
        # Get extension
        ext = url.split('.')[-1]
        if len(ext) > 4 or not ext.isalnum():
            ext = 'jpg' # default
            
        # Clean exp code or use uuid
        safe_name = exp_code.replace('.', '_').replace('-', '_') if exp_code else str(uuid.uuid4())[:8]
        filename = f"{safe_name}.{ext}"
        filepath = os.path.join(IMAGE_DIR, filename)
        
        # Avoid duplicate names if multiple images per code
        counter = 1
        while os.path.exists(filepath):
            # check if file size is same, if same it might be the same image
            filename = f"{safe_name}_{counter}.{ext}"
            filepath = os.path.join(IMAGE_DIR, filename)
            counter += 1
            
        with open(filepath, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)
                
        # Return path formatted for web with forward slashes
        return filepath.replace('\\', '/')
    except Exception as e:
        print(f"  [!] Failed to download image {url}: {e}")
        return None

def extract_experiment_data(demo_url, category):
    soup = get_soup(demo_url)
    if not soup:
        return None

    # Title is usually an h1 or h2 on the demo page
    title_elem = soup.find('h1', class_='page-header') or soup.find('h2')
    title = title_elem.text.strip() if title_elem else "Untitled"

    # Description (usually follow the title)
    # The actual structure is unknown, let's grab all text from the main content div
    content_div = soup.find('div', class_='col-md-9') or soup.find('main') or soup.find('article') or soup.find('div', class_='content')
    
    full_text = ""
    description = ""
    if content_div:
        # Paragraphs hold the detailed text
        paragraphs = content_div.find_all('p')
        text_lines = [p.text.strip() for p in paragraphs if p.text.strip()]
        full_text = "\n".join(text_lines)
        if text_lines:
            description = text_lines[0] # Use first paragraph as short description
            
    # Attempt to extract code like "3A15.42"
    code_match = re.search(r'\b[1-9][A-Z]\d{2}\.\d{2}\b', title)
    code = code_match.group(0) if code_match else ""
    
    # If title has the code, let's clean it up
    if code and code in title:
        title = title.replace(code, '').replace('-', '').strip()

    # Image Extraction
    image_paths = []
    # Search for all images in the content div or the whole body
    search_area = content_div if content_div else soup
    imgs = search_area.find_all('img')
    for img in imgs:
        src = img.get('src')
        if src:
            local_path = download_image(src, code)
            if local_path:
                image_paths.append(local_path)
                
    main_image = image_paths[0] if image_paths else ""

    return {
        "url": demo_url,
        "category": category,
        "code": code,
        "title": title,
        "description": description,
        "full_text": full_text,
        "images": image_paths,
        "main_image": main_image
    }

def scrape_category(category_idx, category_name):
    print(f"Scraping category: {category_name} ({category_idx})")
    cat_url = f"{BASE_URL}demos/pira/{category_idx}"
    soup = get_soup(cat_url)
    
    experiments = []
    
    if not soup:
        return experiments
        
    # Find all links to demos
    # The links are likely inside some list or grid
    demo_links = soup.find_all('a', href=re.compile(r'/demo/\d+'))
    
    # Use a set to avoid duplicate URLs
    seen_urls = set()
    
    for link in demo_links:
        href = link.get('href')
        if not href.startswith('http'):
            # It might be a relative relative from root or current dir
            if href.startswith('/'):
                full_url = BASE_URL.rstrip('/') + href
            else:
                continue # Ignore weird links for now
        else:
            full_url = href
            
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        
        print(f"  Fetching: {full_url}")
        data = extract_experiment_data(full_url, category_name)
        if data:
            experiments.append(data)
            
    return experiments

def main():
    print("Starting Web Scraper for Física UFMG Demonstrations...")
    all_experiments = []
    
    # Attempting to brute-force categorical indices 1-9 based on standard physics index schemes
    for idx, category_name in CATEGORIES_MAPPING.items():
        data = scrape_category(idx, category_name)
        all_experiments.extend(data)
        
    print(f"\nTotal experiments scraped: {len(all_experiments)}")
    
    # Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_experiments, f, ensure_ascii=False, indent=2)
        
    print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
