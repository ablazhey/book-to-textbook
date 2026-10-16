export const meta = {
  name: 'book-final',
  description: 'Этап 5: финал — саммари книги, совокупный экзамен 20–30 вопросов, итоговый проект (по целесообразности), критик финала',
  whenToUse: 'Конвейер «книга → учебник»: когда все разделы и их тесты готовы',
  phases: [
    { title: 'Саммари', detail: 'редактор пишет саммари книги на 2–4 страницы' },
    { title: 'Экзамен', detail: 'совокупный тест по всей книге, пропорционально разделам' },
    { title: 'Проект', detail: 'оценка целесообразности + сквозной итоговый проект' },
    { title: 'Критика финала', detail: 'экзамен покрывает книгу, проект выполним' },
    { title: 'Страница', detail: 'пересборка textbook.html из готовых файлов курса' },
  ],
}

// args: { courseDir, lang, bookTitle }
const { courseDir, lang, bookTitle } = args
const SUMMARY_FILE = courseDir + '/final/summary.md'
const EXAM_FILE = courseDir + '/final/exam.json'
const PROJECT_FILE = courseDir + '/final/project.json'

const FILE_RESULT = {
  type: 'object',
  required: ['file'],
  properties: { file: { type: 'string' }, notes: { type: 'string' } },
}
const QUIZ_RESULT = {
  type: 'object',
  required: ['file', 'questionsCount'],
  properties: { file: { type: 'string' }, questionsCount: { type: 'number' }, notes: { type: 'string' } },
}
const ASSESS = {
  type: 'object',
  required: ['needed', 'reason'],
  properties: { needed: { type: 'boolean' }, reason: { type: 'string' } },
}
const CRITIC_LIMIT =
  '\nФОРМАТ ОТВЕТА (обязательно): не больше 5 замечаний суммарно, только БЛОКИРУЮЩИЕ — фактические ошибки, ' +
  'непокрытые разделы, невыполнимый проект. Стилистику и «можно улучшить» НЕ писать.\n'

const FINAL_CRITIC = {
  type: 'object',
  required: ['verdict', 'examIssues', 'projectIssues'],
  properties: {
    verdict: { type: 'string', enum: ['approve', 'rework'] },
    examIssues: { type: 'array', items: { type: 'string' } },
    projectIssues: { type: 'array', items: { type: 'string' } },
  },
}

const baseCtx = 'Книга: «' + bookTitle + '». Каталог курса: ' + courseDir +
  ' (map.json — карта разделов и тем, chapters/ — оригинальные главы, topics/ — конспекты и тесты тем, sections/ — тесты разделов). ' +
  'Язык учебника: «' + lang + '».'

const summaryPrompt = () =>
  'Ты — редактор. ' + baseCtx + '\n' +
  'Напиши саммари всей книги на 2–4 страницы на языке «' + lang + '»: главная идея, ключевые концепции по разделам, ' +
  'как они связаны между собой, что читатель должен уметь после книги. Строго по содержанию книги (прочитай map.json ' +
  'и конспекты тем, при сомнениях сверяйся с главами). Пиши плотно: определения в строку, механизмы списком, ' +
  'сравнения таблицей, без вводных оборотов и повторов. Если в конспектах тем есть 1–3 картинки, которые держат ' +
  'главную идею книги (общая схема, ключевой график), перенеси их той же строкой ![подпись](images/имя.png) с тем же путём. ' +
  'Запиши markdown в ' + SUMMARY_FILE + ' и верни {file, notes}.'

const examPrompt = (issues) =>
  'Ты — составитель экзаменов. ' + baseCtx + '\n' +
  'Составь финальный экзамен по ВСЕЙ книге: 20–30 вопросов на языке «' + lang + '», количество вопросов на раздел — ' +
  'пропорционально его объёму в map.json. Не дублируй вопросы тематических тестов и тестов разделов (проверь их в topics/ и sections/). ' +
  'Только вопросы с выбором варианта: "single" (один верный) или "multi" (несколько верных — в конце формулировки q ' +
  'явно укажи их число, например «(выберите 2 варианта)», и это число обязано совпадать с длиной массива correct). ' +
  'Открытых вопросов быть не должно. ' +
  'Формат вопроса: {"q","type"("single"|"multi"),"options","correct","explanation","wrongExplanations","ref"}.\n' +
  (issues ? 'Экзамен уже существует — ДОРАБОТАЙ его по замечаниям критика: ' + JSON.stringify(issues) + '\n' : '') +
  'Запиши JSON {"questions":[...]} в ' + EXAM_FILE + ' и верни {file, questionsCount, notes}.'

const projectAssessPrompt = () =>
  'Ты — методист-оценщик. ' + baseCtx + '\n' +
  'Реши, позволяет ли тематика книги дать читателю итоговое ПРАКТИЧЕСКОЕ задание — сквозной проект, объединяющий навыки ' +
  'из разных разделов (прочитай map.json и оцени долю прикладных тем). Практика не обязательна — только по целесообразности. ' +
  'Верни {needed, reason}.'

