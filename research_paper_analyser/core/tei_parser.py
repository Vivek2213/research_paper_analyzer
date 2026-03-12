import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, Iterable


MOJIBAKE_REPLACEMENTS = {
    "âˆ†": "∆",
    "â‰ƒ": "≃",
    "â‰¥": "≥",
    "â‰¤": "≤",
    "âˆ¼": "∼",
    "âˆ’": "−",
    "Ã—": "×",
    "âŠ™": "⊙",
    "MâŠ™": "M⊙",
    "Î±": "α",
    "Î²": "β",
    "Î»": "λ",
    "Ï€": "π",
    "Î¸": "θ",
    "Î›": "Λ",
}


@dataclass(frozen=True)
class ParsedPaper:
    title: str
    sections: Dict[str, str]
    full_text: str


def _normalize_section_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name.strip()).lower()
    return name


def _collapse_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _repair_mojibake(text: str) -> str:
    repaired = text
    for broken, fixed in MOJIBAKE_REPLACEMENTS.items():
        repaired = repaired.replace(broken, fixed)
    return repaired


def _extract_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    text = " ".join(part for part in element.itertext() if part and part.strip())
    return _repair_mojibake(_collapse_whitespace(text))


def _collect_paragraphs(elements: Iterable[ET.Element]) -> str:
    paragraphs = []
    for element in elements:
        text = _extract_text(element)
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs).strip()


def parse_tei(tei_xml: str) -> ParsedPaper:
    root = ET.fromstring(tei_xml)
    ns = {"tei": "http://www.tei-c.org/ns/1.0"}

    title_el = root.find(".//tei:titleStmt/tei:title", ns)
    title = _extract_text(title_el) or "Untitled"

    sections: Dict[str, str] = {}
    full_text_parts = []

    abstract_text = _collect_paragraphs(root.findall(".//tei:profileDesc/tei:abstract//tei:p", ns))
    if abstract_text:
        sections["abstract"] = abstract_text
        full_text_parts.append(abstract_text)

    for div in root.findall(".//tei:text//tei:div", ns):
        head_el = div.find("tei:head", ns)
        head_text = _extract_text(head_el) or "section"
        section_name = _normalize_section_name(head_text)
        section_text = _collect_paragraphs(div.findall("./tei:p", ns))
        if not section_text:
            section_text = _collect_paragraphs(div.findall(".//tei:p", ns))
        if section_text:
            sections.setdefault(section_name, "")
            sections[section_name] = (sections[section_name] + "\n" + section_text).strip()
            full_text_parts.append(section_text)

    full_text = "\n".join(full_text_parts).strip()
    return ParsedPaper(title=title, sections=sections, full_text=full_text)
