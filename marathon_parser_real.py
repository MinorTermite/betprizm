#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET Marathon parser — MAXIMUM POPULAR LEAGUES + LIVE
Парсит все популярные лиги и live-события с Marathon Bet

Установка:
  pip install -U requests beautifulsoup4 lxml gspread google-auth

Запуск:
  python marathon_parser.py
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


# =========================
# CONFIG - MAXIMUM LEAGUES
# =========================
BASE = "https://www.marathonbet.ru"

# Fallback список - ВСЕ популярные лиги
POPULAR_FALLBACK = [
    # ==================== FOOTBALL - TOP LEAGUES ====================
    ("football", "Лига чемпионов УЕФА", f"{BASE}/su/popular/Football/UEFA/Champions%2BLeague%2B-%2B26493"),
    ("football", "Лига Европы УЕФА", f"{BASE}/su/popular/Football/UEFA/Europa%2BLeague%2B-%2B26494"),
    ("football", "Лига конференций УЕФА", f"{BASE}/su/popular/Football/UEFA/Conference%2BLeague%2B-%2B26495"),
    ("football", "Англия. Премьер-лига", f"{BASE}/su/popular/Football/England/Premier%2BLeague%2B-%2B21520?lid=15600999"),
    ("football", "Испания. Ла Лига", f"{BASE}/su/popular/Football/Spain/Primera%2BDivision%2B-%2B8736?lid=26570477"),
    ("football", "Италия. Серия A", f"{BASE}/su/popular/Football/Italy/Serie%2BA%2B-%2B22434?lid=15601013"),
    ("football", "Германия. Бундеслига", f"{BASE}/su/popular/Football/Germany/Bundesliga%2B-%2B22436"),
    ("football", "Франция. Лига 1", f"{BASE}/su/popular/Football/France/Ligue%2B1%2B-%2B21533?interval=ALL_TIME"),
    
    # Футбол - Другие популярные лиги
    ("football", "Россия. Премьер-лига", f"{BASE}/su/football/Russia/Premier%2BLiga%2B-%2B26492"),
    ("football", "Англия. Чемпионшип", f"{BASE}/su/football/England/Championship%2B-%2B21521"),
    ("football", "Испания. Сегунда", f"{BASE}/su/football/Spain/Segunda%2BDivision%2B-%2B8737"),
    ("football", "Италия. Серия B", f"{BASE}/su/football/Italy/Serie%2BB%2B-%2B22435"),
    ("football", "Германия. 2. Бундеслига", f"{BASE}/su/football/Germany/2.%2BBundesliga%2B-%2B22437"),
    ("football", "Франция. Лига 2", f"{BASE}/su/football/France/Ligue%2B2%2B-%2B21534"),
    ("football", "Нидерланды. Эредивизие", f"{BASE}/su/football/Netherlands/Eredivisie%2B-%2B21528"),
    ("football", "Португалия. Примейра Лига", f"{BASE}/su/football/Portugal/Primeira%2BLiga%2B-%2B22441"),
    ("football", "Турция. Суперлига", f"{BASE}/su/football/Turkey/Super%2BLig%2B-%2B22444"),
    ("football", "Бельгия. Про Лига", f"{BASE}/su/football/Belgium/Jupiler%2BPro%2BLeague%2B-%2B21519"),
    ("football", "Шотландия. Премьершип", f"{BASE}/su/football/Scotland/Premiership%2B-%2B21532"),
    ("football", "Бразилия. Серия A", f"{BASE}/su/football/Brazil/Serie%2BA%2B-%2B22428"),
    ("football", "Аргентина. Примера Дивисьон", f"{BASE}/su/football/Argentina/Primera%2BDivision%2B-%2B22427"),
    ("football", "США. MLS", f"{BASE}/su/football/USA/MLS%2B-%2B21535"),
    ("football", "Мексика. Лига MX", f"{BASE}/su/football/Mexico/Liga%2BMX%2B-%2B21529"),
    ("football", "Саудовская Аравия. Про Лига", f"{BASE}/su/football/Saudi%2BArabia/Pro%2BLeague%2B-%2B26490"),
    ("football", "Япония. Джей-Лига", f"{BASE}/su/football/Japan/J1%2BLeague%2B-%2B22439"),
    ("football", "Южная Корея. К-Лига", f"{BASE}/su/football/South%2BKorea/K%2BLeague%2B1%2B-%2B22442"),
    ("football", "Австралия. A-League", f"{BASE}/su/football/Australia/A-League%2B-%2B21517"),
    ("football", "Украина. Премьер-лига", f"{BASE}/su/football/Ukraine/Premier%2BLiga%2B-%2B26491"),
    ("football", "Польша. Экстракласа", f"{BASE}/su/football/Poland/Extraklasa%2B-%2B21530"),
    ("football", "Греция. Суперлига", f"{BASE}/su/football/Greece/Super%2BLiga%2B-%2B22433"),
    ("football", "Австрия. Бундеслига", f"{BASE}/su/football/Austria/Bundesliga%2B-%2B21518"),
    ("football", "Швейцария. Суперлига", f"{BASE}/su/football/Switzerland/Super%2BLeague%2B-%2B21536"),
    ("football", "Дания. Суперлига", f"{BASE}/su/football/Denmark/Superliga%2B-%2B21524"),
    ("football", "Норвегия. Элитесерия", f"{BASE}/su/football/Norway/Eliteserien%2B-%2B21531"),
    ("football", "Швеция. Алльсвенскан", f"{BASE}/su/football/Sweden/Allsvenskan%2B-%2B21537"),
    ("football", "Чехия. Первая лига", f"{BASE}/su/football/Czech%2BRepublic/1.%2BLiga%2B-%2B21525"),
    ("football", "Словакия. Суперлига", f"{BASE}/su/football/Slovakia/Nike%2BLiga%2B-%2B26489"),
    ("football", "Хорватия. ХНЛ", f"{BASE}/su/football/Croatia/1.%2BNL%2B-%2B22431"),
    ("football", "Сербия. Суперлига", f"{BASE}/su/football/Serbia/SuperLiga%2B-%2B22443"),
    ("football", "Румыния. Лига 1", f"{BASE}/su/football/Romania/SuperLiga%2B-%2B26487"),
    ("football", "Венгрия. НБ I", f"{BASE}/su/football/Hungary/NB%2BI%2B-%2B21526"),
    ("football", "Болгария. Первая лига", f"{BASE}/su/football/Bulgaria/First%2BLeague%2B-%2B22429"),
    ("football", "Казахстан. Премьер-лига", f"{BASE}/su/football/Kazakhstan/Premier%2BLiga%2B-%2B26486"),
    ("football", "Беларусь. Высшая лига", f"{BASE}/su/football/Belarus/Vysheshaya%2BLiga%2B-%2B26485"),
    ("football", "Финляндия. Вейккауслига", f"{BASE}/su/football/Finland/Veikkausliiga%2B-%2B21527"),
    ("football", "Ирландия. Премьер-дивизион", f"{BASE}/su/football/Ireland/Premier%2BDivision%2B-%2B21522"),
    ("football", "Италия. Кубок", f"{BASE}/su/football/Italy/Coppa%2BItalia%2B-%2B22440"),
    ("football", "Англия. Кубок", f"{BASE}/su/football/England/FA%2BCup%2B-%2B21523"),
    ("football", "Испания. Кубок Короля", f"{BASE}/su/football/Spain/Copa%2Bdel%2BRey%2B-%2B8738"),
    ("football", "Германия. Кубок", f"{BASE}/su/football/Germany/DFB%2BPokal%2B-%2B22438"),
    ("football", "Франция. Кубок", f"{BASE}/su/football/France/Coupe%2Bde%2BFrance%2B-%2B21538"),
    ("football", "Россия. Кубок", f"{BASE}/su/football/Russia/Cup%2B-%2B26496"),
    ("football", "КОНМЕБОЛ. Копа Либертадорес", f"{BASE}/su/football/International/Copa%2BLibertadores%2B-%2B26497"),
    ("football", "КОНМЕБОЛ. Южноамериканский кубок", f"{BASE}/su/football/International/Copa%2BSudamericana%2B-%2B26498"),
    
    # ==================== HOCKEY ====================
    ("hockey", "КХЛ", f"{BASE}/su/popular/Ice%2BHockey/KHL%2B-%2B52309?lid=15577535"),
    ("hockey", "НХЛ", f"{BASE}/su/popular/Ice%2BHockey/NHL%2B-%2B52310"),
    ("hockey", "ВХЛ", f"{BASE}/su/ice-hockey/Russia/VHL%2B-%2B52311"),
    ("hockey", "МХЛ", f"{BASE}/su/ice-hockey/Russia/MHL%2B-%2B52312"),
    ("hockey", "Швеция. SHL", f"{BASE}/su/ice-hockey/Sweden/SHL%2B-%2B52313"),
    ("hockey", "Финляндия. Liiga", f"{BASE}/su/ice-hockey/Finland/Liiga%2B-%2B52314"),
    ("hockey", "Чехия. Extraliga", f"{BASE}/su/ice-hockey/Czech%2BRepublic/Extraliga%2B-%2B52315"),
    ("hockey", "Германия. DEL", f"{BASE}/su/ice-hockey/Germany/DEL%2B-%2B52316"),
    ("hockey", "Швейцария. National League", f"{BASE}/su/ice-hockey/Switzerland/National%2BLeague%2B-%2B52317"),
    ("hockey", "Словакия. Extraliga", f"{BASE}/su/ice-hockey/Slovakia/Extraliga%2B-%2B52318"),
    ("hockey", "Австрия. ICEHL", f"{BASE}/su/ice-hockey/Austria/ICEHL%2B-%2B52319"),
    ("hockey", "Норвегия. Eliteserien", f"{BASE}/su/ice-hockey/Norway/Eliteserien%2B-%2B52320"),
    ("hockey", "Дания. Metal Ligaen", f"{BASE}/su/ice-hockey/Denmark/Metal%2BLigaen%2B-%2B52321"),
    ("hockey", "Беларусь. Экстралига", f"{BASE}/su/ice-hockey/Belarus/Extraliga%2B-%2B52322"),
    ("hockey", "Казахстан. ЧРК", f"{BASE}/su/ice-hockey/Kazakhstan/Championship%2B-%2B52323"),
    ("hockey", "Польша. PHL", f"{BASE}/su/ice-hockey/Poland/PHL%2B-%2B52324"),
    ("hockey", "Великобритания. EIHL", f"{BASE}/su/ice-hockey/United%2BKingdom/EIHL%2B-%2B52325"),
    ("hockey", "Франция. Ligue Magnus", f"{BASE}/su/ice-hockey/France/Ligue%2BMagnus%2B-%2B52326"),
    ("hockey", "Швейцария. Swiss League", f"{BASE}/su/ice-hockey/Switzerland/Swiss%2BLeague%2B-%2B52327"),
    ("hockey", "Россия. Женская лига", f"{BASE}/su/ice-hockey/Russia/Women%2BLeague%2B-%2B52328"),
    
    # ==================== BASKETBALL ====================
    ("basket", "NBA", f"{BASE}/su/popular/Basketball/NBA%2B-%2B69367?lid=15577646"),
    ("basket", "Евролига", f"{BASE}/su/basketball/Europe/EuroLeague%2B-%2B69368"),
    ("basket", "Еврокубок", f"{BASE}/su/basketball/Europe/EuroCup%2B-%2B69369"),
    ("basket", "Единая лига ВТБ", f"{BASE}/su/basketball/International/VTB%2BUnited%2BLeague%2B-%2B69370"),
    ("basket", "Испания. ACB", f"{BASE}/su/basketball/Spain/ACB%2B-%2B69371"),
    ("basket", "Турция. BSL", f"{BASE}/su/basketball/Turkey/BSL%2B-%2B69372"),
    ("basket", "Италия. LBA", f"{BASE}/su/basketball/Italy/Lega%2BA%2B-%2B69373"),
    ("basket", "Германия. BBL", f"{BASE}/su/basketball/Germany/BBL%2B-%2B69374"),
    ("basket", "Франция. Pro A", f"{BASE}/su/basketball/France/Pro%2BA%2B-%2B69375"),
    ("basket", "Греция. HEBA A1", f"{BASE}/su/basketball/Greece/A1%2BEthniki%2B-%2B69376"),
    ("basket", "Австралия. NBL", f"{BASE}/su/basketball/Australia/NBL%2B-%2B69377"),
    ("basket", "Китай. CBA", f"{BASE}/su/basketball/China/CBA%2B-%2B69378"),
    ("basket", "Аргентина. LNB", f"{BASE}/su/basketball/Argentina/LNB%2B-%2B69379"),
    ("basket", "Бразилия. NBB", f"{BASE}/su/basketball/Brazil/NBB%2B-%2B69380"),
    ("basket", "Литва. LKL", f"{BASE}/su/basketball/Lithuania/LKL%2B-%2B69381"),
    ("basket", "Сербия. KLS", f"{BASE}/su/basketball/Serbia/KLS%2B-%2B69382"),
    ("basket", "Хорватия. ABA", f"{BASE}/su/basketball/Croatia/ABA%2B-%2B69383"),
    ("basket", "Польша. PLK", f"{BASE}/su/basketball/Poland/PLK%2B-%2B69384"),
    ("basket", "Израиль. Winner League", f"{BASE}/su/basketball/Israel/Winner%2BLeague%2B-%2B69385"),
    ("basket", "Бельгия. BNXT", f"{BASE}/su/basketball/Belgium/BNXT%2B-%2B69386"),
    ("basket", "WNBA", f"{BASE}/su/basketball/USA/WNBA%2B-%2B69387"),
    ("basket", "NCAA", f"{BASE}/su/basketball/USA/NCAA%2B-%2B69388"),
    
    # ==================== TENNIS ====================
    ("tennis", "ATP. Australian Open", f"{BASE}/su/tennis/ATP/Australian%2BOpen%2B-%2B88880"),
    ("tennis", "ATP. Roland Garros", f"{BASE}/su/tennis/ATP/Roland%2BGarros%2B-%2B88881"),
    ("tennis", "ATP. Уимблдон", f"{BASE}/su/tennis/ATP/Wimbledon%2B-%2B88882"),
    ("tennis", "ATP. US Open", f"{BASE}/su/tennis/ATP/US%2BOpen%2B-%2B88883"),
    ("tennis", "ATP. Masters 1000", f"{BASE}/su/tennis/ATP/Masters%2B1000%2B-%2B88884"),
    ("tennis", "ATP. Турниры 500", f"{BASE}/su/tennis/ATP/ATP%2B500%2B-%2B88885"),
    ("tennis", "ATP. Турниры 250", f"{BASE}/su/tennis/ATP/ATP%2B250%2B-%2B88886"),
    ("tennis", "WTA. Australian Open", f"{BASE}/su/tennis/WTA/Australian%2BOpen%2B-%2B88887"),
    ("tennis", "WTA. Roland Garros", f"{BASE}/su/tennis/WTA/Roland%2BGarros%2B-%2B88888"),
    ("tennis", "WTA. Уимблдон", f"{BASE}/su/tennis/WTA/Wimbledon%2B-%2B88889"),
    ("tennis", "WTA. US Open", f"{BASE}/su/tennis/WTA/US%2BOpen%2B-%2B88890"),
    ("tennis", "WTA. Турниры 1000", f"{BASE}/su/tennis/WTA/WTA%2B1000%2B-%2B88891"),
    ("tennis", "WTA. Турниры 500", f"{BASE}/su/tennis/WTA/WTA%2B500%2B-%2B88892"),
    ("tennis", "WTA. Турниры 250", f"{BASE}/su/tennis/WTA/WTA%2B250%2B-%2B88893"),
    ("tennis", "ITF. Мужчины", f"{BASE}/su/tennis/ITF/Men%2B-%2B88894"),
    ("tennis", "ITF. Женщины", f"{BASE}/su/tennis/ITF/Women%2B-%2B88895"),
    ("tennis", "Challenger", f"{BASE}/su/tennis/ATP/Challenger%2B-%2B88896"),
    ("tennis", "Davis Cup", f"{BASE}/su/tennis/International/Davis%2BCup%2B-%2B88897"),
    
    # ==================== VOLLEYBALL ====================
    ("volleyball", "CEV. Лига чемпионов", f"{BASE}/su/volleyball/Europe/CEV%2BChampions%2BLeague%2B-%2B77777"),
    ("volleyball", "Россия. Суперлига", f"{BASE}/su/volleyball/Russia/Superliga%2B-%2B77778"),
    ("volleyball", "Италия. SuperLega", f"{BASE}/su/volleyball/Italy/SuperLega%2B-%2B77779"),
    ("volleyball", "Польша. PlusLiga", f"{BASE}/su/volleyball/Poland/PlusLiga%2B-%2B77780"),
    ("volleyball", "Германия. Bundesliga", f"{BASE}/su/volleyball/Germany/Bundesliga%2B-%2B77781"),
    ("volleyball", "Франция. Ligue A", f"{BASE}/su/volleyball/France/Ligue%2BA%2B-%2B77782"),
    ("volleyball", "Турция. Efeler Ligi", f"{BASE}/su/volleyball/Turkey/Efeler%2BLigi%2B-%2B77783"),
    ("volleyball", "Бразилия. Superliga", f"{BASE}/su/volleyball/Brazil/Superliga%2B-%2B77784"),
    ("volleyball", "Италия. Серия A1 (жен)", f"{BASE}/su/volleyball/Italy/Serie%2BA1%2BWomen%2B-%2B77785"),
    ("volleyball", "Турция. Sultanlar Ligi", f"{BASE}/su/volleyball/Turkey/Sultanlar%2BLigi%2B-%2B77786"),
    ("volleyball", "Россия. Суперлига (жен)", f"{BASE}/su/volleyball/Russia/Superliga%2BWomen%2B-%2B77787"),
    ("volleyball", "Польша. Tauron Liga (жен)", f"{BASE}/su/volleyball/Poland/Tauron%2BLiga%2B-%2B77788"),
    ("volleyball", "Лига наций. Мужчины", f"{BASE}/su/volleyball/International/VNL%2BMen%2B-%2B77789"),
    ("volleyball", "Лига наций. Женщины", f"{BASE}/su/volleyball/International/VNL%2BWomen%2B-%2B77790"),
    
    # ==================== MMA ====================
    ("mma", "UFC", f"{BASE}/su/mma/UFC%2B-%2B99999"),
    ("mma", "Bellator", f"{BASE}/su/mma/Bellator%2B-%2B99998"),
    ("mma", "ONE Championship", f"{BASE}/su/mma/ONE%2BChampionship%2B-%2B99997"),
    ("mma", "PFL", f"{BASE}/su/mma/PFL%2B-%2B99996"),
    ("mma", "ACA", f"{BASE}/su/mma/ACA%2B-%2B99995"),
    ("mma", "RCC", f"{BASE}/su/mma/RCC%2B-%2B99994"),
    ("mma", "Eagle FC", f"{BASE}/su/mma/Eagle%2BFC%2B-%2B99993"),
    ("mma", "UFC. Вечер боёв", f"{BASE}/su/mma/UFC/Fight%2BNight%2B-%2B99992"),
    
    # ==================== ESPORTS ====================
    ("esports", "CS2. Major", f"{BASE}/su/e-sports/Counter-Strike/Major%2B-%2B111111"),
    ("esports", "CS2. ESL Pro League", f"{BASE}/su/e-sports/Counter-Strike/ESL%2BPro%2BLeague%2B-%2B111112"),
    ("esports", "CS2. BLAST Premier", f"{BASE}/su/e-sports/Counter-Strike/BLAST%2BPremier%2B-%2B111113"),
    ("esports", "CS2. IEM", f"{BASE}/su/e-sports/Counter-Strike/IEM%2B-%2B111114"),
    ("esports", "Dota 2. The International", f"{BASE}/su/e-sports/Dota%2B2/The%2BInternational%2B-%2B111115"),
    ("esports", "Dota 2. DPC", f"{BASE}/su/e-sports/Dota%2B2/DPC%2B-%2B111116"),
    ("esports", "Dota 2. BLAST Slam", f"{BASE}/su/popular/e-Sports/Dota+2/BLAST+Slam+-+20603920?lid=20621739"),
    ("esports", "LoL. LCK", f"{BASE}/su/e-sports/League%2Bof%2BLegends/LCK%2B-%2B111117"),
    ("esports", "LoL. LPL", f"{BASE}/su/e-sports/League%2Bof%2BLegends/LPL%2B-%2B111118"),
    ("esports", "LoL. LEC", f"{BASE}/su/e-sports/League%2Bof%2BLegends/LEC%2B-%2B111119"),
    ("esports", "LoL. LCS", f"{BASE}/su/e-sports/League%2Bof%2BLegends/LCS%2B-%2B111120"),
    ("esports", "LoL. Worlds", f"{BASE}/su/e-sports/League%2Bof%2BLegends/Worlds%2B-%2B111121"),
    ("esports", "Valorant. Champions Tour", f"{BASE}/su/e-sports/Valorant/VCT%2B-%2B111122"),
    ("esports", "Rocket League. RLCS", f"{BASE}/su/e-sports/Rocket%2BLeague/RLCS%2B-%2B111123"),
    ("esports", "Overwatch. OWL", f"{BASE}/su/e-sports/Overwatch/OWL%2B-%2B111124"),
    ("esports", "PUBG. Global Championship", f"{BASE}/su/e-sports/PUBG/Global%2BChampionship%2B-%2B111125"),
    ("esports", "Apex Legends. ALGS", f"{BASE}/su/e-sports/Apex%2BLegends/ALGS%2B-%2B111126"),
    ("esports", "Rainbow Six. EUL", f"{BASE}/su/e-sports/Rainbow%2BSix/European%2BLeague%2B-%2B111127"),
]

