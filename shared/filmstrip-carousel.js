/* Filmstrip carousel + full-screen zoom viewer.
   Shared implementation of the "chapter 5: Creeping Agency of Grapevines" filmstrip from
   a-city-of-vineyards/index.html — see filmstrip-carousel.css for the companion styles.
   Exposes window.FilmstripCarousel = {createFilmstrip, createViewer}. Plain classic script, no
   imports/exports, safe to load with a <script src> tag on any page. */
(function(global){
  "use strict";
  const SVG_NS = "http://www.w3.org/2000/svg";
  const reducedQuery = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
  const I_L = "M10 3L5 8l5 5", I_R = "M6 3l5 5-5 5", I_X = "M3.5 3.5l9 9M12.5 3.5l-9 9";

  function h(tag, cls){
    const n = document.createElement(tag);
    if(cls) n.className = cls;
    return n;
  }
  function icon(d){
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("width","16"); svg.setAttribute("height","16"); svg.setAttribute("viewBox","0 0 16 16");
    svg.setAttribute("aria-hidden","true");
    const p = document.createElementNS(SVG_NS, "path");
    p.setAttribute("d", d); p.setAttribute("fill","none"); p.setAttribute("stroke","currentColor");
    p.setAttribute("stroke-width","1.4"); p.setAttribute("stroke-linecap","round"); p.setAttribute("stroke-linejoin","round");
    svg.appendChild(p);
    return svg;
  }
  function btn(cls, label, iconPath, text){
    const b = h("button", cls); b.type = "button"; b.setAttribute("aria-label", label);
    if(iconPath) b.appendChild(icon(iconPath));
    if(text != null) b.appendChild(document.createTextNode(text));
    return b;
  }

  /* ---------- full-screen pan/zoom viewer ---------- */
  function createViewer(){
    const dlg = h("dialog","fs-viewer"); dlg.setAttribute("aria-label","Larger view");
    const top = h("div","fs-vw-top");
    const count = h("span","fs-vw-count"); count.setAttribute("aria-live","polite");
    const zoomWrap = h("span","fs-vw-zoom");
    const out = btn("fs-vw-btn fs-vw-out","Zoom out",null,"−");
    const zin = btn("fs-vw-btn fs-vw-in","Zoom in",null,"+");
    const closeBtn = btn("fs-vw-btn fs-vw-close","Close",I_X);
    zoomWrap.appendChild(out); zoomWrap.appendChild(zin); zoomWrap.appendChild(closeBtn);
    top.appendChild(count); top.appendChild(zoomWrap);
    const stage = h("div","fs-vw-stage");
    const vimg = document.createElement("img"); vimg.alt = ""; stage.appendChild(vimg);
    const prev = btn("fs-vw-btn fs-vw-prev","Previous",I_L);
    const next = btn("fs-vw-btn fs-vw-next","Next",I_R);
    const vcap = h("div","fs-vw-cap");
    dlg.appendChild(top); dlg.appendChild(stage); dlg.appendChild(prev); dlg.appendChild(next); dlg.appendChild(vcap);
    document.body.appendChild(dlg);

    let items = [], idx = 0, returnTo = null;
    const z = {s:1, x:0, y:0, base:1, w:0, h:0};
    function fit(){
      const r = stage.getBoundingClientRect();
      z.base = Math.min(r.width / z.w, r.height / z.h);
      z.s = 1; z.x = 0; z.y = 0; apply();
    }
    function clampPan(){
      const r = stage.getBoundingClientRect(), k = z.base * z.s;
      const mx = Math.max(0, (z.w * k - r.width) / 2), my = Math.max(0, (z.h * k - r.height) / 2);
      z.x = Math.min(mx, Math.max(-mx, z.x)); z.y = Math.min(my, Math.max(-my, z.y));
    }
    function apply(){
      clampPan();
      const k = z.base * z.s;
      vimg.style.width = z.w + "px"; vimg.style.height = z.h + "px";
      vimg.style.transform = "translate(" + (z.x - z.w*k/2) + "px," + (z.y - z.h*k/2) + "px) scale(" + k + ")";
      out.disabled = z.s <= 1; zin.disabled = z.s >= 6;
    }
    function zoomAt(f, cx, cy){
      const r = stage.getBoundingClientRect();
      const ns = Math.min(6, Math.max(1, z.s * f)), q = ns / z.s;
      const px = (cx == null ? r.left + r.width/2 : cx) - (r.left + r.width/2);
      const py = (cy == null ? r.top + r.height/2 : cy) - (r.top + r.height/2);
      z.x = px - (px - z.x) * q; z.y = py - (py - z.y) * q; z.s = ns; apply();
    }
    function show(i){
      idx = (i + items.length) % items.length;
      const it = items[idx];
      z.w = it.w; z.h = it.h;
      vimg.alt = it.alt || "";
      vimg.src = it.previewSrc || it.full;
      if(it.full && it.full !== vimg.src){
        const hi = new Image();
        hi.onload = function(){ if(items[idx] === it) vimg.src = it.full; };
        hi.src = it.full;
      }
      vcap.textContent = it.caption || "";
      count.textContent = items.length > 1 ? (idx + 1) + " / " + items.length : "";
      prev.hidden = next.hidden = items.length < 2;
      fit();
    }
    function open(list, i, from){
      items = list; returnTo = from || document.activeElement;
      dlg.showModal(); document.documentElement.style.overflow = "hidden";
      show(i);
      closeBtn.focus();
    }
    dlg.addEventListener("close", function(){
      document.documentElement.style.overflow = "";
      vimg.removeAttribute("src");
      if(returnTo && returnTo.focus) returnTo.focus({preventScroll:true});
    });
    closeBtn.addEventListener("click", function(){ dlg.close(); });
    prev.addEventListener("click", function(){ show(idx - 1); });
    next.addEventListener("click", function(){ show(idx + 1); });
    zin.addEventListener("click", function(){ zoomAt(1.6); });
    out.addEventListener("click", function(){ zoomAt(1/1.6); });
    dlg.addEventListener("keydown", function(e){
      if(e.key === "ArrowLeft" && items.length > 1){ e.preventDefault(); show(idx - 1); }
      else if(e.key === "ArrowRight" && items.length > 1){ e.preventDefault(); show(idx + 1); }
      else if(e.key === "+" || e.key === "="){ zoomAt(1.6); }
      else if(e.key === "-"){ zoomAt(1/1.6); }
      else if(e.key === "0"){ fit(); }
    });
    stage.addEventListener("wheel", function(e){ e.preventDefault(); zoomAt(Math.exp(-e.deltaY * 0.0022), e.clientX, e.clientY); }, {passive:false});
    stage.addEventListener("dblclick", function(e){ if(z.s > 1) fit(); else zoomAt(2.5, e.clientX, e.clientY); });
    const pts = new Map(); let g = null;
    stage.addEventListener("pointerdown", function(e){
      stage.setPointerCapture(e.pointerId); pts.set(e.pointerId, {x:e.clientX, y:e.clientY});
      stage.classList.add("drag");
      const a = Array.from(pts.values());
      g = a.length === 2 ? {pinch:true, d:Math.hypot(a[0].x-a[1].x, a[0].y-a[1].y), s:z.s}
                          : {pinch:false, x0:e.clientX, y0:e.clientY, zx:z.x, zy:z.y};
    });
    stage.addEventListener("pointermove", function(e){
      if(!pts.has(e.pointerId) || !g) return;
      pts.set(e.pointerId, {x:e.clientX, y:e.clientY});
      const a = Array.from(pts.values());
      if(g.pinch && a.length === 2){
        const d = Math.hypot(a[0].x-a[1].x, a[0].y-a[1].y);
        zoomAt((g.s * d / g.d) / z.s, (a[0].x+a[1].x)/2, (a[0].y+a[1].y)/2);
      } else if(!g.pinch && z.s > 1){
        z.x = g.zx + e.clientX - g.x0; z.y = g.zy + e.clientY - g.y0; apply();
      }
    });
    function up(e){
      if(!pts.has(e.pointerId)) return;
      pts.delete(e.pointerId);
      if(g && !g.pinch && z.s === 1 && items.length > 1){
        const dx = e.clientX - g.x0, dy = e.clientY - g.y0;
        if(Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.4) show(idx + (dx < 0 ? 1 : -1));
      }
      if(g && !g.pinch && e.pointerType === "touch" && Math.hypot(e.clientX-g.x0, e.clientY-g.y0) < 10){
        const now = Date.now();
        if(now - (stage._tap || 0) < 320){ if(z.s > 1) fit(); else zoomAt(2.5, e.clientX, e.clientY); stage._tap = 0; }
        else stage._tap = now;
      }
      if(!pts.size){ g = null; stage.classList.remove("drag"); } else g = null;
    }
    stage.addEventListener("pointerup", up); stage.addEventListener("pointercancel", up);
    const onResize = function(){ if(dlg.open) fit(); };
    addEventListener("resize", onResize);

    return {
      open: open,
      dialog: dlg,
      destroy: function(){ removeEventListener("resize", onResize); if(dlg.open) dlg.close(); dlg.remove(); }
    };
  }

  /* ---------- filmstrip: a slow horizontal strip pinned and moved by the page scroll ---------- */
  function createFilmstrip(opts){
    const media = opts.media, n = media.length;
    const vw = opts.viewer || createViewer();
    const ownsViewer = !opts.viewer;

    const strip = h("div","fs-strip");
    strip.setAttribute("role","region");
    strip.setAttribute("aria-label", opts.ariaLabel || (n + " photograph" + (n === 1 ? "" : "s") + ", side by side"));
    /* topOffset may be a fixed CSS value or a function re-measured on every layout pass (a fixed
       header's height can change, e.g. as its contents wrap at narrow widths) */
    function applyTopOffset(){
      if(!opts.topOffset) return;
      const v = typeof opts.topOffset === "function" ? opts.topOffset() : opts.topOffset;
      if(v) strip.style.setProperty("--fs-top", v);
    }
    applyTopOffset();
    const sticky = h("div","fs-sticky");
    const track = h("div","fs-track"); track.tabIndex = 0;

    const figs = media.map(function(m, i){
      const fig = document.createElement("figure");
      const b = h("button","fs-zoom"); b.type = "button"; b.setAttribute("aria-label","Open larger view");
      const img = document.createElement("img");
      img.className = "fs-ph";
      img.src = m.small || m.src;
      if(m.small) img.srcset = m.small + " 1200w, " + m.src + " " + Math.max(m.w, m.h) + "w";
      img.sizes = m.sizes || "(min-width: 700px) 40rem, 80vw";
      img.width = m.w; img.height = m.h;
      img.alt = m.alt || "";
      img.loading = "lazy"; img.decoding = "async";
      b.appendChild(img);
      b.addEventListener("click", function(){
        const list = media.map(function(x){
          return {full:x.src, previewSrc:x.small || x.src, w:x.w, h:x.h, alt:x.alt,
            caption:[x.caption, x.credit].filter(Boolean).join(" · ")};
        });
        vw.open(list, i, b);
      });
      fig.appendChild(b);
      track.appendChild(fig);
      return fig;
    });
    sticky.appendChild(track);

    const foot = h("div","fs-foot");
    const cap = h("p","fs-cap");
    cap.hidden = true;   /* no shared caption/credit text exists for this set of photographs */
    const arrows = h("span","fs-arrows");
    const prevBtn = btn("fs-arrow fs-prev","Previous photograph",I_L);
    const nextBtn = btn("fs-arrow fs-next","Next photograph",I_R);
    arrows.appendChild(prevBtn); arrows.appendChild(nextBtn);
    const prog = h("span","fs-prog"); prog.setAttribute("aria-hidden","true");
    const progI = document.createElement("i"); prog.appendChild(progI);
    foot.appendChild(cap); foot.appendChild(arrows); foot.appendChild(prog);
    sticky.appendChild(foot);
    strip.appendChild(sticky);

    let reduced = reducedQuery();
    let run = false, span = 0, topPx = 0, moveRaf = 0;
    /* Native position:sticky would normally pin .fs-sticky here, exactly as in chapter 5 — but on a
       page where an ancestor (here, <body>) has only overflow-x restricted, some browsers still treat
       it as that element's nearest scroll container, which starves position:sticky of the viewport it
       needs and leaves the element scrolling away instead of pinning. Driving the pin from JS (reusing
       the same scroll-progress math as the horizontal movement below) sidesteps that regardless of the
       host page's own overflow setup, while leaving the CSS position:sticky rule in place as the base/
       fallback appearance before this runs. */
    function pinSticky(){
      if(!run){ sticky.style.cssText = ""; return; }
      const r = strip.getBoundingClientRect(), stickyH = sticky.offsetHeight || (innerHeight - topPx);
      if(r.top > topPx) sticky.style.cssText = "";
      else if(r.bottom - stickyH < topPx) sticky.style.cssText = "position:absolute;left:0;right:0;bottom:0;top:auto";
      else sticky.style.cssText = "position:fixed;top:" + topPx + "px;left:" + r.left + "px;width:" + r.width + "px";
    }
    function stripLayout(){
      applyTopOffset();
      topPx = parseFloat(getComputedStyle(strip).getPropertyValue("--fs-top")) || 0;
      reduced = reducedQuery();
      run = !reduced;
      strip.classList.toggle("fs-run", run);
      track.style.transform = "";
      if(run){
        span = Math.max(0, track.scrollWidth - track.clientWidth);
        strip.style.setProperty("--fs-h", (innerHeight + span * 1.4) + "px");
      } else strip.style.removeProperty("--fs-h");
      stripMove();
    }
    function stripP(){
      if(!run) return span ? track.scrollLeft / span : 0;
      const r = strip.getBoundingClientRect(), len = strip.offsetHeight - innerHeight;
      return len > 0 ? Math.min(1, Math.max(0, -r.top / len)) : 0;
    }
    function stripMove(){
      if(!run) span = Math.max(0, track.scrollWidth - track.clientWidth);
      pinSticky();
      const p = stripP();
      if(run) track.style.transform = "translateX(" + (-p * span) + "px)";
      progI.style.width = (p * 100) + "%";
      prevBtn.disabled = p <= 0.001; nextBtn.disabled = p >= 0.999;
    }
    function stripGo(dir){
      const mid = track.clientWidth / 2, cur = stripP() * span;
      const cs = figs.map(function(f){ return Math.min(span, Math.max(0, f.offsetLeft + f.offsetWidth/2 - mid)); });
      let tgt = dir > 0 ? cs.find(function(x){ return x > cur + 4; }) : cs.slice().reverse().find(function(x){ return x < cur - 4; });
      if(tgt == null) tgt = dir > 0 ? span : 0;
      if(run){
        const len = strip.offsetHeight - innerHeight, top = strip.getBoundingClientRect().top + scrollY;
        scrollTo({top: top + (span ? tgt/span : 0) * len, behavior: reduced ? "auto" : "smooth"});
      } else track.scrollTo({left: tgt, behavior: reduced ? "auto" : "smooth"});
    }
    prevBtn.addEventListener("click", function(){ stripGo(-1); });
    nextBtn.addEventListener("click", function(){ stripGo(1); });
    /* Scroll fires far more often than the display can paint (especially during trackpad/mouse-wheel
       momentum), and stripMove()/pinSticky() both read layout (getBoundingClientRect) and then write
       it (inline styles) — doing that on every raw scroll event forces a synchronous layout on each
       one. Collapsing same-frame calls into one with requestAnimationFrame keeps the same visible
       result (still updates every frame) without the redundant layout work between frames. */
    function queueMove(){
      if(moveRaf) return;
      moveRaf = requestAnimationFrame(function(){ moveRaf = 0; stripMove(); });
    }
    track.addEventListener("scroll", queueMove, {passive:true});
    track.addEventListener("keydown", function(e){
      if(e.key === "ArrowRight"){ e.preventDefault(); stripGo(1); }
      if(e.key === "ArrowLeft"){ e.preventDefault(); stripGo(-1); }
    });
    track.addEventListener("focusin", function(e){
      if(!run) return;
      const f = e.target.closest("figure"); if(!f) return;
      const tgt = Math.min(span, Math.max(0, f.offsetLeft + f.offsetWidth/2 - track.clientWidth/2));
      const len = strip.offsetHeight - innerHeight, top = strip.getBoundingClientRect().top + scrollY;
      scrollTo({top: top + (span ? tgt/span : 0) * len});
    });

    const onScroll = queueMove;
    addEventListener("scroll", onScroll, {passive:true});
    let lastW = innerWidth, rz = 0;
    const onResize = function(){
      if(innerWidth === lastW && run){ stripMove(); return; }
      lastW = innerWidth; clearTimeout(rz); rz = setTimeout(stripLayout, 180);
    };
    addEventListener("resize", onResize);
    let ro = 0, observer = null;
    if("ResizeObserver" in window){
      observer = new ResizeObserver(function(){ clearTimeout(ro); ro = setTimeout(function(){ if(run) stripLayout(); }, 250); });
      observer.observe(document.body);
    }
    const RM = matchMedia("(prefers-reduced-motion: reduce)");
    const onReducedChange = function(){ stripLayout(); };
    if(RM.addEventListener) RM.addEventListener("change", onReducedChange); else RM.addListener(onReducedChange);

    stripLayout();

    return {
      el: strip,
      relayout: stripLayout,
      destroy: function(){
        if(moveRaf) cancelAnimationFrame(moveRaf);
        removeEventListener("scroll", onScroll);
        removeEventListener("resize", onResize);
        if(observer) observer.disconnect();
        if(RM.removeEventListener) RM.removeEventListener("change", onReducedChange); else RM.removeListener(onReducedChange);
        if(ownsViewer) vw.destroy();
      }
    };
  }

  /* ---------- "one at a time" mode: progressively enhance an existing static .fs-strip.fs-one ----------
     Unlike createFilmstrip, this builds no DOM: the figures/images/captions are written directly on
     the host page (see a-city-of-vineyards/index.html chapter 3), so the component already works
     with no JS at all and under prefers-reduced-motion — a plain native horizontally-scrollable,
     scroll-snap row, same markup either way. This only adds the extras: the progress line, working
     arrow buttons, keyboard arrow-key navigation, and the full-screen zoom viewer. It never pins to
     the viewport and never changes the page's height — the host page scrolls past it normally. */
  function enhanceOneAtATime(strip, opts){
    if(!strip) return null;
    opts = opts || {};
    const track = strip.querySelector(".fs-track");
    const figs = Array.prototype.slice.call(track.querySelectorAll(":scope > figure"));
    const prevBtn = strip.querySelector(".fs-prev"), nextBtn = strip.querySelector(".fs-next");
    const progI = strip.querySelector(".fs-prog i");
    const vw = opts.viewer || createViewer();
    const ownsViewer = !opts.viewer;

    const list = figs.map(function(fig){
      const btn2 = fig.querySelector(".fs-zoom"), img = fig.querySelector("img.fs-ph");
      const capEl = fig.querySelector("figcaption");
      return {
        full: (btn2 && btn2.dataset.full) || (img && img.currentSrc) || (img && img.src),
        previewSrc: img && (img.currentSrc || img.src),
        w: img ? (img.naturalWidth || img.width) : 0, h: img ? (img.naturalHeight || img.height) : 0,
        alt: img ? img.alt : "", caption: capEl ? capEl.textContent : ""
      };
    });
    figs.forEach(function(fig, i){
      const btn2 = fig.querySelector(".fs-zoom");
      if(btn2) btn2.addEventListener("click", function(){ vw.open(list, i, btn2); });
    });

    function span(){ return Math.max(0, track.scrollWidth - track.clientWidth); }
    function progress(){ const s = span(); return s ? track.scrollLeft / s : 0; }
    /* figure.offsetLeft is relative to whichever ancestor is actually positioned, which isn't
       necessarily .fs-track itself (e.g. in "one at a time" mode .fs-track has no position of its
       own, so offsetLeft would land relative to .fs-strip and pick up its padding) — measuring via
       getBoundingClientRect instead is unambiguous regardless of the surrounding markup. */
    function leftIn(fig){
      return fig.getBoundingClientRect().left - track.getBoundingClientRect().left + track.scrollLeft;
    }
    let raf = 0;
    function move(){
      raf = 0;
      const p = progress();
      if(progI) progI.style.width = (p * 100) + "%";
      if(prevBtn) prevBtn.disabled = p <= 0.001;
      if(nextBtn) nextBtn.disabled = p >= 0.999;
    }
    function queue(){ if(!raf) raf = requestAnimationFrame(move); }
    function go(dir){
      const mid = track.clientWidth / 2, cur = progress() * span();
      const centers = figs.map(function(f){ return Math.min(span(), Math.max(0, leftIn(f) + f.offsetWidth/2 - mid)); });
      let tgt = dir > 0 ? centers.find(function(x){ return x > cur + 4; })
                         : centers.slice().reverse().find(function(x){ return x < cur - 4; });
      if(tgt == null) tgt = dir > 0 ? span() : 0;
      track.scrollTo({left: tgt, behavior: reducedQuery() ? "auto" : "smooth"});
    }
    if(prevBtn) prevBtn.addEventListener("click", function(){ go(-1); });
    if(nextBtn) nextBtn.addEventListener("click", function(){ go(1); });
    track.addEventListener("scroll", queue, {passive: true});
    track.addEventListener("keydown", function(e){
      if(e.key === "ArrowRight"){ e.preventDefault(); go(1); }
      if(e.key === "ArrowLeft"){ e.preventDefault(); go(-1); }
    });
    track.addEventListener("focusin", function(e){
      const f = e.target.closest("figure"); if(!f) return;
      const tgt = Math.min(span(), Math.max(0, leftIn(f) + f.offsetWidth/2 - track.clientWidth/2));
      track.scrollTo({left: tgt});
    });
    addEventListener("resize", queue);
    move();

    return {
      el: strip,
      destroy: function(){
        if(raf) cancelAnimationFrame(raf);
        removeEventListener("resize", queue);
        if(ownsViewer) vw.destroy();
      }
    };
  }

  global.FilmstripCarousel = { createFilmstrip: createFilmstrip, createViewer: createViewer, enhanceOneAtATime: enhanceOneAtATime };
})(window);
