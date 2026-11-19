import React, { useEffect, useState } from 'react';
import { AbsoluteFill, Audio, Img, Sequence, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

// Vertical (1080×1920) history / legend short from real archive pictures. Layout of the approved sample
// (00-video-mau/MAU-EDIT-20S.mp4): gold bar + small label (place / kind of document), large title, the picture in
// the middle, rings that are drawn when the voice names a detail, the subtitle under the picture, the credit at the
// foot. Cuts on the idea; with "fade" (seconds, script.json) the next picture dissolves in over the last one instead
// ("dựng liền mạch", owner 14/11). Positions come from scripts/arc/layout.py via build.py.
// Themes (script.json "style"): "paper" (default, chosen by the owner 13/11: ivory archive paper, ink text, the picture
// as a print with a white mat, red rings), "warm" (the picture itself, blurred and darkened, fills the background, so
// every shot has its own colour; the picture floats with a shadow and a gold frame), "classic" (the flat dark brown of
// the sample).
type View = [number, number, number, number];
export type PicBox = { src: string; w: number; h: number; box: [number, number, number, number]; view: View;
  zoom?: { to: View; s: number; e: number }; drift?: number; move?: { from: View; to: View } };
export type Mark = { s: number; box: View; shape: 'ellipse' | 'rect'; on: number };
export type Shot = { s: number; e: number; scene: number; shot: number; label: string; title: string; titleSize: number;
  caption: string; credit: string; bar: number; captionY: number | null; subY: number; pics: PicBox[]; marks: Mark[]; newScene?: boolean;
  edit?: string /* name of the catalogue edit (scripts/arc/edits.py): for the preview and the shot sheet, not drawn */ };
export type Sub = { s: number; e: number; text: string; hl?: string[] };
type FontChunk = { family: string; file: string; range: string };
export type PlanA = { duration: number; shots: Shot[]; subs: Sub[]; voice: { s: number; src: string }[]; music: string | null;
  musicVolume: number; fonts: FontChunk[]; theme?: string; total?: number; fade?: number;
  hook?: { text: string; s: number; e: number; hl?: string[] }; cards?: { text: string; s: number; e: number; hl?: string[] }[];
  intro?: { title: string; items: { src: string; w: number; h: number; name: string }[]; pick: number; mid: number; e: number; credit?: string };
  grain?: string; sfx?: string;
  // the fixed header of the legend videos (owner 19/11): label + title at the top for the whole video, brush font
  head?: { label: string; title: string; hl?: string[] }; display?: string; subSize?: number };

type Theme = { wash?: number; grade?: string; backdropFilter?: string; vig?: boolean; outline?: number; shake?: boolean; bg: string; bgCss?: string; bar: string; label: string; title: string; sub: string; subHl: string; subShadow: string; credit: string;
  ring: string; frame: string; mat: number; shadow: string; backdrop: boolean; subWeight: number; titleShadow: string };
export const THEMES: Record<string, Theme> = {
  warm: { bg: '#1b1410', bar: '#e9be86', label: '#f0c995', title: '#fff6e6', sub: '#fffaf0', subHl: '#f2c67f',
    subShadow: '0 2px 14px rgba(0,0,0,.75), 0 0 3px rgba(0,0,0,.6)', credit: 'rgba(235,225,212,.8)', ring: '#f2c070',
    frame: '2px solid rgba(240,201,149,.85)', mat: 0, shadow: '0 28px 70px rgba(0,0,0,.65), 0 6px 18px rgba(0,0,0,.45)',
    backdrop: true, subWeight: 500, titleShadow: '0 4px 24px rgba(0,0,0,.55)' },
  paper: { wash: 0.3, bg: '#efe5cf', bgCss: 'radial-gradient(ellipse 90% 75% at 50% 42%, #f7f0de 0%, #efe5cf 55%, #dccdaa 100%)', bar: '#a8432a', label: '#9c3f26', title: '#2b1d12', sub: '#24180f', subHl: '#a8432a',
    subShadow: 'none', credit: 'rgba(80,62,45,.85)', ring: '#c0392b', frame: '1px solid rgba(60,40,20,.25)', mat: 12,
    shadow: '0 18px 40px rgba(70,45,20,.35), 0 3px 8px rgba(70,45,20,.25)', backdrop: false, subWeight: 500, titleShadow: 'none' },
  // owner 18/11 (urban legends: "hình ảnh phải phù hợp với kịch bản kinh dị"): black with a dark red glow, the pictures
  // darkened and cold with dark edges, film grain and a faint flicker, blood-red key words, white outlined subtitles
  horror: { grade: 'saturate(.5) contrast(1.15) brightness(.8)', backdropFilter: 'blur(40px) saturate(.35) brightness(.3)', vig: true, outline: 5, shake: true,
    bg: '#070505', bgCss: 'radial-gradient(ellipse 95% 70% at 50% 42%, #220a0a 0%, #0c0505 55%, #000000 100%)', bar: '#c1121f', label: '#b5aca6', title: '#f4eee8',
    sub: '#ffffff', subHl: '#ff3324', subShadow: 'none', credit: 'rgba(190,182,176,.6)', ring: '#ff2a2a', frame: '1px solid rgba(255,255,255,.2)', mat: 0,
    shadow: '0 30px 90px rgba(0,0,0,.9), 0 0 60px rgba(120,0,0,.25)', backdrop: true, subWeight: 700, titleShadow: '0 4px 22px rgba(0,0,0,.8)' },
  classic: { bg: '#211a18', bar: '#e9be86', label: '#efc391', title: '#fbf6ea', sub: '#fffdf5', subHl: '#f2c67f',
    subShadow: '0 2px 10px rgba(0,0,0,.45)', credit: 'rgba(214,205,200,.82)', ring: '#e6b46e', frame: '1.5px solid rgba(214,190,156,.62)',
    mat: 0, shadow: 'none', backdrop: false, subWeight: 400, titleShadow: 'none' },
};
const SERIF = '"Noto Serif JP", serif', SANS = '"Noto Sans JP", sans-serif';
const M = 69;
const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ease = (x: number) => { const p = clamp01(x); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const easeOut = (x: number) => 1 - Math.pow(1 - clamp01(x), 3);
const easeSine = (x: number) => (1 - Math.cos(Math.PI * clamp01(x))) / 2;
const rnd = (n: number) => { const x = Math.sin(n * 12.9898) * 43758.5453; return x - Math.floor(x); };   // the same for a frame on every render
const outlineOf = (r: number) => Array.from({ length: 16 }, (_, i) => { const a = (i / 16) * 2 * Math.PI;
  return `${(Math.cos(a) * r).toFixed(1)}px ${(Math.sin(a) * r).toFixed(1)}px 0 #000`; }).join(', ') + ', 0 6px 16px rgba(0,0,0,.6)';

let fontsLoading: Promise<void> | null = null;
const useFonts = (fonts: FontChunk[], text: string, display?: string) => {
  const [h] = useState(() => delayRender('JP fonts'));
  useEffect(() => {
    (fontsLoading ??= (async () => {
      for (const f of fonts)
        document.fonts.add(new FontFace(f.family, `url(${staticFile(f.file)}) format('woff2')`, { weight: '100 900', unicodeRange: f.range }));
      await Promise.all([700, 500, 400].flatMap((wt) => [document.fonts.load(`${wt} 60px ${SERIF}`, text), document.fonts.load(`${wt} 40px ${SANS}`, text)]));
      if (display) await document.fonts.load(`400 60px "${display}"`, text);
    })()).then(() => continueRender(h)).catch((e) => cancelRender(e));
  }, [h, fonts, text]);
};

// region of the picture shown at time t: a zoom when asked for, else a slow drift (push-in by `drift` over the shot)
export const viewAt = (p: PicBox, t: number, s: number, e: number): View => {
  if (p.zoom) {
    const k = ease((t - p.zoom.s) / Math.max(0.1, p.zoom.e - p.zoom.s));
    return p.view.map((v, i) => v + (p.zoom!.to[i] - v) * k) as View;
  }
  if (p.move) {   // pan across a wide picture, or push in / pull out (owner 17/11: more motion), over the whole shot
    const k = easeSine((t - s) / Math.max(0.5, e - s));
    return p.move.from.map((v, i) => v + (p.move!.to[i] - v) * k) as View;
  }
  if (!p.drift) return p.view;
  const k = clamp01((t - s) / Math.max(0.5, e - s)) * p.drift / 2;
  const [a, b, c, d] = p.view, w = c - a, h = d - b;
  return [a + w * k, b + h * k, c - w * k, d - h * k];
};

const PicView: React.FC<{ p: PicBox; t: number; sh: Shot; th: Theme; marks: Mark[] }> = ({ p, t, sh, th, marks }) => {
  const [x, y, bw, bh] = p.box;
  const [v0, v1, v2, v3] = viewAt(p, t, sh.s, sh.e);
  const sx = bw / ((v2 - v0) * p.w), sy = bh / ((v3 - v1) * p.h);
  const m = th.mat;
  return (
    <div style={{ position: 'absolute', left: x - m, top: y - m, width: bw + 2 * m, height: bh + 2 * m, background: m ? '#fbf8f1' : 'transparent', boxShadow: th.shadow, border: th.frame, boxSizing: 'content-box', marginLeft: -1, marginTop: -1 }}>
      <div style={{ position: 'absolute', left: m, top: m, width: bw, height: bh, overflow: 'hidden', background: '#000' }}>
        <Img src={staticFile(p.src)} style={{ position: 'absolute', left: -v0 * p.w * sx, top: -v1 * p.h * sy, width: p.w * sx, height: p.h * sy, maxWidth: 'none', filter: th.grade }} />
        {th.vig ? <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 75% 75% at 50% 50%, rgba(0,0,0,0) 45%, rgba(0,0,0,.62) 100%)' }} /> : null}
        <svg width={bw} height={bh} style={{ position: 'absolute', left: 0, top: 0 }}>
          {marks.filter((mk) => t >= mk.s).map((mk, i) => {
            const X = (f: number) => ((f - v0) / (v2 - v0)) * bw, Y = (f: number) => ((f - v1) / (v3 - v1)) * bh;
            const [a, b, c, d] = mk.box;
            const draw = easeOut((t - mk.s) / 0.5);   // the ring is drawn round in half a second
            const st = { fill: 'none', stroke: th.ring, strokeWidth: 5, strokeLinecap: 'round' as const, strokeDasharray: 1, strokeDashoffset: 1 - draw,
              filter: 'drop-shadow(0 0 4px rgba(0,0,0,.6))' };
            return mk.shape === 'rect'
              ? <rect key={i} pathLength={1} x={X(a)} y={Y(b)} width={X(c) - X(a)} height={Y(d) - Y(b)} rx={6} style={st} />
              // turned by -90° so the ring starts drawing at the top: its radii are swapped to keep the box's shape
              : <ellipse key={i} pathLength={1} cx={(X(a) + X(c)) / 2} cy={(Y(b) + Y(d)) / 2} rx={(Y(d) - Y(b)) / 2} ry={(X(c) - X(a)) / 2}
                  transform={`rotate(-90 ${(X(a) + X(c)) / 2} ${(Y(b) + Y(d)) / 2})`} style={st} />;
          })}
        </svg>
      </div>
    </div>
  );
};

// the shot's own picture, blurred and darkened, as the background (warm theme)
const Backdrop: React.FC<{ p: PicBox; t: number; sh: Shot; filter?: string }> = ({ p, t, sh, filter }) => {
  const k = clamp01((t - sh.s) / Math.max(0.5, sh.e - sh.s));
  const c = Math.max(1080 / p.w, 1920 / p.h) * 1.25, w = p.w * c, h = p.h * c;
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <Img src={staticFile(p.src)} style={{ position: 'absolute', left: (1080 - w) / 2, top: (1920 - h) / 2, width: w, height: h, maxWidth: 'none',
        filter: filter || 'blur(36px) saturate(1.45) brightness(.62)', transform: `scale(${1 + 0.04 * k})` }} />
      <AbsoluteFill style={{ background: 'linear-gradient(180deg, rgba(20,14,10,.55) 0%, rgba(20,14,10,.18) 30%, rgba(20,14,10,.2) 62%, rgba(14,10,8,.78) 100%)' }} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.5) 100%)' }} />
    </AbsoluteFill>
  );
};

