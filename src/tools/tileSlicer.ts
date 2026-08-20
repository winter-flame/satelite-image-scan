/**
 * Tile-slicing script for large planetary imagery.
 * Slices an input image into fixed-size tiles (default 512x512) with
 * configurable overlap, writing each tile to disk plus a manifest.json
 * describing tile positions (useful for reassembly or georeferencing).
 *
 * Usage:
 *   npx ts-node src/tools/tileSlicer.ts --input path/to/swath.tif --output tiles/ [--tileSize 512] [--overlap 64] [--format png] [--concurrency 4]
 */

import sharp from "sharp";
import path from "path";
import fs from "fs/promises";

interface TileMeta {
  index: number;
  filename: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface Options {
  input: string;
  output: string;
  tileSize: number;
  overlap: number;
  format: "png" | "jpeg" | "webp";
  concurrency: number;
}

function parseArgs(argv: string[]): Options {
  const get = (flag: string, fallback?: string) => {
    const i = argv.indexOf(flag);
    return i !== -1 ? argv[i + 1] : fallback;
  };

  const input = get("--input");
  const output = get("--output");
  if (!input || !output) {
    console.error(
      "Usage: ts-node tileSlicer.ts --input <path> --output <dir> [--tileSize 512] [--overlap 64] [--format png] [--concurrency 4]"
    );
    process.exit(1);
  }

  const tileSize = parseInt(get("--tileSize", "512")!, 10);
  const overlap = parseInt(get("--overlap", "64")!, 10);
  const format = (get("--format", "png") as Options["format"]);
  const concurrency = parseInt(get("--concurrency", "4")!, 10);

  if (overlap >= tileSize) {
    console.error("overlap must be smaller than tileSize");
    process.exit(1);
  }

  return { input, output, tileSize, overlap, format, concurrency };
}

/**
 * Computes tile origin coordinates along one axis.
 * Tiles march forward by (tileSize - overlap) each step. The final tile
 * is clamped to end exactly at `total`, so every tile is a full `tileSize`
 * (the last tile just overlaps its neighbor more than the standard stride).
 */
function computeOrigins(total: number, tileSize: number, overlap: number): number[] {
  if (total <= tileSize) return [0];

  const stride = tileSize - overlap;
  const origins: number[] = [];
  let pos = 0;

  while (pos + tileSize < total) {
    origins.push(pos);
    pos += stride;
  }
  origins.push(total - tileSize); // final tile, clamped flush to the edge

  // de-dupe in case stride pushed us exactly onto the last tile already
  return [...new Set(origins)];
}

async function runPool<T>(items: T[], concurrency: number, worker: (item: T, idx: number) => Promise<void>) {
  let cursor = 0;
  async function next(): Promise<void> {
    const i = cursor++;
    if (i >= items.length) return;
    await worker(items[i], i);
    return next();
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, items.length) }, () => next()));
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));

  await fs.mkdir(opts.output, { recursive: true });

  const image = sharp(opts.input, { limitInputPixels: false });
  const metadata = await image.metadata();

  if (!metadata.width || !metadata.height) {
    throw new Error("Could not read image dimensions. Is the input file valid?");
  }

  const { width, height } = metadata;
  console.log(`Input: ${opts.input} (${width}x${height})`);

  const xOrigins = computeOrigins(width, opts.tileSize, opts.overlap);
  const yOrigins = computeOrigins(height, opts.tileSize, opts.overlap);

  const positions: { x: number; y: number }[] = [];
  for (const y of yOrigins) {
    for (const x of xOrigins) {
      positions.push({ x, y });
    }
  }

  console.log(
    `Slicing into ${positions.length} tiles (${opts.tileSize}x${opts.tileSize}, overlap ${opts.overlap})`
  );

  const manifest: TileMeta[] = [];
  let done = 0;

  await runPool(positions, opts.concurrency, async ({ x, y }, index) => {
    const filename = `tile_${String(index).padStart(5, "0")}_x${x}_y${y}.${opts.format}`;
    const outPath = path.join(opts.output, filename);

    await sharp(opts.input, { limitInputPixels: false })
      .extract({ left: x, top: y, width: opts.tileSize, height: opts.tileSize })
      .toFormat(opts.format)
      .toFile(outPath);

    manifest.push({ index, filename, x, y, width: opts.tileSize, height: opts.tileSize });

    done++;
    if (done % 25 === 0 || done === positions.length) {
      console.log(`  ${done}/${positions.length} tiles written`);
    }
  });

  manifest.sort((a, b) => a.index - b.index);

  const manifestPath = path.join(opts.output, "manifest.json");
  await fs.writeFile(
    manifestPath,
    JSON.stringify(
      {
        source: opts.input,
        sourceWidth: width,
        sourceHeight: height,
        tileSize: opts.tileSize,
        overlap: opts.overlap,
        tileCount: manifest.length,
        tiles: manifest,
      },
      null,
      2
    )
  );

  console.log(`Done. ${manifest.length} tiles written to ${opts.output}`);
  console.log(`Manifest: ${manifestPath}`);
}

main().catch((err) => {
  console.error("Tile slicing failed:", err);
  process.exit(1);
});
