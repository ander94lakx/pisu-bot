# `pisu-bot`

Telegram bot that scraps estate agencies and looks for ""cheap"" flats.

- **`pisu_bot.py`**: The bot itself.
- **`channel_updater.py`**: Updates a separate channel that notifies about new flats periodically.
- **`scrap.py`**: The differens scrapping methods.
''

Uses [Selenium](https://www.selenium.dev/) for web scrapping, [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) as weapper for Telegram's API and [schedule](https://schedule.readthedocs.io/en/stable/) for automatically update a telegram channel with info.

The bot scraps in Idealista and Fotocasa and implements commands to search in both or separately
