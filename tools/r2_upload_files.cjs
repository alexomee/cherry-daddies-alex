// Upload arbitrary files to R2 with Content-Type inferred from the key extension.
// CommonJS (.cjs) — aws-sdk v2 resolved via NODE_PATH (agentiqa/node_modules).
// Creds come from env (set by the python wrapper; never written to disk).
//   node tools/r2_upload_files.cjs <manifest.json>     manifest = [{ file, key }, ...]
// Unlike r2_upload_mixes.cjs (audio/mpeg only) this sets text/html for the page
// and video/mp4 for clips so the gallery streams inline in a browser.
const fs = require("fs");
const path = require("path");
const AWS = require("aws-sdk");

const CT = {
  ".mp4": "video/mp4",
  ".html": "text/html; charset=utf-8",
  ".mp3": "audio/mpeg",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
};

const manifest = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const Bucket = process.env.R2_BUCKET_NAME;
const s3 = new AWS.S3({
  endpoint: process.env.R2_ENDPOINT,
  accessKeyId: process.env.R2_ACCESS_KEY_ID,
  secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  signatureVersion: "v4",
  region: "auto",
  s3ForcePathStyle: true,
});

(async () => {
  let done = 0, fail = 0;
  for (const it of manifest) {
    const ct = CT[path.extname(it.key).toLowerCase()] || "application/octet-stream";
    try {
      await s3.putObject({
        Bucket, Key: it.key, Body: fs.readFileSync(it.file), ContentType: ct,
      }).promise();
      done++;
      console.log(`✓ ${done}/${manifest.length} ${it.key} [${ct}]`);
    } catch (e) {
      fail++;
      console.error(`✗ ${it.key}: ${e.message}`);
    }
  }
  console.log(`DONE: ${done} ok, ${fail} fail of ${manifest.length}`);
  process.exit(fail ? 1 : 0);
})();
