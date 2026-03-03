#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRIZM Blockchain API — чтение транзакций кошелька"""

import json
import time
import requests

# Подтверждённые рабочие ноды (core.prizm.vip — основная, проверено 2026-02-28)
PRIZM_NODES = [
    "https://core.prizm.vip",
    "https://blockchain.prizm.vip",
]
WALLET = "PRIZM-4N7T-L2A7-RQZA-5BETW"
CACHE_FILE = "prizm_last_tx.json"
NQT = 100  # 1 PRIZM = 100 NQT (2 decimal places)


def _get(params: dict, timeout=12) -> dict | None:
    for node in PRIZM_NODES:
        try:
            r = requests.get(f"{node}/prizm", params=params, timeout=timeout, verify=True)
            if r.ok:
                data = r.json()
                if "errorCode" not in data:
                    return data
        except Exception:
            continue
    return None


def get_transactions(first_index=0, last_index=99) -> list[dict]:
    """Получить список транзакций на кошелёк PRIZM"""
    data = _get({
        "requestType": "getBlockchainTransactions",
        "account": WALLET,
        "type": 0,
        "firstIndex": first_index,
        "lastIndex": last_index,
    })
    if not data:
        return []
    return data.get("transactions", [])


def get_new_transactions() -> list[dict]:
    """Вернуть только новые транзакции (после последней проверки)"""
    last_ts = 0
    try:
        with open(CACHE_FILE) as f:
            last_ts = json.load(f).get("last_ts", 0)
    except Exception:
        pass

    txs = get_transactions()
    # Возвращаем все транзакции, чтобы телеграм бот мог обрабатывать выплаты (исходящие)
    new_txs = [t for t in txs if t.get("timestamp", 0) > last_ts]

    if new_txs:
        new_last = max(t.get("timestamp", 0) for t in new_txs)
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"last_ts": new_last, "checked": int(time.time())}, f)
        except Exception:
            pass

    return new_txs


def get_message(tx: dict) -> str:
    """
    Извлечь текстовое сообщение из транзакции.
    Поддерживает plain text (attachment.message).
    Зашифрованные сообщения (encryptedMessage) возвращают пустую строку —
    они не могут быть прочитаны без приватного ключа кошелька.
    """
    att = tx.get("attachment") or {}
    msg = att.get("message", "")
    is_text = att.get("messageIsText", True)
    if msg and is_text:
        return str(msg).strip()
    return ""


def has_encrypted_message(tx: dict) -> bool:
    """Проверить есть ли зашифрованное сообщение (ставка с шифрованием)"""
    att = tx.get("attachment") or {}
    return "encryptedMessage" in att


def parse_bet_comment(comment: str) -> dict | None:
    """
    Разобрать комментарий ставки.
    Поддерживает как короткий формат "ID ТИП СУММА", 
    так и длинный дескриптивный "Матч..., ID П1 СУММА".
    """
    if not comment:
        return None
    
    import re
    # Ищем ID (число от 6 до 12 цифр)
    id_match = re.search(r'\b(\d{6,12})\b', comment)
    if not id_match:
        return None
    match_id = id_match.group(1)

    # Ищем тип ставки (П1, П2, X, 1X, X2, 12)
    # Используем word boundaries для точности
    type_match = re.search(r'\b(П1|П2|X|1X|X2|12|P1|P2)\b', comment, re.IGNORECASE)
    if not type_match:
        return None
    bet_type = type_match.group(1).upper().replace("P1", "П1").replace("P2", "П2")

    # Ищем сумму (число после 'Ставка:' или просто число после типа ставки)
    # Сначала пробуем найти число после "Ставка:"
    amount = 0.0
    amt_match = re.search(r'Ставка:\s*([\d\s,.]+)', comment, re.IGNORECASE)
    if amt_match:
        amt_str = amt_match.group(1).replace(" ", "").replace(",", ".")
        try:
            amount = float(amt_str)
        except ValueError:
            pass
    
    # Если не нашли через 'Ставка:', берем первое число после типа ставки или ID
    if amount <= 0:
        # Ищем все числа и берем то, которое не ID и не коэффициент (обычно оно больше 100)
        all_nums = re.findall(r'\b(\d+[\s,.]?\d*)\b', comment)
        for val in all_nums:
            clean_val = val.replace(" ", "").replace(",", ".")
            try:
                num = float(clean_val)
                if num != float(match_id) and num >= 1.0: # Сумма ставки обычно >= 1
                    amount = num
                    # Если это похоже на коэффициент (мелкое число), продолжаем поиск
                    if num < 10 and '.' in clean_val:
                        continue
                    break
            except ValueError:
                continue

    return {"match_id": match_id, "bet_type": bet_type, "amount": amount}


def prizm_amount(tx: dict) -> float:
    """Перевести внутренние единицы PRIZM → реальные монеты (1 PRIZM = 100 NQT)"""
    raw = tx.get("amountNQT", 0)
    try:
        return int(raw) / NQT
    except Exception:
        return 0.0


def get_coef(match: dict, outcome: str) -> float:
    """
    Получить коэффициент для исхода из данных матча.
    Поддерживает:
    1. Текущий плоский формат (p1, x, p2, p1x, p12, px2)
    2. Legacy формат (odds: {"1": ..., "X": ..., "2": ...})
    """
    if not match:
        return 0.0

    # Отображение исходов на плоские поля и ключи словаря odds
    flat_map = {"П1": "p1", "П2": "p2", "X": "x", "1X": "p1x", "X2": "px2", "12": "p12"}
    odds_map = {"П1": "1", "П2": "2", "X": "X", "1X": "1X", "X2": "X2", "12": "12"}

    # 1. Пробуем плоский формат
    field = flat_map.get(outcome)
    if field and field in match:
        val = match.get(field)
        if val and val not in ("—", "-", "0.00", ""):
            try:
                return float(val)
            except (ValueError, TypeError):
                pass

    # 2. Пробуем вложенный словарь odds (legacy)
    odds = match.get("odds") or {}
    key = odds_map.get(outcome, outcome)
    val = odds.get(key)
    if val and val not in ("—", "-", "0.00", ""):
        try:
            return float(val)
        except (ValueError, TypeError):
            pass

    return 0.0


def get_sender_address(tx: dict) -> str:
    return tx.get("senderRS", tx.get("sender", "unknown"))


def get_balance() -> dict:
    """
    Получить баланс кошелька PRIZM.
    Возвращает: {"balance": float, "unconfirmed": float, "wallet": str, "node": str}
    """
    for node in PRIZM_NODES:
        try:
            r = requests.get(
                f"{node}/prizm",
                params={"requestType": "getAccount", "account": WALLET},
                timeout=12,
                verify=True,
            )
            if not r.ok:
                continue
            data = r.json()
            if "errorCode" in data:
                continue
            balance_nqt     = int(data.get("balanceNQT", 0))
            unconfirmed_nqt = int(data.get("unconfirmedBalanceNQT", 0))
            return {
                "balance":     balance_nqt / NQT,
                "unconfirmed": unconfirmed_nqt / NQT,
                "wallet":      WALLET,
                "node":        node,
            }
        except Exception:
            continue
    return {"balance": None, "unconfirmed": None, "wallet": WALLET, "node": None}
