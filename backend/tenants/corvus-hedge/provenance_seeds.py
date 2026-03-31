"""Provenance seed data for investment analysis domain."""

SEED_SOURCES: tuple[dict, ...] = (
    # SEC regulations
    {"canonical_id": "SEC Regulation FD", "family": "SEC", "authority_level": "regulatory",
     "issuing_body": "SEC", "notes": "Fair Disclosure — prohibits selective disclosure of material information"},
    {"canonical_id": "SEC Regulation SHO", "family": "SEC", "authority_level": "regulatory",
     "issuing_body": "SEC", "notes": "Short sale regulation including locate and close-out requirements"},
    {"canonical_id": "SEC Form 10-K", "family": "SEC Filings", "authority_level": "regulatory",
     "issuing_body": "SEC", "notes": "Annual report — comprehensive financial and operational disclosure"},
    {"canonical_id": "SEC Form 10-Q", "family": "SEC Filings", "authority_level": "regulatory",
     "issuing_body": "SEC", "notes": "Quarterly report — interim financial statements and MD&A"},
    {"canonical_id": "SEC Form 8-K", "family": "SEC Filings", "authority_level": "regulatory",
     "issuing_body": "SEC", "notes": "Current report — material events disclosure"},
    # Accounting standards
    {"canonical_id": "FASB ASC 606", "family": "GAAP", "authority_level": "binding_standard",
     "issuing_body": "FASB", "notes": "Revenue recognition from contracts with customers"},
    {"canonical_id": "FASB ASC 842", "family": "GAAP", "authority_level": "binding_standard",
     "issuing_body": "FASB", "notes": "Lease accounting standard"},
    # Economic data
    {"canonical_id": "FRED", "family": "Economic Data", "authority_level": "informational",
     "issuing_body": "Federal Reserve Bank of St. Louis", "notes": "Federal Reserve Economic Data — macro indicators"},
    {"canonical_id": "BLS", "family": "Economic Data", "authority_level": "informational",
     "issuing_body": "Bureau of Labor Statistics", "notes": "Employment, CPI, PPI data"},
    {"canonical_id": "BEA", "family": "Economic Data", "authority_level": "informational",
     "issuing_body": "Bureau of Economic Analysis", "notes": "GDP, PCE, trade balance data"},
    # Options standards
    {"canonical_id": "OCC", "family": "Options", "authority_level": "regulatory",
     "issuing_body": "Options Clearing Corporation", "notes": "Options clearing, exercise, and settlement rules"},
    {"canonical_id": "CBOE", "family": "Options", "authority_level": "industry_practice",
     "issuing_body": "Cboe Global Markets", "notes": "VIX methodology, options exchange rules"},
)
