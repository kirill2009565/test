# bot.py - Telegram бот с S_Taper 0.8.4.0
import telebot
import re
import threading
import schedule
import time
from datetime import datetime, timedelta
import sqlite3

# Фикс для Python 3.12
def adapt_datetime(dt):
    return dt.isoformat()

def convert_datetime(b):
    return datetime.fromisoformat(b.decode())

sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

# ==================== ИМПОРТ S_Taper 0.8.4.0 ====================
from s_taper import Taper
import s_taper as s_taper

print("Доступные атрибуты в S_Taper:", [x for x in dir(s_taper) if not x.startswith('_')])

try:
    from S_Taper import Model, CharField, TextField, IntField, DateTimeField, BooleanField

    print("✅ Импорт из S_Taper (основной модуль)")
except ImportError:
    try:
        from S_Taper.modules import Model, CharField, TextField, IntField, DateTimeField, BooleanField

        print("✅ Импорт из S_Taper.modules")
    except ImportError:
        try:
            Model = s_taper.Model
            CharField = s_taper.CharField
            TextField = s_taper.TextField
            IntField = s_taper.IntField
            DateTimeField = s_taper.DateTimeField
            BooleanField = s_taper.BooleanField
            print("✅ Найдены атрибуты в S_Taper")
        except AttributeError:
            print("❌ Не могу найти Model в S_Taper")
            import sqlite3

            USE_SIMPLE_SQLITE = True
        else:
            USE_SIMPLE_SQLITE = False
    else:
        USE_SIMPLE_SQLITE = False
else:
    USE_SIMPLE_SQLITE = False

TOKEN = "8354223369:AAGO8lIfocWo4yFFuQvFLxa-RowsdBVozcE"
bot = telebot.TeleBot(TOKEN)

# ==================== БАЗА ДАННЫХ ====================
if not USE_SIMPLE_SQLITE:
    print("Используем S_Taper...")
    db = Taper('bot_database.db')
    if hasattr(Model, 'set_db'):
        Model.set_db(db)
        print("✅ Model.set_db() вызван")


    class User(Model):
        user_id = IntField(primary_key=True)
        first_name = CharField(max_length=100)
        username = CharField(max_length=100, null=True)
        registration_date = DateTimeField(default=datetime.now)


    class FAQ(Model):
        question = CharField(max_length=500)
        answer = TextField()
        usage_count = IntField(default=0)


    class Reminder(Model):
        user_id = IntField()
        text = TextField()
        remind_time = DateTimeField()
        created = DateTimeField(default=datetime.now)
        is_sent = BooleanField(default=False)


    try:
        db.create_all()
        print("✅ Таблицы созданы через S_Taper")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        USE_SIMPLE_SQLITE = True
else:
    print("Используем простой SQLite3...")
    import sqlite3


    def init_simple_db():
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                username TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT,
                remind_time TIMESTAMP,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_sent BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()


    init_simple_db()
    print("✅ Таблицы созданы через SQLite3")


# ==================== ФУНКЦИИ РАБОТЫ С ДАННЫМИ ====================
def add_user(user_id, first_name, username):
    if not USE_SIMPLE_SQLITE:
        user = User(user_id=user_id, first_name=first_name, username=username)
        user.save()
    else:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, first_name, username)
            VALUES (?, ?, ?)
        ''', (user_id, first_name, username))
        conn.commit()
        conn.close()


def init_faq():
    faq_data = [
    ("контакт телефон", "📞 Телефон: +7 (924) 539-22-36")
]

    if not USE_SIMPLE_SQLITE:
        for question, answer in faq_data:
            existing = FAQ.filter(question=question).first()
            if not existing:
                faq = FAQ(question=question, answer=answer)
                faq.save()
    else:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        for question, answer in faq_data:
            cursor.execute('SELECT id FROM faq WHERE question = ?', (question,))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO faq (question, answer) VALUES (?, ?)',
                               (question, answer))
        conn.commit()
        conn.close()
    print("✅ FAQ инициализирован")


def find_faq_answer(user_text):
    user_text = user_text.lower().strip()
    if not USE_SIMPLE_SQLITE:
        all_faq = FAQ.filter_all()
        best_answer = None
        best_score = 0
        for faq in all_faq:
            score = 0
            keywords = faq.question.split()
            for keyword in keywords:
                if keyword in user_text:
                    score += 1
            if score > best_score:
                best_score = score
                best_answer = faq
        if best_answer and best_score >= 1:
            best_answer.usage_count += 1
            best_answer.save()
            return best_answer.answer
        return None
    else:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('SELECT id, question, answer FROM faq')
        all_faq = cursor.fetchall()
        best_answer = None
        best_score = 0
        best_id = None
        for faq_id, question, answer in all_faq:
            score = 0
            keywords = question.split()
            for keyword in keywords:
                if keyword in user_text:
                    score += 1
            if score > best_score:
                best_score = score
                best_answer = answer
                best_id = faq_id
        if best_answer and best_score >= 1 and best_id:
            cursor.execute('UPDATE faq SET usage_count = usage_count + 1 WHERE id = ?', (best_id,))
            conn.commit()
        conn.close()
        return best_answer


def add_reminder(user_id, text, minutes):
    remind_time = datetime.now() + timedelta(minutes=minutes)
    if not USE_SIMPLE_SQLITE:
        reminder = Reminder(user_id=user_id, text=text, remind_time=remind_time)
        reminder.save()
    else:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reminders (user_id, text, remind_time)
            VALUES (?, ?, ?)
        ''', (user_id, text, remind_time))
        conn.commit()
        conn.close()
    return True


