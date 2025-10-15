import fs from "fs";
import path from "path";
import type { Plugin, ResolvedConfig, ViteDevServer } from "vite";

type AntMap = Record<string, number>;

function readANT(projectRoot: string): AntMap {
  const target = path.resolve(projectRoot, "src/shared/constants/breakpoints.ts");
  if (!fs.existsSync(target)) {
    throw new Error(`[vite-plugin-custom-media] Not found: ${target}`);
  }
  // 雑にパース: export const ANT = { ... } as const; を読み取る
  const src = fs.readFileSync(target, "utf8");
  const m = src.match(/export const ANT\s*=\s*\{([\s\S]*?)\}\s*as const/);
  if (!m) throw new Error("[vite-plugin-custom-media] ANT object not found.");
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
    throw new Error("[vite-plugin-custom-media] ANT must include at least md and xl.");
  }
  return map;
}

function generateCSS(ANT: AntMap): string {
  const md = ANT.md;
  const xl = ANT.xl;
  const mdMax = md - 1; // 767
  const xlMax = xl - 1; // 1199

  return `/* AUTO-GENERATED from src/shared/constants/breakpoints.ts. Do not edit. */
@custom-media --lt-md (max-width: ${mdMax}px);   /* ≤${mdMax} */
@custom-media --md-only (min-width: ${md}px) and (max-width: ${xlMax}px); /* ${md}–${xlMax} */
@custom-media --ge-xl (min-width: ${xl}px);      /* ≥${xl} */
`;
}

function writeOut(projectRoot: string, css: string): string {
  const outPath = path.resolve(projectRoot, "src/styles/custom-media.css");
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, css, "utf8");
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
