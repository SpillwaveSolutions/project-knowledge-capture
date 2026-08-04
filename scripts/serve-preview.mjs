#!/usr/bin/env node
/**
 * Static preview server for the PKC plugin docs + sample-knowledge.
 * Binds 0.0.0.0:8080 for the live preview proxy.
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const PORT = Number(process.env.PORT || 8080);
const HOST = process.env.HOST || "0.0.0.0";

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".md": "text/markdown; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".txt": "text/plain; charset=utf-8",
  ".yml": "text/yaml; charset=utf-8",
  ".yaml": "text/yaml; charset=utf-8",
};

function safeJoin(base, reqPath) {
  const decoded = decodeURIComponent(reqPath.split("?")[0]);
  const cleaned = path.normalize(decoded).replace(/^(\.\.(\/|\\|$))+/, "");
  const full = path.join(base, cleaned);
  if (!full.startsWith(base)) return null;
  return full;
}

function send(res, status, body, type = "text/plain; charset=utf-8") {
  res.writeHead(status, {
    "Content-Type": type,
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
  });
  res.end(body);
}

const server = http.createServer((req, res) => {
  const url = req.url || "/";

  if (url === "/" || url === "/index.html") {
    const html = fs.readFileSync(path.join(ROOT, "preview", "index.html"), "utf8");
    return send(res, 200, html, MIME[".html"]);
  }

  // Serve plugin files for the explorer
  const mounts = [
    ["/sample-knowledge/", path.join(ROOT, "sample-knowledge")],
    ["/docs/", path.join(ROOT, "docs")],
    ["/skills/", path.join(ROOT, "skills")],
    ["/templates/", path.join(ROOT, "templates")],
    ["/preview/", path.join(ROOT, "preview")],
    ["/README.md", path.join(ROOT, "README.md")],
    ["/AGENTS.md", path.join(ROOT, "AGENTS.md")],
    ["/CLAUDE.md", path.join(ROOT, "CLAUDE.md")],
  ];

  for (const [prefix, base] of mounts) {
    if (prefix.endsWith(".md")) {
      if (url === prefix || url.startsWith(prefix + "?")) {
        if (!fs.existsSync(base)) return send(res, 404, "Not found");
        return send(res, 200, fs.readFileSync(base), MIME[".md"]);
      }
      continue;
    }
    if (url.startsWith(prefix)) {
      const rel = url.slice(prefix.length) || "index.md";
      const file = safeJoin(base, rel);
      if (!file) return send(res, 403, "Forbidden");
      let target = file;
      if (fs.existsSync(target) && fs.statSync(target).isDirectory()) {
        target = path.join(target, "index.md");
      }
      if (!fs.existsSync(target) || !fs.statSync(target).isFile()) {
        return send(res, 404, `Not found: ${url}`);
      }
      const ext = path.extname(target).toLowerCase();
      return send(res, 200, fs.readFileSync(target), MIME[ext] || "application/octet-stream");
    }
  }

  // API: list sample knowledge tree
  if (url === "/api/tree") {
    const sk = path.join(ROOT, "sample-knowledge");
    const walk = (dir, prefix = "") => {
      const out = [];
      for (const name of fs.readdirSync(dir).sort()) {
        const full = path.join(dir, name);
        const rel = prefix ? `${prefix}/${name}` : name;
        const st = fs.statSync(full);
        if (st.isDirectory()) out.push(...walk(full, rel));
        else if (name.endsWith(".md")) out.push(rel);
      }
      return out;
    };
    return send(res, 200, JSON.stringify({ files: walk(sk) }, null, 2), MIME[".json"]);
  }

  if (url === "/api/meta") {
    const plugin = JSON.parse(
      fs.readFileSync(path.join(ROOT, ".claude-plugin", "plugin.json"), "utf8"),
    );
    return send(
      res,
      200,
      JSON.stringify(
        {
          name: plugin.name,
          version: plugin.version,
          description: plugin.description,
          skills: fs.readdirSync(path.join(ROOT, "skills")).filter((d) =>
            fs.existsSync(path.join(ROOT, "skills", d, "SKILL.md")),
          ),
          commands: fs
            .readdirSync(path.join(ROOT, "commands"))
            .filter((f) => f.endsWith(".md"))
            .map((f) => f.replace(/\.md$/, "")),
        },
        null,
        2,
      ),
      MIME[".json"],
    );
  }

  send(res, 404, "Not found");
});

server.listen(PORT, HOST, () => {
  console.log(`PKC preview listening on http://${HOST}:${PORT}`);
});
