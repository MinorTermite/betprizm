#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET - Парсер ставок
Читает входящие транзакции PRIZM-кошелька,
парсит комментарий (формат: "ID исход сумма"),
сохраняет в bets.json + Google Sheets
"""

import json
import os
import re
import requests
from datetime import datetime, timezone

# ===== КОНФИГУРАЦИЯ =====
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
WALLET      = "PRIZM-4N7T-L2A7-RQZA-5BETW"
PRIZM_NODES = [
    "https://n1.prizm.space:9976",
    "https://n2.prizm.space:9976",
    "http://node1.prizm.space:9976",
]
PRIZM_EPOCH = 1511654400   # 2017-11-26 00:00:00 UTC (genesis PRIZM)
NQT         = 100_000_000  # 1 PRIZM = 100000000 NQT

BETS_FILE    = os.path.join(SCRIPT_DIR, "bets.json")
MATCHES_FILE = os.path.join(SCRIPT_DIR, "matches.json")
CREDS_FILE   = os.path.join(SCRIPT_DIR, "credentials.json")
SHEET_ID     = "1QkVj51WMKSd6-LU4vZK3dYPk6QLQIO014ydpACtThNk"

# ===== PRIZM API =====

def prizm_request(params, timeout=15):
    """Выполнить запрос к PRIZM-ноде (пробует несколько нод)"""
    for node in PRIZM_NODES:
        try:
            r = requests.get(f"{node}/prizm", params=params, timeout=timeout, verify=False)
            data = r.json()
            if "errorCode" not in data:
                return data
        except Exception:
            continue
    return {}


def get_transactions(first_index=0, last_index=99):
    """Получить входящие транзакции на кошелёк"""
    data = prizm_request({
        "requestType":      "getAccountTransactions",
        "account":          WALLET,
        "type":             0,       # обычный платёж
        "subtype":          0,
        "firstIndex":       first_index,
        "lastIndex":        last_index,
        "includeIndirect":  "false",
    })
    return data.get("transactions", [])


# ===== ВСПОМОГАТЕЛЬНЫЕ =====

def prizm_ts_to_dt(ts):
    """Перевод PRIZM timestamp → строка даты"""
    try:
        return datetime.fromtimestamp(PRIZM_EPOCH + int(ts), tz=timezone.utc)\
                       .strftime('%Y-%m-%d %H:%M:%S')
    except Exception:
        return datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def nqt_to_pzm(nqt_str):
    """Перевод NQT → PZM"""
    try:
        return round(int(nqt_str) / NQT, 2)
    except Exception:
        return 0.0


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ===== ПАРСИНГ КОММЕНТАРИЯ =====

# Поддерживаемые форматы: "27080379 П1 10", "27080379 P2 5.5", "27080379 X 20"
BET_PATTERN = re.compile(
    r'^(\d+)\s+(П1|П2|P1|P2|X|1X|X2|12|1|2)\s+([\d]+(?:[.,]\d+)?)$',
    re.IGNORECASE | re.UNICODE
)

OUTCOME_MAP = {
    "P1": "П1", "1": "П1",
    "P2": "П2", "2": "П2",
}


def parse_comment(text):
    """
    Возвращает (match_id, outcome, amount) или None.
    Принимает кириллицу и латиницу, запятую или точку.
    """
    if not text:
        return None
    text = text.strip()
    m = BET_PATTERN.match(text)
    if not m:
        return None
    match_id = m.group(1)
    outcome  = m.group(2).upper()
    outcome  = OUTCOME_MAP.get(outcome, outcome)   # нормализуем латиницу → кириллица
    amount   = float(m.group(3).replace(",", "."))
    return match_id, outcome, amount


# ===== МАТЧИ =====

def load_matches_index():
    """Индекс матчей по ID строкой"""
    data = load_json(MATCHES_FILE, {})
    return {str(m["id"]): m for m in data.get("matches", [])}


def get_coef(match, outcome):
    """Получить коэффициент для исхода"""
    odds = match.get("odds") or {}
    # ключи в odds: "1", "X", "2", "1X", "X2", "12"
    key_map = {"П1": "1", "П2": "2", "X": "X", "1X": "1X", "X2": "X2", "12": "12"}
    return float(odds.get(key_map.get(outcome, outcome), 0) or 0)


# ===== СТАВКИ =====

def load_bets():
    return load_json(BETS_FILE, {"bets": [], "last_update": None, "total_bets": 0})


def process_transactions(txs, matches_idx, existing_bets):
    """Вернуть список новых ставок из транзакций"""
    seen_tx = {b["tx_id"] for b in existing_bets}
    new_bets = []

    for tx in txs:
        tx_id = tx.get("transaction") or tx.get("fullHash", "")
        if tx_id in seen_tx:
            continue

        # Пропускаем исходящие (от нашего кошелька)
        if tx.get("recipientRS", "") != WALLET:
            continue

        # Читаем сообщение из attachment
        att = tx.get("attachment") or {}
        message = att.get("message", "")
        if not att.get("messageIsText", True):
            continue   # бинарное сообщение — пропускаем

        parsed = parse_comment(message)
        if not parsed:
            # транзакция без корректной ставки — просто пропускаем
            continue

        match_id, outcome, amount_from_comment = parsed
        amount_actual = nqt_to_pzm(tx.get("amountNQT", "0"))

        match     = matches_idx.get(match_id)
        coef      = get_coef(match, outcome) if match else 0.0
        pot_win   = round(amount_actual * coef, 2) if coef else 0.0
        bet_time  = prizm_ts_to_dt(tx.get("timestamp", 0))

        if match:
            match_name = f"{match.get('team1','?')} vs {match.get('team2','?')}"
            sport      = match.get("sport", "—")
        else:
            match_name = f"Матч #{match_id}"
            sport      = "—"

        bet = {
            "tx_id":       tx_id,
            "from_wallet": tx.get("senderRS", "—"),
            "match_id":    match_id,
            "match_name":  match_name,
            "sport":       sport,
            "outcome":     outcome,
            "coefficient": coef,
            "amount":      amount_actual,
            "potential_win": pot_win,
            "status":      "pending",
            "time":        bet_time,
            "comment":     message,
        }
        new_bets.append(bet)
        print(f"  [BET] {bet['from_wallet'][:20]}... | {match_name} | "
              f"{outcome} × {coef} | {amount_actual} PZM → {pot_win} PZM")

    return new_bets


# ===== GOOGLE SHEETS =====

def update_sheets(all_bets):
    try:
        from google.oauth2.service_account import Credentials
        import gspread

        creds = Credentials.from_service_account_file(
            CREDS_FILE,
            scopes=["https://www.googleapis.com/auth/spreadsheets"]
        )
        gc    = gspread.authorize(creds)
        sheet = gc.open_by_key(SHEET_ID)

        try:
            ws = sheet.worksheet("Ставки")
        except Exception:
            ws = sheet.add_worksheet("Ставки", rows=2000, cols=12)

        headers = ["TX ID", "Кошелёк", "Матч", "Спорт",
                   "Исход", "Коэф", "Сумма PZM", "Выигрыш PZM", "Статус", "Время"]

        existing = ws.get_all_values()
        if not existing or existing[0] != headers:
            ws.clear()
            ws.append_row(headers)
            existing = [headers]

        existing_txs = {row[0] for row in existing[1:]}
        new_rows = [
            [b["tx_id"], b["from_wallet"], b["match_name"], b["sport"],
             b["outcome"], b["coefficient"], b["amount"], b["potential_win"],
             b["status"], b["time"]]
            for b in all_bets if b["tx_id"] not in existing_txs
        ]
        if new_rows:
            ws.append_rows(new_rows, value_input_option="USER_ENTERED")
        print(f"  [OK] Google Sheets: +{len(new_rows)} строк")
    except Exception as e:
        print(f"  [WARN] Google Sheets недоступен: {e}")


# ===== MAIN =====

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"[{now}] Проверка ставок PRIZM...")

    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    matches_idx = load_matches_index()
    bets_data   = load_bets()
    existing    = bets_data.get("bets", [])

    print(f"  Матчей в базе: {len(matches_idx)}")
    print(f"  Ставок в базе: {len(existing)}")

    txs = get_transactions()
    print(f"  Транзакций получено: {len(txs)}")

    if not txs:
        print("  Нет новых транзакций или API недоступен")
        return

    new_bets = process_transactions(txs, matches_idx, existing)
    print(f"  Новых ставок: {len(new_bets)}")

    if new_bets:
        all_bets = existing + new_bets
        bets_data = {
            "last_update": now,
            "total_bets":  len(all_bets),
            "bets":        all_bets,
        }
        save_json(BETS_FILE, bets_data)
        print(f"  [OK] bets.json сохранён ({len(all_bets)} ставок)")

        if os.path.exists(CREDS_FILE):
            update_sheets(all_bets)
    else:
        # Обновляем временную метку даже без новых ставок
        bets_data["last_update"] = now
        save_json(BETS_FILE, bets_data)

    print(f"  Done.")


if __name__ == "__main__":
    main()
