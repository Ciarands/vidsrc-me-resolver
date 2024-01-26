import re
import requests

from utils import Utilities
from typing import Optional, Dict, List

class MultiembedExtractor:
    @staticmethod
    def process_hunter_args(hunter_args: str) -> List:
        hunter_args = re.search(r"^\"(.*?)\",(.*?),\"(.*?)\",(.*?),(.*?),(.*?)$", hunter_args)
        processed_matches = list(hunter_args.groups())
        processed_matches[0] = str(processed_matches[0])
        processed_matches[1] = int(processed_matches[1])
        processed_matches[2] = str(processed_matches[2])
        processed_matches[3] = int(processed_matches[3])
        processed_matches[4] = int(processed_matches[4])
        processed_matches[5] = int(processed_matches[5])
        return processed_matches

    def resolve_source(self, **kwargs) -> Optional[Dict]:
        req = requests.get(kwargs.get("url"), headers={"Referer": kwargs.get("referrer")})
        if req.status_code != 200:
            print(f"[MultiembedExtractor] Failed to retrieve media, status code: {req.status_code}...")
            return None
        
        hunter_args = re.search(r"eval\(function\(h,u,n,t,e,r\).*?}\((.*?)\)\)", req.text) # magecart moment
        if not hunter_args:
            print(f"[MultiembedExtractor] Failed to retrieve media, could not find eval function...")
            return None
        
        processed_hunter_args = self.process_hunter_args(hunter_args.group(1))
        unpacked = Utilities.hunter(*processed_hunter_args)

        subtitles = {}
        hls_urls = re.findall(r"file:\"([^\"]*)\"", unpacked)
        subtitle_match = re.search(r"subtitle:\"([^\"]*)\"", unpacked)

        if not hls_urls:
            print("[MultiembedExtractor] Failed to extract hls or password url...")
            return None

        if subtitle_match:
            for subtitle in subtitle_match.group(1).split(","):
                subtitle_data = re.search(r"^\[(.*?)\](.*$)", subtitle)
                if not subtitle_data:
                    continue
                subtitles.update({subtitle_data.group(1): subtitle_data.group(2)})
        
        return {
            "streams": hls_urls,
            "subtitles": subtitles,
        }