# CI/CD Pipelines

This directory contains GitHub Actions workflows for continuous integration and continuous deployment.

## Workflows

### 1. Backend CI/CD (`backend-ci-cd.yml`)
Handles backend application testing, building, and deployment.

**Triggers:**
- Push to `main` or `develop` branches (when backend files change)
- Pull requests to `main` or `develop` (when backend files change)

**Jobs:**
- **test**: Runs linting, type checking, and unit tests with coverage
- **build-and-push**: Builds and pushes Docker images to ACR
- **deploy-dev**: Deploys to development environment
- **deploy-prod**: Deploys to production environment

**Required Secrets:**
- `ACR_LOGIN_SERVER`: Azure Container Registry URL
- `ACR_USERNAME`: ACR username
- `ACR_PASSWORD`: ACR password
- `AZURE_CREDENTIALS_DEV`: Azure service principal for dev
- `AZURE_CREDENTIALS_PROD`: Azure service principal for prod

### 2. Frontend CI/CD (`frontend-ci-cd.yml`)
Handles frontend application testing, building, and deployment.

**Triggers:**
- Push to `main` or `develop` branches (when frontend files change)
- Pull requests to `main` or `develop` (when frontend files change)

**Jobs:**
- **test**: Runs linting, type checking, and builds
- **deploy-dev**: Deploys to Azure Static Web Apps (dev)
- **deploy-prod**: Deploys to Azure Static Web Apps (prod)

**Required Secrets:**
- `VITE_API_BASE_URL_DEV`: Development API URL
- `VITE_API_BASE_URL_PROD`: Production API URL
- `AZURE_STATIC_WEB_APPS_API_TOKEN_DEV`: Dev Static Web Apps token
- `AZURE_STATIC_WEB_APPS_API_TOKEN_PROD`: Prod Static Web Apps token

### 3. Infrastructure CI/CD (`infrastructure-ci-cd.yml`)
Handles Terraform infrastructure validation and deployment.

**Triggers:**
- Push to `main` or `develop` branches (when infrastructure files change)
- Pull requests to `main` or `develop` (when infrastructure files change)

**Jobs:**
- **validate**: Validates Terraform configuration
- **plan-dev/plan-prod**: Creates Terraform plans
- **apply-dev/apply-prod**: Applies infrastructure changes

**Required Secrets:**
- `AZURE_CREDENTIALS_DEV`: Azure service principal for dev
- `AZURE_CREDENTIALS_PROD`: Azure service principal for prod
- `AZURE_TENANT_ID`: Azure tenant ID
- `ACR_LOGIN_SERVER`: ACR URL for image references

### 4. Security Scanning (`security-scanning.yml`)
Runs security scans on dependencies, containers, code, and infrastructure.

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Scheduled daily at 2 AM UTC

**Jobs:**
- **dependency-scan**: Scans backend and frontend dependencies
- **container-scan**: Scans Docker images for vulnerabilities
- **codeql**: Static code analysis for Python and JavaScript
- **secret-scan**: Checks for leaked secrets using Gitleaks
- **terraform-security**: Scans Terraform with Checkov and tfsec

### 5. Pull Request Checks (`pr-checks.yml`)
Validates pull requests for quality and consistency.

**Triggers:**
- Pull requests to `main` or `develop` branches

**Jobs:**
- **pr-metadata**: Validates PR title format (conventional commits)
- **lint-commits**: Validates commit message format
- **conflict-check**: Checks for merge conflicts
- **label-sync**: Auto-labels based on changed files
- **auto-assign**: Auto-assigns reviewers

## Setup Instructions

### 1. Configure Azure Service Principals

Create service principals for each environment:

```bash
# Development
az ad sp create-for-rbac --name "sp-reportscheduler-dev" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-reportscheduler-dev \
  --sdk-auth

# Production
az ad sp create-for-rbac --name "sp-reportscheduler-prod" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-reportscheduler-prod \
  --sdk-auth
```

### 2. Set GitHub Secrets

Go to repository Settings → Secrets and variables → Actions:

**Container Registry:**
- `ACR_LOGIN_SERVER`: `crreportscheduler.azurecr.io`
- `ACR_USERNAME`: From ACR access keys
- `ACR_PASSWORD`: From ACR access keys

**Azure Credentials:**
- `AZURE_CREDENTIALS_DEV`: JSON output from dev service principal
- `AZURE_CREDENTIALS_PROD`: JSON output from prod service principal
- `AZURE_TENANT_ID`: Your Azure tenant ID

**Frontend:**
- `VITE_API_BASE_URL_DEV`: `https://ca-reportscheduler-api-dev.{region}.azurecontainerapps.io`
- `VITE_API_BASE_URL_PROD`: `https://ca-reportscheduler-api-prod.{region}.azurecontainerapps.io`
- `AZURE_STATIC_WEB_APPS_API_TOKEN_DEV`: From Static Web Apps deployment token
- `AZURE_STATIC_WEB_APPS_API_TOKEN_PROD`: From Static Web Apps deployment token

