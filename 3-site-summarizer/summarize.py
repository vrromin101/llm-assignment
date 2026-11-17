"""Enter a site name (e.g. abc.com) -> get a summary of that site."""
import os, re, sys
from collections import Counter
import requests
from bs4 import BeautifulSoup


def fetch_text(site):
    url = site if site.startswith("http") else "https://" + site
    r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for t in soup(["script", "style", "noscript", "nav", "footer"]):
        t.decompose()
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
    return title, text[:12000]


def llm_summary(title, text):
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=400,
        messages=[{"role": "user",
                   "content": f"Summarize this website in 4-5 sentences.\nTitle: {title}\n\n{text}"}],
    )
    return msg.content[0].text


def fallback_summary(text, n=4):
    """Extractive summary (no API key needed)."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    words = Counter(w for w in re.findall(r"[a-z]{4,}", text.lower()))
    scored = sorted(sentences[:80], key=lambda s: -sum(words[w] for w in re.findall(r"[a-z]{4,}", s.lower())))
    return " ".join(scored[:n])


if __name__ == "__main__":
    site = sys.argv[1] if len(sys.argv) > 1 else input("Enter site name (e.g. abc.com): ").strip()
    try:
        title, text = fetch_text(site)
    except Exception as e:
        raise SystemExit(f"Could not fetch site: {e}")
    print(f"\nTitle: {title}\n")
    if os.getenv("ANTHROPIC_API_KEY"):
        print(llm_summary(title, text))
    else:
        print(fallback_summary(text))
