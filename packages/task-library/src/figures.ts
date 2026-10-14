import type { Figure, Fill } from "./types";

/**
 * Platform-free figure geometry. Returns SVG primitives in a 100x100 box that the web app renders with
 * <svg> and the Android app with react-native-svg. Fills use patterns (stripes, dots) as well as colour,
 * so no puzzle depends on colour alone (accessibility requirement).
 */

export interface Prim {
  tag: "path" | "circle" | "rect";
  attrs: Record<string, string | number>;
}

const BASE: Record<string, string> = {
  arrow: "M50 8 L82 44 H62 V92 H38 V44 H18 Z",
  triangle: "M50 8 L92 88 H8 Z",
  flag: "M22 8 V92 M22 10 L82 28 L22 48 Z",
  star: "M50 6 L61 38 L95 38 L67 58 L78 92 L50 71 L22 92 L33 58 L5 38 L39 38 Z",
  square: "M14 14 H86 V86 H14 Z",
  diamond: "M50 6 L92 50 L50 94 L8 50 Z",
  cross: "M38 8 H62 V38 H92 V62 H62 V92 H38 V62 H8 V38 H38 Z",
  heart: "M50 88 C10 60 4 34 22 20 C34 10 46 16 50 28 C54 16 66 10 78 20 C96 34 90 60 50 88 Z",
  moon: "M64 8 A42 42 0 1 0 64 92 A34 34 0 1 1 64 8 Z",
};

export const SHAPES = Object.keys(BASE);

export function fillAttrs(fill: Fill, color = "currentColor"): Record<string, string | number> {
  switch (fill) {
    case "solid":
      return { fill: color, stroke: color, "stroke-width": 3 };
    case "empty":
      return { fill: "none", stroke: color, "stroke-width": 5 };
    case "striped":
      return { fill: "url(#sds-stripes)", stroke: color, "stroke-width": 4 };
    case "dotted":
      return { fill: "url(#sds-dots)", stroke: color, "stroke-width": 4 };
  }
}

function polyPath(cells: number[][]): string {
  const maxX = Math.max(...cells.map((c) => c[0])) + 1;
  const maxY = Math.max(...cells.map((c) => c[1])) + 1;
  const size = 84 / Math.max(maxX, maxY);
  const ox = (100 - size * maxX) / 2;
  const oy = (100 - size * maxY) / 2;
  return cells
    .map(([x, y]) => {
      const px = ox + x * size;
      const py = oy + y * size;
      return `M${px} ${py} h${size} v${size} h${-size} Z`;
    })
    .join(" ");
}

/** Primitives for one figure, including `count` copies laid out in a row. */
export function figurePrims(fig: Figure, color = "currentColor"): Prim[] {
  const count = Math.max(1, Math.min(4, fig.count || 1));
  const scale = count === 1 ? 1 : count === 2 ? 0.5 : count === 3 ? 0.36 : 0.26;
  const prims: Prim[] = [];
  for (let k = 0; k < count; k++) {
    const offset = count === 1 ? 0 : (100 / count) * k + (100 / count - 100 * scale) / 2;
    const transform = count === 1
      ? `rotate(${fig.rotation} 50 50)`
      : `translate(${offset} ${50 - 50 * scale}) scale(${scale}) rotate(${fig.rotation} 50 50)`;
    const attrs = { ...fillAttrs(fig.fill, color), transform, "stroke-linejoin": "round" };
    if (fig.shape === "circle") prims.push({ tag: "circle", attrs: { cx: 50, cy: 50, r: 40, ...attrs } });
    else if (fig.shape === "poly" && fig.cells) prims.push({ tag: "path", attrs: { d: polyPath(fig.cells), ...attrs } });
    else prims.push({ tag: "path", attrs: { d: BASE[fig.shape] ?? BASE.square, ...attrs } });
  }
  return prims;
}

/** Colours for the T1 colour mode, always shown with their name so colour is never the only cue. */
export const TOKEN_COLORS: Record<string, string> = {
  red: "#d64545", blue: "#2f6fd6", green: "#2e9e5b", yellow: "#e0b100", purple: "#8a4fd6", orange: "#e07a1f",
};
