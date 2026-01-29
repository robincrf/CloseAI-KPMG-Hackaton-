
from typing import List, Dict

KPMG_DBNOMICS_SERIES = [
    # ──────────────────────────────────────────────────────────
    # 1. MACRO CLÉ (FRANCE & ZONE EURO)
    # ──────────────────────────────────────────────────────────
    {
        'provider': 'OECD',
        'dataset': 'QNA',
        'series': 'FRA.B1_GE.CARSA.Q',
        'name': 'PIB France (trimestriel)'
    },
    {
        'provider': 'OECD',
        'dataset': 'MEI',
        'series': 'FRA.LR.STSA.M',
        'name': 'Taux de chômage France (mensuel)'
    },
    
    # ──────────────────────────────────────────────────────────
    # 2. SENTIMENT & BUSINESS CLIMATE (Indicateurs Avancés)
    # Pour anticiper les retournements de marché (Due Diligence)
    # ──────────────────────────────────────────────────────────
    {
        'provider': 'OECD',
        'dataset': 'MEI',
        'series': 'FRA.BSC.GOLD.IXOBSA.M',
        'name': 'Confiance des entreprises France (Business Climate)'
    },

    # ──────────────────────────────────────────────────────────
    # 3. FINANCEMENT & TAUX (Crucial pour le M&A et Valo)
    # ──────────────────────────────────────────────────────────
    {
        'provider': 'OECD',
        'dataset': 'MEI',
        'series': 'FRA.IRLTLT01.ST.M',
        'name': 'Taux long terme (10 ans) France'
    },

    # ──────────────────────────────────────────────────────────
    # 4. CONSOMMATION & PRODUCTION SECTORIELLE
    # ──────────────────────────────────────────────────────────
    {
        'provider': 'OECD',
        'dataset': 'MEI',
        'series': 'FRA.SLRTTO01.IXOBSA.M',
        'name': 'Ventes de détail France (Consommation)'
    },
    {
        'provider': 'OECD',
        'dataset': 'MEI',
        'series': 'FRA.PRMNTO01.IXOBSA.M',
        'name': 'Production industrielle France (Général)'
    },
    {
        'provider': 'OECD',
        'dataset': 'MEI',
        'series': 'FRA.PRCNTO01.IXOBSA.M',
        'name': 'Production dans la Construction (Immobilier)'
    },

    # ──────────────────────────────────────────────────────────
    # 5. BENCHMARK INTERNATIONAL (USA / ALLEMAGNE)
    # ──────────────────────────────────────────────────────────
    {
        'provider': 'OECD',
        'dataset': 'QNA',
        'series': 'USA.B1_GE.CARSA.Q',
        'name': 'PIB USA (trimestriel)'
    }
]

KPMG_ADZUNA_SEARCHES: List[Dict[str, any]] = [
    
    # ──────────────────────────────────────────────────────────
    # 1. VEILLE CONCURRENTIELLE & MÉTIERS (Audit/Conseil)
    # Objectif : Surveiller le marché des talents Senior/Manager
    # ──────────────────────────────────────────────────────────
    {
        "what": "Senior Manager Audit",
        "where": "Paris",
        "results_per_page": 20,
        "endpoint_type": "search"
    },
    {
        "what": "Consultant M&A Transaction Services",
        "where": "France",
        "results_per_page": 20,
        "endpoint_type": "search"
    },
    
    # ──────────────────────────────────────────────────────────
    # 2. TRANSFORMATIONS RÈGLEMENTAIRES (ESG & Compliance)
    # Objectif : Capter la demande sur les nouveaux enjeux (CSRD)
    # ──────────────────────────────────────────────────────────
    {
        "what": "Expert Décarbonation Industrie",
        "where": "France",
        "results_per_page": 20,
        "endpoint_type": "search"
    },
    
    # ──────────────────────────────────────────────────────────
    # 3. TECHNOLOGIES DISRUPTIVES (IA & Data)
    # Objectif : Benchmarker l'adoption de l'IA chez les clients
    # ──────────────────────────────────────────────────────────
    {
        "what": "Generative AI Engineer",
        "where": "France",
        "salary_min": 60000,
        "results_per_page": 50,
        "endpoint_type": "search"
    },

    # ──────────────────────────────────────────────────────────
    # 4. ANALYSES SALARIALES (Benchmarks de marché)
    # Objectif : Fournir des données de coût salarial pour les Business Plans
    # ──────────────────────────────────────────────────────────
    {
        "what": "Expert Comptable",
        "where": "Paris",
        "endpoint_type": "histogram"
    },
    
    # ──────────────────────────────────────────────────────────
    # 5. IDENTIFICATION DE PROSPECTS (Top Recruteurs)
    # Objectif : Identifier les entreprises en hyper-croissance
    # ──────────────────────────────────────────────────────────
    {
        "what": "Digital Transformation",
        "where": "France",
        "endpoint_type": "top_companies"
    }
]

