#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PRIZM Blockchain API — чтение транзакций кошелька"""

import json
import time
import requests

PRIZM_NODES = [
    "https://blockchain.prizm.space",
    "https://node1.prizm.space",
    "https://node2.prizm.space",
]
WALLET = "PRIZM-4N7T-L2A7-RQZA-5BETW"
CACHE_FILE = "prizm_last_tx.json"


def _get(params: dict, timeout=10) -> dict | None:
    for node in PRIZM_NODES:
        try:
            r = requests.get(f"{node}/prizm", params=params, timeout=timeout)
            if r.ok:
                return r.json()
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
    # Загружаем последний известный timestamp
    last_ts = 0
    try:
        with open(CACHE_FILE) as f:
            last_ts = json.load(f).get("last_ts", 0)
    except Exception:
        pass

    txs = get_transactions()
    new_txs = [t for t in txs if t.get("timestamp", 0) > last_ts]

    if new_txs:
        new_last = max(t.get("timestamp", 0) for t in new_txs)
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"last_ts": new_last, "checked": int(time.time())}, f)
        except Exception:
            pass

    return new_txs


def parse_bet_comment(comment: str) -> dict | None:
    """
    Разобрать комментарий ставки.
    Формат: "27080379 П1 10" или "27080379 п2 5.5"
    Возвращает: {"match_id": "27080379", "bet_type": "П1", "amount": 10.0}
    """
    if not comment:
        return None
    parts = comment.strip().split()
    if len(parts) < 2:
        return None

    match_id = parts[0]
    if not match_id.isdigit():
        return None

    bet_type = parts[1].upper()
    valid_types = {"П1", "П2", "X", "1X", "X2", "12", "P1", "P2"}
    # Нормализуем P1/P2 → П1/П2
    bet_type = bet_type.replace("P1", "П1").replace("P2", "П2")
    if bet_type not in valid_types:
        return None

    amount = 0.0
    if len(parts) >= 3:
        try:
            amount = float(parts[2])
        except ValueError:
            pass

    return {"match_id": match_id, "bet_type": bet_type, "amount": amount}


def prizm_amount(tx: dict) -> float:
    """Перевести внутренние единицы PRIZM → реальные монеты"""
    raw = tx.get("amountNQT", 0)
    try:
        return int(raw) / 100  # 1 PRIZM = 100 NQT
    except Exception:
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
                timeout=10,
            )
            if not r.ok:
                continue
            data = r.json()
            if "errorCode" in data:
                continue
            # balanceNQT и unconfirmedBalanceNQT — в NQT (делим на 100)
            balance_nqt     = int(data.get("balanceNQT", 0))
            unconfirmed_nqt = int(data.get("unconfirmedBalanceNQT", 0))
            return {
                "balance":     balance_nqt / 100,
                "unconfirmed": unconfirmed_nqt / 100,
                "wallet":      WALLET,
                "node":        node,
            }
        except Exception:
            continue
    return {"balance": None, "unconfirmed": None, "wallet": WALLET, "node": None}
