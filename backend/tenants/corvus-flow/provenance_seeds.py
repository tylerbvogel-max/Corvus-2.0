"""Provenance seed data for plumbing domain."""

SEED_SOURCES: list[dict] = [
    # Plumbing codes
    {"canonical_id": "IPC", "family": "IPC", "authority_level": "binding_standard", "issuing_body": "ICC", "notes": "International Plumbing Code"},
    {"canonical_id": "UPC", "family": "UPC", "authority_level": "binding_standard", "issuing_body": "IAPMO", "notes": "Uniform Plumbing Code"},
    {"canonical_id": "IFGC", "family": "IFGC", "authority_level": "binding_standard", "issuing_body": "ICC", "notes": "International Fuel Gas Code"},
    {"canonical_id": "IRC-P", "family": "IRC", "authority_level": "binding_standard", "issuing_body": "ICC", "notes": "International Residential Code — Plumbing chapters"},
    # NFPA
    {"canonical_id": "NFPA 13", "family": "NFPA", "authority_level": "binding_standard", "issuing_body": "NFPA", "notes": "Installation of Sprinkler Systems"},
    {"canonical_id": "NFPA 13D", "family": "NFPA", "authority_level": "binding_standard", "issuing_body": "NFPA", "notes": "Sprinkler Systems in One- and Two-Family Dwellings"},
    {"canonical_id": "NFPA 54", "family": "NFPA", "authority_level": "binding_standard", "issuing_body": "NFPA", "notes": "National Fuel Gas Code"},
    # Product standards
    {"canonical_id": "ASSE 1010", "family": "ASSE", "authority_level": "industry_practice", "issuing_body": "ASSE International", "notes": "Water Hammer Arresters"},
    {"canonical_id": "ASSE 1013", "family": "ASSE", "authority_level": "industry_practice", "issuing_body": "ASSE International", "notes": "Reduced Pressure Principle Backflow Preventers"},
    {"canonical_id": "ASSE 1016", "family": "ASSE", "authority_level": "industry_practice", "issuing_body": "ASSE International", "notes": "Automatic Compensating Valves for Individual Fixture Fittings"},
    {"canonical_id": "ASSE 1017", "family": "ASSE", "authority_level": "industry_practice", "issuing_body": "ASSE International", "notes": "Temperature Actuated Mixing Valves for Hot Water Distribution"},
    # NSF standards
    {"canonical_id": "NSF/ANSI 61", "family": "NSF", "authority_level": "industry_practice", "issuing_body": "NSF International", "notes": "Drinking Water System Components — Health Effects"},
    {"canonical_id": "NSF/ANSI 372", "family": "NSF", "authority_level": "industry_practice", "issuing_body": "NSF International", "notes": "Drinking Water System Components — Lead Content"},
    # Federal regulations
    {"canonical_id": "SDWA 1417", "family": "EPA", "authority_level": "regulatory", "issuing_body": "EPA", "notes": "Safe Drinking Water Act — Lead-Free Requirements"},
    {"canonical_id": "EPA WaterSense", "family": "EPA", "authority_level": "regulatory", "issuing_body": "EPA", "notes": "Water Efficiency Labeling Program"},
    # OSHA
    {"canonical_id": "OSHA 1926 Subpart P", "family": "OSHA", "authority_level": "regulatory", "issuing_body": "Department of Labor", "notes": "Excavation Safety Standards"},
    {"canonical_id": "OSHA 1910.146", "family": "OSHA", "authority_level": "regulatory", "issuing_body": "Department of Labor", "notes": "Permit-Required Confined Spaces"},
    # Material standards
    {"canonical_id": "ASTM D2564", "family": "ASTM", "authority_level": "industry_practice", "issuing_body": "ASTM International", "notes": "PVC Solvent Cement"},
    {"canonical_id": "ASTM D2235", "family": "ASTM", "authority_level": "industry_practice", "issuing_body": "ASTM International", "notes": "ABS Solvent Cement"},
    {"canonical_id": "ASTM B828", "family": "ASTM", "authority_level": "industry_practice", "issuing_body": "ASTM International", "notes": "Solder Joint Procedures for Copper Tube"},
    # CFR
    {"canonical_id": "CFR", "family": "CFR", "authority_level": "regulatory", "issuing_body": "Federal Government", "notes": "Code of Federal Regulations"},
]
