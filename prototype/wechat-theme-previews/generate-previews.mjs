import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const rootDir = path.dirname(fileURLToPath(import.meta.url));
const sourceMdPath = path.join(rootDir, "article.md");
const sourceImgDir = path.join(rootDir, "imgs");
const copiedMdPath = path.join(rootDir, "article.md");
const copiedImgDir = path.join(rootDir, "imgs");
const baoyuScriptPath = path.resolve("C:/Users/86156/.codex/skills/baoyu-markdown-to-html/scripts/main.ts");
const baoyuThemeIds = ["default", "grace", "simple", "modern"];

const ARTICLE_MAX_WIDTH = 720;
const PAGE_MAX_WIDTH = 860;
const sourceMarkdown = fs.readFileSync(sourceMdPath, "utf8");
const imageCaptions = extractImageCaptions(sourceMarkdown);

const themes = [
  {
    id: "claude",
    label: "Claude",
    note: "暖色强调、产品感、信息框明确",
    css: `
      :root {
        --bg: #f7f3ee;
        --surface: #fffdf9;
        --text: #312a25;
        --muted: #75675d;
        --line: #e7ddd1;
        --accent: #d86d47;
        --accent-soft: #f4e6de;
        --quote-bg: #faf5f0;
        --code-bg: #2f3138;
        --code-top: #444752;
        --table-head: #f7ebe3;
        --table-stripe: #fdf7f2;
        --caption-bg: #fbf3ec;
      }
      body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; background: var(--bg); }
      .page { max-width: ${PAGE_MAX_WIDTH}px; margin: 0 auto; padding: 32px 24px 72px; }
      .chrome { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; color:var(--muted); font-size:13px; letter-spacing:.04em; }
      .chip { background: var(--accent-soft); color: var(--accent); padding: 6px 12px; border-radius: 999px; font-weight: 700; }
      .article { max-width: ${ARTICLE_MAX_WIDTH}px; margin: 0 auto; background: linear-gradient(180deg, #fffdf9 0%, #fffaf4 100%); border: 1px solid rgba(216,109,71,.12); box-shadow: 0 24px 70px rgba(119,87,65,.08); border-radius: 28px; padding: 56px 56px 72px; }
      .article h1 { color: var(--accent); font-size: 44px; line-height: 1.15; letter-spacing: -.04em; margin: 0 0 20px; font-weight: 800; }
      .article h2 { font-size: 30px; margin: 56px 0 20px; color: #372e28; line-height: 1.3; font-weight: 800; display: inline-block; padding: 0 14px 8px 0; border-bottom: 3px solid rgba(216,109,71,.22); }
      .article h3 { font-size: 22px; margin: 32px 0 16px; color: #54453b; line-height: 1.35; font-weight: 700; }
      .article p, .article li, .article blockquote { font-size: 19px; line-height: 1.95; color: var(--text); }
      .article p { margin: 0 0 20px; }
      .article h1 + p { margin-top: 0; }
      .article h1 + p em { font-style: normal; color: #8b7d72; font-size: 16px; }
      .article hr { border: none; height: 1px; width: 132px; margin: 44px auto; background: linear-gradient(90deg, transparent 0%, rgba(216,109,71,.58) 50%, transparent 100%); }
      .article strong { color: var(--accent); background: linear-gradient(180deg, transparent 0%, transparent 58%, rgba(216,109,71,.15) 58%, rgba(216,109,71,.15) 100%); padding: 0 4px; }
      .article blockquote { margin: 30px 0; padding: 20px 24px; border-left: 4px solid var(--accent); background: linear-gradient(180deg, #fdf6f1 0%, #faf2ea 100%); color: #725d51; border-radius: 0 16px 16px 0; }
      .article pre { background: var(--code-bg); color: #f5f6f7; border-radius: 12px; padding: 18px 20px; overflow: auto; margin: 28px 0; position: relative; box-shadow: 0 18px 36px rgba(26,28,34,.18); }
      .article pre::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 30px; border-radius: 12px 12px 0 0; background: var(--code-top); }
      .article pre code { display: block; padding-top: 18px; font-size: 15px; line-height: 1.8; font-family: "JetBrains Mono", "Cascadia Code", monospace; white-space: pre-wrap; }
      .article code:not(pre code) { background: #f2ebe5; border-radius: 6px; padding: 2px 6px; font-size: .9em; }
    `,
  },
  {
    id: "nyt",
    label: "纽约时报",
    note: "报刊专栏感、克制、正式",
    css: `
      :root {
        --bg: #f6f4ef;
        --surface: #fffdfa;
        --text: #1f1c18;
        --muted: #615a54;
        --line: #d8d1c7;
        --quote-bg: #f4f2ee;
        --code-bg: #30333a;
        --code-top: #434754;
        --table-head: #f1ece4;
        --table-stripe: #faf7f2;
        --caption-bg: #f4efe8;
      }
      body { font-family: Georgia, "Noto Serif SC", "Songti SC", "STSong", serif; background: var(--bg); }
      .page { max-width: ${PAGE_MAX_WIDTH}px; margin: 0 auto; padding: 36px 24px 80px; }
      .chrome { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; color:var(--muted); font-size:13px; }
      .chip { border: 1px solid var(--line); padding: 6px 12px; font-weight: 700; letter-spacing: .06em; }
      .article { max-width: ${ARTICLE_MAX_WIDTH}px; margin: 0 auto; background: var(--surface); padding: 54px 56px 78px; box-shadow: 0 18px 50px rgba(39,31,24,.06); border: 1px solid #ece6dd; position: relative; }
      .article::before { content: ""; position: absolute; inset: 18px; border: 1px solid rgba(29,27,24,.08); pointer-events: none; }
      .article h1 { font-size: 45px; line-height: 1.14; color: #111; margin: 0 0 16px; font-weight: 700; letter-spacing: -.03em; }
      .article h1::after { content: ""; display:block; width:100%; height:1px; background:#1d1b18; margin-top:18px; }
      .article h2 { font-size: 31px; margin: 60px 0 22px; color: #151312; line-height: 1.26; font-weight: 700; text-align: center; }
      .article h2::after { content: ""; display: block; width: 84px; height: 1px; background: #1d1b18; margin: 12px auto 0; }
      .article h3 { font-size: 22px; margin: 34px 0 16px; color: #222; font-weight: 700; }
      .article p, .article li, .article blockquote { font-size: 19px; line-height: 1.96; color: var(--text); }
      .article p { margin: 0 0 20px; }
      .article h1 + p em { font-style: italic; color: var(--muted); font-size: 16px; }
      .article hr { border: none; height: 1px; width: 126px; margin: 42px auto; background: #d4ccc2; }
      .article strong { color: #111; font-weight: 700; }
      .article blockquote { margin: 30px 0; padding: 20px 26px; border-left: 3px solid #202020; background: var(--quote-bg); font-style: italic; }
      .article pre { background: var(--code-bg); color: #f4f4f6; border-radius: 8px; padding: 18px 20px; overflow: auto; margin: 28px 0; position: relative; box-shadow: 0 12px 30px rgba(23,25,31,.18); }
      .article pre::before { content: ""; position: absolute; inset: 0 0 auto 0; height: 28px; border-radius: 8px 8px 0 0; background: var(--code-top); }
      .article pre code { display:block; padding-top: 16px; font-size: 15px; line-height: 1.8; font-family: "JetBrains Mono", "Cascadia Code", monospace; white-space: pre-wrap; }
    `,
  },
  {
    id: "deep-reading",
    label: "深度阅读",
    note: "研究阅读感、沉浸、层次稳",
    css: `
      :root {
        --bg: #f4f5f7;
        --surface: #ffffff;
        --text: #22252b;
        --muted: #6f7683;
        --line: #dbe1ea;
        --quote-bg: #f7f9fc;
        --accent: #111827;
        --code-bg: #2f3440;
        --code-top: #474d5b;
        --table-head: #eef2f7;
        --table-stripe: #f8fafc;
        --caption-bg: #f4f7fb;
      }
      body { font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; background: var(--bg); }
      .page { max-width: ${PAGE_MAX_WIDTH}px; margin: 0 auto; padding: 26px 24px 72px; }
      .chrome { display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; color:var(--muted); font-size:13px; }
      .chip { background:#fff; border:1px solid var(--line); padding: 6px 12px; border-radius: 999px; font-weight: 700; }
      .article { max-width: ${ARTICLE_MAX_WIDTH}px; margin: 0 auto; background: var(--surface); padding: 48px 54px 70px; border-radius: 22px; box-shadow: 0 12px 40px rgba(34,44,66,.08); border: 1px solid #e8ecf2; }
      .article h1 { font-size: 42px; line-height: 1.18; color: #121821; margin: 0 0 18px; font-weight: 800; letter-spacing: -.03em; }
      .article h2 { font-size: 30px; margin: 58px 0 20px; color: #111827; line-height: 1.3; font-weight: 800; padding-left: 18px; border-left: 5px solid #c9d4e5; }
      .article h3 { font-size: 22px; margin: 34px 0 14px; color: #303846; font-weight: 700; }
      .article p, .article li, .article blockquote { font-size: 18px; line-height: 1.95; color: var(--text); }
      .article p { margin: 0 0 18px; }
      .article h1 + p em { font-style: normal; color: var(--muted); font-size: 15px; font-weight: 500; }
      .article hr { border:none; height:1px; width:134px; margin:40px auto; background:linear-gradient(90deg, transparent 0%, rgba(148,163,184,.72) 50%, transparent 100%); }
      .article strong { font-weight: 800; color: #111827; }
      .article blockquote { margin: 28px 0; padding: 20px 24px; border: 1px solid #e5eaf2; background: var(--quote-bg); color: #4b5563; border-left: 4px solid #1f2937; border-radius: 16px; }
      .article pre { background: var(--code-bg); color:#f5f7fa; border-radius: 10px; padding: 18px 20px; overflow:auto; margin: 28px 0; position:relative; box-shadow:0 14px 34px rgba(28,33,43,.18); }
      .article pre::before { content:""; position:absolute; inset:0 0 auto 0; height: 28px; border-radius:10px 10px 0 0; background: var(--code-top); }
      .article pre code { display:block; padding-top:16px; font-size:15px; line-height:1.8; font-family:"JetBrains Mono","Cascadia Code",monospace; white-space:pre-wrap; }
    `,
  },
  {
    id: "medium",
    label: "Medium",
    note: "现代长文、通透、易读",
    css: `
      :root {
        --bg: #f8f7f4;
        --surface: #ffffff;
        --text: #242424;
        --muted: #6b6b6b;
        --line: #e6e3dd;
        --quote-bg: #fafafa;
        --accent: #111111;
        --code-bg: #2f3136;
        --code-top: #44464d;
        --table-head: #f2f1ed;
        --table-stripe: #faf9f6;
        --caption-bg: #f6f5f2;
      }
      body { font-family: sohne, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif; background: var(--bg); }
      .page { max-width: ${PAGE_MAX_WIDTH}px; margin: 0 auto; padding: 34px 24px 88px; }
      .chrome { display:flex; justify-content:space-between; align-items:center; margin-bottom:24px; color:var(--muted); font-size:13px; }
      .chip { background:#fff; border:1px solid var(--line); padding:6px 12px; border-radius:999px; font-weight:700; }
      .article { max-width: ${ARTICLE_MAX_WIDTH}px; margin: 0 auto; background: var(--surface); padding: 42px 44px 68px; box-shadow: 0 12px 34px rgba(0,0,0,.05); border-radius: 18px; }
      .article h1 { font-size: 44px; line-height: 1.12; color: var(--accent); margin: 0 0 16px; font-weight: 800; letter-spacing: -.035em; }
      .article h2 { font-size: 31px; margin: 56px 0 18px; color: #151515; line-height: 1.28; font-weight: 800; letter-spacing: -.03em; }
      .article h3 { font-size: 23px; margin: 34px 0 14px; color: #333; font-weight: 700; }
      .article p, .article li, .article blockquote { font-size: 20px; line-height: 1.92; color: var(--text); }
      .article p { margin: 0 0 18px; }
      .article h1 + p em { font-style: normal; color: var(--muted); font-size: 15px; }
      .article hr { border:none; height:1px; width:132px; margin:40px auto; background:#ddd8cf; }
      .article strong { font-weight: 800; color:#151515; }
      .article blockquote { margin: 28px 0; padding: 8px 0 8px 18px; border-left: 3px solid #181818; background: transparent; color: #4b4b4b; font-style: italic; }
      .article pre { background: var(--code-bg); color:#f8f8f8; border-radius: 10px; padding: 18px 20px; overflow:auto; margin: 28px 0; position:relative; box-shadow: 0 12px 28px rgba(32,34,38,.18); }
      .article pre::before { content:""; position:absolute; inset:0 0 auto 0; height:28px; border-radius:10px 10px 0 0; background: var(--code-top); }
      .article pre code { display:block; padding-top:16px; font-size:15px; line-height:1.8; font-family:"JetBrains Mono","Cascadia Code",monospace; white-space:pre-wrap; }
    `,
  },
];

