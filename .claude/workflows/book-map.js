export const meta = {
  name: 'book-map',
  description: 'Этап 1: карта учебника — структуролог строит разделы→темы, критик проверяет',
  whenToUse: 'Конвейер «книга → интерактивный учебник», запускается после извлечения глав (этап 0)',
  phases: [
    { title: 'Структура', detail: 'структуролог строит карту разделы → темы' },
    { title: 'Критика структуры', detail: 'проверка гранулярности, покрытия, порядка' },
  ],
}

// args: { courseDir: string, lang: string }
const { courseDir, lang } = args
const MAP_FILE = courseDir + '/map.json'

const MAP_RESULT = {
  type: 'object',
  required: ['file', 'sectionsCount', 'topicsCount', 'outline'],
  properties: {
    file: { type: 'string' },
    sectionsCount: { type: 'number' },
    topicsCount: { type: 'number' },
    outline: { type: 'string', description: 'компактный текстовый список: раздел — его темы' },
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

const makerPrompt = (issues) =>
  'Ты — структуролог учебных курсов. Главы книги (markdown) лежат в ' + courseDir + '/chapters, ' +
  'оглавление с метаданными — в ' + courseDir + '/toc.json. Прочитай оглавление и просмотри главы.\n' +
  'Построй карту интерактивного учебника: разделы → темы. Тема — учебная единица на 10–20 минут изучения; ' +
  'раздел объединяет связанные темы (обычно совпадает с частью/блоком книги). Покрой ВСЮ книгу.\n' +
  'Запиши в ' + MAP_FILE + ' JSON вида: {"sections":[{"id":"s1","title":"...","topics":[{"id":"s1t1","title":"...",' +
  '"minutes":15,"chapterFiles":["chapters/ch03.md"],"summary":"о чём тема, 1–2 предложения","applied":true}]}]} — ' +
  'applied=true для прикладных тем (навык/метод/инструмент, которые читатель может применить), false для теоретических/обзорных. ' +
  'Названия разделов и тем — на языке: ' + lang + '.\n' +
  (issues ? 'Карта уже существует — ДОРАБОТАЙ её по замечаниям критика: ' + JSON.stringify(issues) + '\n' : '') +
  'Верни {file, sectionsCount, topicsCount, outline}.'

const criticPrompt = () =>
  'Ты — критик структуры учебного курса. Прочитай карту ' + MAP_FILE + ' и сверь её с ' + courseDir + '/toc.json ' +
  'и главами в ' + courseDir + '/chapters.\n' +
  'Проверь: (1) гранулярность — каждая тема реально тянет на 10–20 минут, нет тем-гигантов и тем-обрывков; ' +
  '(2) покрытие — вся книга покрыта, важные главы не выпали; (3) порядок логичен для изучения; ' +
  '(4) chapterFiles каждой темы существуют и действительно содержат материал этой темы; ' +
  '(5) флаг applied расставлен осмысленно.\n' +
  'Верни {verdict:"approve"|"rework", issues:[конкретные замечания]}.'

phase('Структура')
let result = await agent(makerPrompt(null), { label: 'структуролог', phase: 'Структура', schema: MAP_RESULT })

phase('Критика структуры')
const review = await agent(criticPrompt(), { label: 'критик структуры', phase: 'Критика структуры', schema: CRITIC })

let criticIssues = []
if (review && review.verdict === 'rework') {
  criticIssues = review.issues
  log('Критик вернул карту на доработку: замечаний — ' + review.issues.length)
  result = (await agent(makerPrompt(review.issues), { label: 'структуролог:доработка', phase: 'Структура', schema: MAP_RESULT })) || result
}

return { map: result, criticIssues }