// paper theme (owner 17/11): the shot's picture, blurred, sepia and faint, over the paper, slowly growing
const Wash: React.FC<{ p: PicBox; t: number; sh: Shot; o: number }> = ({ p, t, sh, o }) => {
  const k = clamp01((t - sh.s) / Math.max(0.5, sh.e - sh.s));
  const c = Math.max(1080 / p.w, 1920 / p.h) * 1.15, w = p.w * c, h = p.h * c;
  return (
    <AbsoluteFill style={{ overflow: 'hidden', opacity: o }}>
      <Img src={staticFile(p.src)} style={{ position: 'absolute', left: (1080 - w) / 2, top: (1920 - h) / 2, width: w, height: h, maxWidth: 'none',
        filter: 'blur(28px) sepia(.55) saturate(1.1)', transform: `scale(${1.02 + 0.06 * k})` }} />
    </AbsoluteFill>
  );
};

// the hook: the picture darkened, the words very large in the middle of it — fully there on the very first frame (the
// feed shows it), with a small punch (scale 1.08 → 1 in 0.25 s); key words in the theme's highlight colour; it fades
// out in 0.35 s when the first line has been said
const Hook: React.FC<{ hk: { text: string; s: number; e: number; hl?: string[] }; t: number; on: number; box: number[]; color: string; font?: string }> = ({ hk, t, on, box, color, font }) => {
  const k = easeOut((t - hk.s) / 0.25), sc = 1.08 - 0.08 * k;
  const rows = hk.text.split('\n');
  const n = Math.max(...rows.map((r) => [...r].reduce((a, c) => a + (c.charCodeAt(0) < 0x2000 ? 0.55 : 1), 0)));
  const size = Math.min(150, Math.floor(980 / Math.max(1, n) / 1.04 / 1.08));
  const ring = Array.from({ length: 16 }, (_, i) => { const a = (i / 16) * 2 * Math.PI; return `${(Math.cos(a) * 7).toFixed(1)}px ${(Math.sin(a) * 7).toFixed(1)}px 0 #000`; }).join(', ');
  return (
    <AbsoluteFill style={{ opacity: on }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: box[1] - 40, height: box[3] + 80, background: 'radial-gradient(ellipse 75% 60% at 50% 50%, rgba(0,0,0,.55) 0%, rgba(0,0,0,.25) 70%, rgba(0,0,0,0) 100%)' }} />
      <div style={{ position: 'absolute', left: 30, right: 30, top: box[1] + box[3] / 2, transform: `translateY(-50%) scale(${sc})`,
        textAlign: 'center', fontFamily: font || SERIF, fontWeight: font ? 400 : 900, fontSize: size, lineHeight: 1.18, color: '#ffffff', letterSpacing: '0.03em',
        textShadow: `${ring}, 0 10px 30px rgba(0,0,0,.6)` }}>
        {rows.map((r, i) => <div key={i}><Highlight text={r} hl={hk.hl || []} color={color} /></div>)}
      </div>
    </AbsoluteFill>
  );
};

