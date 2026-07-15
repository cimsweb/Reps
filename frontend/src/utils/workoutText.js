const MONTHS_RU = {
  1: "Января",
  2: "Февраля",
  3: "Марта",
  4: "Апреля",
  5: "Мая",
  6: "Июня",
  7: "Июля",
  8: "Августа",
  9: "Сентября",
  10: "Октября",
  11: "Ноября",
  12: "Декабря",
};

const DAY_HEADER_RE = /^\s*(\d{1,2})\s+[А-Яа-яЁё]+\s*$/;

function isValidDayHeaderLine(line) {
  const match = line.trim().match(DAY_HEADER_RE);
  if (!match) {
    return false;
  }
  const day = Number.parseInt(match[1], 10);
  return day >= 1 && day <= 31;
}

export function formatDayHeader(dateInput) {
  const date = typeof dateInput === "string" ? new Date(`${dateInput}T00:00:00`) : dateInput;
  const month = MONTHS_RU[date.getMonth() + 1] ?? date.toLocaleString("ru-RU", { month: "long" });
  return `${date.getDate()} ${month}`;
}

export function toLines(text) {
  if (!text) {
    return [];
  }
  return text.split("\n").map((line) => {
    const trimmed = line.trim();
    if (!trimmed) {
      return { text: "", bullet: false, plain: false, blank: true };
    }
    if (trimmed.startsWith("- ")) {
      return { text: trimmed.slice(2), bullet: true, plain: false, blank: false };
    }
    return { text: line, bullet: false, plain: true, blank: false };
  });
}

const DEFAULT_CYCLE_NAMES = new Set(["основная часть", "план"]);

function normalizeLabel(value) {
  return (value ?? "").trim().toLowerCase();
}

function isStructuralLabel(line) {
  return DEFAULT_CYCLE_NAMES.has(normalizeLabel(line));
}

function isJunkExercise(exercise, cycleName) {
  const name = exercise.name?.trim() ?? "";
  if (!name) {
    return true;
  }
  if (isStructuralLabel(name) && !exercise.details?.trim()) {
    return true;
  }
  if (normalizeLabel(name) === normalizeLabel(cycleName) && isStructuralLabel(name)) {
    return true;
  }
  return false;
}

function stripWrappingQuotes(value) {
  const trimmed = value.trim();
  if (
    (trimmed.startsWith('"') && trimmed.endsWith('"')) ||
    (trimmed.startsWith("'") && trimmed.endsWith("'"))
  ) {
    return trimmed.slice(1, -1).trim();
  }
  if (trimmed.startsWith('"') || trimmed.startsWith("'")) {
    return trimmed.slice(1).trim();
  }
  return trimmed;
}

function appendExerciseLines(lines, exercise) {
  const name = stripWrappingQuotes(exercise.name ?? "");
  const details = exercise.details?.trim();
  if (!name) {
    return;
  }
  if (name.includes("\n")) {
    for (const rawLine of name.split("\n")) {
      const line = stripWrappingQuotes(rawLine.trim());
      if (!line || isValidDayHeaderLine(line) || isStructuralLabel(line)) {
        continue;
      }
      if (line.startsWith("- ")) {
        lines.push(line);
      } else {
        lines.push(line);
      }
    }
    return;
  }
  lines.push(details ? `- ${name} — ${details}` : `- ${name}`);
}

function formatCycleText(cycle) {
  const exercises = (cycle?.exercises ?? []).filter((exercise) => !isJunkExercise(exercise, cycle.name));
  if (!exercises.length) {
    return "";
  }
  const lines = [];
  const cycleName = cycle.name?.trim() ?? "";
  if (cycleName && !isStructuralLabel(cycleName)) {
    lines.push(cycleName);
  }
  for (const exercise of exercises) {
    appendExerciseLines(lines, exercise);
  }
  return lines.join("\n");
}

export function formatWorkoutDisplayText(workout) {
  if (!workout) {
    return "";
  }
  if (!workout.cycles?.length) {
    return workout.title || "";
  }
  return workout.cycles
    .map((cycle) => formatCycleText(cycle))
    .filter(Boolean)
    .join("\n\n")
    .trim();
}

export function buildDayBlockText(dateInput, body) {
  const header = formatDayHeader(dateInput);
  const normalizedBody = (body || "").trim();
  return normalizedBody ? `${header}\n\n${normalizedBody}` : header;
}