const sharedCss = `
  .article ul, .article ol { margin: 0 0 22px 1.2em; }
  .article li { margin-bottom: 10px; }
  figure.wechat-figure { margin: 34px 0; }
  figure.wechat-figure img { width: 100%; display: block; border-radius: 14px; box-shadow: 0 16px 38px rgba(25, 27, 31, 0.08); }
  figure.wechat-figure figcaption {
    margin-top: 12px;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.7;
    text-align: center;
    letter-spacing: .01em;
    background: var(--caption-bg);
    border-radius: 999px;
    display: inline-block;
    padding: 6px 14px;
    position: relative;
    left: 50%;
    transform: translateX(-50%);
  }
  .article table {
    width: 100%;
    border-collapse: collapse;
    margin: 28px 0;
    border: 1px solid var(--line);
    border-radius: 14px;
    overflow: hidden;
    table-layout: fixed;
    background: #fff;
  }
  .article th,
  .article td {
    padding: 14px 16px;
    border: 1px solid var(--line);
    text-align: left;
    vertical-align: top;
    font-size: 15px;
    line-height: 1.75;
  }
  .article th {
    background: var(--table-head);
    font-weight: 700;
  }
  .article tbody tr:nth-child(even) td {
    background: var(--table-stripe);
  }
  @media (max-width: 820px) {
    .page { padding: 20px 16px 48px; }
    .article { padding: 30px 22px 44px; border-radius: 16px; }
    .article h1 { font-size: 34px; }
    .article h2 { font-size: 26px; }
    .article h3 { font-size: 20px; }
    .article p, .article li, .article blockquote { font-size: 17px; }
    .article table { display: block; overflow-x: auto; white-space: nowrap; }
  }
`;

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function resolveBunRunner() {
  const candidates = [
    { command: "bun", args: [], useCmdShell: false },
    { command: "D:\\npx.cmd", args: ["-y", "bun"], useCmdShell: true },
    { command: "npx.cmd", args: ["-y", "bun"], useCmdShell: true },
    { command: "npx", args: ["-y", "bun"], useCmdShell: false },
  ];
  for (const candidate of candidates) {
    try {
      runProcess(candidate.command, [...candidate.args, "--version"], {
        stdio: "ignore",
        useCmdShell: candidate.useCmdShell,
      });
      return candidate;
    } catch {
      continue;
    }
  }
  throw new Error("未找到可用的 bun 或 npx 运行环境。");
}

