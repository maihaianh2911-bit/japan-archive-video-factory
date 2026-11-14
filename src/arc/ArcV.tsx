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
  zoom?: { to: View; s: number; e: number }; drift?: number };
export type Mark = { s: number; box: View; shape: 'ellipse' | 'rect'; on: number };
export type Shot = { s: number; e: number; scene: number; shot: number; label: string; title: string; titleSize: number;
  caption: string; credit: string; bar: number; captionY: number | null; subY: number; pics: PicBox[]; marks: Mark[]; newScene?: boolean };
export type Sub = { s: number; e: number; text: string; hl?: string[] };
type FontChunk = { family: string; file: string; range: string };
export type PlanA = { duration: number; shots: Shot[]; subs: Sub[]; voice: { s: number; src: string }[]; music: string | null;
  musicVolume: number; fonts: FontChunk[]; theme?: string; total?: number; fade?: number };

type Theme = { bg: string; bgCss?: string; bar: string; label: string; title: string; sub: string; subHl: string; subShadow: string; credit: string;
  ring: string; frame: string; mat: number; shadow: string; backdrop: boolean; subWeight: number; titleShadow: string };
export const THEMES: Record<string, Theme> = {
  warm: { bg: '#1b1410', bar: '#e9be86', label: '#f0c995', title: '#fff6e6', sub: '#fffaf0', subHl: '#f2c67f',
    subShadow: '0 2px 14px rgba(0,0,0,.75), 0 0 3px rgba(0,0,0,.6)', credit: 'rgba(235,225,212,.8)', ring: '#f2c070',
    frame: '2px solid rgba(240,201,149,.85)', mat: 0, shadow: '0 28px 70px rgba(0,0,0,.65), 0 6px 18px rgba(0,0,0,.45)',
    backdrop: true, subWeight: 500, titleShadow: '0 4px 24px rgba(0,0,0,.55)' },
  paper: { bg: '#efe5cf', bgCss: 'radial-gradient(ellipse 90% 75% at 50% 42%, #f7f0de 0%, #efe5cf 55%, #dccdaa 100%)', bar: '#a8432a', label: '#9c3f26', title: '#2b1d12', sub: '#24180f', subHl: '#a8432a',
    subShadow: 'none', credit: 'rgba(80,62,45,.85)', ring: '#c0392b', frame: '1px solid rgba(60,40,20,.25)', mat: 12,
    shadow: '0 18px 40px rgba(70,45,20,.35), 0 3px 8px rgba(70,45,20,.25)', backdrop: false, subWeight: 500, titleShadow: 'none' },
  classic: { bg: '#211a18', bar: '#e9be86', label: '#efc391', title: '#fbf6ea', sub: '#fffdf5', subHl: '#f2c67f',
    subShadow: '0 2px 10px rgba(0,0,0,.45)', credit: 'rgba(214,205,200,.82)', ring: '#e6b46e', frame: '1.5px solid rgba(214,190,156,.62)',
    mat: 0, shadow: 'none', backdrop: false, subWeight: 400, titleShadow: 'none' },
};
const SERIF = '"Noto Serif JP", serif', SANS = '"Noto Sans JP", sans-serif';
const M = 69;
const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ease = (x: number) => { const p = clamp01(x); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };
const easeOut = (x: number) => 1 - Math.pow(1 - clamp01(x), 3);

let fontsLoading: Promise<void> | null = null;
const useFonts = (fonts: FontChunk[], text: string) => {
  const [h] = useState(() => delayRender('JP fonts'));
  useEffect(() => {
    (fontsLoading ??= (async () => {
      for (const f of fonts)
        document.fonts.add(new FontFace(f.family, `url(${staticFile(f.file)}) format('woff2')`, { weight: '100 900', unicodeRange: f.range }));
      await Promise.all([700, 500, 400].flatMap((wt) => [document.fonts.load(`${wt} 60px ${SERIF}`, text), document.fonts.load(`${wt} 40px ${SANS}`, text)]));
    })()).then(() => continueRender(h)).catch((e) => cancelRender(e));
  }, [h, fonts, text]);
};

// region of the picture shown at time t: a zoom when asked for, else a slow drift (push-in by `drift` over the shot)
export const viewAt = (p: PicBox, t: number, s: number, e: number): View => {
  if (p.zoom) {
    const k = ease((t - p.zoom.s) / Math.max(0.1, p.zoom.e - p.zoom.s));
    return p.view.map((v, i) => v + (p.zoom!.to[i] - v) * k) as View;
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
        <Img src={staticFile(p.src)} style={{ position: 'absolute', left: -v0 * p.w * sx, top: -v1 * p.h * sy, width: p.w * sx, height: p.h * sy, maxWidth: 'none' }} />
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
const Backdrop: React.FC<{ p: PicBox; t: number; sh: Shot }> = ({ p, t, sh }) => {
  const k = clamp01((t - sh.s) / Math.max(0.5, sh.e - sh.s));
  const c = Math.max(1080 / p.w, 1920 / p.h) * 1.25, w = p.w * c, h = p.h * c;
  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      <Img src={staticFile(p.src)} style={{ position: 'absolute', left: (1080 - w) / 2, top: (1920 - h) / 2, width: w, height: h, maxWidth: 'none',
        filter: 'blur(36px) saturate(1.45) brightness(.62)', transform: `scale(${1 + 0.04 * k})` }} />
      <AbsoluteFill style={{ background: 'linear-gradient(180deg, rgba(20,14,10,.55) 0%, rgba(20,14,10,.18) 30%, rgba(20,14,10,.2) 62%, rgba(14,10,8,.78) 100%)' }} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 55%, rgba(0,0,0,.5) 100%)' }} />
    </AbsoluteFill>
  );
};

