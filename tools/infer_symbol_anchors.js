#!/usr/bin/env node
/* Map function-like debug strings to the IDA functions that reference them. */

const fs = require("fs");
const path = require("path");

function csv(value) {
  const text = String(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

const input = process.argv[2];
const output = process.argv[3];
if (!input || !output) {
  console.error("usage: infer_symbol_anchors.js INPUT_DIR OUTPUT.csv");
  process.exit(2);
}

const functions = JSON.parse(
  fs.readFileSync(path.join(input, "functions.json"), "utf8")
).sort((a, b) => a.address - b.address);
const strings = JSON.parse(
  fs.readFileSync(path.join(input, "strings.json"), "utf8")
);

function functionAt(address) {
  let low = 0;
  let high = functions.length - 1;
  while (low <= high) {
    const middle = (low + high) >> 1;
    const fn = functions[middle];
    if (address < fn.address) high = middle - 1;
    else if (address >= fn.end) low = middle + 1;
    else return fn;
  }
  return null;
}

const acceptable =
  /^(?:__|Sec|DRV_|SYSAPI_|USBCop_|Jay_|FRC_|HDMI_|DP_|DPTX_|DPRX_)[A-Za-z0-9_]{2,120}$/;
const rows = [];
const seen = new Set();
for (const item of strings) {
  if (!acceptable.test(item.text)) continue;
  const functionsForString = new Map();
  for (const xref of item.xrefs) {
    const fn = functionAt(xref);
    if (fn) functionsForString.set(fn.address, fn);
  }
  for (const fn of functionsForString.values()) {
    const key = `${fn.address}:${item.address}:${item.text}`;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({
      functionAddress: fn.address,
      idaName: fn.name,
      inferredName: item.text,
      evidenceAddress: item.address,
      stringFunctionCount: functionsForString.size,
    });
  }
}
rows.sort(
  (a, b) =>
    a.functionAddress - b.functionAddress ||
    a.inferredName.localeCompare(b.inferredName)
);

const lines = [
  "function_address,ida_name,inferred_name,evidence_address,evidence_ambiguity",
];
for (const row of rows) {
  lines.push(
    [
      `0x${row.functionAddress.toString(16).toUpperCase().padStart(8, "0")}`,
      row.idaName,
      row.inferredName,
      `0x${row.evidenceAddress.toString(16).toUpperCase().padStart(8, "0")}`,
      row.stringFunctionCount === 1 ? "single-function-xref" : "shared-string",
    ]
      .map(csv)
      .join(",")
  );
}
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, lines.join("\n") + "\n");
console.log(JSON.stringify({ anchors: rows.length }, null, 2));
