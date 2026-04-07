# Azure Dev Deployment

## Scope

This guide is for deploying both apps to Azure App Service in the dev environment:

- Resource Group: `shopbot-dev-rg`
- App Service Plan: `shopbot-asp`
- Frontend App Service: `shopbot-dev-fe`
- Backend App Service: `shopbot-dev-be`

## GitHub Secrets

For this single workflow, these two GitHub repository secrets are enough:

- `AZURE_WEBAPP_PUBLISH_PROFILE_FE`
- `AZURE_WEBAPP_PUBLISH_PROFILE_BE`

No other GitHub secrets are required if GitHub Actions only deploys code.

You only need more Azure auth secrets later if you want GitHub Actions to:

- update Azure App Settings
- run Azure CLI commands
- use OIDC instead of publish profiles

For that later upgrade, use:

- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

## Workflow File

Use:

- `.github/workflows/deploy-backend-dev.yml`

This single workflow:

1. builds and deploys the Next.js frontend
2. installs and verifies the FastAPI backend
3. deploys the backend

## Azure App Service Configuration

### Frontend App Service: `shopbot-dev-fe`

Recommended:

- Runtime stack: `Node 20 LTS`
- Startup command: `npm start`
- Always On: `On`
- HTTPS Only: `On`

Application Settings:

- `NEXT_PUBLIC_API_URL=https://shopbot-dev-be.azurewebsites.net`
- `SCM_DO_BUILD_DURING_DEPLOYMENT=true`
- `ENABLE_ORYX_BUILD=1`

### Backend App Service: `shopbot-dev-be`

Recommended:

- Runtime stack: `Python 3.11`
- Startup command: `gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app`
- Always On: `On`
- HTTPS Only: `On`

Application Settings:

- `DATABASE_URL=<your-dev-postgres-connection-string>`
- `JWT_SECRET_KEY=<strong-random-secret>`
- `FRONTEND_URL=https://shopbot-dev-fe.azurewebsites.net`
- `BACKEND_URL=https://shopbot-dev-be.azurewebsites.net`
- `ALLOWED_ORIGINS=https://shopbot-dev-fe.azurewebsites.net`
- `TRUSTED_HOSTS=shopbot-dev-be.azurewebsites.net`
- `ENVIRONMENT=development`
- `DEBUG=false`
- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=none`
- `SCM_DO_BUILD_DURING_DEPLOYMENT=1`
- `ENABLE_ORYX_BUILD=1`

Optional backend settings:

- `COMPANY_NAME=ShopBot`
- `ACCESS_TOKEN_EXPIRE_MINUTES=15`
- `REFRESH_TOKEN_EXPIRE_DAYS=30`
- `OPENAI_API_KEY=<your-dev-openai-key>`
- `COOKIE_DOMAIN=`

If Azure has trouble downloading publish profiles for Linux web apps, add:

- `WEBSITE_WEBDEPLOY_USE_SCM=true`

If remote build still doesn't run, make sure `WEBSITE_RUN_FROM_PACKAGE` is not set to `1`.

## Important Cookie Note

Your frontend and backend are on different Azure App Service hostnames.

Because of that, backend cookie auth should use:

- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=none`

Without those, browser auth cookies usually won't flow correctly between frontend and backend.

## Deployment Steps

1. Verify `shopbot-dev-fe` and `shopbot-dev-be` exist in `shopbot-dev-rg`.
2. Set frontend runtime to Node 20 LTS and backend runtime to Python 3.11.
3. Set the frontend startup command to `npm start`.
4. Set the backend startup command to `gunicorn -w 2 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 app.main:app`.
5. Add the frontend and backend Application Settings listed above.
6. Download the publish profiles for both App Services.
7. Save them in GitHub secrets:
   `AZURE_WEBAPP_PUBLISH_PROFILE_FE`
   `AZURE_WEBAPP_PUBLISH_PROFILE_BE`
8. Commit `.github/workflows/deploy-backend-dev.yml`.
9. Push to `dev` or run the workflow manually.
10. Check GitHub Actions logs and Azure log stream if either app fails to start.

## Dev Suitability

This setup is sufficient for development.

Recommended improvements:

1. Move from publish profiles to OIDC later.
2. Use a dedicated dev database.
3. Add Alembic migrations to the release flow.
4. Turn on Azure App Service logs for both apps.
5. Add a post-deploy health check later for `/health` on the backend.

## What You Still Need

From your side, I still need confirmation of:

- the exact dev `DATABASE_URL`
- whether `OPENAI_API_KEY` is required in dev
- whether both App Services are Linux or Windows