### 3. Configure GitHub Environments

Create environments in repository Settings → Environments:

**development:**
- Protection rules: Optional
- Deployment branches: `develop`

**production:**
- Protection rules: Required reviewers (recommended)
- Deployment branches: `main`

### 4. Enable Required GitHub Features

- Enable "Dependency graph" (Settings → Security → Code security)
- Enable "Dependabot alerts" (Settings → Security → Code security)
- Enable "Code scanning" (Settings → Security → Code security)
- Enable "Secret scanning" (Settings → Security → Code security)

### 5. Update Configuration Files

Edit `.github/auto-assign.yml` and `.github/labeler.yml`:
- Add reviewer usernames
- Add assignee usernames
- Customize file patterns if needed

## Workflow Behavior

### Branch Strategy

- **develop**: Development environment
  - Automatic deployment on push
  - Used for testing and validation
  
- **main**: Production environment
  - Automatic deployment on push
  - Should be protected with required reviews

### Deployment Flow

1. **Pull Request**:
   - PR checks run (title, commits, conflicts)
   - Tests run for affected components
   - Terraform plan generated (if infrastructure changed)
   - Security scans execute
   - Auto-labeling and reviewer assignment

2. **Merge to develop**:
   - Full test suite runs
   - Docker images built and pushed
   - Infrastructure applied (if changed)
   - Applications deployed to dev environment

3. **Merge to main**:
   - Full test suite runs
   - Docker images built and pushed
   - Infrastructure applied (if changed)
   - Applications deployed to prod environment
   - GitHub releases created

### Rolling Back

To rollback a deployment:

**Backend:**
```bash
az containerapp update \
  --name ca-reportscheduler-api-prod \
  --resource-group rg-reportscheduler-prod \
  --image crreportscheduler.azurecr.io/reportscheduler-api:previous-tag
```

**Frontend:**
Use Azure Static Web Apps portal to revert to previous deployment.

**Infrastructure:**
```bash
cd infrastructure/environments/prod
git checkout <previous-commit> -- .
terraform plan
terraform apply
```

## Monitoring

### GitHub Actions

- View workflow runs: Actions tab
- Check logs: Click on workflow run → Job → Step
- Download artifacts: Workflow run → Artifacts section

### Azure

- Container Apps logs: Azure Portal → Container App → Log stream
- Application Insights: Azure Portal → Application Insights → Logs/Metrics
- Static Web Apps: Azure Portal → Static Web App → Environment → Logs

## Troubleshooting

### Build Failures

1. **Backend tests fail:**
   - Check test logs in workflow run
   - Verify database/Redis service health
   - Check environment variables

2. **Docker build fails:**
   - Review Dockerfile syntax
   - Check base image availability
   - Verify build context paths

3. **Terraform apply fails:**
   - Review plan output
   - Check Azure permissions
   - Verify resource naming conflicts

### Deployment Failures

1. **Container app update fails:**
   - Check image exists in ACR
   - Verify container app name/resource group
   - Review Azure service health

2. **Static Web Apps deployment fails:**
   - Check deployment token validity
   - Verify build output location
   - Review app configuration

### Security Scan Issues

1. **Dependency vulnerabilities:**
   - Review Dependabot alerts
   - Update vulnerable packages
   - Check for patches/workarounds

2. **Container vulnerabilities:**
   - Update base images
   - Review Trivy scan results
   - Apply security patches

3. **Secret leaks:**
   - Review Gitleaks output
   - Rotate exposed secrets immediately
   - Update secret scanning patterns

## Best Practices

1. **Always use feature branches** for development
2. **Write descriptive commit messages** following conventional commits
3. **Keep PRs small and focused** (< 500 lines of code)
4. **Add tests** for new features and bug fixes
5. **Review Terraform plans** before merging infrastructure changes
6. **Monitor deployments** in Azure Portal after merges
7. **Tag releases** for better version tracking
8. **Rotate secrets regularly** (every 90 days recommended)
9. **Review security scan results** weekly
10. **Keep dependencies updated** using Dependabot

## Cost Optimization

- Development deployments use lower-tier resources
- Security scans run on schedule to avoid excessive usage
- Artifacts retained for 7 days only
- Consider disabling automatic deployments for infrequent changes

## Maintenance

### Regular Tasks

- **Weekly**: Review security scan results
- **Monthly**: Update GitHub Actions versions
- **Quarterly**: Rotate service principal credentials
- **Yearly**: Review and optimize workflow configurations

### Updating Workflows

1. Create feature branch
2. Modify workflow files
3. Test on feature branch
4. Create PR for review
5. Merge to develop first
6. Monitor dev deployments
7. Merge to main after validation