KPMG_BLUESKY_SEARCHES = {
    # ──────────────────────────────────────────────────────────
    # 1. VEILLE CONCURRENTS & ÉCOSYSTÈME (Benchmark)
    # ──────────────────────────────────────────────────────────
    "clients_concurrents": [
        "KPMG France", "KPMG Strategy",
        "Deloitte France Insights"
    ],
    
    # ──────────────────────────────────────────────────────────
    # 2. RÈGLEMENTATION & COMPLIANCE (Levier de missions)
    # ──────────────────────────────────────────────────────────
    "regulations": [
        "CSRD reporting", "taxonomie européenne",
        "pilier 2 OCDE"
    ],
    
    # ──────────────────────────────────────────────────────────
    # 3. SIGNAUX FAIBLES M&A & STARTUPS (Early Warning)
    # ──────────────────────────────────────────────────────────
    "signaux_faibles": [
        "startup seed fintech France",
        "série A levée de fonds",
        "redressement judiciaire"
    ],
    
    # ──────────────────────────────────────────────────────────
    # 4. INNOVATION MÉTIER & DISRUPTION
    # ──────────────────────────────────────────────────────────
    "innovation": [
        "IA générative audit",
        "automatisation reporting financier",
        "cloud souverain France"
    ]
}

# La logique de consolidation reste la même dans votre config.py
ALL_BLUESKY_QUERIES = []
for category, queries in KPMG_BLUESKY_SEARCHES.items():
    ALL_BLUESKY_QUERIES.extend(queries)

print(f" Configuration Bluesky : {len(ALL_BLUESKY_QUERIES)} requêtes")


KPMG_QUERIES_NEWS_API = [
    # ──────────────────────────────────────────────────────────
    # 1. M&A & MOUVEMENTS STRATÉGIQUES (Opportunités de Deal)
    # ──────────────────────────────────────────────────────────
    "mergers and acquisitions 2025 trends",
    "hostile takeover bids 2025",
    "IPO market outlook 2025",
    
    # ──────────────────────────────────────────────────────────
    # 2. RÈGLEMENTATION & RISQUES (L'angle Audit/Compliance)
    # ──────────────────────────────────────────────────────────
    "CSRD implementation challenges",
    "SEC climate disclosure ruling",
    "OECD Pillar Two global minimum tax",
    
    # ──────────────────────────────────────────────────────────
    # 3. DISRUPTION SECTORIELLE (Veille métier)
    # ──────────────────────────────────────────────────────────
    "generative AI in corporate auditing",
    "quantum computing in financial modeling",
    "supply chain resilience technology",
    
    # ──────────────────────────────────────────────────────────
    # 4. SURVEILLANCE DES CONCURRENTS (Competitive Intel)
    # ──────────────────────────────────────────────────────────
    "Deloitte annual revenue 2024 2025",
    "PwC global strategy update",
    "Accenture acquisitions digital transformation"
]

