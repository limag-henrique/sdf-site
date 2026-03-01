import json
import os
import re

def clean_filename(name):
    """Sanitize string to be used as a filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()

def main():
    print("Starting Markdown Generation...")
    
    if not os.path.exists('experiments.json'):
        print("Error: experiments.json not found! Run scraper.py first.")
        return
        
    with open('experiments.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    base_dir = "Acervo_de_Textos"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    count = 0
    for exp in data:
        cat = clean_filename(exp.get('category', 'Outros'))
        cat_dir = os.path.join(base_dir, cat)
        if not os.path.exists(cat_dir):
            os.makedirs(cat_dir)
            
        title = clean_filename(exp.get('title', 'Untitled'))
        code = exp.get('code', '')
        
        filename = f"{code}_{title}.md" if code else f"{title}.md"
        filename = filename.replace(' ', '_')
        filepath = os.path.join(cat_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as out:
            out.write(f"# {exp.get('title')}\n\n")
            if code:
                out.write(f"**Código:** {code}\n")
            out.write(f"**Categoria:** {exp.get('category')}\n\n")
            if exp.get('description'):
                out.write(f"## Descrição Curta\n{exp.get('description')}\n\n")
            if exp.get('main_image'):
                out.write(f"## Imagem\n![{title}](../../{exp.get('main_image')})\n\n")
            if exp.get('full_text'):
                out.write(f"## Texto Completo\n{exp.get('full_text')}\n")
                
        count += 1
        
    print(f"Successfully generated {count} markdown files in {base_dir}/")

if __name__ == "__main__":
    main()
