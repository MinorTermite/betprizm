#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PRIZMBET Telegram Bot v3.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ChatAction.TYPING   — «печатает...» на каждой команде
✅ setMyCommands       — автодополнение команд в меню /
✅ Rate Limiter        — защита от флуда
✅ Inline Win/Loss     — кнопки прямо в уведомлении о ставке
✅ Progress Bar        — прогресс при рассылке
✅ Inline Mode         — поиск матчей через @bot в любом чате
✅ Throttle            — задержка между отправками (anti-flood API)
✅ Deep Links          — /start ref_CODE (реферальная ссылка)
✅ Confirm кнопки      — подтверждение опасных действий
✅ Auto-cleanup        — удаление временных сообщений
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import sys
import logging
import time
import asyncio
import hashlib
import functools
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, BotCommand, BotCommandScopeChat,
    InlineQueryResultArticle, InputTextMessageContent,
)
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler, InlineQueryHandler,
)

import prizm_api

# ══════════════════════════════════════════════════════════════
#  КОНФИГ
# ══════════════════════════════════════════════════════════════
BOT_TOKEN    = "8560914086:AAFGDc70pfIwBX0FhwQDWmFjcnnpVvKOxps"
ADMIN_ID     = 984705599
WALLET       = "PRIZM-4N7T-L2A7-RQZA-5BETW"
BETS_FILE    = Path("bets.json")
MATCHES_FILE = Path("matches.json")
CONFIG_FILE  = Path("bot_config.json")

RATE_LIMIT_SEC   = 2      # секунд между командами для обычных юзеров
BROADCAST_DELAY  = 0.05   # задержка между отправками при рассылке (anti-flood)
PROGRESS_STEP    = 10     # обновлять прогресс-бар каждые N пользователей

# ══════════════════════════════════════════════════════════════
#  ЛОГИРОВАНИЕ
# ══════════════════════════════════════════════════════════════
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
#  RATE LIMITER
# ══════════════════════════════════════════════════════════════
_last_cmd: dict[int, float] = defaultdict(float)

def is_rate_limited(user_id: int) -> bool:
    """True если пользователь шлёт команды слишком часто"""
    if user_id == ADMIN_ID:
        return False  # Админ никогда не ограничен
    now = time.monotonic()
    if now - _last_cmd[user_id] < RATE_LIMIT_SEC:
        return True
    _last_cmd[user_id] = now
    return False

# ══════════════════════════════════════════════════════════════
#  ДЕКОРАТОР: TYPING + RATE LIMIT
# ══════════════════════════════════════════════════════════════
def smart_handler(func):
    """
    Универсальный декоратор для всех команд:
    1. Показывает «печатает...» пока обрабатывается запрос
    2. Блокирует флуд (rate limit)
    """
    @functools.wraps(func)
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        if not update.effective_chat or not update.effective_user:
            return
        user_id = update.effective_user.id
        # Rate limit (не для админа)
        if is_rate_limited(user_id):
            return
        # Typing action
        try:
            await update.effective_chat.send_action(ChatAction.TYPING)
        except Exception:
            pass
        return await func(update, ctx)
    return wrapper

# ══════════════════════════════════════════════════════════════
#  КОНФИГ / ХРАНИЛИЩЕ
# ══════════════════════════════════════════════════════════════
def load_config() -> dict:
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8")) if CONFIG_FILE.exists() else {}
    except Exception:
        return {}

def save_config(cfg: dict):
    CONFIG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

def get_notify_ids() -> list[int]:
    cfg = load_config()
    ids = [ADMIN_ID]
    old_group = cfg.get("group_chat_id")
    if old_group and old_group not in ids:
        ids.append(old_group)
    for gid_str in cfg.get("groups", {}).keys():
        try:
            gid = int(gid_str)
            if gid not in ids:
                ids.append(gid)
        except ValueError:
            pass
    return ids

def track_user(user_id: int, first_name: str = "", username: str = ""):
    cfg = load_config()
    users = cfg.setdefault("users", {})
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "first_name": first_name,
            "username": username,
            "joined": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        cfg["users"] = users
        save_config(cfg)

def get_all_users() -> dict:
    return load_config().get("users", {})

def track_group(group_id: int, group_name: str = ""):
    cfg = load_config()
    groups = cfg.setdefault("groups", {})
    gid = str(group_id)
    if gid not in groups:
        groups[gid] = {"name": group_name, "joined": datetime.now().strftime("%Y-%m-%d %H:%M")}
        cfg["groups"] = groups
        save_config(cfg)

def get_all_groups() -> dict:
    return load_config().get("groups", {})