"""
SP500_TOP50_YFINANCE = [
    # --- TECH & SEMI-CONDUCTEURS ---
    "AAPL", "MSFT", "GOOGL", "NVDA", "AVGO", "ORCL", "ADBE", "CRM", "AMD", "CSCO",
    "TXN", "QCOM", "INTC", "AMAT", "MU", "LRCX", "ADI", "KLAC", "SNPS", "CDNS",
    "PANW", "FTNT", "MSI", "ANET", "ADSK", "IBM", "PLTR", "NOW", "APH", "TEL",

    # --- SERVICES FINANCIERS & BANQUES ---
    "BRK-B", "JPM", "V", "MA", "BAC", "MS", "GS", "WFC", "C", "BLK",
    "AXP", "SPGI", "MCO", "ICE", "CME", "BX", "KKR", "SCHW", "PNC", "USB",
    "TFC", "BK", "COF", "AON", "MMC", "AJG", "CB", "PGR", "ALL", "TRV",

    # --- SANTÉ & PHARMA ---
    "UNH", "LLY", "JNJ", "ABBV", "MRK", "PFE", "TMO", "ABT", "DHR", "AMGN",
    "ISRG", "ELV", "CI", "SYK", "MDT", "GILD", "VRTX", "BSX", "ZTS", "REGN",
    "BDX", "HCA", "MCK", "CVS", "COR", "IQV", "EW", "IDXX", "BIIB", "DXCM",

    # --- CONSOMMATION & RETAIL ---
    "AMZN", "WMT", "COST", "HD", "PG", "KO", "PEP", "MCD", "NKE", "LOW",
    "PM", "EL", "CL", "MO", "MDLZ", "TJX", "TGT", "DG", "DLTR", "ORLY",
    "AZO", "SBUX", "CMG", "MAR", "HLT", "BKNG", "DASH", "TSLA", "LULU", "NVR",

    # --- INDUSTRIE, ÉNERGIE & UTILITIES ---
    "XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "VLO", "NEE", "DUK",
    "SO", "D", "AEP", "SRE", "CAT", "DE", "HON", "GE", "RTX", "LMT",
    "NOC", "GD", "BA", "UPS", "UNP", "FDX", "ETN", "PH", "ITW", "EMR",
    "GEV", "TT", "WM", "RSG", "MMM", "LIN", "APD", "SHW", "CTAS", "PLD",

    # --- TÉLÉCOMS & MÉDIAS ---
    "META", "NFLX", "DIS", "TMUS", "T", "VZ", "CMCSA", "CHTR", "PARA", "WBD"


# Note : J'ai ajouté 150 tickers clés supplémentaires couvrant le mid-cap et le growth.
# Pour atteindre les 250, on complète avec les leaders sectoriels suivants :

    "VRT", "SMCI", "DECK", "STX", "WDC", "MCHP", "MPWR", "ON", "TER", "TYL",
    "FICO", "JKHY", "TRMB", "AKAM", "GEN", "NET", "DDOG", "OKTA", "ZS", "CRWD",
    "MDB", "SNOW", "TEAM", "WDAY", "SAP", "ASML", "TSM", "ARM", "SPOT", "UBER",
    "LYFT", "ABNB", "EXPE", "RCL", "CCL", "NCLH", "YUM", "DRI", "WEN", "DPZ",
    "LEN", "DHI", "PHM", "TOL", "VMC", "MLM", "EXP", "URI", "FCX", "NEM",
    "CTVA", "DOW", "CE", "EMN", "FMC", "MOS", "CF", "NTR", "ADM", "TSN",
    "K", "GIS", "SYY", "KR", "KDP", "STZ", "BF-B", "TAP", "MNST", "CELH",
    "BBY", "BURL", "ROST", "GPS", "ULTA", "EBAY", "ETSY", "RVN", "W", "F",
    "GM", "STLA", "HMC", "TM", "RIVN", "LCID", "FSLR", "ENPH", "SEDG", "RUN",
    "HAS", "MAT", "EA", "TTWO", "RBLX", "MTCH", "IAC", "NYT", "NWSA", "FOXA"
]
"""


