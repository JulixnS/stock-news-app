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


def title_contains(title: str, ticker: str, name: str | None = None) -> bool:
    """True if the title names this company, by ticker or by company name.

    `name` takes yfinance's raw longName ("Apple Inc.") or a bare alias
    ("Apple") -- the suffix is stripped here either way.

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
        alias = strip_company_suffix(name)
        # Case-insensitive: headlines vary between "Apple", "APPLE", "apple".
        if alias and re.search(rf"(?<!\w){re.escape(alias)}(?!\w)", title, re.I):
            return True

    return False
