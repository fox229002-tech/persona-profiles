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

/* Reference composition */
.block-container{max-width:1450px!important;padding-left:2rem!important;padding-right:2rem!important}
.ob-page{max-width:1360px;margin:auto}
.ob-hero{border-radius:0;min-height:0;aspect-ratio:2.15/1}
.ob-hero-content{padding:6% 0 4% 7%;width:53%}
.ob-hero h1{font-size:clamp(33px,4vw,59px)!important;line-height:1.1!important}
.ob-section{padding:46px 3% 12px}
.ob-section h2{font-weight:600!important}
.ob-grid4{gap:25px}
.ob-step{background:transparent;border-radius:0;padding:0 6px}
.ob-step img{width:75px;height:75px}
.ob-step h3{font-size:20px!important;font-weight:600!important}
.ob-compat{margin-top:25px}
.ob-example{grid-template-columns:32% 1fr 28%;background:linear-gradient(115deg,#DCEBE2,#F0EAF1);gap:20px;padding:22px}
.ob-example img{max-height:260px;border-radius:15px}
.ob-example h3{font:600 24px Georgia,serif!important}
.ob-example aside{background:#e6f0e9;border-radius:17px;padding:18px}
.ob-example aside ul{padding-left:20px;line-height:1.7}
.ob-example-compat{background:linear-gradient(115deg,#E5EDE7,#E9E1F2)}
.ob-price{position:relative;overflow:hidden;min-height:290px;padding:28px 34px;display:flex;flex-direction:column;align-items:flex-start;background:#dcebe2}
.ob-price:nth-child(2){background:#e8dff1}
.ob-price img{position:absolute;inset:0;width:100%;height:100%;max-height:none;object-fit:cover;z-index:0}
.ob-price h3,.ob-price p,.ob-price strong,.ob-price a{position:relative;z-index:1;max-width:67%}
.ob-price h3{margin:0 0 12px;font-size:25px!important}
.ob-price p{margin:0}
.ob-price strong{margin-top:auto}
.ob-price a{display:inline-block;margin-top:12px;padding:8px 24px;background:#789a8a;color:white!important;text-decoration:none;border-radius:22px}
.ob-price:nth-child(2) a{background:#6E5C8E}
.ob-two{gap:45px;align-items:start}
.ob-two .ob-section{padding-top:48px}
.ob-about{min-height:0}
.ob-about img{width:140px}
.ob-faq details,.ob-example details{border-bottom:1px solid #d8d1da;padding:12px 0}
.ob-faq summary,.ob-example summary{cursor:pointer;font-weight:600}
.ob-faq details p,.ob-example details p{font-size:15px;line-height:1.6}
.ob-footer{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:15px;background:#eee9e5;padding:25px 3%;border:0}
@media(max-width:900px){.ob-hero{aspect-ratio:auto;min-height:470px}.ob-example{grid-template-columns:35% 1fr}.ob-example aside{grid-column:1/-1}}
@media(max-width:650px){.block-container{padding-left:1rem!important;padding-right:1rem!important}.ob-hero{min-height:590px}.ob-hero-content{width:100%;padding:45px 7%}.ob-hero-image{opacity:.5}.ob-grid4{grid-template-columns:repeat(2,1fr)}.ob-example{grid-template-columns:1fr}.ob-example aside{grid-column:auto}.ob-two{grid-template-columns:1fr}.ob-price h3,.ob-price p,.ob-price strong,.ob-price a{max-width:75%}}

/* Header navigation: positioned inside hero, not above it */
.ob-hero{position:relative}
.ob-hero .ob-nav{position:absolute;top:0;left:0;right:0;z-index:5;display:flex;align-items:center;gap:10px;padding:20px 4%;flex-wrap:nowrap}
.ob-hero .ob-logo{margin-right:auto;color:#5E4A7B;font:600 29px Georgia,serif;white-space:nowrap}
.ob-hero .ob-nav a{display:inline-flex;align-items:center;justify-content:center;white-space:nowrap;text-decoration:none!important;font-size:14px;font-weight:600;color:#3B3445;background:rgba(246,244,239,.76);border:1px solid rgba(110,92,142,.15);border-radius:999px;padding:10px 17px;transition:background .18s ease,transform .18s ease}
.ob-hero .ob-nav a:hover{background:#E9DFF0;color:#5E4A7B;text-decoration:none!important;transform:translateY(-1px)}
.ob-hero .ob-nav a:focus-visible{outline:3px solid #6E5C8E;outline-offset:3px}
.ob-hero .ob-hero-content{padding-top:11%}
@media(max-width:900px){.ob-hero .ob-nav{gap:7px;padding:14px 3%}.ob-hero .ob-nav a{padding:8px 10px;font-size:12px}.ob-hero .ob-logo{font-size:24px}.ob-hero .ob-hero-content{padding-top:100px}}
@media(max-width:650px){.ob-hero .ob-nav{position:relative;flex-wrap:wrap;justify-content:center;padding:14px 4%;background:rgba(214,231,222,.88)}.ob-hero .ob-logo{width:100%;text-align:center;margin:0 0 5px}.ob-hero .ob-nav a{font-size:12px}.ob-hero .ob-hero-content{padding-top:40px}.ob-hero{min-height:640px}}

/* Header refinement: shared left edge, left-aligned navigation, milk-green buttons */
.ob-hero .ob-nav{justify-content:flex-start;gap:12px;padding:18px 4%}
.ob-hero .ob-logo{font-size:20px!important;margin-right:34px!important;flex:none;width:auto}
.ob-hero .ob-nav a{font-size:18px!important;padding:11px 17px!important;background:#d9e6d8!important;border-color:#d9e6d8!important;font-weight:600}
.ob-hero .ob-nav a:hover{background:#c5d9c9!important;border-color:#b6cfbe!important}
.ob-hero .ob-hero-content{padding-left:4%!important;width:55%}
.ob-hero .ob-cta{font-size:20px!important;padding:19px 31px!important;gap:21px!important;border-radius:40px!important;margin-top:37px!important;text-decoration:none!important}
@media(max-width:1100px){.ob-hero .ob-nav{gap:7px}.ob-hero .ob-logo{margin-right:15px!important}.ob-hero .ob-nav a{font-size:15px!important;padding:9px 12px!important}.ob-hero .ob-cta{font-size:17px!important;padding:16px 25px!important}}
@media(max-width:650px){.ob-hero .ob-nav{justify-content:flex-start;gap:7px;padding:12px 4%}.ob-hero .ob-logo{width:100%;text-align:left;margin:0!important}.ob-hero .ob-nav a{font-size:13px!important;padding:8px 10px!important}.ob-hero .ob-hero-content{padding-left:4%!important;width:100%}.ob-hero .ob-cta{font-size:17px!important;padding:16px 23px!important;margin-top:35px!important}}

/* Hero final vertical alignment */
@media(min-width:901px){
  .ob-hero .ob-nav{top:15px!important}
  .ob-hero .ob-hero-content{padding-top:calc(11% - 35px)!important}
  .ob-hero .ob-cta{margin-top:72px!important}
}
@media(min-width:651px) and (max-width:900px){
  .ob-hero .ob-nav{top:12px!important}
  .ob-hero .ob-hero-content{padding-top:68px!important}
}

/* Lift only heading and description; keep CTA on the cream foreground */
@media(min-width:901px){.ob-hero .ob-hero-content h1,.ob-hero .ob-hero-content>p{position:relative;top:-20px}}

/* Section 2: one cream palette, botanical backdrop and three compatibility steps */
#how{background:#F6F4EF}
#how .ob-compat-new{position:relative;isolation:isolate;overflow:hidden;background:#F6F4EF;border-radius:24px;margin-top:38px;padding:35px 38px 58px;min-height:390px}
#how .ob-compat-art{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:center bottom;z-index:-1;pointer-events:none}
#how .ob-compat-body{position:relative;z-index:1;max-width:1050px;margin:0 auto}
#how .ob-compat-intro{font-size:16px;line-height:1.5;margin:0 0 12px;color:#484450}
#how .ob-compat-new h3{font:600 clamp(30px,3.2vw,44px)/1.15 Georgia,serif!important;margin:0 0 16px;color:#2B2A33}
#how .ob-compat-lead{max-width:900px;font-size:18px;line-height:1.5;color:#484450;margin:0 0 38px}
#how .ob-compat-steps{display:grid;grid-template-columns:1.25fr 1fr 0.9fr;gap:30px;align-items:start}
#how .ob-compat-step{display:flex;align-items:flex-start;gap:16px;min-width:0}
#how .ob-compat-number{display:inline-flex;flex:0 0 48px;width:48px;height:48px;border-radius:50%;align-items:center;justify-content:center;background:#6E9989;color:white;font:600 23px Georgia,serif}
#how .ob-compat-step p{margin:7px 0 0;font:600 19px/1.35 Georgia,serif;color:#2B2A33}
@media(max-width:900px){#how .ob-compat-new{padding:28px 25px 50px}#how .ob-compat-steps{gap:16px}#how .ob-compat-step{gap:10px}#how .ob-compat-number{flex-basis:40px;width:40px;height:40px;font-size:20px}#how .ob-compat-step p{font-size:16px}}
@media(max-width:650px){#how .ob-compat-new{margin-top:28px;padding:24px 16px 75px;min-height:0}#how .ob-compat-art{object-fit:cover;opacity:.55}#how .ob-compat-lead{font-size:16px;margin-bottom:25px}#how .ob-compat-steps{grid-template-columns:1fr;gap:17px}#how .ob-compat-step p{font-size:17px}}

/* Approved section-two layout: numbered icon row and raised, centered compatibility content */
#how .ob-step{position:relative}
#how .ob-step-number{display:inline-flex;align-items:center;justify-content:center;width:46px;height:46px;border-radius:50%;background:#6e9989;color:#fff;font:600 23px Georgia,serif;vertical-align:middle;margin-right:9px}
#how .ob-step img{display:block;margin-left:63px;margin-bottom:14px}
#how .ob-step h3{display:flex;align-items:flex-start;gap:12px;line-height:1.2!important}
#how .ob-step-number{flex:0 0 46px;margin:-5px 0 0}
#how .ob-step p{margin-left:58px}
#how .ob-compat-new{padding:30px 32px 145px!important;min-height:405px!important;margin-top:35px!important}
#how .ob-compat-new .ob-compat-art{z-index:0!important;object-position:center bottom}
#how .ob-compat-new .ob-compat-body{max-width:900px!important;margin:0 auto!important;text-align:left;z-index:1!important}
#how .ob-compat-new .ob-compat-intro{margin-bottom:8px!important}
#how .ob-compat-new h3{margin-bottom:10px!important}
#how .ob-compat-new .ob-compat-lead{max-width:880px;margin-bottom:28px!important}
#how .ob-compat-new .ob-compat-steps{grid-template-columns:1.35fr 1fr .8fr;gap:24px}
#how .ob-compat-new .ob-compat-step{align-items:flex-start;gap:14px}
#how .ob-compat-new .ob-compat-step p{margin:5px 0 0!important}
@media(max-width:900px){#how .ob-step img{margin-left:0}#how .ob-step p{margin-left:0}#how .ob-compat-new{padding-bottom:110px!important}}
@media(max-width:650px){#how .ob-step h3{gap:8px}#how .ob-step-number{flex-basis:34px;width:34px;height:34px;font-size:18px}#how .ob-compat-new{padding:24px 20px 95px!important}#how .ob-compat-new .ob-compat-steps{grid-template-columns:1fr;gap:14px}#how .ob-compat-new .ob-compat-art{opacity:.35}}

/* Step layout: number and illustration share a row, all copy left aligned */
#how .ob-grid4{gap:34px!important;align-items:start}
#how .ob-step{padding:0!important}
#how .ob-step-top{display:flex;align-items:center;gap:22px;height:90px;margin-bottom:12px}
#how .ob-step-top .ob-step-number{display:flex;align-items:center;justify-content:center;flex:0 0 52px;width:52px;height:52px;margin:0!important;background:#6e9989;color:#fff;border-radius:50%;font:600 25px Georgia,serif}
#how .ob-step-top img{display:block;width:80px;height:80px;margin:0!important;object-fit:contain}
#how .ob-step h3{display:block!important;margin:0 0 12px!important;font:600 22px/1.2 Georgia,serif!important;min-height:55px}
#how .ob-step p{margin:0!important;font-size:16px;line-height:1.55;max-width:265px}
#how .ob-compat-new{padding-bottom:165px!important}
@media(max-width:900px){#how .ob-grid4{gap:22px!important}#how .ob-step-top{gap:12px}#how .ob-step h3{font-size:19px!important}}
@media(max-width:650px){#how .ob-step-top{height:72px}#how .ob-step-top img{width:60px;height:60px}#how .ob-step-top .ob-step-number{width:40px;height:40px;flex-basis:40px;font-size:20px}#how .ob-step h3{min-height:0}}

/* Keep the approved three-line hero headline stable at desktop zoom levels. */
@media(min-width:901px){
 .ob-hero .ob-hero-content{width:64%!important}
 .ob-hero h1{font-size:clamp(33px,3.65vw,59px)!important;white-space:nowrap}
 .ob-hero .ob-title-line{white-space:nowrap}
}
@media(max-width:900px){.ob-hero .ob-title-break{display:none}.ob-hero h1{white-space:normal}}

/* Desktop hero CTA is anchored to the illustration, not to text height.
   Browser zoom may reflow the heading, but the CTA stays at the same
   proportional distance from the bottom and left edges. */
@media(min-width:901px){
 .ob-hero .ob-hero-content{position:static!important}
 .ob-hero .ob-cta{
  position:absolute!important;
  left:4%!important;
  bottom:1.5%!important;
  margin:0!important;
  z-index:6;
 }
}

/* Keep botanical artwork at its native aspect ratio: zoom and text
   wrapping must not make the flowers grow to fill a taller card. */
#how .ob-compat-new .ob-compat-art{
 top:auto!important;
 bottom:0!important;
 left:0!important;
 right:auto!important;
 width:100%!important;
 height:auto!important;
 max-width:none!important;
 object-fit:contain!important;
 object-position:center bottom!important;
}
@media(max-width:650px){
 #how .ob-compat-new .ob-compat-art{opacity:.35}
}

/* Responsive composition: align all compatibility copy within one
   proportional inner column, never shift it with a fixed pixel transform. */
#how .ob-compat-new .ob-compat-body{
 transform:none!important;
 width:100%;
 max-width:none!important;
 margin:0!important;
 padding-left:19%;
 padding-right:3%;
 box-sizing:border-box;
}
#how .ob-compat-new .ob-compat-steps{
 grid-template-columns:minmax(0,1.35fr) minmax(0,1fr) minmax(0,.8fr);
}
@media(min-width:901px){
 #how .ob-step h3{font-size:27px!important;line-height:1.16!important;min-height:66px}
}
@media(min-width:651px) and (max-width:900px){
 #how .ob-step h3{font-size:23px!important;line-height:1.2!important}
 #how .ob-compat-new .ob-compat-body{padding-left:13%;padding-right:2%}
}
@media(max-width:650px){
 #how .ob-compat-new .ob-compat-body{padding-left:0;padding-right:0}
 #how .ob-compat-new .ob-compat-steps{grid-template-columns:1fr}
}
/* Step layout: intrinsic heading heights; CSS subgrid aligns descriptions
   to the tallest heading in each row without fixed-height overlap. */
#how .ob-grid4{grid-template-rows:repeat(3,auto);row-gap:0!important;align-items:stretch}
#how .ob-step{
 display:grid!important;
 grid-template-rows:subgrid;
 grid-row:span 3;
 align-content:start;
 row-gap:0;
}
#how .ob-step h3{
 height:auto!important;
 min-height:0!important;
 margin:0!important;
 overflow:visible!important;
}
#how .ob-step p{margin:14px 0 0!important}
@media(max-width:900px){
 #how .ob-grid4{grid-template-rows:repeat(6,auto);row-gap:0!important}
}
/* Compatibility: protect the botanical edges and give all three steps
   readable columns across desktop browser zoom levels. */
@media(min-width:901px){
 #how .ob-compat-new .ob-compat-body{
  padding-left:20%!important;
  padding-right:11%!important;
  width:100%!important;
  margin:0!important;
 }
 #how .ob-compat-new .ob-compat-steps{
  grid-template-columns:minmax(0,1.5fr) minmax(0,1fr) minmax(0,1fr)!important;
  gap:18px!important;
 }
 #how .ob-compat-new .ob-compat-step{gap:10px!important}
 #how .ob-compat-new .ob-compat-number{flex:0 0 44px;width:44px;height:44px}
 #how .ob-compat-new .ob-compat-step p{
  font-size:clamp(16px,1.3vw,19px)!important;
  overflow-wrap:normal!important;
  word-break:normal!important;
  hyphens:none!important;
 }
}
@media(min-width:901px) and (max-width:1150px){
 #how .ob-compat-new .ob-compat-steps{
  grid-template-columns:minmax(0,1.25fr) minmax(0,1fr)!important;
  row-gap:18px!important;
 }
 #how .ob-compat-new .ob-compat-step:last-child{grid-column:2}
}

/* Unified result-preview cards. Botanical artwork is decorative and never
   determines the text layout. */
.ob-example,.ob-example-compat{
 position:relative;
 isolation:isolate;
 overflow:hidden;
 background:#E5EFE9!important;
 border-radius:24px;
 grid-template-columns:minmax(0,29%) minmax(0,1fr) minmax(0,28%);
 gap:clamp(16px,2.5vw,32px);
 padding:clamp(20px,2.4vw,34px);
 align-items:center;
}
.ob-example > img:first-child{
 display:block;width:100%;height:auto;aspect-ratio:1/1;
 object-fit:cover;max-height:none;border-radius:22px;
 position:relative;z-index:1;
}
.ob-example .ob-example-copy{position:relative;z-index:2}
.ob-example .ob-example-copy h3{margin:0 0 14px!important}
.ob-example .ob-example-copy p{margin:0;line-height:1.55}
.ob-example aside{
 position:relative;z-index:2;
 background:rgba(246,244,239,.88)!important;
 padding:20px 20px 20px 22px;
 border-radius:18px;
}
.ob-example aside ul{margin-bottom:0}
.ob-example .ob-example-botanical{
 position:absolute!important;z-index:1!important;
 width:clamp(360px,46%,650px)!important;
 height:100%!important;max-height:none!important;
 object-fit:cover!important;
 object-position:right center!important;
 right:0;bottom:0;
 border-radius:0!important;
 pointer-events:none;
 opacity:1;
 -webkit-mask-image:linear-gradient(to right,transparent 0%,transparent 65%,#000 94%);
 mask-image:linear-gradient(to right,transparent 0%,transparent 65%,#000 94%);
}
@media(min-width:901px){
 .ob-example aside{margin-right:clamp(22px,3vw,42px)}
}
@media(max-width:900px){
 .ob-example,.ob-example-compat{grid-template-columns:minmax(0,35%) minmax(0,1fr)}
 .ob-example aside{grid-column:2}
 .ob-example .ob-example-botanical{width:45%!important;opacity:.65}
}
@media(max-width:650px){
 .ob-example,.ob-example-compat{grid-template-columns:minmax(0,1fr);gap:18px}
 .ob-example > img:first-child{width:min(100%,330px);margin-inline:auto}
 .ob-example aside{grid-column:auto;margin-right:0}
 .ob-example .ob-example-botanical{width:75%!important;right:0!important;bottom:0!important;opacity:.35}
}

/* Result previews: stronger hierarchy, checked benefits and in-card disclosure. */
.ob-example .ob-example-copy h3{
 font-size:clamp(28px,2.25vw,36px)!important;
 line-height:1.16!important;
 margin:0 0 16px!important;
}
.ob-example .ob-example-copy p{font-size:clamp(17px,1.2vw,20px)!important;line-height:1.5!important}
.ob-example aside b{font-size:clamp(18px,1.3vw,21px)!important}
.ob-example aside ul{list-style:none!important;padding:0!important;margin:14px 0 0!important}
.ob-example aside li{
 position:relative;
 padding-left:35px;
 margin:12px 0;
 font-size:clamp(15px,1.1vw,18px);
 line-height:1.4;
}
.ob-example aside li::before{
 content:"✓";
 position:absolute;left:0;top:0;
 width:24px;height:24px;
 display:grid;place-items:center;
 border-radius:50%;
 background:#729E8D;color:white;
 font:700 16px Arial,sans-serif;
}
.ob-example .ob-example-details{border:0!important;padding:0!important;margin-top:22px;position:relative;z-index:3}
.ob-example .ob-example-details summary{
 display:inline-flex;align-items:center;justify-content:center;
 background:#6E5C8E;color:white!important;
 border-radius:999px;
 padding:15px 24px;
 font:600 16px Arial,sans-serif!important;
 list-style:none;cursor:pointer;
 transition:background .15s ease;
}
.ob-example .ob-example-details summary::-webkit-details-marker{display:none}
.ob-example .ob-example-details summary::after{content:" →";margin-left:12px}
.ob-example .ob-example-details[open] summary::after{content:" ↑"}
.ob-example .ob-example-details summary:hover{background:#594877}
.ob-example .ob-example-details .ob-example-placeholder{
 margin-top:16px;
 padding:15px 18px;
 border-radius:12px;
 background:rgba(246,244,239,.93);
 font-size:15px;line-height:1.5;
}
@media(max-width:650px){
 .ob-example .ob-example-copy h3{font-size:28px!important}
 .ob-example .ob-example-details summary{width:100%;padding:15px}
}

/* Final editorial layout for result cards */
#example h2,#compat-example h2{font-size:clamp(30px,2.85vw,43px)!important;line-height:1.15!important;margin-bottom:30px!important}
.ob-example,.ob-example-compat{align-items:stretch!important}
.ob-example .ob-example-copy{display:flex;flex-direction:column;justify-content:center;min-width:0}
.ob-example .ob-example-copy h3{margin-bottom:8px!important}
.ob-example .ob-example-tagline{font:italic 500 clamp(17px,1.25vw,21px) Georgia,serif;color:#6E5C8E;margin-bottom:22px}
.ob-example .ob-example-copy p{margin-bottom:0!important}
.ob-example .ob-example-details{margin-top:26px!important}
.ob-example aside{align-self:center;background:transparent!important;border:0!important;box-shadow:none!important;padding:12px 12px 12px 0!important;margin-right:clamp(34px,4vw,62px)!important}
.ob-example aside b{font-size:clamp(20px,1.5vw,24px)!important}
.ob-example aside li{margin:15px 0!important}
.ob-example .ob-example-botanical{width:clamp(280px,38%,560px)!important;-webkit-mask-image:linear-gradient(to right,transparent 0%,transparent 77%,#000 98%)!important;mask-image:linear-gradient(to right,transparent 0%,transparent 77%,#000 98%)!important}
@media(max-width:900px){.ob-example aside{margin-right:40px!important}.ob-example .ob-example-botanical{width:40%!important;opacity:.5!important}}
@media(max-width:650px){#example h2,#compat-example h2{font-size:30px!important}.ob-example aside{margin-right:0!important;padding:8px 0!important}.ob-example .ob-example-botanical{width:65%!important;opacity:.2!important}.ob-example .ob-example-tagline{margin-bottom:16px}}

/* Align card headings and give benefit rows more breathing room. */
@media(min-width:901px){
 .ob-example .ob-example-copy{justify-content:flex-start!important;padding-top:clamp(12px,1.5vw,24px)!important}
 .ob-example aside{align-self:start!important;padding-top:clamp(12px,1.5vw,24px)!important}
}
.ob-example .ob-example-copy h3,.ob-example aside b{
 font-size:clamp(26px,2.1vw,34px)!important;
 line-height:1.18!important;
}
.ob-example aside li{margin:20px 0!important}
@media(max-width:900px){
 .ob-example .ob-example-copy h3,.ob-example aside b{font-size:clamp(24px,3vw,30px)!important}
 .ob-example aside li{margin:16px 0!important}
}

/* Result card heading baseline: identical typography and vertical start. */
@media(min-width:901px){
 .ob-example .ob-example-copy{
  justify-content:flex-start!important;
  padding-top:20px!important;
 }
 .ob-example aside{
  align-self:start!important;
  padding:20px 12px 12px 0!important;
 }
}
.ob-example .ob-example-copy h3,
.ob-example aside > b{
 display:block!important;
 font-family:Georgia,serif!important;
 font-weight:600!important;
 font-style:normal!important;
 font-size:clamp(26px,2.1vw,34px)!important;
 line-height:1.18!important;
 letter-spacing:normal!important;
}

/* Responsive result cards: headings share one top baseline and right title has room. */
@media(min-width:901px){
 .ob-example,.ob-example-compat{
  grid-template-columns:minmax(0,29%) minmax(0,1fr) minmax(265px,30%)!important;
  align-items:center!important;
 }
 .ob-example .ob-example-copy{
  align-self:start!important;
  padding-top:0!important;
 }
 .ob-example aside{
  align-self:start!important;
  margin-right:0!important;
  padding:0!important;
  min-width:0!important;
 }
 .ob-example .ob-example-copy h3,
 .ob-example aside > b{
  font:600 clamp(24px,1.9vw,31px)/1.2 Georgia,serif!important;
  margin:0 0 18px!important;
  padding:0!important;
 }
 .ob-example aside > b{white-space:nowrap!important}
 .ob-example aside ul{margin-top:16px!important}
 /* Reserve the ornamental right edge without changing the heading baseline. */
 .ob-example aside ul{max-width:calc(100% - clamp(48px,5vw,90px))!important}
 .ob-example aside li{overflow-wrap:break-word}
}

/* Tariff cards: consistent headings, uncropped centered artwork, prominent CTAs. */
.ob-price{min-height:320px!important;padding:34px 38px!important}
.ob-price img{object-fit:cover!important;object-position:right center!important}
.ob-price h3{font:500 clamp(30px,2.7vw,38px)/1.15 Georgia,serif!important;max-width:78%!important;min-height:2.3em;margin:0 0 20px!important}
.ob-price p{font-size:17px!important;line-height:1.55!important}
.ob-price a{display:inline-flex!important;align-items:center;justify-content:center;font-size:19px!important;font-weight:600!important;padding:15px 34px!important;border-radius:32px!important;margin-top:16px!important}
@media(max-width:700px){
 .ob-price{padding:26px!important;min-height:300px!important}
 .ob-price h3{font-size:29px!important;min-height:0;max-width:80%!important}
 .ob-price p{font-size:15px!important}
 .ob-price a{font-size:17px!important;padding:13px 28px!important}
}

/* Tariffs: matched vertical rhythm, readable copy, and checkmark lists */
.ob-price{isolation:isolate}
.ob-price img{object-fit:cover!important;object-position:right bottom!important}
.ob-price h3{margin-bottom:4px!important;min-height:2.3em!important;max-width:62%!important}
.ob-price .ob-price-sub{position:relative;z-index:1;color:#6E5C8E;font:italic 21px/1.3 Georgia,serif;max-width:58%;margin:0 0 22px}
.ob-price .ob-price-list{position:relative;z-index:1;list-style:none;padding:0;margin:0 0 16px;max-width:55%;width:55%;font-size:17px;line-height:1.4}
.ob-price .ob-price-list li{display:flex;align-items:flex-start;gap:10px;margin:0 0 11px}
.ob-price .ob-price-list li:before{content:"✓";display:inline-flex;flex:none;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;background:#709f8e;color:#fff;font:bold 16px Arial,sans-serif}
.ob-price strong{font-family:Georgia,serif!important;font-weight:700!important;font-size:36px!important;max-width:58%!important}
.ob-price a{max-width:58%!important}
@media(max-width:900px){
 .ob-price .ob-price-list{max-width:62%;width:62%;font-size:15px}
 .ob-price h3{font-size:clamp(25px,3vw,34px)!important}
 .ob-price .ob-price-sub{font-size:18px}
}
@media(max-width:650px){
 .ob-price .ob-price-list{max-width:70%;width:70%;font-size:14px}
 .ob-price h3{max-width:75%!important;min-height:2.3em!important}
 .ob-price .ob-price-sub{max-width:70%}
}

/* Compact tariff cards: keep artwork and prices at the original height */
.ob-price{min-height:290px!important;padding:28px 34px!important}
.ob-price h3{font-size:clamp(26px,2.3vw,34px)!important;line-height:1.15!important;min-height:2.3em!important;max-width:70%!important;margin:0 0 10px!important;overflow-wrap:normal!important;word-break:normal!important;hyphens:none!important}
.ob-price .ob-price-list{font-size:15px!important;line-height:1.3!important;max-width:54%!important;width:54%!important;margin:0 0 8px!important}
.ob-price .ob-price-list li{gap:8px!important;margin:0 0 6px!important}
.ob-price .ob-price-list li:before{width:18px!important;height:18px!important;font-size:13px!important}
.ob-price strong{font-size:32px!important}
.ob-price a{padding:11px 28px!important;font-size:18px!important;margin-top:9px!important}
@media(max-width:700px){
 .ob-price{min-height:290px!important;padding:24px!important}
 .ob-price h3{font-size:clamp(24px,5vw,30px)!important;max-width:75%!important}
 .ob-price .ob-price-list{font-size:14px!important;max-width:63%!important;width:63%!important}
}

/* Final compact tariff layout: no bullets and no stretched vertical gaps */
.ob-price{height:auto!important;min-height:0!important;aspect-ratio:1.7/1;padding:25px 32px!important;justify-content:flex-start}
.ob-price h3{font-size:clamp(27px,2.5vw,35px)!important;min-height:0!important;margin:0 0 20px!important;max-width:68%!important}
.ob-price .ob-price-lines{position:relative;z-index:1;font-size:16px!important;line-height:1.5!important;max-width:59%!important;margin:0 0 12px!important}
.ob-price strong{margin-top:auto!important;font-size:32px!important}
.ob-price a{margin-top:9px!important;padding:11px 28px!important}
@media(max-width:700px){
 .ob-price{aspect-ratio:auto;min-height:330px!important;padding:24px!important}
 .ob-price h3{font-size:29px!important;max-width:75%!important}
 .ob-price .ob-price-lines{font-size:14px!important;max-width:65%!important}
}

/* Tariffs: group heading, description, price and button vertically */
.ob-price{justify-content:flex-start!important}
.ob-price h3{margin-bottom:18px!important}
.ob-price .ob-price-lines{margin-bottom:14px!important}
.ob-price strong{margin-top:0!important}
.ob-price a{margin-top:10px!important}

/* Tariffs: keep the copy, price and CTA together below the heading */
.ob-price{justify-content:flex-start!important}
.ob-price h3{margin-bottom:15px!important}
.ob-price .ob-price-lines{margin-top:0!important;margin-bottom:12px!important}
.ob-price strong{margin-top:0!important}
.ob-price a{margin-top:10px!important}

/* Tariff cards: prevent price and CTA from escaping the fixed-ratio artwork */
.ob-price{display:flex!important;flex-direction:column!important;justify-content:flex-start!important;gap:0!important;aspect-ratio:1.7/1!important;box-sizing:border-box!important}
.ob-price h3{flex:0 0 auto!important;margin:0 0 14px!important}
.ob-price .ob-price-lines{flex:0 0 auto!important;margin:0 0 12px!important}
.ob-price strong{display:block!important;flex:0 0 auto!important;margin:0 0 10px!important;line-height:1.1!important}
.ob-price a{flex:0 0 auto!important;margin:0!important;align-self:flex-start!important}
@media(max-width:700px){.ob-price{aspect-ratio:auto!important;min-height:330px!important}}

/* Tariff content: raise all elements 0.5cm, then everything below title a further 1.2cm */
@media(min-width:701px){
 .ob-price{padding-top:calc(25px - 0.5cm)!important}
 .ob-price h3{margin-bottom:calc(14px - 1.2cm)!important}
}

/* Equal tariff layout: one-line titles, shared vertical positions */
@media(min-width:901px){
 .ob-price h3{font-size:clamp(24px,2.05vw,30px)!important;white-space:nowrap!important;max-width:85%!important;min-height:0!important;line-height:1.15!important;margin-bottom:14px!important}
 .ob-price .ob-price-lines{margin-top:0!important;margin-bottom:12px!important}
}

/* Tariffs: consolidated responsive grid (replaces accumulated positional overrides) */
.ob-price-grid{
 display:grid!important;
 grid-template-columns:repeat(2,minmax(0,1fr))!important;
 gap:clamp(16px,2vw,28px)!important;
 align-items:stretch!important;
}
.ob-price-grid > .ob-price{
 display:grid!important;
 grid-template-columns:minmax(0,1fr)!important;
 grid-template-rows:minmax(46px,auto) minmax(114px,auto) auto auto!important;
 align-content:start!important;
 align-items:start!important;
 justify-items:start!important;
 row-gap:8px!important;
 box-sizing:border-box!important;
 width:100%!important;
 min-width:0!important;
 min-height:340px!important;
 height:auto!important;
 aspect-ratio:auto!important;
 padding:clamp(24px,2.5vw,36px)!important;
 position:relative!important;
 overflow:hidden!important;
}
.ob-price-grid > .ob-price > img{
 position:absolute!important;
 inset:0!important;
 width:100%!important;
 height:100%!important;
 object-fit:cover!important;
 object-position:right center!important;
 z-index:0!important;
 pointer-events:none!important;
}
.ob-price-grid > .ob-price > h3{
 grid-row:1!important;
 margin:0!important;
 padding:0!important;
 font:500 clamp(25px,2.05vw,32px)/1.14 Georgia,serif!important;
 max-width:100%!important;
 min-height:0!important;
 white-space:normal!important;
 overflow-wrap:normal!important;
 position:relative!important;
 z-index:1!important;
}
.ob-price-grid > .ob-price > .ob-price-lines{
 grid-row:2!important;
 align-self:start!important;
 margin:0!important;
 width:auto!important;
 max-width:62%!important;
 font-size:clamp(14px,1.2vw,17px)!important;
 line-height:1.48!important;
 position:relative!important;
 z-index:1!important;
}
.ob-price-grid > .ob-price > strong{
 grid-row:3!important;
 margin:0!important;
 max-width:65%!important;
 font:700 clamp(29px,2.3vw,36px)/1.1 Georgia,serif!important;
 position:relative!important;
 z-index:1!important;
}
.ob-price-grid > .ob-price > a{
 grid-row:4!important;
 margin:0!important;
 max-width:none!important;
 padding:12px 28px!important;
 font-size:18px!important;
 position:relative!important;
 z-index:1!important;
}
@media(max-width:1050px){
 .ob-price-grid > .ob-price{
  grid-template-rows:minmax(78px,auto) minmax(126px,auto) auto auto!important;
 }
 .ob-price-grid > .ob-price > h3{font-size:clamp(23px,2.7vw,29px)!important}
 .ob-price-grid > .ob-price > .ob-price-lines{max-width:65%!important;font-size:14px!important}
}
@media(max-width:700px){
 .ob-price-grid{grid-template-columns:minmax(0,1fr)!important}
 .ob-price-grid > .ob-price{
  grid-template-rows:minmax(44px,auto) minmax(116px,auto) auto auto!important;
  min-height:315px!important;
 }
 .ob-price-grid > .ob-price > h3{font-size:clamp(23px,5vw,30px)!important;max-width:100%!important}
 .ob-price-grid > .ob-price > .ob-price-lines{max-width:66%!important;font-size:14px!important}
 .ob-price-grid > .ob-price > a{font-size:17px!important}
}
/* Lift tariff prices by 0.5 cm; keep CTA buttons in their grid rows */
.ob-price-grid > .ob-price > strong{transform:translateY(-0.5cm)!important}
/* FAQ: increase question-to-answer spacing by 0.5 cm */
.ob-faq details[open] > p{margin-top:calc(1em + 0.5cm)!important}
/* FAQ disclosure markers: plum chevrons, preserving native details interaction */
.ob-faq summary{list-style:none!important;display:flex;align-items:baseline;gap:10px}
.ob-faq summary::-webkit-details-marker{display:none}
.ob-faq summary::before{content:"";display:inline-block;flex:0 0 8px;width:8px;height:8px;border-right:2px solid #6E5C8E;border-bottom:2px solid #6E5C8E;transform:rotate(-45deg);transition:transform .2s ease}
.ob-faq details[open] > summary::before{transform:rotate(45deg)}
/* FAQ anchor lives on the existing rendered FAQ body, without adding a grid item. */
.ob-faq-body#faq{scroll-margin-top:240px!important}
/* Shared grid rows: headings and content align at every desktop zoom. */
@media(min-width:901px){
 .ob-two{
  grid-template-columns:minmax(0,1fr) minmax(0,1fr);
  grid-template-rows:auto auto;
  column-gap:45px;
  row-gap:0;
  align-items:start;
  padding:48px 4% 15px;
 }
 .ob-two > .ob-section{display:contents}
 .ob-two .ob-about > h2{grid-column:1;grid-row:1}
 .ob-two .ob-faq > h2{grid-column:2;grid-row:1}
 .ob-two .ob-section > h2{
  height:auto!important;min-height:0!important;
  margin:0 0 26px!important;
 }
 .ob-two .ob-about-body{grid-column:1;grid-row:2;min-width:0}
 .ob-two .ob-faq-body{grid-column:2;grid-row:2;min-width:0}
 .ob-two .ob-about-body > p:first-of-type{margin-top:0!important}
 .ob-two .ob-about-body > img{margin-top:0!important}
 .ob-two .ob-faq-body > details:first-of-type{
  margin-top:0!important;padding-top:0!important;
 }
}
@media(max-width:900px){
 .ob-two .ob-about-body,.ob-two .ob-faq-body{display:flow-root}
}
.ob-two .ob-faq summary{font-size:17px!important;line-height:1.7!important}
</style>
"""

def render_landing(price_profile: int, price_full: int):
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ob-page">
      <header class="ob-hero">
        {img("header.webp", "Девушка среди холмов", "ob-hero-image")}
      <nav class="ob-nav" aria-label="Навигация">
        <span class="ob-logo">Образы</span>
        <a href="#how">Как это работает</a>
        <a href="#example">Примеры</a>
        <a href="#prices">Тарифы</a>
        <a href="#faq">Вопросы</a>
      </nav>
        <div class="ob-hero-content">
          <h1>Узнайте себя через<span class="ob-title-break"><br></span><span class="ob-title-line">образы, которые вам</span><span class="ob-title-break"><br></span>близки</h1>
          <p>Необычный способ исследовать свою личность,<br>
          увидеть привычные реакции и понять,<br>
          как вы взаимодействуете с другими</p>
          <a class="ob-cta" href="?view=research">Начать исследование <span aria-hidden="true">→</span></a>
        </div>
      </header>
      <section class="ob-section" id="how">
        <h2>Как это работает?</h2>
        <div class="ob-grid4">
          <article class="ob-step"><div class="ob-step-top"><span class="ob-step-number">1</span>{img("01_obraz.svg", "Первый этап")}</div><h3>Назовите близкие образы</h3><p>Напишите имена персонажей, героев или известных людей, которые вам близки</p></article>
          <article class="ob-step"><div class="ob-step-top"><span class="ob-step-number">2</span>{img("02_profili.svg", "Второй этап")}</div><h3>Получите описания профилей</h3><p>Познакомьтесь с несколькими обезличенными описаниями</p></article>
          <article class="ob-step"><div class="ob-step-top"><span class="ob-step-number">3</span>{img("03_vybor.svg", "Третий этап")}</div><h3>Отметьте своё</h3><p>Выберите одно или несколько подходящих описаний</p></article>
          <article class="ob-step"><div class="ob-step-top"><span class="ob-step-number">4</span>{img("04_razbor.svg", "Четвёртый этап")}</div><h3>Получите разбор</h3><p>Узнайте свои сильные и слабые стороны, зоны перегрузки и рекомендации</p></article>
        </div>
        <div class="ob-compat ob-compat-new">
          {img("etapi_sovmestimost.webp", "Декоративные травы и холмы", "ob-compat-art")}
          <div class="ob-compat-body">
            <p class="ob-compat-intro">Дополнительно можно пройти тестирование на совместимость профилей</p>
            <h3>Тест на Совместимость</h3>
            <p class="ob-compat-lead">Узнайте сильные стороны вашего союза, возможные противоречия, сценарии развития отношений и способы достижения взаимопонимания</p>
            <div class="ob-compat-steps" aria-label="Три этапа теста на совместимость">
              <div class="ob-compat-step"><span class="ob-compat-number">1</span><p>Предложите пройти тестирование Профиля вашему партнеру</p></div>
              <div class="ob-compat-step"><span class="ob-compat-number">2</span><p>Загрузите ваши профили</p></div>
              <div class="ob-compat-step"><span class="ob-compat-number">3</span><p>Получите разбор</p></div>
            </div>
          </div>
        </div>
      </section>
      <section class="ob-section" id="example">
        <h2>Пример результата «Профиль»</h2>
        <div class="ob-example">
          {img("primer_profile.webp", "Иллюстрация профиля")}
          <div class="ob-example-copy"><h3>Профиль личности</h3><div class="ob-example-tagline">Ваши особенности — ваш ресурс</div><p>Исследуйте особенности своего характера через близкие вам образы<br>Узнайте, какие качества помогают вам справляться с задачами, как проявляются привычные реакции и что может становиться источником перегрузки</p><details class="ob-example-details"><summary>Посмотреть полный пример</summary><div class="ob-example-placeholder">Полный текст примера профиля пока не предоставлен<br>Добавим утверждённый пример без вымышленных результатов</div></details></div>
          <aside><b>Что вы узнаете</b><ul><li>Сильные стороны и ресурсы</li><li>Привычные реакции</li><li>Зоны перегрузки</li><li>Рекомендации для повседневной жизни</li></ul></aside>
          {img("primer_rightside.webp", "", "ob-example-botanical")}
        </div>
      </section>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ob-page">
      <section class="ob-section" id="compat-example">
        <h2>Пример результата «Совместимость»</h2>
        <div class="ob-example ob-example-compat">
          {img("primer_sovmestimost.webp", "Иллюстрация совместимости")}
          <div class="ob-example-copy"><h3>Два профиля —<br>один союз</h3><div class="ob-example-tagline">Понять друг друга глубже</div><p>Посмотрите, в чём ваши особенности дополняют друг друга, где могут возникать недопонимания и какие подходы помогут выстраивать более осознанное взаимодействие</p><details class="ob-example-details"><summary>Посмотреть полный пример</summary><div class="ob-example-placeholder">Полный текст примера совместимости пока не предоставлен<br>Добавим утверждённый пример</div></details></div>
          <aside><b>В разборе</b><ul><li>Точки соприкосновения</li><li>Возможные противоречия</li><li>Сценарии взаимодействия</li><li>Практические рекомендации</li></ul></aside>
          {img("primer_rightside.webp", "", "ob-example-botanical")}
        </div>
      </section>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ob-page">
      <section class="ob-section" id="prices">
        <h2>Тарифы</h2>
        <div class="ob-price-grid">
          <article class="ob-price">{img("cena_profile.webp", "Тариф Профиль")}<h3>Профиль</h3><p class="ob-price-lines">Полный разбор личности<br>Сильные стороны и ресурсы<br>Зоны перегрузки<br>Рекомендации</p><strong>{price_profile} ₽</strong><a href="?view=research">Выбрать</a></article>
          <article class="ob-price">{img("cena_sovmestimost.webp", "Тариф Профиль и совместимость")}<h3>Профиль + совместимость</h3><p class="ob-price-lines">Ваш полный профиль<br>Анализ совместимости<br>Сильные/уязвимые стороны союза<br>Рекомендации</p><strong>{price_full} ₽</strong><a href="?view=research">Выбрать</a></article>
        </div>
      </section>
      <div class="ob-two">
        <section class="ob-section ob-about" id="about">
          <h2>Почему именно образы?</h2>
          <div class="ob-about-body">
          {img("cvetok.png", "Цветок")}
          <p>Образ позволяет передать гораздо больше информации, чем человек способен выразить словами</p>
          <p>Образы становятся отправной точкой для размышлений о привычках, реакциях и особенностях характера, которые определяют взаимодействие человека с окружающим миром</p>
          </div>
        </section>
        <section class="ob-section ob-faq"><h2>Частые вопросы</h2>
        <div class="ob-faq-body" id="faq">
<details><summary>Это психологический тест или гадание на кофейной гуще?</summary>
<p>Ни то ни другое.</p>
<p>Изначально автор не планировал создавать тест. Исследование началось с попытки разобраться в собственных особенностях, негативно влияющих на здоровье и психологическое благополучие, и найти способы преодоления связанных с ними трудностей.</p>
<p>Позднее выяснилось, что этот подход может быть полезен и для понимания взаимоотношений с другими людьми. Так появилась идея исследования совместимости.</p>
<p>Первые результаты оказались познавательными и полезными для участников. Однако для полноценной научной проверки методики необходимы исследования на более широкой аудитории и систематический анализ полученных данных.</p>
<p>Поэтому автор будет благодарен за отзывы и обратную связь. Ваш опыт поможет совершенствовать методику и развивать проект.</p></details>
<details><summary>Каких персонажей нужно предоставить для теста?</summary>
<p>От выбора персонажей непосредственно зависят результаты тестирования, поэтому к нему следует подойти внимательно и ответственно.</p>
<p><strong>Когда лучше проходить тест?</strong></p>
<p>Желательно проходить тестирование в спокойном, умиротворённом состоянии, без спешки. Самовосприятие человека может меняться со временем и под влиянием жизненных обстоятельств, что неизбежно отражается на результатах.</p>
<p><strong>Каких персонажей можно выбирать?</strong></p>
<p>Подойдут герои кинофильмов, мультфильмов, комиксов и литературных произведений, а также известные исторические личности и современные медийные персоны. Главное условие — наличие достаточной информации об их характере, поведении и образе жизни, позволяющей составить представление об их психологических особенностях.</p>
<p><strong>Как выбирать персонажей?</strong></p>
<p>Основной критерий — сходство с самим собой, если вы способны мысленно сопоставить свои особенности с характером персонажа. Если такое сопоставление затруднительно, можно руководствоваться личной симпатией к персонажу.</p>
<p><strong>А если выбрать персонажей ради шутки?</strong></p>
<p>Даже такой результат может оказаться интересным и полезным. Однако случайный или шуточный выбор способен внести искажения по сравнению с результатом, полученным при вдумчивом подходе к тестированию.</p></details>
<details><summary>Можно ли сохранить результат?</summary>
<p>Да. После завершения тестирования вы можете скачать результат на своё устройство в текстовом формате (.txt).</p>
<p><strong>Обратите внимание:</strong> результаты не сохраняются в приложении. Исследования «Профиль» и «Совместимость» формируют отдельные результаты, каждый из которых необходимо скачать самостоятельно.</p>
<p>Не забудьте сохранить файлы после завершения тестирования! В противном случае результаты будут утрачены, и для их повторного получения придётся пройти тест заново.</p></details>
<details><summary>Можно ли вернуть деньги, если результат не устроил?</summary>
<p>Результаты тестирования предоставляются в рамках платной услуги. Поскольку исследование носит интерпретационный характер, несовпадение полученного результата с вашими ожиданиями само по себе не является основанием для возврата денежных средств.</p>
<p>До оплаты вы можете ознакомиться с примерами результатов, представленными на сайте, и самостоятельно решить, подходит ли вам такой формат исследования.</p>
<p>Условия оказания услуги и возврата денежных средств определяются публичной офертой с учётом требований законодательства Российской Федерации. Перед прохождением платного исследования необходимо ознакомиться с офертой и подтвердить согласие с её условиями. Если вы не согласны с ними, рекомендуем воздержаться от приобретения услуги.</p>
<p><strong>Возрастное ограничение — 18+.</strong> Методика проверялась только на совершеннолетней аудитории и не предназначена для лиц младше 18 лет. Подтверждая согласие на прохождение исследования, вы также подтверждаете, что достигли совершеннолетия.</p></details></div></section>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="ob-page"><footer class="ob-footer"><strong>Образы</strong><span>Оферта · Политика конфиденциальности · Контакты</span><span>ИП Фофанова · реквизиты уточняются</span><span>18+</span></footer></div>', unsafe_allow_html=True)
    docs = [("Оферта","oferta.pdf"),("Политика конфиденциальности","privacy.pdf")]
    available = [(label, ASSETS / filename) for label,filename in docs if (ASSETS / filename).exists()]
    if available:
        cols=st.columns(len(available))
        for col,(label,path) in zip(cols,available):
            with col:
                st.download_button(f"Скачать: {label}",path.read_bytes(),file_name=path.name,mime="application/pdf")
