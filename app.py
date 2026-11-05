import json
import base64
import hmac
import hashlib
import secrets
import random
import re
import time
import uuid
from pathlib import Path

import requests
import streamlit as st
from order_manager import OrderManager, JournalError

st.set_page_config(page_title="Образы — исследование себя", page_icon="🌿", layout="wide")

# Временная диагностика: доступна только при включённом тестовом режиме.
if st.secrets.get("TEST_FAILURE_MODE", False):
    with st.sidebar.expander("🔐 Проверка шифрования"):
        if st.button("Проверить ключ Fernet", key="crypto_check"):
            try:
                from result_crypto import encrypt_result, decrypt_result
                key = str(st.secrets["result_encryption"]["key"])
                sample = "Тест шифрования: Образы 🌿"
                token = encrypt_result(sample, key)
                if decrypt_result(token, key) != sample:
                    raise RuntimeError("Текст не совпал")
                st.success("Шифрование: OK")
            except Exception:
                st.error("Шифрование: ошибка. Проверьте ключ и настройки.")

        if st.button("Проверить запрет повторной генерации (без ИИ)", key="generation_replay_check"):
            try:
                manager = OrderManager.from_streamlit_secrets()
                order_id = st.session_state.get("order_id")
                secret = st.session_state.get("order_recovery_secret")
                if not order_id or not secret:
                    st.warning("Откройте исследование с заказом в текущей сессии.")
                else:
                    access_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
                    response = manager.claim_generation(order_id, "profile", access_hash, str(uuid.uuid4()))
                    if response.get("status") == "completed":
                        st.success("Повторная генерация заблокирована сервером. ИИ не вызывался.")
                    elif response.get("status") == "processing":
                        st.info("Сервер сообщает: генерация ещё выполняется. ИИ не вызывался.")
                    elif response.get("status") == "claimed":
                        st.warning("Сервер разрешил генерацию: у этого заказа нет завершённого профиля. ИИ не вызывался.")
                    else:
                        st.error("Неожиданный статус проверки.")
            except Exception as exc:
                st.error("Ошибка проверки: " + type(exc).__name__)

        if st.button("Проверить повтор после ошибки (без ИИ)", key="generation_retry_check"):
            try:
                manager = OrderManager.from_streamlit_secrets()
                order_id = "OBR-TEST-" + uuid.uuid4().hex[:20].upper()
                secret = secrets.token_urlsafe(32)
                access_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
                manager.create_order("test", 0, order_id=order_id, recovery_hash=access_hash)
                first_id = str(uuid.uuid4())
                first = manager.claim_generation(order_id, "profile", access_hash, first_id)
                if first.get("status") != "claimed":
                    raise RuntimeError("first_claim_failed")
                busy = manager.claim_generation(order_id, "profile", access_hash, str(uuid.uuid4()))
                if busy.get("status") != "processing":
                    raise RuntimeError("parallel_claim_not_blocked")
                manager.finish_generation(order_id, "profile", access_hash, first_id, "failed")
                second_id = str(uuid.uuid4())
                retry = manager.claim_generation(order_id, "profile", access_hash, second_id)
                if retry.get("status") != "claimed":
                    raise RuntimeError("retry_not_allowed")
                manager.finish_generation(order_id, "profile", access_hash, second_id, "failed")
                st.success("Проверка пройдена: параллельный запуск запрещён, после ошибки повтор разрешён. ИИ не вызывался.")
            except Exception as exc:
                st.error("Проверка повторной попытки: " + type(exc).__name__)

        if st.button("Проверить обмен с Google Drive (2 минуты)", key="crypto_drive_check"):
            try:
                from result_crypto import encrypt_result, decrypt_result
                key = str(st.secrets["result_encryption"]["key"])
                manager = OrderManager.from_streamlit_secrets()
                order_id = "OBR-TEST-" + uuid.uuid4().hex
                secret = secrets.token_urlsafe(32)
                access_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
                sample = "Фиктивный тестовый результат Образы 🌿"
                ciphertext = encrypt_result(sample, key)
                manager.create_order("test", 0, order_id=order_id)
                manager.update_order(order_id, service_status="completed")
                saved = manager.save_temporary_result(order_id, "profile", ciphertext, access_hash)
                fetched = manager.get_temporary_result(order_id, "profile", access_hash)
                if fetched.get("status") != "available" or decrypt_result(fetched["ciphertext"], key) != sample:
                    raise RuntimeError("Восстановленный текст не совпадает")
                st.success("Google Drive: сохранение и восстановление OK (2 минуты)")
                st.caption("Только фиктивные данные. Доступ истечёт через 2 минуты.")
            except Exception as exc:
                # Технический код ошибки без URL, токенов и содержимого ответа.
                from order_manager import JournalError
                if isinstance(exc, JournalError):
                    st.error("Обмен: ошибка журнала. " + str(exc).split("Apps Script отклонил операцию: ")[-1].splitlines()[0][:120])
                else:
                    st.error("Обмен: ошибка типа " + type(exc).__name__)
                st.caption("Ключ шифрования и текст результата не отображаются.")



SYSTEM = "Ты умный и эмпатичный ИИ, помогай пользователю находить себя."


