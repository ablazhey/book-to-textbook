#!/usr/bin/env python3
"""Извлечение глав из PDF (по закладкам/outline) в markdown + toc.json.

Использование: extract_pdf.py <book.pdf> <course_dir>
Результат: <course_dir>/chapters/chNN.md, <course_dir>/toc.json
и <course_dir>/images/* — картинки со страниц (best effort: pypdf отдаёт встроенные
растровые объекты; мелочь до MIN_IMAGE_BYTES — иконки, буллеты — пропускаем).
В тексте главы после текста страницы стоят маркеры ![](images/pNNN_имя.png).
Слова маркеров в подсчёт words не входят.

Требует pypdf. Границы глав берутся из плоского списка закладок верхнего уровня
(each bookmark -> start page; следующая закладка задаёт конец предыдущей главы).
"""
import json
import os
import re
import sys

import pypdf

MIN_IMAGE_BYTES = 8 * 1024
IMAGE_MARKER = re.compile(r"!\[[^\]]*\]\([^)]*\)")


def count_words(text):
    return len(IMAGE_MARKER.sub("", text).split())


def page_images(page, page_no, images_dir):
    """Сохранить растровые картинки страницы, вернуть markdown-маркеры.
    pypdf для части кодировок требует Pillow — при любой ошибке молча отдаём пусто."""
    markers = []
    try:
        images = list(page.images)
    except Exception:
        return markers
    for n, img in enumerate(images, 1):
        try:
            data = img.data
            name = os.path.basename(img.name or "img")
        except Exception:
            continue
        if not data or len(data) < MIN_IMAGE_BYTES:
            continue
        stem, ext = os.path.splitext(name)
        ext = ext.lower() if ext.lower() in (".png", ".jpg", ".jpeg", ".gif", ".webp") else ".png"
        fname = "p%03d_%d%s" % (page_no, n, ext)
        os.makedirs(images_dir, exist_ok=True)
        with open(os.path.join(images_dir, fname), "wb") as f:
            f.write(data)
        markers.append("![](images/%s)" % fname)
    return markers


def clean_text(text):
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_pdf.py <book.pdf> <course_dir>")
    book, course = sys.argv[1], sys.argv[2]
    ch_dir = os.path.join(course, "chapters")
    images_dir = os.path.join(course, "images")
    os.makedirs(ch_dir, exist_ok=True)
    images_total = 0

    reader = pypdf.PdfReader(book)
    total_pages = len(reader.pages)

    bookmarks = []
    for item in reader.outline:
        if isinstance(item, list):
            continue  # игнорируем вложенность — работаем с плоским верхним уровнем
        title = item.title.strip()
        try:
            page_num = reader.get_destination_page_number(item)
        except Exception:
            continue
        bookmarks.append((title, page_num))

    if not bookmarks:
        raise SystemExit("В PDF нет закладок верхнего уровня — нужен другой способ разбиения на главы")

    # диапазоны страниц: от закладки до следующей закладки (или конца книги)
    chapters = []
    for idx, (title, start) in enumerate(bookmarks):
        end = bookmarks[idx + 1][1] if idx + 1 < len(bookmarks) else total_pages
        end = max(end, start + 1)
        pages_text = []
        for p in range(start, min(end, total_pages)):
            try:
                pages_text.append(reader.pages[p].extract_text() or "")
            except Exception:
                pass
            markers = page_images(reader.pages[p], p + 1, images_dir)
            images_total += len(markers)
            pages_text.extend(markers)
        text = clean_text("\n\n".join(pages_text))
        if len(IMAGE_MARKER.sub("", text)) < 50:
            continue
        name = "ch%02d.md" % (len(chapters) + 1)
        with open(os.path.join(ch_dir, name), "w", encoding="utf-8") as f:
            f.write("# %s\n\n%s\n" % (title, text))
        words = count_words(text)
        chapters.append({
            "file": "chapters/" + name,
            "index": len(chapters) + 1,
            "title": title,
            "source": "pdf pages %d-%d" % (start + 1, min(end, total_pages)),
            "words": words,
            "pageStart": start + 1,
            "pageEnd": min(end, total_pages),
        })

    def meta_str(v, default=""):
        if v is None:
            return default
        if hasattr(v, "get_object"):
            v = v.get_object()
        s = str(v).strip()
        return s if s else default

    meta = reader.metadata or {}
    toc = {
        "book": os.path.basename(book),
        "title": meta_str(meta.get("/Title"), os.path.basename(book)),
        "author": meta_str(meta.get("/Author")),
        "language": "",
        "chaptersCount": len(chapters),
        "totalWords": sum(c["words"] for c in chapters),
        "pageNote": "pageStart/pageEnd — реальные страницы PDF (1-based)",
        "chapters": chapters,
    }
    with open(os.path.join(course, "toc.json"), "w", encoding="utf-8") as f:
        json.dump(toc, f, ensure_ascii=False, indent=2)

    print("Книга: %s — %s" % (toc["title"], toc["author"]))
    print("Глав извлечено: %d, слов: %d" % (len(chapters), toc["totalWords"]))
    print("Картинок сохранено в images/: %d" % images_total)
    for c in chapters:
        print("  %-10s %5d сл.  стр.%d-%d  %s" % (c["file"].split("/")[-1], c["words"], c["pageStart"], c["pageEnd"], c["title"][:60]))


if __name__ == "__main__":
    main()