# LIVE события - числовые ID категорий (Marathon перешел на них)
LIVE_URLS = [
    f"{BASE}/su/live/26418", # Football
    f"{BASE}/su/live/43658", # Ice Hockey
    f"{BASE}/su/live/45356", # Basketball
    f"{BASE}/su/live/22723", # Tennis
    f"{BASE}/su/live/1372932", # e-Sports
    f"{BASE}/su/live/23690", # Volleyball
    f"{BASE}/su/live/414329", # Table Tennis
    f"{BASE}/su/live/439050", # MMA
]

# Output
OUT_JSON = "matches.json"

# Google Sheets (опционально)
WRITE_SHEETS = os.getenv("WRITE_SHEETS", "1") != "0"
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")
SHEET_NAME = os.getenv("SHEET_NAME", "Matches")
CREDS_FILE = os.getenv("CREDS_FILE", "credentials.json")

# Requests
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
TIMEOUT = 25


# =========================
# HTTP
# =========================
def http_get(url: str) -> str:
    headers = {
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru,en;q=0.9",
        "Connection": "keep-alive",
    }
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    return r.text


def infer_sport(league: str, t1: str, t2: str) -> str:
    """Определяет вид спорта по строке, если он ошибочно присвоен (например, при редиректе LIVE на общую страницу)"""
    text = f"{league} {t1} {t2}".lower()
    if "настольный теннис" in text or "table tennis" in text: return "tabletennis"
    if any(x in text for x in ["dota", "counter-strike", "cs2", "valorant", "league of legends", "rocket league", "pubg"]): return "esports"
    if any(x in text for x in ["хоккей", "nhl", "кхл", "вхл", "мхл", "hockey", "shl", "liiga"]): return "hockey"
    if any(x in text for x in ["баскет", "nba", "нба", "евролига", "vtb", "basket"]): return "basket"
    if any(x in text for x in ["теннис", "atp", "wta", "itf", "tennis"]): return "tennis"
    if any(x in text for x in ["волейбол", "volleyball", "cev", "vnl"]): return "volleyball"
    if any(x in text for x in ["mma", "ufc", "bellator", "pfl", "aca", "единоборства"]): return "mma"
    return "football"


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def clean_name(s: str) -> str:
    """Удаляет лишний технический текст из названий команд (матч, счет, серии и т.д.)"""
    if not s:
        return ""
    # Удаляем "(Первый матч 0:0)", "счет 1:1" и т.п.
    s = re.sub(r"\(?Первый матч\s+\d+:\d+\)?", "", s, flags=re.I)
    s = re.sub(r"\(?счет\s+\d+:\d+\)?", "", s, flags=re.I)
    s = re.sub(r"\(?серия\s+\d+:\d+\)?", "", s, flags=re.I)
    
    # Удаляем счет по сетам/геймам в скобках: (11:8, 4:11, 11:7)
    s = re.sub(r"\(\d{1,2}:\d{1,2}(?:,\s*\d{1,2}:\d{1,2})*\)", "", s)
    
    # Удаляем счет в конце или отдельно
    s = re.sub(r"\d+:\d+", "", s).strip()
    
    # Удаляем слово "матч" если оно стоит отдельно
    s = re.sub(r"\bматч\b", "", s, flags=re.I).strip()
    # Удаляем лишние пробелы, тире и спецсимволы по краям
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -/\\")


