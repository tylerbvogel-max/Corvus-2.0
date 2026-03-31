"""Known apps for Corvus screen watcher — personal workstation (all screens)."""

KNOWN_APPS: tuple[tuple[str, str, str], ...] = (
    # Data Engineering
    ("databricks", "Databricks", "Data engineering, analytics, and ML platform"),
    ("spark_ui", "Spark UI", "Apache Spark job monitoring and debugging"),
    ("github", "GitHub", "Code repository and CI/CD"),
    ("vscode", "VS Code", "Code editor and development environment"),
    ("dbt", "dbt", "Data transformation and modeling tool"),
    # SAP
    ("sap_byd", "SAP Business ByDesign", "Cloud ERP — current production system"),
    ("sap_s4hana", "SAP S/4HANA", "On-premise/cloud ERP — reference knowledge"),
    ("sap_fiori", "SAP Fiori", "SAP HTML5 application framework and launchpad"),
    ("sap_analytics", "SAP Analytics Cloud", "Business intelligence and planning"),
    # Manufacturing
    ("synchrono", "Synchrono SyncManufacturing", "Advanced Planning and Scheduling system"),
    # Collaboration
    ("teams", "Microsoft Teams", "Team messaging and collaboration"),
    ("outlook", "Microsoft Outlook", "Email client"),
    ("jira", "Jira", "Issue tracking and project management"),
    ("confluence", "Confluence", "Documentation and knowledge base"),
    # General
    ("excel", "Microsoft Excel", "Spreadsheets and data analysis"),
    ("terminal", "Terminal", "Command line interface"),
    ("browser", "Web Browser", "General web browsing and research"),
)