// the intro: the series' board — a title, four pictures with their names; this video's one lights up when it is named
const Intro: React.FC<{ it: NonNullable<PlanA['intro']>; t: number; th: Theme; on: number }> = ({ it, t, th, on }) => {
  const k = easeOut((t - it.mid) / 0.3), picked = t >= it.mid;
  const rows = it.title.split('\n');
  const n = Math.max(1, ...rows.map((r) => [...r].reduce((a, c) => a + (c.charCodeAt(0) < 0x2000 ? 0.55 : 1), 0)));
  const size = Math.min(104, Math.floor(980 / n / 1.04));
  const TW = 470, TH = 440, X = [56, 554], Y = [392, 928];
  return (
    <AbsoluteFill style={{ opacity: on, background: th.bgCss || th.bg }}>
      <div style={{ position: 'absolute', left: 30, right: 30, top: 250 - (rows.length * size * 1.2) / 2, textAlign: 'center', fontFamily: SERIF, fontWeight: 900, fontSize: size, lineHeight: 1.2,
        color: th.title, letterSpacing: '0.03em', textShadow: outlineOf(5) }}>
        {rows.map((r, i) => <div key={i} style={{ color: i === rows.length - 1 && rows.length > 1 ? th.subHl : th.title }}>{r}</div>)}
      </div>
      {it.items.map((p, i) => {
        const me = i === it.pick, x = X[i % 2], y = Y[Math.floor(i / 2)];
        const c = Math.max(TW / p.w, TH / p.h), w = p.w * c, h = p.h * c;
        const pop = 0.95 + 0.05 * easeOut((t - 0.08 * i) / 0.3), sc = pop * (picked && me ? 1 + 0.06 * k : 1);
        return (
          <div key={i} style={{ position: 'absolute', left: x, top: y, width: TW, opacity: picked && !me ? 1 - 0.72 * k : 1, transform: `scale(${sc})`, transformOrigin: `${TW / 2}px ${TH / 2}px`, zIndex: me ? 2 : 1 }}>
            <div style={{ position: 'relative', width: TW, height: TH, overflow: 'hidden', background: '#000',
              border: picked && me ? `5px solid ${th.ring}` : '2px solid rgba(255,255,255,.28)', boxSizing: 'border-box',
              boxShadow: picked && me ? `0 0 50px ${th.ring}` : '0 14px 40px rgba(0,0,0,.6)' }}>
              <Img src={staticFile(p.src)} style={{ position: 'absolute', left: (TW - w) / 2, top: (TH - h) / 2, width: w, height: h, maxWidth: 'none', filter: th.grade }} />
              <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse 80% 80% at 50% 45%, rgba(0,0,0,0) 40%, rgba(0,0,0,.6) 100%)' }} />
              <div style={{ position: 'absolute', left: 12, top: 6, fontFamily: SERIF, fontWeight: 900, fontSize: 60, color: picked && me ? th.subHl : '#fff', textShadow: outlineOf(4) }}>{i + 1}</div>
            </div>
            <div style={{ marginTop: 10, textAlign: 'center', fontFamily: SANS, fontWeight: 700, fontSize: 40, lineHeight: 1.2, whiteSpace: 'nowrap', color: picked && me ? th.subHl : th.title, textShadow: outlineOf(3) }}>{p.name}</div>
          </div>
        );
      })}
      {it.credit ? <div style={{ position: 'absolute', left: M + 3, right: M, top: 1745, fontFamily: SANS, fontWeight: 400, fontSize: 23, lineHeight: 1.3, color: th.credit, letterSpacing: '0.04em' }}>{it.credit}</div> : null}
    </AbsoluteFill>
  );
};