# ══════════════════════════════════════════════════════════════
#  СТАВКИ / МАТЧИ
# ══════════════════════════════════════════════════════════════
def load_bets() -> list:
    try:
        if not BETS_FILE.exists():
            return []
        data = json.loads(BETS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("bets", [])
    except Exception:
        return []

def save_bets(bets: list):
    data = {
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_bets": len(bets),
        "bets": bets,
    }
    BETS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def load_matches() -> dict:
    try:
        data = json.loads(MATCHES_FILE.read_text(encoding="utf-8"))
        return {m["id"]: m for m in data.get("matches", [])}
    except Exception:
        return {}

# ══════════════════════════════════════════════════════════════
#  UI ХЕЛПЕРЫ
# ══════════════════════════════════════════════════════════════
def progress_bar(done: int, total: int, width: int = 12) -> str:
    """█████░░░░░░░ 45%"""
    if total == 0:
        return "[░░░░░░░░░░░░] 0%"
    filled = int(width * done / total)
    bar = "█" * filled + "░" * (width - filled)
    pct = int(100 * done / total)
    return f"[{bar}] {pct}%"

def get_main_keyboard(is_admin=False) -> ReplyKeyboardMarkup:
    buttons = [
        ["🎰 Сделать ставку", "📋 Мои ставки"],
        ["📖 Правила",        "⭐ Преимущества"],
    ]
    if is_admin:
        buttons.append(["📊 Ставки (Админ)", "📈 Статистика"])
        buttons.append(["💰 Баланс",          "📢 Группы"])
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def fmt_bet(bet: dict, idx: int = None) -> str:
    prefix = f"#{idx} " if idx is not None else ""
    emoji  = {"pending": "⏳", "win": "✅", "loss": "❌", "cancelled": "🚫"}.get(bet.get("status"), "⏳")
    league = f"  🏆 {bet['league']}\n" if bet.get("league") else ""
    return (
        f"{prefix}{emoji} *{bet.get('team1','?')} — {bet.get('team2','?')}*\n"
        f"{league}"
        f"  Исход: `{bet.get('bet_type','?')}` | Коэф: `×{bet.get('coef','?')}`\n"
        f"  Ставка: `{bet.get('amount',0):.1f} PRIZM` → Выигрыш: `{bet.get('payout',0):.1f} PRIZM`\n"
        f"  📅 {bet.get('time','?')} | ID: `{bet.get('id','?')}`"
    )

def bet_notify_kb(bet_id: str) -> InlineKeyboardMarkup:
    """Inline кнопки Win/Loss прямо в уведомлении о ставке"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Выигрыш",  callback_data=f"win:{bet_id}"),
        InlineKeyboardButton("❌ Проигрыш", callback_data=f"loss:{bet_id}"),
    ]])

def confirm_kb(action: str, bet_id: str) -> InlineKeyboardMarkup:
    """Кнопки подтверждения опасного действия"""
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Да, подтверждаю", callback_data=f"confirm_{action}:{bet_id}"),
        InlineKeyboardButton("❌ Отмена",           callback_data="cancel"),
    ]])

def referral_code(user_id: int) -> str:
    return hashlib.md5(f"{user_id}:prizmbet2026".encode()).hexdigest()[:8].upper()

# ══════════════════════════════════════════════════════════════
#  КОМАНДЫ — ПУБЛИЧНЫЕ
# ══════════════════════════════════════════════════════════════
@smart_handler
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user     = update.effective_user
    is_admin = (user.id == ADMIN_ID)
    track_user(user.id, user.first_name, user.username or "")

    # Deep link: /start ref_XXXXXXXX
    ref_code = ctx.args[0] if ctx.args else None
    ref_bonus = ""
    if ref_code and ref_code.startswith("ref_"):
        ref_bonus = "\n🎁 *Вы перешли по реферальной ссылке!* Приятной игры."

    text = (
        f"👋 Привет, *{user.first_name}*!{ref_bonus}\n\n"
        "🎰 *PRIZMBET — Криптобукмекер*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Как сделать ставку:\n\n"
        "1️⃣ Открой сайт:\n"
        "   [minortermite.github.io/betprizm](https://minortermite.github.io/betprizm)\n"
        "2️⃣ Выбери матч и нажми на коэффициент\n"
        "3️⃣ Скопируй сообщение из купона\n"
        "4️⃣ Отправь PRIZM на кошелёк:\n"
        f"   `{WALLET}`\n"
        "5️⃣ В комментарий вставь скопированный текст\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📌 Используй кнопки меню ниже"
    )
    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=get_main_keyboard(is_admin),
    )

@smart_handler
async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Справка PRIZMBET*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎯 *Обозначения ставок:*\n"
        "  `П1` — победа хозяев\n"
        "  `П2` — победа гостей\n"
        "  `X`  — ничья\n"
        "  `1X` / `X2` / `12` — двойные исходы\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Пример комментария к переводу:*\n"
        "`Галатасарай vs Ливерпуль 10 мар 20:45 П2 1.76`\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🔎 Поиск матчей прямо в чате:\n"
        "Напиши `@PrizmBet2bot <команда>` в любом чате\n\n"
        "👉 Полные правила: /rules"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_rules(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 *ПРАВИЛА PRIZMBET*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💎 *Ставки принимаются только в PRIZM*\n\n"
        "📊 *Лимиты:*\n"
        "  • Минимум: `1 500 PRIZM`\n"
        "  • Максимум: `200 000 PRIZM`\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🏷️ *Типы ставок:*\n"
        "  • `П1` — победа 1-й команды (хозяева)\n"
        "  • `П2` — победа 2-й команды (гости)\n"
        "  • `X`  — ничья\n"
        "  • `1X` — хозяева или ничья\n"
        "  • `X2` — гости или ничья\n"
        "  • `12` — победа любой команды\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ *Важно:*\n"
        "  • Ставки только *до начала* матча\n"
        "  • Проигрыш — ставка не возвращается\n"
        "  • Выплаты в течение 24 часов\n"
        "  • PRIZMBET вправе отклонить ставку"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_advantages(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "⭐ *ПРЕИМУЩЕСТВА PRIZMBET*\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅  *Без верификации*\n"
        "    Никаких документов и паспортов\n\n"
        "🕵️  *Анонимно и без KYC*\n"
        "    Полная конфиденциальность\n\n"
        "🔓  *Без условий по обороту*\n"
        "    Выводи средства в любое время\n\n"
        "🌍  *Без гео-ограничений*\n"
        "    Доступно из любой страны\n\n"
        "₿  *Баланс в PRIZM*\n"
        "    Децентрализованная блокчейн-монета\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "🎰 /start   📋 /rules"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_mybets(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    bets = load_bets()
    my   = [b for b in bets if b.get("tg_id") == user_id]

    if not my:
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("🎰 Сделать ставку", url="https://minortermite.github.io/betprizm/"),
        ]])
        await update.message.reply_text(
            "📭 *У вас пока нет ставок*\n\nПерейдите на сайт и выберите матч!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=kb,
        )
        return

    total_amount = sum(b.get("amount", 0) for b in my)
    wins   = sum(1 for b in my if b.get("status") == "win")
    losses = sum(1 for b in my if b.get("status") == "loss")

    lines = [
        f"📋 *Ваши ставки* ({len(my)} всего)\n"
        f"💰 Поставлено: `{total_amount:.1f} PRIZM` | ✅ {wins} побед | ❌ {losses} проигрышей\n"
    ]
    for i, b in enumerate(reversed(my[-10:]), 1):
        lines.append(fmt_bet(b, i))

    await update.message.reply_text("\n\n".join(lines), parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Реферальная ссылка пользователя"""
    user = update.effective_user
    code = referral_code(user.id)
    link = f"https://t.me/PrizmBet2bot?start=ref_{code}"

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔗 Поделиться ссылкой", url=f"https://t.me/share/url?url={link}&text=Криптобукмекер+PRIZMBET"),
    ]])
    text = (
        f"🎁 *Реферальная программа*\n\n"
        f"Ваша ссылка:\n`{link}`\n\n"
        f"Приглашайте друзей и получайте бонусы!\n"
        f"Каждый приглашённый игрок — +бонус вам 🎉"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

# ══════════════════════════════════════════════════════════════
#  КОМАНДЫ — ТОЛЬКО АДМИН
# ══════════════════════════════════════════════════════════════
@smart_handler
async def cmd_bets(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    bets    = load_bets()
    pending = [b for b in bets if b.get("status") == "pending"]

    if not pending:
        await update.message.reply_text("🎯 Активных ставок нет")
        return

    total_vol = sum(b.get("amount", 0) for b in pending)
    lines = [
        f"📊 *Активных ставок: {len(pending)}*\n"
        f"💰 Общий объём: `{total_vol:.1f} PRIZM`\n"
    ]
    for i, b in enumerate(pending[-15:], 1):
        lines.append(fmt_bet(b, i))

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔄 Обновить",        callback_data="refresh_bets"),
        InlineKeyboardButton("🔍 Проверить PRIZM",  callback_data="check_prizm"),
    ], [
        InlineKeyboardButton("💰 Баланс кошелька", callback_data="check_balance"),
    ]])
    await update.message.reply_text(
        "\n\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=kb,
    )

