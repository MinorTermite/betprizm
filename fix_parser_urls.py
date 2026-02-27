import sys

with open('marathon_parser_real.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Restore the original long list of sports first, then replace prefixes
original_list = """    # ==================== HOCKEY ====================
    ("hockey", "КХЛ", f"{BASE}/su/popular/Ice%2BHockey/KHL%2B-%2B52309?lid=15577535"),
    ("hockey", "НХЛ", f"{BASE}/su/popular/Ice%2BHockey/NHL%2B-%2B52310"),
    ("hockey", "ВХЛ", f"{BASE}/su/betting/Ice+Hockey/Russia/VHL%2B-%2B52311"),
    ("hockey", "МХЛ", f"{BASE}/su/betting/Ice+Hockey/Russia/MHL%2B-%2B52312"),
    ("hockey", "Швеция. SHL", f"{BASE}/su/betting/Ice+Hockey/Sweden/SHL%2B-%2B52313"),
    ("hockey", "Финляндия. Liiga", f"{BASE}/su/betting/Ice+Hockey/Finland/Liiga%2B-%2B52314"),
    ("hockey", "Чехия. Extraliga", f"{BASE}/su/betting/Ice+Hockey/Czech%2BRepublic/Extraliga%2B-%2B52315"),
    ("hockey", "Германия. DEL", f"{BASE}/su/betting/Ice+Hockey/Germany/DEL%2B-%2B52316"),
    ("hockey", "Швейцария. National League", f"{BASE}/su/betting/Ice+Hockey/Switzerland/National%2BLeague%2B-%2B52317"),
    ("hockey", "Словакия. Extraliga", f"{BASE}/su/betting/Ice+Hockey/Slovakia/Extraliga%2B-%2B52318"),
    ("hockey", "Австрия. ICEHL", f"{BASE}/su/betting/Ice+Hockey/Austria/ICEHL%2B-%2B52319"),
    ("hockey", "Норвегия. Eliteserien", f"{BASE}/su/betting/Ice+Hockey/Norway/Eliteserien%2B-%2B52320"),
    ("hockey", "Дания. Metal Ligaen", f"{BASE}/su/betting/Ice+Hockey/Denmark/Metal%2BLigaen%2B-%2B52321"),
    ("hockey", "Беларусь. Экстралига", f"{BASE}/su/betting/Ice+Hockey/Belarus/Extraliga%2B-%2B52322"),
    ("hockey", "Казахстан. ЧРК", f"{BASE}/su/betting/Ice+Hockey/Kazakhstan/Championship%2B-%2B52323"),
    ("hockey", "Польша. PHL", f"{BASE}/su/betting/Ice+Hockey/Poland/PHL%2B-%2B52324"),
    ("hockey", "Великобритания. EIHL", f"{BASE}/su/betting/Ice+Hockey/United%2BKingdom/EIHL%2B-%2B52325"),
    ("hockey", "Франция. Ligue Magnus", f"{BASE}/su/betting/Ice+Hockey/France/Ligue%2BMagnus%2B-%2B52326"),
    ("hockey", "Швейцария. Swiss League", f"{BASE}/su/betting/Ice+Hockey/Switzerland/Swiss%2BLeague%2B-%2B52327"),
    ("hockey", "Россия. Женская лига", f"{BASE}/su/betting/Ice+Hockey/Russia/Women%2BLeague%2B-%2B52328"),
    
    # ==================== BASKETBALL ====================
    ("basket", "NBA", f"{BASE}/su/popular/Basketball/NBA%2B-%2B69367?lid=15577646"),
    ("basket", "Евролига", f"{BASE}/su/betting/Basketball/Europe/EuroLeague%2B-%2B69368"),
    ("basket", "Еврокубок", f"{BASE}/su/betting/Basketball/Europe/EuroCup%2B-%2B69369"),
    ("basket", "Единая лига ВТБ", f"{BASE}/su/betting/Basketball/International/VTB%2BUnited%2BLeague%2B-%2B69370"),
    ("basket", "Испания. ACB", f"{BASE}/su/betting/Basketball/Spain/ACB%2B-%2B69371"),
    ("basket", "Турция. BSL", f"{BASE}/su/betting/Basketball/Turkey/BSL%2B-%2B69372"),
    ("basket", "Италия. LBA", f"{BASE}/su/betting/Basketball/Italy/Lega%2BA%2B-%2B69373"),
    ("basket", "Германия. BBL", f"{BASE}/su/betting/Basketball/Germany/BBL%2B-%2B69374"),
    ("basket", "Франция. Pro A", f"{BASE}/su/betting/Basketball/France/Pro%2BA%2B-%2B69375"),
    ("basket", "Греция. HEBA A1", f"{BASE}/su/betting/Basketball/Greece/A1%2BEthniki%2B-%2B69376"),
    ("basket", "Австралия. NBL", f"{BASE}/su/betting/Basketball/Australia/NBL%2B-%2B69377"),
    ("basket", "Китай. CBA", f"{BASE}/su/betting/Basketball/China/CBA%2B-%2B69378"),
    ("basket", "Аргентина. LNB", f"{BASE}/su/betting/Basketball/Argentina/LNB%2B-%2B69379"),
    ("basket", "Бразилия. NBB", f"{BASE}/su/betting/Basketball/Brazil/NBB%2B-%2B69380"),
    ("basket", "Литва. LKL", f"{BASE}/su/betting/Basketball/Lithuania/LKL%2B-%2B69381"),
    ("basket", "Сербия. KLS", f"{BASE}/su/betting/Basketball/Serbia/KLS%2B-%2B69382"),
    ("basket", "Хорватия. ABA", f"{BASE}/su/betting/Basketball/Croatia/ABA%2B-%2B69383"),
    ("basket", "Польша. PLK", f"{BASE}/su/betting/Basketball/Poland/PLK%2B-%2B69384"),
    ("basket", "Израиль. Winner League", f"{BASE}/su/betting/Basketball/Israel/Winner%2BLeague%2B-%2B69385"),
    ("basket", "Бельгия. BNXT", f"{BASE}/su/betting/Basketball/Belgium/BNXT%2B-%2B69386"),
    ("basket", "WNBA", f"{BASE}/su/betting/Basketball/USA/WNBA%2B-%2B69387"),
    ("basket", "NCAA", f"{BASE}/su/betting/Basketball/USA/NCAA%2B-%2B69388"),
    
    # ==================== TENNIS ====================
    ("tennis", "ATP. Australian Open", f"{BASE}/su/betting/Tennis/ATP/Australian%2BOpen%2B-%2B88880"),
    ("tennis", "ATP. Roland Garros", f"{BASE}/su/betting/Tennis/ATP/Roland%2BGarros%2B-%2B88881"),
    ("tennis", "ATP. Уимблдон", f"{BASE}/su/betting/Tennis/ATP/Wimbledon%2B-%2B88882"),
    ("tennis", "ATP. US Open", f"{BASE}/su/betting/Tennis/ATP/US%2BOpen%2B-%2B88883"),
    ("tennis", "ATP. Masters 1000", f"{BASE}/su/betting/Tennis/ATP/Masters%2B1000%2B-%2B88884"),
    ("tennis", "ATP. Турниры 500", f"{BASE}/su/betting/Tennis/ATP/ATP%2B500%2B-%2B88885"),
    ("tennis", "ATP. Турниры 250", f"{BASE}/su/betting/Tennis/ATP/ATP%2B250%2B-%2B88886"),
    ("tennis", "WTA. Australian Open", f"{BASE}/su/betting/Tennis/WTA/Australian%2BOpen%2B-%2B88887"),
    ("tennis", "WTA. Roland Garros", f"{BASE}/su/betting/Tennis/WTA/Roland%2BGarros%2B-%2B88888"),
    ("tennis", "WTA. Уимблдон", f"{BASE}/su/betting/Tennis/WTA/Wimbledon%2B-%2B88889"),
    ("tennis", "WTA. US Open", f"{BASE}/su/betting/Tennis/WTA/US%2BOpen%2B-%2B88890"),
    ("tennis", "WTA. Турниры 1000", f"{BASE}/su/betting/Tennis/WTA/WTA%2B1000%2B-%2B88891"),
    ("tennis", "WTA. Турниры 500", f"{BASE}/su/betting/Tennis/WTA/WTA%2B500%2B-%2B88892"),
    ("tennis", "WTA. Турниры 250", f"{BASE}/su/betting/Tennis/WTA/WTA%2B250%2B-%2B88893"),
    ("tennis", "ITF. Мужчины", f"{BASE}/su/betting/Tennis/ITF/Men%2B-%2B88894"),
    ("tennis", "ITF. Женщины", f"{BASE}/su/betting/Tennis/ITF/Women%2B-%2B88895"),
    ("tennis", "Challenger", f"{BASE}/su/betting/Tennis/ATP/Challenger%2B-%2B88896"),
    ("tennis", "Davis Cup", f"{BASE}/su/betting/Tennis/International/Davis%2BCup%2B-%2B88897"),
    
    # ==================== VOLLEYBALL ====================
    ("volleyball", "CEV. Лига чемпионов", f"{BASE}/su/betting/Volleyball/Europe/CEV%2BChampions%2BLeague%2B-%2B77777"),
    ("volleyball", "Россия. Суперлига", f"{BASE}/su/betting/Volleyball/Russia/Superliga%2B-%2B77778"),
    ("volleyball", "Италия. SuperLega", f"{BASE}/su/betting/Volleyball/Italy/SuperLega%2B-%2B77779"),
    ("volleyball", "Польша. PlusLiga", f"{BASE}/su/betting/Volleyball/Poland/PlusLiga%2B-%2B77780"),
    ("volleyball", "Германия. Bundesliga", f"{BASE}/su/betting/Volleyball/Germany/Bundesliga%2B-%2B77781"),
    ("volleyball", "Франция. Ligue A", f"{BASE}/su/betting/Volleyball/France/Ligue%2BA%2B-%2B77782"),
    ("volleyball", "Турция. Efeler Ligi", f"{BASE}/su/betting/Volleyball/Turkey/Efeler%2BLigi%2B-%2B77783"),
    ("volleyball", "Бразилия. Superliga", f"{BASE}/su/betting/Volleyball/Brazil/Superliga%2B-%2B77784"),
    ("volleyball", "Италия. Серия A1 (жен)", f"{BASE}/su/betting/Volleyball/Italy/Serie%2BA1%2BWomen%2B-%2B77785"),
    ("volleyball", "Турция. Sultanlar Ligi", f"{BASE}/su/betting/Volleyball/Turkey/Sultanlar%2BLigi%2B-%2B77786"),
    ("volleyball", "Россия. Суперлига (жен)", f"{BASE}/su/betting/Volleyball/Russia/Superliga%2BWomen%2B-%2B77787"),
    ("volleyball", "Польша. Tauron Liga (жен)", f"{BASE}/su/betting/Volleyball/Poland/Tauron%2BLiga%2B-%2B77788"),
    ("volleyball", "Лига наций. Мужчины", f"{BASE}/su/betting/Volleyball/International/VNL%2BMen%2B-%2B77789"),
    ("volleyball", "Лига наций. Женщины", f"{BASE}/su/betting/Volleyball/International/VNL%2BWomen%2B-%2B77790"),
    
    # ==================== MMA ====================
    ("mma", "UFC", f"{BASE}/su/betting/MMA/UFC%2B-%2B99999"),
    ("mma", "Bellator", f"{BASE}/su/betting/MMA/Bellator%2B-%2B99998"),
    ("mma", "ONE Championship", f"{BASE}/su/betting/MMA/ONE%2BChampionship%2B-%2B99997"),
    ("mma", "PFL", f"{BASE}/su/betting/MMA/PFL%2B-%2B99996"),
    ("mma", "ACA", f"{BASE}/su/betting/MMA/ACA%2B-%2B99995"),
    ("mma", "RCC", f"{BASE}/su/betting/MMA/RCC%2B-%2B99994"),
    ("mma", "Eagle FC", f"{BASE}/su/betting/MMA/Eagle%2BFC%2B-%2B99993"),
    ("mma", "UFC. Вечер боёв", f"{BASE}/su/betting/MMA/UFC/Fight%2BNight%2B-%2B99992"),
    
    # ==================== ESPORTS ====================
    ("esports", "CS2. Major", f"{BASE}/su/betting/e-Sports/Counter-Strike/Major%2B-%2B111111"),
    ("esports", "CS2. ESL Pro League", f"{BASE}/su/betting/e-Sports/Counter-Strike/ESL%2BPro%2BLeague%2B-%2B111112"),
    ("esports", "CS2. BLAST Premier", f"{BASE}/su/betting/e-Sports/Counter-Strike/BLAST%2BPremier%2B-%2B111113"),
    ("esports", "CS2. IEM", f"{BASE}/su/betting/e-Sports/Counter-Strike/IEM%2B-%2B111114"),
    ("esports", "Dota 2. The International", f"{BASE}/su/betting/e-Sports/Dota%2B2/The%2BInternational%2B-%2B111115"),
    ("esports", "Dota 2. DPC", f"{BASE}/su/betting/e-Sports/Dota%2B2/DPC%2B-%2B111116"),
    ("esports", "Dota 2. BLAST Slam", f"{BASE}/su/betting/e-Sports/Dota+2/BLAST+Slam+-+20603920?lid=20621739"),
    ("esports", "LoL. LCK", f"{BASE}/su/betting/e-Sports/League%2Bof%2BLegends/LCK%2B-%2B111117"),
    ("esports", "LoL. LPL", f"{BASE}/su/betting/e-Sports/League%2Bof%2BLegends/LPL%2B-%2B111118"),
    ("esports", "LoL. LEC", f"{BASE}/su/betting/e-Sports/League%2Bof%2BLegends/LEC%2B-%2B111119"),
    ("esports", "LoL. LCS", f"{BASE}/su/betting/e-Sports/League%2Bof%2BLegends/LCS%2B-%2B111120"),
    ("esports", "LoL. Worlds", f"{BASE}/su/betting/e-Sports/League%2Bof%2BLegends/Worlds%2B-%2B111121"),
    ("esports", "Valorant. Champions Tour", f"{BASE}/su/betting/e-Sports/Valorant/VCT%2B-%2B111122"),
    ("esports", "Rocket League. RLCS", f"{BASE}/su/betting/e-Sports/Rocket%2BLeague/RLCS%2B-%2B111123"),
    ("esports", "Overwatch. OWL", f"{BASE}/su/betting/e-Sports/Overwatch/OWL%2B-%2B111124"),
    ("esports", "PUBG. Global Championship", f"{BASE}/su/betting/e-Sports/PUBG/Global%2BChampionship%2B-%2B111125"),
    ("esports", "Apex Legends. ALGS", f"{BASE}/su/betting/e-Sports/Apex%2BLegends/ALGS%2B-%2B111126"),
    ("esports", "Rainbow Six. EUL", f"{BASE}/su/betting/e-Sports/Rainbow%2BSix/European%2BLeague%2B-%2B111127"),
"""

# I need to find the block in marathon_parser_real.py and replace it
import re

content = re.sub(
    r'    # ==================== HOCKEY ====================.*# ==================== ESPORTS ====================[^\]]*\]',
    original_list + "\n]",
    content,
    flags=re.DOTALL
)

# And fix the football ones too
content = content.replace(r'/su/football/', '/su/betting/Football/')

with open('marathon_parser_real.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replacement done")
