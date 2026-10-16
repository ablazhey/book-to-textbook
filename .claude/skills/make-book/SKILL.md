---
name: make-book
description: Turns a book (epub or pdf) into an interactive HTML textbook — locally, with no publishing. Per-topic notes, quizzes with explanations and chapter references, section tests, a final exam, a summary and an end-to-end project. Use when asked to "make a textbook from this book", "process this book", "/make-book path/to/book.epub" (also: «сделай учебник из книги», «обработай эту книгу»). The result is a single file courses/<slug>/textbook.html that opens with a double click. It never pushes or uploads anything.
---

# make-book — book → interactive textbook (local)

You drive a pipeline of ready-made workflows in `.claude/workflows/`. Subagents inside the workflows write the notes and quizzes; your job is to prepare the input, launch the batches, **recover from failures**, and assemble the result. Everything stays on this computer: no `git push`, no deploy, no uploads, no publishing. Talk to the user in the user's language.

## 0. Before you start

Check, and tell the user if something is missing:
- the **Workflow** tool is available (otherwise the pipeline cannot run — say so and stop);
- `python3 --version` (epub extraction and the build use only the standard library, tested on 3.9; PDF needs pypdf, see below);
- for PDF: `python3 -c "import pypdf"`; if it fails, offer `pip3 install pypdf`;
- for mobi/azw3/fb2 there is no extractor — offer to convert to epub (`ebook-convert book.mobi book.epub` from Calibre).

