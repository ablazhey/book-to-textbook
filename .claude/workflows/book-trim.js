export const meta = {
  name: 'book-trim',
  description: 'Ретрофит конспектов: убрать пересказ соседних тем и уложиться в заявленное время, не сломав тесты',
  whenToUse: 'Когда готовые конспекты переросли свой бюджет времени или дублируют соседние темы',
  phases: [
    { title: 'Сокращение', detail: 'редактор режет дубли и укладывается в бюджет слов' },
    { title: 'Критика', detail: 'проверка: тесты по-прежнему отвечаются, факты темы не потеряны' },
    { title: 'Страница', detail: 'пересборка textbook.html из готовых файлов курса' },
  ],
}

// args: { courseDir, lang, topics: [{ id, title, minutes, chapterFiles, summary }] }
const { courseDir, lang, topics } = args
// Формат ссылки на источник зависит от языка курса: [гл. N, стр. X] для ru, [ch. N, p. X] для остальных.
// Сборщик понимает оба маркера (гл./ch.), число в ссылке — номер главы.
const RU = String(lang || '').toLowerCase().startsWith('ru')
const CH = RU ? 'гл.' : 'ch.'
const PG = RU ? 'стр.' : 'p.'
const WORDS_PER_MINUTE = 180

const FILE_RESULT = {
  type: 'object',
  required: ['file', 'wordsBefore', 'wordsAfter'],
  properties: {
    file: { type: 'string' },
    wordsBefore: { type: 'number' },
    wordsAfter: { type: 'number' },
    notes: { type: 'string' },
  },
}
const CRITIC = {
  type: 'object',
  required: ['verdict', 'issues'],
  properties: {
    verdict: { type: 'string', enum: ['approve', 'rework'] },
    issues: { type: 'array', items: { type: 'string' } },
  },
}
const REBUILD_RESULT = {
  type: 'object',
  required: ['file'],
  properties: { file: { type: 'string' }, notes: { type: 'string' } },
}

const CRITIC_LIMIT =
  '\nФОРМАТ ОТВЕТА (обязательно): не больше 5 замечаний, только БЛОКИРУЮЩИЕ — потерянная опора для вопроса теста, ' +
  'выпавший материал темы, выход за коридор объёма, оборванный текст. Стилистику, единообразие оформления, ' +
  'номера страниц и «можно улучшить» НЕ писать. Нет блокирующего — verdict "approve".\n'

// соседние темы передаём текстом, чтобы агент не читал map.json целиком
function siblings(t) {
  const others = (args.sectionTopics || []).filter((x) => x.id !== t.id)
  if (!others.length) return '  (соседи не переданы)\n'
  return others.map((x) => '  • «' + x.title + '» — ' + (x.summary || '')).join('\n') + '\n'
}

function budget(t) { return Math.round((t.minutes || 12) * WORDS_PER_MINUTE) }
function chapterList(t) { return t.chapterFiles.map((f) => courseDir + '/' + f).join(', ') }
// итоговый тест раздела тоже опирается на конспекты — при сокращении его легко сломать
function sectionTestFile(t) { return courseDir + '/sections/' + t.id.split('t')[0] + '.test.json' }

