#!/usr/bin/env python3
"""Сборка интерактивного HTML-учебника из артефактов курса (этап 6, только stdlib).

Использование: build_textbook.py <course_dir>
Читает: map.json, toc.json, glossary.json,
        topics/*.material.md|quiz.json|practice.json,
        sections/*.test.json, final/summary.md|exam.json|project.json, translated/*.md
Пишет:  <course_dir>/textbook.html

Собирается инкрементально: чего ещё нет — помечается «в работе».
"""
import html
import json
import os
import re
import sys

UI_RU = {
    "textbook": "Учебник",
    "minShort": "~%s мин",
    "chShort": "гл.",
    "pgShort": "стр.",
    "check": "Проверить",
    "correct": "Верно",
    "wrong": "Неверно",
    "source": "Источник в книге",
    "quiz": "Тест по теме",
    "sectionTest": "Итоговый тест раздела",
    "exam": "Финальный экзамен",
    "practice": "Практическое задание",
    "project": "Итоговый проект",
    "summary": "Саммари книги",
    "chapterText": "Текст главы",
    "expected": "Ожидаемый результат",
    "checklist": "Самопроверка",
    "steps": "Инструкция",
    "inProgress": "в работе",
    "passed": "пройдено",
    "result": "Результат",
    "retry": "Пройти заново",
    "yourAnswer": "Ваш ответ",
    "progress": "Прогресс",
    "passRule": "Тема засчитывается при 80% верных ответов",
    "section": "Раздел",
    "final": "Финал",
    "time": "Время",
    "showAnswer": "Эталонный ответ",
    "answered": "отвечено",
    "mistakes": "Работа над ошибками",
    "mistakesHint": "Неверные вопросы вернутся к ответу, верные свернутся",
    "toc": "Оглавление",
    "search": "Поиск по темам",
    "searchEmpty": "Ничего не найдено",
    "theme": "Тема оформления",
    "notes": "Ваши заметки и ответы",
    "notesPlaceholder": "Пишите прямо здесь — текст сохраняется в браузере",
    "copy": "Скопировать бланк",
    "copied": "Скопировано",
    "cards": "Карточки терминов",
    "cardsHint": "Термины книги в оригинале и переводе",
    "flip": "Показать перевод",
    "know": "Знаю",
    "dontKnow": "Повторить",
    "cardsDone": "Все карточки пройдены",
    "cardsReset": "Начать заново",
    "openChapter": "Открыть текст главы",
    "keyHints": "Клавиши: 1–9 — выбрать ответ, Enter — проверить, / — поиск",
    "done": "Готово",
    "progressPage": "Прогресс по тестам",
    "pPassed": "зачтено",
    "pTaken": "пройдено",
    "pAvg": "средний балл",
    "pTest": "Тест",
    "pWhere": "Раздел",
    "pScore": "Балл",
    "pStatus": "Статус",
    "pNotTaken": "не пройден",
    "pFailed": "не зачтён",
    "pEmpty": "Тесты ещё не проходились — результаты появятся здесь автоматически.",
    "tabDigest": "Конспект",
    "tabQuiz": "Тестовые задания",
    "tabPractice": "Практика",
    "prevTopic": "Предыдущая тема",
    "nextTopic": "Следующая тема",
    "chapterNav": "Навигация по темам",
    "openSource": "Источник",
    "closeSource": "Закрыть",
    "ctaRead": "Читать конспект",
    "ctaTestPrefix": "Пройти тест",
    "ctaQuestions": "вопросов",
    "readSettings": "Настройки чтения",
    "fontSize": "Размер шрифта",
    "textWidth": "Ширина текста",
    "lineSpacing": "Межстрочный интервал",
    "widthNarrow": "Узкая",
    "widthNormal": "Обычная",
    "widthWide": "Широкая",
    "spacingTight": "Плотный",
    "spacingNormal": "Обычный",
    "spacingLoose": "Свободный",
    "sessionList": "Список",
    "sessionView": "По одному",
    "sessionQuestion": "Вопрос",
    "sessionOf": "из",
    "sessionPrev": "‹ Назад",
    "sessionNext": "Дальше ›",
    "sessionFinish": "Показать результат",
    "examAnswered": "Ответ принят",
    "correctAnswer": "Правильный ответ",
}


UI_EN = {
    "textbook": "Textbook",
    "minShort": "~%s min",
    "chShort": "ch.",
    "pgShort": "p.",
    "check": "Check",
    "correct": "Correct",
    "wrong": "Incorrect",
    "source": "Source in the book",
    "quiz": "Topic quiz",
    "sectionTest": "Section test",
    "exam": "Final exam",
    "practice": "Practice task",
    "project": "Final project",
    "summary": "Book summary",
    "chapterText": "Chapter text",
    "expected": "Expected result",
    "checklist": "Self-check",
    "steps": "Instructions",
    "inProgress": "in progress",
    "passed": "passed",
    "result": "Result",
    "retry": "Retake",
    "yourAnswer": "Your answer",
    "progress": "Progress",
    "passRule": "A topic counts as passed at 80% correct answers",
    "section": "Section",
    "final": "Final",
    "time": "Time",
    "showAnswer": "Reference answer",
    "answered": "answered",
    "mistakes": "Review mistakes",
    "mistakesHint": "Wrong questions come back to be answered, correct ones collapse",
    "toc": "Contents",
    "search": "Search topics",
    "searchEmpty": "Nothing found",
    "theme": "Theme",
    "notes": "Your notes and answers",
    "notesPlaceholder": "Write right here — the text is saved in your browser",
    "copy": "Copy worksheet",
    "copied": "Copied",
    "cards": "Term cards",
    "cardsHint": "Terms of the book, original and translation",
    "flip": "Show translation",
    "know": "Know it",
    "dontKnow": "Repeat",
    "cardsDone": "All cards done",
    "cardsReset": "Start over",
    "openChapter": "Open chapter text",
    "keyHints": "Keys: 1–9 — choose an answer, Enter — check, / — search",
    "done": "Done",
    "progressPage": "Quiz progress",
    "pPassed": "passed",
    "pTaken": "taken",
    "pAvg": "average score",
    "pTest": "Test",
    "pWhere": "Section",
    "pScore": "Score",
    "pStatus": "Status",
    "pNotTaken": "not taken",
    "pFailed": "not passed",
    "pEmpty": "No tests taken yet — results will appear here automatically.",
    "tabDigest": "Notes",
    "tabQuiz": "Quiz",
    "tabPractice": "Practice",
    "prevTopic": "Previous topic",
    "nextTopic": "Next topic",
    "chapterNav": "Topic navigation",
    "openSource": "Source",
    "closeSource": "Close",
    "ctaRead": "Read the notes",
    "ctaTestPrefix": "Take the quiz",
    "ctaQuestions": "questions",
    "readSettings": "Reading settings",
    "fontSize": "Font size",
    "textWidth": "Text width",
    "lineSpacing": "Line spacing",
    "widthNarrow": "Narrow",
    "widthNormal": "Normal",
    "widthWide": "Wide",
    "spacingTight": "Tight",
    "spacingNormal": "Normal",
    "spacingLoose": "Loose",
    "sessionList": "List",
    "sessionView": "One by one",
    "sessionQuestion": "Question",
    "sessionOf": "of",
    "sessionPrev": "‹ Back",
    "sessionNext": "Next ›",
    "sessionFinish": "Show result",
    "examAnswered": "Answer recorded",
    "correctAnswer": "Correct answer",
}


def _ui_language():
    """Язык интерфейса — из <course_dir>/course.json {"lang": "..."}: ru — русский,
    любой другой — английский (других словарей нет). Без файла — ru, как раньше.
    Читаем при импорте: часть CSS/шаблонов собирается из UI на уровне модуля."""
    try:
        with open(os.path.join(sys.argv[1], "course.json"), encoding="utf-8") as f:
            lang = str(json.load(f).get("lang", "ru")).strip().lower()
    except (IndexError, OSError, ValueError, AttributeError):
        return "ru"
    return "ru" if lang in ("", "ru") or lang.startswith("ru-") else "en"


UI = UI_RU if _ui_language() == "ru" else UI_EN


def norm_ref(text):
    """Подпись ссылки на источник приводим к языку интерфейса: «[гл. 5, стр. 79]» <-> «[ch. 5, p. 79]».
    Агенты пишут маркер как в промпте (или как привыкли), сборщик показывает его единообразно."""
    t = re.sub(r"(?<![A-Za-zА-Яа-яЁё])(?:гл|ch|chap|chapter)\.?(?=\s*\d)", UI["chShort"], text or "", flags=re.I)
    return re.sub(r"(?<![A-Za-zА-Яа-яЁё])(?:стр|pp?|pages?)\.?(?=\s*\d)", UI["pgShort"], t, flags=re.I)


def _is_table_sep(s):
    return bool(re.match(r"^\|[\s:|-]+\|$", s.strip())) and "-" in s


def md_to_html(md, clickable_refs=True, captions=True):
    """Минимальный markdown → HTML: заголовки, списки, цитаты, таблицы, разделители, абзацы,
    картинки ![подпись](images/имя.png). captions=False — не выводить подпись из alt: у глав
    книги alt — это длинное описание картинки, а настоящая подпись идёт следующей строкой."""
    out = []
    in_list = in_quote = False

    def close_blocks(keep_list=False, keep_quote=False):
        nonlocal in_list, in_quote
        if in_list and not keep_list:
            out.append("</ul>")
            in_list = False
        if in_quote and not keep_quote:
            out.append("</blockquote>")
            in_quote = False

    ref_open, ref_close = (('<button type="button" class="ref" data-opench>', '</button>')
                           if clickable_refs else ('<span class="ref">', '</span>'))

    def inline(text):
        e = html.escape(text)
        e = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e)
        e = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", e)
        e = re.sub(r"`([^`]+)`", r"<code>\1</code>", e)
        return re.sub(r"\[((?:гл|ch|chap|chapter)\.?\s*\d[^\]]*)\]",
                      lambda m: ref_open + "[" + norm_ref(m.group(1)) + "]" + ref_close, e, flags=re.I)

    def cells(row):
        return [c.strip() for c in row.strip().strip("|").split("|")]

    lines = md.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        s = line.rstrip()

        # таблица: строка-заголовок, строка-разделитель, дальше тело.
        # Оборачиваем в контейнер со своей горизонтальной прокруткой, чтобы
        # широкая таблица не растягивала всю страницу.
        if (s.strip().startswith("|") and i + 1 < len(lines)
                and _is_table_sep(lines[i + 1])):
            close_blocks()
            head = cells(s)
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(cells(lines[i]))
                i += 1
            t = ['<div class="tablewrap"><table><thead><tr>']
            t += ["<th>%s</th>" % inline(h) for h in head]
            t.append("</tr></thead><tbody>")
            for r in rows:
                r = (r + [""] * len(head))[:len(head)]
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue

        # картинка отдельной строкой: ![подпись](images/имя.png)
        m = re.match(r"^!\[(.*?)\]\(([^)\s]+)\)\s*$", s.strip())
        if m:
            close_blocks()
            i += 1
            alt, src = m.group(1).strip(), m.group(2)
            fig = '<figure class="fig"><img src="%s" alt="%s" loading="lazy">' % (
                html.escape(src, quote=True), html.escape(alt, quote=True))
            if captions and alt:
                fig += "<figcaption>%s</figcaption>" % inline(alt)
            out.append(fig + "</figure>")
            continue

        i += 1
        quoted = bool(re.match(r"^>\s?", s))
        if quoted:
            s = re.sub(r"^>\s?", "", s)
        esc = inline(s)

        if quoted and not in_quote:
            close_blocks()
            out.append("<blockquote>")
            in_quote = True
        elif in_quote and not quoted and s.strip():
            close_blocks(keep_list=in_list)

        if re.match(r"^([-*_])\1{2,}$", s.strip()):
            close_blocks()
            out.append("<hr>")
            continue
        m = re.match(r"^(#{1,6}) (.+)$", esc)
        if m:
            close_blocks(keep_quote=in_quote)
            lvl = min(len(m.group(1)) + 1, 6)
            out.append("<h%d>%s</h%d>" % (lvl, m.group(2), lvl))
        elif re.match(r"^[-*] ", esc):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append("<li>%s</li>" % esc[2:])
        elif not s.strip():
            close_blocks(keep_quote=in_quote)
        else:
            close_blocks(keep_quote=in_quote)
            out.append("<p>%s</p>" % esc)
    close_blocks()
    return "\n".join(out)


