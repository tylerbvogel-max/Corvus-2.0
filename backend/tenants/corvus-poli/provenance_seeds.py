"""Provenance seed data for presidential behavioral modeling."""

SEED_SOURCES: list[dict] = [
    # Primary sources — direct presidential communications
    {"canonical_id": "Truth Social", "family": "Social Media", "authority_level": "primary", "issuing_body": "President", "notes": "Direct presidential posts on Truth Social (2022-present)"},
    {"canonical_id": "Twitter Archive", "family": "Social Media", "authority_level": "primary", "issuing_body": "President", "notes": "Complete Twitter archive (2009-2021, ~60,000 tweets)"},
    {"canonical_id": "Executive Orders", "family": "Official Acts", "authority_level": "primary", "issuing_body": "White House", "notes": "Signed executive orders, both terms"},
    {"canonical_id": "Presidential Memoranda", "family": "Official Acts", "authority_level": "primary", "issuing_body": "White House", "notes": "Presidential memoranda and proclamations"},
    {"canonical_id": "Press Conferences", "family": "Transcripts", "authority_level": "primary", "issuing_body": "White House", "notes": "Official press conference transcripts"},
    {"canonical_id": "Rally Transcripts", "family": "Transcripts", "authority_level": "primary", "issuing_body": "Campaign/President", "notes": "Campaign and presidential rally transcripts"},
    {"canonical_id": "State of the Union", "family": "Transcripts", "authority_level": "primary", "issuing_body": "White House", "notes": "SOTU and joint session addresses"},
    {"canonical_id": "UN Addresses", "family": "Transcripts", "authority_level": "primary", "issuing_body": "White House", "notes": "UN General Assembly speeches"},
    {"canonical_id": "Debate Transcripts", "family": "Transcripts", "authority_level": "primary", "issuing_body": "Commission on Presidential Debates", "notes": "2016, 2020, 2024 debate transcripts"},
    # Secondary sources — behavioral context
    {"canonical_id": "Art of the Deal", "family": "Published Works", "authority_level": "secondary", "issuing_body": "Donald Trump / Tony Schwartz", "notes": "1987 book; foundational negotiation philosophy"},
    {"canonical_id": "Crippled America", "family": "Published Works", "authority_level": "secondary", "issuing_body": "Donald Trump", "notes": "2015 book; policy positions pre-presidency"},
    {"canonical_id": "Interview Transcripts", "family": "Transcripts", "authority_level": "secondary", "issuing_body": "Various Media", "notes": "Major TV/print interview transcripts"},
    # Tertiary sources — observer accounts
    {"canonical_id": "Woodward Books", "family": "Journalist Accounts", "authority_level": "tertiary", "issuing_body": "Bob Woodward", "notes": "Fear (2018), Rage (2020), Peril (2021), War (2024)"},
    {"canonical_id": "Bolton Memoir", "family": "Insider Accounts", "authority_level": "tertiary", "issuing_body": "John Bolton", "notes": "The Room Where It Happened (2020)"},
    {"canonical_id": "Mattis Accounts", "family": "Insider Accounts", "authority_level": "tertiary", "issuing_body": "Various", "notes": "Reported accounts of Defense Secretary tenure"},
    # Outcome data
    {"canonical_id": "Federal Register", "family": "Official Record", "authority_level": "primary", "issuing_body": "U.S. Government", "notes": "Official record of executive orders and rules"},
    {"canonical_id": "Congressional Record", "family": "Official Record", "authority_level": "primary", "issuing_body": "U.S. Congress", "notes": "Legislative actions and presidential statements"},
]
