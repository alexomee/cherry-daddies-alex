#!/usr/bin/env python3
"""Set and verify CORS rules on the R2 bucket (agentiqa-releases).

Allows GET and HEAD from all origins (*), including practice.cherrydaddies.com,
with exposed headers for Web Audio range requests.
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
AG = Path.home() / "projects" / "agentiqa"
DOC = AG / "docs" / "plans" / "2026-03-09-preview-release.md"


def creds_env():
    env = dict(os.environ)
    for line in DOC.read_text(encoding="utf-8").splitlines():
        m = re.match(r'^(R2_(?:ENDPOINT|ACCESS_KEY_ID|SECRET_ACCESS_KEY|BUCKET_NAME))=(.*)$', line.strip())
        if m:
            env[m.group(1)] = m.group(2)
    env["NODE_PATH"] = str(AG / "node_modules")
    for k in ("R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_BUCKET_NAME"):
        if not env.get(k):
            sys.exit(f"missing {k} in {DOC}")
    return env


NODE_SCRIPT = """
const AWS = require('aws-sdk');
const s3 = new AWS.S3({
  endpoint: process.env.R2_ENDPOINT,
  accessKeyId: process.env.R2_ACCESS_KEY_ID,
  secretAccessKey: process.env.R2_SECRET_ACCESS_KEY,
  signatureVersion: 'v4',
  region: 'auto',
  s3ForcePathStyle: true,
});

async function main() {
  const Bucket = process.env.R2_BUCKET_NAME;
  const corsParams = {
    Bucket,
    CORSConfiguration: {
      CORSRules: [
        {
          AllowedHeaders: ['*'],
          AllowedMethods: ['GET', 'HEAD'],
          AllowedOrigins: ['*'],
          ExposeHeaders: ['ETag', 'Content-Length', 'Accept-Ranges', 'Content-Range'],
          MaxAgeSeconds: 86400,
        }
      ]
    }
  };
  await s3.putBucketCors(corsParams).promise();
  const current = await s3.getBucketCors({ Bucket }).promise();
  console.log('R2 CORS configured successfully on', Bucket, ':', JSON.stringify(current, null, 2));
}

main().catch(err => {
  console.error('Failed to set CORS:', err);
  process.exit(1);
});
"""


def main():
    env = creds_env()
    subprocess.run(["node", "-e", NODE_SCRIPT], env=env, check=True)


if __name__ == "__main__":
    main()