const Highlight: React.FC<{ text: string; hl: string[]; color: string }> = ({ text, hl, color }) => {
  if (!hl.length) return <>{text}</>;
  const re = new RegExp(`(${hl.map((h) => h.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'g');
  return <>{text.split(re).map((part, i) => (hl.includes(part) ? <span key={i} style={{ color }}>{part}</span> : <span key={i}>{part}</span>))}</>;
};

export const ArcV: React.FC<PlanA> = (plan) => {
  useFonts(plan.fonts, plan.shots.map((s) => s.label + s.title + s.caption + s.credit).join('') + plan.subs.map((s) => s.text).join(''));
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
  const head = prev && prev.title === sh.title && prev.label === sh.label ? 1 : easeOut((t - sh.s) / 0.45);
  const lift = (1 - head) * 18;
  // dissolve: the last shot's pictures (caption, credit) stay under the new ones while these fade in
  const fade = plan.fade || 0;
  const same = (a: Shot, b: Shot) => a.pics.length === b.pics.length && a.pics.every((p, i) => p.src === b.pics[i].src && p.box.join() === b.pics[i].box.join());
  const mix = prev && fade > 0 && t < sh.s + fade && !same(prev, sh) ? ease((t - sh.s) / fade) : 1;
  const out = mix < 1 && prev ? prev : null;
  return (
    <AbsoluteFill style={{ background: th.bgCss || th.bg }}>
      {th.backdrop && out ? <Backdrop p={out.pics[0]} t={t} sh={out} /> : null}
      {th.backdrop ? <AbsoluteFill style={{ opacity: mix }}><Backdrop p={sh.pics[0]} t={t} sh={sh} /></AbsoluteFill> : null}
      {/* header: bar, label (place / kind of document), title */}
      <div style={{ position: 'absolute', left: M + 3, top: sh.bar, width: 92 * (0.4 + 0.6 * head), height: 6, background: th.bar }} />
      {sh.label ? (
        <div style={{ position: 'absolute', left: M + 3, top: sh.bar + 38 + lift * 0.6, opacity: head, fontFamily: SANS, fontWeight: 500, fontSize: 40, lineHeight: 1.25, color: th.label, letterSpacing: '0.02em', whiteSpace: 'nowrap', textShadow: th.titleShadow }}>{sh.label}</div>
      ) : null}
      <div style={{ position: 'absolute', left: M, top: sh.bar + 135 - 0.2 * sh.titleSize + lift, opacity: head, fontFamily: SERIF, fontWeight: 700, fontSize: sh.titleSize, lineHeight: 1.25, color: th.title, letterSpacing: '0.02em', whiteSpace: 'nowrap', textShadow: th.titleShadow }}>{sh.title}</div>
      {out ? <AbsoluteFill style={{ opacity: 1 - mix }}>
        {out.pics.map((p, i) => <PicView key={i} p={p} t={t} sh={out} th={th} marks={out.marks.filter((m) => m.on === i)} />)}
      </AbsoluteFill> : null}
      <AbsoluteFill style={{ opacity: mix }}>
        {sh.pics.map((p, i) => <PicView key={i} p={p} t={t} sh={sh} th={th} marks={sh.marks.filter((m) => m.on === i)} />)}
      </AbsoluteFill>
      {out && out.caption && out.captionY !== null ? (
        <div style={{ position: 'absolute', left: M + 3, top: out.captionY + (th.mat ? th.mat : 0), opacity: 1 - mix, fontFamily: SANS, fontWeight: 500, fontSize: 38, lineHeight: 1.3, color: th.label, textShadow: th.titleShadow }}>{out.caption}</div>
      ) : null}
      {sh.caption && sh.captionY !== null ? (
        <div style={{ position: 'absolute', left: M + 3, top: sh.captionY + (th.mat ? th.mat : 0), opacity: mix, fontFamily: SANS, fontWeight: 500, fontSize: 38, lineHeight: 1.3, color: th.label, textShadow: th.titleShadow }}>{sh.caption}</div>
      ) : null}
      {sub ? (
        <div style={{ position: 'absolute', left: 50, right: 50, top: sh.subY, textAlign: 'center' }}>
          {sub.text.split('\n').map((l, i) => (
            <div key={i} style={{ fontFamily: SANS, fontWeight: th.subWeight, fontSize: 52, lineHeight: 1.46, color: th.sub, letterSpacing: '0.04em', textShadow: th.subShadow }}>
              <Highlight text={l} hl={sub.hl || []} color={th.subHl} />
            </div>
          ))}
        </div>
      ) : null}
      {out && out.credit && out.credit !== sh.credit ? (
        <div style={{ position: 'absolute', left: M + 3, right: M, top: 1745, opacity: 1 - mix, fontFamily: SANS, fontWeight: 400, fontSize: 25, lineHeight: 1.3, color: th.credit, letterSpacing: '0.05em' }}>{out.credit}</div>
      ) : null}
      {sh.credit ? (
        <div style={{ position: 'absolute', left: M + 3, right: M, top: 1745, opacity: out && out.credit !== sh.credit ? mix : 1, fontFamily: SANS, fontWeight: 400, fontSize: 25, lineHeight: 1.3, color: th.credit, letterSpacing: '0.05em' }}>{sh.credit}</div>
      ) : null}
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
