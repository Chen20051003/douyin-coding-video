/* Shared Canvas helpers for the three compositions. Deterministic: no Date, no Math.random. */
(function (global) {
  const HF = {};
  HF.W = 1920;
  HF.H = 1080;
  HF.GOLD = "#C9A96A";
  HF.PAPER = "#EDE4D3";
  HF.INK = "#EAEAF2";
  HF.MUTED = "#8A8AA0";
  HF.RED = "#B53A2F";
  HF.GREEN = "#7FD6A4";
  HF.CYAN = "#78D7FF";
  HF.SANS = '"Noto Sans SC","Microsoft YaHei",sans-serif';
  HF.SERIF = '"Noto Serif SC","STZhongsong","SimSun",serif';
  HF.MONO = '"Consolas","Cascadia Mono",monospace';

  HF.clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  HF.lerp = (a, b, t) => a + (b - a) * t;
  HF.smoothstep = (a, b, x) => {
    const t = HF.clamp((x - a) / (b - a), 0, 1);
    return t * t * (3 - 2 * t);
  };
  HF.easeOutCubic = (t) => 1 - Math.pow(1 - t, 3);
  HF.easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  HF.easeOutExpo = (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t));
  HF.easeOutBack = (t) => {
    const c1 = 1.70158, c3 = c1 + 1;
    return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
  };
  HF.rng = (seed) => {
    let a = seed >>> 0;
    return function () {
      a |= 0;
      a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  };

  HF.setFont = (ctx, size, weight, family, italic) => {
    ctx.font = `${italic ? "italic " : ""}${weight} ${size}px ${family || HF.SANS}`;
  };

  HF.text = (ctx, str, x, y, o) => {
    o = o || {};
    const size = o.size || 24;
    const prev = ctx.globalAlpha;
    HF.setFont(ctx, size, o.weight || 400, o.family, o.italic);
    ctx.fillStyle = o.color || HF.INK;
    ctx.textAlign = o.align || "left";
    ctx.textBaseline = o.baseline || "alphabetic";
    ctx.globalAlpha = o.alpha == null ? prev : o.alpha;
    if (o.letterSpacing && "letterSpacing" in ctx) ctx.letterSpacing = o.letterSpacing + "px";
    ctx.fillText(str, x, y);
    if ("letterSpacing" in ctx) ctx.letterSpacing = "0px";
    ctx.globalAlpha = prev;
  };

  HF.wrap = (ctx, text, maxWidth) => {
    const lines = [];
    let line = "";
    for (const ch of text) {
      const test = line + ch;
      if (ctx.measureText(test).width > maxWidth && line) {
        lines.push(line);
        line = ch;
      } else line = test;
    }
    if (line) lines.push(line);
    return lines;
  };

  HF.roundRect = (ctx, x, y, w, h, r) => {
    r = Math.min(r, w / 2, h / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
  };

  HF.panel = (ctx, x, y, w, h, r, fill, stroke, lw) => {
    HF.roundRect(ctx, x, y, w, h, r || 14);
    ctx.fillStyle = fill || "rgba(12,12,26,0.92)";
    ctx.fill();
    if (stroke) {
      ctx.strokeStyle = stroke;
      ctx.lineWidth = lw || 1;
      ctx.stroke();
    }
  };

  HF.grainPattern = null;
  HF.makeGrain = () => {
    const c = document.createElement("canvas");
    c.width = c.height = 256;
    const g = c.getContext("2d");
    const img = g.createImageData(256, 256);
    const rand = HF.rng(918273);
    for (let i = 0; i < img.data.length; i += 4) {
      const v = 128 + (rand() - 0.5) * 80;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
      img.data[i + 3] = 255;
    }
    g.putImageData(img, 0, 0);
    HF.grainPattern = c;
  };

  HF.grain = (ctx, t, alpha) => {
    if (!HF.grainPattern) HF.makeGrain();
    ctx.save();
    ctx.globalAlpha = alpha == null ? 0.05 : alpha;
    ctx.globalCompositeOperation = "overlay";
    const ox = (t * 53) % 256, oy = (t * 37) % 256;
    const pat = ctx.createPattern(HF.grainPattern, "repeat");
    ctx.translate(-ox, -oy);
    ctx.fillStyle = pat;
    ctx.fillRect(0, 0, 2560, 1600);
    ctx.restore();
  };

  HF.vignette = (ctx, w, h) => {
    const g = ctx.createRadialGradient(w / 2, h / 2, h * 0.25, w / 2, h / 2, h * 0.85);
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(0,0,0,0.55)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  };

  HF.stars = (count, seed) => {
    const rand = HF.rng(seed);
    const arr = [];
    for (let i = 0; i < count; i++) {
      arr.push({
        x: rand() * HF.W,
        y: rand() * HF.H,
        r: 0.6 + rand() * 1.8,
        p: rand() * Math.PI * 2,
        s: 0.4 + rand() * 1.3,
        gold: rand() < 0.18,
      });
    }
    return arr;
  };

  HF.drawStars = (ctx, stars, t, alpha) => {
    for (const s of stars) {
      const tw = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(t * s.s + s.p));
      ctx.globalAlpha = tw * (alpha == null ? 0.55 : alpha);
      ctx.fillStyle = s.gold ? HF.GOLD : "#C7D2FF";
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.globalAlpha = 1;
  };

  HF.subtitle = (ctx, cn, en, t, start, end, W, H, o) => {
    o = o || {};
    if (t < start || t > end) return;
    const fade = 0.3;
    let a = 1;
    if (t < start + fade) a = (t - start) / fade;
    if (t > end - fade) a = Math.min(a, (end - t) / fade);
    a = HF.clamp(a, 0, 1);
    const rise = (1 - HF.easeOutCubic(HF.clamp((t - start) / 0.5, 0, 1))) * 10;
    const y = o.y || H * 0.862;
    ctx.save();
    ctx.globalAlpha = a;
    ctx.textAlign = "center";
    HF.setFont(ctx, o.cnSize || 46, 700, HF.SANS);
    ctx.fillStyle = o.cnColor || HF.INK;
    ctx.fillText(cn, W / 2, y + rise);
    HF.setFont(ctx, o.enSize || 24, 400, HF.SERIF, true);
    ctx.fillStyle = o.enColor || HF.MUTED;
    ctx.fillText(en, W / 2, y + (o.gap || 44) + rise);
    ctx.restore();
  };

  HF.header = (ctx, left, center, right, W, color) => {
    const c = color || HF.MUTED;
    ctx.save();
    ctx.globalAlpha = 0.9;
    HF.text(ctx, left, 64, 54, { size: 18, color: c, letterSpacing: 2.4 });
    HF.text(ctx, center, W / 2, 54, { size: 17, color: c, align: "center", letterSpacing: 4 });
    HF.text(ctx, right, W - 64, 54, { size: 16, color: c, align: "right", letterSpacing: 2.6 });
    ctx.strokeStyle = "rgba(201,169,106,0.15)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(64, 74);
    ctx.lineTo(W - 64, 74);
    ctx.stroke();
    ctx.restore();
  };

  HF.progress = (ctx, t, dur, W, H, color) => {
    const p = HF.clamp(t / dur, 0, 1);
    ctx.fillStyle = "rgba(255,255,255,0.08)";
    ctx.fillRect(0, H - 6, W, 3);
    ctx.fillStyle = color || HF.GOLD;
    ctx.fillRect(0, H - 6, W * p, 3);
    const g = ctx.createLinearGradient(W * p - 80, 0, W * p, 0);
    g.addColorStop(0, "rgba(201,169,106,0)");
    g.addColorStop(1, "rgba(201,169,106,0.8)");
    ctx.fillStyle = g;
    ctx.fillRect(Math.max(0, W * p - 80), H - 6, 80, 3);
  };

  HF.base = (ctx, t, duration) => {
    const g = ctx.createLinearGradient(0, 0, 0, HF.H);
    g.addColorStop(0, "#060610");
    g.addColorStop(0.55, "#0A0A1C");
    g.addColorStop(1, "#05050E");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, HF.W, HF.H);
    const glow = ctx.createRadialGradient(HF.W / 2, HF.H * 0.42, 40, HF.W / 2, HF.H * 0.42, HF.W * 0.55);
    glow.addColorStop(0, "rgba(39,44,96,0.28)");
    glow.addColorStop(1, "rgba(0,0,0,0)");
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, HF.W, HF.H);
  };

  HF.finishFrame = (ctx, t, duration) => {
    HF.grain(ctx, t, 0.045);
    HF.vignette(ctx, HF.W, HF.H);
    HF.progress(ctx, t, duration, HF.W, HF.H);
  };

  global.HF = HF;
})(window);