function runProcess(command, args, options = {}) {
  if (options.useCmdShell) {
    return execFileSync("cmd.exe", ["/c", command, ...args], options);
  }
  return execFileSync(command, args, options);
}

function syncDir(sourceDir, targetDir) {
  ensureDir(targetDir);
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    const sourcePath = path.join(sourceDir, entry.name);
    const targetPath = path.join(targetDir, entry.name);
    if (entry.isDirectory()) {
      syncDir(sourcePath, targetPath);
      continue;
    }
    fs.copyFileSync(sourcePath, targetPath);
  }
}

function stripFrontmatter(text) {
  const match = text.match(/^---\n[\s\S]*?\n---\n([\s\S]*)$/);
  return match ? match[1] : text;
}

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function extractImageCaptions(markdown) {
  const map = new Map();
  const imageRegex = /!\[([^\]]*)\]\(([^)]+)\)/g;
  for (const match of markdown.matchAll(imageRegex)) {
    const alt = (match[1] || "").trim();
    const src = (match[2] || "").trim();
    if (src) {
      map.set(src, alt);
      map.set(src.replaceAll("\\", "/"), alt);
    }
  }
  return map;
}

function injectCaptionedFigures(html, captions) {
  return html.replace(/<p([^>]*)>\s*(<img\b[^>]*src="([^"]+)"[^>]*>)\s*<\/p>/g, (full, attrs, imgTag, src) => {
    const normalizedSrc = src.replaceAll("\\", "/");
    const caption = captions.get(src) || captions.get(normalizedSrc) || "";
    const captionHtml = caption ? `<figcaption>${escapeHtml(caption)}</figcaption>` : "";
    return `<figure class="preview-figure">${imgTag}${captionHtml}</figure>`;
  });
}