Input: the path to the book + the textbook language (default: the language the user writes in) + `--auto` (optional: don't wait for confirmation after the pilot). If there is no path, ask once.

Warn about the cost up front: this uses **a lot of tokens** (every topic gets an author, a critic, a quiz writer and a quiz critic; roughly 0.5–2 million subagent tokens per topic including retries — a ~50-topic book is tens of millions). The pilot will give the real figure. The computer must not sleep during a long run: start `caffeinate -dimsu -t 28800 &` (macOS) or disable sleep another way — when the machine sleeps, agents fail in bulk.

## 1. Extract the chapters (stage 0, no AI)

`slug` is a short Latin name derived from the book title, `courseDir = courses/<slug>`.

```bash
python3 .claude/workflows/scripts/extract_epub.py "<book.epub>" courses/<slug>
python3 -I .claude/workflows/scripts/extract_pdf.py "<book.pdf>" courses/<slug>
```
(one of the two). You get `chapters/chNN.md`, `toc.json` and `images/`. Then record the textbook language, which the build uses to pick the page interface (en or ru; any other language falls back to en):

```bash
echo '{"lang":"<lang>"}' > courses/<slug>/course.json
```
 Read the script's output: the number of chapters and words. Pieces like "Part 1", "Foreword", "Reference materials" of 50–300 words are normal — the structurer will sort them out. If the whole book came out as one file, or nothing came out, stop and tell the user (a PDF without bookmarks cannot be cut this way).

If the book's language differs from the textbook language, no translation is needed: the authors write the notes in the target language directly from the original. Use `book-translate` only when the user explicitly asks for a full translation of the chapters.

## 2. The map (stage 1)

```
Workflow({name:'book-map', args:{courseDir:'courses/<slug>', lang:'<ru|uk|en|…>'}})
```
This produces `courseDir/map.json`: sections → topics (`id, title, minutes, chapterFiles, summary, applied`). Read it yourself and check that every chapter is covered and there are no stub topics. The critic sometimes reports "map.json is missing" because of the resume cache — trust the file, not the report.

## 3. The pilot (stages 2–3 on two topics)

Take two topics from **one section**: one with `applied:false` and one with `applied:true`. Run:

```
Workflow({name:'book-topics', args:{
  courseDir:'courses/<slug>', lang:'<lang>',
  topics:[ …the topic objects taken WHOLE from map.json, including minutes… ],
  rules:'', hasGlossary:false,
  sectionTopics:[ …ALL topics of the section as {id,title,summary}… ]
}})
```
Two rules whose violation silently ruins the result:
- **`minutes` is mandatory.** The word budget is computed from it (minutes × 180). Without it every topic gets the 12-minute default.
- **`sectionTopics` is mandatory.** Without it the agent can't see the neighbouring topics and starts retelling them.

After the pilot show the user: `courses/<slug>/textbook.html` (built automatically), the size of the notes, the number of questions, the **tokens spent** (`usage.subagent_tokens` in the final notification) and a forecast for the whole book = tokens per topic × number of topics. Unless `--auto`, ask (AskUserQuestion): continue as is / the format needs changes. Write the user's corrections as one line in `rules` and pass it to all following batches.

## 4. Batches by section

One section at a time, at most 5 topics per batch (a 12-topic section = 3 batches), with the same `book-topics` call. For every batch `sectionTopics` is the whole section.

Always pass `lang` in the args of every workflow call: the prompts use it to pick the reference markers (`[ch. N, p. X]` for English, `[гл. N, стр. X]` for Russian) and figure captions.

**Recovering from failures is the most important part.** Dropped connections and computer sleep kill some agents in every run. The workflow result gives `material.verdict` and `quiz.questions` per topic. A batch is done only when, **for all topics at the same time**, `material.verdict ≠ failed` and `quiz.questions > 0`. Otherwise:

```
Workflow({scriptPath:'<scriptPath from the launch response>', resumeFromRunId:'<Run ID>', args:<THE SAME args, in full>})
```
- Pass `args` again every time — a resume without them fails (`Cannot destructure property 'courseDir'`).
- The resume cache works on a prefix of the agent calls, so topics that were already done sometimes "roll back" to failed — that is normal, just keep resuming until everything converges in a single result. Don't cap the number of attempts (3–6 resumes per batch is typical).
- If a critic failed, its call is silently counted as "approve". That doesn't block anything, but spot-check with `grep -c '"q"' topics/<id>.quiz.json` — a quiz should have 5–10 questions (11–16 occasionally slip through).
- Launch workflows by the `scriptPath` returned on the first launch, never by `name` after you edited a script: the tool snapshots named workflows when the session starts, so edits made mid-session are not picked up. Don't edit a script while a run uses it.
- While a workflow runs, don't poll in a loop; a completion notification will arrive.

After each converged batch tell the user the progress in one line (N of total topics).

## 5. Section tests and the final stage

When all topics of a section are done, run the section test (one section per call):
```
Workflow({name:'book-section-test', args:{courseDir:'courses/<slug>', lang:'<lang>',
  section:{id:'s1', title:'…'}, topicIds:['s1t1','s1t2', …]}})
```
It has converged when `questions > 0` and `verdict ≠ skipped`; otherwise resume as above.

When all sections are done:
```
Workflow({name:'book-final', args:{courseDir:'courses/<slug>', lang:'<lang>', bookTitle:'<book title>'}})
```
It produces `final/summary.md`, `final/exam.json` (20–30 questions) and `final/project.json` (if the book is hands-on). It has converged when both the summary and the exam exist.

You can go section by section without waiting for the end of the book, but don't launch several batches in parallel — you will run into rate limits and more failures.

## 6. Build and show (local)

```bash
python3 .claude/workflows/scripts/build_textbook.py courses/<slug>
open courses/<slug>/textbook.html      # macOS; Linux: xdg-open; Windows: start
```
The file works without internet and without a server (images sit next to it in `images/`, links are relative; the only external thing is Google Fonts, replaced by system fonts when offline) — the `courses/<slug>/` folder can be zipped and sent as is. The reader's progress is stored in the browser (localStorage); a topic counts as passed at ≥80% correct answers.

Final report to the user: the path to `textbook.html`, the number of topics and questions, which topics came out with caveats (too many/too few questions, a critic failed), and the total tokens spent.

## What not to do
- Don't publish or upload the result unless the user explicitly asks; this is a local tool.
- Don't edit `chapters/` by hand and don't rewrite notes around the workflows — the critics check the text against the original.
- Don't run two workflows of the same course at once.
- Don't promise that every error was caught: the critics catch many factual errors (numbers, invented details, retelling of neighbouring topics) but that is not a guarantee — for important courses skim at least the pilot topics yourself.

## Other workflows
- `book-trim` — if finished notes came out longer than their stated time or duplicate their neighbours: `args {courseDir, lang, topics:[{id,title,minutes,chapterFiles,summary}]}`; it also checks that the questions can still be answered from the shortened text.
- `book-translate` — full chapter translation plus a shared glossary: `args {courseDir, lang, chapters:['chapters/ch01.md',…], needGlossary:true|false}`; after it, set `hasGlossary:true` in `book-topics`.