# ---------- обращение к модели ----------
def ask_llm(prompt: str) -> str:
    provider = st.secrets.get("PROVIDER", "deepseek")

    if provider == "gemini":
        primary = st.secrets.get("GEMINI_MODEL", "gemini-3.8-flash")
        models = [primary] + [
            m for m in ("gemini-3.6-flash", "gemini-3.1-flash-lite") if m != primary
        ]
        last_err = None
        for model in models:
            for attempt in range(2):
                try:
                    r = requests.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                        headers={
                            "x-goog-api-key": st.secrets["GEMINI_API_KEY"],
                            "Content-Type": "application/json",
                        },
                        json={
                            "system_instruction": {"parts": [{"text": SYSTEM}]},
                            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                            "generationConfig": {"temperature": 0.7},
                        },
                        timeout=120,
                    )
                    if r.status_code in (429, 500, 503, 504):
                        last_err = f"{r.status_code} ({model})"
                        time.sleep(2 * (attempt + 1))
                        continue
                    r.raise_for_status()
                    data = r.json()
                    if not data.get("candidates"):
                        raise RuntimeError(f"Пустой ответ модели: {data.get('promptFeedback')}")
                    parts = data["candidates"][0].get("content", {}).get("parts", [])
                    return "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
                except requests.exceptions.Timeout:
                    last_err = f"таймаут ({model})"
        raise RuntimeError("Сервер перегружен. Попробуйте через минуту.")

    if provider == "claude":
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": st.secrets["ANTHROPIC_API_KEY"],
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": st.secrets.get("CLAUDE_MODEL", "claude-sonnet-5-5"),
                "max_tokens": 3000,
                "system": SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=120,
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"]).strip()

    r = requests.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {st.secrets['DEEPSEEK_API_KEY']}"},
        json={
            "model": "deepseek-chat",
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=120,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


# ---------- логика ----------
CARD_SAMPLES = """Образцы желаемого стиля: простой, ясный русский, короткие фразы, без пафоса и громоздких метафор. Содержание не копируй.
[
  {
    "portrait": "Глубокий мыслитель и стратег. Склонен к постоянному самонаблюдению, рациональному самоконтролю, философскому взгляду на события. Спокойствие не пассивно — оно дисциплинирующее. Эмоции подчинены разуму, решения принимаются в системе ценностей, а не в порыве.",
    "brain_zones": ["Префронтальная кора (анализ, контроль)", "Задняя поясная извилина (саморефлексия, наблюдение)", "Миндалина в тормозящем режиме (контроль аффекта)"],
    "signs": ["Привычка всё обдумывать, прежде чем решить", "Записи и дневники как способ разгрузки", "Трудно показывать усталость при других"],
    "overload": ["Перенапряжение от необходимости быть «оплотом здравомыслия»", "Эмоциональное выгорание при постоянной сдержанности"],
    "adaptation": "Интроспекция, ретриты, философские размышления. Возврат к письменным практикам (журналы, трактаты) как способ структурировать перегрузки."
  },
  {
    "portrait": "Целеустремлённый реформатор. Жёсткий, гибкий, стратегически амбициозный. Способен разрушить структуру ради новой, если старая мешает целям. Энергия направлена не на созерцание, а на изменение. Ядро — вера в идею, даже если она противоречит текущим обстоятельствам.",
    "brain_zones": ["Поясная кора (воля и настойчивость)", "Лобные доли (инициативность, принятие решений)", "Область Брока и Вернике (сильная внутренняя речь, аргументация)"],
    "signs": ["Говорит о цели даже в отдыхе", "Быстро меняет тактику, если старая мешает", "Раздражается, когда возражают без аргументов"],
    "overload": ["Психическая жёсткость → игнор обратной связи", "Риск эмоционального тоннелирования → «слепое» следование идее"],
    "adaptation": "Контакт с альтернативными источниками информации. Мета-позиция: наблюдение за собой «внутри идеи». Необходимо окружение, способное давать контраргументы без угрозы для доверия."
  },
  {
    "portrait": "Бюрократический идеалист. Мягкий в поведении, но устойчивый в убеждениях. Склонен выстраивать системы, структуры иерархии. Полагается на предсказуемость и правила. Ищет баланс между реализмом и сохранением прошлого.",
    "brain_zones": ["Орбитофронтальная кора (социальные нормы, компромиссы)", "Гиппокамп (память, связь с прошлым)", "Зеркальные нейроны (чтение намерений других)"],
    "signs": ["Ежедневные ритуалы и привычные маршруты", "Аккуратные списки, архивы, заметки", "Сдержанность при посторонних, мягкая ирония"],
    "overload": ["Давление со стороны более жёстких фигур", "Раскол между лояльностью структурам и необходимостью адаптироваться"],
    "adaptation": "Выход за пределы привычных ролей. Постепенное расширение круга общения. Личное творчество как форма индивидуализации (музыка, работа с текстами, визуальные схемы)."
  }
]"""

ANALYSIS_SAMPLE = """Образец структуры и тона (содержание и книги не копируй, подбирай под выбранный профиль):

🧬 Образ жизни
Человек структуры и долгосрочного равновесия. Живёт по внутреннему регламенту: определённое время для работы, обязательств, личных дел. Оценивает свои действия с точки зрения пользы для системы — семьи, коллектива, государства. Не склонен к резким переменам. Предпочитает устойчивые форматы — стабильную работу, понятные отношения, узнаваемую среду.

🔁 Типичные привычки
- Склонность к ежедневным ритуалам (чай в одно и то же время, привычные маршруты).
- Создание и поддержание документации — блокноты, списки, файлы, архивы.
- Сдержанность в выражении эмоций на публике, возможна мягкая ирония.
- Нежелание делиться личным, даже с близкими.

⚠️ Возможные психофизиологические проблемы
- Перегрузка от консерватизма среды: ощущение, что всё вокруг застряло, но нет ресурса изменить.
- Подавление эмоций → психосоматические реакции: повышенное давление, расстройства ЖКТ.
- Чувство вины за отступление от правил, даже когда правила устарели.

🤝 Советы: как подружиться со своим мозгом
- Добавляйте новизну безопасно: книги других жанров, разговоры с непривычными собеседниками, смена обстановки.
- Позвольте себе слабость: не всё должно быть под контролем. Состояние «не знаю» — это ресурс для роста.
- Разрешите себе менять мнение: ваш авторитет не рушится, если вы пересматриваете взгляды.

📚 Рекомендуемые книги
- Автор — «Название» (короткая пометка, чем полезна)"""

STYLE_RULES = (
    "Стиль: простой, живой, понятный русский язык, как у умного собеседника, а не как научная статья. "
    "Короткие и средние предложения. Никакого канцелярита, патетики и вычурных метафор "
    "(не используй слова вроде «монолит», «флуктуации», «аппаратный», «выплавлено», «тотальный»). "
    "Зоны мозга называй точно, а пояснение в скобках делай коротким, в несколько слов."
)


def generate_profiles(characters: str) -> list[dict]:
    prompt = (
        f"Пользователь назвал персонажей фильмов, книг или реальных публичных людей: {characters}.\n"
        "Если после имени в скобках есть пояснение, это лишь справка о том, кто это; "
        "психотип определяй сам, не опираясь на характеристики, которые дал пользователь. "
        "Для КАЖДОГО создай отдельную обезличенную психофизиологическую карточку. "
        "Образы формируются не как историческая справка, а как метафорические психотипы. "
        "Не называй имён, не упоминай персонажей и не намекай на них, не нумеруй.\n"
        + STYLE_RULES + "\n"
        "Верни ТОЛЬКО JSON-массив без пояснений и без markdown. Каждый элемент — объект:\n"
        "portrait (строка: психологический портрет, 3–4 предложения),\n"
        "brain_zones (массив из 3 строк вида «Зона (что она даёт)»: это твоя внутренняя опора для логичного описания, пользователю она не показывается),\n"
        "signs (массив из 3 строк: как этот тип проявляется в повседневных привычках и в теле),\n"
        "overload (массив из 2 точек психофизиологической перегрузки),\n"
        "adaptation (строка: стратегия адаптации, 2–3 предложения).\n\n"
        + CARD_SAMPLES
    )
    raw = ask_llm(prompt)
    raw = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.M).strip()
    profiles = json.loads(raw)
    random.shuffle(profiles)  # порядок не должен выдавать, где чей образ
    return profiles


