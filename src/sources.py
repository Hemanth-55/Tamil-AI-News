"""Where the news comes from. Every source is free and needs no API key.

kind:
  official  - a company announcing its own news (primary source, counts as verified on its own)
  outlet    - an established newsroom (a story is verified once 2+ independent outlets report it)
  aggregate - Google News search feeds: many newsrooms, used to count independent confirmations
  learn     - tutorials and explainers
"""
OFFICIAL = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Google AI": "https://blog.google/technology/ai/rss/",
    "Microsoft AI": "https://blogs.microsoft.com/ai/feed/",
    "NVIDIA": "https://blogs.nvidia.com/feed/",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "AWS Machine Learning": "https://aws.amazon.com/blogs/machine-learning/feed/",
    "Apple Machine Learning": "https://machinelearning.apple.com/rss.xml",
}
OUTLETS = {
    "TechCrunch": "https://techcrunch.com/category/artificial-intelligence/feed/",
    "The Verge": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "MIT Technology Review": "https://www.technologyreview.com/topic/artificial-intelligence/feed",
    "Ars Technica": "https://arstechnica.com/ai/feed/",
    "VentureBeat": "https://venturebeat.com/category/ai/feed/",
    "Wired": "https://www.wired.com/feed/tag/ai/latest/rss",
    "The Decoder": "https://the-decoder.com/feed/",
}
# Google News search feeds pull Reuters, Bloomberg, CNBC, AP and others; each item names its publisher
AGGREGATE = {
    "Google News · OpenAI": "https://news.google.com/rss/search?q=OpenAI+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News · Anthropic": "https://news.google.com/rss/search?q=Anthropic+Claude+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News · Google AI": "https://news.google.com/rss/search?q=Google+Gemini+OR+DeepMind+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News · Meta AI": "https://news.google.com/rss/search?q=%22Meta%22+AI+Llama+OR+Zuckerberg+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News · AI": "https://news.google.com/rss/search?q=%22artificial+intelligence%22+OR+%22AI+model%22+when:1d&hl=en-US&gl=US&ceid=US:en",
    "Google News · labs": "https://news.google.com/rss/search?q=OpenAI+OR+Anthropic+OR+Gemini+OR+%22Meta+AI%22+OR+Nvidia+OR+xAI+OR+Mistral+when:1d&hl=en-US&gl=US&ceid=US:en",
}
LEARN = {
    "Hugging Face blog": "https://huggingface.co/blog/feed.xml",
    "Simon Willison": "https://simonwillison.net/atom/everything/",
    "Google Developers": "https://developers.googleblog.com/feeds/posts/default",
}
HN = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=60"
HF_TRENDING = "https://huggingface.co/api/models?sort=trendingScore&direction=-1&limit=8"

# publishers we trust as independent confirmations when they appear inside Google News items
TRUSTED = {"reuters", "bloomberg", "associated press", "ap news", "cnbc", "the verge", "techcrunch", "wired",
           "ars technica", "mit technology review", "financial times", "the wall street journal", "wsj",
           "the new york times", "bbc", "the guardian", "axios", "the information", "venturebeat", "zdnet",
           "engadget", "the decoder", "fortune", "business insider", "forbes", "cnn", "semafor", "politico",
           "nature", "science", "ieee spectrum", "fast company", "the register", "9to5google", "9to5mac", "cnet"}

AI_WORDS = ("ai", "a.i.", "artificial intelligence", "llm", "gpt", "chatgpt", "openai", "anthropic", "claude", "gemini",
            "deepmind", "llama", "mistral", "nvidia", "copilot", "machine learning", "neural", "model", "agent",
            "agi", "xai", "grok", "deepseek", "qwen", "hugging face", "diffusion", "robot", "chip", "gpu", "inference")

