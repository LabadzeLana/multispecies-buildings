/* Dogs page: continuous breathing ambient sound.
   Self-contained, passive module: it only listens to hashchange/visibility/media events and never
   calls into or modifies the page's own routing, hero, or video code. No external libraries.
   Loaded on every page via <script src>, but does nothing until the hash is exactly #/story/dogs. */
(function(){
  "use strict";

  /* ---- tunable constants ---- */
  var GAIN_MIN = 0.05;          /* quietest point of the breathing curve (0-1, fraction of full level) */
  var GAIN_MAX = 0.55;          /* loudest point of the breathing curve */
  var SWELL_MIN_S = 15;         /* shortest a single rise or fall may take, in seconds */
  var SWELL_MAX_S = 45;         /* longest a single rise or fall may take, in seconds */
  var ENTER_FADE_S = 3;         /* fade-in when the ambience starts (route enter, resume, toggled on) */
  var LEAVE_FADE_S = 1.5;       /* fade-out when leaving the Dogs route or hiding the tab */
  var DUCK_OUT_S = 0.6;         /* fade-out when another sound on the page starts */
  var DUCK_IN_S = 1.5;          /* fade-back-in once that other sound stops */

  /* media/dogs/dogs-ambience.{m4a,ogg}: already a seamless loop (crossfaded at the source), so a
     plain AudioBufferSourceNode with loop=true is all that's needed here */
  var SRC_M4A = "media/dogs/dogs-ambience.m4a";
  var SRC_OGG = "media/dogs/dogs-ambience.ogg";
  var SESSION_KEY = "msb.dogsAmbience.off";

  /* ---- route detection: passive, mirrors the page's own hash format without touching its router ---- */
  function onDogsRoute(){
    var h = location.hash.replace(/^#\/?/, "");
    var parts = h.split("/");
    return parts[0] === "story" && parts[1] === "dogs";
  }

  /* ---- state ---- */
  var ctx = null, unavailable = false;
  var masterGain = null, duckGain = null, breathGain = null;
  var buffer = null, bufferPromise = null, source = null;
  var active = false;            /* true while "on this route and should be audible" */
  var userOff = false;
  var breathTimer = null;
  var duckSources = new Set();   /* media elements currently making audible sound of their own */
  var gestureAttached = false;

  try { userOff = sessionStorage.getItem(SESSION_KEY) === "1"; } catch (e) {}

  function nowCtx(){ return ctx.currentTime; }

  function ensureContext(){
    if (ctx || unavailable) return ctx;
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) { unavailable = true; return null; }
      ctx = new AC();
      masterGain = ctx.createGain(); masterGain.gain.value = 0;
      duckGain = ctx.createGain(); duckGain.gain.value = 1;
      breathGain = ctx.createGain(); breathGain.gain.value = GAIN_MIN;
      breathGain.connect(duckGain); duckGain.connect(masterGain); masterGain.connect(ctx.destination);
    } catch (e) { unavailable = true; ctx = null; }
    return ctx;
  }

  function pickSrc(){
    try {
      var probe = document.createElement("audio");
      if (probe.canPlayType && probe.canPlayType('audio/mp4; codecs="mp4a.40.2"')) return SRC_M4A;
      if (probe.canPlayType && probe.canPlayType('audio/ogg; codecs="opus"')) return SRC_OGG;
    } catch (e) {}
    return SRC_M4A;
  }

  function loadBuffer(){
    if (bufferPromise) return bufferPromise;
    if (!ensureContext()) return Promise.reject(new Error("no audio context"));
    var url = pickSrc();
    bufferPromise = fetch(url).then(function(r){
      if (!r.ok) throw new Error("fetch failed");
      return r.arrayBuffer();
    }).then(function(ab){
      return new Promise(function(resolve, reject){
        ctx.decodeAudioData(ab, resolve, reject);
      });
    }).then(function(buf){ buffer = buf; return buf; })
      .catch(function(){ buffer = null; return null; });
    return bufferPromise;
  }

  /* ---- the slow, irregular "breathing" gain curve ---- */
  function scheduleBreath(){
    if (!ctx || unavailable) return;
    clearTimeout(breathTimer);
    var cur = breathGain.gain.value;
    var range = GAIN_MAX - GAIN_MIN;
    var target;
    var tries = 0;
    do {
      target = GAIN_MIN + Math.random() * range;
      tries++;
    } while (Math.abs(target - cur) < range * 0.25 && tries < 6);
    var dur = SWELL_MIN_S + Math.random() * (SWELL_MAX_S - SWELL_MIN_S);
    var t = nowCtx();
    breathGain.gain.cancelScheduledValues(t);
    breathGain.gain.setValueAtTime(cur, t);
    breathGain.gain.linearRampToValueAtTime(target, t + dur);
    breathTimer = setTimeout(scheduleBreath, dur * 1000);
  }
  function stopBreath(){ clearTimeout(breathTimer); breathTimer = null; }

  /* ---- starting / stopping the looping source ---- */
  function startSource(){
    if (!ctx || !buffer || source) return;
    source = ctx.createBufferSource();
    source.buffer = buffer;
    source.loop = true;
    source.connect(breathGain);
    try { source.start(0); } catch (e) { source = null; return; }
    if (!breathTimer) scheduleBreath();
  }
  function stopSource(){
    stopBreath();
    if (source) { try { source.stop(); } catch (e) {} try { source.disconnect(); } catch (e) {} source = null; }
  }

  function rampGain(node, target, seconds){
    if (!ctx) return;
    var t = nowCtx();
    node.gain.cancelScheduledValues(t);
    node.gain.setValueAtTime(node.gain.value, t);
    node.gain.linearRampToValueAtTime(target, t + Math.max(0.01, seconds));
  }

  /* ---- attempt to actually sound: needs a context, a decoded buffer, and nothing blocking it ---- */
  function tryAudible(fadeSeconds){
    if (!active || userOff || unavailable || !ctx) return;
    if (ctx.state !== "running") { armGestureUnlock(); return; }
    if (!buffer) { loadBuffer().then(function(){ if (active && !userOff) tryAudible(fadeSeconds); }); return; }
    startSource();
    rampGain(masterGain, 1, fadeSeconds == null ? ENTER_FADE_S : fadeSeconds);
  }

  function silence(fadeSeconds, andStop){
    if (!ctx) return;
    rampGain(masterGain, 0, fadeSeconds);
    if (andStop) setTimeout(stopSource, fadeSeconds * 1000 + 80);
  }

  /* ---- first-gesture unlock, only attached while actually needed ---- */
  var GESTURE_EVENTS = ["pointerdown", "touchend", "click", "keydown"];
  var GESTURE_OPTS = { capture: true, passive: true };
  function onGesture(){
    if (!ctx) return;
    ctx.resume().then(function(){
      disarmGestureUnlock();
      if (active && !userOff) tryAudible();
    }).catch(function(){});
  }
  function armGestureUnlock(){
    if (gestureAttached || !ctx) return;
    gestureAttached = true;
    GESTURE_EVENTS.forEach(function(ev){ document.addEventListener(ev, onGesture, GESTURE_OPTS); });
  }
  function disarmGestureUnlock(){
    if (!gestureAttached) return;
    gestureAttached = false;
    GESTURE_EVENTS.forEach(function(ev){ document.removeEventListener(ev, onGesture, GESTURE_OPTS); });
  }

  /* ---- route lifecycle ---- */
  function enterRoute(){
    if (active) return;
    active = true;
    if (!ensureContext()) return;
    loadBuffer();
    if (ctx.state !== "running") { ctx.resume().catch(function(){}); armGestureUnlock(); }
    tryAudible(ENTER_FADE_S);
    showToggle();
  }
  function leaveRoute(){
    if (!active) return;
    active = false;
    disarmGestureUnlock();
    silence(LEAVE_FADE_S, true);
    hideToggle();
  }
  function checkRoute(){ if (onDogsRoute()) enterRoute(); else leaveRoute(); }

  /* ---- tab visibility ---- */
  function onVisibility(){
    if (!ctx || !active) return;
    if (document.hidden) {
      silence(LEAVE_FADE_S, false);
      setTimeout(function(){ if (document.hidden) ctx.suspend().catch(function(){}); }, LEAVE_FADE_S * 1000 + 80);
    } else if (!userOff) {
      ctx.resume().then(function(){ tryAudible(ENTER_FADE_S); }).catch(function(){});
    }
  }

  /* ---- ducking: passively watch for other sound on the page ---- */
  function isAudible(m){ return !!m && !m.paused && !m.muted && m.volume > 0 && !m.ended; }
  function recomputeDuck(){
    var any = false;
    duckSources.forEach(function(m){ if (isAudible(m)) any = true; });
    if (!ctx) return;
    rampGain(duckGain, any ? 0 : 1, any ? DUCK_OUT_S : DUCK_IN_S);
  }
  function watchDuckSource(m){
    if (duckSources.has(m)) return;
    duckSources.add(m);
    ["play", "pause", "ended", "volumechange", "emptied"].forEach(function(ev){
      m.addEventListener(ev, recomputeDuck);
    });
    recomputeDuck();
  }
  function forgetDuckSource(m){
    if (!duckSources.has(m)) return;
    duckSources.delete(m);
    recomputeDuck();
  }
  var viewRoot = document.getElementById("view");
  if (viewRoot && "MutationObserver" in window) {
    new MutationObserver(function(muts){
      muts.forEach(function(mu){
        mu.addedNodes && mu.addedNodes.forEach(function(n){
          if (n.nodeType !== 1) return;
          if (n.matches && n.matches("video,audio")) watchDuckSource(n);
          if (n.querySelectorAll) n.querySelectorAll("video,audio").forEach(watchDuckSource);
        });
        mu.removedNodes && mu.removedNodes.forEach(function(n){
          if (n.nodeType !== 1) return;
          if (n.matches && n.matches("video,audio")) forgetDuckSource(n);
          if (n.querySelectorAll) n.querySelectorAll("video,audio").forEach(forgetDuckSource);
        });
      });
    }).observe(viewRoot, { childList: true, subtree: true });
  }

  /* ---- on/off control: built once, revealed only after the opening's own lock is lifted ---- */
  var toggleBtn = null;
  function buildToggle(){
    if (toggleBtn) return toggleBtn;
    var b = document.createElement("button");
    b.type = "button";
    b.className = "amb-toggle";
    b.innerHTML =
      '<svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">' +
        '<path d="M2 7v4h3l4 3.2V3.8L5 7H2z" fill="currentColor" stroke="none"/>' +
        '<g class="amb-waves" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round">' +
          '<path d="M11.3 6.2a4 4 0 0 1 0 5.6"/>' +
          '<path d="M13.1 4.3a7 7 0 0 1 0 9.4"/>' +
        '</g>' +
        '<path class="amb-off-mark" d="M11 6l4.5 6M15.5 6 11 12" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>' +
      '</svg>';
    b.addEventListener("click", function(){ setUserOff(!userOff); });
    document.body.appendChild(b);
    toggleBtn = b;
    syncToggle();
    return b;
  }
  function syncToggle(){
    if (!toggleBtn) return;
    var on = !userOff;
    toggleBtn.setAttribute("aria-pressed", String(on));
    toggleBtn.setAttribute("aria-label", on ? "Sound on" : "Sound off");
  }
  function setUserOff(off){
    userOff = off;
    try {
      if (off) sessionStorage.setItem(SESSION_KEY, "1");
      else sessionStorage.removeItem(SESSION_KEY);
    } catch (e) {}
    syncToggle();
    if (off) silence(LEAVE_FADE_S, true);
    else if (active) tryAudible(ENTER_FADE_S);
  }
  var lockObserver = null;
  function showToggle(){
    buildToggle();
    /* This script tag loads before the page's own <script>, so on a fresh load the opening's
       stLock(true) (which sets html.st-locked) may not have run yet at this exact point — watch
       for the class first, then settle the initial state on the next tick, by which time the
       main script's own hashchange/init handling (same dispatch, or same parse pass) has run. */
    if ("MutationObserver" in window && !lockObserver) {
      lockObserver = new MutationObserver(function(){
        toggleBtn.classList.toggle("amb-show", !document.documentElement.classList.contains("st-locked"));
      });
      lockObserver.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    }
    setTimeout(function(){
      if (!active) return;
      toggleBtn.classList.toggle("amb-show", !document.documentElement.classList.contains("st-locked"));
    }, 0);
  }
  function hideToggle(){
    if (lockObserver) { lockObserver.disconnect(); lockObserver = null; }
    if (toggleBtn) toggleBtn.classList.remove("amb-show");
  }

  /* ---- wire up: passive listeners only ---- */
  window.addEventListener("hashchange", checkRoute);
  document.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("pagehide", function(){ if (active) { silence(LEAVE_FADE_S, true); } });
  checkRoute();
})();
