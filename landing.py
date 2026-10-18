"""Публичная главная страница. Не содержит логики тестирования."""
import base64
import html
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).parent / "assets"

def img(name, alt="", cls=""):
    p = ASSETS / name
    if not p.exists():
        return f'<div class="ob-missing">Ожидается файл assets/{html.escape(name)}</div>'
    ext = p.suffix.lower()
    mime = {".webp":"image/webp",".png":"image/png",".svg":"image/svg+xml"}[ext]
    data = base64.b64encode(p.read_bytes()).decode("ascii")
    return f'<img class="{cls}" src="data:{mime};base64,{data}" alt="{html.escape(alt)}" loading="lazy">'

CSS = """
<style>
html{scroll-behavior:smooth}
.stApp{background:#F6F4EF}
.block-container{max-width:1300px!important;padding-top:0.5rem!important}
.ob-page{font-family:Arial,sans-serif;color:#2B2A33}
.ob-page *{box-sizing:border-box}
.ob-page section{scroll-margin-top:30px}
.ob-nav{display:flex;align-items:center;gap:26px;flex-wrap:wrap;padding:19px 4%;position:relative;z-index:2}
.ob-logo{font:600 30px Georgia,serif;color:#6E5C8E;margin-right:auto}
.ob-nav a{font-size:15px;color:#2B2A33;text-decoration:none}
.ob-nav a:hover{text-decoration:underline}
.ob-hero{position:relative;background:#D6E7DE;border-radius:22px;overflow:hidden;min-height:560px}
.ob-hero-image{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center}
.ob-hero-content{position:relative;z-index:1;width:55%;padding:70px 0 75px 6%}
.ob-hero h1{font:500 clamp(35px,4.2vw,61px)/1.12 Georgia,serif!important;letter-spacing:-.035em;margin:0 0 25px}
.ob-hero p{font-size:19px;line-height:1.6;max-width:510px}
.ob-cta{display:inline-flex;gap:16px;align-items:center;background:#6E5C8E;color:white!important;text-decoration:none;padding:16px 25px;border-radius:30px;font-weight:600;margin-top:20px}
.ob-section{padding:70px 4% 15px}
.ob-section h2{font:500 clamp(29px,3.2vw,43px) Georgia,serif!important;margin:0 0 26px}
.ob-grid4{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:17px}
.ob-step,.ob-price{border-radius:20px;background:white;padding:24px}
.ob-step img{width:88px;height:88px;object-fit:contain}
.ob-step h3,.ob-price h3{font:500 22px Georgia,serif!important}
.ob-step p,.ob-price p{line-height:1.55;font-size:15px}
.ob-compat{margin-top:25px;background:#E6E0EE;border-radius:20px;padding:24px 30px}
.ob-compat h3{font:500 25px Georgia,serif!important;margin:0 0 15px}
.ob-compat-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.ob-example{display:grid;grid-template-columns:40% 1fr;gap:36px;align-items:center;background:white;border-radius:22px;padding:26px}
.ob-example img{width:100%;height:auto;max-height:350px;object-fit:contain}
.ob-example p{font-size:17px;line-height:1.6}
.ob-price-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}
.ob-price img{width:100%;max-height:240px;object-fit:contain}
.ob-price strong{font-size:29px;color:#6E5C8E}
.ob-two{display:grid;grid-template-columns:1fr 1fr;gap:38px}
.ob-about{position:relative;min-height:360px}
.ob-about img{width:160px;float:right;margin:10px}
.ob-about p{font-size:17px;line-height:1.7}
.ob-footer{margin-top:75px;padding:35px 4%;border-top:1px solid #D6D0D9;font-size:14px;line-height:1.8}
.ob-footer a{color:#6E5C8E;margin-right:20px}
.ob-missing{padding:20px;border:1px dashed #B9A9D6;border-radius:10px}
@media(max-width:900px){.ob-grid4{grid-template-columns:repeat(2,1fr)}.ob-hero-content{width:68%}.ob-two{grid-template-columns:1fr}}
@media(max-width:650px){.ob-nav{gap:12px}.ob-logo{width:100%}.ob-nav a{font-size:13px}.ob-hero{min-height:620px}.ob-hero-image{object-position:65% center;opacity:.45}.ob-hero-content{width:100%;padding:45px 7%}.ob-hero p{font-size:16px}.ob-grid4,.ob-price-grid,.ob-compat-grid,.ob-example{grid-template-columns:1fr}.ob-section{padding:45px 3% 8px}.ob-example{gap:12px}}
</style>
"""