def analyze(cards: list[dict]) -> str:
    text = "\n\n".join(
        f"Карточка {i}:\n{json.dumps(c, ensure_ascii=False, indent=2)}"
        for i, c in enumerate(cards, 1)
    )
    prompt = (
        "Пользователь выбрал как наиболее близкие эти метафорические психотипы:\n\n"
        f"{text}\n\n"
        "Создай полную психофизиологическую модель по пяти разделам. Пиши на «вы». "
        + STYLE_RULES + " "
        "Используй ровно эти заголовки с иконками:\n"
        "🧬 Образ жизни (абзац)\n"
        "🔁 Типичные привычки (список из 5–6 пунктов)\n"
        "⚠️ Возможные психофизиологические проблемы (список из 4 пунктов)\n"
        "🤝 Советы: как подружиться со своим мозгом (список из 4 советов)\n"
        "📚 Рекомендуемые книги (5 книг: автор — название, с короткой пометкой, чем полезна)\n"
        "Зоны мозга в карточках — твоя внутренняя опора, чтобы логично вывести типичные перегрузки; "
        "в тексте зоны не называй и не утверждай ничего про измерения мозга. "
        "Проблемы описывай через привычки и телесные признаки (сон, напряжение в шее и плечах, "
        "усталость, пищеварение, концентрация), без диагнозов. "
        "Если выбрано несколько карточек, объедини их в один целостный портрет и ни одну не теряй: "
        "в привычках и проблемах должны быть признаки каждой выбранной карточки.\n"
        "В самом конце одной тёплой строкой, без казённых формулировок, скажи: если усталость, "
        "плохой сон или напряжение в теле держатся давно, стоит показаться врачу, "
        "тело лучше слушать вовремя.\n\n"
        + ANALYSIS_SAMPLE
    )
    return ask_llm(prompt)


def build_profile_text(cards: list[dict], result: str) -> str:
    """Текст профиля для скачивания (его же можно загрузить во вкладку «Совместимость»)."""
    lines = ["ПСИХОПРОФИЛЬ", ""]
    for n, c in enumerate(cards, 1):
        lines += [
            f"Выбранный образ {n}",
            "Портрет: " + c.get("portrait", ""),
            "Как проявляется: " + "; ".join(c.get("signs", [])),
            "Точки перегрузки: " + "; ".join(c.get("overload", [])),
            "Адаптация: " + c.get("adaptation", ""),
            "",
        ]
    lines += ["РАЗБОР", result]
    return "\n".join(lines)


def read_profile_file(f) -> str:
    name = f.name.lower()
    if name.endswith(".docx"):
        from docx import Document

        return "\n".join(p.text for p in Document(f).paragraphs)
    return f.read().decode("utf-8", errors="ignore")