# the companies that run AI: stories about them are ranked first and can trigger breaking alerts
COMPANIES = {
    "OpenAI": ("openai", "chatgpt", "gpt-", "sam altman", "sora", "codex"),
    "Anthropic": ("anthropic", "claude", "dario amodei"),
    "Google": ("google", "gemini", "deepmind", "alphabet", "sundar pichai", "demis hassabis"),
    "Meta": ("meta ", "meta's", "llama", "zuckerberg"),
    "Microsoft": ("microsoft", "copilot", "satya nadella", "azure"),
    "NVIDIA": ("nvidia", "jensen huang", "blackwell", "cuda"),
    "Apple": ("apple intelligence", "apple ", "apple's", "siri"),
    "Amazon": ("amazon", "aws", "alexa", "bedrock"),
    "xAI": ("xai", "grok"),
    "DeepSeek": ("deepseek",),
    "Mistral": ("mistral",),
}

# official YouTube channels (free RSS; channel ids are looked up from the handle at run time)
YOUTUBE = {"OpenAI": "@OpenAI", "Anthropic": "@anthropic-ai", "Google DeepMind": "@googledeepmind",
           "Google for Developers": "@GoogleDevelopers", "NVIDIA": "@NVIDIA", "Microsoft": "@Microsoft",
           "Meta AI": "@AIatMeta", "Hugging Face": "@HuggingFace"}

# AI in sport: kept for the career section
SPORTS_AI = "https://news.google.com/rss/search?q=%22sports+analytics%22+OR+%22AI%22+%28NBA+OR+NFL+OR+MLB+OR+NHL+OR+cricket%29+when:3d&hl=en-US&gl=US&ceid=US:en"

# ------------------------------------------------------------------ sports business (added 2026-11-25)
# Hemi is building a career as a sports-industry advisor: the money, deals and decisions behind sport,
# in the US, India and European football. Broad league searches, then kept only when the headline is about business
# and the publisher is trusted.
_G = "https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q="
SPORTS_BIZ = {
    "US": _G + "NFL+OR+NBA+OR+MLB+OR+NHL+OR+MLS+OR+WNBA+OR+NCAA+OR+%22sports+business%22+when:2d",
    "INDIA": _G + "IPL+OR+BCCI+OR+%22Indian+Super+League%22+OR+%22Pro+Kabaddi%22+OR+%22Indian+sports%22+when:2d",
    "EUROPE": _G + "%22Premier+League%22+OR+UEFA+OR+%22La+Liga%22+OR+Bundesliga+OR+%22Serie+A%22+OR+%22Champions+League%22+when:2d",
}
BIZ_WORDS = ("revenue", "rights", "deal", "sponsor", "valuation", "valued", "takeover", "invest", "stake", "owner",
             "ownership", "sale", "sells", "buy", "billion", "million", "bn", "£", "€", "$", "auction", "finance",
             "financial", "profit", "loss", "broadcast", "streaming", "media", "stadium", "arena", "partnership",
             "brand", "regulator", "salary cap", "betting", "private equity", "fund", "ipo", "lockout", "cba",
             "expansion", "franchise", "commercial", "ticket", "economics", "business", "acquire", "acquisition", "merger")
SPORTS_TRUSTED = {"sportico", "sports business journal", "front office sports", "the athletic", "espn", "espncricinfo",
                  "cricbuzz", "bbc", "bbc sport", "sky sports", "the guardian", "reuters", "bloomberg", "financial times",
                  "the new york times", "the wall street journal", "wsj", "cnbc", "forbes", "associated press", "ap news",
                  "sportcal", "sportbusiness", "sportspro", "off the pitch", "the economic times", "mint", "livemint",
                  "business standard", "the hindu", "the indian express", "hindustan times", "times of india",
                  "moneycontrol", "the times of india", "yahoo sports", "axios", "the times", "the telegraph",
                  "football365", "insidesport", "inside sport", "sports illustrated", "cbs sports", "nbc sports",
                  "the business of sports", "boardroom", "variety", "deadline", "the hollywood reporter"}
