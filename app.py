import json
import random
import re
import time
from pathlib import Path

import requests
import streamlit as st

st.set_page_config(page_title="Образы — исследование себя", page_icon="🌿", layout="wide")

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
        raise RuntimeError(f"Gemini сейчас перегружен, попробуйте через минуту. Последняя ошибка: {last_err}")

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


def process_payment(plan_key: str, amount: int) -> bool:
    """ЗАГЛУШКА. Здесь подключается реальная оплата (ЮKassa, Stripe и т.п.):
    создать платёж на сумму amount, дождаться подтверждения и вернуть True/False."""
    return True


# ---------- интерфейс ----------
# ---------- оформление и навигация ----------
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

st.markdown("**ОБРАЗЫ**  ·  пространство для исследования себя")
page = st.radio("Раздел сайта", ["Главная", "Исследование"], horizontal=True, label_visibility="collapsed", key="site_page")

if page == "Главная":
    st.markdown('<div class="hero"><span class="hero-kicker">Метафорическое исследование</span><h1>Узнайте себя через образы, которые вам близки</h1><p>Назовите персонажей, с которыми вы себя ассоциируете. Искусственный интеллект создаст обезличенные описания — выберите те, в которых узнаёте себя, и получите персональный разбор.</p></div>', unsafe_allow_html=True)
    show_art("landscape.svg")
    if st.button("Начать исследование →", type="primary", key="start_hero"):
        st.session_state.site_page = "Исследование"
        st.rerun()
    st.markdown("## Как это работает")
    steps = st.columns(4)
    for col, heading, description in zip(steps,
        ["01 · Назовите образы", "02 · Прочитайте карточки", "03 · Выберите близкие", "04 · Получите разбор"],
        ["Введите от одного до трёх персонажей.", "ИИ создаст анонимные описания в случайном порядке.", "Отметьте все карточки, в которых узнаёте себя.", "Получите рекомендации и сохраните результат."]):
        with col:
            with st.container(border=True):
                st.markdown("**" + heading + "**")
                st.write(description)
    st.markdown("## Что вы получите")
    a,b=st.columns([1,1])
    with a:
        with st.container(border=True):
            st.markdown("### Профиль")
            st.write("Образ жизни, повторяющиеся привычки, возможные перегрузки, рекомендации и книги.")
            st.markdown("**" + str(PRICE_PROFILE) + " ₽ · тестовая цена**")
    with b:
        with st.container(border=True):
            st.markdown("### Профиль + совместимость")
            st.write("Профиль и анализ сочетания двух людей: сильные стороны, возможные разногласия и варианты взаимодействия.")
            st.markdown("**" + str(PRICE_FULL) + " ₽ · тестовая цена**")
    st.markdown("## О методе")
    st.write("Это метафорическое упражнение для саморефлексии, а не психологическая диагностика, медицинское заключение или прогноз будущего. Описания создаёт ИИ; пользователь сам решает, какие из них ему близки.")
    st.markdown("## Частые вопросы")
    with st.expander("Будут ли названы персонажи в карточках?"):
        st.write("Нет. Карточки представлены без имён персонажей и перемешаны.")
    with st.expander("Это психологический тест или терапия?"):
        st.write("Нет. Это развлекательный и информационный формат саморефлексии.")
    with st.expander("Можно ли сохранить результат?"):
        st.write("Да, профиль и анализ совместимости можно скачать в текстовом файле.")
    with st.expander("Нужно ли платить при тестировании?"):
        st.write("Нет. Оплата в прототипе имитируется; деньги не списываются.")
    st.divider()
    st.caption("18+ · Прототип сервиса «Образы» · Тестовый режим. Юридические документы будут опубликованы после согласования инфраструктуры и условий запуска.")
    st.stop()

pwd = st.secrets.get("APP_PASSWORD")
if pwd and st.text_input("Пароль", type="password") != pwd:
    st.stop()

st.title("Исследование себя через образы")
st.caption(
    "Образы создаёт ИИ как метафорические психотипы, а не историческая справка. "
    "Это не диагностика и не медицинская информация."
)

tab_profile, tab_compat = st.tabs(["Мой профиль", "Совместимость"])

