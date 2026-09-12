// Upload dashboard mixes to R2. CommonJS (.cjs) — aws-sdk v2 resolved via NODE_PATH
// (agentiqa/node_modules). Creds come from env (set by the python wrapper; never on disk).
//   node tools/r2_upload_mixes.cjs <manifest.json>
// manifest = [{ file, key }, ...]
const fs = require("fs");
const AWS = require("aws-sdk");

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
  const CONCURRENCY = 12;
  let idx = 0;

  async function worker() {
    while (idx < manifest.length) {
      const it = manifest[idx++];
      try {
        await s3.putObject({
          Bucket, Key: it.key,
          Body: fs.readFileSync(it.file),
          ContentType: "audio/mpeg",
        }).promise();
        done++;
        console.log(`✓ ${done}/${manifest.length} ${it.key}`);
      } catch (e) {
        fail++;
        console.error(`✗ ${it.key}: ${e.message}`);
      }
    }
  }

  await Promise.all(Array.from({ length: CONCURRENCY }, () => worker()));
  console.log(`DONE: ${done} ok, ${fail} fail of ${manifest.length}`);
  process.exit(fail ? 1 : 0);
})();
