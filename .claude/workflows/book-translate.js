export const meta = {
  name: 'book-translate',
  description: 'Этап 0.5: перевод глав книги — переводчик + критик перевода, общий глоссарий терминов',
  whenToUse: 'Только если оператор включил ПЕРЕВОД КНИГИ=да; вызывается батчами вместе с разделами (главы пилота — на пилоте)',
  phases: [
    { title: 'Глоссарий', detail: 'первая глава: перевод + формирование глоссария' },
    { title: 'Перевод', detail: 'перевод остальных глав строго по глоссарию' },
    { title: 'Критика перевода', detail: 'сверка перевода с оригиналом' },
    { title: 'Страница', detail: 'пересборка textbook.html из готовых файлов курса' },
  ],
}

// args: { courseDir, lang, chapters: ['chapters/ch01.md', ...], needGlossary: boolean }
const { courseDir, lang, chapters, needGlossary = false } = args
const GLOSSARY = courseDir + '/glossary.json'

const FILE_RESULT = {
  type: 'object',
  required: ['file'],
  properties: { file: { type: 'string' }, notes: { type: 'string' } },
}
const CRITIC_LIMIT =
  '\nФОРМАТ ОТВЕТА (обязательно): не больше 5 замечаний, только БЛОКИРУЮЩИЕ — то, что делает результат фактически неверным или ломает связанные файлы. Стилистику, шероховатости языка, единообразие оформления и «можно улучшить» НЕ писать. Каждое замечание — одно-два предложения. Нет блокирующего — verdict \"approve\".\n'

const CRITIC = {
  type: 'object',
  required: ['verdict', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['approve', 'rework'] },
    issues: { type: 'array', items: { type: 'string' } },
  },
}

function outFile(ch) { return courseDir + '/translated/' + ch.split('/').pop() }
function shortName(ch) { return ch.split('/').pop() }

const translatorPrompt = (ch, buildGlossary, issues) =>
  'Ты — переводчик книг. Переведи главу ' + courseDir + '/' + ch + ' на язык «' + lang + '» полностью, ' +
  'без сокращений и пересказа: сохрани структуру заголовков, списки, примеры, сноски. ' +
  'Художественный текст — сохраняя стиль; технический — точность важнее гладкости. ' +
  'Строки-маркеры картинок ![описание](images/имя.png) сохраняй на том же месте: путь в скобках — БЕЗ изменений, ' +
  'описание в квадратных скобках можно перевести.\n' +
  (buildGlossary
    ? 'Глоссария ещё нет: по ходу перевода собери глоссарий ключевых терминов книги и запиши его в ' + GLOSSARY +
      ' как JSON {"термин-оригинал":"перевод", ...} (примерно 15–40 терминов).'
    : 'Перед переводом прочитай глоссарий ' + GLOSSARY + ' и переводи термины СТРОГО по нему.') +
  (issues ? '\nПеревод уже существует (' + outFile(ch) + ') — ДОРАБОТАЙ его по замечаниям критика: ' + JSON.stringify(issues) : '') +
  '\nЗапиши перевод в ' + outFile(ch) + ' и верни {file, notes}.'

const criticPrompt = (ch) =>
  'Ты — критик перевода. Сверь перевод ' + outFile(ch) + ' с оригиналом ' + courseDir + '/' + ch + ' по смысловым блокам.\n' +
  'Проверь: (1) пропуски — абзацы, примеры, сноски не потеряны; (2) искажения смысла; ' +
  '(3) консистентность терминов с глоссарием ' + GLOSSARY + '; (4) естественность языка «' + lang + '»; ' +
  '(5) маркеры картинок ![…](images/…) на месте, пути к файлам не изменены.\n' +
  'Верни {verdict:"approve"|"rework", issues:[конкретные замечания]}.'

async function translateOne(ch, buildGlossary, phaseName) {
  let out = await agent(translatorPrompt(ch, buildGlossary, null),
    { label: 'перевод:' + shortName(ch), phase: phaseName, schema: FILE_RESULT })
  if (!out) return { chapter: ch, verdict: 'skipped' }
  for (let i = 0; i < 1; i++) {
    const rev = await agent(criticPrompt(ch) + CRITIC_LIMIT,
      { label: 'критик перевода:' + shortName(ch), phase: 'Критика перевода', schema: CRITIC })
    if (!rev || rev.verdict === 'approve') return { chapter: ch, file: outFile(ch), verdict: 'approve', reworks: i }
    log('Перевод ' + shortName(ch) + ': доработка ' + (i + 1) + ' (' + rev.issues.length + ' замечаний)')
    out = (await agent(translatorPrompt(ch, buildGlossary, rev.issues),
      { label: 'перевод:доработка:' + shortName(ch), phase: phaseName, schema: FILE_RESULT })) || out
  }
  return { chapter: ch, file: outFile(ch), verdict: 'accepted-after-rework' }
}

const results = []
let rest = chapters
if (needGlossary && chapters.length) {
  // первая глава переводится одна и формирует глоссарий — остальные обязаны ему следовать
  results.push(await translateOne(chapters[0], true, 'Глоссарий'))
  rest = chapters.slice(1)
}
const restResults = await pipeline(rest, (ch) => translateOne(ch, false, 'Перевод'))

// Пересборка страницы: детерминированный скрипт, без ИИ — просто перечитывает
// готовые файлы курса и обновляет textbook.html, чтобы страница не отставала от батча перевода.
phase('Страница')
await agent(
  'Выполни команду `python3 .claude/workflows/scripts/build_textbook.py ' + courseDir + '` из корня репозитория ' +
  '(там, где лежит каталог .claude). Это чистый детерминированный сборщик (только stdlib Python, без ИИ) — ' +
  'он читает уже готовые файлы курса ' + courseDir + ' и переписывает ' + courseDir + '/textbook.html. ' +
  'Если команда упала — исправь причину (путь/окружение) и повтори.\n' +
  'Верни {file: "' + courseDir + '/textbook.html", notes: "<вывод команды>"}.',
  { label: 'сборка учебника', phase: 'Страница', schema: FILE_RESULT, effort: 'low' }
)

return { translated: results.concat(restResults.filter(Boolean)) }