def as_float(s: str) -> Optional[float]:
    if s is None:
        return None
    s = s.replace(",", ".").strip()
    if not s:
        return None
    try:
        return float(s)
    except:
        return None


@dataclass
class Link:
    sport: str
    title: str
    url: str


# =========================
# PARSERS
# =========================

def parse_football_table(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    # В сыром HTML контейнер - div.coupon-row
    rows = soup.select("div.coupon-row")
    
    for row in rows:
        # Пытаемся взять ID разными способами (BS может привести к нижнему регистру)
        event_id = row.get("data-event-treeid") or row.get("data-event-treeId") or row.get("data-event-id")
        if not event_id:
            continue
            
        member_links = row.select("a.member-link")
        if len(member_links) < 2:
            continue
            
        t1 = clean_name(member_links[0].get_text())
        t2 = clean_name(member_links[1].get_text())
        
        m_link = member_links[0].get("href")
        match_url = urljoin(BASE, m_link) if m_link else ""

        # Дата и время часто в .date-wrapper или .date
        time_el = row.select_one(".date-wrapper") or row.select_one(".date")
        time_txt = norm_space(time_el.get_text()) if time_el else ""
        
        date_str = ""
        time_str = ""
        m_dt = re.search(r"(\d{1,2}\s+[а-яёА-Я]{2,4})\s+(\d{1,2}:\d{2})", time_txt)
        if m_dt:
            date_str = m_dt.group(1)
            time_str = m_dt.group(2)
        else:
            time_str = time_txt if ":" in time_txt else ""

        odds_dict = {}
        # Мапинг ключей из data-selection-key (содержат @Match_Result.1 или похожее)
        key_map = {
            "Match_Result.1": "p1", "Match_Result.draw": "x", "Match_Result.3": "p2",
            "Result.HD": "p1x", "Result.HA": "p12", "Result.AD": "px2"
        }
        for btn in row.select(".selection-link"):
            sel_key = btn.get("data-selection-key", "")
            for suffix, field in key_map.items():
                if sel_key.endswith(suffix):
                    val = btn.get_text().strip()
                    odds_dict[field] = f"{as_float(val):.3g}" if as_float(val) else "0.00"
                    break

        out.append({
            "sport": "football", "league": "", "id": event_id,
            "date": date_str, "time": time_str, "team1": t1, "team2": t2,
            "match_url": match_url,
            "p1": odds_dict.get("p1", "0.00"), "x": odds_dict.get("x", "0.00"), "p2": odds_dict.get("p2", "0.00"),
            "p1x": odds_dict.get("p1x", "0.00"), "p12": odds_dict.get("p12", "0.00"), "px2": odds_dict.get("px2", "0.00"),
        })

    return out


def parse_2way_winner(html: str, sport: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    for row in soup.select("div.coupon-row"):
        event_id = row.get("data-event-treeId") or row.get("data-event-id")
        if not event_id:
            continue
            
        member_links = row.select("a.member-link")
        if len(member_links) < 2:
            continue
            
        t1 = clean_name(member_links[0].get_text())
        t2 = clean_name(member_links[1].get_text())
        
        m_link = member_links[0].get("href")
        match_url = urljoin(BASE, m_link) if m_link else ""

        time_el = row.select_one(".date-wrapper") or row.select_one(".date")
        time_txt = norm_space(time_el.get_text()) if time_el else ""
        
        date_str = ""
        time_str = ""
        m_dt = re.search(r"(\d{1,2}\s+[а-яёА-Я]{2,4})\s+(\d{1,2}:\d{2})", time_txt)
        if m_dt:
            date_str = m_dt.group(1)
            time_str = m_dt.group(2)
        else:
            time_str = time_txt if ":" in time_txt else ""

        # Для 2-way обычно просто первые две котировки в ряду
        odds_btns = row.select(".selection-link")
        p1_val = p2_val = 0.0
        if len(odds_btns) >= 2:
            p1_val = as_float(odds_btns[0].get_text())
            p2_val = as_float(odds_btns[-1].get_text())

        out.append({
            "sport": sport, "league": "", "id": event_id,
            "date": date_str, "time": time_str, "team1": t1, "team2": t2,
            "match_url": match_url,
            "p1": f"{p1_val:.3g}" if p1_val else "0.00",
            "x": "—",
            "p2": f"{p2_val:.3g}" if p2_val else "0.00",
            "p1x": "—",
            "p12": f"{min(p1_val, p2_val)*0.95:.3g}" if p1_val and p2_val else "0.00",
            "px2": "—",
        })

    return out


def parse_esports_winner_only(html: str, league_title: str) -> List[dict]:
    return parse_2way_winner(html, "esports")


def parse_live_matches(html: str, sport: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    out = []

    # В LIVE Marathon группирует матчи по блокам (category-container)
    containers = soup.select(".category-container")
    if not containers:
        # Fallback если структура другая (бывает в некоторых разделах)
        containers = [soup]

    for cont in containers:
        # Ищем заголовок лиги в этом контейнере
        label_el = cont.select_one(".category-label-td") or cont.select_one(".sport-category-label")
        league_name = "LIVE"
        if label_el:
            # Берем первую строку текста (чтобы не брать "Все события", "Назад" и т.д.)
            raw_txt = label_el.get_text().strip()
            league_name = raw_txt.split('\n')[0].strip()
            # Дополнительная очистка от мусора
            league_name = re.sub(r"\s+(Все события|Назад|Скрыть|Показать|До выигрыша).*", "", league_name, flags=re.I).strip()
            league_name = league_name.strip(" -/")

        rows = cont.select("div.coupon-row")
        for row in rows:
            # Пытаемся взять ID разными способами
            event_id = row.get("data-event-treeid") or row.get("data-event-treeId") or row.get("data-event-id")
            if not event_id:
                continue
                
            member_links = row.select("a.member-link")
            if len(member_links) < 2:
                continue
                
            t1 = clean_name(member_links[0].get_text())
            t2 = clean_name(member_links[1].get_text())
            
            m_link = member_links[0].get("href")
            match_url = urljoin(BASE, m_link) if m_link else ""

            out.append({
                "sport": sport, "league": league_name, "id": event_id,
                "date": "LIVE", "time": "LIVE", "team1": t1, "team2": t2,
                "match_url": match_url,
                "p1": "0.00", "x": "—", "p2": "0.00", "p1x": "—", "p12": "0.00", "px2": "—",
            })
            
            odds_btns = row.select(".selection-link")
            if len(odds_btns) >= 2:
                try:
                    p1_val = odds_btns[0].get_text().strip()
                    p2_val = odds_btns[-1].get_text().strip()
                    p1 = as_float(p1_val)
                    p2 = as_float(p2_val)
                    if p1: out[-1]["p1"] = f"{p1:.3g}"
                    if p2: out[-1]["p2"] = f"{p2:.3g}"
                except:
                    pass

    return out





def main() -> None:
    print("=" * 60)
    print("PRIZMBET Marathon Parser — MAXIMUM LEAGUES + LIVE")
    print("=" * 60)
    
    print(f"[INFO] Парсинг {len(POPULAR_FALLBACK)} лиг...")

    all_items: List[dict] = []
    success_count = 0
    error_count = 0
    
    # Парсинг популярных лиг
    for sport, title, url in POPULAR_FALLBACK:
        print(f"[INFO] Парсинг: {title}")
        try:
            html = http_get(url)
            if sport == "football":
                items = parse_football_table(html)
                for it in items:
                    it["league"] = title
                print(f"[OK]  Матчей: {len(items)}")
            elif sport == "esports":
                items = parse_esports_winner_only(html, title)
                print(f"[OK]  Событий: {len(items)}")
            else:
                items = parse_2way_winner(html, sport)
                for it in items:
                    it["league"] = title
                print(f"[OK]  Событий: {len(items)}")
            
            all_items.extend(items)
            if len(items) > 0:
                success_count += 1
        except Exception as e:
            error_count += 1
            print(f"[ERR] Пропущено ({title}): {e}")

    # Парсинг LIVE событий
    print("\n[INFO] Парсинг LIVE событий...")
    live_sport_map = {
        "/live/26418": "football",
        "/live/43658": "hockey",
        "/live/45356": "basket",
        "/live/22723": "tennis",
        "/live/1372932": "esports",
        "/live/23690": "volleyball",
        "/live/414329": "tabletennis",
        "/live/439050": "mma",
    }
    
    for live_url in LIVE_URLS:
        sport = "other"
        for key, value in live_sport_map.items():
            if key in live_url:
                sport = value
                break
        
        print(f"[INFO] LIVE {sport}: {live_url}")
        try:
            html = http_get(live_url)
            items = parse_live_matches(html, sport)
            print(f"[OK]  LIVE событий: {len(items)}")
            all_items.extend(items)
        except Exception as e:
            print(f"[ERR] LIVE {sport}: {e}")

    # Dedup by (id) and correct sports
    uniq = {}
    for m in all_items:
        m_id = m.get('id', '')
        if not m_id:
            continue
            
        # Для LIVE событий уточняем вид спорта через infer_sport, так как Marathon
        # часто редиректит URL категории на весь список LIVE
        if m.get("date") == "LIVE":
            m["sport"] = infer_sport(m.get("league", ""), m.get("team1", ""), m.get("team2", ""))
            
        if m_id not in uniq:
            uniq[m_id] = m
        else:
            # Если уже есть, обновляем только если новый имеет более понятный спорт
            if uniq[m_id]["sport"] == "other" and m["sport"] != "other":
                uniq[m_id]["sport"] = m["sport"]
            # Если оба LIVE, берем с более чистым названием лиги (если у одного 'Все события')
            if len(m["league"]) > 3 and "Все" not in m["league"]:
                uniq[m_id]["league"] = m["league"]

    all_items = list(uniq.values())

    payload = {
        "last_update": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "matches": all_items,
    }
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] JSON обновлён: {OUT_JSON}")
    print(f"[OK] Всего матчей: {len(all_items)}")
    print(f"[OK] Успешно лиг: {success_count}, Ошибок: {error_count}")

    # Stats by sport
    sports = {}
    for m in all_items:
        sports[m['sport']] = sports.get(m['sport'], 0) + 1
    print("\nПо видам спорта:")
    for sport, count in sorted(sports.items(), key=lambda x: -x[1]):
        print(f"  {sport}: {count}")


if __name__ == "__main__":
    main()
