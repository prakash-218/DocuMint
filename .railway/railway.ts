// How Railway builds and runs the web service (it replaces railway.json, which Railway stops reading on 2026-12-01).
// It is applied by hand with the Railway CLI, not on deploy: see README.md next to this file.
import { defineRailway, github, preserve, project, service } from "railway/iac";

// This file manages only the web service; the Worker, Postgres and the bucket keep their own settings in Railway.
export const partial = "DocuMint";

// The values stay in Railway: listed here only so Railway knows they're meant to be there.
const VARIABLES = [
  "$PORT", "DATABASE_URL", "DB_HOST", "DB_NAME", "DB_PASSWORD", "DB_PORT", "DB_USER",
  "EMAIL_ACCOUNTS", "EMAIL_ORG_DOMAIN", "EMAIL_SYNC_DAYS", "FLASK_DEBUG", "FLASK_ENV",
  "GMAIL_IMAP_FOLDERS", "GMAIL_IMAP_HOST", "GMAIL_IMAP_MATCH", "GMAIL_IMAP_PASSWORD", "GMAIL_IMAP_USER",
  "GMAIL_SMTP_FROM", "GMAIL_SMTP_HOST", "JWT_SECRET", "MYSQL_DATABASE",
  "S3_ACCESS_KEY_ID", "S3_BUCKET", "S3_ENDPOINT", "S3_REGION", "S3_SECRET_ACCESS_KEY", "SECRET_KEY",
];

export default defineRailway(() => {
  const web = service("DocuMint", {
    source: github("prakash-218/DocuMint"),
    build: { builder: "DOCKERFILE", dockerfilePath: "Dockerfile" },
    preDeploy: "python scripts/dbtool.py migrate",       // migrations run before the new version takes traffic
    healthcheck: "/healthz",
    healthcheckTimeout: 60,
    deploy: { restartPolicyType: "ON_FAILURE", restartPolicyMaxRetries: 10 },
    regions: { "asia-southeast1-eqsg3a": 1 },          // Singapore, one replica
    env: Object.fromEntries(VARIABLES.map((name) => [name, preserve()])),
  });
  return project("DocuMint", { resources: [web] });
});