# ---- вкладка 1: профиль ----
with tab_profile:
    st.markdown("### Ваши образы")
    a_art, b_art = st.columns(2)
    with a_art:
        show_art("woman.svg")
    with b_art:
        show_art("man.svg")
    st.info(
        "Введите 1–3 персонажей фильмов, книг или публичных людей, с которыми вы себя ассоциируете. "
        "Если персонаж малоизвестен, укажите в скобках, кто это (откуда он, кем является), "
        "без описания характера. "
        "Пример: Гоша (герой фильма «Москва слезам не верит»), "
        "Харли Квинн, Дональд Трамп"
    )

    characters = st.text_input("Персонажи")

    if st.button("Создать описания", disabled=not characters.strip()):
        with st.spinner("Создаю описания..."):
            try:
                st.session_state.profiles = generate_profiles(characters)
                st.session_state.pop("result", None)
                st.session_state.pop("profile_text", None)
                for k in [k for k in st.session_state if str(k).startswith("pick_")]:
                    del st.session_state[k]
            except Exception as e:
                st.error(f"Не получилось: {e}")

    profiles = st.session_state.get("profiles")
    if profiles:
        st.markdown("Отметьте галочкой **любые** описания, которые вам подходят: одно, два или все.")
        for i, p in enumerate(profiles):
            with st.expander(f"📄 Профиль {i + 1}", expanded=True):
                st.markdown(f"**Психологический портрет**\n\n{p.get('portrait', '')}")
                signs = "\n".join(f"- {s}" for s in p.get("signs", []))
                st.markdown(f"**Как это проявляется в жизни**\n\n{signs}")
                over = "\n".join(f"- {o}" for o in p.get("overload", []))
                st.markdown(f"**Точки перегрузки**\n\n{over}")
                st.markdown(f"**Стратегия адаптации**\n\n{p.get('adaptation', '')}")
                st.checkbox("✅ Это про меня", key=f"pick_{i}")

        chosen = [p for i, p in enumerate(profiles) if st.session_state.get(f"pick_{i}")]
        paid_plan = st.session_state.get("paid_plan")

        def run_analysis():
            st.session_state.result = analyze(chosen)
            st.session_state.profile_text = build_profile_text(chosen, st.session_state.result)

        if paid_plan is None:
            st.markdown("### Выберите вариант")
            keys = list(PLANS)
            choice = st.radio(
                "Что вы хотите получить?",
                keys,
                format_func=lambda k: PLANS[k]["label"],
                captions=[PLANS[k]["desc"] for k in keys],
                key="plan_choice",
            )
            if not chosen:
                st.caption("Сначала отметьте подходящие описания выше.")
            if st.button(f"💳 Оплатить {PLANS[choice]['price']} {CURRENCY} и получить разбор",
                         disabled=not chosen):
                if process_payment(choice, PLANS[choice]["price"]):
                    st.session_state.paid_plan = choice  # оплата не списывается повторно при ошибке
                    ok = False
                    with st.spinner("Анализирую..."):
                        try:
                            run_analysis()
                            ok = True
                        except Exception as e:
                            st.error(f"Не получилось: {e}")
                    if ok:
                        st.rerun()
                else:
                    st.error("Оплата не прошла. Попробуйте ещё раз.")
            st.caption("🧪 Демо-режим: оплата имитируется, деньги не списываются.")
        else:
            st.success(f"Ваш вариант: {PLANS[paid_plan]['label']} (оплачено, демо)")
            if st.button("Получить рекомендации", disabled=not chosen):
                with st.spinner("Анализирую..."):
                    try:
                        run_analysis()
                    except Exception as e:
                        st.error(f"Не получилось: {e}")

    if st.session_state.get("result"):
        st.subheader("🧠 Рекомендации")
        st.markdown(st.session_state.result)
        st.download_button(
            "⬇️ Скачать мой профиль (.txt)",
            st.session_state.profile_text,
            file_name="psychoprofile.txt",
            help="Файл можно загрузить во вкладке «Совместимость».",
        )

# ---- вкладка 2: совместимость ----
with tab_compat:
    st.markdown("### Два профиля — одна история взаимодействия")
    show_art("couple.svg")
    plan_now = st.session_state.get("paid_plan")
    if plan_now != "full":
        st.warning("🔒 Разбор совместимости входит в вариант «Профиль + совместимость».")
        if plan_now == "profile":
            extra = PRICE_FULL - PRICE_PROFILE
            label = f"💳 Добавить совместимость за {extra} {CURRENCY}"
            amount = extra
        else:
            label = f"💳 Открыть «Профиль + совместимость» за {PRICE_FULL} {CURRENCY}"
            amount = PRICE_FULL
        if st.button(label):
            if process_payment("full", amount):
                st.session_state.paid_plan = "full"
                st.rerun()
            else:
                st.error("Оплата не прошла. Попробуйте ещё раз.")
        st.caption("🧪 Демо-режим: оплата имитируется, деньги не списываются.")
    else:
        st.info(
            "Загрузите два готовых профиля (файл .txt или .docx, скачанный во вкладке «Мой профиль») "
            "или вставьте текст, чтобы увидеть сочетание, возможные трения и способы с ними справляться."
        )
        relation = st.selectbox("Тип отношений", RELATION_TYPES)

        texts, names = [], []
        for key, default in (("a", "Человек А"), ("b", "Человек Б")):
            st.markdown(f"#### {default}")
            names.append(st.text_input("Имя или подпись", value=default, key=f"name_{key}"))
            text = ""
            if key == "a" and st.session_state.get("profile_text"):
                if st.checkbox("Взять мой профиль из вкладки «Мой профиль»", key="use_mine"):
                    text = st.session_state.profile_text
            if not text:
                up = st.file_uploader("Файл профиля", type=["txt", "docx"], key=f"file_{key}")
                if up is not None:
                    try:
                        text = read_profile_file(up)
                    except Exception as e:
                        st.error(f"Не удалось прочитать файл: {e}")
            if not text:
                text = st.text_area("Или вставьте текст профиля", key=f"text_{key}", height=150)
            texts.append(text.strip())

        ready = all(len(t) > 50 for t in texts)
        if st.button("Проверить совместимость", disabled=not ready):
            with st.spinner("Анализирую сочетание..."):
                try:
                    na, nb = names[0] or "Человек А", names[1] or "Человек Б"
                    st.session_state.compat = analyze_compatibility(texts[0], texts[1], na, nb, relation)
                    st.session_state.compat_text = (
                        f"РАЗБОР СОВМЕСТИМОСТИ\n{na} и {nb} ({relation})\n\n{st.session_state.compat}"
                    )
                except Exception as e:
                    st.error(f"Не получилось: {e}")

        if st.session_state.get("compat"):
            st.subheader("💞 Разбор совместимости")
            st.markdown(st.session_state.compat)
            st.download_button(
                "⬇️ Скачать разбор совместимости (.txt)",
                st.session_state.get("compat_text", st.session_state.compat),
                file_name="compatibility.txt",
            )
