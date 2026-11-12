import React from 'react';
import { Composition } from 'remotion';
import { ArcV, PlanA } from './ArcV';

const FPS = 30;
// The whole plan comes in as props (scripts/arc/build.py), its length included.
const EMPTY: PlanA = { duration: 1, shots: [], subs: [], voice: [], music: null, musicVolume: 0.16, fonts: [] };

export const ArcRoot: React.FC = () => (
  <Composition
    id="ArcV"
    component={ArcV as unknown as React.FC<Record<string, unknown>>}
    width={1080}
    height={1920}
    fps={FPS}
    durationInFrames={FPS}
    defaultProps={EMPTY as unknown as Record<string, unknown>}
    calculateMetadata={({ props }) => ({ durationInFrames: Math.max(1, Math.ceil((props as unknown as PlanA).duration * FPS)) })}
  />
);