def check_reminders():
    now = datetime.now()
    if not USE_SIMPLE_SQLITE:
        reminders = Reminder.filter_all()
        sent_count = 0
        for reminder in reminders:
            if reminder.remind_time <= now and not reminder.is_sent:
                try:
                    bot.send_message(reminder.user_id, f"🔔 Напоминание: {reminder.text}")
                    reminder.is_sent = True
                    reminder.save()
                    sent_count += 1
                except Exception as e:
                    print(f"Ошибка отправки: {e}")
        return sent_count
    else:
        conn = sqlite3.connect('bot_database.db', check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute('''
                    SELECT id, user_id, text FROM reminders 
                    WHERE remind_time <= ? AND is_sent = 0
                ''', (now,))
        reminders = cursor.fetchall()
        sent_count = 0
        for reminder_id, user_id, text in reminders:
            try:
                bot.send_message(user_id, f"🔔 Напоминание: {text}")
                cursor.execute('UPDATE reminders SET is_sent = 1 WHERE id = ?', (reminder_id,))
                sent_count += 1
            except Exception as e:
                print(f"Ошибка отправки: {e}")
        conn.commit()
        conn.close()
        return sent_count


# ==================== ОБРАБОТЧИКИ КОМАНД ====================
@bot.message_handler(commands=['start'])
def handle_start(message):
    add_user(message.from_user.id, message.from_user.first_name, message.from_user.username)
    bot.reply_to(message, f"👋 Привет, {message.from_user.first_name}!\n/help - справка")


@bot.message_handler(commands=['help'])
def handle_help(message):
    help_text = """/start - Начать
/help - Справка
/remind [текст] через [N] минут

"""
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['remind'])
def handle_remind(message):
    text = message.text.lower()
    if "через" in text and "минут" in text:
        try:
            parts = text.split("через")
            reminder_text = parts[0].replace("/remind", "").strip()
            import re
            match = re.search(r'(\d+)\s*минут', parts[1])
            if match:
                minutes = int(match.group(1))
                add_reminder(message.from_user.id, reminder_text, minutes)
                bot.reply_to(message, f"✅ Напоминание через {minutes} мин.")
                return
        except:
            pass
    bot.reply_to(message, "❌ /remind [текст] через [N] минут")


@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    if message.text.startswith('/'):
        return
    answer = find_faq_answer(message.text)
    if answer:
        bot.reply_to(message, answer)
    else:
        bot.reply_to(message, "🤔 Не понял. Спроси про время работы или контакты")


# ==================== ЗАПУСК ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Запуск бота")
    print("=" * 50)
    init_faq()


    def scheduler():
        schedule.every(1).minutes.do(check_reminders)
        while True:
            schedule.run_pending()
            time.sleep(1)


    threading.Thread(target=scheduler, daemon=True).start()
    print("✅ Планировщик запущен")
    print("\n✅ Бот готов!")
    print("=" * 50)

    try:
        bot.polling(none_stop=True)
    except KeyboardInterrupt:
        print("\n🛑 Бот остановлен")