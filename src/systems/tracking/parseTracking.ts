/**
 * Restricted YAML parser for tracking/ files (D-008 dashboard).
 *
 * ponytail: deliberately tiny instead of a yaml dependency. Supported syntax is
 * exactly what progress-tracking-schema.md allows the files to use: `key: value`
 * maps nested by two-space indentation, `- item` string lists, `#` comments,
 * quoted strings, null/true/false/[]. Anything else throws, so a malformed
 * tracking file fails the build instead of rendering a wrong status.
 */

export type TrackingValue =
  | string
  | boolean
  | null
  | TrackingValue[]
  | { [key: string]: TrackingValue };

export type TrackingDoc = { [key: string]: TrackingValue };

function scalar(raw: string): TrackingValue {
  const v = raw.trim();
  if (v === "" || v === "null" || v === "~") return null;
  if (v === "true") return true;
  if (v === "false") return false;
  if (v === "[]") return [];
  const quoted = v.match(/^"(.*)"$/) ?? v.match(/^'(.*)'$/);
  return quoted ? quoted[1]! : v;
}

export function parseTrackingYaml(src: string, file = "tracking.yaml"): TrackingDoc {
  const root: TrackingDoc = {};
  // Each frame is a map plus the indent column its keys sit at.
  const stack: Array<{ keysIndent: number; node: TrackingDoc }> = [{ keysIndent: 0, node: root }];
  let list: { arr: TrackingValue[]; indent: number } | null = null;
  const lines = src.split("\n");

  const fail = (n: number, why: string): never => {
    throw new Error(`${file}:${n + 1} ${why}`);
  };

  for (let i = 0; i < lines.length; i++) {
    const rawLine = lines[i]!;
    if (rawLine.includes("\t")) fail(i, "tab indentation is not supported");
    const line = rawLine.replace(/\s+$/, "");
    if (!line || /^\s*#/.test(line)) continue;
    const indent = line.length - line.trimStart().length;
    const body = line.trim();

    if (body.startsWith("- ")) {
      if (!list || indent < list.indent) fail(i, "list item outside a list context");
      list!.arr.push(scalar(body.slice(2)));
      continue;
    }
    list = null;

    if (/^[[{&*|>]/.test(body)) fail(i, `unsupported YAML syntax: ${body}`);
    const m = body.match(/^([A-Za-z_][\w-]*):(.*)$/);
    if (!m) fail(i, `unsupported line: ${body}`);
    const key = m![1]!;
    const rest = m![2] ?? "";

    while (stack.length > 1 && indent < stack[stack.length - 1]!.keysIndent) stack.pop();
    const frame = stack[stack.length - 1]!;
    if (indent !== frame.keysIndent) fail(i, `bad indentation (${indent})`);

    if (rest.trim() !== "") {
      frame.node[key] = scalar(rest);
      continue;
    }

    // Empty value: decide by the next non-empty, non-comment line.
    let j = i + 1;
    while (j < lines.length && (!lines[j]!.trim() || /^\s*#/.test(lines[j]!))) j++;
    const next = j < lines.length ? lines[j]! : "";
    const nextIndent = next.length - next.trimStart().length;
    if (next.trim().startsWith("- ") && nextIndent > indent) {
      const arr: TrackingValue[] = [];
      frame.node[key] = arr;
      list = { arr, indent: nextIndent };
    } else if (next.trim() && nextIndent > indent && !next.trim().startsWith("- ")) {
      const child: TrackingDoc = {};
      frame.node[key] = child;
      stack.push({ keysIndent: nextIndent, node: child });
    } else {
      frame.node[key] = null;
    }
  }
  return root;
}