async function trimTopic(t) {
  const materialFile = courseDir + '/topics/' + t.id + '.material.md'
  const quizFile = courseDir + '/topics/' + t.id + '.quiz.json'
  const b = budget(t)
  const lo = Math.round(b * 0.85)
  const hi = Math.round(b * 1.15)

  const editorPrompt = (issues) =>
    'Ты — редактор учебных конспектов. Язык: «' + lang + '».\n' +
    'Файл: ' + materialFile + ' (тема «' + t.title + '», заявлена на ' + t.minutes + ' мин).\n' +
    'Задача: СОКРАТИТЬ конспект до ' + lo + '–' + hi + ' слов, не потеряв ничего, что принадлежит именно этой теме.\n\n' +
    'Что резать в первую очередь:\n' +
    '1. Пересказ материала соседних тем. Соседи этого раздела:\n' + siblings(t) +
    'Если факт, кейс или определение закреплены за одной из них — оставь одну-две строки связки с отсылкой, ' +
    'а развёрнутый разбор удали. map.json читать не нужно.\n' +
    '2. Повторы: один и тот же факт в теле и в кратком резюме — оставь в одном месте.\n' +
    '3. Длинные «прим. редактора» и авторские обобщения, не подкреплённые книгой.\n' +
    '4. Многословные формулировки — при равном смысле выбирай короткую.\n\n' +
    'ЧТО ТРОГАТЬ НЕЛЬЗЯ (жёстко):\n' +
    '- Прочитай тест темы ' + quizFile + ' И итоговый тест раздела ' + sectionTestFile(t) + ' (если он есть). ' +
    'КАЖДЫЙ вопрос обоих тестов должен по-прежнему однозначно отвечаться из сокращённого конспекта. ' +
    'Факт, на котором держится хоть один вопрос, удалять запрещено — это сломает учебник.\n' +
    '- Шапку конспекта (источники, как читать ссылки, время чтения) сохрани, время чтения приведи в соответствие.\n' +
    '- Ссылки на источник [' + CH + ' N, ' + PG + ' X] у оставшихся тезисов сохрани.\n' +
    '- Картинки ![подпись](images/имя.png) сохрани (они в бюджет слов не входят); пути не меняй.\n' +
    '- Ничего не дописывай сверх книги: это сокращение, а не переписывание.\n\n' +
    (issues ? 'Предыдущая версия забракована критиком — исправь: ' + JSON.stringify(issues) + '\n\n' : '') +
    'Перед сдачей посчитай слова: wc -w ' + materialFile + '. Перезапиши файл и верни ' +
    '{file, wordsBefore, wordsAfter, notes}.'

  const criticPrompt = () =>
    'Ты — критик. Проверь сокращённый конспект ' + materialFile + ' (тема «' + t.title + '»).\n' +
    'Источники для сверки: тест ' + quizFile + ', оригинальные главы ' + chapterList(t) + '.\n\n' +
    'Проверь по порядку:\n' +
    '(1) ГЛАВНОЕ — пройди по КАЖДОМУ вопросу теста и убедись, что ответ по-прежнему выводится из конспекта. ' +
    'Любой вопрос, потерявший опору в тексте, — блокирующее замечание с номером вопроса.\n' +
    '(2) Объём: посчитай wc -w, должно быть ' + lo + '–' + hi + ' слов.\n' +
    '(3) Не выпало ли то, что принадлежит именно этой теме (тема: «' + t.title + '» — ' + (t.summary || '') + ').\n' +
    '(4) Не осталось ли развёрнутого пересказа соседних тем.\n' +
    '(5) Целостность: нет оборванных фраз, висящих отсылок на удалённые разделы, битых ссылок [' + CH + ' N]; ' +
    'картинки ![…](images/…) из исходной версии не потеряны, пути не изменены.\n' +
    'Верни {verdict:"approve"|"rework", issues:[конкретные замечания]}.'

  phase('Сокращение')
  let out = await agent(editorPrompt(null), { label: 'сокращение:' + t.id, phase: 'Сокращение', schema: FILE_RESULT })
  if (!out) return { id: t.id, verdict: 'skipped' }

  let lastIssues = []
  let verdict = 'approve'
  for (let i = 0; i < 1; i++) {
    const rev = await agent(criticPrompt() + CRITIC_LIMIT, { label: 'критик:' + t.id, phase: 'Критика', schema: CRITIC })
    if (!rev || rev.verdict === 'approve') { lastIssues = rev ? rev.issues : []; break }
    lastIssues = rev.issues
    verdict = 'accepted-after-rework'
    log(t.id + ': критик вернул сокращение на доработку (' + rev.issues.length + ' замечаний)')
    out = (await agent(editorPrompt(rev.issues),
      { label: 'сокращение:доработка' + (i + 1) + ':' + t.id, phase: 'Сокращение', schema: FILE_RESULT })) || out
  }

  return {
    id: t.id,
    title: t.title,
    verdict,
    wordsBefore: out.wordsBefore,
    wordsAfter: out.wordsAfter,
    budget: b,
    notes: lastIssues,
  }
}

const results = await pipeline(topics, (t) => trimTopic(t))

// Пересборка страницы: детерминированный скрипт, без ИИ — просто перечитывает
// готовые файлы курса и обновляет textbook.html.
phase('Страница')
await agent(
  'Выполни команду `python3 .claude/workflows/scripts/build_textbook.py ' + courseDir + '` из корня репозитория ' +
  '(там, где лежит каталог .claude). Это чистый детерминированный сборщик (только stdlib Python, без ИИ) — ' +
  'он читает уже готовые файлы курса ' + courseDir + ' и переписывает ' + courseDir + '/textbook.html. ' +
  'Если команда упала — исправь причину (путь/окружение) и повтори.\n' +
  'Верни {file: "' + courseDir + '/textbook.html", notes: "<вывод команды>"}.',
  { label: 'сборка учебника', phase: 'Страница', schema: REBUILD_RESULT, effort: 'low' }
)

return { trimmed: results.filter(Boolean) }
