"""Explicit online maintenance command. Normal extract/build never accesses network."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'assets/vendor'
URLS={
 'd3.js':'https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js',
 'markmap.js':'https://cdn.jsdelivr.net/npm/markmap-view@0.18.12/dist/browser/index.js',
 'katex.js':'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.js',
 'katex.css':'https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/katex.min.css',
 'LICENSE-d3.txt':'https://cdn.jsdelivr.net/npm/d3@7.9.0/LICENSE',
 'LICENSE-markmap.txt':'https://cdn.jsdelivr.net/npm/markmap-view@0.18.12/LICENSE',
 'LICENSE-katex.txt':'https://cdn.jsdelivr.net/npm/katex@0.16.22/LICENSE',
}
def main():
    for name,url in URLS.items():
        path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(urllib.request.urlopen(url,timeout=60).read())
    css=(ROOT/'katex.css').read_text(encoding='utf-8')
    for name in sorted(set(re.findall(r'url\((fonts/[^)]+)\)',css))):
        URLS[name]='https://cdn.jsdelivr.net/npm/katex@0.16.22/dist/'+name
        path=ROOT/name;path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(urllib.request.urlopen(URLS[name],timeout=60).read())
    manifest={'versions':{'d3':'7.9.0','markmap-view':'0.18.12','katex':'0.16.22'},
      'files':[{'file':name,'url':url,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()} for name,url in URLS.items()]}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Downloaded and recorded',len(URLS),'files. Review changes before distributing.')
if __name__=='__main__':main()