function buildBaoyuOverrideCss() {
  return `
    body {
      max-width: ${PAGE_MAX_WIDTH}px !important;
      margin: 0 auto !important;
      padding: 28px 20px 64px !important;
      background: #f5f2eb !important;
      box-sizing: border-box;
    }
    #output,
    #output > .container {
      max-width: ${ARTICLE_MAX_WIDTH}px !important;
      margin: 0 auto !important;
    }
    #output > .container {
      box-sizing: border-box;
    }
    .preview-figure {
      margin: 1.8em auto !important;
    }
    .preview-figure img {
      display: block !important;
      width: 100% !important;
      margin: 0 auto !important;
      border-radius: 12px;
    }
    .preview-figure figcaption {
      margin-top: 10px;
      text-align: center;
      color: #7a7a7a;
      font-size: 13px;
      line-height: 1.7;
    }
    table {
      width: 100% !important;
      border-collapse: collapse !important;
      margin: 1.8em 0 !important;
      table-layout: fixed;
      overflow: hidden;
    }
    th,
    td {
      border: 1px solid rgba(15, 23, 42, 0.14) !important;
      padding: 12px 14px !important;
      text-align: left !important;
      vertical-align: top !important;
      font-size: 14px !important;
      line-height: 1.75 !important;
      word-break: break-word !important;
      background: #ffffff;
    }
    th {
      background: #f4efe7 !important;
      font-weight: 700 !important;
    }
    tbody tr:nth-child(even) td {
      background: #faf8f4 !important;
    }
  `;
}