export function buildWeekRawText(startDateInput, dayBodies) {
  const start = new Date(`${startDateInput}T00:00:00`);
  const blocks = dayBodies.map((body, index) => {
    const date = new Date(start);
    date.setDate(start.getDate() + index);
    const iso = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    return buildDayBlockText(iso, body);
  });
  return blocks.filter(Boolean).join("\n\n").trim();
}

export function splitWeekRawText(text) {
  if (!text?.trim()) {
    return [];
  }
  const normalized = text.replace(/\r\n/g, "\n").trim();
  const lines = normalized.split("\n");
  const blocks = [];
  let current = [];

  for (const line of lines) {
    if (isValidDayHeaderLine(line) && current.length > 0) {
      blocks.push(current.join("\n").trim());
      current = [line];
    } else {
      current.push(line);
    }
  }
  if (current.length > 0) {
    blocks.push(current.join("\n").trim());
  }
  return blocks.length > 0 ? blocks : [normalized];
}

export function mapWeekBlocksToFields(blocks, startDateInput, workouts = []) {
  const fields = Array.from({ length: 7 }, () => ({ title: "", text: "" }));
  const usedBlocks = new Set();

  for (let dayIndex = 0; dayIndex < 7; dayIndex += 1) {
    const date = new Date(`${startDateInput}T00:00:00`);
    date.setDate(date.getDate() + dayIndex);
    const iso = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    const expectedHeader = formatDayHeader(iso);
    const blockIndex = blocks.findIndex(
      (block, index) => !usedBlocks.has(index) && block.split("\n")[0]?.trim() === expectedHeader,
    );
    if (blockIndex < 0) {
      continue;
    }
    usedBlocks.add(blockIndex);
    const workout = workouts.find(
      (item) => String(item.planned_date ?? "").slice(0, 10) === iso,
    );
    fields[dayIndex] = {
      title: workout?.title ?? "",
      text: extractDayBodyFromBlock(blocks[blockIndex]),
    };
  }

  return fields;
}

export function countWeekDayHeaders(text) {
  if (!text?.trim()) {
    return 0;
  }
  const lines = text.replace(/\r\n/g, "\n").split("\n");
  return lines.filter((line) => isValidDayHeaderLine(line)).length;
}

export function extractDayBodyFromBlock(block) {
  const lines = block.split("\n");
  const bodyLines = [];
  let skippedHeader = false;

  for (const line of lines) {
    if (!skippedHeader && isValidDayHeaderLine(line)) {
      skippedHeader = true;
      continue;
    }
    if (skippedHeader || !isValidDayHeaderLine(line)) {
      bodyLines.push(line);
    }
  }
  return bodyLines.join("\n").trim();
}

export function mergeDayIntoWeekRawText(weekText, dateInput, dayBody) {
  const startDate = new Date(`${dateInput}T00:00:00`);
  const targetHeader = formatDayHeader(dateInput);
  const newBlock = buildDayBlockText(dateInput, dayBody);
  const blocks = splitWeekRawText(weekText);
  let replaced = false;

  const updated = blocks.map((block) => {
    const firstLine = block.split("\n")[0]?.trim() ?? "";
    if (firstLine === targetHeader) {
      replaced = true;
      return newBlock;
    }
    return block;
  });

  if (!replaced) {
    const insertAt = Math.min(
      Math.max(0, Math.floor((startDate - new Date(blocks[0] ? `${dateInput}T00:00:00` : dateInput)) / 86400000)),
      updated.length,
    );
    updated.splice(insertAt, 0, newBlock);
  }

  return updated.filter(Boolean).join("\n\n").trim();
}

export function computeTextDiff(oldText, newText) {
  const oldLines = (oldText || "").split("\n");
  const newLines = (newText || "").split("\n");
  const max = Math.max(oldLines.length, newLines.length);
  const result = [];

  for (let index = 0; index < max; index += 1) {
    const oldLine = oldLines[index];
    const newLine = newLines[index];
    if (oldLine === undefined) {
      result.push({ type: "added", text: newLine });
      continue;
    }
    if (newLine === undefined) {
      result.push({ type: "removed", text: oldLine });
      continue;
    }
    if (oldLine === newLine) {
      result.push({ type: "same", text: oldLine });
      continue;
    }
    result.push({ type: "removed", text: oldLine });
    result.push({ type: "added", text: newLine });
  }
  return result;
}
