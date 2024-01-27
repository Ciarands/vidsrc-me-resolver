import re
import requests

from utils import Utilities
from typing import Optional, Dict

class VidsrcStreamExtractor:
    @staticmethod
    def decode_hls_url(encoded_url: str) -> str:
        def format_hls_b64(data: str) -> str:
            encoded_b64 = re.sub(r"\/@#@\/[^=\/]+==", "", data)
            if re.search(r"\/@#@\/[^=\/]+==", encoded_b64):
                return format_hls_b64(encoded_b64)
            return encoded_b64

        formatted_b64 = format_hls_b64(encoded_url[2:])
        b64_data = Utilities.decode_base64_url_safe(formatted_b64)
        return b64_data.decode("utf-8")

    def resolve_source(self, **kwargs) -> Optional[Dict]:
        req = requests.get(kwargs.get("url"), headers={"Referer": kwargs.get("referrer")})
        if req.status_code != 200:
            print(f"[VidsrcStreamExtractor] Failed to retrieve media, status code: {req.status_code}...")
            return None
        
        encoded_hls_url = re.search(r'file:"([^"]*)"', req.text)
        hls_password_url = re.search(r'var pass_path = "(.*?)";', req.text)

        if not encoded_hls_url or not hls_password_url:
            print("[VidsrcStreamExtractor] Failed to extract hls or password url...")
            return None
        
        hls_password_url = hls_password_url.group(1)
        if hls_password_url.startswith("//"):
            hls_password_url = f"https:{hls_password_url}"

        hls_url = self.decode_hls_url(encoded_hls_url.group(1))
        requests.get(hls_password_url, headers={"Referer": kwargs.get("referrer")}) # 26/01/2024 - this isnt necessary, also actual source calls this continuously

        return {
            "streams": [hls_url],
            "subtitles": {}
        }