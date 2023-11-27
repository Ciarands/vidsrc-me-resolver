import os
import re
import base64
import requests

from typing import Optional
from bs4 import BeautifulSoup

class VidSrcExtractor:
    def hunter_duf(self, d, e, f) -> int:
        '''Used by self.hunter'''
        g = list("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/")
        h = g[0:e]
        i = g[0:f]
        d = list(d)[::-1]
        j = 0
        for c,b in enumerate(d):
            if b in h:
                j = j + h.index(b)*e**c
    
        k = ""
        while j > 0:
            k = i[j%f] + k
            j = (j - (j%f))//f
    
        return int(k) or 0
    
    def hunter(self, h, u, n, t, e, r) -> str:
        '''Decodes the common h,u,n,t,e,r packer'''
        r = ""
        i = 0
        while i < len(h):
            j = 0
            s = ""
            while h[i] is not n[e]:
                s = ''.join([s,h[i]])
                i = i + 1
    
            while j < len(n):
                s = s.replace(n[j],str(j))
                j = j + 1
    
            r = ''.join([r,''.join(map(chr, [self.hunter_duf(s,e,10) - t]))])
            i = i + 1
    
        return r

    def decode_src(self, encoded, seed) -> str:
        '''decodes hash found @ vidsrc.me embed page'''
        encoded_buffer = bytes.fromhex(encoded)
        decoded = ""
        for i in range(len(encoded_buffer)):
            decoded += chr(encoded_buffer[i] ^ ord(seed[i % len(seed)]))
        return decoded

    def handle_vidsrc_stream(self, url, source) -> str:
        '''Main vidsrc, get urls from here its fast'''
        req = requests.get(url, headers={"Referer": source})

        hls_url = re.search(r'file:"([^"]*)"', req.text).group(1)
        hls_url = re.sub(r'\/\/\S+?=', '', hls_url).replace('#2', '')
        hls_url = base64.b64decode(hls_url).decode('utf-8')

        set_pass = re.search(r'var pass_path = "(.*?)";', req.text).group(1)
        if set_pass.startswith("//"):
            set_pass = f"https:{set_pass}"

        requests.get(set_pass, headers={"Referer": source})
        return hls_url
    
    def handle_2embed(self, url, source) -> str:
        '''Site provides ssl error :( cannot fetch from here'''
        pass

    def handle_multiembed(self, url, source) -> str:
        '''Fallback site used by vidsrc'''
        req = requests.get(url, headers={"Referer": source})
        matches = re.search(r'escape\(r\)\)}\((.*?)\)', req.text)
        processed_values = []

        if not matches:
            raise Exception("No values found")

        for val in matches.group(1).split(','):
            val = val.strip()
            if val.isdigit() or (val[0] == '-' and val[1:].isdigit()):
                processed_values.append(int(val))
            elif val[0] == '"' and val[-1] == '"':
                processed_values.append(val[1:-1])

        unpacked = self.hunter(*processed_values)
        hls_url = re.search(r'file:"([^"]*)"', unpacked).group(1)
        return hls_url

    def get_vidsrc_stream(self, name, url) -> Optional[str]:
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "html.parser")
        sources = {attr.text: attr.get("data-hash") for attr in soup.find_all("div", {"class": "server"})}

        source = sources.get(name)
        if not source:
            print(f"No source found for {name}, available sources:", ", ".join(list(sources.keys())))
            return None

        print(f"Requesting {name}...")
        req_1 = requests.get(f"https://rcp.vidsrc.me/rcp/{source}", headers={"Referer": url})
        soup = BeautifulSoup(req_1.text, "html.parser")

        encoded = soup.find("div", {"id": "hidden"}).get("data-h")
        seed = soup.find("body").get("data-i")

        decoded_url = self.decode_src(encoded, seed)
        if decoded_url.startswith("//"):
            decoded_url = f"https:{decoded_url}"

        req_2 = requests.get(decoded_url, allow_redirects=False, headers={"Referer": f"https://rcp.vidsrc.me/rcp/{source}"})
        location = req_2.headers.get("Location")

        match location.split("/"): # i wanted to test out sequence patterns :) TODO: find and add other sources such as playhydrax.com
            case [_, _, "vidsrc.stream", *_]: 
                return self.handle_vidsrc_stream(location, f"https://rcp.vidsrc.me/rcp/{source}")
            case [_, _, "2embed.cc", *_]:
                print("[Warning] 2Embed does not work, this will not return anything!")
                return self.handle_2embed(location, f"https://rcp.vidsrc.me/rcp/{source}")
            case [_, _, "multiembed.mov", *_]:
                return self.handle_multiembed(location, f"https://rcp.vidsrc.me/rcp/{source}")

if __name__ == "__main__":
    tmdb = input("Input imdb code: ")

    # use VidSrc PRO, it has virtually everything and is super fast
    vse = VidSrcExtractor()
    movie = vse.get_vidsrc_stream("VidSrc PRO", f"https://vidsrc.me/embed/{tmdb}")
    if movie:
        os.system(f"mpv --fs {movie}")