@smart_handler
async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
        
    msg = await update.message.reply_text("⏳ _Считаю статистику из блокчейна..._", parse_mode=ParseMode.MARKDOWN)
    
    bets    = load_bets()
    total_bets   = len(bets)
    pending = sum(1 for b in bets if b.get("status") == "pending")
    wins    = sum(1 for b in bets if b.get("status") == "win")
    losses  = sum(1 for b in bets if b.get("status") == "loss")
    
    # Calculate blockchain stats (last 100 txs for speed, or more if needed)
    txs = prizm_api.get_transactions(0, 500)
    real_income = 0.0
    real_payouts = 0.0
    
    for tx in txs:
        amount = prizm_api.prizm_amount(tx)
        if tx.get("senderRS") == prizm_api.WALLET:
            real_payouts += amount
        elif tx.get("recipientRS") == prizm_api.WALLET:
            real_income += amount
            
    # Include unconfirmed balance in real_income just in case
    balance_info = prizm_api.get_balance()
    current_balance = balance_info.get("balance", 0.0) if balance_info.get("balance") is not None else 0.0
            
    profit  = real_income - real_payouts
    wr      = f"{wins / (wins + losses) * 100:.0f}%" if (wins + losses) else "—"

    text = (
        f"📊 *Статистика PRIZMBET*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎰 Всего ставок в БД: `{total_bets}`\n"
        f"⏳ Ожидают:           `{pending}`\n"
        f"✅ Выиграли:          `{wins}`\n"
        f"❌ Проиграли:         `{losses}`\n"
        f"📈 Винрейт дома:      `{wr}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📥 Входящие TX (500): `{real_income:.1f} PRIZM`\n"
        f"📤 Исходящие TX (500): `{real_payouts:.1f} PRIZM`\n"
        f"💰 Баланс кошелька:   `{current_balance:.1f} PRIZM`\n"
        f"📈 Профит (за 500 TX): `{profit:.1f} PRIZM`"
    )
    await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_win(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        await update.message.reply_text("Использование: `/win <ID_ставки>`", parse_mode=ParseMode.MARKDOWN)
        return
    bets   = load_bets()
    bet_id = ctx.args[0]
    for b in bets:
        if b.get("id") == bet_id:
            # Запросить подтверждение
            await update.message.reply_text(
                f"⚠️ *Подтвердить выигрыш?*\n\n{fmt_bet(b)}\n\n"
                f"Выплата: `{b.get('payout', 0):.1f} PRIZM`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=confirm_kb("win", bet_id),
            )
            return
    await update.message.reply_text(f"❌ Ставка `{bet_id}` не найдена", parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_loss(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not ctx.args:
        await update.message.reply_text("Использование: `/loss <ID_ставки>`", parse_mode=ParseMode.MARKDOWN)
        return
    bets   = load_bets()
    bet_id = ctx.args[0]
    for b in bets:
        if b.get("id") == bet_id:
            await update.message.reply_text(
                f"⚠️ *Подтвердить проигрыш?*\n\n{fmt_bet(b)}",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=confirm_kb("loss", bet_id),
            )
            return
    await update.message.reply_text(f"❌ Ставка `{bet_id}` не найдена", parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = await update.message.reply_text("🔍 _Запрашиваю баланс..._", parse_mode=ParseMode.MARKDOWN)
    try:
        info = prizm_api.get_balance()
        if info["balance"] is None:
            await msg.edit_text("❌ Не удалось получить баланс — все ноды недоступны.")
            return
        text = (
            f"💰 *Баланс кошелька PRIZMBET*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔑 `{info['wallet']}`\n\n"
            f"💎 Баланс:            `{info['balance']:.2f} PRIZM`\n"
            f"⏳ Неподтверждённый: `{info['unconfirmed']:.2f} PRIZM`\n\n"
            f"🌐 Нода: `{info['node']}`"
        )
        await msg.edit_text(text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")

@smart_handler
async def cmd_check_tx(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = await update.message.reply_text("🔍 _Проверяю транзакции PRIZM..._", parse_mode=ParseMode.MARKDOWN)
    try:
        await check_prizm_transactions(ctx.bot)
        await msg.edit_text("✅ Проверка завершена")
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {e}")

@smart_handler
async def cmd_broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    raw   = update.message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            "📢 *Рассылка всем пользователям*\n\n"
            "Использование:\n`/broadcast <текст>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    text  = parts[1].strip()
    users = get_all_users()
    if not users:
        await update.message.reply_text("❌ Нет пользователей в базе")
        return

    total  = len(users)
    sent   = failed = 0
    msg    = await update.message.reply_text(
        f"📤 *Рассылка запущена*\n\n{progress_bar(0, total)}\n0 / {total}",
        parse_mode=ParseMode.MARKDOWN,
    )
    for i, uid_str in enumerate(users.keys(), 1):
        try:
            uid = int(uid_str)
            if uid == ADMIN_ID:
                continue
            await ctx.bot.send_message(chat_id=uid, text=text)
            sent += 1
        except Exception as e:
            log.warning(f"broadcast → {uid_str}: {e}")
            failed += 1
        # Throttle anti-flood
        await asyncio.sleep(BROADCAST_DELAY)
        # Обновлять прогресс каждые N шагов
        if i % PROGRESS_STEP == 0 or i == total:
            try:
                await msg.edit_text(
                    f"📤 *Рассылка...*\n\n{progress_bar(i, total)}\n{i} / {total}",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception:
                pass

    await msg.edit_text(
        f"✅ *Рассылка завершена*\n\n"
        f"{progress_bar(total, total)}\n\n"
        f"✅ Доставлено: `{sent}`\n"
        f"❌ Ошибок:     `{failed}`",
        parse_mode=ParseMode.MARKDOWN,
    )

@smart_handler
async def cmd_group_post(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    raw   = update.message.text or ""
    parts = raw.split(None, 1)
    if len(parts) < 2 or not parts[1].strip():
        await update.message.reply_text(
            "📤 *Пост во все группы*\n\n"
            "Использование:\n`/group_post <текст>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    text      = parts[1].strip()
    group_ids = [g for g in get_notify_ids() if g != ADMIN_ID]
    if not group_ids:
        await update.message.reply_text("❌ Нет подключённых групп")
        return

    sent = failed = 0
    msg  = await update.message.reply_text(
        f"📤 _Отправляю в {len(group_ids)} групп..._",
        parse_mode=ParseMode.MARKDOWN,
    )
    for gid in group_ids:
        try:
            await ctx.bot.send_message(chat_id=gid, text=text)
            sent += 1
        except Exception as e:
            log.warning(f"group_post → {gid}: {e}")
            failed += 1
        await asyncio.sleep(BROADCAST_DELAY)

    await msg.edit_text(
        f"✅ *Посты отправлены*\n\n"
        f"✅ Успешно: `{sent}`\n"
        f"❌ Ошибок:  `{failed}`",
        parse_mode=ParseMode.MARKDOWN,
    )

@smart_handler
async def cmd_setgroup(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    cfg    = load_config()
    groups = cfg.get("groups", {})

    if not ctx.args:
        if not groups:
            await update.message.reply_text(
                "📢 *Группы/каналы*\n\nПодключено: 0\n\n"
                "Как добавить:\n"
                "1. Добавь бота в группу администратором\n"
                "2. `/chatid` — в группе\n"
                "3. `/setgroup <id>` — боту в ЛС",
                parse_mode=ParseMode.MARKDOWN,
            )
        else:
            lines = [f"📢 *Группы ({len(groups)}):*\n"]
            for gid, data in groups.items():
                lines.append(f"• `{gid}` — {data.get('name','?')} | {data.get('joined','')}")
            lines.append("\n`/setgroup remove <id>` — удалить")
            await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)
        return

    if ctx.args[0].lower() == "remove":
        if len(ctx.args) < 2:
            await update.message.reply_text("❌ `/setgroup remove <chat_id>`", parse_mode=ParseMode.MARKDOWN)
            return
        try:
            gid = int(ctx.args[1])
            if str(gid) in groups:
                del groups[str(gid)]
                cfg["groups"] = groups
                save_config(cfg)
                await update.message.reply_text(f"✅ Группа `{gid}` удалена", parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("❌ Группа не найдена", parse_mode=ParseMode.MARKDOWN)
        except ValueError:
            await update.message.reply_text("❌ Неверный ID", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        gid = int(ctx.args[0])
        if str(gid) in groups:
            await update.message.reply_text(f"⚠️ Группа `{gid}` уже добавлена", parse_mode=ParseMode.MARKDOWN)
            return
        track_group(gid)
        await update.message.reply_text(
            f"✅ Группа добавлена: `{gid}`\nВсего: {len(groups) + 1}",
            parse_mode=ParseMode.MARKDOWN,
        )
        try:
            await ctx.bot.send_message(
                chat_id=gid,
                text="✅ *PRIZMBET* — уведомления подключены!",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            await update.message.reply_text(f"⚠️ Тест не прошёл: {e}", parse_mode=ParseMode.MARKDOWN)
    except ValueError:
        await update.message.reply_text("❌ Пример: `/setgroup -1001234567890`", parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_chatid(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    await update.message.reply_text(
        f"💬 *Chat ID:* `{chat.id}`\n"
        f"Тип: `{chat.type}`\n"
        f"Название: `{chat.title or chat.username or '—'}`\n\n"
        f"Используй: `/setgroup {chat.id}`",
        parse_mode=ParseMode.MARKDOWN,
    )

@smart_handler
async def cmd_list_groups(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    groups = get_all_groups()
    if not groups:
        await update.message.reply_text(
            "❌ Нет подключённых групп\n\n"
            "1️⃣ `/chatid` — в группе\n"
            "2️⃣ `/setgroup <id>` — боту",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    lines = [f"📋 *Группы ({len(groups)}):*\n"]
    for i, (gid, data) in enumerate(groups.items(), 1):
        lines.append(f"{i}. `{gid}`\n   {data.get('name','?')} | с {data.get('joined','')}")
    lines.append("\n📤 `/group_post <текст>` | ❌ `/setgroup remove <id>`")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

@smart_handler
async def cmd_stats_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    users  = get_all_users()
    groups = get_all_groups()
    bets   = load_bets()
    active = sum(1 for b in bets if b.get("status") == "pending")
    text = (
        f"📊 *PRIZMBET Статистика*\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Пользователей: `{len(users)}`\n"
        f"👫 Групп/каналов: `{len(groups)}`\n\n"
        f"🎰 Всего ставок:  `{len(bets)}`\n"
        f"   ⏳ Активных:   `{active}`\n"
        f"   ✅ Завершённых:`{len(bets) - active}`\n\n"
        f"💾 БД: ~{(len(str(users)) + len(str(groups))) // 1024 + 1} KB"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

# ══════════════════════════════════════════════════════════════
#  INLINE MODE — @bot поиск матча в любом чате
# ══════════════════════════════════════════════════════════════
async def inline_query_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query   = (update.inline_query.query or "").lower().strip()
    matches = load_matches()
    results = []

    for mid, m in list(matches.items())[:50]:
        t1 = m.get("team1", "")
        t2 = m.get("team2", "")
        if query and query not in f"{t1} {t2}".lower():
            continue
        league = m.get("league", "")
        date   = m.get("date", "")
        o1     = m.get("odds_1", "?")
        ox     = m.get("odds_x", "?")
        o2     = m.get("odds_2", "?")

        title   = f"{t1} — {t2}"
        desc    = f"{league} | {date}"
        content = (
            f"🎰 *{t1} — {t2}*\n"
            f"🏆 {league}\n"
            f"📅 {date}\n\n"
            f"П1: `×{o1}` | X: `×{ox}` | П2: `×{o2}`\n\n"
            f"🔗 [Сделать ставку](https://minortermite.github.io/betprizm/)"
        )
        results.append(InlineQueryResultArticle(
            id=mid,
            title=title,
            description=desc,
            input_message_content=InputTextMessageContent(
                content,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            ),
            thumb_url="https://i.imgur.com/4M7IWwP.png",  # иконка PRIZM
        ))
        if len(results) >= 20:
            break

    await update.inline_query.answer(results, cache_time=30, is_personal=False)

# ══════════════════════════════════════════════════════════════
#  CALLBACK HANDLER (Inline кнопки)
# ══════════════════════════════════════════════════════════════
async def callback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data or ""

    # ── Win/Loss прямо в уведомлении о ставке ──────────────
    if data.startswith("win:") or data.startswith("loss:"):
        if update.effective_user.id != ADMIN_ID:
            await q.answer("⛔ Только для администратора", show_alert=True)
            return
        action, bet_id = data.split(":", 1)
        # Показываем confirm-кнопки
        bets = load_bets()
        for b in bets:
            if b.get("id") == bet_id:
                label = "выигрыш" if action == "win" else "проигрыш"
                await q.message.edit_reply_markup(reply_markup=confirm_kb(action, bet_id))
                await q.answer(f"Подтвердите {label}!")
                return

    # ── Подтверждение win/loss ──────────────────────────────
    if data.startswith("confirm_win:") or data.startswith("confirm_loss:"):
        if update.effective_user.id != ADMIN_ID:
            return
        _, rest   = data.split("_", 1)
        action, bet_id = rest.split(":", 1)
        bets = load_bets()
        for b in bets:
            if b.get("id") == bet_id:
                b["status"] = action
                save_bets(bets)
                emoji = "✅" if action == "win" else "❌"
                label = "ВЫИГРЫШ" if action == "win" else "ПРОИГРЫШ"
                await q.message.edit_text(
                    f"{emoji} *Ставка {bet_id} — {label}*\n\n{fmt_bet(b)}",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=None,
                )
                # Уведомить игрока
                tg_id = b.get("tg_id")
                if tg_id:
                    try:
                        if action == "win":
                            msg = (
                                f"🎉 *Ваша ставка выиграла!*\n\n{fmt_bet(b)}\n\n"
                                f"💸 Выплата `{b.get('payout',0):.1f} PRIZM` будет отправлена на кошелёк."
                            )
                        else:
                            msg = f"😔 *Ставка не сыграла*\n\n{fmt_bet(b)}\n\nУдачи в следующий раз!"
                        await ctx.bot.send_message(
                            chat_id=int(tg_id), text=msg, parse_mode=ParseMode.MARKDOWN
                        )
                    except Exception:
                        pass
                return

    # ── Отмена ─────────────────────────────────────────────
    if data == "cancel":
        await q.message.edit_reply_markup(reply_markup=bet_notify_kb(
            q.message.text.split("BET")[1].split()[0] if "BET" in (q.message.text or "") else "?"
        ))
        await q.answer("Отменено")
        return

    # ── Обновить список ставок ──────────────────────────────
    if data == "refresh_bets":
        await cmd_bets(update, ctx)

    # ── Проверить PRIZM ─────────────────────────────────────
    elif data == "check_prizm":
        await q.message.reply_text("🔍 _Проверяю транзакции..._", parse_mode=ParseMode.MARKDOWN)
        await check_prizm_transactions(ctx.bot)

    # ── Баланс ─────────────────────────────────────────────
    elif data == "check_balance":
        try:
            info = prizm_api.get_balance()
            if info["balance"] is None:
                await q.message.reply_text("❌ Все ноды недоступны")
            else:
                await q.message.reply_text(
                    f"💰 *Баланс:* `{info['balance']:.2f} PRIZM`\n"
                    f"⏳ Неподтверждённый: `{info['unconfirmed']:.2f} PRIZM`",
                    parse_mode=ParseMode.MARKDOWN,
                )
        except Exception as e:
            await q.message.reply_text(f"❌ Ошибка: {e}")

# ══════════════════════════════════════════════════════════════
#  ТЕКСТОВЫЕ КНОПКИ (reply keyboard)
# ══════════════════════════════════════════════════════════════
async def handle_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    dispatch = {
        "🎰 Сделать ставку":    cmd_start,
        "📋 Мои ставки":        cmd_mybets,
        "📖 Правила":           cmd_rules,
        "⭐ Преимущества":      cmd_advantages,
        "📊 Ставки (Админ)":    cmd_bets,
        "📈 Статистика":        cmd_stats,
        "💰 Баланс":            cmd_balance,
        "📢 Группы":            cmd_setgroup,
    }
    handler = dispatch.get(text)
    if handler:
        await handler(update, ctx)

# ══════════════════════════════════════════════════════════════
#  ПРОВЕРКА PRIZM ТРАНЗАКЦИЙ
# ══════════════════════════════════════════════════════════════
async def check_prizm_transactions(bot=None):
    log.info("Checking PRIZM transactions...")
    new_txs = prizm_api.get_new_transactions()
    if not new_txs:
        log.info("No new transactions")
        return

    bets    = load_bets()
    matches = load_matches()
    bet_ids = {b.get("tx_id") for b in bets}
    added   = 0

    for tx in new_txs:
        tx_id = tx.get("transaction", "")
        if tx_id in bet_ids:
            continue
            
        amount       = prizm_api.prizm_amount(tx)
        
        # Исходящая транзакция (Выплата)
        if tx.get("senderRS") == WALLET:
            recipient = tx.get("recipientRS", "Unknown")
            if amount > 1.0: # Игнорируем тестовые копейки
                log.info(f"Outgoing TX (Payout): {amount} PRIZM to {recipient}")
                
                # Уведомляем админа и группы о выплате
                if bot:
                    payout_text = (
                        f"Очередные выплаты! {datetime.now().strftime('%d %B %Yг.')}\n\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 `...{recipient[-10:]}`\n"
                        f"💰 `{amount:.2f} PRIZM`\n"
                        f"🔗 `{tx_id[:18]}...`\n\n"
                        f"🟣 PRIZMBET — когда решает коэффициент"
                    )
                    for cid in get_notify_ids():
                        try:
                            await bot.send_message(
                                chat_id=cid,
                                text=payout_text,
                                parse_mode=ParseMode.MARKDOWN,
                            )
                        except Exception as e:
                            log.error(f"Notify payout {cid}: {e}")
            continue



        amount       = prizm_api.prizm_amount(tx)
        sender       = prizm_api.get_sender_address(tx)
        comment      = prizm_api.get_message(tx)
        parsed       = prizm_api.parse_bet_comment(comment)
        is_encrypted = prizm_api.has_encrypted_message(tx)

        if not parsed:
            log.info(f"TX {tx_id[:12]}: unrecognized/encrypted={is_encrypted}")
            
            # Пропускаем спам-транзакции и транзакции без распознанного матча/шифрования < 1500 (минимальная ставка)
            if amount < 1.0:
                 log.info(f"Ignoring tiny unrecognized TX: {amount} PRIZM")
                 continue
                 
            match_id = "unknown"; bet_type = "unknown"
            match    = {"team1": "Неизвестно", "team2": "Неизвестно"}
            coef = payout = 0.0
        else:
            match_id = parsed["match_id"]; bet_type = parsed["bet_type"]
            match    = matches.get(match_id, {})
            coef     = prizm_api.get_coef(match, bet_type)
            payout   = round(amount * coef, 2) if coef > 0 else 0

        bet = {
            "id":       f"BET{int(time.time())}{added}",
            "tx_id":    tx_id,
            "match_id": match_id,
            "team1":    match.get("team1", "Неизвестно"),
            "team2":    match.get("team2", "Неизвестно"),
            "league":   match.get("league", ""),
            "bet_type": bet_type,
            "coef":     coef,
            "amount":   amount,
            "payout":   payout,
            "sender":   sender,
            "tg_id":    "",
            "status":   "pending",
            "time":     datetime.now().strftime("%d.%m.%Y %H:%M"),
        }
        bets.append(bet)
        bet_ids.add(tx_id)
        added += 1
        log.info(f"New bet: {bet['id']} {bet['team1']} {bet_type} {amount} PRIZM")

        if bot:
            header = "✅ *Ставка принята*"
            if not parsed:
                header += " _(зашифровано)_" if is_encrypted else " _(не распознано)_"



            match_line = (
                f"🏆 {bet.get('league','')}\n"
                f"📅 {match.get('date', '—')}\n"
                f"⚽ {bet['team1']} — {bet['team2']}\n"
                f"🎯 Тип: `{bet['bet_type']}`  Коэф: `×{bet['coef']}`\n\n"
            ) if parsed else ""

            bet_text = (
                f"{header}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 `{bet['sender']}`\n"
                f"💰 `{bet['amount']:.2f} PRIZM`\n"
                f"🔗 `{bet['tx_id'][:18]}...`\n\n"
                f"{match_line}"
                f"🆔 `{bet['id']}`\n\n"
                f"🟣 PRIZMBET — когда решает коэффициент"
            )
            # Кнопки Win/Loss — только в ЛС к админу
            for cid in get_notify_ids():
                try:
                    kb = bet_notify_kb(bet["id"]) if cid == ADMIN_ID else None
                    await bot.send_message(
                        chat_id=cid,
                        text=bet_text,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=kb,
                    )
                    log.info(f"Notified {cid}")
                except Exception as e:
                    log.error(f"Notify {cid}: {e}")

    if added:
        save_bets(bets)
        log.info(f"Saved {added} bets")


async def poll_transactions_job(context: ContextTypes.DEFAULT_TYPE):
    """Фоновая задача для проверки новых транзакций"""
    try:
        await check_prizm_transactions(context.bot)
    except Exception as e:
        log.error(f"Error in poll_transactions_job: {e}")

# ══════════════════════════════════════════════════════════════
#  POST INIT — регистрация команд в меню Telegram
# ══════════════════════════════════════════════════════════════
async def post_init(app: Application):
    """Вызывается после запуска. Регистрирует команды в меню /"""
    user_cmds = [
        BotCommand("start",      "🏠 Главное меню"),
        BotCommand("mybets",     "📋 Мои ставки"),
        BotCommand("referral",   "🎁 Реферальная ссылка"),
        BotCommand("rules",      "📖 Правила"),
        BotCommand("advantages", "⭐ Преимущества"),
        BotCommand("help",       "❓ Справка"),
    ]
    admin_cmds = user_cmds + [
        BotCommand("bets",        "📊 Все активные ставки"),
        BotCommand("stats",       "📈 Статистика"),
        BotCommand("stats_users", "👥 Статистика пользователей"),
        BotCommand("check_tx",    "🔍 Проверить транзакции"),
        BotCommand("balance",     "💰 Баланс кошелька"),
        BotCommand("broadcast",   "📢 Рассылка всем"),
        BotCommand("group_post",  "📤 Пост во все группы"),
        BotCommand("list_groups", "👫 Список групп"),
        BotCommand("setgroup",    "⚙️ Управление группами"),
        BotCommand("chatid",      "💬 ID текущего чата"),
    ]
    # Установить команды для обычных пользователей
    await app.bot.set_my_commands(user_cmds)
    # Установить расширенное меню для админа
    try:
        await app.bot.set_my_commands(
            admin_cmds,
            scope=BotCommandScopeChat(chat_id=ADMIN_ID),
        )
    except Exception as e:
        log.warning(f"Admin commands scope error: {e}")
        
    # Запускаем фоновую проверку транзакций (каждые 60 секунд)
    if app.job_queue:
        app.job_queue.run_repeating(poll_transactions_job, interval=60, first=10)
        log.info("✅ Background transaction polling started (every 60s)")
    else:
        log.error("❌ JobQueue is disabled! Transactions won't be polled automatically.")

    log.info("✅ Bot commands registered in Telegram menu")

# ══════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════
def main():
    if not BOT_TOKEN:
        log.critical("BOT_TOKEN не задан!")
        sys.exit(1)

    log.info("Starting PRIZMBET Bot v3.0...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)   # регистрация меню после старта
        .build()
    )

    # Публичные команды
    app.add_handler(CommandHandler("start",       cmd_start))
    app.add_handler(CommandHandler("help",        cmd_help))
    app.add_handler(CommandHandler("rules",       cmd_rules))
    app.add_handler(CommandHandler("advantages",  cmd_advantages))
    app.add_handler(CommandHandler("mybets",      cmd_mybets))
    app.add_handler(CommandHandler("referral",    cmd_referral))
    app.add_handler(CommandHandler("chatid",      cmd_chatid))

    # Команды только для админа
    app.add_handler(CommandHandler("bets",        cmd_bets))
    app.add_handler(CommandHandler("stats",       cmd_stats))
    app.add_handler(CommandHandler("stats_users", cmd_stats_users))
    app.add_handler(CommandHandler("win",         cmd_win))
    app.add_handler(CommandHandler("loss",        cmd_loss))
    app.add_handler(CommandHandler("balance",     cmd_balance))
    app.add_handler(CommandHandler("check_tx",    cmd_check_tx))
    app.add_handler(CommandHandler("broadcast",   cmd_broadcast))
    app.add_handler(CommandHandler("group_post",  cmd_group_post))
    app.add_handler(CommandHandler("list_groups", cmd_list_groups))
    app.add_handler(CommandHandler("setgroup",    cmd_setgroup))

    # Inline mode (поиск матчей через @bot)
    app.add_handler(InlineQueryHandler(inline_query_handler))

    # Callback (inline кнопки)
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Reply keyboard (текстовые кнопки)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    log.info(f"Admin: {ADMIN_ID} | Wallet: {WALLET}")
    log.info(f"Notify IDs: {get_notify_ids()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
