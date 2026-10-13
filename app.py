import json
import random
import re

import requests
import streamlit as st

st.set_page_config(page_title="Профиль по персонажам", page_icon="🧠")

SYSTEM = "Ты умный и эмпатичный ИИ, помогай пользователю находить себя."


# ---------- обращение к модели ----------
def ask_llm(prompt: str) -> str:
    provider = st.secrets.get("PROVIDER", "deepseek")

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
STYLE_SAMPLE = """Образец структуры и тона (содержание не копируй):
{
  "portrait": "Глубокий мыслитель и стратег. Склонен к постоянному самонаблюдению, рациональному самоконтролю. Спокойствие не пассивно, а дисциплинирующее. Эмоции подчинены разуму.",
  "brain_zones": ["Префронтальная кора (анализ, контроль)", "Задняя поясная извилина (саморефлексия, наблюдение)", "Миндалина в тормозящем режиме (контроль аффекта)"],
  "overload": ["Перенапряжение от необходимости быть «оплотом здравомыслия»", "Эмоциональное выгорание при постоянной сдержанности"],
  "adaptation": "Интроспекция, ретриты, философские размышления. Возврат к письменным практикам как способ структурировать перегрузки."
}"""


def generate_profiles(characters: str) -> list[dict]:
    prompt = (
        f"Пользователь назвал персонажей фильмов, книг или реальных публичных людей: {characters}.\n"
        "Для КАЖДОГО создай отдельную обезличенную психофизиологическую карточку. "
        "Образы формируются не как историческая справка, а как метафорические психотипы. "
        "Не называй имён, не упоминай персонажей и не намекай на них, не нумеруй. "
        "Пиши живо и конкретно, это описание типа.\n"
        "Верни ТОЛЬКО JSON-массив без пояснений и без markdown. Каждый элемент — объект:\n"
        "portrait (строка: психологический портрет, 3–5 предложений),\n"
        "brain_zones (массив из 3–4 строк вида «Зона (что она даёт/как проявляется)»),\n"
        "overload (массив из 2–3 точек психофизиологической перегрузки),\n"
        "adaptation (строка: стратегия адаптации, 2–3 предложения).\n\n"
        + STYLE_SAMPLE
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
        "Создай полную психофизиологическую модель по пяти разделам. Пиши на «вы», "
        "тёплым, живым, конкретным языком. Используй ровно эти заголовки:\n"
        "🧬 Образ жизни (абзац)\n"
        "🔁 Типичные привычки (список из 5–6 пунктов)\n"
        "⚠️ Возможные психофизиологические проблемы (список из 4 пунктов)\n"
        "🤝 Советы: как подружиться со своим мозгом (список из 4 советов)\n"
        "📚 Рекомендуемые книги (5 книг: автор — название, с короткой пометкой, чем полезна)\n"
        "Если выбрано несколько карточек, объедини их в один целостный портрет."
    )
    return ask_llm(prompt)


# ---------- интерфейс ----------
pwd = st.secrets.get("APP_PASSWORD")
if pwd and st.text_input("Пароль", type="password") != pwd:
    st.stop()

st.title("🧠 Профиль по персонажам")
st.caption(
    "Образы создаёт ИИ как метафорические психотипы, а не историческая справка. "
    "Это не диагностика и не медицинская информация."
)
st.info(
    "Введите 1–3 персонажей или публичных людей, с которыми вы себя ассоциируете. "
    "Если персонаж редкий, добавьте описание в скобках. "
    "Пример: Анна (интроверт, тревожная), Гоша (добрый, тихий лидер)"
)

characters = st.text_input("Персонажи")

if st.button("Создать описания", disabled=not characters.strip()):
    with st.spinner("Создаю описания..."):
        try:
            st.session_state.profiles = generate_profiles(characters)
            st.session_state.pop("result", None)
        except Exception as e:
            st.error(f"Не получилось: {e}")

profiles = st.session_state.get("profiles")
if profiles:
    for i, p in enumerate(profiles, 1):
        with st.expander(f"📄 Профиль {i}", expanded=True):
            st.markdown(f"**Психологический портрет**\n\n{p.get('portrait', '')}")
            zones = "\n".join(f"- {z}" for z in p.get("brain_zones", []))
            st.markdown(f"**Зоны мозга**\n\n{zones}")
            over = "\n".join(f"- {o}" for o in p.get("overload", []))
            st.markdown(f"**Точки перегрузки**\n\n{over}")
            st.markdown(f"**Стратегия адаптации**\n\n{p.get('adaptation', '')}")

    chosen = st.multiselect(
        "Какие описания вам подходят?",
        options=list(range(1, len(profiles) + 1)),
        format_func=lambda n: f"Профиль {n}",
    )
    if st.button("Получить рекомендации", disabled=not chosen):
        with st.spinner("Анализирую..."):
            try:
                st.session_state.result = analyze([profiles[n - 1] for n in chosen])
            except Exception as e:
                st.error(f"Не получилось: {e}")

if st.session_state.get("result"):
    st.subheader("🧠 Рекомендации")
    st.markdown(st.session_state.result)
