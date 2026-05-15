import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

NS = "http://www.mediawiki.org/xml/export-0.11/"

TARGET_SECTIONS = {"See", "Do", "Eat", "Drink", "Buy", "Sleep", "Get in", "Get around"}

@dataclass
class DestinationArticle:
    title: str
    sections: dict[str, str] = field(default_factory=dict)


def strip_wikitext(text: str) -> str:
    text = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', text)  # [[link|label]] → label
    text = re.sub(r'\{\{[^}]+\}\}', '', text)                        # {{templates}}
    text = re.sub(r"'{2,3}", '', text)                               # '''bold''', ''italic''
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL) # <ref> citations
    text = re.sub(r'<[^>]+>', '', text)                              # remaining HTML tags
    text = re.sub(r'\n{3,}', '\n\n', text)                          # collapse blank lines
    return text.strip()


def extract_sections(wikitext: str) -> dict[str, str]:
    sections = {}
    current_section = None
    current_lines = []

    for line in wikitext.splitlines():
        heading_match = re.match(r'^==\s*([^=]+?)\s*==\s*$', line)
        if heading_match:
            if current_section in TARGET_SECTIONS and current_lines:
                sections[current_section] = strip_wikitext('\n'.join(current_lines))
            current_section = heading_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section in TARGET_SECTIONS and current_lines:
        sections[current_section] = strip_wikitext('\n'.join(current_lines))

    return sections


def is_valid_destination(title: str, wikitext: str, is_redirect: bool) -> bool:
    if is_redirect:
        return False
    if wikitext.strip().startswith("#REDIRECT"):
        return False
    if "{{disambiguation}}" in wikitext.lower():
        return False
    if "{{phrasebook}}" in wikitext.lower():
        return False
    return True


def parse_dump(filepath: str) -> list[DestinationArticle]:
    articles = []

    with open(filepath, "rb") as f:
        for event, elem in ET.iterparse(f, events=("end",)):
            if elem.tag != f"{{{NS}}}page":
                continue

            ns_val = elem.findtext(f"{{{NS}}}ns") or ""
            if ns_val != "0":
                elem.clear()
                continue

            title = elem.findtext(f"{{{NS}}}title") or ""
            is_redirect = elem.find(f"{{{NS}}}redirect") is not None
            wikitext = elem.findtext(f".//{{{NS}}}text") or ""

            if is_valid_destination(title, wikitext, is_redirect):
                sections = extract_sections(wikitext)
                if sections:
                    articles.append(DestinationArticle(title=title, sections=sections))

            elem.clear()

    return articles


if __name__ == "__main__":
    articles = parse_dump("./data/enwikivoyage-20260501-pages-articles-multistream.xml")
    print(f"Parsed {len(articles)} destination articles")

    # tokyo = next((a for a in articles if a.title == "Tokyo"), None)
    # if tokyo:
    #     print(f"\nTokyo sections: {list(tokyo.sections.keys())}")
    #     print(f"\nEat preview:\n{tokyo.sections.get('Eat', '')[:300]}")
    a = articles[550]
    print (a.title)
    print(a.sections.get("See"))