SIREN_EXTENDED_INSEE = [
    # ──────────────────────────────────────────────────────────
    # 1. CAC 40 - LES POIDS LOURDS (Indispensable pour l'Audit)
    # ──────────────────────────────────────────────────────────
        "442395448",  # TotalEnergies
        "775670417",  # LVMH
        "954507931",  # Unibail-Rodamco-Westfield

    # ──────────────────────────────────────────────────────────
    # 2. RETAIL & GRANDE DISTRIBUTION (Benchmark sectoriel)
    # ──────────────────────────────────────────────────────────
        "428268023",  # Auchan
        "542095336",  # Leroy Merlin

    # ──────────────────────────────────────────────────────────
    # 3. FRENCH TECH & LICORNES (Cibles M&A / Growth)
    # ──────────────────────────────────────────────────────────
        "878706389",  # Doctolib
        "802174462",  # Mirakl

    # ──────────────────────────────────────────────────────────
    # 4. INFRASTRUCTURE & INDUSTRIE (Focus ESG/Décarbonation)
    # ──────────────────────────────────────────────────────────
        "552066953",  # Bouygues
        "380243956"  # Forvia (Faurecia)
    ]


SEC_TARGET_COMPANIES =[
    # ──────────────────────────────────────────────────────────
    # 1. BIG TECH & IA (Les moteurs du marché)
    # ──────────────────────────────────────────────────────────
    ("0000320193", "Apple Inc."),
    ("0001018724", "Amazon.com Inc."),
    ("0001326801", "Meta Platforms Inc."),
    ("0001045810", "NVIDIA Corp."),
    
    # ──────────────────────────────────────────────────────────
    # 2. FINANCE & PAIEMENTS (Indicateurs de consommation)
    # ──────────────────────────────────────────────────────────
    ("0000019617", "JPMorgan Chase & Co."),
    
    # ──────────────────────────────────────────────────────────
    # 3. CONSEIL & SERVICES TECH (Vos concurrents/partenaires)
    # ──────────────────────────────────────────────────────────
    ("0001467373", "Accenture PLC"), 
    # ──────────────────────────────────────────────────────────
    # 4. SANTÉ & PHARMA (Secteurs à forte marge)
    # ──────────────────────────────────────────────────────────
    ("0000200406", "Johnson & Johnson"),
    # ──────────────────────────────────────────────────────────
    # 5. INDUSTRIE, ÉNERGIE & TRANSPORT
    # ──────────────────────────────────────────────────────────
    ("0001318605", "Tesla Inc.")
]

GOOGLE_RSS_QUERIES = [
    # ──────────────────────────────────────────────────────────
    # 1. VEILLE CONCURRENTIELLE (Audit & Conseil)
    # ──────────────────────────────────────────────────────────
    "KPMG France news",
    "McKinsey insights digital transformation",
    
    # ──────────────────────────────────────────────────────────
    # 2. M&A, PRIVATE EQUITY & TRANSACTIONS (Due Diligence)
    # ──────────────────────────────────────────────────────────
    "LBO deals France",
    "Private Equity exit strategies 2025",
    "SPAC liquidation trends",
    
    # ──────────────────────────────────────────────────────────
    # 3. RÉGLEMENTATION & ESG (Le nerf de la guerre)
    # ──────────────────────────────────────────────────────────
    "CSRD reporting implementation",
    "OECD global minimum tax pillar 2",
    "anti-money laundering directive EU",
    
    # ──────────────────────────────────────────────────────────
    # 4. TECHNOLOGIES RUPTURISTES (Veille IT)
    # ──────────────────────────────────────────────────────────
    "Generative AI enterprise adoption",
    "AI Act compliance requirements",
    "edge computing industrial IoT",
    
    # ──────────────────────────────────────────────────────────
    # 5. SIGNAUX FAIBLES & RISQUES (Early Warning)
    # ──────────────────────────────────────────────────────────
    "profit warning S&P 500",
    "C-suite executive turnover",
    "insider trading investigations",
    
    # ──────────────────────────────────────────────────────────
    # 6. FOCUS SECTORIELS (Benchmarks)
    # ──────────────────────────────────────────────────────────
    "banking sector consolidation Europe",
    "luxury goods market growth China",
    "automotive transition EV strategy",
    "defense industry spending EU",
    
    # ──────────────────────────────────────────────────────────
    # 7. MACROÉCONOMIE & GÉOPOLITIQUE
    # ──────────────────────────────────────────────────────────
    "ECB interest rate forecast",
    "inflation CPI Eurozone news",
    "US-China trade relations technology"
]

