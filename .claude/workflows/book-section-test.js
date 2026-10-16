export const meta = {
  name: 'book-section-test',
  description: 'Этап 4: итоговый тест раздела 10–20 вопросов (составитель + критик покрытия)',
  whenToUse: 'Конвейер «книга → учебник»: когда все темы раздела готовы',
  phases: [
    { title: 'Тест раздела', detail: 'составитель собирает 10–20 вопросов на связи между темами' },
    { title: 'Критика', detail: 'покрытие всех тем, отсутствие дублей с тематическими тестами' },
    { title: 'Страница', detail: 'пересборка textbook.html из готовых файлов курса' },
  ],
}

// args: { courseDir, lang, section: { id, title }, topicIds: [...] }
const { courseDir, lang, section, topicIds } = args
const TEST_FILE = courseDir + '/sections/' + section.id + '.test.json'
const materials = topicIds.map((id) => courseDir + '/topics/' + id + '.material.md').join(', ')
const quizzes = topicIds.map((id) => courseDir + '/topics/' + id + '.quiz.json').join(', ')

const QUIZ_RESULT = {
  type: 'object',
  required: ['file', 'questionsCount'],
  properties: { file: { type: 'string' }, questionsCount: { type: 'number' }, notes: { type: 'string' } },
}
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

const makerPrompt = (issues) =>
  'Ты — составитель итоговых тестов. Раздел «' + section.title + '» учебника. ' +
  'Конспекты тем раздела: ' + materials + '. Тематические тесты (их вопросы ПОВТОРЯТЬ НЕЛЬЗЯ): ' + quizzes + '.\n' +
  'Составь итоговый тест раздела: 10–20 вопросов на языке «' + lang + '», покрывающий ВСЕ темы раздела, ' +
  'с уклоном в СВЯЗИ между темами (сравнение подходов, применение идей одной темы к материалу другой, сквозные принципы), ' +
  'а не повтор тематических вопросов. Только вопросы с выбором варианта: "single" (один верный) или "multi" ' +
  '(несколько верных — в конце формулировки q явно укажи их число, например «(выберите 2 варианта)», и это число ' +
  'обязано совпадать с длиной массива correct). Открытых вопросов быть не должно. Формат каждого вопроса тот же, ' +
  'что в тематических тестах: {"q","type"("single"|"multi"),"options","correct","explanation","wrongExplanations","ref"} — ' +
  'ref указывает на главу книги.\n' +
  (issues ? 'Тест уже существует — ДОРАБОТАЙ его по замечаниям критика: ' + JSON.stringify(issues) + '\n' : '') +
  'Запиши JSON {"sectionId":"' + section.id + '","title":"' + section.title + '","questions":[...]} в ' + TEST_FILE +
  ' и верни {file, questionsCount, notes}.'

const criticPrompt = () =>
  'Ты — критик тестов. Прочитай итоговый тест раздела ' + TEST_FILE + ', конспекты тем (' + materials + ') ' +
  'и тематические тесты (' + quizzes + ').\n' +
  'Проверь: (1) покрытие — каждая тема раздела представлена хотя бы одним вопросом; ' +
  '(2) нет дублей и перефразировок вопросов из тематических тестов; (3) есть вопросы на связи между темами; ' +
  '(4) верные ответы верны по конспектам, объяснения и ref корректны; (5) вопросов 10–20, JSON валиден; ' +
  '(6) type только "single" или "multi" — открытых вопросов нет; (7) у "multi" в тексте вопроса указано число ' +
  'верных вариантов, и оно совпадает с длиной массива correct.\n' +
  'Верни {verdict:"approve"|"rework", issues:[конкретные замечания]}.'

// Обрывы связи случаются часто — до 2 доп. попыток той же задачи в рамках
// одного прогона воркфлоу, прежде чем сдаваться.
async function withRetry(makeCall, tries) {
  tries = tries || 3
  let out = null
  for (let i = 0; i < tries && !out; i++) out = await makeCall()
  return out
}

phase('Тест раздела')
let out = await withRetry(() => agent(makerPrompt(null), { label: 'тест раздела:' + section.id, phase: 'Тест раздела', schema: QUIZ_RESULT }))

let verdict = 'skipped'
let lastIssues = []
if (out) {
  verdict = 'approve'
  for (let i = 0; i < 1; i++) {
    const rev = await withRetry(() => agent(criticPrompt() + CRITIC_LIMIT, { label: 'критик:' + section.id, phase: 'Критика', schema: CRITIC }))
    if (!rev || rev.verdict === 'approve') break
    lastIssues = rev.issues
    verdict = 'accepted-after-rework'
    log('Тест раздела ' + section.id + ': доработка ' + (i + 1))
    out = (await withRetry(() =>
      agent(makerPrompt(rev.issues), { label: 'тест раздела:доработка:' + section.id, phase: 'Тест раздела', schema: QUIZ_RESULT }))) || out
  }
}

// Пересборка страницы: детерминированный скрипт, без ИИ — просто перечитывает
// готовые файлы курса и обновляет textbook.html.
phase('Страница')
await withRetry(() => agent(
  'Выполни команду `python3 .claude/workflows/scripts/build_textbook.py ' + courseDir + '` из корня репозитория ' +
  '(там, где лежит каталог .claude). Это чистый детерминированный сборщик (только stdlib Python, без ИИ) — ' +
  'он читает уже готовые файлы курса ' + courseDir + ' и переписывает ' + courseDir + '/textbook.html. ' +
  'Если команда упала — исправь причину (путь/окружение) и повтори.\n' +
  'Верни {file: "' + courseDir + '/textbook.html", notes: "<вывод команды>"}.',
  { label: 'сборка учебника', phase: 'Страница', schema: FILE_RESULT, effort: 'low' }
))

return { sectionId: section.id, file: TEST_FILE, questions: out ? out.questionsCount : 0, verdict, rejectedIssues: lastIssues }
