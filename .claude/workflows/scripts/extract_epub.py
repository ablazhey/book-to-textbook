#!/usr/bin/env python3
"""Извлечение глав из EPUB в markdown + toc.json (только stdlib).

Использование: extract_epub.py <book.epub> <course_dir>
Результат: <course_dir>/chapters/chNN.md, <course_dir>/toc.json
и <course_dir>/images/* — картинки книги; в тексте главы на их месте стоит
маркер ![alt](images/имя.png), чтобы автор конспекта мог перенести рисунок.
Слова маркеров в подсчёт words/approxPages не входят — повторный прогон по уже
извлечённой книге не сдвигает номера «страниц».
"""
import html
import json
import os
import re
import sys
import zipfile
from html.parser import HTMLParser
from urllib.parse import unquote, urljoin
from xml.etree import ElementTree as ET

BLOCK = {"p", "div", "br", "li", "tr", "section", "article", "blockquote", "pre", "figure"}
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
IMAGE_MARKER = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HEAD = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}
SKIP = {"script", "style", "head", "title"}


class Extractor(HTMLParser):
    """XHTML -> markdown-ish текст с сохранением заголовков и списков."""

    def __init__(self, img_hook=None):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip_depth = 0
        self.head_level = None
        self.in_li = False
        # img_hook(src, alt) -> путь картинки в курсе (или None, если не удалось достать)
        self.img_hook = img_hook

    def handle_startendtag(self, tag, attrs):
        # <img .../> и <image .../> приходят сюда, а не в handle_starttag
        self.handle_starttag(tag, attrs)

    def handle_starttag(self, tag, attrs):
        if tag in SKIP:
            self.skip_depth += 1
        elif tag in ("img", "image"):
            if self.skip_depth or not self.img_hook:
                return
            a = dict(attrs)
            src = a.get("src") or a.get("href") or a.get("xlink:href")
            if not src:
                return
            alt = re.sub(r"\s+", " ", a.get("alt") or "").strip()[:200]
            path = self.img_hook(src, alt)
            if path:
                self.out.append("\n![%s](%s)\n" % (alt.replace("]", ")"), path))
        elif tag in HEAD:
            self.out.append("\n\n" + HEAD[tag] + " ")
            self.head_level = tag
        elif tag == "li":
            self.out.append("\n- ")
            self.in_li = True
        elif tag in BLOCK:
            self.out.append("\n")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag in ("strong", "b"):
            self.out.append("**")

    def handle_endtag(self, tag):
        if tag in SKIP:
            self.skip_depth = max(0, self.skip_depth - 1)
        elif tag in HEAD:
            self.out.append("\n")
            self.head_level = None
        elif tag == "li":
            self.in_li = False
        elif tag in BLOCK:
            self.out.append("\n")
        elif tag in ("em", "i"):
            self.out.append("*")
        elif tag in ("strong", "b"):
            self.out.append("**")

    def handle_data(self, data):
        if self.skip_depth:
            return
        text = re.sub(r"\s+", " ", data)
        if text.strip() or (self.out and not self.out[-1].endswith(" ")):
            self.out.append(text)

    def text(self):
        raw = "".join(self.out)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r" *\n *", "\n", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def count_words(text):
    """Слова текста без маркеров картинок."""
    return len(IMAGE_MARKER.sub("", text).split())


def make_img_hook(zf, chapter_path, saved, pending):
    """Хук для Extractor: резервирует имя картинки в <course>/images/ и отдаёт
    относительный путь для markdown. saved: имя файла -> внутренний путь в EPUB,
    чтобы одинаковые имена из разных каталогов не перезаписывали друг друга.
    Сама запись файла откладывается (pending) до принятия главы — картинки
    обложки/титула, которые отбрасываются по длине текста, в курс не попадают."""
    base = os.path.dirname(chapter_path)
    names = zf.namelist()

    def hook(src, alt):
        src = unquote(src.split("#")[0].split("?")[0])
        if src.startswith("data:") or not src.lower().endswith(IMAGE_EXT):
            return None
        inner = os.path.normpath(os.path.join(base, src)) if base else os.path.normpath(src)
        if inner not in names:
            return None
        name = os.path.basename(inner).lower()
        stem, ext = os.path.splitext(name)
        n = 1
        while name in saved and saved[name] != inner:
            n += 1
            name = "%s-%d%s" % (stem, n, ext)
        if name not in saved:
            saved[name] = inner
            pending.append((name, inner))
        return "images/" + name

    return hook


def flush_images(zf, images_dir, pending, saved, written, keep):
    """Записать отложенные картинки главы (keep=True) или снять их резерв."""
    for name, inner in pending:
        if keep:
            os.makedirs(images_dir, exist_ok=True)
            with open(os.path.join(images_dir, name), "wb") as f:
                f.write(zf.read(inner))
            written.add(name)
        elif name not in written:
            del saved[name]


def ns_strip(tag):
    return tag.split("}")[-1]


def find_opf(zf):
    container = zf.read("META-INF/container.xml").decode("utf-8", "replace")
    root = ET.fromstring(container)
    for el in root.iter():
        if ns_strip(el.tag) == "rootfile":
            return el.attrib["full-path"]
    raise SystemExit("Не найден OPF в container.xml")