def read_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def read_text(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return None


def chapter_range_label(nums):
    """[3,4,5] -> 'гл. 3–5' (en: 'ch. 3–5'); [7] -> 'гл. 7'; несмежные — 'гл. 3, 7'."""
    nums = sorted(set(nums))
    if not nums:
        return None
    if len(nums) > 1 and nums[-1] - nums[0] + 1 == len(nums):
        return "%s %d–%d" % (UI["chShort"], nums[0], nums[-1])
    return UI["chShort"] + " " + ", ".join(str(n) for n in nums)


def collect(course):
    cmap = read_json(os.path.join(course, "map.json")) or {"sections": []}
    toc = read_json(os.path.join(course, "toc.json")) or {}
    book_title = toc.get("title", UI["textbook"])
    # имя страницы — короткое и опознаваемое, без подзаголовка книги после двоеточия
    data = {"title": book_title, "pageTitle": UI["textbook"] + " " + book_title.split(":")[0].strip(),
            "author": toc.get("author", ""), "sections": []}
    for sec in cmap.get("sections", []):
        s = {"id": sec["id"], "title": sec["title"], "topics": []}
        for t in sec.get("topics", []):
            tid = t["id"]
            material = read_text(os.path.join(course, "topics", tid + ".material.md"))
            if material:
                # заголовок темы уже выводится отдельно — убираем дублирующий H1 из конспекта
                material = re.sub(r"\A\s*#\s+.+?\n", "", material)
            quiz = read_json(os.path.join(course, "topics", tid + ".quiz.json"))
            practice = read_json(os.path.join(course, "topics", tid + ".practice.json"))
            chapter_html = None
            chapter_nums = []
            for cf in t.get("chapterFiles", []):
                # перевод приоритетнее оригинала; если главу не переводили (или перевод
                # книги не включён) — показываем оригинальный текст, а не пропускаем вкладку
                src = read_text(os.path.join(course, "translated", os.path.basename(cf)))
                if not src:
                    src = read_text(os.path.join(course, cf))
                if src:
                    piece = md_to_html(src, clickable_refs=False, captions=False)
                    m = re.search(r"ch(\d+)", os.path.basename(cf))
                    # id ch<N> — якорь для панели источника: клик по ссылке [гл. N]
                    # в разборе ошибки прокручивает именно к этой главе, а не к началу
                    if m:
                        num = int(m.group(1))
                        chapter_nums.append(num)
                        piece = '<div class="chapterchunk" id="ch%d">%s</div>' % (num, piece)
                    chapter_html = (chapter_html or "") + piece
            s["topics"].append({
                "id": tid,
                "title": t["title"],
                "minutes": t.get("minutes"),
                "ready": bool(material),
                "materialHtml": md_to_html(material) if material else None,
                "chapterHtml": chapter_html,
                "chapterRange": chapter_range_label(chapter_nums),
                "questions": (quiz or {}).get("questions", []),
                "practice": practice if practice and practice.get("needed") else None,
            })
        s["test"] = read_json(os.path.join(course, "sections", sec["id"] + ".test.json"))
        data["sections"].append(s)
    data["summaryHtml"] = (lambda x: md_to_html(x) if x else None)(read_text(os.path.join(course, "final", "summary.md")))
    data["exam"] = read_json(os.path.join(course, "final", "exam.json"))
    project = read_json(os.path.join(course, "final", "project.json"))
    data["project"] = project if project and project.get("needed") else None
    glossary = read_json(os.path.join(course, "glossary.json")) or {}
    data["glossary"] = [{"t": k, "d": v} for k, v in glossary.items() if isinstance(v, str)]
    return data


CSS = """
/* Палитра: холодный сланец вместо тёплой бумаги — книга про приборы и цифры, а не про уют.
   Акцент индиго держится отдельно от семантических зелёного/красного, чтобы «верно/неверно»
   не спорило с навигацией. */
:root{
--bg:#f4f6f8;--card:#ffffff;--fg:#16202b;--muted:#5c6b7a;--line:#dce3ea;--line-soft:#e9eef3;
--accent:#2d4a7c;--accent-soft:#e8eef8;--on-accent:#ffffff;
--ok:#0f7a52;--ok-bg:#e6f4ee;--bad:#a3251d;--bad-bg:#fbeceb;--warn:#8a5a00;--warn-bg:#fdf2df;
--shadow:0 1px 2px rgba(22,32,43,.05),0 4px 16px rgba(22,32,43,.04);
--display:"Golos Text","Helvetica Neue",Arial,sans-serif;
--body:"Literata",Georgia,"Times New Roman",serif;
--mono:"JetBrains Mono",ui-monospace,"SF Mono",Menlo,monospace;
--appbar-h:48px;
--fs:17px;--measure:72ch;--lh:1.7;
}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
--bg:#121820;--card:#1a222c;--fg:#e4ebf2;--muted:#94a5b6;--line:#2a3541;--line-soft:#222c37;
--accent:#8fb2e8;--accent-soft:#1d2b3f;--on-accent:#121820;
--ok:#4fc48d;--ok-bg:#123026;--bad:#f0938a;--bad-bg:#33191a;--warn:#e8b45f;--warn-bg:#302408;
--shadow:0 1px 2px rgba(0,0,0,.4),0 4px 16px rgba(0,0,0,.25);
}}
:root[data-theme=dark]{
--bg:#121820;--card:#1a222c;--fg:#e4ebf2;--muted:#94a5b6;--line:#2a3541;--line-soft:#222c37;
--accent:#8fb2e8;--accent-soft:#1d2b3f;--on-accent:#121820;
--ok:#4fc48d;--ok-bg:#123026;--bad:#f0938a;--bad-bg:#33191a;--warn:#e8b45f;--warn-bg:#302408;
--shadow:0 1px 2px rgba(0,0,0,.4),0 4px 16px rgba(0,0,0,.25);
}
*{box-sizing:border-box}
/* Переключение .page (goToPage) резко меняет высоту документа — без этого
   браузерный scroll anchoring «услужливо» подправляет позицию скролла,
   чтобы визуально не дёргалось, и наш сброс на верх страницы не побеждает */
html{overflow-anchor:none}
body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--body);font-size:var(--fs);
line-height:var(--lh);-webkit-font-smoothing:antialiased}
.wrap{display:grid;grid-template-columns:296px minmax(0,1fr);max-width:1300px;margin:0 auto;min-height:100vh}

/* Верхняя панель — липнет над всем; на узком экране открывает оглавление шторкой,
   на любой ширине держит кнопки библиотеки/офлайн и текущую тему вместо плавающих кружков */
.appbar{position:sticky;top:0;z-index:30;display:flex;align-items:center;gap:10px;
padding:max(6px,env(safe-area-inset-top)) 16px 6px;background:var(--bg);border-bottom:1px solid var(--line)}
.menubtn{display:none;align-items:center;justify-content:center;flex:none;background:transparent;
border:1px solid var(--line);border-radius:7px;width:34px;height:34px;padding:0;cursor:pointer;position:relative}
.menubtn:hover{border-color:var(--accent)}
.menuicon,.menuicon::before,.menuicon::after{content:"";position:absolute;left:8px;right:8px;height:2px;
background:var(--fg);border-radius:1px}
.menuicon{top:16px}.menuicon::before{top:-6px}.menuicon::after{top:6px}
.appbar-mid{flex:1;min-width:0;display:flex;flex-direction:column;justify-content:center;gap:4px}
.curtopic{font-family:var(--display);font-size:12.5px;font-weight:600;color:var(--fg);
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.abar{height:3px;background:var(--line);border-radius:2px;overflow:hidden}
.abar i{display:block;height:100%;background:var(--ok);width:0;transition:width .35s ease}
.libslot{display:flex;gap:6px;flex:none}
/* Иконки, не текстовые пилюли: на узком экране «← Библиотека» + «⬇ Офлайн»
   текстом съедали большую часть appbar, не оставляя места под .curtopic.
   Название кнопки — в title/aria-label, как у офлайн-кнопки на полке. */
.libbtn{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
border-radius:100px;border:1px solid var(--line);background:var(--card);color:var(--accent);
font-size:15px;text-decoration:none;cursor:pointer;flex:none}
.libbtn:hover{border-color:var(--accent)}
.libbtn[data-state="saved"]{color:var(--ok);border-color:var(--ok)}
.libbtn[data-state="error"]{color:var(--bad);border-color:var(--bad)}
/* офлайн-копия есть, но вышла новая версия книги — ↻ приглашает обновить */
.libbtn[data-state="stale"]{color:var(--accent);border-color:var(--accent);background:var(--accent-soft)}
/* Во время скачивания книга может весить единицы-десятки МБ — кнопка на
   время растягивается в пилюлю с процентом, чтобы читатель видел прогресс,
   а не гадал, зависло приложение или нет */
.libbtn[data-state="busy"]{color:var(--accent);width:auto;padding:0 11px;
font-family:var(--mono);font-size:11.5px;font-variant-numeric:tabular-nums}
.scrim{position:fixed;inset:0;background:rgba(10,14,20,.42);z-index:35;opacity:0;pointer-events:none;
transition:opacity .2s ease}
body.nav-open .scrim,body.source-open .scrim{opacity:1;pointer-events:auto}

/* Панель источника — полный текст главы как справочник, а не равноправная
   вкладка: выезжает справа поверх контента, не толкает степпер темы */
.drawer{position:fixed;top:0;right:0;bottom:0;width:min(560px,100vw);z-index:50;
background:var(--card);border-left:1px solid var(--line);box-shadow:-10px 0 30px rgba(0,0,0,.18);
display:flex;flex-direction:column;transform:translateX(101%);transition:transform .22s ease}
body.source-open .drawer{transform:translateX(0)}
.drawerhead{display:flex;align-items:center;justify-content:space-between;gap:12px;
padding:16px 20px;border-bottom:1px solid var(--line);flex:none}
.drawerhead b{font-family:var(--display);font-size:15px;font-weight:600}
#sourcebody{overflow-y:auto;padding:22px 28px 60px;flex:1}
#sourcebody .panel{display:block;max-width:none}
@media(max-width:900px){.drawer{width:100vw}}

/* Поповер настроек чтения — кнопка «Aa» в верхней панели */
.popwrap{position:relative}
.pop{position:absolute;top:calc(100% + 8px);right:0;z-index:40;background:var(--card);
border:1px solid var(--line);border-radius:10px;box-shadow:var(--shadow);padding:14px 16px;
width:240px}
.popgroup{margin-bottom:12px}
.popgroup:last-child{margin-bottom:0}
.poplabel{display:block;font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;
text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.segmented{display:flex;border:1px solid var(--line);border-radius:7px;overflow:hidden}
.segmented button{flex:1;background:var(--bg);color:var(--fg);border:0;border-radius:0;
padding:7px 6px;font-family:var(--display);font-size:12.5px;cursor:pointer}
.segmented button+button{border-left:1px solid var(--line)}
.segmented button.on{background:var(--accent);color:var(--on-accent)}

/* Боковая навигация — оглавление курса с прогрессом и поиском */
nav{border-right:1px solid var(--line);padding:26px 20px 60px;position:sticky;top:var(--appbar-h);
height:calc(100vh - var(--appbar-h));overflow-y:auto;background:var(--bg)}
.navhead{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
nav h1{font-family:var(--display);font-size:16px;font-weight:600;letter-spacing:-.01em;margin:0 0 3px;
line-height:1.35;text-wrap:balance}
nav .author{color:var(--muted);font-size:12.5px;font-family:var(--display);margin-bottom:16px}
/* Оглавление — вложенный список: раздел сворачивается вместе со своими темами */
.navsec{border:0;background:transparent;padding:0;margin:4px 0;border-radius:0}
.navsec>summary{display:flex;gap:8px;align-items:baseline;padding:7px 9px;margin:0 -9px;border-radius:5px;
font-family:var(--mono);font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);
cursor:pointer;list-style:none}
.navsec>summary::-webkit-details-marker{display:none}
.navsec>summary:hover{background:var(--accent-soft);color:var(--fg)}
.navsec>summary .n{color:var(--accent);font-variant-numeric:tabular-nums;flex:none}
.navsec>summary .st{flex:1;min-width:0;text-wrap:balance;overflow-wrap:anywhere}
.navsec>summary .cnt{font-variant-numeric:tabular-nums;flex:none;letter-spacing:0}
.navsec>summary .cnt.full{color:var(--ok)}
.navsec>summary::after{content:"▸";flex:none;font-size:9px;transition:transform .15s;color:var(--muted)}
.navsec[open]>summary::after{transform:rotate(90deg)}
.navsec[open]>summary{color:var(--fg)}
.navsec .items{padding-left:12px;border-left:1px solid var(--line);margin:2px 0 8px 4px}
nav a{display:block;padding:6px 9px;margin:1px 0;border-radius:5px;color:var(--fg);text-decoration:none;
font-family:var(--display);font-size:13.5px;line-height:1.4;border-left:2px solid transparent}
nav .toplink{margin:2px -9px;font-family:var(--display);font-size:13px}
nav a:hover{background:var(--accent-soft)}
nav a:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
nav a.here{background:var(--accent-soft);border-left-color:var(--accent);font-weight:500}
nav a.done::after{content:" ✓";color:var(--ok);font-weight:700}
nav a.wip{color:var(--muted)}
nav a.wip::after{content:" · """ + UI["inProgress"] + """";font-size:10.5px;font-family:var(--mono)}
nav a.hidden,.navsec.hidden{display:none}
.pmeta{display:flex;justify-content:space-between;font-family:var(--mono);font-size:10.5px;
letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:7px}
.pmeta span{font-variant-numeric:tabular-nums}
.pbar{height:3px;background:var(--line);border-radius:2px;overflow:hidden;margin-bottom:14px}
.pbar i{display:block;height:100%;background:var(--ok);width:0;transition:width .35s ease}
.searchbox{position:relative;margin-bottom:6px}
.searchbox input{width:100%;padding:7px 11px;border:1px solid var(--line);border-radius:6px;
background:var(--card);color:var(--fg);font-family:var(--display);font-size:13px}
.searchbox input:focus-visible{outline:2px solid var(--accent);outline-offset:-1px;border-color:var(--accent)}
.noresult{font-family:var(--mono);font-size:11px;color:var(--muted);padding:8px 0}
.iconbtn{background:transparent;border:1px solid var(--line);color:var(--muted);border-radius:5px;
width:28px;height:28px;font-size:13px;cursor:pointer;flex:none;display:grid;place-items:center;padding:0}
.iconbtn:hover{border-color:var(--accent);color:var(--accent)}

/* Читательская колонка — ширина держится около 65 знаков */
main{padding:52px 56px 140px;max-width:var(--measure);min-width:0}
h2{font-family:var(--display);font-size:30px;font-weight:600;letter-spacing:-.02em;line-height:1.2;
margin:0 0 10px;text-wrap:balance;scroll-margin-top:calc(var(--appbar-h) + 12px)}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);
margin:64px 0 10px;font-variant-numeric:tabular-nums}
.eyebrow:first-child{margin-top:0}
h3{font-family:var(--display);font-size:21px;font-weight:600;letter-spacing:-.01em;line-height:1.3;
margin:44px 0 8px;text-wrap:balance;scroll-margin-top:calc(var(--appbar-h) + 12px)}
h4{font-family:var(--display);font-size:16.5px;font-weight:600;margin:28px 0 6px}
h5,h6{font-family:var(--display);font-size:15px;font-weight:600;margin:22px 0 6px}
p{margin:14px 0}
ul{padding-left:22px}
li{margin:6px 0}
.meta{color:var(--muted);font-size:13px;font-family:var(--mono);letter-spacing:.02em}
.hint{color:var(--muted);font-size:12.5px;font-family:var(--mono);letter-spacing:.02em;margin-top:8px}
/* Ссылка на источник — координата в книге; кликом открывается сам текст главы */
.ref{font-family:var(--mono);font-size:.8em;color:var(--accent);white-space:nowrap;letter-spacing:-.01em;
background:transparent;border:0;border-bottom:1px dotted var(--accent);padding:0;cursor:pointer}
.ref:hover{background:var(--accent-soft)}
.ref:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
code{font-family:var(--mono);font-size:.87em;background:var(--line-soft);padding:1px 5px;border-radius:3px}

/* Одна тема — один экран: читатель долистывает конспект до конца и упирается
   в кнопку перехода, а не в начало следующей темы. .page — верхнеуровневые
   разделы книги (тема, тест раздела, финал, прогресс) — показан только
   текущий, остальные display:none. Заодно решает и производительность:
   у Traction 67 тем в одном документе, layout/paint нужен только видимой */
.page{display:none}
.page.current{display:block}

.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:24px 26px;margin:32px 0;
box-shadow:var(--shadow)}
.card>h3:first-child,.card>h4:first-child{margin-top:0}
details{border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:20px 0;background:var(--card)}
details summary{cursor:pointer;font-family:var(--display);font-weight:600;font-size:13.5px}
details summary:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
details[open] summary{margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid var(--line-soft)}
details.flash{animation:flash 1.1s ease}
@keyframes flash{0%,100%{box-shadow:var(--shadow)}25%{box-shadow:0 0 0 3px var(--accent)}}

/* Степпер темы: Конспект → Тест (→ Практика). Липнет к верху — переключатель
   остаётся под рукой при длинном конспекте. Полный текст — не шаг, а
   справочник: открывается панелью источника (см. .drawer ниже), не вкладкой. */
.tabsrow{display:flex;align-items:center;gap:6px;margin:14px 0 0;border-bottom:1px solid var(--line);
position:sticky;top:var(--appbar-h);background:var(--bg);z-index:5}
.tabs{display:flex;gap:2px;overflow-x:auto;scrollbar-width:none;flex:1;min-width:0}
.tabs::-webkit-scrollbar{display:none}
.sourcebtn{display:block;margin:12px 0 0}
.tab{background:transparent;color:var(--muted);border:0;border-bottom:2px solid transparent;
border-radius:0;padding:11px 15px;font-family:var(--display);font-size:13.5px;font-weight:500;
white-space:nowrap;cursor:pointer;flex:none;display:inline-flex;align-items:center;gap:7px}
.tab:hover{color:var(--fg);background:var(--accent-soft)}
.tab:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.tab[aria-selected=true]{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
.tab .n{font-family:var(--mono);font-size:10px;width:17px;height:17px;border-radius:50%;
border:1.5px solid var(--line);color:var(--muted);display:inline-flex;align-items:center;
justify-content:center;flex:none;font-variant-numeric:tabular-nums;transition:background .15s,border-color .15s,color .15s}
.tab[aria-selected=true] .n{border-color:var(--accent);color:var(--accent)}
.tab.done .n{background:var(--ok);border-color:var(--ok);color:var(--on-accent)}
.tab .dot{display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--ok);margin-left:1px;
vertical-align:middle}
.panel{display:none;padding-top:4px}
.panel.on{display:block}
.panel.flash{animation:panelflash 1s ease}
@keyframes panelflash{0%,100%{background:transparent}30%{background:var(--accent-soft)}}
.panel>h4:first-child,.panel>p:first-child{margin-top:14px}
.endmarker{height:1px}
blockquote{margin:20px 0;padding:14px 18px;border-left:2px solid var(--accent);background:var(--accent-soft);
border-radius:0 6px 6px 0;font-size:15px}
blockquote p{margin:7px 0}
blockquote p:first-child{margin-top:0}
blockquote p:last-child{margin-bottom:0}
hr{border:0;border-top:1px solid var(--line);margin:36px 0}

/* Картинки и графики из книги: белая подложка — диаграммы с прозрачным фоном
   нечитаемы на тёмной теме; подпись — из alt маркера ![подпись](images/…) */
.fig{margin:24px 0;text-align:center}
.fig img{max-width:100%;height:auto;background:#fff;border:1px solid var(--line);border-radius:8px;padding:6px}
.fig figcaption{font-family:var(--display);font-size:13.5px;line-height:1.45;color:var(--muted);
margin:8px auto 0;max-width:60ch}
.fig+h6{text-align:center;color:var(--muted);font-weight:500;font-size:13.5px;margin:-14px 0 24px}

/* Таблицы: прокрутка живёт внутри своего контейнера, страница вбок не едет */
.tablewrap{overflow-x:auto;margin:22px 0;border:1px solid var(--line);border-radius:8px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:14.5px;line-height:1.55}
th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:top}
th{font-family:var(--display);font-weight:600;font-size:12.5px;letter-spacing:.03em;color:var(--muted);
text-transform:uppercase;white-space:nowrap;background:var(--bg)}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover{background:var(--accent-soft)}
td:first-child{font-variant-numeric:tabular-nums}
table .ref{white-space:nowrap}

/* Тест: каждый вопрос проверяется отдельно и сразу */
.quizhead{display:flex;justify-content:space-between;align-items:baseline;gap:12px;flex-wrap:wrap}
.tally{font-family:var(--mono);font-size:11.5px;color:var(--muted);letter-spacing:.05em;
font-variant-numeric:tabular-nums;white-space:nowrap}
.q{border-top:1px solid var(--line-soft);padding:22px 0}
.q:first-of-type{border-top:0;padding-top:4px}
/* режим «по одному» — .q переключает style.display сам JS (setQuizView), но
   первому видимому вопросу всё равно нужно погасить верхнюю границу-разделитель */
.card.session[data-view="qs"] .q{border-top:0;padding-top:4px}
.q .qt{font-family:var(--display);font-weight:600;font-size:16px;line-height:1.45;margin-bottom:12px;
display:flex;gap:10px}
.q .qn{font-family:var(--mono);font-size:13px;color:var(--accent);font-variant-numeric:tabular-nums;flex:none}
.q[data-state=correct] .qn{color:var(--ok)}
.q[data-state=wrong] .qn{color:var(--bad)}
.opt{display:flex;gap:10px;align-items:flex-start;padding:10px 13px;margin:6px 0;border:1px solid var(--line);
border-radius:6px;cursor:pointer;background:var(--bg);font-size:15.5px;line-height:1.5;transition:border-color .15s}
.opt:hover{border-color:var(--accent)}
.opt:focus-within{outline:2px solid var(--accent);outline-offset:1px}
.opt input{margin:5px 0 0;flex:none;accent-color:var(--accent)}
.opt .k{font-family:var(--mono);font-size:11px;color:var(--muted);flex:none;margin-top:4px;min-width:12px}
.opt.ok{background:var(--ok-bg);border-color:var(--ok)}
.opt.bad{background:var(--bad-bg);border-color:var(--bad)}
.opt.locked{cursor:default}
.qact{margin-top:10px}
input[type=text]{width:100%;padding:10px 13px;border:1px solid var(--line);border-radius:6px;background:var(--bg);
color:var(--fg);font-family:var(--body);font-size:15.5px}
input[type=text]:focus-visible{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
textarea{width:100%;min-height:110px;padding:11px 13px;border:1px solid var(--line);border-radius:6px;
background:var(--bg);color:var(--fg);font-family:var(--body);font-size:15px;line-height:1.6;resize:vertical}
textarea:focus-visible{outline:2px solid var(--accent);outline-offset:1px;border-color:var(--accent)}
/* line-height:1.2, а не унаследованный var(--lh) (текстовый интервал конспекта,
   настраивается читателем и доходит до 1.9) — иначе высота кнопки растёт
   вместе с межстрочным интервалом, хотя на самой кнопке одна строка текста */
button{background:var(--accent);color:var(--on-accent);border:0;border-radius:6px;padding:9px 18px;font-size:13.5px;
font-family:var(--display);font-weight:600;cursor:pointer;line-height:1.2}
button:hover{filter:brightness(1.12)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
button.ghost{background:transparent;color:var(--accent);border:1px solid var(--line)}
button.sm{padding:6px 13px;font-size:12.5px}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-top:18px}

/* Разбор ответа: полоса слева кодирует исход, он читается до чтения текста */
.fb{margin-top:12px;padding:13px 16px;border-radius:6px;font-size:14.5px;line-height:1.6;display:none}
.fb.show{display:block}
.fb.ok{background:var(--ok-bg);border-left:3px solid var(--ok)}
.fb.bad{background:var(--bad-bg);border-left:3px solid var(--bad)}
.fb b{display:block;font-family:var(--display);margin-bottom:5px}
.fb div{margin-top:7px}
/* Тест как сессия — один вопрос на экран, а не длинная форма: на телефоне
   так и задание, и разбор ошибки помещаются без прокрутки внутри вопроса */
.card.session:not([data-view="list"]) .tally{display:none}
.sessionbar{display:flex;align-items:center;gap:12px;margin:14px 0 0}
.sessionpos{font-family:var(--mono);font-size:11.5px;color:var(--muted);letter-spacing:.05em;
white-space:nowrap;flex:none;font-variant-numeric:tabular-nums}
.sessionprog{flex:1;height:4px;background:var(--line);border-radius:2px;overflow:hidden}
.sessionprog i{display:block;height:100%;width:0;background:var(--accent);transition:width .25s ease}
.sessionnav{display:flex;align-items:center;margin-top:18px}
.sessionnav [data-sessionnext]{margin-left:auto}

/* Экран результата теста — заменяет вопросы и навигацию сессии по завершении */
.result{display:none}
.resulttop{display:flex;align-items:center;gap:20px;margin:8px 0 4px}
.resultstat b{font-family:var(--display);font-size:26px;display:block;line-height:1.2}
.resultstat span{font-family:var(--mono);font-size:12.5px;color:var(--muted);letter-spacing:.04em;
text-transform:uppercase}
.mistakelist{margin-top:18px;display:flex;flex-direction:column;gap:14px}
.mistake{display:flex;gap:12px;padding-top:14px;border-top:1px solid var(--line-soft)}
.mistake:first-child{border-top:0;padding-top:0}
.mn{font-family:var(--mono);font-size:12px;color:var(--bad);flex:none;padding-top:2px}
.mbody{min-width:0}
.mq{font-family:var(--display);font-weight:600;font-size:15px;line-height:1.4;margin-bottom:6px}
.ma{font-size:14px;line-height:1.5;margin-top:3px}
.ma i{font-style:normal;color:var(--muted)}
.ma.bad{color:var(--bad)}
.ma.ok{color:var(--ok)}
.resultbtns{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}
.badge{display:inline-block;font-family:var(--mono);font-size:10.5px;padding:2px 7px;border-radius:3px;
background:var(--line-soft);color:var(--muted);vertical-align:middle;margin-left:9px;font-variant-numeric:tabular-nums}
.badge.done{background:var(--ok-bg);color:var(--ok)}
.wip-note{font-family:var(--mono);font-size:12.5px;color:var(--muted);letter-spacing:.04em}

/* Практика как заполняемый бланк */
.task li{position:relative}
.chk{display:flex;gap:10px;align-items:flex-start;padding:7px 10px;border-radius:5px;cursor:pointer;
font-size:15.5px;line-height:1.55}
.chk:hover{background:var(--accent-soft)}
.chk input{margin:6px 0 0;flex:none;accent-color:var(--ok)}
.chk.on{color:var(--muted)}
.chk.on .t{text-decoration:line-through}
.tasklist{list-style:none;padding:0;margin:8px 0}
.tasklist li{margin:1px 0}
.stepn{font-family:var(--mono);font-size:11.5px;color:var(--accent);flex:none;margin-top:4px;min-width:18px;
font-variant-numeric:tabular-nums}
.taskprog{font-family:var(--mono);font-size:11.5px;color:var(--muted);letter-spacing:.05em;
font-variant-numeric:tabular-nums}

/* Сводка по тестам */
.pgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:12px;margin-bottom:6px}
.stat{background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:14px 16px}
.stat .v{font-family:var(--display);font-size:26px;font-weight:600;line-height:1.1;
font-variant-numeric:tabular-nums}
.stat .l{font-family:var(--mono);font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
color:var(--muted);margin-top:4px}
.stat.ok .v{color:var(--ok)}
.stat.bad .v{color:var(--bad)}
.pill{display:inline-block;font-family:var(--mono);font-size:11px;padding:2px 9px;border-radius:20px;
background:var(--line-soft);color:var(--muted);white-space:nowrap}
.pill.ok{background:var(--ok-bg);color:var(--ok)}
.pill.bad{background:var(--bad-bg);color:var(--bad)}
table a{color:var(--accent);text-decoration:none;border-bottom:1px solid transparent}
table a:hover{border-bottom-color:var(--accent)}
.emptynote{font-family:var(--mono);font-size:12.5px;color:var(--muted);padding:6px 0}

/* Карточки терминов */
.deck{display:grid;gap:14px;justify-items:center}
.flash-card{width:100%;background:var(--bg);border:1px solid var(--line);border-radius:8px;padding:34px 24px;
text-align:center;min-height:150px;display:grid;place-content:center;gap:10px;cursor:pointer;
touch-action:pan-y;transition:transform .2s ease}
.flash-card .term{font-family:var(--display);font-size:22px;font-weight:600;line-height:1.3}
.flash-card .tr{font-size:18px;color:var(--accent);font-family:var(--display)}
.deckmeta{font-family:var(--mono);font-size:11.5px;color:var(--muted);letter-spacing:.05em;
font-variant-numeric:tabular-nums}

/* Главная кнопка темы — одна на весь маршрут: читать конспект → пройти тест →
   дальше. Пред/след ниже неё — второстепенная навигация, не основное действие */
.cta{display:block;text-align:center;margin-top:26px;padding:14px 20px;border-radius:9px;
background:var(--accent);color:var(--on-accent);font-family:var(--display);font-weight:600;
font-size:15px;line-height:1.3;text-decoration:none;cursor:pointer}
.cta:hover{filter:brightness(1.1)}
.cta:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* Навигация «предыдущая/следующая тема» в конце темы — низкая полоска, не карточка.
   Это тоже <nav>, а nav{...} и его версия в @media(max-width:900px) написаны
   для #booknav (сайдбар, на узком экране — выезжающая шторка) — без явного
   сброса ВСЕГО, что там задано, .chapternav наследует и position:fixed,
   и transform:translateX(-101%) от закрытой шторки: на любом экране ≤900px
   (то есть на любом телефоне и iPad) кнопки пред/след были полностью вне
   экрана, невидимы и некликабельны. Поймано тем же способом, что и баг с
   нижней панелью вкладок в pwa/build.py — тоже голый <nav> вместо класса. */
.chapternav{display:flex;justify-content:space-between;gap:10px;margin-top:14px;padding:12px 0 0;
border-top:1px solid var(--line);position:static;top:auto;left:auto;right:auto;bottom:auto;
width:auto;height:auto;z-index:auto;border-right:0;overflow-y:visible;background:transparent;
transform:none;transition:none;box-shadow:none}
.navbtn{flex:1;min-width:0;display:flex;flex-direction:column;gap:1px;padding:6px 10px;border-radius:8px;
border:1px solid var(--line);text-decoration:none;color:var(--fg);background:var(--card);
line-height:1.25;transition:border-color .15s}
.navbtn:hover{border-color:var(--accent)}
.navbtn:focus-visible{outline:2px solid var(--accent);outline-offset:1px}
.navbtn.next{text-align:right;align-items:flex-end}
.navbtn.empty{visibility:hidden;border-color:transparent}
.navbtn .nb-dir{font-family:var(--mono);font-size:10px;letter-spacing:.06em;text-transform:uppercase;
color:var(--muted)}
.navbtn .nb-title{font-family:var(--display);font-size:13.5px;font-weight:600;max-width:100%;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis}

@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
@media(max-width:900px){
.wrap{grid-template-columns:1fr}
.menubtn{display:inline-flex}
/* На узком экране оглавление — шторка поверх контента, не статичный блок над текстом:
   иначе читатель пролистывает список тем, прежде чем увидит хоть строку конспекта */
nav{position:fixed;top:0;left:0;bottom:0;width:min(320px,85vw);height:100vh;z-index:40;
padding:calc(20px + env(safe-area-inset-top)) 20px 24px;
transform:translateX(-101%);transition:transform .22s ease;box-shadow:0 12px 40px rgba(0,0,0,.28)}
body.nav-open nav{transform:translateX(0)}
main{padding:28px 20px 90px}
h2{font-size:25px}.eyebrow{margin-top:44px}
}
"""

JS = r"""
const UI=__UI__, GLOSSARY=__GLOSSARY__, QUIZZES=__QUIZZES__, SLUG=__SLUG__;
const KEYS='1234567890';

/* ---------- хранилище: у каждой книги свой ключ, иначе тест, сданный в
   одной книге, засчитывается в другой (все книги живут на одном origin,
   а id тестов вроде s1t1_quiz — одинаковые в разных курсах) ---------- */
const KEY='tb:'+SLUG;
const PREFS_KEY='tb:prefs';
(function migrateLegacyProgress(){
 // до этой правки все книги писали в один общий ключ 'tb' — при первом
 // открытии КАЖДОЙ книги копируем его как её собственный прогресс: мы не
 // знаем, какой книге эти данные принадлежали, так что копия достаётся
 // всем один раз (лучше лишний прогресс, чем потерянный)
 try{
  if(localStorage.getItem(KEY))return;
  const legacy=localStorage.getItem('tb');
  if(!legacy)return;
  localStorage.setItem(KEY,legacy);
  const old=JSON.parse(legacy);
  old._migrated=true;
  localStorage.setItem('tb',JSON.stringify(old));
 }catch(e){}
})();
function load(){try{return JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){return{}}}
function save(k,v){try{const s=load();s[k]=v;localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}}
function get(k,d){const s=load();return k in s?s[k]:d}

/* ---------- настройки, общие для всех книг (тема оформления и т.п.) ---------- */
function loadPrefs(){try{return JSON.parse(localStorage.getItem(PREFS_KEY)||'{}')}catch(e){return{}}}
function savePref(k,v){try{const s=loadPrefs();s[k]=v;localStorage.setItem(PREFS_KEY,JSON.stringify(s))}catch(e){}}
function getPref(k,d){const s=loadPrefs();return k in s?s[k]:d}

/* ---------- тема ---------- */
function applyTheme(t){
 if(t==='auto')document.documentElement.removeAttribute('data-theme');
 else document.documentElement.setAttribute('data-theme',t);
 // две кнопки — в шапке и в оглавлении — показывают одно и то же состояние
 document.querySelectorAll('.themebtn').forEach(b=>{b.textContent=t==='dark'?'☾':t==='light'?'☀':'◐'});
}
applyTheme(getPref('theme','auto'));

/* ---------- настройки чтения: размер шрифта, ширина колонки, интервал ---------- */
function applyReadingPrefs(){
 const fs=getPref('fs',17), measure=getPref('measure',72), lh=getPref('lh',1.7);
 const r=document.documentElement.style;
 r.setProperty('--fs',fs+'px');
 r.setProperty('--measure',measure+'ch');
 r.setProperty('--lh',lh);
 document.querySelectorAll('.segmented').forEach(seg=>{
  const pref=seg.dataset.pref;
  const cur=String(pref==='fs'?fs:pref==='measure'?measure:lh);
  seg.querySelectorAll('button').forEach(b=>b.classList.toggle('on',b.dataset.val===cur));
 });
}
applyReadingPrefs();

/* ---------- панель источника: полный текст главы — справочник, не вкладка.
   Узел панели физически переносится внутрь #sourcebody (не клонируется),
   при закрытии возвращается туда же, откуда взят, чтобы тема не потеряла
   часть DOM навсегда ---------- */
let sourceHome=null;
function restoreSourcePanel(){
 if(!sourceHome)return;
 sourceHome.parent.insertBefore(sourceHome.node,sourceHome.next);
 sourceHome=null;
}
function openSource(topicId,refText){
 const panel=document.querySelector('.panel[data-of="'+topicId+'"][data-panel="text"]');
 if(!panel)return;
 restoreSourcePanel();
 sourceHome={node:panel,parent:panel.parentNode,next:panel.nextSibling};
 const body=document.getElementById('sourcebody');
 body.appendChild(panel);
 const a=document.querySelector('nav a[href="#'+topicId+'"]');
 document.getElementById('sourcetitle').textContent=a?a.dataset.title:'';
 document.body.classList.add('source-open');
 document.getElementById('source').setAttribute('aria-hidden','false');
 const numMatch=refText&&refText.match(/\d+/);
 const target=numMatch?panel.querySelector('#ch'+numMatch[0]):null;
 if(target){
  target.scrollIntoView({block:'start'});
  target.classList.remove('flash');void target.offsetWidth;target.classList.add('flash');
 }else{
  body.scrollTop=0;
 }
}
function closeSource(){
 document.body.classList.remove('source-open');
 document.getElementById('source').setAttribute('aria-hidden','true');
 restoreSourcePanel();
}

/* ---------- верхняя панель: высота как CSS-переменная, а не константа ---------- */
/* env(safe-area-inset-top) на разных iPad/iPhone разный — проще один раз
   измерить реальную высоту шапки, чем гадать числом в CSS */
function syncAppbarHeight(){
 const ab=document.querySelector('.appbar');
 if(ab)document.documentElement.style.setProperty('--appbar-h',ab.offsetHeight+'px');
}
syncAppbarHeight();
window.addEventListener('resize',syncAppbarHeight);

/* ---------- шторка оглавления (узкий экран) ---------- */
function toggleDrawer(){
 document.body.classList.contains('nav-open')?closeDrawer():openDrawer();
}
function openDrawer(){
 document.body.classList.add('nav-open');
 const t=document.getElementById('navtoggle');if(t)t.setAttribute('aria-expanded','true');
}
function closeDrawer(){
 document.body.classList.remove('nav-open');
 const t=document.getElementById('navtoggle');if(t)t.setAttribute('aria-expanded','false');
}
document.addEventListener('keydown',e=>{
 if(e.key!=='Escape')return;
 const pop=document.getElementById('readpop');
 if(pop&&!pop.hasAttribute('hidden')){pop.setAttribute('hidden','');
  document.getElementById('readbtn').setAttribute('aria-expanded','false');return}
 if(document.body.classList.contains('source-open')){closeSource();return}
 if(document.body.classList.contains('nav-open'))closeDrawer();
});

/* ---------- позиция чтения: тема + открытая вкладка, чтобы книга открывалась
   не с «Прогресса», а с того места, где читатель остановился ---------- */
function savePos(topic,panel){
 if(!topic)return;
 const prev=get('pos',{});
 save('pos',{topic:topic,panel:panel||(prev.topic===topic?prev.panel:'digest'),ts:Date.now()});
}
/* Внутристраничная прокрутка — цель уже видима (текущая .page), тут нет
   риска content-visibility-заглушки, обычный scrollIntoView достаточен */
function scrollToEl(el){
 if(!el)return;
 el.scrollIntoView({block:'start'});
}
/* Переход между «страницами» книги: показываем ровно одну .page, остальные
   display:none — читатель, долистав тему до конца, упирается в пустоту и
   кнопку «дальше», а не в начало следующей темы */
function showPage(id){
 const pages=[...document.querySelectorAll('.page')];
 let found=false;
 pages.forEach(p=>{
  const match=p.dataset.page===id;
  p.classList.toggle('current',match);
  if(match)found=true;
 });
 return found;
}
function goToPage(id){
 if(!showPage(id))return false;
 window.scrollTo(0,0);
 return true;
}
/* Переход по ссылке внутри книги — через pushState, а не обычный клик по
   #якорю: родная навигация браузера норовит докрутить/сфокусировать элемент
   с этим id (например саму карточку теста, а не начало страницы), и наш
   сброс скролла в начало страницы эту докрутку не всегда перебивает.
   pushState меняет location.hash без какой-либо автоматической прокрутки. */
function navigateHash(href){
 const id=(href||'').replace(/^#/,'');
 if(!id)return;
 if(location.hash!=='#'+id)history.pushState(null,'','#'+id);
 goToPage(id);
}
function scrollToHash(){
 const id=(location.hash||'').slice(1);
 if(!id)return;
 if(goToPage(id))return;
 // хэш не совпал ни с одной .page (страница из старой сборки удалена и
 // т.п.) — со старым элементом просто прокручиваем на месте, если он
 // всё же существует, иначе не оставляем читателя на пустом экране
 const el=document.getElementById(id);
 if(el){scrollToEl(el);return}
 goToPage('progress');
}
window.addEventListener('hashchange',scrollToHash);
function restorePosition(){
 if(location.hash){scrollToHash();return} // прямая ссылка на тему важнее сохранённой позиции
 const pos=get('pos',null);
 if(pos&&pos.topic&&document.getElementById(pos.topic)){
  showTab(pos.topic,pos.panel,false);
  goToPage(pos.topic);
  return;
 }
 goToPage('progress'); // ни хэша, ни сохранённой позиции — открываем книгу с прогресса, как раньше
}

/* ---------- проверка одного вопроса ---------- */
function shortMatch(val,exp){
 val=(val||'').trim().toLowerCase();exp=(exp||'').toLowerCase();
 if(!val)return false;
 const words=exp.split(/[^\p{L}\p{N}]+/u).filter(w=>w.length>3);
 if(!words.length)return val===exp;
 return words.filter(w=>val.includes(w)).length/words.length>=0.5;
}
function gradeQuestion(q){
 const type=q.dataset.type, correct=JSON.parse(q.dataset.correct||'[]');
 const isExam=q.closest('.card[data-exam="1"]');
 let ok=false, picked=[];
 if(type==='short'){
  ok=shortMatch(q.querySelector('input[type=text]').value,q.dataset.answer);
 }else{
  // picked — по value инпута (исходный индекс варианта), а не по позиции в DOM:
  // shuffleOptions() переставляет .opt местами при каждой попытке, позиция «плывёт»
  const inputs=[...q.querySelectorAll('.opt input')];
  picked=inputs.filter(i=>i.checked).map(i=>parseInt(i.value,10));
  ok=picked.length===correct.length&&picked.every(p=>correct.includes(p));
  if(!isExam){
   inputs.forEach(i=>{
    const o=i.closest('.opt'), v=parseInt(i.value,10);
    o.classList.remove('ok','bad');o.classList.add('locked');
    if(correct.includes(v))o.classList.add('ok');
    else if(i.checked)o.classList.add('bad');
   });
  }else{
   inputs.forEach(i=>i.closest('.opt').classList.add('locked'));
  }
 }
 q.dataset.state=ok?'correct':'wrong';
 if(!ok)q.dataset.everWrong='1'; // переживает resetQuestion() — нужно для фильтра «работа над ошибками»
 const fb=q.querySelector('.fb');
 if(isExam){
  // на экзамене разбор не показываем до конца — иначе это уже не экзамен, а тренировка
  fb.className='fb show';
  fb.innerHTML='<b>'+UI.examAnswered+'</b>';
 }else{
  fb.className='fb show '+(ok?'ok':'bad');
  let h='<b>'+(ok?UI.correct:UI.wrong)+'</b>';
  if(type==='short'&&q.dataset.answer)h+='<div><i>'+UI.showAnswer+':</i> '+q.dataset.answer+'</div>';
  if(!ok){
   const wrongs=JSON.parse(q.dataset.wrong||'[]');
   picked.filter(p=>!correct.includes(p)).forEach(p=>{if(wrongs[p])h+='<div>'+wrongs[p]+'</div>'});
  }
  h+='<div>'+q.dataset.expl+'</div>';
  if(q.dataset.ref)h+='<div><i>'+UI.source+':</i> <button type="button" class="ref" data-opench>'+q.dataset.ref+'</button></div>';
  fb.innerHTML=h;
 }
 const act=q.querySelector('.qact');if(act)act.style.display='none';
 return ok;
}
function tally(box){
 const qs=sessionQs(box);
 const graded=qs.filter(q=>q.dataset.state);
 const right=qs.filter(q=>q.dataset.state==='correct').length;
 const t=box.querySelector('.tally');
 if(t)t.textContent=UI.answered+' '+graded.length+'/'+qs.length+' · '+UI.correct.toLowerCase()+' '+right;
 updateSessionNav(box);
 // в режиме «по одному» финиш — по клику на «Показать результат» (updateSessionNav
 // сам подставит эту подпись на последнем вопросе), а не автоматически после ответа;
 // «Список» — старый режим печати/обзора, там как и раньше — сразу после последнего ответа
 if(graded.length===qs.length&&box.dataset.view==='list')finalizeSession(box);
}
function resetQuestion(q){
 delete q.dataset.state;
 q.querySelectorAll('input').forEach(i=>{if(i.type==='text')i.value='';else i.checked=false});
 q.querySelectorAll('.opt').forEach(o=>o.classList.remove('ok','bad','locked'));
 q.querySelector('.fb').className='fb';
 const act=q.querySelector('.qact');if(act)act.style.display='';
}

/* ---------- тест как сессия: один вопрос на экран ---------- */
function sessionQs(box){
 const all=[...box.querySelectorAll('.qs > .q')];
 // «работа над ошибками» временно сужает список вопросов до тех, что этой
 // попыткой отмечены как ошибочные (см. gradeQuestion: data-everWrong переживает
 // resetQuestion, поэтому фильтр не теряет вопрос сразу после его сброса)
 if(box.dataset.filter==='wrong')return all.filter(q=>q.dataset.everWrong==='1');
 return all;
}
function escHtml(s){
 const d=document.createElement('div');
 d.textContent=s==null?'':String(s);
 return d.innerHTML;
}
function shuffleOptions(q){
 const wrap=q.querySelector('.opts');
 if(!wrap)return;
 const nodes=[...wrap.children];
 for(let i=nodes.length-1;i>0;i--){
  const j=Math.floor(Math.random()*(i+1));
  [nodes[i],nodes[j]]=[nodes[j],nodes[i]];
 }
 // перенумеровываем видимые метки 1..9 по НОВОМУ визуальному порядку —
 // клавиши 1–9 всегда должны попадать в то, что реально нарисовано под этой цифрой
 nodes.forEach((n,idx)=>{
  wrap.appendChild(n);
  const k=n.querySelector('.k');
  if(k)k.textContent=idx<9?String(idx+1):'';
 });
}
function shuffleQuestionOrder(box){
 if(box.dataset.shuffleq!=='1')return;
 const wrap=box.querySelector('.qs');
 const nodes=[...wrap.children];
 for(let i=nodes.length-1;i>0;i--){
  const j=Math.floor(Math.random()*(i+1));
  [nodes[i],nodes[j]]=[nodes[j],nodes[i]];
 }
 nodes.forEach((n,idx)=>{
  wrap.appendChild(n);
  const qn=n.querySelector('.qn');
  // номер вопроса — по НОВОМУ порядку показа, а не по месту в исходном конспекте,
  // иначе «Вопрос 3 из 10» не совпадёт с тем, что реально написано на карточке
  if(qn)qn.textContent=String(idx+1).padStart(2,'0');
 });
}
function optionTextMap(q){
 const map={};
 q.querySelectorAll('.opt').forEach(o=>{
  const input=o.querySelector('input');
  const spans=o.querySelectorAll('span');
  map[parseInt(input.value,10)]=spans[1]?spans[1].textContent:'';
 });
 return map;
}
function updateSessionBar(box){
 const qs=sessionQs(box);
 const i=Math.min(+box.dataset.idx||0,qs.length-1);
 const pos=box.querySelector('.sessionpos');
 if(pos)pos.textContent=UI.sessionQuestion+' '+(i+1)+' '+UI.sessionOf+' '+qs.length;
 const bar=box.querySelector('.sessionprog i');
 if(bar)bar.style.width=qs.length?Math.round((i+1)/qs.length*100)+'%':'0%';
}
function updateSessionNav(box){
 const qs=sessionQs(box);
 const i=Math.min(+box.dataset.idx||0,Math.max(qs.length-1,0));
 const q=qs[i];
 const prev=box.querySelector('[data-sessionprev]');
 const next=box.querySelector('[data-sessionnext]');
 if(prev)prev.style.visibility=i>0?'visible':'hidden';
 if(next&&q){
  const answered=!!q.dataset.state;
  next.style.display=answered?'':'none';
  next.textContent=i>=qs.length-1?UI.sessionFinish:UI.sessionNext;
 }
}
function setQuizView(box,view){
 box.dataset.view=view;
 const qs=sessionQs(box);
 const bar=box.querySelector('.sessionbar');
 const nav=box.querySelector('.sessionnav');
 const listbtn=box.querySelector('[data-listview]');
 const result=box.querySelector('.result');
 // .q за пределами текущего фильтра (не ошибочные, во время «работы над ошибками»)
 // прячем всегда — независимо от вида
 [...box.querySelectorAll('.qs > .q')].forEach(q=>{
  if(!qs.includes(q))q.style.display='none';
 });
 if(view==='result'){
  qs.forEach(q=>q.style.display='none');
  if(bar)bar.style.display='none';
  if(nav)nav.style.display='none';
  if(listbtn)listbtn.style.display='none';
  if(result)result.style.display='block';
  return;
 }
 if(result)result.style.display='none';
 if(listbtn)listbtn.style.display='';
 if(view==='list'){
  qs.forEach(q=>q.style.display='');
  if(bar)bar.style.display='none';
  if(nav)nav.style.display='none';
  if(listbtn)listbtn.textContent=UI.sessionView;
  return;
 }
 const i=Math.min(+box.dataset.idx||0,Math.max(qs.length-1,0));
 box.dataset.idx=i;
 qs.forEach((q,n)=>q.style.display=n===i?'':'none');
 if(bar)bar.style.display='';
 if(nav)nav.style.display='flex';
 if(listbtn)listbtn.textContent=UI.sessionList;
 updateSessionBar(box);
 updateSessionNav(box);
}
function ringSvg(pct,pass){
 const r=34,c=Math.round(2*Math.PI*r),off=Math.round(c*(1-pct/100));
 const color=pass?'var(--ok)':'var(--accent)';
 return '<svg viewBox="0 0 80 80" width="80" height="80" aria-hidden="true">'
  +'<circle cx="40" cy="40" r="'+r+'" fill="none" style="stroke:var(--line)" stroke-width="8"/>'
  +'<circle cx="40" cy="40" r="'+r+'" fill="none" style="stroke:'+color+'" stroke-width="8" '
  +'stroke-dasharray="'+c+'" stroke-dashoffset="'+off+'" stroke-linecap="round" transform="rotate(-90 40 40)"/>'
  +'<text x="40" y="46" text-anchor="middle" font-size="20" font-weight="700" style="fill:var(--fg)">'+pct+'%</text></svg>';
}
function finalizeSession(box){
 const qs=[...box.querySelectorAll('.qs > .q')]; // итог — по ВСЕМ вопросам, не по текущему фильтру
 const total=qs.length;
 const right=qs.filter(q=>q.dataset.state==='correct').length;
 const wrong=qs.filter(q=>q.dataset.state==='wrong');
 const pct=total?Math.round(right/total*100):0, pass=pct>=80;
 save(box.id,{pct:pct,pass:pass});
 const hist=get('attempts:'+box.id,[]);
 hist.push({ts:Date.now(),pct:pct,wrong:wrong.map(q=>qs.indexOf(q))});
 while(hist.length>10)hist.shift();
 save('attempts:'+box.id,hist);
 // paintNav ДО чтения relatedCta ниже: кнопка «дальше» на экране результата
 // должна отражать уже посчитанный pass, а не то, что было до этого теста
 paintNav();
 let h='<div class="resulttop">'+ringSvg(pct,pass)
  +'<div class="resultstat"><b>'+right+' / '+total+'</b><span>'+(pass?UI.passed:UI.pFailed)+'</span></div></div>';
 if(!pass)h+='<p class="meta">'+UI.passRule+'</p>';
 if(wrong.length){
  h+='<div class="mistakelist">';
  wrong.forEach(q=>{
   const qn=q.querySelector('.qn')?q.querySelector('.qn').textContent:'';
   const qtSpan=q.querySelector('.qt span:last-child');
   const qt=qtSpan?qtSpan.textContent:'';
   let yourAns,correctAns;
   if(q.dataset.type==='short'){
    yourAns=q.querySelector('input[type=text]').value||'—';
    correctAns=q.dataset.answer||'';
   }else{
    const map=optionTextMap(q);
    const inputs=[...q.querySelectorAll('.opt input')];
    const pickedIdx=inputs.filter(i=>i.checked).map(i=>parseInt(i.value,10));
    yourAns=pickedIdx.map(i=>map[i]).join(', ')||'—';
    const correctIdx=JSON.parse(q.dataset.correct||'[]');
    correctAns=correctIdx.map(i=>map[i]).join(', ');
   }
   h+='<div class="mistake"><div class="mn">'+escHtml(qn)+'</div><div class="mbody">'
    +'<div class="mq">'+escHtml(qt)+'</div>'
    +'<div class="ma bad"><i>'+UI.yourAnswer+':</i> '+escHtml(yourAns)+'</div>'
    +'<div class="ma ok"><i>'+UI.correctAnswer+':</i> '+escHtml(correctAns)+'</div>'
    +(q.dataset.ref?'<button type="button" class="ref" data-opench>'+escHtml(q.dataset.ref)+'</button>':'')
    +'</div></div>';
  });
  h+='</div>';
 }
 let btns='';
 if(wrong.length)btns+='<button type="button" class="cta" data-mistakes="'+box.id+'">'+UI.mistakes+'</button>';
 btns+='<button type="button" class="ghost" data-retry="'+box.id+'">'+UI.retry+'</button>';
 const relatedCta=document.querySelector('.cta[data-quiz="'+box.id+'"]');
 if(pass&&relatedCta)btns+='<a class="cta" href="'+relatedCta.getAttribute('href')+'">'+escHtml(relatedCta.textContent)+'</a>';
 h+='<div class="resultbtns">'+btns+'</div>';
 box.querySelector('.result').innerHTML=h;
 box.dataset.filter='';
 setQuizView(box,'result');
}
function retrySession(box){
 [...box.querySelectorAll('.qs > .q')].forEach(q=>{resetQuestion(q);delete q.dataset.everWrong;shuffleOptions(q)});
 shuffleQuestionOrder(box);
 box.dataset.filter='';
 box.dataset.idx=0;
 setQuizView(box,'qs');
}
function reviewMistakes(box){
 box.dataset.filter='wrong';
 box.dataset.idx=0;
 [...box.querySelectorAll('.qs > .q')].forEach(q=>{if(q.dataset.everWrong==='1')resetQuestion(q)});
 setQuizView(box,'qs');
}
function initQuizzes(){
 document.querySelectorAll('.card.session').forEach(box=>{
  box.querySelectorAll('.qs > .q').forEach(q=>shuffleOptions(q));
  shuffleQuestionOrder(box);
  setQuizView(box,'qs');
 });
}

/* ---------- события ---------- */
document.addEventListener('change',e=>{
 const opt=e.target.closest('.opt');
 if(opt){
  const q=opt.closest('.q');
  if(q.dataset.state)return;
  // одиночный выбор проверяется сразу — это и есть учебная петля «ответил → узнал»
  if(q.dataset.type==='single'){gradeQuestion(q);tally(q.closest('.card'))}
  return;
 }
 const chk=e.target.closest('.chk');
 if(chk){
  chk.classList.toggle('on',e.target.checked);
  save(chk.dataset.chk,e.target.checked);
  paintTask(chk.closest('.task'));
 }
});
document.addEventListener('input',e=>{
 if(e.target.matches('textarea[data-note]'))save(e.target.dataset.note,e.target.value);
 if(e.target.matches('#search'))filterNav(e.target.value);
});
document.addEventListener('click',e=>{
 const one=e.target.closest('[data-one]');
 if(one){const q=one.closest('.q');if(!q.dataset.state){gradeQuestion(q);tally(q.closest('.card'))}return}
 const retry=e.target.closest('[data-retry]');
 if(retry){
  const box=document.getElementById(retry.dataset.retry);
  retrySession(box);
  box.scrollIntoView({block:'start'});return;
 }
 const mist=e.target.closest('[data-mistakes]');
 if(mist){
  const box=document.getElementById(mist.dataset.mistakes);
  reviewMistakes(box);
  box.scrollIntoView({block:'start'});return;
 }
 const lv=e.target.closest('[data-listview]');
 if(lv){
  const box=lv.closest('.card.session');
  setQuizView(box,box.dataset.view==='list'?'qs':'list');
  return;
 }
 const sn=e.target.closest('[data-sessionnext]');
 if(sn){
  const box=sn.closest('.card.session');
  const i=+box.dataset.idx||0, qs=sessionQs(box);
  if(i>=qs.length-1){finalizeSession(box);return}
  box.dataset.idx=i+1;
  setQuizView(box,'qs');
  return;
 }
 const sp=e.target.closest('[data-sessionprev]');
 if(sp){
  const box=sp.closest('.card.session');
  const i=+box.dataset.idx||0;
  if(i>0){box.dataset.idx=i-1;setQuizView(box,'qs')}
  return;
 }
 const tab=e.target.closest('.tab');
 if(tab){showTab(tab.dataset.tab,tab.dataset.panel,true);return}
 const ref=e.target.closest('[data-opench]');
 if(ref){
  // ссылка на источник (в разборе ошибки или прямо в тексте конспекта [гл. N])
  // открывает панель источника этой же темы, при возможности — на нужной главе
  const sec=ref.closest('section');
  const h3=sec&&sec.querySelector('h3[id]');
  if(h3){
   const q=ref.closest('.q');
   openSource(h3.id, q?q.dataset.ref:ref.textContent);
  }
  return;
 }
 const srcbtn=e.target.closest('[data-source]');
 if(srcbtn){openSource(srcbtn.dataset.source,null);return}
 if(e.target.closest('#sourceclose')){closeSource();return}
 const goq=e.target.closest('[data-goquiz]');
 if(goq){
  e.preventDefault();
  const id=goq.dataset.goquiz;
  navigateHash('#'+id);
  showTab(id,'quiz',true);
  return;
 }
 const cta=e.target.closest('.cta[data-cta]');
 if(cta){
  e.preventDefault();
  const panel=cta.dataset.gotopanel;
  if(panel){
   // «читать конспект» / «пройти тест» — это ТА ЖЕ тема, просто другая вкладка
   showTab(cta.dataset.topic,panel,true);
   scrollToEl(document.getElementById(cta.dataset.topic));
  }else{
   navigateHash(cta.getAttribute('href'));
  }
  return;
 }
 const th=e.target.closest('.themebtn');
 if(th){const cur=getPref('theme','auto');const next=cur==='auto'?'light':cur==='light'?'dark':'auto';
  savePref('theme',next);applyTheme(next);return}
 const segbtn=e.target.closest('.segmented button');
 if(segbtn){
  const seg=segbtn.closest('.segmented');
  const val=seg.dataset.pref==='lh'?parseFloat(segbtn.dataset.val):parseInt(segbtn.dataset.val,10);
  savePref(seg.dataset.pref,val);
  applyReadingPrefs();
  return;
 }
 const readbtn=e.target.closest('#readbtn');
 if(readbtn){
  const pop=document.getElementById('readpop');
  const opening=pop.hasAttribute('hidden');
  if(opening){pop.removeAttribute('hidden');readbtn.setAttribute('aria-expanded','true')}
  else{pop.setAttribute('hidden','');readbtn.setAttribute('aria-expanded','false')}
  return;
 }
 const navtoggle=e.target.closest('#navtoggle');
 if(navtoggle){toggleDrawer();return}
 if(e.target.closest('#scrim')){
  if(document.body.classList.contains('source-open'))closeSource();
  else closeDrawer();
  return;
 }
 if(e.target.closest('#booknav a')){closeDrawer();/* не return — переход обрабатывает общий перехватчик ниже */}
 // общий перехватчик ссылок на страницы книги (оглавление, кнопки
 // «предыдущая/следующая тема», ссылка «Прогресс» и т.п.) — все ещё не
 // обработанные выше клики по #якорю, ведущему на существующую .page
 const pagelink=e.target.closest('a[href^="#"]');
 if(pagelink){
  const id=pagelink.getAttribute('href').slice(1);
  if(document.querySelector('.page[data-page="'+id+'"]')){
   e.preventDefault();
   navigateHash('#'+id);
   return;
  }
 }
 const cp=e.target.closest('[data-copy]');
 if(cp){copyTask(cp);return}
 const fc=e.target.closest('[data-card]');
 if(fc){cardAction(fc.dataset.card);return}
 // клик вне попапа настроек чтения — закрыть его
 const readpop=document.getElementById('readpop');
 if(readpop&&!readpop.hasAttribute('hidden')&&!e.target.closest('.popwrap')){
  readpop.setAttribute('hidden','');
  document.getElementById('readbtn').setAttribute('aria-expanded','false');
 }
});

/* ---------- практика: бланк, который заполняют прямо на странице ---------- */
function paintTask(task){
 if(!task)return;
 const all=[...task.querySelectorAll('.chk input')];
 const on=all.filter(i=>i.checked).length;
 const p=task.querySelector('.taskprog');
 if(p)p.textContent=on+' / '+all.length;
}
function copyTask(btn){
 const task=btn.closest('.task');
 const lines=[task.querySelector('h3').innerText,''];
 task.querySelectorAll('.tasklist').forEach(list=>{
  const h=list.previousElementSibling;
  if(h&&/^H\d$/.test(h.tagName))lines.push(h.innerText+':');
  list.querySelectorAll('.chk').forEach(c=>{
   lines.push((c.querySelector('input').checked?'[x] ':'[ ] ')+c.querySelector('.t').innerText);
  });
  lines.push('');
 });
 const note=task.querySelector('textarea[data-note]');
 if(note&&note.value.trim()){lines.push(UI.notes+':',note.value.trim())}
 const text=lines.join('\n');
 const done=()=>{const o=btn.textContent;btn.textContent=UI.copied;setTimeout(()=>btn.textContent=o,1600)};
 if(navigator.clipboard&&navigator.clipboard.writeText){
  navigator.clipboard.writeText(text).then(done,()=>fallbackCopy(text,done));
 }else fallbackCopy(text,done);
}
function fallbackCopy(text,done){
 const ta=document.createElement('textarea');ta.value=text;ta.style.position='fixed';ta.style.opacity='0';
 document.body.appendChild(ta);ta.select();
 try{document.execCommand('copy');done()}catch(e){}
 document.body.removeChild(ta);
}

/* ---------- карточки терминов ---------- */
let deck=[],deckPos=0,deckShown=false;
function deckInit(){
 const known=get('cards_known',[]);
 deck=GLOSSARY.filter(c=>!known.includes(c.t));
 if(!deck.length){deck=[]}
 deckPos=0;deckShown=false;deckRender();
}
function deckRender(){
 const el=document.getElementById('deck');if(!el)return;
 const meta=document.getElementById('deckmeta');
 if(!deck.length){
  el.innerHTML='<div class="flash-card"><div class="term">'+UI.cardsDone+' ✓</div></div>';
  if(meta)meta.textContent='';
  document.getElementById('deckact').innerHTML='<button class="ghost sm" data-card="reset">'+UI.cardsReset+'</button>';
  return;
 }
 const c=deck[deckPos%deck.length];
 el.innerHTML='<div class="flash-card"><div class="term">'+c.t+'</div>'+
  (deckShown?'<div class="tr">'+c.d+'</div>':'')+'</div>';
 if(meta)meta.textContent=(deckPos%deck.length+1)+' / '+deck.length;
 document.getElementById('deckact').innerHTML=deckShown
  ?'<button class="sm" data-card="know">'+UI.know+'</button>'+
   '<button class="ghost sm" data-card="again">'+UI.dontKnow+'</button>'
  :'<button class="sm" data-card="flip">'+UI.flip+'</button>';
}
function cardAction(a){
 if(!deck.length&&a!=='reset')return;
 if(a==='flip'){deckShown=true}
 else if(a==='know'){
  const c=deck[deckPos%deck.length];
  const known=get('cards_known',[]);known.push(c.t);save('cards_known',known);
  deck=deck.filter(x=>x.t!==c.t);deckShown=false;
  if(deckPos>=deck.length)deckPos=0;
 }
 else if(a==='again'){deckPos=(deckPos+1)%deck.length;deckShown=false}
 else if(a==='reset'){save('cards_known',[]);deckInit();return}
 deckRender();
}

/* ---------- карточки терминов: свайп вправо/влево = «Знаю»/«Повторить», тап
   по самой карточке = перевернуть (кнопки под колодой делают то же самое —
   свайп просто быстрее на телефоне). deckRender() каждый раз пересоздаёт
   .flash-card заново, поэтому слушатели навешаны на #deck, а не на саму карточку */
(function(){
 const deckEl=document.getElementById('deck');
 if(!deckEl)return;
 let startX=null,curX=null,dragged=false;
 deckEl.addEventListener('touchstart',e=>{
  if(!deck.length)return;
  startX=curX=e.touches[0].clientX;dragged=false;
  const card=deckEl.querySelector('.flash-card');
  if(card)card.style.transition='none'; // палец ведёт карточку без задержки на анимацию
 },{passive:true});
 deckEl.addEventListener('touchmove',e=>{
  if(startX==null)return;
  curX=e.touches[0].clientX;
  const dx=curX-startX;
  if(Math.abs(dx)>10)dragged=true;
  const card=deckEl.querySelector('.flash-card');
  if(card)card.style.transform='translateX('+dx+'px) rotate('+(dx/18)+'deg)';
 },{passive:true});
 deckEl.addEventListener('touchend',()=>{
  if(startX==null)return;
  const dx=curX-startX;
  const card=deckEl.querySelector('.flash-card');
  if(Math.abs(dx)>60){cardAction(dx>0?'know':'again')} // deckRender() создаст новую карточку взамен
  else if(card){card.style.transition='';card.style.transform=''} // не хватило — плавно назад в центр
  startX=curX=null;
 });
 deckEl.addEventListener('click',e=>{
  if(e.target.closest('[data-card]'))return; // кнопки — отдельный обработчик
  if(!dragged&&!deckShown&&deck.length)cardAction('flip');
 });
})();

/* ---------- поиск по оглавлению ---------- */
function filterNav(qs){
 const s=(qs||'').trim().toLowerCase();
 let shown=0;
 document.querySelectorAll('nav a[data-title]').forEach(a=>{
  const hit=!s||a.dataset.title.toLowerCase().includes(s);
  a.classList.toggle('hidden',!hit);
  if(hit)shown++;
 });
 document.querySelectorAll('.navsec').forEach(sec=>{
  const titleHit=s&&(sec.dataset.title||'').toLowerCase().includes(s);
  const any=[...sec.querySelectorAll('a[data-title]')].some(a=>!a.classList.contains('hidden'));
  if(titleHit)sec.querySelectorAll('a[data-title]').forEach(a=>a.classList.remove('hidden'));
  sec.classList.toggle('hidden',!!s&&!any&&!titleHit);
  // при поиске раскрываем найденное, при очистке возвращаем сохранённое состояние
  if(s)sec.open=any||titleHit;
  else sec.open=get('sec_'+sec.dataset.sec,sec.dataset.def==='1');
 });
 const nr=document.getElementById('noresult');
 if(nr)nr.style.display=s&&!shown?'':'none';
}

/* ---------- сводка по тестам ---------- */
function renderProgress(){
 const host=document.getElementById('progressbody');
 if(!host)return;
 const s=load();
 const taken=QUIZZES.filter(q=>s[q.id]);
 const passed=taken.filter(q=>s[q.id].pass);
 const avg=taken.length?Math.round(taken.reduce((a,q)=>a+s[q.id].pct,0)/taken.length):0;
 let h='<div class="pgrid">'+
  stat(passed.length+' / '+QUIZZES.length,UI.pPassed,passed.length===QUIZZES.length?'ok':'')+
  stat(taken.length+' / '+QUIZZES.length,UI.pTaken,'')+
  stat(taken.length?avg+'%':'—',UI.pAvg,taken.length?(avg>=80?'ok':'bad'):'')+
  '</div>';
 if(!taken.length){
  h+='<p class="emptynote">'+UI.pEmpty+'</p>';
  host.innerHTML=h;return;
 }
 h+='<div class="tablewrap"><table><thead><tr><th>'+UI.pTest+'</th><th>'+UI.pWhere+
    '</th><th>'+UI.pScore+'</th><th>'+UI.pStatus+'</th></tr></thead><tbody>';
 QUIZZES.forEach(q=>{
  const st=s[q.id];
  const pill=!st?'<span class="pill">'+UI.pNotTaken+'</span>'
   :st.pass?'<span class="pill ok">'+UI.passed+'</span>'
   :'<span class="pill bad">'+UI.pFailed+'</span>';
  const goq=q.tabbed?' data-goquiz="'+q.anchor+'"':'';
  h+='<tr><td><a href="#'+q.anchor+'"'+goq+'>'+q.title+'</a></td><td>'+q.sec+'</td><td>'+
     (st?st.pct+'%':'—')+'</td><td>'+pill+'</td></tr>';
 });
 h+='</tbody></table></div>';
 host.innerHTML=h;
}
function stat(v,l,cls){return '<div class="stat '+(cls||'')+'"><div class="v">'+v+'</div><div class="l">'+l+'</div></div>'}

/* ---------- навигация: галочки, прогресс, подсветка текущей темы ---------- */
function paintNav(){
 const s=load();let done=0,total=0;
 document.querySelectorAll('nav a[data-quiz]').forEach(a=>{
  total++;const st=s[a.dataset.quiz];
  a.classList.toggle('done',!!(st&&st.pass));
  if(st&&st.pass)done++;
 });
 const bar=document.getElementById('pbar');
 if(bar&&total){bar.style.width=Math.round(done/total*100)+'%';
  document.getElementById('ptext').textContent=done+' / '+total}
 const abarfill=document.getElementById('abarfill');
 if(abarfill&&total)abarfill.style.width=Math.round(done/total*100)+'%';
 document.querySelectorAll('[data-badge]').forEach(b=>{
  const st=s[b.dataset.badge];
  b.className='badge'+(st&&st.pass?' done':'');
  b.textContent=st?st.pct+'%':'';
  b.style.display=st?'':'none';
 });
 // зелёная точка на вкладке заданий, когда тест зачтён
 document.querySelectorAll('[data-dot]').forEach(dot=>{
  const st=s[dot.dataset.dot];
  dot.style.display=st&&st.pass?'':'none';
 });
 // счётчик пройденных тестов на самой свёрнутой шапке раздела
 document.querySelectorAll('.navsec').forEach(sec=>{
  const links=[...sec.querySelectorAll('a[data-quiz]')];
  const c=sec.querySelector('.cnt');
  if(!c)return;
  if(!links.length){c.textContent='';return}
  const ok=links.filter(a=>{const st=s[a.dataset.quiz];return st&&st.pass}).length;
  c.textContent=ok+'/'+links.length;
  c.classList.toggle('full',ok===links.length);
 });
 // степпер темы: кружок с номером становится галочкой, когда шаг пройден
 document.querySelectorAll('.tab[data-panel="digest"]').forEach(tb=>{
  const done=!!s['read:'+tb.dataset.tab];
  tb.classList.toggle('done',done);
  const n=tb.querySelector('.n');if(n)n.textContent=done?'✓':n.dataset.n;
 });
 document.querySelectorAll('.tab[data-panel="quiz"]').forEach(tb=>{
  const st=s[tb.dataset.tab+'_quiz'];
  const done=!!(st&&st.pass);
  tb.classList.toggle('done',done);
  const n=tb.querySelector('.n');if(n)n.textContent=done?'✓':n.dataset.n;
 });
 // главная кнопка темы: читать → пройти тест → дальше (следующая тема/
 // тест раздела/финал — в зависимости от того, что этой теме назначено при сборке)
 document.querySelectorAll('.cta[data-cta]').forEach(cta=>{
  const tid=cta.dataset.topic, quiz=cta.dataset.quiz;
  const read=!!s['read:'+tid];
  const st=quiz?s[quiz]:null;
  const passed=quiz?!!(st&&st.pass):true;
  let label,href,gotopanel='';
  if(!read){label=UI.ctaRead;href='#'+tid;gotopanel='digest'}
  else if(!passed){
   const qmeta=QUIZZES.find(q=>q.id===quiz);
   label=UI.ctaTestPrefix+' ('+(qmeta?qmeta.count:0)+' '+UI.ctaQuestions+')';
   href='#'+tid;gotopanel='quiz';
  }else if(cta.dataset.final){label=UI.exam;href='#'+cta.dataset.final}
  else if(cta.dataset.sectiontest){label=UI.sectionTest;href='#'+cta.dataset.sectiontest}
  else if(cta.dataset.next){label=UI.nextTopic;href='#'+cta.dataset.next}
  else{label=UI.ctaRead;href='#'+tid;gotopanel='digest'}
  cta.textContent=label;
  cta.setAttribute('href',href);
  cta.dataset.gotopanel=gotopanel;
 });
 renderProgress();
}

/* ---------- восстановление сохранённого ---------- */
function restore(){
 const s=load();
 document.querySelectorAll('.chk').forEach(c=>{
  if(s[c.dataset.chk]){c.querySelector('input').checked=true;c.classList.add('on')}
 });
 document.querySelectorAll('.task').forEach(paintTask);
 document.querySelectorAll('textarea[data-note]').forEach(t=>{
  if(s[t.dataset.note])t.value=s[t.dataset.note];
 });
 document.querySelectorAll('.card[id]').forEach(box=>{
  const t=box.querySelector('.tally');
  if(t&&box.querySelectorAll('.q').length)t.textContent=UI.answered+' 0/'+box.querySelectorAll('.q').length;
 });
}

/* ---------- клавиатура ---------- */
document.addEventListener('keydown',e=>{
 const tag=(e.target.tagName||'').toLowerCase();
 const typing=tag==='input'||tag==='textarea';
 if(e.key==='/'&&!typing){e.preventDefault();const s=document.getElementById('search');if(s)s.focus();return}
 if(e.key==='Escape'&&e.target.id==='search'){e.target.value='';filterNav('');e.target.blur();return}
 if(typing&&e.key==='Enter'){
  const q=e.target.closest('.q');
  if(q&&!q.dataset.state){e.preventDefault();gradeQuestion(q);tally(q.closest('.card'))}
  return;
 }
 if(typing)return;
 if(e.key==='Enter'){
  const q=currentQuestion();
  if(q&&!q.dataset.state){gradeQuestion(q);tally(q.closest('.card'))}
  return;
 }
 const idx=KEYS.indexOf(e.key);
 if(idx>=0){
  const q=currentQuestion();
  if(!q||q.dataset.state)return;
  const inputs=q.querySelectorAll('.opt input');
  if(idx<inputs.length){
   inputs[idx].checked=q.dataset.type==='multi'?!inputs[idx].checked:true;
   inputs[idx].dispatchEvent(new Event('change',{bubbles:true}));
  }
  return;
 }
 if(e.key==='ArrowRight'||e.key==='ArrowLeft'){
  const box=activeSessionBox();
  if(!box)return;
  e.preventDefault();
  const btn=box.querySelector(e.key==='ArrowRight'?'[data-sessionnext]':'[data-sessionprev]');
  if(!btn)return;
  const usable=e.key==='ArrowRight'?btn.style.display!=='none':btn.style.visibility!=='hidden';
  if(usable)btn.click();
 }
});
function activeSessionBox(){
 // сессия «в фокусе» — та, что реально попадает в видимую часть экрана;
 // на странице темы одновременно может существовать только одна открытая карточка теста
 return [...document.querySelectorAll('.card.session[data-view="qs"]')].find(box=>{
  const r=box.getBoundingClientRect();
  return r.top<window.innerHeight&&r.bottom>0;
 });
}
function currentQuestion(){
 // «текущий» — первый неотвеченный вопрос, попадающий в видимую часть экрана
 const qs=[...document.querySelectorAll('.q')];
 return qs.find(q=>{
  if(q.dataset.state)return false;
  const r=q.getBoundingClientRect();
  return r.top<window.innerHeight*0.9&&r.bottom>0;
 });
}

/* ---------- свайп между вопросами теста (влево — дальше, вправо — назад) —
   только когда текущий вопрос уже проверен, иначе смахнуть = случайно
   пропустить вопрос, не ответив ---------- */
let qSwipeX=null;
document.addEventListener('touchstart',e=>{
 const q=e.target.closest('.qs > .q');
 qSwipeX=(q&&q.dataset.state&&q.closest('.card.session')?.dataset.view==='qs')
  ?e.touches[0].clientX:null;
},{passive:true});
document.addEventListener('touchend',e=>{
 if(qSwipeX==null)return;
 const dx=e.changedTouches[0].clientX-qSwipeX;
 qSwipeX=null;
 if(Math.abs(dx)<60)return;
 const q=e.target.closest('.qs > .q');
 const box=q&&q.closest('.card.session');
 if(!box)return;
 const btn=box.querySelector(dx<0?'[data-sessionnext]':'[data-sessionprev]');
 if(!btn)return;
 const usable=dx<0?btn.style.display!=='none':btn.style.visibility!=='hidden';
 if(usable)btn.click();
});

/* ---------- вкладки темы ---------- */
function showTab(tid,panel,scroll){
 const tabs=[...document.querySelectorAll('.tab[data-tab="'+tid+'"]')];
 if(!tabs.length)return false;
 const target=tabs.find(t=>t.dataset.panel===panel)||tabs[0];
 tabs.forEach(t=>t.setAttribute('aria-selected',String(t===target)));
 document.querySelectorAll('.panel[data-of="'+tid+'"]').forEach(p=>{
  p.classList.toggle('on',p.dataset.panel===target.dataset.panel);
 });
 savePos(tid,target.dataset.panel);
 if(scroll){
  const bar=target.closest('.tabs');
  const r=bar.getBoundingClientRect();
  // подтягиваем к панели вкладок, только если она уехала за пределы экрана
  if(r.top<0||r.top>window.innerHeight*0.6)bar.scrollIntoView({block:'start'});
 }
 return true;
}
document.addEventListener('keydown',e=>{
 const tab=e.target.closest&&e.target.closest('.tab');
 if(!tab)return;
 if(e.key!=='ArrowRight'&&e.key!=='ArrowLeft')return;
 e.preventDefault();
 const tabs=[...document.querySelectorAll('.tab[data-tab="'+tab.dataset.tab+'"]')];
 const i=tabs.indexOf(tab);
 const next=tabs[(i+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length];
 showTab(next.dataset.tab,next.dataset.panel,false);next.focus();
});

/* ---------- вложенное оглавление: состояние разделов ---------- */
function initSections(){
 document.querySelectorAll('.navsec').forEach(sec=>{
  sec.open=get('sec_'+sec.dataset.sec,sec.dataset.def==='1');
  sec.addEventListener('toggle',()=>{
   if(!document.getElementById('search').value.trim())save('sec_'+sec.dataset.sec,sec.open);
  });
 });
}
function revealLink(a){
 const sec=a.closest('.navsec');
 if(sec&&!sec.open)sec.open=true;
}

/* ---------- подсветка текущей темы в оглавлении + шапке, позиция чтения ---------- */
if('IntersectionObserver' in window){
 const ab=document.querySelector('.appbar');
 const above=(ab?ab.offsetHeight:48)+8;
 const io=new IntersectionObserver(entries=>{
  entries.forEach(en=>{
   if(!en.isIntersecting)return;
   const a=document.querySelector('nav a[href="#'+en.target.id+'"]');
   if(!a)return;
   document.querySelectorAll('nav a.here').forEach(x=>x.classList.remove('here'));
   a.classList.add('here');
   revealLink(a);
   a.scrollIntoView({block:'nearest'});
   const ct=document.getElementById('curtopic');
   if(ct)ct.textContent=a.dataset.title||'';
   savePos(en.target.id);
  });
 },{rootMargin:'-'+above+'px 0px -65% 0px'});
 document.querySelectorAll('main h2[id],main h3[id]').forEach(h=>io.observe(h));
}

/* ---------- «конспект дочитан»: маркер в конце панели, шаг степпера
   зеленеет, когда он реально попал в кадр (не просто открыт) ---------- */
function initReadTracking(){
 const markers=[...document.querySelectorAll('.panel[data-panel="digest"] .endmarker')];
 if(!markers.length||!('IntersectionObserver' in window))return;
 const io=new IntersectionObserver(entries=>{
  entries.forEach(en=>{
   if(!en.isIntersecting)return;
   const tid=en.target.closest('.panel').dataset.of;
   if(get('read:'+tid,false))return;
   save('read:'+tid,true);
   paintNav();
  });
 });
 markers.forEach(m=>io.observe(m));
}

initSections();initQuizzes();restore();paintNav();deckInit();restorePosition();initReadTracking();
"""


def wrong_list(q, size):
    """wrongExplanations приходит от агентов то списком, то словарём {"0": "..."} — сводим к списку."""
    w = q.get("wrongExplanations") or []
    if isinstance(w, dict):
        return [str(w.get(str(i), w.get(i, ""))) for i in range(size)]
    # Агенты пишут либо список по всем вариантам (пустая строка на месте верного), либо
    # по одному объяснению на каждый НЕВЕРНЫЙ вариант без «дырок». Второй формат при
    # позиционной раскладке съезжает: объяснение уходит к соседнему варианту (в разных
    # курсах так выглядит ~19% вопросов). Узнаём его по длине и раскладываем по неверным.
    correct = {i for i in (q.get("correct") or []) if isinstance(i, int)}
    if correct and len(w) != size and len(w) == size - len(correct):
        it = iter(w)
        return ["" if i in correct else str(next(it)) for i in range(size)]
    return [str(w[i]) if i < len(w) else "" for i in range(size)]


def render_quiz(qid, questions, title, shuffle_questions=False, is_exam=False):
    """Тест как сессия: один вопрос на экран (JS переключает .q через data-idx),
    варианты в исходном порядке — их порядок читатель видит перетасованным
    заново при каждой попытке через JS (см. shuffleOptions()), а не при сборке:
    иначе refresh страницы каждый раз показывал бы один и тот же порядок.
    input.value = исходный индекс варианта — переживает перестановку узлов.
    """
    if not questions:
        return ""
    parts = ['<div class="card session" id="%s" data-shuffleq="%d" data-exam="%d" '
             'data-view="qs" data-idx="0"><div class="quizhead"><h3>%s</h3>'
             '<span class="tally"></span>'
             '<button type="button" class="ghost sm" data-listview>%s</button></div>'
             '<div class="sessionbar"><span class="sessionpos"></span>'
             '<div class="sessionprog"><i></i></div></div><div class="qs">'
             % (qid, 1 if shuffle_questions else 0, 1 if is_exam else 0,
                html.escape(title), UI["sessionList"])]
    for i, q in enumerate(questions):
        qtype = q.get("type", "single")
        options = q.get("options") or []
        section_attr = (' data-section="%s"' % html.escape(str(q["sectionId"]), quote=True)
                        if q.get("sectionId") else "")
        parts.append('<div class="q" data-type="%s" data-correct=\'%s\' data-wrong=\'%s\' '
                     'data-expl="%s" data-ref="%s" data-answer="%s"%s>'
                     % (qtype, json.dumps(q.get("correct", [])),
                        html.escape(json.dumps(wrong_list(q, len(options)), ensure_ascii=False), quote=True),
                        html.escape(q.get("explanation", ""), quote=True),
                        html.escape(norm_ref(q.get("ref", "")), quote=True),
                        html.escape(q.get("shortAnswer", ""), quote=True),
                        section_attr))
        parts.append('<div class="qt"><span class="qn">%02d</span><span>%s</span></div>'
                     % (i + 1, html.escape(q.get("q", ""))))
        if qtype == "short":
            parts.append('<input type="text" placeholder="%s">' % UI["yourAnswer"])
            parts.append('<div class="qact"><button class="ghost sm" data-one>%s</button></div>' % UI["check"])
        else:
            itype = "checkbox" if qtype == "multi" else "radio"
            parts.append('<div class="opts">')
            for j, opt in enumerate(options):
                key = str(j + 1) if j < 9 else ""
                # value — исходный индекс варианта; переставляя .opt в DOM при
                # перетасовке, gradeQuestion() всё равно найдёт верный ответ по value
                parts.append('<label class="opt"><input type="%s" name="%s_%d" value="%d">'
                             '<span class="k">%s</span><span>%s</span></label>'
                             % (itype, qid, i, j, key, html.escape(str(opt))))
            parts.append("</div>")
            # у multi нет момента «выбор завершён» — нужен явный шаг проверки
            if qtype == "multi":
                parts.append('<div class="qact"><button class="ghost sm" data-one>%s</button></div>' % UI["check"])
        parts.append('<div class="fb"></div></div>')
    parts.append("</div>")  # .qs
    parts.append('<div class="sessionnav">'
                 '<button type="button" class="ghost sm" data-sessionprev>%s</button>'
                 '<button type="button" class="cta sm" data-sessionnext style="display:none"></button>'
                 '</div>' % UI["sessionPrev"])
    parts.append('<div class="result"></div>')
    parts.append('<p class="hint">%s</p></div>' % UI["keyHints"])
    return "\n".join(parts)


def render_practice(p, title, key):
    """Практика — не текст, а бланк: шаги и критерии отмечаются, заметки сохраняются."""
    if not p:
        return ""
    h = ['<div class="card task"><div class="quizhead"><h3>%s: %s</h3>'
         '<span class="taskprog"></span></div>' % (title, html.escape(p.get("title", "")))]
    if p.get("description"):
        h.append("<p>%s</p>" % html.escape(p["description"]))
    if p.get("timeEstimate"):
        h.append('<p class="meta">%s: %s</p>' % (UI["time"], html.escape(str(p["timeEstimate"]))))
    if p.get("steps"):
        h.append("<h4>%s</h4><ul class=\"tasklist\">" % UI["steps"])
        for i, s in enumerate(p["steps"]):
            h.append('<li><label class="chk" data-chk="%s_s%d"><input type="checkbox">'
                     '<span class="stepn">%02d</span><span class="t">%s</span></label></li>'
                     % (key, i, i + 1, html.escape(str(s))))
        h.append("</ul>")
    if p.get("expectedResult"):
        h.append("<h4>%s</h4><p>%s</p>" % (UI["expected"], html.escape(str(p["expectedResult"]))))
    if p.get("checklist"):
        h.append("<h4>%s</h4><ul class=\"tasklist\">" % UI["checklist"])
        for i, c in enumerate(p["checklist"]):
            h.append('<li><label class="chk" data-chk="%s_c%d"><input type="checkbox">'
                     '<span class="t">%s</span></label></li>' % (key, i, html.escape(str(c))))
        h.append("</ul>")
    h.append('<h4>%s</h4><textarea data-note="%s_note" placeholder="%s"></textarea>'
             % (UI["notes"], key, UI["notesPlaceholder"]))
    h.append('<div class="row"><button class="ghost sm" data-copy>%s</button></div>' % UI["copy"])
    h.append("</div>")
    return "\n".join(h)


def render_topic_tabs(t, qid):
    """Тема как маршрут «Конспект → Тест» (+ «Практика», если есть).

    Полный текст главы — больше не шаг маршрута, а справочник: панель остаётся
    в DOM (data-panel=text), но открывается отдельной выезжающей панелью
    источника, а не переключением вкладки — см. openSource() в JS.
    """
    tid = t["id"]
    tabs, panels = [], []

    def add(panel, label, content, active=False, mark=""):
        # префикс panel_ обязателен: без него id панели «quiz» совпал бы с id
        # карточки теста внутри неё, а getElementById вернул бы не тот элемент
        pid = "panel_%s_%s" % (tid, panel)
        n = len(tabs) + 1
        tabs.append('<button class="tab" role="tab" type="button" data-tab="%s" data-panel="%s" '
                    'aria-selected="%s" aria-controls="%s"><span class="n" data-n="%d">%d</span>'
                    '<span>%s</span>%s</button>'
                    % (tid, panel, "true" if active else "false", pid, n, n,
                       html.escape(label), mark))
        panels.append('<div class="panel%s" id="%s" role="tabpanel" data-of="%s" data-panel="%s">%s</div>'
                      % (" on" if active else "", pid, tid, panel, content))

    if t["chapterHtml"]:
        # не add(): полный текст не участвует в степпере и не получает кнопку-вкладку
        panels.append('<div class="panel" id="panel_%s_text" data-of="%s" data-panel="text">%s</div>'
                      % (tid, tid, t["chapterHtml"]))
    # end-marker — по нему JS узнаёт, что читатель дочитал конспект до конца
    add("digest", UI["tabDigest"], t["materialHtml"] + '<div class="endmarker"></div>', active=True)
    if t["questions"]:
        add("quiz", UI["tabQuiz"], render_quiz(qid, t["questions"], UI["quiz"]),
            mark='<span class="dot" data-dot="%s" style="display:none"></span>' % qid)
    if t["practice"]:
        add("practice", UI["tabPractice"], render_practice(t["practice"], UI["practice"], tid))

    source_btn = ('<button type="button" class="ghost sm sourcebtn" data-source="%s">%s</button>'
                  % (tid, UI["openSource"])) if t["chapterHtml"] else ""

    # «Источник» — своей строкой под степпером, а не в одном ряду с ним:
    # в узком степпере из двух-трёх шагов лишний элемент отжимал у «Тестовые
    # задания» место и обрезал подпись без намёка на прокрутку
    return ('<div class="tabsrow"><div class="tabs steps" role="tablist">%s</div></div>%s%s'
            % ("".join(tabs), source_btn, "".join(panels)))


def render_chapter_nav(order, idx, section_test_anchor=None, final_anchor=None):
    """Главная кнопка темы (.cta, состояние считает JS) + «предыдущая/следующая
    тема» — второстепенная навигация под ней. Обе работают поверх любой открытой
    вкладки, т.к. стоят после блока вкладок, а не внутри панели."""
    t = order[idx]
    prev_t = order[idx - 1] if idx > 0 else None
    next_t = order[idx + 1] if idx + 1 < len(order) else None

    def btn(tt, cls, dir_label):
        if not tt:
            return '<span class="navbtn %s empty"></span>' % cls
        return ('<a class="navbtn %s" href="#%s"><span class="nb-dir">%s</span>'
                '<span class="nb-title">%s</span></a>'
                % (cls, tt["id"], dir_label, html.escape(tt["title"])))

    cta = ('<a class="cta" data-cta data-topic="%s" data-quiz="%s" data-next="%s" '
           'data-sectiontest="%s" data-final="%s"></a>'
           % (t["id"], (t["id"] + "_quiz") if t["questions"] else "",
              next_t["id"] if next_t else "",
              section_test_anchor or "", final_anchor or ""))

    if not prev_t and not next_t:
        return cta

    return (cta + '<nav class="chapternav" aria-label="%s">%s%s</nav>'
            % (html.escape(UI["chapterNav"], quote=True),
               btn(prev_t, "prev", "‹ " + UI["prevTopic"]),
               btn(next_t, "next", UI["nextTopic"] + " ›")))


def render_cards(glossary):
    if not glossary:
        return "", ""
    body = ('<div class="eyebrow">%s</div><h2 id="cards">%s</h2>'
            '<p class="meta">%s</p>'
            '<div class="card"><div class="deck"><div id="deck"></div>'
            '<div class="deckmeta" id="deckmeta"></div>'
            '<div class="row" id="deckact"></div></div></div>'
            % (UI["cards"], UI["cards"], UI["cardsHint"]))
    nav = '<a href="#cards" data-title="%s">%s</a>' % (UI["cards"], UI["cards"])
    return nav, body


def build(course):
    d = collect(course)
    nav = ['<nav id="booknav"><div class="navhead"><div><h1>%s</h1><div class="author">%s</div></div>'
           '<button class="iconbtn themebtn" title="%s" aria-label="%s">◐</button></div>'
           % (html.escape(d["title"]), html.escape(d["author"]), UI["theme"], UI["theme"])]
    nav.append('<div class="pmeta"><span>%s</span><span id="ptext"></span></div>'
               '<div class="pbar"><i id="pbar"></i></div>' % UI["progress"])
    nav.append('<div class="searchbox"><input id="search" type="text" placeholder="%s" '
               'autocomplete="off"></div><div class="noresult" id="noresult" style="display:none">%s</div>'
               % (UI["search"], UI["searchEmpty"]))
    nav.append('<a class="toplink" href="#progress" data-title="%s">%s</a>'
               % (UI["progressPage"], UI["progressPage"]))
    body = ['<section class="page current" data-page="progress"><div class="eyebrow">%s</div>'
            '<h2 id="progress">%s</h2><div id="progressbody"></div></section>'
            % (UI["progress"], UI["progressPage"])]
    quizzes = []

    for n, sec in enumerate(d["sections"], 1):
        # нумерация разделов — не украшение: курс проходится по порядку
        sec_label = "%s %02d" % (UI["section"], n)
        # раздел открыт по умолчанию, если в нём уже есть готовый материал
        default_open = "1" if any(t["ready"] for t in sec["topics"]) else "0"
        nav.append('<details class="navsec" data-sec="%s" data-def="%s" data-title="%s">'
                   '<summary><span class="n">%02d</span><span class="st">%s</span>'
                   '<span class="cnt"></span></summary><div class="items">'
                   % (sec["id"], default_open, html.escape(sec["title"], quote=True),
                      n, html.escape(sec["title"])))
        # эйбрио раздела теперь не отдельный блок в общей ленте, а часть
        # СТРАНИЦЫ первой темы раздела — у каждой темы своя страница, у
        # эйбрио своей страницы нет и никогда не было отдельной ссылки на него
        sec_intro = '<div class="eyebrow">%s</div><h2 id="%s">%s</h2>' % (sec_label, sec["id"], html.escape(sec["title"]))
        for topic_idx, t in enumerate(sec["topics"]):
            qid = t["id"] + "_quiz"
            cls = "" if t["ready"] else ' class="wip"'
            attr = ' data-quiz="%s"' % qid if t["questions"] else ""
            if t["questions"]:
                quizzes.append({"id": qid, "title": t["title"], "sec": sec_label,
                                "anchor": t["id"], "tabbed": True, "count": len(t["questions"])})
            nav.append('<a href="#%s"%s%s data-title="%s">%s</a>'
                       % (t["id"], cls, attr, html.escape(t["title"], quote=True), html.escape(t["title"])))
            badge = '<span class="badge" data-badge="%s" style="display:none"></span>' % qid if t["questions"] else ""
            # одна тема — одна страница (.page): дочитал до конца — упёрся в
            # кнопку перехода, а не в начало следующей темы; section — не
            # декорация, а ограничивает область поиска главы для ссылки-источника
            body.append('<section class="page" data-page="%s">' % t["id"])
            body.append(sec_intro if topic_idx == 0 else "")
            body.append('<h3 id="%s">%s%s</h3>' % (t["id"], html.escape(t["title"]), badge))
            if not t["ready"]:
                body.append('<p class="wip-note">— %s —</p></section>' % UI["inProgress"])
                continue
            meta_bits = []
            if t.get("minutes"):
                meta_bits.append(UI["minShort"] % t["minutes"])
            if t["questions"]:
                meta_bits.append("%d %s" % (len(t["questions"]), UI["ctaQuestions"]))
            if t.get("chapterRange"):
                meta_bits.append(t["chapterRange"])
            if meta_bits:
                body.append('<p class="meta">%s</p>' % " · ".join(meta_bits))
            body.append(render_topic_tabs(t, qid))
            # пред/след — только внутри раздела: соседняя тема из другого раздела
            # не «своя» (то же ограничение, что и boundaryRule в book-topics.js)
            is_last_in_section = topic_idx == len(sec["topics"]) - 1
            has_section_test = bool(sec.get("test") and sec["test"].get("questions"))
            section_test_anchor = sec["id"] + "_test" if is_last_in_section and has_section_test else None
            is_last_section = n == len(d["sections"])
            has_exam = bool(d["exam"] and d["exam"].get("questions"))
            final_anchor = "exam" if is_last_in_section and is_last_section and has_exam else None
            body.append(render_chapter_nav(sec["topics"], topic_idx, section_test_anchor, final_anchor))
            body.append("</section>")
        if sec.get("test") and sec["test"].get("questions"):
            tid = sec["id"] + "_test"
            nav.append('<a href="#%s" data-quiz="%s" data-title="%s"><b>%s</b></a>'
                       % (tid, tid, UI["sectionTest"], UI["sectionTest"]))
            quizzes.append({"id": tid, "title": UI["sectionTest"], "sec": sec_label, "anchor": tid,
                            "count": len(sec["test"]["questions"])})
            # id не дублируем: он принадлежит карточке теста, иначе getElementById
            # вернёт заголовок и кнопки «заново»/«работа над ошибками» перестанут работать
            body.append('<section class="page" data-page="%s">' % tid)
            body.append('<h3>%s: %s</h3>' % (UI["sectionTest"], html.escape(sec["title"])))
            body.append(render_quiz(tid, sec["test"]["questions"], UI["sectionTest"], shuffle_questions=True))
            body.append("</section>")
        nav.append("</div></details>")

    cards_nav, cards_body = render_cards(d["glossary"])

    if d["summaryHtml"] or d["exam"] or d["project"] or cards_body:
        nav.append('<details class="navsec" data-sec="final" data-def="1" data-title="%s">'
                   '<summary><span class="n">◆</span><span class="st">%s</span>'
                   '<span class="cnt"></span></summary><div class="items">'
                   % (UI["final"], UI["final"]))
        # «Финал» — не отдельная страница, а ярлык на первой из summary/exam/
        # project (как эйбрио раздела выше); у карточек терминов свой ярлык
        final_eyebrow_used = False

        def final_eyebrow():
            nonlocal final_eyebrow_used
            if final_eyebrow_used:
                return ""
            final_eyebrow_used = True
            return '<div class="eyebrow">%s</div>' % UI["final"]

        if d["summaryHtml"]:
            nav.append('<a href="#summary" data-title="%s">%s</a>' % (UI["summary"], UI["summary"]))
            body.append('<section class="page" data-page="summary">%s<h2 id="summary">%s</h2>%s</section>'
                        % (final_eyebrow(), UI["summary"], d["summaryHtml"]))
        if d["exam"] and d["exam"].get("questions"):
            # id карточки — "exam_quiz", не "exam": иначе он совпал бы с id заголовка
            # <h2 id="exam"> ниже, и document.getElementById('exam') (retry/mistakes)
            # находил бы заголовок вместо карточки теста
            nav.append('<a href="#exam" data-quiz="exam_quiz" data-title="%s"><b>%s</b></a>' % (UI["exam"], UI["exam"]))
            quizzes.append({"id": "exam_quiz", "title": UI["exam"], "sec": UI["final"], "anchor": "exam",
                            "count": len(d["exam"]["questions"])})
            body.append('<section class="page" data-page="exam">%s<h2 id="exam">%s</h2>%s</section>'
                        % (final_eyebrow(), UI["exam"],
                           render_quiz("exam_quiz", d["exam"]["questions"], UI["exam"],
                                       shuffle_questions=True, is_exam=True)))
        if d["project"]:
            nav.append('<a href="#project" data-title="%s">%s</a>' % (UI["project"], UI["project"]))
            body.append('<section class="page" data-page="project">%s<h2 id="project">%s</h2>%s</section>'
                        % (final_eyebrow(), UI["project"],
                           render_practice(d["project"], UI["project"], "project")))
        if cards_body:
            nav.append(cards_nav)
            body.append('<section class="page" data-page="cards">%s</section>' % cards_body)
        nav.append("</div></details>")
    nav.append("</nav>")

    # Golos Text / Literata / JetBrains Mono — все три с полноценной кириллицей,
    # системные фолбэки на случай, если шрифты не догрузятся
    fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
             '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
             'family=Golos+Text:wght@400;500;600;700&'
             'family=Literata:opsz,wght@7..72,400;7..72,500;7..72,600&'
             'family=JetBrains+Mono:wght@400;500&display=swap">')
    slug = os.path.basename(os.path.normpath(course))
    js = (JS.replace("__UI__", json.dumps(UI, ensure_ascii=False))
            .replace("__GLOSSARY__", json.dumps(d["glossary"], ensure_ascii=False))
            .replace("__QUIZZES__", json.dumps(quizzes, ensure_ascii=False))
            .replace("__SLUG__", json.dumps(slug, ensure_ascii=False)))
    def segmented(pref, options):
        # options: [(значение, подпись)]; активная кнопка подсвечивается в JS (applyReadingPrefs)
        return ('<div class="segmented" data-pref="%s">%s</div>'
                % (pref, "".join('<button type="button" data-val="%s">%s</button>' % (v, html.escape(l))
                                 for v, l in options)))

    reading_pop = (
        '<div class="pop" id="readpop" hidden>'
        '<div class="popgroup"><span class="poplabel">%s</span>%s</div>'
        '<div class="popgroup"><span class="poplabel">%s</span>%s</div>'
        '<div class="popgroup"><span class="poplabel">%s</span>%s</div>'
        '</div>'
        % (UI["fontSize"], segmented("fs", [("16", "S"), ("18", "M"), ("20", "L"), ("22", "XL")]),
           UI["textWidth"], segmented("measure", [("60", UI["widthNarrow"]), ("72", UI["widthNormal"]),
                                                   ("88", UI["widthWide"])]),
           UI["lineSpacing"], segmented("lh", [("1.5", UI["spacingTight"]), ("1.7", UI["spacingNormal"]),
                                                ("1.9", UI["spacingLoose"])]))
    )
    # Верхняя панель — общая для всех размеров экрана: на узком открывает
    # оглавление шторкой, на любом держит кнопки библиотеки/офлайн (слот
    # заполняет pwa/build.py) и текущую тему вместо плавающих кружков.
    appbar = ('<header class="appbar">'
              '<button class="menubtn" id="navtoggle" type="button" aria-controls="booknav" '
              'aria-expanded="false" aria-label="%s"><span class="menuicon" aria-hidden="true"></span></button>'
              '<div class="appbar-mid"><div class="curtopic" id="curtopic"></div>'
              '<div class="abar"><i id="abarfill"></i></div></div>'
              '<span id="lib-slot" class="libslot"></span>'
              '<div class="popwrap">'
              '<button class="iconbtn" id="readbtn" type="button" aria-expanded="false" '
              'title="%s" aria-label="%s">Aa</button>%s</div>'
              '<button class="iconbtn themebtn" type="button" title="%s" aria-label="%s">◐</button>'
              '</header><div class="scrim" id="scrim"></div>'
              '<aside id="source" role="dialog" aria-label="%s" aria-hidden="true" class="drawer">'
              '<div class="drawerhead"><b id="sourcetitle"></b>'
              '<button type="button" class="iconbtn" id="sourceclose" aria-label="%s">✕</button></div>'
              '<div id="sourcebody"></div></aside>'
              % (html.escape(UI["toc"], quote=True),
                 UI["readSettings"], UI["readSettings"], reading_pop,
                 UI["theme"], UI["theme"],
                 html.escape(UI["openSource"], quote=True), UI["closeSource"]))
    # Настройки чтения читаются из localStorage до основного скрипта (который
    # выполняется в конце body) — иначе на миг мелькнёт вёрстка с размерами
    # по умолчанию, прежде чем применятся сохранённые читателем настройки.
    prefs_preload = ('<script>(function(){try{'
                      "var p=JSON.parse(localStorage.getItem('tb:prefs')||'{}');"
                      "var r=document.documentElement.style;"
                      "if(p.fs)r.setProperty('--fs',p.fs+'px');"
                      "if(p.measure)r.setProperty('--measure',p.measure+'ch');"
                      "if(p.lh)r.setProperty('--lh',p.lh);"
                      '}catch(e){}})();</script>')
    doc = ("<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
           "<title>%s</title>\n%s\n<style>%s</style>\n%s\n"
           "%s\n<div class=\"wrap\">%s<main>%s</main></div>\n<script>%s</script>"
           % (html.escape(d["pageTitle"]), fonts, CSS, prefs_preload,
              appbar, "\n".join(nav), "\n".join(body), js))
    out = os.path.join(course, "textbook.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    ready = sum(1 for s in d["sections"] for t in s["topics"] if t["ready"])
    total = sum(len(s["topics"]) for s in d["sections"])
    qs = sum(len(t["questions"]) for s in d["sections"] for t in s["topics"])
    tasks = sum(1 for s in d["sections"] for t in s["topics"] if t["practice"])
    print("Собрано: %s (%d/%d тем, %d вопросов, %d практик, %d карточек)"
          % (out, ready, total, qs, tasks, len(d["glossary"])))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build_textbook.py <course_dir>")
    build(sys.argv[1])
