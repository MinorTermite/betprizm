#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💎 PRIZMBET - Автообновление данных
Объединённая версия с лучшими функциями из обоих проектов
"""

import schedule
import time
import subprocess
import datetime
import json
import os
from pathlib import Path

# ===== КОНФИГУРАЦИЯ =====
UPDATE_INTERVAL_HOURS = int(os.getenv("UPDATE_INTERVAL_HOURS", "5"))
MATCHES_FILE = "matches.json"
LOG_FILE = "update_log.txt"
PARSER_SCRIPT = "marathon_to_sheets.py"

def print_banner():
    """Красивый баннер при запуске"""
    banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║        💎 PRIZMBET - СИСТЕМА АВТООБНОВЛЕНИЯ v2.0                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝

⚙️  Конфигурация:
   • Интервал обновления: каждые {UPDATE_INTERVAL_HOURS} часа(ов)
   • Файл данных: {MATCHES_FILE}
   • Лог-файл: {LOG_FILE}
   • Парсер: {PARSER_SCRIPT}

📊 Что обновляется:
   ✓ Коэффициенты на все матчи
   ✓ Список актуальных матчей
   ✓ Дата и время последнего обновления
   ✓ Запись в Google Sheets (если настроено)

💡 Особенности:
   • Первое обновление сразу при запуске
   • Автоматическое создание резервных данных при ошибках
   • Детальное логирование всех операций
   • Graceful shutdown при Ctrl+C

🛑 Остановка: Нажмите Ctrl+C

"""
    print(banner)

def log_message(message, level="INFO"):
    """Логирование с временной меткой и уровнем"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    prefix = {
        "INFO": "ℹ️ ",
        "SUCCESS": "✅",
        "ERROR": "❌",
        "WARNING": "⚠️ ",
        "START": "🔄",
        "FINISH": "🏁"
    }.get(level, "")
    
    log_entry = f"[{timestamp}] {prefix} {message}"
    print(log_entry)
    
    # Сохранение в лог-файл
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    except:
        pass

def separator(char="=", length=70):
    """Печать разделителя"""
    print(char * length)

def update_matches():
    """Основная функция обновления данных"""
    separator()
    log_message("ЗАПУСК ОБНОВЛЕНИЯ ДАННЫХ", "START")
    separator()
    
    try:
        # Проверка наличия парсера
        if not os.path.exists(PARSER_SCRIPT):
            log_message(f"Файл {PARSER_SCRIPT} не найден!", "WARNING")
            log_message("Создание mock данных...", "INFO")
            create_mock_data()
            return
        
        # Запуск парсера
        log_message("Запуск парсера Marathon...", "INFO")
        result = subprocess.run(
            ['python', PARSER_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300,  # 5 минут таймаут
            encoding='utf-8'
        )
        
        # Вывод результатов парсера
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        if result.returncode == 0:
            log_message("Парсинг завершён успешно!", "SUCCESS")
            
            # Проверка и статистика файла
            if os.path.exists(MATCHES_FILE):
                size = os.path.getsize(MATCHES_FILE)
                with open(MATCHES_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    matches_count = len(data.get('matches', []))
                    
                    # Группировка по лигам
                    leagues = {}
                    for match in data.get('matches', []):
                        league = match.get('league', 'Неизвестно')
                        leagues[league] = leagues.get(league, 0) + 1
                    
                    log_message(f"Загружено матчей: {matches_count}", "SUCCESS")
                    log_message(f"Количество лиг: {len(leagues)}", "SUCCESS")
                    log_message(f"Размер файла: {size / 1024:.2f} KB", "INFO")
                    
                    # Топ-5 лиг по количеству матчей
                    if leagues:
                        print("\n📊 Топ-5 лиг по количеству матчей:")
                        sorted_leagues = sorted(leagues.items(), key=lambda x: x[1], reverse=True)[:5]
                        for i, (league, count) in enumerate(sorted_leagues, 1):
                            print(f"  {i}. {league}: {count} матч(ей)")
            else:
                log_message("Файл matches.json не создан!", "WARNING")
        else:
            log_message("Ошибка при парсинге:", "ERROR")
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip():
                        print(f"  ⚠️  {line}")
            log_message("Использование существующих данных...", "INFO")
    
    except subprocess.TimeoutExpired:
        log_message("Превышено время ожидания (5 минут)", "WARNING")
        log_message("Парсинг прерван, используются существующие данные", "INFO")
    except Exception as e:
        log_message(f"Критическая ошибка: {str(e)}", "ERROR")
        log_message("Создание резервных данных...", "INFO")
        create_mock_data()
    
    # Время следующего обновления
    next_update = datetime.datetime.now() + datetime.timedelta(hours=UPDATE_INTERVAL_HOURS)
    separator()
    log_message(f"Следующее обновление: {next_update.strftime('%Y-%m-%d %H:%M:%S')}", "INFO")
    separator()
    print()

def create_mock_data():
    """Создание тестовых данных при ошибках"""
    mock_data = {
        "last_update": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "matches": [
            {
                "sport": "football",
                "league": "Англия. Премьер-лига",
                "id": "MOCK001",
                "date": datetime.datetime.now().strftime('%d %b'),
                "time": "20:00",
                "team1": "Манчестер Сити",
                "team2": "Ливерпуль",
                "p1": "2.10",
                "x": "3.40",
                "p2": "3.50",
                "p1x": "1.30",
                "p12": "1.25",
                "px2": "1.70"
            },
            {
                "sport": "hockey",
                "league": "КХЛ",
                "id": "MOCK002",
                "date": datetime.datetime.now().strftime('%d %b'),
                "time": "19:30",
                "team1": "СКА",
                "team2": "ЦСКА",
                "p1": "1.85",
                "x": "0.00",
                "p2": "2.10",
                "p1x": "0.00",
                "p12": "0.00",
                "px2": "0.00"
            }
        ]
    }
    
    with open(MATCHES_FILE, 'w', encoding='utf-8') as f:
        json.dump(mock_data, f, ensure_ascii=False, indent=2)
    
    log_message(f"Созданы тестовые данные в {MATCHES_FILE}", "SUCCESS")

def main():
    """Главная функция"""
    print_banner()
    
    # Настройка расписания
    schedule.every(UPDATE_INTERVAL_HOURS).hours.do(update_matches)
    
    # Первое обновление сразу при запуске
    log_message("ПЕРВОЕ ОБНОВЛЕНИЕ ПРИ ЗАПУСКЕ", "START")
    update_matches()
    
    # Бесконечный цикл проверки расписания
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Проверка каждую минуту
    except KeyboardInterrupt:
        print()
        separator()
        log_message("АВТООБНОВЛЕНИЕ ОСТАНОВЛЕНО ПОЛЬЗОВАТЕЛЕМ", "FINISH")
        separator()
        print("\n💎 Спасибо за использование PRIZMBET!")
        print("📱 Telegram: https://t.me/+PMrQ9Nbzu08wYmI0\n")

if __name__ == "__main__":
    main()