RELATION_TYPES = ["Романтические отношения", "Дружба", "Работа и партнёрство", "Семья"]


COMPAT_SAMPLE = """Образец формата (содержание, названия типов и формулировки не копируй):

| Параметр | Человек А | Человек Б | Сочетание |
|---|---|---|---|
| Ценности | Эстетика, свобода через контроль | Честь, структура, предсказуемость | ✔ Высокое: оба уважают внутренний кодекс |
| Темп | Скачками, реактивный | Стабильный, холодноватый | ⚠ Разный ритм |

Проблема 1. Борьба за контроль
- **Сценарий:** оба хотят держать стратегию и склонны проверять другого.
- **Реакция:** молчание одного читается как манипуляция, импульсивные ходы другого как угроза стабильности.
- **Решение:** разделить зоны ответственности («ты отвечаешь за X, я за Y») и записать общие правила пары."""


def analyze_compatibility(a: str, b: str, name_a: str, name_b: str, relation: str) -> str:
    prompt = (
        f"Ниже два психопрофиля: «{name_a}» и «{name_b}». Тип отношений: {relation}.\n\n"
        f"=== ПРОФИЛЬ «{name_a}» ===\n{a[:7000]}\n\n"
        f"=== ПРОФИЛЬ «{name_b}» ===\n{b[:7000]}\n\n"
        "Это метафорические психотипы для самопознания. Составь разбор совместимости. "
        "Пиши на «вы», обращаясь к паре, и называй людей по именам из заголовков. "
        + STYLE_RULES + " "
        "Оба человека равноценны: никого не обвиняй, не ставь диагнозов, не называй никого "
        "«токсичным», не выноси вердикт «подходят / не подходят» и не называй сроков. "
        "Пиши «склонен», «может», а не «всегда». Опирайся только на содержимое профилей, "
        "зоны мозга и измерения не упоминай. "
        "Используй ровно эти заголовки с иконками:\n"
        "🔍 Кто они (по строке на каждого: придумай короткое образное название типа и "
        "добавь 1–2 предложения)\n"
        "💠 Точки соприкосновения (markdown-таблица: Параметр | имя первого | имя второго | Сочетание; "
        "4 строки: Ценности, Темп, Роль в паре, Эмоции; в последней колонке ✔ или ⚠ и несколько слов)\n"
        "😶‍🌫️ Как каждый ведёт себя в стрессе и что получается в паре (абзац)\n"
        "❤️‍🔥 Потенциал отношений (3 пункта: почему это может работать)\n"
        "⚠️ Возможные проблемы (3 проблемы; у каждой строки «Сценарий», «Реакция», «Решение»; "
        "решения конкретные: договорённости, фразы, ритуалы)\n"
        "✅ Идеальный формат союза (3–4 пункта)\n"
        "🔮 Если смотреть вперёд (два условных сценария: «если ничего не менять» и «если договориться»; "
        "без сроков и без вердикта)\n"
        "📚 Книги для пары (3 книги: автор — название, с короткой пометкой)\n"
        "В конце одной тёплой строкой скажи: если трения повторяются и тяжелы, "
        "стоит обратиться к семейному психологу, это нормальный шаг.\n\n"
        + COMPAT_SAMPLE
    )
    return ask_llm(prompt)


# ---------- тарифы и оплата ----------
PRICE_PROFILE = int(st.secrets.get("PRICE_PROFILE", 199))
PRICE_FULL = int(st.secrets.get("PRICE_FULL", 349))
CURRENCY = "₽"

PLANS = {
    "profile": {
        "label": f"Только профиль — {PRICE_PROFILE} {CURRENCY}",
        "price": PRICE_PROFILE,
        "desc": "Полный разбор выбранных образов: образ жизни, привычки, перегрузки, советы и книги.",
    },
    "full": {
        "label": f"Профиль + совместимость — {PRICE_FULL} {CURRENCY}",
        "price": PRICE_FULL,
        "desc": "Всё из первого варианта и разбор совместимости двух профилей: "
        "сильные стороны пары, трения и шаги по их преодолению.",
    },
}


def journal():
    """Журнал включается после настройки Apps Script в Secrets."""
    if "order_journal" not in st.secrets:
        if st.secrets.get("REQUIRE_JOURNAL", False):
            raise JournalError("Журнал заказов не настроен")
        return None
    return OrderManager.from_streamlit_secrets()


def journal_event(event_type, *, result=None, operation="", status="ok"):
    manager = journal()
    order_id = st.session_state.get("order_id")
    if not manager or not order_id:
        if st.secrets.get("REQUIRE_JOURNAL", False):
            raise JournalError("Нет подтверждённого заказа")
        return
    key = f"journal_event_id_{event_type}_{operation}"
    event_id = st.session_state.setdefault(key, str(uuid.uuid4()))
    manager.log_event(order_id, event_type, operation=operation,
                      status=status, result=result, event_id=event_id)
    st.session_state.pop(key, None)