PRESS_RELEASE_URLS = [
    # ──────────────────────────────────────────────────────────
    # APPLE NEWSROOM (20 articles)
    # ──────────────────────────────────────────────────────────
    "https://www.apple.com/newsroom/2025/01/apple-announces-new-ai-features/",
    "https://www.apple.com/newsroom/2025/01/apple-intelligence-expansion-europe/",
    "https://www.apple.com/newsroom/2024/12/apple-reports-q4-2024-results/",


    # ──────────────────────────────────────────────────────────
    # MICROSOFT NEWS (20 articles)
    # ──────────────────────────────────────────────────────────
    "https://news.microsoft.com/2025/01/microsoft-expands-azure-ai-global-infrastructure/",
    "https://news.microsoft.com/2025/01/microsoft-partnership-mistral-ai-2025/",
    "https://news.microsoft.com/2023/03/microsoft-future-of-work-ai/",

    # ──────────────────────────────────────────────────────────
    # GOOGLE BLOG / ALPHABET (20 articles)
    # ──────────────────────────────────────────────────────────
    "https://blog.google/technology/ai/google-gemini-2-0-flash-updates/",
    "https://blog.google/technology/ai/google-ai-agents-business-productivity/",
    "https://blog.google/technology/ai/google-gemini-pro-integration-developers/",

    # ──────────────────────────────────────────────────────────
    # META NEWSROOM (10 articles)
    # ──────────────────────────────────────────────────────────
    "https://about.fb.com/news/2025/01/meta-ai-llama-4-training-update/",
    "https://about.fb.com/news/2024/12/meta-quest-3s-sales-performance/",
    "https://about.fb.com/news/2023/09/meta-connect-2023-quest-3-launch/",

    # ──────────────────────────────────────────────────────────
    # TESLA BLOG (10 articles)
    # ──────────────────────────────────────────────────────────
    "https://www.tesla.com/blog/tesla-energy-expansion-megapack/"
]

FRED_SERIES_COMPLETE = [
    # --- CROISSANCE & PRODUCTION ---
    "GDP",              # Produit Intérieur Brut (trimestriel)
    "GDPC1",            # PIB réel (ajusté inflation)
    "JTSJOL",           # Job Openings (Offres d'emploi - Enquête JOLTS)
    
    # --- INFLATION & PRIX ---
    "CPIAUCSL",         # Indice des Prix à la Consommation (CPI)
    "CPILFESL",         # CPI Core (hors alimentation/énergie)
    "PCEPI",            # Personal Consumption Expenditures (indicateur FED préféré)
    
    # --- TAUX D'INTÉRÊT & POLITIQUE MONÉTAIRE ---
    "FEDFUNDS",         # Taux directeur de la FED (Fed Funds Rate)
    "DGS2",             # Taux obligations 2 ans (Treasury)
    "DPRIME",           # Prime Rate (taux bancaire de référence)
    
    # --- MARCHÉS FINANCIERS & VOLATILITÉ ---
    "SP500",            # Indice S&P 500
    "DJIA",             # Dow Jones Industrial Average
    "BAMLH0A0HYM2",     # ICE BofA US High Yield Index Option-Adjusted Spread
    
    # --- CONSOMMATION & CONFIANCE ---
    "PCE",              # Dépenses de consommation personnelle
    "PSAVERT",          # Taux d'épargne personnelle
    "DRCLACBS",         # Taux de défaillance sur les cartes de crédit
    
    # --- SECTEUR MANUFACTURIER & SERVICES ---
    "NAPM",             # ISM Manufacturing PMI
    "NAPMNOI",          # ISM New Orders Index
    "TCU",              # Taux d'utilisation des capacités (Capacity Utilization)
    
    # --- DETTE, DÉFICITS & MASSE MONÉTAIRE ---
    "GFDEBTN",          # Dette publique totale (Federal Debt)
    "GFDEGDQ188S",      # Dette/PIB ratio
    
    # --- COMMERCE INTERNATIONAL & LOGISTIQUE ---
    "BOPGSTB",          # Balance commerciale (biens et services)
    "IMPGS"           # Importations totales
]

