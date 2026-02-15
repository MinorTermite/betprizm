const fetch = require('node-fetch');
const { writeFileSync } = require('fs');
const { join } = require('path');

// Популярные лиги для парсинга
const POPULAR_LEAGUES = [
  { sport: 'football', name: 'Англия. Премьер-лига', url: 'https://www.marathonbet.ru/su/popular/Football/England/Premier+League+-+21520' },
  { sport: 'football', name: 'Испания. Ла Лига', url: 'https://www.marathonbet.ru/su/popular/Football/Spain/Primera+Division+-+8736' },
  { sport: 'football', name: 'Лига чемпионов УЕФА', url: 'https://www.marathonbet.ru/su/popular/Football/UEFA+Champions+League/UEFA+Champions+League+-+97179' },
  { sport: 'football', name: 'Лига Европы УЕФА', url: 'https://www.marathonbet.ru/su/popular/Football/UEFA+Europa+League/UEFA+Europa+League+-+97180' },
  { sport: 'hockey', name: 'КХЛ', url: 'https://www.marathonbet.ru/su/popular/Ice+Hockey/KHL+-+52309' },
  { sport: 'basket', name: 'NBA', url: 'https://www.marathonbet.ru/su/popular/Basketball/NBA+-+69367' },
  { sport: 'esports', name: 'Dota 2', url: 'https://www.marathonbet.ru/su/popular/e-Sports/Dota+2/' },
  { sport: 'esports', name: 'CS2', url: 'https://www.marathonbet.ru/su/popular/e-Sports/Counter-Strike/' }
];

async function parseMarathon() {
  const matches = [];
  
  for (const league of POPULAR_LEAGUES) {
    try {
      console.log(`Парсинг: ${league.name}`);
      
      // Здесь будет реальный парсинг
      // Пока создаём mock данные
      const mockMatches = generateMockMatches(league);
      matches.push(...mockMatches);
      
    } catch (error) {
      console.error(`Ошибка парсинга ${league.name}:`, error);
    }
  }
  
  return matches;
}

function generateMockMatches(league) {
  const now = new Date();
  const matches = [];
  
  // Генерируем 3-5 матчей для каждой лиги
  const count = Math.floor(Math.random() * 3) + 3;
  
  for (let i = 0; i < count; i++) {
    const date = new Date(now.getTime() + (i * 24 * 60 * 60 * 1000));
    const dateStr = date.toLocaleDateString('ru-RU', { day: '2-digit', month: 'short' });
    
    const teams = getRandomTeams(league.sport);
    
    const match = {
      sport: league.sport,
      league: league.name,
      id: `${Date.now()}_${i}_${Math.random().toString(36).substr(2, 9)}`,
      date: dateStr,
      time: `${String(Math.floor(Math.random() * 6) + 17).padStart(2, '0')}:${['00', '30'][Math.floor(Math.random() * 2)]}`,
      team1: teams[0],
      team2: teams[1],
      p1: (Math.random() * 3 + 1.5).toFixed(2),
      x: league.sport === 'football' ? (Math.random() * 2 + 2.5).toFixed(2) : '0.00',
      p2: (Math.random() * 3 + 1.5).toFixed(2),
      p1x: league.sport === 'football' ? (Math.random() * 0.5 + 1.2).toFixed(2) : '0.00',
      p12: league.sport === 'football' ? (Math.random() * 0.3 + 1.1).toFixed(2) : '0.00',
      px2: league.sport === 'football' ? (Math.random() * 0.5 + 1.3).toFixed(2) : '0.00'
    };
    
    matches.push(match);
  }
  
  return matches;
}

function getRandomTeams(sport) {
  const teams = {
    football: [
      ['Манчестер Сити', 'Ливерпуль'],
      ['Арсенал', 'Челси'],
      ['Барселона', 'Реал Мадрид'],
      ['Бавария', 'Боруссия Д'],
      ['ПСЖ', 'Марсель'],
      ['Интер', 'Милан'],
      ['Атлетико', 'Севилья']
    ],
    hockey: [
      ['СКА', 'ЦСКА'],
      ['Ак Барс', 'Авангард'],
      ['Металлург Мг', 'Трактор'],
      ['Динамо М', 'Спартак']
    ],
    basket: [
      ['Лейкерс', 'Уорриорз'],
      ['Селтикс', 'Хит'],
      ['Наггетс', 'Санз'],
      ['Баксс', 'Сиксерс']
    ],
    esports: [
      ['Team Spirit', 'OG'],
      ['Liquid', 'Secret'],
      ['Navi', 'G2'],
      ['Vitality', 'FaZe']
    ]
  };
  
  const sportTeams = teams[sport] || teams.football;
  return sportTeams[Math.floor(Math.random() * sportTeams.length)];
}

exports.handler = async (event, context) => {
  // Проверка авторизации (опционально)
  const authHeader = event.headers.authorization;
  const expectedToken = process.env.UPDATE_TOKEN || 'prizmbet-secret-2026';
  
  if (event.httpMethod === 'GET' && event.queryStringParameters?.token !== expectedToken) {
    // Разрешаем GET без токена для просмотра статуса
    if (!event.queryStringParameters?.status) {
      return {
        statusCode: 403,
        body: JSON.stringify({ error: 'Unauthorized' })
      };
    }
  }
  
  try {
    console.log('Начало парсинга...');
    const matches = await parseMarathon();
    
    const data = {
      last_update: new Date().toLocaleString('ru-RU'),
      matches: matches
    };
    
    // В продакшене данные нужно сохранять в облачное хранилище
    // Например, в AWS S3, Netlify Blobs, или другой сервис
    
    console.log(`Парсинг завершён. Найдено матчей: ${matches.length}`);
    
    return {
      statusCode: 200,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      },
      body: JSON.stringify({
        success: true,
        data: data,
        stats: {
          total_matches: matches.length,
          leagues: [...new Set(matches.map(m => m.league))].length
        }
      })
    };
    
  } catch (error) {
    console.error('Ошибка парсинга:', error);
    
    return {
      statusCode: 500,
      body: JSON.stringify({
        success: false,
        error: error.message
      })
    };
  }
};
