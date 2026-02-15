import { promises as fs } from 'node:fs';
import path from 'node:path';

const distDir = path.resolve(process.cwd(), 'dist');
const chunksDir = path.join(distDir, 'chunks');

const MAX_SINGLE_CHUNK_KB = Number(process.env.BUNDLE_MAX_CHUNK_KB || 350);
const MAX_TOTAL_JS_KB = Number(process.env.BUNDLE_MAX_TOTAL_JS_KB || 2400);

const bytesToKb = (bytes) => Number((bytes / 1024).toFixed(2));

async function main() {
  const entries = await fs.readdir(chunksDir, { withFileTypes: true });
  const jsFiles = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.js'))
    .map((entry) => entry.name);

  const sizes = [];
  for (const file of jsFiles) {
    const fullPath = path.join(chunksDir, file);
    const stat = await fs.stat(fullPath);
    sizes.push({
      file,
      bytes: stat.size,
      kb: bytesToKb(stat.size),
    });
  }

  sizes.sort((a, b) => b.bytes - a.bytes);

  const totalBytes = sizes.reduce((sum, file) => sum + file.bytes, 0);
  const totalKb = bytesToKb(totalBytes);

  const oversized = sizes.filter((file) => file.kb > MAX_SINGLE_CHUNK_KB);

  console.log(`Bundle budget check:`);
  console.log(`- max single chunk: ${MAX_SINGLE_CHUNK_KB} KB`);
  console.log(`- max total chunks JS: ${MAX_TOTAL_JS_KB} KB`);
  console.log(`- actual total chunks JS: ${totalKb} KB`);
  console.log(`- largest chunks:`);
  sizes.slice(0, 8).forEach((file) => {
    console.log(`  • ${file.file}: ${file.kb} KB`);
  });

  const failures = [];
  if (totalKb > MAX_TOTAL_JS_KB) {
    failures.push(`Total JS chunks size ${totalKb} KB exceeds ${MAX_TOTAL_JS_KB} KB.`);
  }

  if (oversized.length > 0) {
    failures.push(
      `Found ${oversized.length} chunk(s) exceeding ${MAX_SINGLE_CHUNK_KB} KB: ` +
      oversized.map((f) => `${f.file} (${f.kb} KB)`).join(', ')
    );
  }

  if (failures.length > 0) {
    console.error('\n❌ Bundle budget check failed:');
    failures.forEach((failure) => console.error(`- ${failure}`));
    process.exit(1);
  }

  console.log('\n✅ Bundle budget check passed.');
}

main().catch((error) => {
  console.error('❌ Failed to evaluate bundle budget:', error);
  process.exit(1);
});
