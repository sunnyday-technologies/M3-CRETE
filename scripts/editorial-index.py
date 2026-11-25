"""Index shipped M3 pages for publication intake. Only existing reader links are advertised."""
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
import json
import sys


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.in_title = False
        self.title = []
        self.readers = set()
        self.excluded = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "meta":
            if attrs.get("name", "").lower() == "robots" and "noindex" in attrs.get("content", "").lower():
                self.excluded = True
            if attrs.get("http-equiv", "").lower() == "refresh":
                self.excluded = True
        if tag == "a":
            url = attrs.get("href") or ""
            target = urlsplit(url)
            if target.scheme == "https" and target.netloc == "sunn3d.com" and target.path.startswith("/read/") and not target.query and not target.fragment:
                self.readers.add(url)

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)


def index(root):
    entries = []
    for path in sorted(root.rglob("*.html")):
        relative = path.relative_to(root).as_posix()
        if relative == "404.html":
            continue
        page = Page()
        source = path.read_text(encoding="utf-8-sig")
        page.feed(source)
        if page.excluded:
            continue
        route = "/" + relative.removesuffix("index.html") if path.name == "index.html" else "/" + relative
        entries.append({
            "url": "https://bom.m3-crete.com" + route,
            "title": " ".join("".join(page.title).split()),
            "source_text_sha256": sha256(source.encode("utf-8")).hexdigest(),
            "linked_readers": sorted(page.readers),
        })
    return {"site": "bom.m3-crete.com", "pages": entries}


if __name__ == "__main__":
    root = Path(sys.argv[1])
    output = root / ".well-known/editorial-pages.json"
    output.write_text(json.dumps(index(root), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
