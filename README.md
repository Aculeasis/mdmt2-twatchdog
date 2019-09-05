# TWatchdog plugin for mdmTerminal2
Проверяет terminal и выполняет некоторые действия если он перестал отвечать.

# Установка
```bash
cd mdmTerminal2/src/plugins
git clone https://github.com/Aculeasis/mdmt2-twatchdog
```
И перезапустить терминал.

## Настройка
Настройки хранятся в `mdmTerminal2/src/data/twatchdog.json`, файл будет создан при первом запуске:
```json
{
    "interval": 30,
    "actions": ["log", "notify" ],
    "custom_cmd": ""
}
```
 - **interval**: Интервал проверки терминала, в минутах, если меньше 1 периодическая проверка будет отключена. Также можно активировать командой `twatchdog`.
 - **actions**: Список действий при зависании терминала, порядок выполнения `log, notify, custom, {stop, reset}`,
 если пуст то плагин не запустится:
   - **log**: Залоггировать ошибку.
   - **notify**: Отправить уведомление `twatchdog`.
   - **custom**: Выполнить произвольную shell-команду из **custom_cmd**.
   - **reset**: "Мягкий" перезапуск терминала. Будет проигнорированно если есть **stop**.
   - **stop**: Завершить работу. Терминал будет запущен вновь (если работает в качестве сервиса).
- **custom_cmd**: Произвольная shell-команда. Например, `ls -lh`

# Ссылки
- [mdmTerminal2](https://github.com/Aculeasis/mdmTerminal2)
