#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Инспектирует реальный DOM Winline для обновления селекторов"""
import json
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

INSPECT_JS = """
() => {
    const r = {};
    
    // Ссылки на события
    const links = document.querySelectorAll('a[href*="/event/"]');
    r.eventLinksCount = links.length;
    
    if (links.length > 0) {
        r.firstHref = links[0].href;
        
        // DOM цепочка от первой ссылки вверх
        let el = links[0];
        const chain = [];
        for (let i = 0; i < 10 && el; i++) {
            chain.push(el.tagName + ' :: ' + el.className.substring(0,100));
            el = el.parentElement;
        }
        r.domChain = chain;
        
        // Ищем карточку с кнопками коэффициентов
        let card = links[0];
        for (let i = 0; i < 8 && card; i++) {
            const btns = card.querySelectorAll('button');
            if (btns.length >= 2) {
                r.cardTag = card.tagName;
                r.cardClass = card.className.substring(0,150);
                r.btnInfo = Array.from(btns).slice(0,6).map(function(b) {
                    return {cls: b.className.substring(0,100), txt: (b.innerText||'').trim().substring(0,15)};
                });
                r.cardTextSample = (card.innerText||'').substring(0,250);
                break;
            }
            card = card.parentElement;
        }
    }
    
    // Все кнопки с числами (коэффициентами)
    const coefBtns = [];
    document.querySelectorAll('button').forEach(function(b) {
        const t = (b.innerText||'').trim();
        if (/^\\d+\\.\\d{1,2}$/.test(t)) {
            coefBtns.push({cls: b.className.substring(0,100), val: t});
        }
    });
    r.coefButtons = coefBtns.slice(0, 12);
    
    // Элементы с датой/временем
    const dateEls = [];
    document.querySelectorAll('[class*="date"], [class*="time"], [class*="start"], [class*="schedule"]').forEach(function(el) {
        const t = (el.innerText||'').trim();
        if (t && t.length < 30) {
            dateEls.push({cls: el.className.substring(0,80), txt: t.substring(0,25)});
        }
    });
    r.dateElements = dateEls.slice(0, 10);
    
    // Блоки турниров
    const tournaments = document.querySelectorAll('[class*="tournament"]');
    r.tournamentCount = tournaments.length;
    if (tournaments.length > 0) {
        r.firstTournamentClass = tournaments[0].className.substring(0,150);
        r.firstTournamentText = (tournaments[0].innerText||'').substring(0,100);
    }
    
    return r;
}
"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
    )
    ctx = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        locale="ru-RU",
        viewport={"width": 1600, "height": 900}
    )
    page = ctx.new_page()
    print("Загрузка winline.ru/stavki/sport/futbol ...")
    page.goto("https://winline.ru/stavki/sport/futbol", timeout=40000, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    
    # Скроллим
    for i in range(8):
        page.evaluate("window.scrollBy(0, 500)")
        page.wait_for_timeout(400)
    page.wait_for_timeout(1000)
    
    result = page.evaluate(INSPECT_JS)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    browser.close()
