"""Question-aware context selection (keeps each LLM request small, no embeddings).

* ``parse_query``    — dates, zones, cameras, event ids and violation keywords in the question.
* ``select_rows``    — at most ``MAX_ROWS`` matching log rows (fallback: latest violations).
* ``top_paragraphs`` — regulation paragraphs ranked by character-trigram TF-IDF, which works
  for Thai (no spaces between words) as well as English.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field

import pandas as pd

from backend import regulations
from backend.config import ZONE_LABELS
from backend.textfmt import THAI_MONTHS, zone_name

MAX_ROWS = 15
FALLBACK_ROWS = 10
TOP_PARAGRAPHS = 5
MAX_PARAGRAPH_CHARS = 600

# Extra spellings people use for each zone (the Thai display label and key are always included).
ZONE_ALIASES: dict[str, tuple[str, ...]] = {
    "entrance": ("ทางเข้า", "ประตู"),
    "crane": ("เครน", "ปั้นจั่น"),
    "scaffold": ("นั่งร้าน",),
    "floor3": ("ชั้น 3", "ชั้น3", "ชั้นสาม", "floor 3"),
    "warehouse": ("คลังวัสดุ", "คลัง", "โกดัง"),
}
VIOLATION_WORDS = ("ละเมิด", "ไม่สวมหมวก", "ไม่สวม", "ฝ่าฝืน", "violation", "no-hardhat", "no_hardhat")
THAI_MONTH_ABBR = ("ม.ค.", "ก.พ.", "มี.ค.", "เม.ย.", "พ.ค.", "มิ.ย.", "ก.ค.", "ส.ค.", "ก.ย.", "ต.ค.", "พ.ย.", "ธ.ค.")


@dataclass
class Query:
    dates: set[str] = field(default_factory=set)       # ISO dates
    zones: set[str] = field(default_factory=set)       # zone keys
    cameras: set[str] = field(default_factory=set)     # "cam2"
    event_ids: set[str] = field(default_factory=set)   # "EVT-0002"
    violation: bool = False

    def describe(self) -> str:
        """Thai summary of the filters, for the sources panel."""
        parts = [f"รหัส {', '.join(sorted(self.event_ids))}"] if self.event_ids else []
        parts += [f"วันที่ {', '.join(sorted(self.dates))}"] if self.dates else []
        parts += [", ".join(zone_name(z) for z in sorted(self.zones))] if self.zones else []
        parts += [f"กล้อง {', '.join(sorted(self.cameras))}"] if self.cameras else []
        parts += ["เฉพาะที่ฝ่าฝืน"] if self.violation else []
        return " · ".join(parts)

    @property
    def has_filters(self) -> bool:
        return bool(self.dates or self.zones or self.cameras or self.event_ids)


def _thai_dates(text: str, default_year: int | None) -> set[str]:
    """"29 กันยายน 2569", "29 ก.ย. 69", "29 ก.ย." → ISO dates (BE years converted)."""
    out: set[str] = set()
    names = "|".join(re.escape(m) for m in (*THAI_MONTHS, *THAI_MONTH_ABBR))
    for m in re.finditer(rf"(\d{{1,2}})\s*({names})\s*(\d{{2,4}})?", text):
        day, month_s, year_s = int(m.group(1)), m.group(2), m.group(3)
        month = (THAI_MONTHS.index(month_s) if month_s in THAI_MONTHS else THAI_MONTH_ABBR.index(month_s)) + 1
        if year_s:
            year = int(year_s)
            year = year + 2500 if year < 100 else year   # "69" → 2569 (BE)
            year = year - 543 if year > 2400 else year   # BE → CE
        elif default_year:
            year = default_year
        else:
            continue
        try:
            out.add(pd.Timestamp(year=year, month=month, day=day).strftime("%Y-%m-%d"))
        except ValueError:
            pass
    return out


def parse_query(texts: list[str], default_year: int | None = None) -> Query:
    q = Query()
    text = " ".join(texts)
    low = text.lower()
    q.dates |= set(re.findall(r"\d{4}-\d{2}-\d{2}", text))
    q.dates |= _thai_dates(text, default_year)
    for key, label in ZONE_LABELS.items():
        spellings = (key, label, *ZONE_ALIASES.get(key, ()))
        if any(s.lower() in low for s in spellings):
            q.zones.add(key)
    q.cameras |= {f"cam{int(n)}" for n in re.findall(r"(?:cam|กล้อง(?:ตัวที่|ที่)?)\s*(\d+)", low)}
    q.event_ids |= {f"EVT-{int(n):04d}" for n in re.findall(r"evt[\s\-‑]?(\d+)", low)}
    q.violation = any(w in low for w in VIOLATION_WORDS)
    return q


@dataclass
class RowSelection:
    rows: pd.DataFrame
    matched: int          # rows matching the filters (before the cap); 0 when falling back
    fallback: bool
    description: str


def select_rows(df: pd.DataFrame, query: Query) -> RowSelection:
    """Rows relevant to the question, newest first, capped at ``MAX_ROWS``."""
    newest = df.sort_values("datetime", ascending=False)
    if query.has_filters:
        # Date/zone/camera filters AND together (violation narrows them); event ids are added on top.
        attrs = bool(query.dates or query.zones or query.cameras)
        mask = pd.Series(attrs, index=df.index)
        if query.dates:
            mask &= df["date"].isin(query.dates)
        if query.zones:
            mask &= df["zone"].isin(query.zones)
        if query.cameras:
            mask &= df["camera"].isin(query.cameras)
        if query.violation and attrs:
            mask &= df["violation"]
        if query.event_ids:
            mask |= df["event_id"].isin(query.event_ids)
        hits = newest[mask.reindex(newest.index)]
        if len(hits):
            return RowSelection(hits.head(MAX_ROWS), len(hits), False, query.describe())
    latest = newest[newest["violation"]].head(FALLBACK_ROWS)
    return RowSelection(latest, 0, True, f"ไม่พบเงื่อนไขเฉพาะ — แสดงการฝ่าฝืนล่าสุด {len(latest)} รายการ")


# --- regulation paragraphs ---------------------------------------------------------------

@dataclass
class Paragraph:
    file: str
    title: str
    text: str


_RULE_START = re.compile(r"^\**\s*(ข้อ|ข้อปฏิบัติ|มาตรา|article|section|rule)\b", re.IGNORECASE)


def split_paragraphs(file: str, text: str) -> list[Paragraph]:
    """Blank-line blocks; tables and list items stay with the block before them, headings
    become the title of the following blocks, and long blocks are cut at ``MAX_PARAGRAPH_CHARS``."""
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip()]
    out: list[Paragraph] = []
    heading = ""
    for block in blocks:
        first, *rest = block.splitlines()
        if first.startswith("#"):
            heading = first.lstrip("# ").strip()
            if not rest:
                continue
            block, first = "\n".join(rest).strip(), rest[0]
        attach = out and out[-1].file == file and (block.startswith("|") or re.match(r"^(\d+\.|[-*])\s", block)) \
            and not _RULE_START.match(block)
        if attach:
            out[-1].text += "\n" + block
        else:
            title = re.sub(r"\*+", "", first.split(":")[0]).strip()[:60] if _RULE_START.match(first) else heading
            out.append(Paragraph(file, title or heading, block))
    for p in out:
        if len(p.text) > MAX_PARAGRAPH_CHARS:
            p.text = p.text[:MAX_PARAGRAPH_CHARS].rsplit("\n", 1)[0] + "\n…"
    return out


def all_paragraphs() -> list[Paragraph]:
    paras: list[Paragraph] = []
    for path in regulations.list_paths():
        text = regulations.read_text(path)
        if text:
            paras += split_paragraphs(path.name, text)
    return paras


def _trigrams(text: str) -> Counter[str]:
    s = re.sub(r"[\s*|#`>\-]+", " ", text.lower())
    return Counter(s[i : i + 3] for i in range(len(s) - 2) if s[i : i + 3].strip())


def top_paragraphs(query_text: str, k: int = TOP_PARAGRAPHS, paragraphs: list[Paragraph] | None = None) -> list[Paragraph]:
    """Top ``k`` paragraphs by TF-IDF cosine similarity on character trigrams (document order kept)."""
    paras = all_paragraphs() if paragraphs is None else paragraphs
    if len(paras) <= k:
        return paras
    docs = [_trigrams(p.title + " " + p.text) for p in paras]
    df_count: Counter[str] = Counter(g for d in docs for g in d)
    idf = {g: math.log((1 + len(docs)) / (1 + n)) + 1 for g, n in df_count.items()}

    def vec(c: Counter[str]) -> dict[str, float]:
        v = {g: (1 + math.log(n)) * idf.get(g, 0.0) for g, n in c.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {g: x / norm for g, x in v.items()}

    qv = vec(_trigrams(query_text))
    scores = [sum(qv.get(g, 0.0) * x for g, x in vec(d).items()) for d in docs]
    # Explicit "ข้อ 4" / "rule 4" references win outright.
    for num in re.findall(r"(?:ข้อ(?:ปฏิบัติ(?:ตัวอย่าง)?)?|rule)\s*(\d+)", query_text, re.IGNORECASE):
        for i, p in enumerate(paras):
            if re.search(rf"(?:ข้อ(?:ปฏิบัติ(?:ตัวอย่าง)?)?|rule)\s*{num}\b", p.title, re.IGNORECASE):
                scores[i] += 10.0
    best = sorted(range(len(paras)), key=lambda i: -scores[i])[:k]
    return [paras[i] for i in sorted(best)]
