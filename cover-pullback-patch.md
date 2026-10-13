# Cover pull-back patch (only the landing-page change)

Apply ONLY this to index.html. Do not change anything else (3D model, drawing, panels, seasons, texts, photos in spaces).

Photo used: `2022-07-06 13.29.46-1.jpg` (in the same folder as index.html, 2576x1932).

## 1. Markup
Replace the existing `<div id="cover"> ... </div>` structure so it looks like this. KEEP your current text content
(kicker, h1, description, Enter button, authors). Only add the wrappers, the three layer divs and the hint span:

```html
<div id="cover" tabindex="-1">
<div class="cover-track"><div class="cover-scene">
  <div class="cv-layer cv-b" aria-hidden="true"></div>
  <div class="cv-scrim" aria-hidden="true"></div>
  <div class="cv-scrim-top" aria-hidden="true"></div>

  <!-- ...existing kicker / h1 / description stay here... -->

  <div class="cover-actions">
    <button class="enter" id="enterBtn">...existing...</button>
    <span class="cover-hint" id="coverHint">Scroll to step back &#8595;</span>
  </div>

  <!-- ...existing authors (cover-meta) stays here... -->
</div></div>
</div>
```

## 2. CSS
Remove the old cover layout rules (old `#cover{...}`, `.cover-photo...`, any single-photo cover background) and use this instead:

```css
#cover{
  position:fixed;inset:0;z-index:60;background:#121714;
  overflow-y:auto;overflow-x:hidden;overscroll-behavior:contain;outline:none;
}
.cover-track{position:relative;height:320vh}
.cover-scene{
  position:sticky;top:0;height:100vh;height:100dvh;overflow:hidden;box-sizing:border-box;
  display:flex;flex-direction:column;justify-content:flex-start;gap:.9rem;padding:5vh 6vw 5vh;
}
.cv-layer{position:absolute;background-repeat:no-repeat;background-size:cover;will-change:transform,opacity}
.cv-b{left:0;top:0;width:100%;height:100%;background-position:50% 50%}
.cv-scrim{position:absolute;inset:0;pointer-events:none;
  background:linear-gradient(180deg,rgba(14,18,16,0) 0%,rgba(14,18,16,0) 42%,rgba(14,18,16,.55) 62%,rgba(14,18,16,.88) 100%)}
.cv-scrim-top{position:absolute;left:0;right:0;top:0;height:52%;pointer-events:none;
  background:linear-gradient(180deg,rgba(14,18,16,.66) 0%,rgba(14,18,16,.22) 66%,rgba(14,18,16,0) 100%)}
.cover-scene > *:not(.cv-layer):not(.cv-scrim):not(.cv-scrim-top){position:relative;z-index:2}
#cover .cover-kicker{color:rgba(243,244,240,.85)}
#cover h1{color:#F6F7F3;text-shadow:0 1px 18px rgba(0,0,0,.4)}
#cover h1 span.sub{color:#F1F5F2;text-shadow:0 1px 14px rgba(0,0,0,.7),0 0 3px rgba(0,0,0,.4)}
#cover .cover-line{color:#F0F2EC;margin-top:auto;max-width:56ch;text-shadow:0 1px 14px rgba(0,0,0,.55),0 0 4px rgba(0,0,0,.55)}
#cover .enter{color:#F6F7F3;border-bottom:1px solid #F6F7F3;font-size:1.05rem;padding:.5rem 0 3px}
#cover .cover-meta{color:rgba(243,244,240,.72);margin-top:0;padding-top:1.1rem}
.cover-hint{font-family:var(--sans);font-size:.8rem;letter-spacing:.05em;color:rgba(243,244,240,.82);transition:opacity .5s}
.cover-hint.hide{opacity:0}
@media (prefers-reduced-motion: no-preference){
  .cover-hint:not(.hide){animation:hintnudge 2.2s ease-in-out infinite}
}
@keyframes hintnudge{0%,100%{transform:translateY(0)}50%{transform:translateY(3px)}}
```

## 3. JavaScript
Remove the old cover-photo code, add this once, after the page scripts that define `$`:

```js
/* ---- cover: scroll-driven pull-back (close view of the doorway -> whole building) ---- */
/* path to the wide photo, relative to index.html */
const PULLBACK_SRC = "2022-07-06 13.29.46-1.jpg";
(function coverScene(){
  const cover = document.getElementById("cover");
  const B = cover.querySelector(".cv-b"), scrim = cover.querySelector(".cv-scrim-top"), hint = document.getElementById("coverHint");
  B.style.backgroundImage = 'url("' + PULLBACK_SRC + '")';
  const IB = {w:2576, h:1932, dx:.5475, dy:.839};   /* doorway centre in the photo */
  const SB0 = 2.6, START_Y = .62;
  let g = null;
  const sm = x => { x = Math.max(0, Math.min(1, x)); return x*x*(3-2*x); };
  function measure(){
    const W = cover.clientWidth, H = cover.clientHeight, cB = Math.max(W/IB.w, H/IB.h);
    const Dp = {x:(W-IB.w*cB)*.5 + IB.dx*IB.w*cB, y:(H-IB.h*cB)*.5 + IB.dy*IB.h*cB};
    g = {W, H, Dp, Tp:{x:W*.5, y:H*START_Y}};
    B.style.transformOrigin = Dp.x + "px " + Dp.y + "px";
  }
  function render(){
    if(!g) measure();
    const max = cover.scrollHeight - cover.clientHeight;
    const p = max > 0 ? Math.min(1, Math.max(0, cover.scrollTop/max)) : 0;
    const e = Math.min(1, p/.9), s = Math.pow(SB0, 1-e);
    let tx = (1-e)*(g.Tp.x-g.Dp.x), ty = (1-e)*(g.Tp.y-g.Dp.y);
    tx = Math.min((s-1)*g.Dp.x, Math.max((1-s)*(g.W-g.Dp.x), tx));   /* never reveal an edge */
    ty = Math.min((s-1)*g.Dp.y, Math.max((1-s)*(g.H-g.Dp.y), ty));
    B.style.transform = "translate3d(" + tx.toFixed(1) + "px," + ty.toFixed(1) + "px,0) scale(" + s.toFixed(4) + ")";
    scrim.style.opacity = (1 - .45*sm((p-.2)/.4)).toFixed(3);
    if(hint) hint.classList.toggle("hide", p > .03);
  }
  let raf = 0;
  cover.addEventListener("scroll", ()=>{ if(!raf) raf = requestAnimationFrame(()=>{ raf = 0; render(); }); }, {passive:true});
  window.addEventListener("resize", ()=>{ measure(); render(); });
  window.__coverRender = ()=>{ measure(); render(); };
  measure(); render();
  try{ cover.focus({preventScroll:true}); }catch(e){}
})();
```

## 4. Handlers (small edits to the existing code)
- When "Enter the building" is clicked: keep your existing behaviour (fade `#cover`, then hide it).
- When the header title (`#homeBtn`) is clicked, in addition to showing the cover, reset the effect:

```js
c.style.display = "";
c.scrollTop = 0;
if(window.__coverRender) window.__coverRender();
try{ c.focus({preventScroll:true}); }catch(e){}
```

## Check
Open index.html: the first screen is the doorway close-up; scrolling down pulls back to the whole building; scrolling up moves closer again; Enter and the header title still work.
