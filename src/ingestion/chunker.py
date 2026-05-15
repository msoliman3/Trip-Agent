from dataclasses import dataclass
import re
from xmlparser import DestinationArticle, parse_dump

@dataclass
class Chunk:
    text: str           
    metadata: dict 
    
def clean_section_text(text: str) -> str:
    # 1. Remove image/thumb lines
    text = re.sub(r'\s*thumb\s*\|.*', '', text, flags=re.IGNORECASE)
    
    # 2. Remove subsection headings (===Museums===)
    # You're flattening, so just strip the === markers entirely
    text = re.sub(r'===.*?===', '', text)
    
    # 3. Remove empty bullet points (a * with only whitespace after)
    text = re.sub(r'^\*\s*$', '', text, flags=re.MULTILINE)
    
    # 4. Collapse multiple blank lines into one
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\*\*\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'15px\s?', '', text)
    # Removes [https://some-url.com Display Text] → Display Text
    text = re.sub(r'\[https?://\S+\s+(.*?)\]', r'\1', text) 
    
    return text.strip()

#input: a Destination article with multiple sections 
#output: return a list of chunks with each chunk having the text from one section and also the 
MIN_CHUNK_LENGTH = 50
def chunk_article(article: DestinationArticle) -> list[Chunk]:
    chunks = []
    for section in article.sections.keys():
        raw_text = article.sections.get(section)
        cleaned_text = clean_section_text(raw_text)
        if (len(cleaned_text) < MIN_CHUNK_LENGTH):
            continue
        meta = {"destination" : article.title, "section": section }
        text = f"{article.title} | {section}: {cleaned_text}"
        chunk = Chunk(text, meta)
        chunks.append(chunk)

    return chunks 




if __name__ == "__main__":
    articles = parse_dump("./data/enwikivoyage-20260501-pages-articles-multistream.xml")
    print(f"Parsed {len(articles)} destination articles")

    # tokyo = next((a for a in articles if a.title == "Tokyo"), None)
    # if tokyo:
    #     print(f"\nTokyo sections: {list(tokyo.sections.keys())}")
    #     print(f"\nEat preview:\n{tokyo.sections.get('Eat', '')[:300]}")


    a = articles[500]

        


