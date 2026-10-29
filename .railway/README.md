# Railway configuration

`railway.ts` sets how Railway builds and runs the web service (`DocuMint`):

- the Dockerfile build;
- migrations as the pre-deploy step;
- the `/healthz` health check;
- restart on failure;
- the Singapore region with one replica.

It manages only that service. The Worker, Postgres and the bucket keep their settings in the Railway dashboard. Variables are listed with `preserve()`, so their values stay in Railway and never appear in this file.

Railway does not read this file when it deploys. A change to it takes effect only once it is applied:

```bash
cd .railway
npm ci                      # once: the Railway SDK the CLI uses to read railway.ts (Node 22.6+)
railway config plan         # what would change in Railway (reads only)
railway config apply        # make those changes; asks to confirm, then redeploys the service
```

Add a new variable to `VARIABLES` in `railway.ts` before applying. Otherwise the plan stops and lists the variable it doesn't know about.
