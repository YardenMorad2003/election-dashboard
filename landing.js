/* Landing "instrument": dot-map of Israel from real locality results
   (data/landing_points.json, built by analysis/build_landing_points.py),
   year scrubber 1992-2022, hover/click, locality search.
   Config via window.LANDING = {en, mapHref, strings:{...}} set by the page.
   On the English page the builder's fetch-shim translates locality names
   inside the JSON, so search and tooltips show English automatically. */
(function () {
    'use strict';
    var CFG = window.LANDING || {};
    var EN = !!CFG.en;
    var S = CFG.strings || {};
    var KS = ['13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25'];
    var KYEAR = {};
    // K21/K22 both 2019 (April / September)
    var KSUB = { 21: EN ? 'Apr' : '\u05D0\u05E4\u05E8\u05F3', 22: EN ? 'Sep' : '\u05E1\u05E4\u05D8\u05F3' };

    var canvas = document.getElementById('labCanvas');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var tip = document.getElementById('labTip');
    var yearEl = document.getElementById('labYear');
    var knEl = document.getElementById('labKnesset');
    var barEl = document.getElementById('blocBar');
    var scrubEl = document.getElementById('scrub');
    var playBtn = document.getElementById('playBtn');
    var searchEl = document.getElementById('locSearch');
    var dropEl = document.getElementById('locDrop');

    var REDUCED = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var COARSE = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;

    // colors
    var C_RH = [91, 157, 255];    // right-haredi  (accent blue)
    var C_CLA = [255, 107, 107];  // center-left-arab (red)
    var C_MID = [64, 72, 92];     // even
    function lerp(a, b, t) { return a + (b - a) * t; }
    function mix(c1, c2, t) { return [lerp(c1[0], c2[0], t), lerp(c1[1], c2[1], t), lerp(c1[2], c2[2], t)]; }
    function marginColor(m) { // m = rh - cla in pp
        var t = Math.max(-1, Math.min(1, m / 55));
        return t >= 0 ? mix(C_MID, C_RH, t) : mix(C_MID, C_CLA, -t);
    }

    var P = [];            // points: {n, x(lon), y(lat), e:{k:[rh,cla,to,el]}}
    var cur = [], tgt = [];// per-point [r,g,b,rad,alpha]
    var curK = '25';
    var hoverI = -1, pinI = -1;
    var NAT = null;
    var animId = null, playTimer = null;

    // ---------- data ----------
    fetch('data/landing_points.json').then(function (r) { return r.json(); }).then(function (d) {
        KYEAR = d.years || {};
        NAT = d.national || {};
        P = d.pts || [];
        P.forEach(function (p) {
            var mx = 0;
            KS.forEach(function (k) { if (p.e[k] && p.e[k][3] > mx) mx = p.e[k][3]; });
            p.mxEl = mx;
        });
        cur = P.map(function () { return [10, 12, 16, 0, 0]; });
        buildScrub();
        layout();
        setYear('25', true);
    }).catch(function (e) {
        var m = document.querySelector('.lab-map');
        if (m) m.style.display = 'none';
        console.warn('landing map unavailable:', e);
    });

    // ---------- projection / layout ----------
    var VIEW = { minLon: 34.15, maxLon: 35.95, minLat: 29.45, maxLat: 33.45 };
    var DPR = 1, W = 0, H = 0;
    function layout() {
        DPR = window.devicePixelRatio || 1;
        var box = canvas.parentElement.getBoundingClientRect();
        W = Math.max(200, box.width); H = Math.max(300, box.height);
        canvas.width = W * DPR; canvas.height = H * DPR;
        canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
        var pad = 14;
        var kx = Math.cos(31.5 * Math.PI / 180);
        var dx = (VIEW.maxLon - VIEW.minLon) * kx;
        var dy = VIEW.maxLat - VIEW.minLat;
        var sc = Math.min((W - pad * 2) / dx, (H - pad * 2) / dy);
        var ox = (W - dx * sc) / 2, oy = (H - dy * sc) / 2;
        var maxEl = 0;
        P.forEach(function (p) { if (p.mxEl > maxEl) maxEl = p.mxEl; });
        var rK = 5.4 / Math.sqrt(maxEl || 1);
        P.forEach(function (p) {
            p.px = ox + (p.x - VIEW.minLon) * kx * sc;
            p.py = oy + (VIEW.maxLat - p.y) * sc;
            p.rBase = rK;
        });
        draw();
    }
    if (window.ResizeObserver) new ResizeObserver(function () { layout(); }).observe(canvas.parentElement);

    // ---------- year state ----------
    function targetsFor(k) {
        return P.map(function (p) {
            var e = p.e[k];
            if (!e) return [10, 12, 16, 0, 0];
            var col = marginColor(e[0] - e[1]);
            var rad = 1.5 + Math.sqrt(e[3] || 1) * p.rBase;
            return [col[0], col[1], col[2], Math.min(rad, 7.5), 0.9];
        });
    }
    function setYear(k, instant) {
        curK = k;
        tgt = targetsFor(k);
        updateReadout(k);
        updateScrub(k);
        if (instant || REDUCED) { cur = tgt.map(function (t) { return t.slice(); }); draw(); return; }
        if (animId) cancelAnimationFrame(animId);
        var t0 = performance.now(), DUR = 420;
        var from = cur.map(function (c) { return c.slice(); });
        function step(now) {
            var t = Math.min(1, (now - t0) / DUR);
            var e = t * (2 - t); // easeOut
            for (var i = 0; i < P.length; i++)
                for (var j = 0; j < 5; j++) cur[i][j] = lerp(from[i][j], tgt[i][j], e);
            draw();
            if (t < 1) animId = requestAnimationFrame(step); else animId = null;
        }
        animId = requestAnimationFrame(step);
    }

    function updateReadout(k) {
        if (yearEl) yearEl.textContent = KYEAR[k] + (KSUB[k] ? ' ' + KSUB[k] : '');
        if (knEl) knEl.textContent = (EN ? 'Knesset ' : '\u05DB\u05E0\u05E1\u05EA\u0020') + k;
        var nb = NAT && NAT[k];
        if (barEl && nb) {
            barEl.innerHTML =
                '<div class="bb-labels"><span class="bb-rh">' + S.rh + ' <b class="n">' + nb.rh.toFixed(1) + '%</b></span>' +
                '<span class="bb-cla">' + S.cla + ' <b class="n">' + nb.cla.toFixed(1) + '%</b></span></div>' +
                '<div class="bb-track"><span class="bb-seg rh" style="width:' + nb.rh + '%"></span><span class="bb-seg cla" style="width:' + nb.cla + '%"></span></div>';
        }
    }

    // ---------- draw ----------
    function draw() {
        ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
        ctx.clearRect(0, 0, W, H);
        for (var i = 0; i < P.length; i++) {
            var c = cur[i];
            if (c[4] <= 0.01 || c[3] <= 0.05) continue;
            ctx.globalAlpha = c[4];
            ctx.fillStyle = 'rgb(' + (c[0] | 0) + ',' + (c[1] | 0) + ',' + (c[2] | 0) + ')';
            ctx.beginPath();
            ctx.arc(P[i].px, P[i].py, c[3], 0, 6.2832);
            ctx.fill();
        }
        ctx.globalAlpha = 1;
        var ring = pinI >= 0 ? pinI : hoverI;
        if (ring >= 0) {
            var p = P[ring], cc = cur[ring];
            ctx.strokeStyle = '#e9edf4';
            ctx.lineWidth = 1.4;
            ctx.beginPath();
            ctx.arc(p.px, p.py, (cc[3] || 2) + 3.5, 0, 6.2832);
            ctx.stroke();
        }
    }

    // ---------- hover / click ----------
    function nearest(mx, my) {
        var best = -1, bd = COARSE ? 676 : 169; // 26px^2 for fingers, 13px^2 for a mouse
        for (var i = 0; i < P.length; i++) {
            if (!P[i].e[curK]) continue;
            var dx = P[i].px - mx, dy = P[i].py - my, dd = dx * dx + dy * dy;
            if (dd < bd) { bd = dd; best = i; }
        }
        return best;
    }
    function tipHTML(i, withLink) {
        var p = P[i], e = p.e[curK];
        if (!e) return '';
        var h = '<b>' + p.n + '</b><span class="t-yr n">' + KYEAR[curK] + '</span>' +
            '<div class="t-row"><i class="sw rh"></i>' + S.rh + ' <b class="n">' + e[0].toFixed(1) + '%</b></div>' +
            '<div class="t-row"><i class="sw cla"></i>' + S.cla + ' <b class="n">' + e[1].toFixed(1) + '%</b></div>' +
            (e[2] != null ? '<div class="t-row t-to">' + S.turnout + ' <b class="n">' + e[2].toFixed(1) + '%</b></div>' : '');
        if (withLink) h += '<a class="t-link" href="' + (CFG.mapHref || 'election_map.html') + '#k=' + curK +
            '&loc=' + (p.s != null ? p.s : encodeURIComponent(p.n)) + '">' + S.openMap + ' <span class="arr">' + (EN ? '→' : '←') + '</span></a>';
        return h;
    }
    function placeTip(i) {
        var p = P[i];
        tip.style.display = 'block';
        var tw = tip.offsetWidth, th = tip.offsetHeight;
        var x = p.px + 14, y = p.py - th / 2;
        if (x + tw > W - 8) x = p.px - tw - 14;
        y = Math.max(8, Math.min(H - th - 8, y));
        tip.style.left = x + 'px'; tip.style.top = y + 'px';
    }
    canvas.addEventListener('mousemove', function (ev) {
        var r = canvas.getBoundingClientRect();
        var i = nearest(ev.clientX - r.left, ev.clientY - r.top);
        if (i !== hoverI) {
            hoverI = i;
            canvas.style.cursor = i >= 0 ? 'pointer' : 'default';
            if (pinI < 0) {
                if (i >= 0) { tip.innerHTML = tipHTML(i, false); placeTip(i); }
                else tip.style.display = 'none';
            }
            draw();
        }
    });
    canvas.addEventListener('mouseleave', function () {
        hoverI = -1; if (pinI < 0) tip.style.display = 'none';
        canvas.style.cursor = 'default'; draw();
    });
    canvas.addEventListener('click', function (ev) {
        var r = canvas.getBoundingClientRect();
        var i = nearest(ev.clientX - r.left, ev.clientY - r.top);
        if (i >= 0) pin(i); else unpin();
    });
    function pin(i) {
        pinI = i;
        tip.innerHTML = tipHTML(i, true);
        placeTip(i);
        draw();
    }
    function unpin() { pinI = -1; tip.style.display = 'none'; draw(); }

    // ---------- scrubber ----------
    function buildScrub() {
        if (!scrubEl) return;
        scrubEl.innerHTML = KS.map(function (k) {
            var lab = KYEAR[k] + (KSUB[k] ? '<small>' + KSUB[k] + '</small>' : '');
            return '<button class="tick" data-k="' + k + '" aria-label="' + KYEAR[k] + '"><span class="dot"></span><span class="tlab n">' + lab + '</span></button>';
        }).join('');
        scrubEl.addEventListener('click', function (ev) {
            var b = ev.target.closest('.tick');
            if (b) { stopPlay(); setYear(b.dataset.k); refreshPin(); }
        });
        scrubEl.tabIndex = 0;
        scrubEl.addEventListener('keydown', function (ev) {
            var i = KS.indexOf(curK), dir = 0;
            // forward = reading direction
            if (ev.key === 'ArrowLeft') dir = EN ? -1 : 1;
            if (ev.key === 'ArrowRight') dir = EN ? 1 : -1;
            if (!dir) return;
            ev.preventDefault(); stopPlay();
            var ni = Math.max(0, Math.min(KS.length - 1, i + dir));
            if (ni !== i) { setYear(KS[ni]); refreshPin(); }
        });
        // drag across ticks
        var dragging = false;
        scrubEl.addEventListener('pointerdown', function (ev) { dragging = true; hitTick(ev); });
        window.addEventListener('pointermove', function (ev) { if (dragging) hitTick(ev); });
        window.addEventListener('pointerup', function () { dragging = false; });
        function hitTick(ev) {
            var el = document.elementFromPoint(ev.clientX, ev.clientY);
            var b = el && el.closest ? el.closest('.tick') : null;
            if (b && b.dataset.k !== curK) { stopPlay(); setYear(b.dataset.k); refreshPin(); }
        }
    }
    function updateScrub(k) {
        if (!scrubEl) return;
        scrubEl.querySelectorAll('.tick').forEach(function (b) {
            b.classList.toggle('on', b.dataset.k === k);
        });
    }
    function refreshPin() {
        if (pinI >= 0) {
            if (P[pinI].e[curK]) { tip.innerHTML = tipHTML(pinI, true); placeTip(pinI); }
            else tip.style.display = 'none';
        }
    }

    // ---------- play ----------
    function stopPlay() {
        if (playTimer) { clearInterval(playTimer); playTimer = null; }
        if (playBtn) { playBtn.classList.remove('playing'); playBtn.textContent = '▶'; }
    }
    if (playBtn) playBtn.addEventListener('click', function () {
        if (playTimer) { stopPlay(); return; }
        var i = KS.indexOf(curK);
        if (i >= KS.length - 1) i = -1; // restart from 1992
        playBtn.classList.add('playing'); playBtn.textContent = '⏸';
        var advance = function () {
            i++;
            if (i >= KS.length) { stopPlay(); return; }
            setYear(KS[i]); refreshPin();
        };
        advance();
        playTimer = setInterval(advance, REDUCED ? 1400 : 850);
    });

    // ---------- search ----------
    if (searchEl && dropEl) {
        var items = [];
        var select = function (i) {
            dropEl.style.display = 'none';
            searchEl.value = P[i].n;
            pin(i);
        };
        searchEl.addEventListener('input', function () {
            var q = searchEl.value.trim();
            if (q.length < 1) { dropEl.style.display = 'none'; return; }
            items = [];
            for (var i = 0; i < P.length && items.length < 8; i++)
                if (P[i].n.indexOf(q) === 0) items.push(i);
            for (i = 0; i < P.length && items.length < 8; i++)
                if (P[i].n.indexOf(q) > 0 && items.indexOf(i) < 0) items.push(i);
            if (!items.length) { dropEl.style.display = 'none'; return; }
            dropEl.innerHTML = items.map(function (pi) {
                return '<button class="d-it" data-i="' + pi + '">' + P[pi].n + '</button>';
            }).join('');
            dropEl.style.display = 'block';
        });
        dropEl.addEventListener('click', function (ev) {
            var b = ev.target.closest('.d-it');
            if (b) select(parseInt(b.dataset.i, 10));
        });
        searchEl.addEventListener('keydown', function (ev) {
            if (ev.key === 'Enter' && items.length) { ev.preventDefault(); select(items[0]); }
            if (ev.key === 'Escape') { dropEl.style.display = 'none'; }
        });
        document.addEventListener('click', function (ev) {
            if (!ev.target.closest('.search-row')) dropEl.style.display = 'none';
        });
    }
})();