def parse_opf(zf, opf_path):
    root = ET.fromstring(zf.read(opf_path).decode("utf-8", "replace"))
    manifest, spine, meta = {}, [], {}
    for el in root.iter():
        t = ns_strip(el.tag)
        if t == "item":
            manifest[el.attrib["id"]] = (el.attrib["href"], el.attrib.get("media-type", ""))
        elif t == "itemref":
            spine.append(el.attrib["idref"])
        elif t in ("title", "creator", "language") and el.text:
            meta.setdefault(t, el.text.strip())
    return manifest, spine, meta


def toc_titles(zf, opf_path, manifest):
    """Заголовки из nav.xhtml (EPUB3) или toc.ncx (EPUB2): href -> title."""
    base = os.path.dirname(opf_path)
    titles = {}
    for href, mtype in manifest.values():
        full = os.path.normpath(os.path.join(base, href)) if base else href
        if href.endswith(".ncx"):
            try:
                root = ET.fromstring(zf.read(full).decode("utf-8", "replace"))
            except (KeyError, ET.ParseError):
                continue
            for np in root.iter():
                if ns_strip(np.tag) != "navPoint":
                    continue
                label = content = None
                for ch in np.iter():
                    if ns_strip(ch.tag) == "text" and ch.text:
                        label = label or ch.text.strip()
                    elif ns_strip(ch.tag) == "content":
                        content = ch.attrib.get("src")
                if label and content:
                    titles[unquote(content.split("#")[0])] = label
        elif "nav" in href.lower() and href.endswith((".xhtml", ".html")):
            try:
                raw = zf.read(full).decode("utf-8", "replace")
            except KeyError:
                continue
            for m in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', raw, re.S | re.I):
                label = re.sub(r"<[^>]+>", "", m.group(2))
                label = html.unescape(label).strip()
                if label:
                    titles.setdefault(unquote(m.group(1).split("#")[0]), label)
    return titles


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_epub.py <book.epub> <course_dir>")
    book, course = sys.argv[1], sys.argv[2]
    ch_dir = os.path.join(course, "chapters")
    images_dir = os.path.join(course, "images")
    os.makedirs(ch_dir, exist_ok=True)
    saved_images, written_images = {}, set()

    zf = zipfile.ZipFile(book)
    opf_path = find_opf(zf)
    base = os.path.dirname(opf_path)
    manifest, spine, meta = parse_opf(zf, opf_path)
    titles = toc_titles(zf, opf_path, manifest)

    chapters, idx = [], 0
    for ref in spine:
        if ref not in manifest:
            continue
        href, mtype = manifest[ref]
        if "html" not in mtype and not href.endswith((".xhtml", ".html", ".htm")):
            continue
        full = os.path.normpath(os.path.join(base, href)) if base else href
        try:
            raw = zf.read(full).decode("utf-8", "replace")
        except KeyError:
            continue
        pending = []
        ex = Extractor(make_img_hook(zf, full, saved_images, pending))
        ex.feed(raw)
        text = ex.text()
        keep = len(IMAGE_MARKER.sub("", text)) >= 400  # обложки, копирайт, пустые вставки
        flush_images(zf, images_dir, pending, saved_images, written_images, keep)
        if not keep:
            continue
        idx += 1
        # заголовок: из TOC, иначе первый markdown-заголовок в тексте
        title = titles.get(unquote(href)) or titles.get(href)
        if not title:
            m = re.search(r"^#{1,3} (.+)$", text, re.M)
            title = m.group(1).strip() if m else "Часть %d" % idx
        name = "ch%02d.md" % idx
        with open(os.path.join(ch_dir, name), "w", encoding="utf-8") as f:
            f.write("# %s\n\n%s\n" % (title, text))
        words = count_words(text)
        chapters.append({
            "file": "chapters/" + name,
            "index": idx,
            "title": title,
            "source": href,
            "words": words,
            "approxPages": max(1, round(words / 300)),
        })

    # накопительные «страницы» — чтобы агенты могли ссылаться [гл. N, стр. X]
    page = 1
    for c in chapters:
        c["pageStart"] = page
        page += c["approxPages"]
        c["pageEnd"] = page - 1

    toc = {
        "book": os.path.basename(book),
        "title": meta.get("title", os.path.basename(book)),
        "author": meta.get("creator", ""),
        "language": meta.get("language", ""),
        "chaptersCount": len(chapters),
        "totalWords": sum(c["words"] for c in chapters),
        "pageNote": "approxPages/pageStart/pageEnd — оценка по 300 слов на страницу (в EPUB нет реальных страниц)",
        "chapters": chapters,
    }
    with open(os.path.join(course, "toc.json"), "w", encoding="utf-8") as f:
        json.dump(toc, f, ensure_ascii=False, indent=2)

    print("Книга: %s — %s" % (toc["title"], toc["author"]))
    print("Язык метаданных: %s" % (toc["language"] or "не указан"))
    print("Глав извлечено: %d, слов: %d (~%d стр.)" % (len(chapters), toc["totalWords"], page - 1))
    print("Картинок сохранено в images/: %d" % len(written_images))
    for c in chapters:
        print("  %-14s %5d сл.  %s" % (c["file"].split("/")[-1], c["words"], c["title"][:70]))


if __name__ == "__main__":
    main()
