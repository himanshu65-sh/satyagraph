import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "satyagraph_live.db")

    # Primary model configured to Gemini 3.5 Flash Lite
    GEMINI_MODEL = "gemini-3.5-flash-lite"
    GEMINI_FALLBACK_MODELS = [
        "gemini-3.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-1.5-flash"
    ]
    GROQ_MODEL = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Runtime toggle to let teams demonstrate Groq Failover live on stage
    FORCE_GROQ_FAILOVER = False

    # 100% Live Public Civic & Fact-Check RSS Feeds (Zero Static/Dummy Data)
    LIVE_FEEDS = {
        "PIB & Gov Notifications (Live Google News RSS)": "https://news.google.com/rss/search?q=site:pib.gov.in+OR+%22PIB+Fact+Check%22+OR+%22Government+of+India%22&hl=en-IN&gl=IN&ceid=IN:en",
        "India Fact-Check & Viral Claims (Live RSS)": "https://news.google.com/rss/search?q=%22fact+check%22+India+OR+fake+news+viral&hl=en-IN&gl=IN&ceid=IN:en",
        "Civic Infrastructure & Policy Updates (Live RSS)": "https://news.google.com/rss/search?q=India+policy+scheme+ministry+notification&hl=en-IN&gl=IN&ceid=IN:en",
    }

    HEADERS = {
        "User-Agent": "SatyaGraphCivicAuditor/1.0 (ForgeBuildathon; +https://github.com/satyagraph)"
    }