#-------------------------------------------------------------------
# ──────────────────────────────────────────────────────────
# SCORE DE SÛRETÉ - FILTRAGE & FIABILITÉ DES SOURCES
# ──────────────────────────────────────────────────────────

PRIMARY_SOURCES = [
    # Gouvernementaux US (Données froides/officielles)
    "sec.gov", "federalreserve.gov", "treasury.gov", "bls.gov",
    "census.gov", "gao.gov", "cbo.gov", "bea.gov", "ftc.gov",
    
    # Gouvernementaux EU & France (Critique pour KPMG France)
    "europa.eu", "ecb.europa.eu", "eurostat.ec.europa.eu",
    "banque-france.fr", "insee.fr", "data.gouv.fr", "legifrance.gouv.fr",
    "economie.gouv.fr", "entreprises.gouv.fr",
    
    # Internationaux
    "oecd.org", "imf.org", "worldbank.org", "bis.org",
    "wto.org", "un.org", "iea.org", "who.int",
    
    # Bourses & Régulateurs (M&A et Compliance)
    "nyse.com", "nasdaq.com", "lse.co.uk", "amf-france.org",
    "euronext.com", "fca.org.uk", "esma.europa.eu", "finra.org",
    
    # Académique (Recherche & Innovation)
    ".edu", ".ac.uk", ".gouv.fr", "harvard.edu", "mit.edu", "stanford.edu",
    "polytechnique.edu", "hec.edu", "insead.edu", "nber.org",
    
    # Rapports officiels d'entreprises (Investor Relations)
    "investor.apple.com", "investor.microsoft.com", "abc.xyz/investor",
    "s2.q4cdn.com", "investors.nvidia.com", "lvmh.com/investors"
]

SECONDARY_SOURCES = [
    # Presse économique Tier 1 (Référence mondiale)
    "reuters.com", "bloomberg.com", "ft.com", "wsj.com",
    "economist.com", "forbes.com", "fortune.com", "barrons.com",
    
    # Presse généraliste & Business France
    "nytimes.com", "washingtonpost.com", "theguardian.com",
    "lemonde.fr", "lesechos.fr", "latribune.fr", "lefigaro.fr",
    "challenges.fr", "usinenouvelle.com",
    
    # Spécialisés finance/tech/stratégie
    "cnbc.com", "marketwatch.com", "seekingalpha.com", "investopedia.com",
    "techcrunch.com", "wired.com", "arstechnica.com", "theverge.com",
    "venturebeat.com", "zdnet.com",
    
    # Cabinets de conseil & Stratégie (Benchmarking)
    "mckinsey.com", "bcg.com", "bain.com", "kpmg.com", "kpmg.fr",
    "pwc.com", "ey.com", "deloitte.com", "accenture.com", "gartner.com",
    "forrester.com", "idc.com",
    
    # Think tanks & Analyse macro
    "brookings.edu", "piie.com", "rand.org", "bruegel.org", "ifri.org",
    "cfr.org", "chathamhouse.org"
]

SPAM_INDICATORS = [
    # Patterns de fraude et clickbait
    "clickbait", "scam", "spam", "fake-news", "get-rich-quick", 
    "crypto-pump", "forex-guru", "free-signals", "guaranteed-returns",
    "hot-stock-tip", "secret-method", "unusual-whales-alert",
    
    # Indicateurs de contenu IA basse qualité
    "generated-by-ai", "gpt-summary", "bot-news",
    
    # Domaines suspects ou non vérifiés
    "news-agregator-xyz.com", "cheap-marketing-tips", "press-release-free.net",
    "buy-followers", "pumping-stocks", "dark-web-links",
    
    # Mots-clés de sensationnalisme
    "shocking-revelation", "must-see-video", "anonymous-source-leak",
    "exclusive-leak-internal", "conspiracy-theory", "qanon-updates"
]