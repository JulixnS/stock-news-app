"""Ticker universe for the sentiment backfill.

Grouped by theme for readability; TICKERS is the flat, de-duplicated list
that callers should import.
"""

# The Magnificent 7.
MAGNIFICENT_7 = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
]

# Semiconductors, AI accelerators, and semi-cap equipment.
SEMICONDUCTORS = [
    "AMD", "INTC", "AVGO", "QCOM", "TXN", "MU", "ADI", "NXPI", "MRVL",
    "LRCX", "AMAT", "KLAC", "ASML", "TSM", "ARM", "ON", "MCHP", "SWKS",
    "MPWR", "TER", "ENTG", "ALAB", "CRDO",
]

# Cloud platforms, SaaS, and developer infrastructure.
CLOUD_SOFTWARE = [
    "CRM", "ORCL", "ADBE", "NOW", "SNOW", "DDOG", "MDB", "TEAM", "WDAY",
    "HUBS", "ZS", "CRWD", "PANW", "NET", "OKTA", "TWLO", "ESTC",
    "GTLB", "S", "PATH", "BILL", "ZM", "DBX", "FTNT", "INTU", "ADSK",
    "CDNS", "SNPS",
]

# Data-center hardware, networking, optics, and power.
DATA_CENTER = [
    "SMCI", "DELL", "HPE", "IBM", "CSCO", "ANET", "VRT", "NTAP",
    "WDC", "STX", "CIEN", "COHR", "LITE", "FN", "CLS", "MOD", "ETN",
    "PWR", "GEV", "EQIX", "DLR",
]

# Consumer internet and platform businesses.
INTERNET_PLATFORMS = [
    "NFLX", "UBER", "ABNB", "SHOP", "SPOT", "PINS", "SNAP", "RDDT",
    "DASH", "LYFT", "EBAY", "BKNG", "PYPL", "COIN", "TTD", "APP", "U",
    "RBLX", "DUOL", "MNDY", "GDDY", "AKAM", "VRSN",
]

# Non-US listings and ADRs with heavy AI/cloud exposure.
INTERNATIONAL = [
    "BABA", "BIDU", "JD", "PDD", "SE", "GRAB", "SAP", "STM", "UMC",
]

# Headline names that suffix-stripping the legal longName can't produce.
# Alphabet's products are called "Google"; Meta's are "Facebook"/"Instagram".
# Each entry is checked IN ADDITION TO the ticker and longName, so list only
# the extra trade names -- no need to repeat the legal name.
NAME_ALIASES = {
    "GOOGL": ["Google", "YouTube"],
    "META": ["Facebook", "Instagram"],
    "TSM": ["TSMC"],
    "BABA": ["Alibaba"],
    "AVGO": ["VMware"],
    "CRM": ["Salesforce"],
    "PANW": ["Palo Alto"],
    "NOW": ["ServiceNow"],
}

# Flat, de-duplicated, order-preserving.
TICKERS = list(
    dict.fromkeys(
        MAGNIFICENT_7
        + SEMICONDUCTORS
        + CLOUD_SOFTWARE
        + DATA_CENTER
        + INTERNET_PLATFORMS
        + INTERNATIONAL
    )
)


if __name__ == "__main__":
    print(f"{len(TICKERS)} tickers")
    print(TICKERS)