def render_landing(price_profile: int, price_full: int):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ob-page">
      <nav class="ob-nav" aria-label="Навигация">
        <span class="ob-logo">Образы</span>
        <a href="#how">Как это работает</a>
        <a href="#example">Примеры</a>
        <a href="#prices">Тарифы</a>
        <a href="#faq">Вопросы</a>
      </nav>
      <header class="ob-hero">
        {img("header.webp", "Девушка среди холмов", "ob-hero-image")}
        <div class="ob-hero-content">
          <h1>Узнайте себя через образы, которые вам близки</h1>
          <p>Необычный способ исследовать свою личность,<br>
          увидеть привычные реакции и понять,<br>
          как вы взаимодействуете с другими</p>
          <a class="ob-cta" href="?view=research">Начать исследование <span aria-hidden="true">→</span></a>
        </div>
      </header>
      <section class="ob-section" id="how">
        <h2>Как это работает?</h2>
        <div class="ob-grid4">
          <article class="ob-step">{img("01_obraz.svg", "Первый этап")}<h3>1. Назовите близкие образы</h3><p>Напишите имена персонажей, героев или известных людей, которые вам близки.</p></article>
          <article class="ob-step">{img("02_profili.svg", "Второй этап")}<h3>2. Получите описания профилей</h3><p>Познакомьтесь с несколькими обезличенными описаниями.</p></article>
          <article class="ob-step">{img("03_vybor.svg", "Третий этап")}<h3>3. Отметьте своё</h3><p>Выберите один или несколько подходящих профилей.</p></article>
          <article class="ob-step">{img("04_razbor.svg", "Четвёртый этап")}<h3>4. Получите разбор</h3><p>Узнайте свои сильные и слабые стороны, зоны перегрузки и рекомендации.</p></article>
        </div>
        <div class="ob-compat">
          <p>Дополнительно можно пройти тестирование на совместимость профилей.</p>
          <h3>Совместимость — 2 этапа</h3>
          <div class="ob-compat-grid">
            <div><b>1. Загрузите описания профилей</b><p>Предоставьте два профиля для анализа.</p></div>
            <div><b>2. Получите разбор</b><p>Узнайте сильные стороны вашего союза, возможные противоречия, сценарии развития отношений и способы достижения взаимопонимания.</p></div>
          </div>
        </div>
      </section>
      <section class="ob-section" id="example">
        <h2>Пример результата «Профиль»</h2>
        <div class="ob-example">
          {img("primer_profile.webp", "Иллюстрация профиля")}
          <div><p>В примере разбора представлены особенности образа жизни, привычные реакции, возможные перегрузки и рекомендации.</p></div>
        </div>
      </section>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Посмотреть полный пример — Профиль"):
        st.info("Полный текст примера профиля пока не предоставлен. Добавим утверждённый пример без вымышленных результатов.")
    st.markdown(f"""
    <div class="ob-page">
      <section class="ob-section" id="compat-example">
        <h2>Пример результата «Совместимость»</h2>
        <div class="ob-example">
          {img("primer_sovmestimost.webp", "Иллюстрация совместимости")}
          <div><p>Пример показывает, как анализируются сильные стороны союза, возможные противоречия и пути взаимопонимания.</p></div>
        </div>
      </section>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Посмотреть полный пример — Совместимость"):
        st.info("Полный текст примера совместимости пока не предоставлен. Добавим утверждённый пример.")
    st.markdown(f"""
    <div class="ob-page">
      <section class="ob-section" id="prices">
        <h2>Тарифы</h2>
        <div class="ob-price-grid">
          <article class="ob-price">{img("cena_profile.webp", "Тариф Профиль")}<h3>Профиль</h3><p>Разбор выбранных образов: привычки, реакции, перегрузки, рекомендации и книги.</p><strong>{price_profile} ₽</strong></article>
          <article class="ob-price">{img("cena_sovmestimost.webp", "Тариф Профиль и совместимость")}<h3>Профиль + совместимость</h3><p>Полный профиль и анализ взаимодействия двух людей.</p><strong>{price_full} ₽</strong></article>
        </div>
      </section>
      <div class="ob-two">
        <section class="ob-section ob-about" id="about">
          <h2>Почему именно образы?</h2>
          {img("cvetok.png", "Цветок")}
          <p>Иногда легче узнать собственные черты в знакомом персонаже, чем описать себя напрямую. Образы становятся отправной точкой для размышлений о привычках, реакциях и отношениях.</p>
          <p>Это метафорическое исследование для саморефлексии, а не психологическая или медицинская диагностика.</p>
        </section>
        <section class="ob-section" id="faq"><h2>Частые вопросы</h2></section>
      </div>
    </div>
    """, unsafe_allow_html=True)
    with st.expander("Это психологический тест или терапия?"):
        st.write("Нет. Это метафорическое исследование для саморефлексии, а не диагностика или медицинская консультация.")
    with st.expander("Будут ли известны персонажи по карточкам?"):
        st.write("Имена персонажей в карточках не показываются, а сами карточки перемешиваются.")
    with st.expander("Можно ли сохранить результат?"):
        st.write("Да, результаты можно скачать в формате TXT.")
    with st.expander("Списываются ли деньги при тестировании?"):
        st.write("Нет. В текущей тестовой версии оплата демонстрационная.")
    st.markdown('<div class="ob-page"><footer class="ob-footer"><strong>Образы</strong> · 18+<p>ИП Фофанова — реквизиты и контакты будут добавлены после предоставления точных данных.</p></footer></div>', unsafe_allow_html=True)
    docs = [("Оферта","oferta.pdf"),("Политика конфиденциальности","privacy.pdf")]
    available = [(label, ASSETS / filename) for label,filename in docs if (ASSETS / filename).exists()]
    if available:
        cols=st.columns(len(available))
        for col,(label,path) in zip(cols,available):
            with col:
                st.download_button(f"Скачать: {label}",path.read_bytes(),file_name=path.name,mime="application/pdf")