// the fixed header (owner 19/11): a red label between two thin lines, the title large in the brush font with a red
// glow, over a dark band so it reads on any picture; on screen from the first frame to the last
const Head: React.FC<{ hd: NonNullable<PlanA['head']>; font: string; th: Theme }> = ({ hd, font, th }) => {
  const n = Math.max(1, [...hd.title].reduce((a, c) => a + (c.charCodeAt(0) < 0x2000 ? 0.55 : 1), 0));
  const size = Math.min(128, Math.floor(980 / n / 1.06));
  const line = { flex: 1, height: 3, background: `linear-gradient(90deg, rgba(0,0,0,0), ${th.bar})` };
  return (
    <>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 420, background: 'linear-gradient(180deg, rgba(0,0,0,.82) 0%, rgba(0,0,0,.55) 55%, rgba(0,0,0,0) 100%)' }} />
      {hd.label ? (
        <div style={{ position: 'absolute', left: 120, right: 120, top: 78, display: 'flex', alignItems: 'center', gap: 26 }}>
          <div style={line} />
          <div style={{ fontFamily: font, fontSize: 50, lineHeight: 1, color: th.subHl, letterSpacing: '0.22em', marginRight: '-0.22em', whiteSpace: 'nowrap', textShadow: '0 0 18px rgba(255,0,0,.35), 0 3px 8px #000' }}>{hd.label}</div>
          <div style={{ ...line, transform: 'scaleX(-1)' }} />
        </div>
      ) : null}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center', fontFamily: font, fontSize: size, lineHeight: 1.15, color: th.title, letterSpacing: '0.04em', whiteSpace: 'nowrap',
        textShadow: '0 0 34px rgba(190,0,0,.55), 0 0 4px rgba(0,0,0,.9), 0 6px 18px rgba(0,0,0,.9)' }}>
        <Highlight text={hd.title} hl={hd.hl || []} color={th.subHl} />
      </div>
    </>
  );
};

