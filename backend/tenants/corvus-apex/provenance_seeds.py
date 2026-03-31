"""Provenance seed data for aerospace domain."""

SEED_SOURCES: list[dict] = [
    # FAR family
    {"canonical_id": "FAR", "family": "FAR", "authority_level": "regulatory", "issuing_body": "GSA/DoD/NASA", "notes": "Federal Acquisition Regulation"},
    {"canonical_id": "FAR 31", "family": "FAR", "authority_level": "regulatory", "issuing_body": "GSA/DoD/NASA", "notes": "Contract Cost Principles and Procedures"},
    {"canonical_id": "FAR 31.205", "family": "FAR", "authority_level": "regulatory", "issuing_body": "GSA/DoD/NASA", "notes": "Selected Costs"},
    {"canonical_id": "FAR 52", "family": "FAR", "authority_level": "regulatory", "issuing_body": "GSA/DoD/NASA", "notes": "Solicitation Provisions and Contract Clauses"},
    # DFARS
    {"canonical_id": "DFARS", "family": "DFARS", "authority_level": "regulatory", "issuing_body": "DoD", "notes": "Defense Federal Acquisition Regulation Supplement"},
    {"canonical_id": "DFARS 252", "family": "DFARS", "authority_level": "regulatory", "issuing_body": "DoD", "notes": "DFARS Contract Clauses"},
    # AS standards
    {"canonical_id": "AS9100D", "family": "AS", "authority_level": "industry_practice", "issuing_body": "SAE International", "notes": "Quality Management Systems - Requirements for Aviation, Space, and Defense"},
    {"canonical_id": "AS9102", "family": "AS", "authority_level": "industry_practice", "issuing_body": "SAE International", "notes": "First Article Inspection"},
    {"canonical_id": "AS9110", "family": "AS", "authority_level": "industry_practice", "issuing_body": "SAE International", "notes": "Quality Management Systems for Aviation Maintenance"},
    {"canonical_id": "AS6081", "family": "AS", "authority_level": "industry_practice", "issuing_body": "SAE International", "notes": "Counterfeit Parts Prevention"},
    # MIL-STD
    {"canonical_id": "MIL-STD-882E", "family": "MIL-STD", "authority_level": "binding_standard", "issuing_body": "DoD", "notes": "System Safety"},
    {"canonical_id": "MIL-STD-1472", "family": "MIL-STD", "authority_level": "binding_standard", "issuing_body": "DoD", "notes": "Human Engineering"},
    {"canonical_id": "MIL-STD-810G", "family": "MIL-STD", "authority_level": "binding_standard", "issuing_body": "DoD", "notes": "Environmental Engineering Considerations and Laboratory Tests"},
    {"canonical_id": "MIL-STD-461G", "family": "MIL-STD", "authority_level": "binding_standard", "issuing_body": "DoD", "notes": "EMI/EMC Requirements"},
    # DO standards
    {"canonical_id": "DO-178C", "family": "DO", "authority_level": "industry_practice", "issuing_body": "RTCA", "notes": "Software Considerations in Airborne Systems and Equipment Certification"},
    {"canonical_id": "DO-254", "family": "DO", "authority_level": "industry_practice", "issuing_body": "RTCA", "notes": "Design Assurance Guidance for Airborne Electronic Hardware"},
    {"canonical_id": "DO-160G", "family": "DO", "authority_level": "industry_practice", "issuing_body": "RTCA", "notes": "Environmental Conditions and Test Procedures for Airborne Equipment"},
    # ISO
    {"canonical_id": "ISO 9001", "family": "ISO", "authority_level": "industry_practice", "issuing_body": "ISO", "notes": "Quality Management Systems"},
    {"canonical_id": "ISO 14001", "family": "ISO", "authority_level": "industry_practice", "issuing_body": "ISO", "notes": "Environmental Management Systems"},
    {"canonical_id": "ISO 27001", "family": "ISO", "authority_level": "industry_practice", "issuing_body": "ISO", "notes": "Information Security Management"},
    # NIST
    {"canonical_id": "NIST SP 800-171", "family": "NIST", "authority_level": "regulatory", "issuing_body": "NIST", "notes": "Protecting CUI in Nonfederal Systems"},
    {"canonical_id": "NIST SP 800-53", "family": "NIST", "authority_level": "regulatory", "issuing_body": "NIST", "notes": "Security and Privacy Controls"},
    # ITAR/EAR
    {"canonical_id": "ITAR", "family": "ITAR", "authority_level": "regulatory", "issuing_body": "State Department/DDTC", "notes": "International Traffic in Arms Regulations"},
    {"canonical_id": "EAR", "family": "EAR", "authority_level": "regulatory", "issuing_body": "Commerce Department/BIS", "notes": "Export Administration Regulations"},
    # CMMC
    {"canonical_id": "CMMC", "family": "CMMC", "authority_level": "regulatory", "issuing_body": "DoD", "notes": "Cybersecurity Maturity Model Certification"},
    # SAE
    {"canonical_id": "SAE AMS", "family": "SAE", "authority_level": "industry_practice", "issuing_body": "SAE International", "notes": "Aerospace Material Specifications"},
    # NADCAP
    {"canonical_id": "NADCAP", "family": "NADCAP", "authority_level": "industry_practice", "issuing_body": "PRI", "notes": "National Aerospace and Defense Contractors Accreditation Program"},
    # OSHA
    {"canonical_id": "OSHA", "family": "OSHA", "authority_level": "regulatory", "issuing_body": "Department of Labor", "notes": "Occupational Safety and Health Standards"},
    # ASTM
    {"canonical_id": "ASTM", "family": "ASTM", "authority_level": "industry_practice", "issuing_body": "ASTM International", "notes": "Standard Test Methods and Specifications"},
    # CFR
    {"canonical_id": "CFR", "family": "CFR", "authority_level": "regulatory", "issuing_body": "Federal Government", "notes": "Code of Federal Regulations"},
]
