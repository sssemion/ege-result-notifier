# [@EgeResultNotifierBot](https://t.me/EgeResultNotifierBot)
Телеграм-бот, уведомляющий о публикации результатов ЕГЭ.
Все данные бот получает с [официального портала ЕГЭ](http://checkege.rustest.ru)

----
Для запуска бота локально необходимо:
+ Создать в корне проекта файл `.env` и заполнить следдующими данными:
```CHECK_EGE_EXAM_URL="http://checkege.rustest.ru/api/exam"
CHECK_EGE_CAPTCHA_URL="http://checkege.rustest.ru/api/captcha"
CHECK_EGE_LOGIN_URL="http://checkege.rustest.ru/api/participant/login"

DB_FILENAME="data/db.sqlite"
BOT_API_TOKEN="<YOUR BOT API TOKEN>"

USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
ESSAY_ID="178"
```
+ Запустить файл main.py