def journal_result(result, operation, download_text):
    """Записываем каждый этап один раз; после сбоя продолжаем с незавершённого."""
    manager = journal()
    order_id = st.session_state.get("order_id")
    if not manager or not order_id:
        if st.secrets.get("REQUIRE_JOURNAL", False):
            raise JournalError("Нет подтверждённого заказа")
        return

    # Один и тот же результат в одном заказе всегда получает те же ID событий.
    result_key = str(uuid.uuid5(uuid.NAMESPACE_URL, order_id + ":" + operation + ":" + result))
    for event_type, value in (
        ("ai_response", result),
        ("download_file_hash", download_text.encode("utf-8")),
    ):
        done_key = f"journal_done_{result_key}_{event_type}"
        if not st.session_state.get(done_key):
            event_id = str(uuid.uuid5(uuid.NAMESPACE_URL, result_key + ":" + event_type))
            manager.log_event(order_id, event_type, operation=operation,
                              result=value, event_id=event_id)
            st.session_state[done_key] = True

    completed_key = f"journal_done_{result_key}_completed"
    if not st.session_state.get(completed_key):
        manager.update_order(order_id, result=result, service_status="completed")
        st.session_state[completed_key] = True



def generation_guard(operation):
    """Claim one server-side generation slot per order and operation."""
    manager = journal()
    order_id = st.session_state.get("order_id")
    secret = st.session_state.get("order_recovery_secret")
    if not manager or not order_id or not secret:
        raise JournalError("Невозможно проверить право генерации")
    key = f"generation_claim_{order_id}_{operation}"
    if st.session_state.get(key):
        return st.session_state[key]
    claim_id = str(uuid.uuid4())
    access_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    response = manager.claim_generation(order_id, operation, access_hash, claim_id)
    status = response.get("status")
    if status == "completed":
        raise JournalError("Результат уже создан. Откройте ссылку восстановления.")
    if status == "processing":
        raise JournalError("Генерация уже выполняется. Дождитесь её завершения.")
    if status != "claimed":
        raise JournalError("Не удалось зарезервировать генерацию")
    st.session_state[key] = claim_id
    return claim_id


def generation_finish(operation, status):
    manager = journal()
    order_id = st.session_state.get("order_id")
    secret = st.session_state.get("order_recovery_secret")
    claim_id = st.session_state.get(f"generation_claim_{order_id}_{operation}")
    if not manager or not order_id or not secret or not claim_id:
        raise JournalError("Не найдена активная генерация")
    access_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    manager.finish_generation(order_id, operation, access_hash, claim_id, status)
    st.session_state.pop(f"generation_claim_{order_id}_{operation}", None)


def save_encrypted_result(operation, result, download_text):
    """Test-only: save encrypted output after journal completion; retry without new AI call."""
    if not st.secrets.get("TEST_FAILURE_MODE", False):
        return
    from result_crypto import encrypt_result, decrypt_result
    manager = journal()
    order_id = st.session_state.get("order_id")
    if not manager or not order_id:
        raise JournalError("Нет заказа для временного хранения")
    state_key = f"temporary_{order_id}_{operation}"
    pending = st.session_state.get(state_key)
    if pending is None:
        recovery_secret = st.session_state.get("order_recovery_secret")
        if not recovery_secret:
            raise JournalError("Отсутствует секрет восстановления заказа")
        pending = {
            "secret": recovery_secret,
            "hash": hashlib.sha256(recovery_secret.encode("utf-8")).hexdigest(),
            "ciphertext": encrypt_result(
                json.dumps({"result": result, "download_text": download_text}, ensure_ascii=False),
                str(st.secrets["result_encryption"]["key"])),
        }
        st.session_state[state_key] = pending
    try:
        manager.save_temporary_result(order_id, operation, pending["ciphertext"], pending["hash"])
    except JournalError as exc:
        # A timeout can happen after successful storage; verify exact ciphertext.
        if "result_already_exists" not in str(exc):
            raise
        existing = manager.get_temporary_result(order_id, operation, pending["hash"])
        if existing.get("status") != "available" or existing.get("ciphertext") != pending["ciphertext"]:
            raise
    st.session_state[f"temporary_saved_{order_id}_{operation}"] = True



def order_recovery_link():
    """Stable link issued at checkout; no result is required yet."""
    order_id = st.session_state.get("order_id")
    secret = st.session_state.get("order_recovery_secret")
    if not order_id or not secret:
        return
    from urllib.parse import urlencode
    url = "https://yvtsiteuv37h8wnkzdbpxx.streamlit.app/?" + urlencode({
        "recover_order": order_id, "recover_secret": secret,
    })
    st.info("Сохраните ссылку восстановления заказа. Она откроет последний сохранённый результат, если он уже готов. Не передавайте ссылку другим.")
    st.code(url, language=None)


def recovery_link(operation):
    order_id = st.session_state.get("order_id")
    if not order_id:
        return
    order_recovery_link()