const Highlight: React.FC<{ text: string; hl: string[]; color: string }> = ({ text, hl, color }) => {
  if (!hl.length) return <>{text}</>;
  const re = new RegExp(`(${hl.map((h) => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g');
  return <>{text.split(re).map((part, i) => (hl.includes(part) ? <span key={i} style={{ color }}>{part}</span> : <span key={i}>{part}</span>))}</>;
};

export const ArcV: React.FC<PlanA> = (plan) => {
  useFonts(plan.fonts, plan.shots.map((s) => s.label + s.title + s.caption + s.credit).join('') + plan.subs.map((s) => s.text).join('')
    + (plan.head ? plan.head.label + plan.head.title : '') + (plan.hook?.text || '') + (plan.cards || []).map((c) => c.text).join(''), plan.display);
  const disp = plan.display ? `"${plan.display}", ${SERIF}` : undefined;
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const th = THEMES[plan.theme || 'paper'] || THEMES.paper;
  if (!plan.shots.length) return <AbsoluteFill style={{ backgroundColor: th.bg }} />;
  const idx = Math.max(0, plan.shots.findIndex((s) => t >= s.s && t < s.e));
  const sh = plan.shots.find((s) => t >= s.s && t < s.e) || plan.shots[plan.shots.length - 1];
  const sub = plan.subs.find((s) => t >= s.s && t < s.e);
  const speaking = (tt: number) => plan.subs.some((s) => tt >= s.s - 0.2 && tt < s.e + 0.2);
  // header comes in softly when the title changes (a new idea); same title → it stays
  const prev = idx > 0 ? plan.shots[idx - 1] : null;
  // the hook (owner 18/11): big words over the first picture from frame 0; the first header comes in after it
  const hk = plan.hook && t < plan.hook.e + 0.35 ? plan.hook : null;
  const hookOn = hk ? clamp01((hk.e + 0.35 - t) / 0.35) : 0;
  const card = (plan.cards || []).find((c) => t >= c.s && t < c.e + 0.35);
  const cardOn = card ? clamp01((card.e + 0.35 - t) / 0.35) : 0;
  const cardAtShot = (plan.cards || []).find((c) => Math.abs(c.s - sh.s) < 0.4);
  const headFrom = idx === 0 && plan.hook ? plan.hook.e : cardAtShot ? cardAtShot.e : sh.s;
  const head = prev && prev.title === sh.title && prev.label === sh.label ? 1 : easeOut((t - headFrom) / 0.45);
  const lift = (1 - head) * 18;
  // dissolve: the last shot's pictures (caption, credit) stay under the new ones while these fade in
  const fade = plan.fade || 0;
  const same = (a: Shot, b: Shot) => a.pics.length === b.pics.length && a.pics.every((p, i) => p.src === b.pics[i].src && p.box.join() === b.pics[i].box.join() && p.view.join() === b.pics[i].view.join());
  const mix = prev && fade > 0 && t < sh.s + fade && !same(prev, sh) ? ease((t - sh.s) / fade) : 1;
  const out = mix < 1 && prev ? prev : null;
  // a new picture comes in 3 % larger and settles (0.5 s); a subtitle cue rises in (0.2 s)
  // intro: the board of the series over the first lines; it fades out in 0.3 s when the story starts
  const intro = plan.intro && t < plan.intro.e + 0.3 ? plan.intro : null;
  const introOn = intro ? clamp01((intro.e + 0.3 - t) / 0.3) : 0;
  // a card (and the intro's pick) hits: the frame shakes for a third of a second (horror)
  const hitAt = card ? card.s : plan.intro && t >= plan.intro.mid ? plan.intro.mid : -9;
  const sk = th.shake && t - hitAt < 0.33 ? 1 - (t - hitAt) / 0.33 : 0;
  const shake = sk > 0 ? `translate(${(rnd(frame) - 0.5) * 22 * sk}px, ${(rnd(frame + 7) - 0.5) * 22 * sk}px) scale(${1 + 0.03 * sk})` : undefined;
  const settle = prev && same(prev, sh) ? 1 : 1 + 0.03 * (1 - easeOut((t - sh.s) / 0.5));
  const cue = sub ? easeOut((t - sub.s) / 0.2) : 1;
  return (
    <AbsoluteFill style={{ background: th.bgCss || th.bg, transform: shake }}>
      {th.backdrop && out ? <Backdrop p={out.pics[0]} t={t} sh={out} filter={th.backdropFilter} /> : null}
      {th.backdrop ? <AbsoluteFill style={{ opacity: mix }}><Backdrop p={sh.pics[0]} t={t} sh={sh} filter={th.backdropFilter} /></AbsoluteFill> : null}
      {th.wash && out ? <Wash p={out.pics[0]} t={t} sh={out} o={th.wash * (1 - mix)} /> : null}
      {th.wash ? <Wash p={sh.pics[0]} t={t} sh={sh} o={th.wash * mix} /> : null}
      {/* header: bar, label (place / kind of document), title — or the fixed header, and the label small over the picture */}
      {plan.head ? (sh.label ? (
        <div style={{ position: 'absolute', left: sh.pics[0].box[0] + 4, top: sh.pics[0].box[1] - 50 + lift * 0.4, opacity: head * mix, fontFamily: SANS, fontWeight: 500, fontSize: 30, lineHeight: 1.2, color: th.label, letterSpacing: '0.04em', whiteSpace: 'nowrap', textShadow: th.titleShadow }}>{sh.label}</div>
      ) : null) : (<>
      <div style={{ position: 'absolute', left: M + 3, top: sh.bar, width: 92 * (0.4 + 0.6 * head), height: 6, opacity: head, background: th.bar }} />
      {sh.label ? (
        <div style={{ position: 'absolute', left: M + 3, top: sh.bar + 38 + lift * 0.6, opacity: head, fontFamily: SANS, fontWeight: 500, fontSize: 40, lineHeight: 1.25, color: th.label, letterSpacing: '0.02em', whiteSpace: 'nowrap', textShadow: th.titleShadow }}>{sh.label}</div>
      ) : null}
      <div style={{ position: 'absolute', left: M, top: sh.bar + 135 - 0.2 * sh.titleSize + lift, opacity: head, fontFamily: SERIF, fontWeight: 700, fontSize: sh.titleSize, lineHeight: 1.25, color: th.title, letterSpacing: '0.02em', whiteSpace: 'nowrap', textShadow: th.titleShadow }}>{sh.title}</div>
      </>)}
      {out ? <AbsoluteFill style={{ opacity: 1 - mix }}>
        {out.pics.map((p, i) => <PicView key={i} p={p} t={t} sh={out} th={th} marks={out.marks.filter((m) => m.on === i)} />)}
      </AbsoluteFill> : null}
      <AbsoluteFill style={{ opacity: mix, transform: `scale(${settle})`, transformOrigin: `540px ${sh.pics[0].box[1] + sh.pics[0].box[3] / 2}px` }}>
        {sh.pics.map((p, i) => <PicView key={i} p={p} t={t} sh={sh} th={th} marks={sh.marks.filter((m) => m.on === i)} />)}
      </AbsoluteFill>
      {out && out.caption && out.captionY !== null ? (
        <div style={{ position: 'absolute', left: M + 3, top: out.captionY + (th.mat ? th.mat : 0), opacity: 1 - mix, fontFamily: SANS, fontWeight: 500, fontSize: 38, lineHeight: 1.3, color: th.label, textShadow: th.titleShadow }}>{out.caption}</div>
      ) : null}
      {sh.caption && sh.captionY !== null ? (
        <div style={{ position: 'absolute', left: M + 3, top: sh.captionY + (th.mat ? th.mat : 0), opacity: mix, fontFamily: SANS, fontWeight: 500, fontSize: 38, lineHeight: 1.3, color: th.label, textShadow: th.titleShadow }}>{sh.caption}</div>
      ) : null}
      {out && out.credit && out.credit !== sh.credit ? (
        <div style={{ position: 'absolute', left: M + 3, right: M, top: 1745, opacity: 1 - mix, fontFamily: SANS, fontWeight: 400, fontSize: 25, lineHeight: 1.3, color: th.credit, letterSpacing: '0.05em' }}>{out.credit}</div>
      ) : null}
      {sh.credit ? (
        <div style={{ position: 'absolute', left: M + 3, right: M, top: 1745, opacity: out && out.credit !== sh.credit ? mix : 1, fontFamily: SANS, fontWeight: 400, fontSize: 25, lineHeight: 1.3, color: th.credit, letterSpacing: '0.05em' }}>{sh.credit}</div>
      ) : null}
      {intro ? <Intro it={intro} t={t} th={th} on={introOn} /> : null}
      {plan.head ? <Head hd={plan.head} font={disp || SERIF} th={th} /> : null}
      {hk ? <Hook hk={hk} t={t} on={hookOn} box={plan.shots[0].pics[0].box} color={th.subHl} font={disp} /> : null}
      {card && !hk ? <Hook hk={card} t={t} on={cardOn} box={sh.pics[0].box} color={th.subHl} font={disp} /> : null}
      {sub ? (
        <div style={{ position: 'absolute', left: 50, right: 50, top: (intro ? 1500 : sh.subY) + (1 - cue) * 16, opacity: 0.25 + 0.75 * cue, textAlign: 'center' }}>
          {sub.text.split('\n').map((l, i) => (
            <div key={i} style={{ fontFamily: SANS, fontWeight: plan.subSize ? 900 : th.subWeight, fontSize: plan.subSize || 52, lineHeight: plan.subSize ? 1.38 : 1.46, color: th.sub, letterSpacing: th.outline ? '0.02em' : '0.04em', textShadow: th.outline ? outlineOf(plan.subSize ? th.outline + 1 : th.outline) : th.subShadow }}>
              <Highlight text={l} hl={sub.hl || []} color={th.subHl} />
            </div>
          ))}
        </div>
      ) : null}
      {plan.grain ? (   /* film grain, darker edges and a faint flicker over everything (horror) */
        <AbsoluteFill style={{ overflow: 'hidden', pointerEvents: 'none' }}>
          <Img src={staticFile(plan.grain)} style={{ position: 'absolute', left: -Math.floor(rnd(frame) * 200), top: -Math.floor(rnd(frame + 0.5) * 240), width: 1280, height: 2160, maxWidth: 'none',
            opacity: 0.13, mixBlendMode: 'overlay', transform: `scale(${frame % 2 ? 1 : -1}, ${frame % 4 < 2 ? 1 : -1})`, transformOrigin: '640px 1080px' }} />
          <AbsoluteFill style={{ background: 'radial-gradient(ellipse 85% 70% at 50% 46%, rgba(0,0,0,0) 48%, rgba(0,0,0,.72) 100%)' }} />
          <AbsoluteFill style={{ background: '#000', opacity: 0.07 * rnd(frame * 1.7) * (rnd(Math.floor(frame / 9)) > 0.72 ? 1.6 : 0.5) }} />
        </AbsoluteFill>
      ) : null}
      {plan.sfx ? <Audio src={staticFile(plan.sfx)} volume={0.55} /> : null}
      {plan.voice.map((v, i) => <Sequence key={i} from={Math.round(v.s * fps)}><Audio src={staticFile(v.src)} /></Sequence>)}
      {plan.music ? (
        <Audio src={staticFile(plan.music)} volume={(f) => {
          const tt = f / fps;
          return plan.musicVolume * Math.max(0, Math.min(1, tt / 0.6, (durationInFrames / fps - tt) / 1.2)) * (speaking(tt) ? 0.7 : 1);
        }} />
      ) : null}
    </AbsoluteFill>
  );
};
