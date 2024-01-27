import os
import requests

from utils import Utilities
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from typing import Optional, Tuple, Dict

from sources.superembed import MultiembedExtractor
from sources.vidsrcpro import VidsrcStreamExtractor

SUPPORTED_SOURCES = ["VidSrc PRO", "Superembed"]

class VidsrcMeExtractor:
    BASE_URL : str = "https://vidsrc.me" # vidsrc.me / vidsrc.in / vidsrc.pm / vidsrc.xyz / vidsrc.net
    RCP_URL : str = "https://rcp.vidsrc.me/rcp"

    def __init__(self, **kwargs) -> None:
        self.source_name = kwargs.get("source_name")
        self.fetch_subtitles = kwargs.get("fetch_subtitles")

    def get_sources(self, url: str) -> Tuple[Dict, str]:
        print(f"[>] Requesting {url}...")
        req = requests.get(url)

        if req.status_code != 200:
            print(f"[VidSrcExtractor] Couldnt fetch \"{req.url}\", status code: {req.status_code}\n[VidSrcExtractor] \"{self.BASE_URL}\" likely doesnt have the requested media...")
            return {}, f"https://{urlparse(req.url).hostname}/"
        
        soup = BeautifulSoup(req.text, "html.parser")
        return {source.text: source.get("data-hash") for source in soup.find_all("div", {"class", "server"}) if source.text and source.get("data-hash")}, f"https://{urlparse(req.url).hostname}/"
    
    def get_source(self, hash: str, referrer: str) -> Tuple[Optional[str], str]:
        url = f"{self.RCP_URL}/{hash}"
        print("[>] Requesting RCP domain...")

        req = requests.get(url, headers={"Referer": referrer})
        if req.status_code != 200:
            print(f"[VidSrcExtractor] Couldnt fetch \"{url}\", status code: {req.status_code}")
            return None, url

        soup = BeautifulSoup(req.text, "html.parser")
        encoded = soup.find("div", {"id": "hidden"}).get("data-h")
        seed = soup.find("body").get("data-i") # this is just the imdb id - the "tt" lol

        source = Utilities.decode_src(encoded, seed)
        if source.startswith("//"):
            source = f"https:{source}"

        return source, url
    
    def get_source_url(self, url: str, referrer: str) -> Optional[str]:
        print("[>] Requesting source url...")
        req = requests.get(url, allow_redirects=False, headers={"Referer": referrer})
        if req.status_code != 302:
            print(f"[VidSrcExtractor] Couldnt find redirect for \"{url}\", status code: {req.status_code}")
            return None
        
        return req.headers.get("location")

    def get_streams(self, media_id: str, season: Optional[str], episode: Optional[str]) -> Optional[Dict]:
        url = f"{self.BASE_URL}/embed/{media_id}"
        if season and episode:
            url += f"/{season}-{episode}/"

        sources, sources_referrer = self.get_sources(url)
        source = sources.get(self.source_name)
        if not source:
            available_sources = ", ".join(list(sources.keys()))
            print(f"[VidSrcExtractor] No source found for \"{self.source_name}\"\nAvailable Sources: {available_sources}")
            return None

        source_url, source_url_referrer = self.get_source(source, sources_referrer)
        if not source_url:
            print(f"[VidSrcExtractor] Could not retrieve source url, please check you can request \"{url}\", if this issue persists please open an issue.")
            return None
        
        final_source_url = self.get_source_url(source_url, source_url_referrer)
        if "vidsrc.stream" in final_source_url:
            print(f"[>] Fetching source for \"{self.source_name}\"...")

            extractor = VidsrcStreamExtractor()
            return extractor.resolve_source(url=source_url, referrer=source_url_referrer)
        
        elif "multiembed.mov" in final_source_url:
            extractor = MultiembedExtractor()
            return extractor.resolve_source(url=source_url, referrer=source_url_referrer)
        
        return None

if __name__ == "__main__":
    default_language = "English"
    print("Supported sources -")
    for i, v in enumerate(SUPPORTED_SOURCES, start=1):
        print(f"{i} - {v}")

    source_index = (int(input("Select Source: ")) - 1) % len(SUPPORTED_SOURCES)
    media_id = input("Input imdb/tmdb code: ")

    vse = VidsrcMeExtractor(
        source_name=SUPPORTED_SOURCES[source_index],
        fetch_subtitles=True
    )

    stream_data = vse.get_streams(
        media_id=media_id,
        season=None,
        episode=None
    )

    if stream_data and stream_data.get("streams"):
        stream = stream_data["streams"][0]
        mpv_cmd = f"mpv \"{stream}\" "
        subtitle = stream_data["subtitles"].get(default_language) if stream_data.get("subtitles") else None
        if subtitle: 
            mpv_cmd += f"--sub-file=\"{subtitle}\""

        print("[>] Done!")
        os.system(mpv_cmd)