def restore_from_link():
    """Restore existing encrypted result, never invoke an LLM."""
    order_id = str(st.query_params.get("recover_order", ""))
    operation = str(st.query_params.get("recover_operation", ""))
    secret = str(st.query_params.get("recover_secret", ""))
    if not order_id:
        return False
    st.session_state.site_page = "Исследование"
    if (not re.fullmatch(r"OBR-[A-Za-z0-9-]{10,90}", order_id)
            or operation not in ("", "profile", "compatibility")
            or not re.fullmatch(r"[A-Za-z0-9_-]{40,100}", secret)):
        st.error("Неверная ссылка восстановления.")
        st.stop()
    try:
        from result_crypto import decrypt_result
        manager = journal()
        if not manager:
            raise JournalError("Журнал недоступен")
        access_hash = hashlib.sha256(secret.encode("utf-8")).hexdigest()
        if not operation:
            for candidate in ("compatibility", "profile"):
                response = manager.get_temporary_result(order_id, candidate, access_hash)
                if response.get("status") == "available":
                    operation = candidate
                    break
            else:
                st.info("По этому заказу пока нет доступного сохранённого результата.")
                st.stop()
        else:
            response = manager.get_temporary_result(order_id, operation, access_hash)
            if response.get("status") != "available":
                st.warning("Срок хранения результата истёк.")
                st.stop()
        data = json.loads(decrypt_result(
            response["ciphertext"], str(st.secrets["result_encryption"]["key"])))
        if not isinstance(data.get("result"), str) or not isinstance(data.get("download_text"), str):
            raise ValueError("invalid_result")
        st.session_state.order_id = order_id
        st.session_state.paid_plan = "full" if operation == "compatibility" else "profile"
        if operation == "profile":
            st.session_state.result = data["result"]
            st.session_state.profile_text = data["download_text"]
            st.session_state.research_step = "profile_result"
        else:
            st.session_state.compat = data["result"]
            st.session_state.compat_text = data["download_text"]
            st.session_state.research_step = "compat_result"
        st.query_params.clear()
        st.rerun()
    except (JournalError, ValueError, KeyError, TypeError):
        st.error("Не удалось восстановить результат. Проверьте ссылку и срок действия.")
        st.stop()
    return True


def process_payment(plan_key: str, amount: int) -> bool:
    """Демонстрационная оплата; реальных списаний нет."""
    manager = journal()
    if manager:
        pending = st.session_state.get("pending_order")
        if not pending or pending["plan"] != plan_key or pending["amount"] != amount:
            pending = {"plan": plan_key, "amount": amount,
                       "id": "OBR-" + uuid.uuid4().hex[:20].upper(),
                       "recovery_secret": secrets.token_urlsafe(32)}
            st.session_state.pending_order = pending
        # Keep the same credential across retries; never overwrite a bound hash.
        if "recovery_secret" not in pending:
            pending["recovery_secret"] = secrets.token_urlsafe(32)
        recovery_hash = hashlib.sha256(pending["recovery_secret"].encode("utf-8")).hexdigest()
        order_id = manager.create_order(plan_key, amount, order_id=pending["id"],
                                        recovery_hash=recovery_hash)
        st.session_state.order_id = order_id
        st.session_state.order_recovery_secret = pending["recovery_secret"]
        journal_event("payment_demo", operation=plan_key, status="simulated")
        st.session_state.pop("pending_order", None)
    return True


# ---------- интерфейс ----------
ASSETS = Path(__file__).parent / "assets"
style_file = ASSETS / "site.css"
if style_file.exists():
    st.markdown("<style>" + style_file.read_text(encoding="utf-8") + "</style>", unsafe_allow_html=True)

def show_art(filename, width=None):
    path = ASSETS / filename
    if path.exists():
        if width is None:
            st.image(str(path))
        else:
            st.image(str(path), width=width)

def navigate(step):
    st.session_state.research_step = step
    st.rerun()

if st.query_params.get("recover_order"):
    restore_from_link()

if st.query_params.get("view") == "research":
    requested_plan = st.query_params.get("plan")
    st.session_state.site_page = "Исследование"
    if requested_plan in PLANS:
        st.session_state.checkout_plan = requested_plan
        st.session_state.research_step = "checkout"
    else:
        st.session_state.research_step = "choose"
    st.query_params.clear()

page = st.session_state.get("site_page", "Главная")
if page == "Главная":
    from landing import render_landing
    render_landing(PRICE_PROFILE, PRICE_FULL)
    st.stop()

if st.button("← На главную", key="back_home"):
    st.session_state.site_page = "Главная"
    st.rerun()

pwd = st.secrets.get("APP_PASSWORD")
if pwd and not st.session_state.get("authenticated", False):
    st.markdown("### Вход в тестовую версию")
    with st.form("password_form"):
        entered_password = st.text_input("Пароль доступа", type="password")
        submitted = st.form_submit_button("Войти", type="primary")
    if submitted:
        if hmac.compare_digest(entered_password, str(pwd)):
            st.session_state.authenticated = True
            st.rerun()
        st.error("Неверный пароль")
    st.stop()

if st.secrets.get("TEST_FAILURE_MODE", False):
    with st.expander("Journal fault testing"):
        st.selectbox("Simulated failure", ["none", "create_order", "log_event", "update_order", "all"], key="journal_test_failure")

st.title("Исследование себя через образы")
st.caption(
    "Образы создаёт ИИ как метафорические психотипы, а не историческая справка. "
    "Это не диагностика и не медицинская информация."
)

step = st.session_state.get("research_step", "choose")
plan = st.session_state.get("paid_plan")

# Show the same order recovery link on every post-checkout research screen.
if step in ("characters", "descriptions", "profile_result", "compat_input", "compat_result"):
    order_recovery_link()

if step == "choose":
    st.subheader("Выберите программу исследования")
    st.write("Начните с исследования своего профиля или изучите совместимость двух профилей. "
             "После оплаты мы последовательно проведём вас через все этапы.")
    c1, c2 = st.columns(2)
    with c1:
        show_art("woman.svg", width=180)
        st.markdown(f"### Профиль — {PRICE_PROFILE} ₽")
        st.write(PLANS["profile"]["desc"])
        if st.button("Выбрать «Профиль»", use_container_width=True):
            st.session_state.checkout_plan = "profile"
            navigate("checkout")
    with c2:
        show_art("couple.svg", width=180)
        st.markdown(f"### Профиль + совместимость — {PRICE_FULL} ₽")
        st.write(PLANS["full"]["desc"])
        if st.button("Выбрать «Профиль + совместимость»", use_container_width=True):
            st.session_state.checkout_plan = "full"
            navigate("checkout")