const projectPrompt = (reason, issues) =>
  'Ты — методист итоговых проектов. ' + baseCtx + ' Обоснование целесообразности: ' + reason + '\n' +
  'Создай сквозной итоговый проект по книге на языке «' + lang + '»: JSON {"needed":true,"title":"...",' +
  '"description":"что и зачем делаем","steps":["пошаговая инструкция"],"expectedResult":"эталонный результат — что должно получиться",' +
  '"checklist":["критерии самопроверки"],"sectionsCovered":["id разделов, чьи навыки задействованы"],"timeEstimate":"примерное время"}. ' +
  'Проект должен объединять навыки из НЕСКОЛЬКИХ разделов и быть выполнимым обычным читателем.\n' +
  (issues ? 'Проект уже существует — ДОРАБОТАЙ его по замечаниям критика: ' + JSON.stringify(issues) + '\n' : '') +
  'Запиши JSON в ' + PROJECT_FILE + ' и верни {file, notes}.'

// Обрывы связи случаются часто — до 2 доп. попыток той же задачи в рамках
// одного прогона воркфлоу, прежде чем сдаваться.
async function withRetry(makeCall, tries) {
  tries = tries || 3
  let out = null
  for (let i = 0; i < tries && !out; i++) out = await makeCall()
  return out
}

// Саммари, экзамен и оценка проекта независимы — параллельно
phase('Саммари')
const [summary, exam0, assess] = await parallel([
  () => withRetry(() => agent(summaryPrompt(), { label: 'саммари книги', phase: 'Саммари', schema: FILE_RESULT })),
  () => withRetry(() => agent(examPrompt(null), { label: 'экзамен', phase: 'Экзамен', schema: QUIZ_RESULT })),
  () => withRetry(() => agent(projectAssessPrompt(), { label: 'оценка проекта', phase: 'Проект', schema: ASSESS, effort: 'low' })),
])

let exam = exam0
let project = null
if (assess && assess.needed) {
  project = await withRetry(() => agent(projectPrompt(assess.reason, null), { label: 'итоговый проект', phase: 'Проект', schema: FILE_RESULT }))
}

// Критик финала: экзамен реально проверяет знание всей книги, проект выполним
phase('Критика финала')
const criticPrompt = () =>
  'Ты — критик финальной части курса. ' + baseCtx + '\n' +
  'Прочитай экзамен ' + EXAM_FILE + (assess && assess.needed ? ', проект ' + PROJECT_FILE : '') +
  ', карту map.json и выборочно конспекты тем.\n' +
  'Проверь экзамен: покрывает все разделы пропорционально, вопросы корректны и отвечаются по книге, нет дублей с тестами тем/разделов, ' +
  'вопросов 20–30, type только "single" или "multi" (открытых нет), у "multi" в тексте вопроса указано число верных ' +
  'вариантов и оно совпадает с длиной correct. ' +
  (assess && assess.needed
    ? 'Проверь проект: объединяет навыки нескольких разделов, инструкция полная, результат конкретен и проверяем, выполним без недоступных читателю ресурсов. '
    : 'Проекта нет (обоснование: ' + (assess ? assess.reason : '—') + ') — оцени только экзамен, projectIssues верни пустым. ') +
  'Верни {verdict:"approve"|"rework", examIssues:[...], projectIssues:[...]}.'

let verdict = 'approve'
for (let i = 0; i < 1; i++) {
  const rev = await withRetry(() => agent(criticPrompt() + CRITIC_LIMIT, { label: 'критик финала', phase: 'Критика финала', schema: FINAL_CRITIC }))
  if (!rev || rev.verdict === 'approve') break
  verdict = 'accepted-after-rework'
  log('Критик финала: доработка ' + (i + 1) + ' (экзамен: ' + rev.examIssues.length + ', проект: ' + rev.projectIssues.length + ')')
  const fixes = []
  if (rev.examIssues.length) fixes.push(() => withRetry(() => agent(examPrompt(rev.examIssues), { label: 'экзамен:доработка', phase: 'Экзамен', schema: QUIZ_RESULT })))
  if (rev.projectIssues.length && assess && assess.needed) fixes.push(() => withRetry(() => agent(projectPrompt(assess.reason, rev.projectIssues), { label: 'проект:доработка', phase: 'Проект', schema: FILE_RESULT })))
  if (!fixes.length) break
  const fixed = await parallel(fixes)
  if (rev.examIssues.length && fixed[0]) exam = fixed[0]
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

return {
  summary: summary ? summary.file : null,
  exam: exam ? { file: exam.file, questions: exam.questionsCount } : null,
  project: assess && assess.needed ? { file: PROJECT_FILE, reason: assess.reason, created: !!project } : { needed: false, reason: assess ? assess.reason : '—' },
  verdict,
}
