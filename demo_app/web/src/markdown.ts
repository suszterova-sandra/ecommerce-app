const esc = (s: string) =>
  s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);

/** Minimal markdown for AI answers. Input is HTML-escaped first, so the output is safe to inject. */
export function markdown(src: string): string {
  const out: string[] = [];
  let list: "ul" | "ol" | null = null;
  let table: string[] | null = null;
  const inline = (s: string) =>
    s
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>")
      .replace(/(^|[^*])\*([^*\s][^*]*)\*/g, "$1<i>$2</i>")
      .replace(/(^|\s)_([^_]+)_(?=\s|$|[.,])/g, "$1<i>$2</i>");
  const closeList = () => {
    if (list) out.push(`</${list}>`);
    list = null;
  };
  const closeTable = () => {
    if (table) out.push(`<table>${table.join("")}</table>`);
    table = null;
  };
  // agents cite objects as {metric/net_sales}; the UI shows titles already, so drop the raw references
  const clean = (src || "").replace(/\s?\{(metric|label|attribute|fact|dataset|visualization|dashboard|insight)\/[^}\s]+\}/g, "");
  for (const raw of esc(clean).split("\n")) {
    const line = raw.trimEnd();
    if (/^\s*\|.*\|\s*$/.test(line)) {
      closeList();
      if (/^\s*\|[\s:|-]+\|\s*$/.test(line)) continue;
      table = table || [];
      const cells = line.trim().slice(1, -1).split("|").map((c) => inline(c.trim()));
      table.push(`<tr>${cells.map((c) => `<td>${c}</td>`).join("")}</tr>`);
      continue;
    }
    closeTable();
    let m: RegExpExecArray | null;
    if ((m = /^#{1,6}\s+(.*)$/.exec(line))) {
      closeList();
      out.push(`<h4>${inline(m[1])}</h4>`);
    } else if ((m = /^\s*[-*•]\s+(.*)$/.exec(line))) {
      if (list !== "ul") {
        closeList();
        out.push("<ul>");
        list = "ul";
      }
      out.push(`<li>${inline(m[1])}</li>`);
    } else if ((m = /^\s*\d+[.)]\s+(.*)$/.exec(line))) {
      if (list !== "ol") {
        closeList();
        out.push("<ol>");
        list = "ol";
      }
      out.push(`<li>${inline(m[1])}</li>`);
    } else if (!line.trim()) {
      closeList();
    } else {
      closeList();
      out.push(`<p>${inline(line)}</p>`);
    }
  }
  closeList();
  closeTable();
  return out.join("");
}