elif step == "checkout":
    choice = st.session_state.get("checkout_plan", "profile")
    st.subheader("Оформление заказа")
    st.write(f"Выбранная программа: **{PLANS[choice]['label']}**")
    if choice == "full":
        st.warning(
            "Исследование «Профиль + совместимость» целесообразно, если у вас уже "
            "есть один готовый профиль. Для анализа совместимости нужны два профиля."
        )
        has_profile = st.checkbox("У меня есть готовый профиль", key="has_ready_profile")
    else:
        has_profile = True
    st.info("Сейчас доступен демонстрационный режим: оплата имитируется, деньги не списываются.")
    if st.button(f"Оплатить {PLANS[choice]['price']} ₽ и начать исследование",
                 disabled=not has_profile):
        try:
            process_payment(choice, PLANS[choice]["price"])
            st.session_state.paid_plan = choice
            st.session_state.pop("profiles", None)
            st.session_state.pop("result", None)
            st.session_state.pop("profile_text", None)
            st.session_state.pop("compat", None)
            st.session_state.pop("compat_text", None)
            for key in list(st.session_state):
                if str(key).startswith("pick_"):
                    del st.session_state[key]
            navigate("characters")
        except (JournalError, ValueError, KeyError) as exc:
            st.error(f"Не удалось зарегистрировать заказ: {exc}. Попробуйте ещё раз.")
    if st.button("← К выбору программы"):
        navigate("choose")

elif step == "characters":
    st.subheader("Шаг 1 из 3. Ваши образы")
    a_art, b_art = st.columns(2)
    with a_art:
        show_art("woman.svg")
    with b_art:
        show_art("man.svg")
    st.info(
        "Введите 1–3 персонажей фильмов, книг или публичных людей, с которыми вы себя ассоциируете. "
        "Если персонаж малоизвестен, укажите в скобках, кто это (откуда он, кем является), "
        "без описания характера. Пример: Гоша (герой фильма «Москва слезам не верит»), "
        "Харли Квинн, Дональд Трамп."
    )
    characters = st.text_input("Персонажи", key="research_characters")
    if st.button("Продолжить", disabled=not characters.strip()):
        with st.spinner("Создаю описания..."):
            try:
                st.session_state.profiles = generate_profiles(characters)
                for key in list(st.session_state):
                    if str(key).startswith("pick_"):
                        del st.session_state[key]
                navigate("descriptions")
            except Exception as exc:
                st.error(f"Не получилось создать описания: {str(exc).rstrip(chr(46))}. Введённые персонажи сохранены.")

elif step == "descriptions":
    profiles = st.session_state.get("profiles")
    if not profiles:
        st.warning("Сначала введите персонажей.")
        if st.button("Перейти к вводу персонажей"):
            navigate("characters")
    else:
        st.subheader("Шаг 2 из 3. Выберите подходящие описания")
        st.info("Прочитайте все описания и отметьте «Это про меня» у одного или нескольких подходящих.")
        for i, p in enumerate(profiles):
            st.markdown(f"### Профиль {i + 1}")
            left, right = st.columns(2)
            with left:
                st.markdown(f"**Психологический портрет**\n\n{p.get('portrait', '')}")
                signs = "\n".join(f"- {s}" for s in p.get("signs", []))
                st.markdown(f"**Как это проявляется в жизни**\n\n{signs}")
            with right:
                over = "\n".join(f"- {o}" for o in p.get("overload", []))
                st.markdown(f"**Точки перегрузки**\n\n{over}")
                st.markdown(f"**Стратегия адаптации**\n\n{p.get('adaptation', '')}")
            st.checkbox("Это про меня", key=f"pick_{i}")
            st.divider()
        chosen = [p for i, p in enumerate(profiles) if st.session_state.get(f"pick_{i}")]
        if st.button("Продолжить", disabled=not chosen):
            with st.spinner("Готовлю ваш результат..."):
                try:
                    pending = st.session_state.get("pending_profile_result")
                    if pending is None:
                        generation_guard("profile")
                        journal_event("ai_request", operation="profile")
                        try:
                            result = analyze(chosen)
                        except Exception:
                            generation_finish("profile", "failed")
                            raise
                        download_text = build_profile_text(chosen, result)
                        st.session_state.pending_profile_result = (result, download_text)
                    else:
                        result, download_text = pending
                    journal_result(result, "profile", download_text)
                    save_encrypted_result("profile", result, download_text)
                    generation_finish("profile", "completed")
                    st.session_state.pop("pending_profile_result", None)
                    st.session_state.result = result
                    st.session_state.profile_text = download_text
                    st.session_state.profile_download_clicked = False
                    st.session_state.pop("profile_display_logged", None)
                    navigate("profile_result")
                except Exception as exc:
                    st.error(f"Не удалось подготовить результат: {exc}. Выбранные описания сохранены.")

