// Simple bundle analysis script
import fs from "fs";
import path from "path";

const distDir = "./dist/assets";
const files = fs.readdirSync(distDir);

const jsFiles = files
  .filter((f) => f.endsWith(".js"))
  .map((f) => {
    const stats = fs.statSync(path.join(distDir, f));
    return { name: f, size: stats.size };
  })
  .sort((a, b) => b.size - a.size);

console.log("\n=== Top 10 JS Bundle Sizes ===\n");
jsFiles.slice(0, 10).forEach((file, idx) => {
  const sizeMB = (file.size / 1024 / 1024).toFixed(2);
  const sizeKB = (file.size / 1024).toFixed(2);
  console.log(`${idx + 1}. ${file.name}`);
  console.log(`   Size: ${sizeMB} MB (${sizeKB} KB)\n`);
});

const totalSize = jsFiles.reduce((sum, f) => sum + f.size, 0);
console.log(`Total JS size: ${(totalSize / 1024 / 1024).toFixed(2)} MB`);
