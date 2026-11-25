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