elif step == "profile_result":
    if not st.session_state.get("result"):
        st.warning("Результат пока не готов.")
        if st.button("Вернуться к описаниям"):
            navigate("descriptions")
    else:
        st.subheader("Шаг 3 из 3. Ваш профиль")
        st.markdown(st.session_state.result)
        if not st.session_state.get("profile_display_logged"):
            try:
                manager = journal()
                if manager and st.session_state.get("order_id"):
                    manager.update_order(st.session_state.order_id, result_displayed=True)
                    journal_event("result_displayed", operation="profile")
                st.session_state.profile_display_logged = True
            except Exception as exc:
                st.warning(f"Журнал: {exc}")
        if st.download_button("⬇️ Скачать мой профиль (.txt)", st.session_state.profile_text,
                              file_name="psychoprofile.txt"):
            st.session_state.profile_download_clicked = True
            try:
                journal_event("download_clicked", operation="profile")
            except Exception as exc:
                st.warning(f"Журнал: {exc}")
        if plan == "full":
            st.write("Ваш профиль готов. Теперь можно перейти к исследованию совместимости.")
            if not st.session_state.get("profile_download_clicked", False):
                st.caption("Для продолжения сначала скачайте результат профиля.")
            if st.button("Продолжить тестирование", type="primary",
                         disabled=not st.session_state.get("profile_download_clicked", False)):
                navigate("compat_input")
        else:
            st.markdown("### Продолжить исследование вместе с партнёром")
            st.write("Пригласите партнёра пройти исследование профиля, затем вы сможете "
                     "изучить вашу совместимость по программе «Профиль + совместимость».")
            if not st.session_state.get("profile_download_clicked", False):
                st.caption("Для перехода сначала скачайте результат профиля.")
            if st.button("Начать новое исследование «Профиль + совместимость»",
                         disabled=not st.session_state.get("profile_download_clicked", False)):
                st.session_state.checkout_plan = "full"
                navigate("checkout")

elif step == "compat_input":
    if plan != "full":
        st.warning("Исследование совместимости доступно по комплексному тарифу.")
        if st.button("Выбрать программу"):
            navigate("choose")
    else:
        st.subheader("Два профиля — одна история взаимодействия")
        show_art("couple.svg")
        st.info("Загрузите два готовых профиля (.txt или .docx) или вставьте текст. "
                "Можно использовать профиль, полученный на предыдущем этапе.")
        relation = st.selectbox("Тип отношений", RELATION_TYPES, key="compat_relation")
        texts, names = [], []
        for key, default in (("a", "Человек А"), ("b", "Человек Б")):
            st.markdown(f"#### {default}")
            names.append(st.text_input("Имя или подпись", value=default, key=f"name_{key}"))
            profile_text = ""
            if key == "a" and st.session_state.get("profile_text"):
                if st.checkbox("Взять мой профиль из исследования «Профиль»", key="use_mine"):
                    profile_text = st.session_state.profile_text
            if not profile_text:
                upload = st.file_uploader("Файл профиля", type=["txt", "docx"], key=f"file_{key}")
                if upload is not None:
                    try:
                        profile_text = read_profile_file(upload)
                    except Exception as exc:
                        st.error(f"Не удалось прочитать файл: {exc}")
            if not profile_text:
                profile_text = st.text_area("Или вставьте текст профиля", key=f"text_{key}", height=150)
            texts.append(profile_text.strip())
        ready = all(len(t) > 50 for t in texts)
        if st.button("Проверить совместимость", disabled=not ready):
            with st.spinner("Анализирую сочетание..."):
                try:
                    na, nb = names[0] or "Человек А", names[1] or "Человек Б"
                    pending = st.session_state.get("pending_compat_result")
                    if pending is None:
                        generation_guard("compatibility")
                        journal_event("ai_request", operation="compatibility")
                        try:
                            result = analyze_compatibility(texts[0], texts[1], na, nb, relation)
                        except Exception:
                            generation_finish("compatibility", "failed")
                            raise
                        download_text = (
                            f"РАЗБОР СОВМЕСТИМОСТИ\n{na} и {nb} ({relation})\n\n{result}"
                        )
                        st.session_state.pending_compat_result = (result, download_text)
                    else:
                        result, download_text = pending
                    journal_result(result, "compatibility", download_text)
                    save_encrypted_result("compatibility", result, download_text)
                    generation_finish("compatibility", "completed")
                    st.session_state.pop("pending_compat_result", None)
                    st.session_state.compat = result
                    st.session_state.compat_download_clicked = False
                    st.session_state.compat_text = download_text
                    st.session_state.pop("compat_display_logged", None)
                    navigate("compat_result")
                except Exception as exc:
                    st.error(f"Не получилось: {exc}. Введённые данные сохранены.")

elif step == "compat_result":
    if not st.session_state.get("compat"):
        st.warning("Результат совместимости пока не готов.")
        if st.button("Вернуться к вводу данных"):
            navigate("compat_input")
    else:
        st.subheader("💞 Разбор совместимости")
        st.markdown(st.session_state.compat)
        if not st.session_state.get("compat_display_logged"):
            try:
                manager = journal()
                if manager and st.session_state.get("order_id"):
                    manager.update_order(st.session_state.order_id, result_displayed=True)
                    journal_event("result_displayed", operation="compatibility")
                st.session_state.compat_display_logged = True
            except Exception as exc:
                st.warning(f"Журнал: {exc}")
        if st.download_button("⬇️ Скачать разбор совместимости (.txt)",
                              st.session_state.get("compat_text", st.session_state.compat),
                              file_name="compatibility.txt"):
            st.session_state.compat_download_clicked = True
            try:
                journal_event("download_clicked", operation="compatibility")
            except Exception as exc:
                st.warning(f"Журнал: {exc}")