function postProcessBaoyuHtml(html, captions) {
  const css = buildBaoyuOverrideCss();
  let nextHtml = injectCaptionedFigures(html, captions);
  if (!nextHtml.includes("preview-figure")) {
    return nextHtml;
  }
  if (nextHtml.includes("data-preview-patch")) {
    return nextHtml;
  }
  nextHtml = nextHtml.replace("</head>", `<style data-preview-patch>${css}</style>\n</head>`);
  return nextHtml;
}

function renderCustomPreview(theme) {
  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>${theme.label} 预览</title>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    a { color: inherit; }
    ${theme.css}
    ${sharedCss}
  </style>
</head>
<body>
  <div class="page">
    <div class="chrome">
      <div>${theme.label} · ${theme.note}</div>
      <a href="./index.html">返回索引</a>
    </div>
    <article class="article" id="article"></article>
  </div>
  <script>
    const rawSource = ${JSON.stringify(sourceMarkdown)};

    function stripFrontmatter(text) {
      const match = text.match(/^---\\n([\\s\\S]*?)\\n---\\n([\\s\\S]*)$/);
      if (!match) return text;
      return match[2];
    }

    const renderer = new marked.Renderer();
    renderer.image = ({ href, text }) => {
      const safeAlt = text || "";
      const figcaption = safeAlt ? "<figcaption>" + safeAlt + "</figcaption>" : "";
      return "<figure class=\\"wechat-figure\\"><img src=\\"" + href + "\\" alt=\\"" + safeAlt + "\\" />" + figcaption + "</figure>";
    };
    renderer.blockquote = (quote) => {
      if (typeof quote === "string") return "<blockquote>" + quote + "</blockquote>";
      if (quote && Array.isArray(quote.tokens)) return "<blockquote>" + marked.Parser.parse(quote.tokens) + "</blockquote>";
      return "<blockquote></blockquote>";
    };
    renderer.hr = () => "<hr />";
    marked.setOptions({
      renderer,
      gfm: true,
      breaks: false,
    });

    const content = stripFrontmatter(rawSource);
    document.getElementById("article").innerHTML = marked.parse(content);
  </script>
</body>
</html>`;
}

function renderIndex() {
  const cards = [
    ...themes.map((theme) => ({ label: theme.label, note: theme.note, href: `${theme.id}.html`, group: "Wechat 主题" })),
  ];

  const cardHtml = cards
    .map(
      (card) => `
      <a class="card" href="${card.href}">
        <div class="group">${card.group}</div>
        <h2>${card.label}</h2>
        <p>${card.note}</p>
        <span>打开预览</span>
      </a>
    `,
    )
    .join("");

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>公众号主题对比</title>
  <style>
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: 32px 24px 60px;
      font-family: "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
      background: #f4f2ed;
      color: #1f2937;
    }
    .wrap { max-width: 1100px; margin: 0 auto; }
    h1 { margin: 0 0 12px; font-size: 34px; line-height: 1.15; }
    .intro { margin: 0 0 28px; font-size: 16px; line-height: 1.8; color: #5b6472; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 18px;
    }
    .card {
      display: block;
      padding: 22px 20px;
      border-radius: 18px;
      text-decoration: none;
      background: rgba(255,255,255,.9);
      border: 1px solid #e3ddd4;
      box-shadow: 0 16px 44px rgba(56,43,30,.06);
      transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
      color: inherit;
    }
    .card:hover {
      transform: translateY(-3px);
      box-shadow: 0 20px 50px rgba(56,43,30,.1);
      border-color: #d4c8bb;
    }
    .group {
      display: inline-block;
      margin-bottom: 12px;
      font-size: 12px;
      letter-spacing: .06em;
      color: #8a745f;
      background: #f3ece3;
      border-radius: 999px;
      padding: 5px 10px;
    }
    .card h2 {
      margin: 0 0 10px;
      font-size: 22px;
      line-height: 1.25;
    }
    .card p {
      margin: 0 0 14px;
      font-size: 14px;
      color: #667085;
      line-height: 1.7;
    }
    .card span {
      font-size: 13px;
      color: #111827;
      font-weight: 700;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>公众号排版主题对比</h1>
    <p class="intro">同一篇文章、同一组配图、同一张表格，并统一正文宽度与图注规则。这个仓库只保留 4 套自定义 Wechat 排版，用于后续 skill 化封装。</p>
    <div class="grid">
      ${cardHtml}
    </div>
  </div>
</body>
</html>`;
}

ensureDir(rootDir);

for (const theme of themes) {
  fs.writeFileSync(path.join(rootDir, `${theme.id}.html`), renderCustomPreview(theme), "utf8");
}

fs.writeFileSync(path.join(rootDir, "index.html"), renderIndex(), "utf8");
fs.writeFileSync(copiedMdPath, sourceMarkdown, "utf8");
syncDir(sourceImgDir, copiedImgDir);
