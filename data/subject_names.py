"""data/subject_names.py - merges spelling variants of the SAME subject so classes can be compared.

Used only by the Subject Difficulty page (and the Board Report Card strengths/weak-spots).
It does not touch data/processed/*.csv or data/loader.py.
"""
import re

_GROUPS = {
    "Translation Of The Holy Quran": ["translation of the holy quran", "translation of holy quran", "tarjuma-tul-quran-ul-majeed",
                                      "tarjama tul quran ul majeed"],
    "Mutalia-E-Quran-E-Hakeem": ["mutalia-e-quran-e-hakeem", "mutala e quran hakeem", "mutalia quran", "mutaliae quran-e-hakeem",
                                 "mutaliae-quran-e-hakeem"],
    "General Mathematics": ["general mathematics", "general math", "general maths", "maths general"],
    "Computer Science": ["computer science", "computer science-i"],
    "Urdu": ["urdu", "urdu-i"],
    "Health And Physical Education": ["health and physical education", "health and phy. education", "hpe"],
    "Ethics": ["ethics", "ethics-i", "ethics for non muslims"],
    "Home Economics": ["home economics", "elements of home economics", "out line of home economics",
                       "outline of home economics", "outlines of home economics", "outlines of home-economics"],
    "Business Mathematics": ["business math", "business mathematics", "business math and statistics",
                             "business mathematics and statistics"],
    "Principles Of Accounting": ["principles of accounting", "principles of acounting"],
}
_LOOKUP = {v: k for k, vs in _GROUPS.items() for v in vs}


def unify(name) -> str:
    key = re.sub(r"\s+", " ", str(name)).strip().lower()
    return _LOOKUP.get(key, re.sub(r"\s+", " ", str(name)).strip())
