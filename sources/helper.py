import re

# Legal-entity noise that appears in yfinance longName but never in headlines.
_SUFFIX = r"(?:Inc|Corp|Corporation|Company|Co|Ltd|Limited|plc|LLC|LP|Holdings|Group|New|AG|SE|NV|SA)"


def strip_company_suffix(name: str) -> str:
    """"Apple Inc." -> "Apple". Idempotent, so it is safe to apply twice."""
    if not name:
        return name

    s = re.sub(r"^The\s+", "", name.strip(), flags=re.I)
    s = re.sub(r"\(The\)$", "", s).strip()

    # Loop: "Berkshire Hathaway Inc. New" needs two passes.
    prev = None
    while prev != s:
        prev = s
        s = re.sub(rf",?\s+{_SUFFIX}\.?$", "", s, flags=re.I).strip()

    # "JPMorgan Chase & Co." leaves a dangling "&" once "Co." is gone.
    s = s.rstrip(" ,.&-")

    return s or name


def _name_matches(title: str, name: str) -> bool:
    """True if `title` names the company `name`, trying the full alias and
    its leading token.

    Headlines shorten names past what suffix-stripping catches: the legal
    "Amazon.com, Inc." and "Micron Technology, Inc." appear in headlines as
    plain "Amazon" and "Micron". So beyond the stripped alias we also try its
    leading token ("Amazon.com" -> "Amazon", "Micron Technology" -> "Micron").

    The leading token is gated at 4+ chars so short, word-like fragments
    ("Sea", "ON") can't match ordinary prose. It stays a widening heuristic,
    though -- a generic first word ("Advanced", "Applied", "Taiwan") can still
    over-match; NAME_ALIASES is the precise lever for those.
    """
    if not name:
        return False

    alias = strip_company_suffix(name)
    if not alias:
        return False

    candidates = {alias}
    lead = re.match(r"[A-Za-z0-9]+", alias)
    if lead and len(lead.group()) >= 4 and lead.group().lower() != alias.lower():
        candidates.add(lead.group())

    # Case-insensitive: headlines vary between "Apple", "APPLE", "apple".
    return any(
        re.search(rf"(?<!\w){re.escape(c)}(?!\w)", title, re.I) for c in candidates
    )


def title_contains(title: str, ticker: str, name=None) -> bool:
    """True if the title names this company, by ticker or by company name.

    `name` takes yfinance's raw longName ("Apple Inc."), a bare alias
    ("Apple"), or an iterable of such names -- the suffix is stripped from
    each. Pass several when a company trades under names its legal longName
    doesn't contain (Alphabet's products are called "Google").

    Lookarounds instead of \\b: \\b can't sit next to a non-word character,
    so it silently fails on aliases like "Amazon.com" or "AT&T".
    """
    if not title:
        return False

    # Case-sensitive: tickers are uppercase in headlines, so this keeps
    # word-tickers (ALL, T, ON, V) from matching ordinary prose.
    if ticker and re.search(rf"(?<!\w){re.escape(ticker)}(?!\w)", title):
        return True

    if name:
        names = [name] if isinstance(name, str) else name
        return any(_name_matches(title, n) for n in names)

    return False
