#!/usr/bin/env node
/* Classify IDA-discovered functions by string-xref evidence. */

const fs = require("fs");
const path = require("path");

const categories = [
  ["boot_update", /\bboot\b|update|upgrade|firmware|flash|isp|checksum|partition/i],
  ["factory_service", /factory|mga|service|testpat|debug menu|t-?con|fpga|pdic/i],
  ["osd_ui", /osd|menu|popup|draw|render|resource|language|font|icon/i],
  ["input_keys", /keyevt|joystick|button|remote key|hotkey|long.?press|key /i],
  ["persistent_data", /nvram|eeprom|userdata|save|load|factory data|configuration/i],
  ["video_link", /hdmi|displayport|\bdp\b|edid|hdcp|freesync|vrr|adaptive.?sync|source|cable/i],
  ["picture_pq", /picture|brightness|contrast|color|gamma|black equal|dimming|hdr|lut|white balance/i],
  ["scaler_panel", /scaler|panel|timing|tcon|overdrive|pwm|backlight|histogram|capture|window/i],
  ["audio", /audio|sound|speaker|mute|volume|amp|peq/i],
  ["usb_pd", /usb|type.?c|pdic|\bpd\b|power delivery|hub/i],
  ["ddc_ci", /ddc|vcp|mccs|display data channel/i],
  ["power", /power|standby|sleep|wake|energy|eco|zero power/i],
  ["events_tasks", /task|event|handler|message|queue|callback|state/i],
  ["diagnostics", /error|fail|invalid|assert|crash|watchdog|warning|trace|log/i],
];

function escapeCsv(value) {
  const text = String(value);
  if (/[",\n\r]/.test(text)) return `"${text.replaceAll('"', '""')}"`;
  return text;
}

function classify(inputDir, outputPath) {
  const functions = JSON.parse(
    fs.readFileSync(path.join(inputDir, "functions.json"), "utf8")
  );
  const strings = JSON.parse(
    fs.readFileSync(path.join(inputDir, "strings.json"), "utf8")
  );
  functions.sort((a, b) => a.address - b.address);

  function containingFunction(address) {
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

  const evidence = new Map(functions.map((fn) => [fn.address, []]));
  for (const item of strings) {
    for (const xref of item.xrefs) {
      const fn = containingFunction(xref);
      if (fn) evidence.get(fn.address).push(item.text);
    }
  }

  const rows = functions.map((fn) => {
    const stringsForFunction = evidence.get(fn.address);
    const joined = stringsForFunction.join("\n");
    const labels = categories
      .filter(([, expression]) => expression.test(joined))
      .map(([label]) => label);
    return {
      ...fn,
      categories: labels,
      string_evidence_count: stringsForFunction.length,
      graph_categories: [],
    };
  });

  const rowByAddress = new Map(rows.map((row) => [row.address, row]));
  const neighbors = new Map(rows.map((row) => [row.address, new Set()]));
  for (const row of rows) {
    for (const callee of row.callees) {
      if (!rowByAddress.has(callee)) continue;
      neighbors.get(row.address).add(callee);
      neighbors.get(callee).add(row.address);
    }
  }
  for (let pass = 0; pass < 3; pass += 1) {
    const additions = [];
    for (const row of rows) {
      if (row.categories.length || row.graph_categories.length) continue;
      const votes = new Map();
      let labeledNeighbors = 0;
      for (const address of neighbors.get(row.address)) {
        const adjacent = rowByAddress.get(address);
        const labels = adjacent.categories.length
          ? adjacent.categories
          : adjacent.graph_categories;
        if (labels.length === 0) continue;
        labeledNeighbors += 1;
        for (const label of labels) votes.set(label, (votes.get(label) || 0) + 1);
      }
      if (labeledNeighbors < 2) continue;
      const best = [...votes.entries()].sort((a, b) => b[1] - a[1])[0];
      if (best && best[1] >= 2 && best[1] / labeledNeighbors >= 0.6) {
        additions.push([row, best[0]]);
      }
    }
    for (const [row, label] of additions) row.graph_categories.push(label);
  }

  const lines = [
    [
      "address",
      "end",
      "size",
      "name",
      "instructions",
      "callers",
      "callees",
      "string_evidence",
      "direct_categories",
      "graph_inferred_categories",
    ].join(","),
  ];
  for (const row of rows) {
    lines.push(
      [
        `0x${row.address.toString(16).toUpperCase().padStart(8, "0")}`,
        `0x${row.end.toString(16).toUpperCase().padStart(8, "0")}`,
        `0x${row.size.toString(16).toUpperCase()}`,
        row.name,
        row.instructions,
        row.caller_count,
        row.callees.length,
        row.string_evidence_count,
        row.categories.join("|") || "unclassified",
        row.graph_categories.join("|"),
      ]
        .map(escapeCsv)
        .join(",")
    );
  }
  fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  fs.writeFileSync(outputPath, lines.join("\n") + "\n");

  const counts = Object.fromEntries(categories.map(([name]) => [name, 0]));
  counts.unclassified = 0;
  counts.graph_inferred = 0;
  for (const row of rows) {
    if (row.categories.length === 0 && row.graph_categories.length === 0) {
      counts.unclassified += 1;
    }
    if (row.graph_categories.length) counts.graph_inferred += 1;
    for (const category of row.categories) counts[category] += 1;
  }
  process.stdout.write(JSON.stringify({ functions: rows.length, counts }, null, 2) + "\n");
}

if (process.argv.length !== 4) {
  console.error("usage: classify_ida_inventory.js INPUT_DIR OUTPUT.csv");
  process.exit(2);
}
classify(process.argv[2], process.argv[3]);
