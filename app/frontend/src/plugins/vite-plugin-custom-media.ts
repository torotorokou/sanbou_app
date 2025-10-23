import fs from "fs";
import path from "path";
import type { Plugin, ResolvedConfig, ViteDevServer } from "vite";

type AntMap = Record<string, number>;

function readANT(projectRoot: string): AntMap {
  const target = path.resolve(projectRoot, "src/shared/constants/breakpoints.ts");
  if (!fs.existsSync(target)) {
    throw new Error(`[vite-plugin-custom-media] Not found: ${target}`);
  }
  // 雑にパース: export const bp = { ... } as const; を読み取る
  const src = fs.readFileSync(target, "utf8");
  const m = src.match(/export const bp\s*=\s*\{([\s\S]*?)\}\s*as const/);
  if (!m) throw new Error("[vite-plugin-custom-media] bp object not found.");
  const body = m[1];
  const map: AntMap = {};
  // 行ごとに key: value を抽出
  for (const line of body.split("\n")) {
    const mm = line.trim().match(/^([a-zA-Z0-9_]+)\s*:\s*([0-9]+)\s*,?\s*$/);
    if (mm) {
      const [, k, v] = mm;
      map[k] = Number(v);
    }
  }
  if (!("md" in map) || !("xl" in map)) {
    throw new Error("[vite-plugin-custom-media] bp must include at least md and xl.");
  }
  return map;
}

function generateCSS(ANT: AntMap): string {
  const md = ANT.md;   // 768
  const xl = ANT.xl;   // 1200
  const mdMax = md - 1; // 767

  // 3本構成: --lt-md / --ge-md / --ge-xl
  return `/* AUTO-GENERATED from src/shared/constants/breakpoints.ts. Do not edit. */
@custom-media --lt-md (max-width: ${mdMax}px);   /* ≤${mdMax} */
@custom-media --ge-md (min-width: ${md}px);      /* ≥${md} */
@custom-media --ge-xl (min-width: ${xl}px);      /* ≥${xl} */
`;
}

function writeOut(projectRoot: string, css: string): string {
  const outPath = path.resolve(projectRoot, "src/shared/theme/responsive.css");
  
  // 既存ファイルを読み取ってカスタムメディア部分のみを置換
  let existingContent = "";
  if (fs.existsSync(outPath)) {
    existingContent = fs.readFileSync(outPath, "utf8");
  }
  
  // カスタムメディア定義のマーカー
  const startMarker = "/* === AUTO-GENERATED CUSTOM MEDIA (DO NOT EDIT) === */";
  const endMarker = "/* === END AUTO-GENERATED === */";
  
  // 既存のカスタムメディアセクションを置換
  const startIdx = existingContent.indexOf(startMarker);
  const endIdx = existingContent.indexOf(endMarker);
  
  let newContent: string;
  if (startIdx !== -1 && endIdx !== -1) {
    // マーカーが見つかった場合は該当部分を置換
    newContent = 
      existingContent.substring(0, startIdx) +
      startMarker + "\n" + css +
      existingContent.substring(endIdx);
  } else {
    // マーカーがない場合はファイル先頭に追加
    newContent = startMarker + "\n" + css + endMarker + "\n\n" + existingContent;
  }
  
  fs.writeFileSync(outPath, newContent, "utf8");
  return outPath;
}

export default function customMediaPlugin(): Plugin {
  let projectRoot = process.cwd();
  let breakpointsFile = "";

  const regenerate = () => {
    const ANT = readANT(projectRoot);
    const css = generateCSS(ANT);
    const out = writeOut(projectRoot, css);
    console.log(`[vite-plugin-custom-media] generated: ${path.relative(projectRoot, out)}`);
  };

  return {
    name: "vite-plugin-custom-media",
    configResolved(config: ResolvedConfig) {
      projectRoot = config.root || process.cwd();
      breakpointsFile = path.resolve(projectRoot, "src/shared/constants/breakpoints.ts");
    },
    buildStart() {
      // build時に確実に生成
      regenerate();
    },
    configureServer(server: ViteDevServer) {
      // dev起動時に初回生成
      regenerate();
      // 監視して変更時に再生成 + フルリロード
      server.watcher.add(breakpointsFile);
      server.watcher.on("change", (changed: string) => {
        if (path.resolve(changed) === breakpointsFile) {
          try {
            regenerate();
            server.ws.send({ type: "full-reload", path: "*" });
          } catch (e) {
            console.error("[vite-plugin-custom-media] regenerate error:", e);
          }
        }
      });
    },
  };
}
