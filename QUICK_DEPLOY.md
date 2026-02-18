# Быстрый деплой PRIZMBET на GitHub Pages

## Два способа:

---

## 1. БЫСТРО (5 минут)

```
1. Создать репозиторий: https://github.com/new -> betprizm -> Public -> Create
2. Загрузить код:
   git remote add origin https://github.com/YOUR_USERNAME/betprizm.git
   git push -u origin master
3. Включить GitHub Pages: Settings -> Pages -> master -> Save
4. Готово! Сайт: https://YOUR_USERNAME.github.io/betprizm/
```

---

## 2. С АВТООБНОВЛЕНИЕМ (данные обновляются каждые 2 часа)

GitHub Actions уже настроен! После пуша он автоматически:
- Парсит матчи с Winline + Marathon (Playwright)
- Обновляет matches.json
- Загружает в Google Sheets (если есть credentials)
- Делает commit + push -> сайт обновляется

### Добавить Google Sheets secret:
```
Settings -> Secrets -> Actions -> New repository secret
Name: GOOGLE_CREDENTIALS_JSON
Value: содержимое credentials.json
```

---

## Проверка

1. **Сайт**: `https://minortermite.github.io/betprizm/`
2. **Winline**: `https://minortermite.github.io/betprizm/winline.html`
3. **Marathon**: `https://minortermite.github.io/betprizm/marathon.html`
4. **Fonbet**: `https://minortermite.github.io/betprizm/fonbet.html`
5. **Actions**: GitHub -> Actions -> зелёные галочки

---

## Проблемы?

**Матчи не грузятся:** F12 -> Console -> посмотреть ошибки
**Actions не работает:** Settings -> Actions -> "Allow all actions"
**Sheets не обновляется:** Проверьте secret GOOGLE_CREDENTIALS_JSON

---

## Подробнее

См. файл: **DEPLOY_INSTRUCTIONS.md**

---

## Контакты

- Telegram: https://t.me/+PMrQ9Nbzu08wYmI0
- Кошелек: PRIZM-4N7T-L2A7-RQZA-5BETW
- Сайт: https://minortermite.github.io/betprizm/
