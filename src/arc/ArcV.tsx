import React, { useEffect, useState } from 'react';
import { AbsoluteFill, Audio, Img, Sequence, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

// Vertical (1080×1920) history / legend short from real archive pictures, laid out as the approved sample
// (00-video-mau/MAU-EDIT-20S.mp4): dark brown background, gold bar + small gold label, cream title, the picture
// in the middle with a thin border, gold rings that appear when the voice names a detail, the subtitle under the
// picture, the credit at the foot. Hard cuts. All positions come from scripts/arc/layout.py via build.py.
type View = [number, number, number, number];
export type PicBox = { src: string; w: number; h: number; box: [number, number, number, number]; view: View;
  zoom?: { to: View; s: number; e: number } };
export type Mark = { s: number; box: View; shape: 'ellipse' | 'rect'; on: number };
export type Shot = { s: number; e: number; scene: number; shot: number; label: string; title: string; titleSize: number;
  caption: string; credit: string; bar: number; captionY: number | null; subY: number; pics: PicBox[]; marks: Mark[] };
export type Sub = { s: number; e: number; text: string };
type FontChunk = { family: string; file: string; range: string };
export type PlanA = { duration: number; shots: Shot[]; subs: Sub[]; voice: { s: number; src: string }[]; music: string | null;
  musicVolume: number; fonts: FontChunk[] };

const BG = '#211a18', GOLD = '#e9be86', LABEL = '#efc391', CREAM = '#fbf6ea', SUB = '#fffdf5', CREDIT = 'rgba(214,205,200,.82)';
const RING = '#e6b46e';
const SERIF = '"Noto Serif JP", serif', SANS = '"Noto Sans JP", sans-serif';
const M = 69;
const clamp01 = (x: number) => (x < 0 ? 0 : x > 1 ? 1 : x);
const ease = (x: number) => { const p = clamp01(x); return p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2; };

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

const viewAt = (p: PicBox, t: number): View => {
  if (!p.zoom) return p.view;
  const k = ease((t - p.zoom.s) / Math.max(0.1, p.zoom.e - p.zoom.s));
  return p.view.map((v, i) => v + (p.zoom!.to[i] - v) * k) as View;
};

// one picture in its bordered box, showing the region `view` (fractions of the picture), with its marks
const PicView: React.FC<{ p: PicBox; t: number; marks: Mark[] }> = ({ p, t, marks }) => {
  const [x, y, bw, bh] = p.box;
  const [v0, v1, v2, v3] = viewAt(p, t);
  const sx = bw / ((v2 - v0) * p.w), sy = bh / ((v3 - v1) * p.h);
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: bw, height: bh }}>
      <div style={{ position: 'absolute', inset: 0, overflow: 'hidden' }}>
        <Img src={staticFile(p.src)} style={{ position: 'absolute', left: -v0 * p.w * sx, top: -v1 * p.h * sy, width: p.w * sx, height: p.h * sy, maxWidth: 'none' }} />
        <svg width={bw} height={bh} style={{ position: 'absolute', left: 0, top: 0 }}>
          {marks.filter((m) => t >= m.s).map((m, i) => {
            const X = (f: number) => ((f - v0) / (v2 - v0)) * bw, Y = (f: number) => ((f - v1) / (v3 - v1)) * bh;
            const [a, b, c, d] = m.box;
            const st = { fill: 'none', stroke: RING, strokeWidth: 4.5, opacity: clamp01((t - m.s) / 0.12), filter: 'drop-shadow(0 0 3px rgba(0,0,0,.55))' };
            return m.shape === 'rect'
              ? <rect key={i} x={X(a)} y={Y(b)} width={X(c) - X(a)} height={Y(d) - Y(b)} rx={6} style={st} />
              : <ellipse key={i} cx={(X(a) + X(c)) / 2} cy={(Y(b) + Y(d)) / 2} rx={(X(c) - X(a)) / 2} ry={(Y(d) - Y(b)) / 2} style={st} />;
          })}
        </svg>
      </div>
      <div style={{ position: 'absolute', inset: -1, border: '1.5px solid rgba(214,190,156,.62)', pointerEvents: 'none' }} />
    </div>
  );
};

export const ArcV: React.FC<PlanA> = (plan) => {
  useFonts(plan.fonts, plan.shots.map((s) => s.label + s.title + s.caption + s.credit).join('') + plan.subs.map((s) => s.text).join(''));
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  if (!plan.shots.length) return <AbsoluteFill style={{ backgroundColor: BG }} />;
  const sh = plan.shots.find((s) => t >= s.s && t < s.e) || plan.shots[plan.shots.length - 1];
  const sub = plan.subs.find((s) => t >= s.s && t < s.e);
  const speaking = (tt: number) => plan.subs.some((s) => tt >= s.s - 0.2 && tt < s.e + 0.2);
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      {/* header: gold bar, label (place / kind of document), title */}
      <div style={{ position: 'absolute', left: M + 3, top: sh.bar, width: 92, height: 6, background: GOLD }} />
      {sh.label ? (
        <div style={{ position: 'absolute', left: M + 3, top: sh.bar + 38, fontFamily: SANS, fontWeight: 400, fontSize: 40, lineHeight: 1.25, color: LABEL, letterSpacing: '0.01em', whiteSpace: 'nowrap' }}>{sh.label}</div>
      ) : null}
      <div style={{ position: 'absolute', left: M, top: sh.bar + 135 - 0.2 * sh.titleSize, fontFamily: SERIF, fontWeight: 700, fontSize: sh.titleSize, lineHeight: 1.25, color: CREAM, letterSpacing: '0.01em', whiteSpace: 'nowrap' }}>{sh.title}</div>
      {sh.pics.map((p, i) => <PicView key={i} p={p} t={t} marks={sh.marks.filter((m) => m.on === i)} />)}
      {sh.caption && sh.captionY !== null ? (
        <div style={{ position: 'absolute', left: M + 3, top: sh.captionY, fontFamily: SANS, fontWeight: 400, fontSize: 38, lineHeight: 1.3, color: LABEL }}>{sh.caption}</div>
      ) : null}
      {sub ? (
        <div style={{ position: 'absolute', left: 50, right: 50, top: sh.subY, textAlign: 'center' }}>
          {sub.text.split('\n').map((l, i) => (
            <div key={i} style={{ fontFamily: SANS, fontWeight: 400, fontSize: 52, lineHeight: 1.46, color: SUB, letterSpacing: '0.04em', textShadow: '0 2px 10px rgba(0,0,0,.45)' }}>{l}</div>
          ))}
        </div>
      ) : null}
      {sh.credit ? (
        <div style={{ position: 'absolute', left: M + 3, right: M, top: 1745, fontFamily: SANS, fontWeight: 400, fontSize: 25, lineHeight: 1.3, color: CREDIT, letterSpacing: '0.05em' }}>{sh.credit}</div>
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
