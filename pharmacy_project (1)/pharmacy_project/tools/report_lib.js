// Small helper library on top of docx-js for the report builder
const fs = require("fs");
const D = require("docx");
const { Paragraph, TextRun, Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle, AlignmentType,
        HeadingLevel, ImageRun, PageBreak } = D;

const FONT = "Arial", CODE = "Courier New";
const W = 9638;                                   // content width (A4, 0.79in margins)

function rich(text, base = {}) {
  const runs = []; const parts = String(text).split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  for (const p of parts) {
    if (!p) continue;
    if (p.startsWith("**")) runs.push(new TextRun({ text: p.slice(2, -2), bold: true, font: FONT, ...base }));
    else if (p.startsWith("`")) runs.push(new TextRun({ text: p.slice(1, -1), font: CODE, size: (base.size || 21) - 2, ...base, color: "7B2C2C" }));
    else runs.push(new TextRun({ text: p, font: FONT, ...base }));
  }
  return runs;
}
const P = (t, o = {}) => new Paragraph({ children: rich(t, o.run || {}), spacing: { after: o.after ?? 120, line: 276 }, alignment: o.align, keepNext: o.keepNext, indent: o.indent });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, pageBreakBefore: true, children: [new TextRun({ text: t, font: FONT })] });
const H1n = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: t, font: FONT })] });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: t, font: FONT })] });
const H3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: t, font: FONT })] });
const bullets = (items) => items.map((t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: rich(t), spacing: { after: 60, line: 264 } }));
const numbered = (items, ref = "num") => items.map((t) => new Paragraph({ numbering: { reference: ref, level: 0 }, children: rich(t), spacing: { after: 60, line: 264 } }));
const caption = (t) => new Paragraph({ children: [new TextRun({ text: t, italics: true, size: 18, color: "555555", font: FONT })], spacing: { before: 60, after: 160 }, alignment: AlignmentType.CENTER });
const gap = (n = 120) => new Paragraph({ children: [], spacing: { after: n } });
const pb = () => new Paragraph({ children: [new PageBreak()] });

function code(text, size = 15) {
  const lines = String(text).replace(/\t/g, "    ").split("\n");
  return lines.map((ln, i) => new Paragraph({
    children: [new TextRun({ text: ln === "" ? " " : ln, font: CODE, size })],
    shading: { type: ShadingType.CLEAR, fill: "F3F3F3", color: "auto" },
    spacing: { after: i === lines.length - 1 ? 140 : 0, line: 220 },
    indent: { left: 80, right: 80 },
    keepLines: true,
  }));
}

const thin = { style: BorderStyle.SINGLE, size: 4, color: "BBBBBB" };
const borders = { top: thin, bottom: thin, left: thin, right: thin };
function cell(text, w, o = {}) {
  return new TableCell({
    width: { size: w, type: WidthType.DXA }, borders,
    shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: String(text ?? "").split("\n").map((ln) => new Paragraph({
      children: o.mono ? [new TextRun({ text: ln, font: CODE, size: o.size || 16, bold: o.bold })] : rich(ln, { size: o.size || 18, bold: o.bold, color: o.color }),
      alignment: o.align, spacing: { after: 0, line: 240 } })),
  });
}
// relative widths -> DXA that sum to total
function fit(rel, total = W) {
  const s = rel.reduce((a, b) => a + b, 0); const w = rel.map((r) => Math.floor((r / s) * total));
  w[w.length - 1] += total - w.reduce((a, b) => a + b, 0); return w;
}
function table(headers, rows, rel, o = {}) {
  const w = fit(rel || headers.map(() => 1), o.total || W);
  const head = new TableRow({ tableHeader: true, children: headers.map((h, i) => cell(h, w[i], { fill: o.headFill || "1F3864", bold: true, color: "FFFFFF", size: o.size || 18 })) });
  const body = rows.map((r, ri) => new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, w[i], { size: o.size || 18, fill: ri % 2 ? "F7F9FC" : undefined, mono: o.mono && o.mono.includes(i), align: o.right && o.right.includes(i) ? AlignmentType.RIGHT : undefined })) }));
  return new Table({ width: { size: o.total || W, type: WidthType.DXA }, columnWidths: w, rows: [head, ...body] });
}
const fmt = (v) => v === null || v === undefined ? "NULL" : (typeof v === "number" ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : String(v));
function resultTable(res, maxRows = 8, o = {}) {
  const cols = res.columns, rows = res.rows.slice(0, maxRows).map((r) => r.map(fmt));
  const rel = cols.map((c, i) => Math.min(30, Math.max(c.length, ...rows.map((r) => r[i].length), 5)));
  const out = [table(cols, rows.length ? rows : [cols.map(() => "")], rel, { size: o.size || 16, headFill: "2E5E9E", right: cols.map((c, i) => i).filter((i) => res.rows.length && typeof res.rows[0][i] === "number") })];
  const extra = res.rows.length - rows.length;
  out.push(new Paragraph({ children: [new TextRun({ text: extra > 0 ? `${res.rows.length} rows in total - first ${rows.length} shown` : `${res.rows.length} row${res.rows.length === 1 ? "" : "s"}`, italics: true, size: 16, color: "666666", font: FONT })], spacing: { before: 40, after: 160 } }));
  return out;
}
function img(path, w, h) {
  return new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ type: "png", data: fs.readFileSync(path), transformation: { width: w, height: h }, altText: { title: path, description: path, name: path } })] });
}
module.exports = { D, FONT, CODE, W, rich, P, H1, H1n, H2, H3, bullets, numbered, caption, gap, pb, code, table, cell, fit, fmt, resultTable, img };
