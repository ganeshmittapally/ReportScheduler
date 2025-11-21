# Azure Pipelines CI/CD

This directory contains Azure Pipelines YAML configurations for Azure DevOps as an alternative to GitHub Actions.

## Pipelines

### 1. Backend Pipeline (`azure-pipelines-backend.yml`)
Handles backend testing, Docker image building, and deployment.

**Stages:**
- **Test**: Linting, type checking, unit tests with coverage
- **Build**: Docker image building and pushing to ACR
- **DeployDev**: Deployment to development environment
- **DeployProd**: Deployment to production environment

### 2. Frontend Pipeline (`azure-pipelines-frontend.yml`)
Handles frontend testing, building, and deployment to Azure Static Web Apps.

**Stages:**
- **Test**: Linting, type checking, and build
- **DeployDev**: Deployment to development Static Web App
- **DeployProd**: Deployment to production Static Web App

### 3. Infrastructure Pipeline (`azure-pipelines-infrastructure.yml`)
Handles Terraform validation, planning, and deployment.

**Stages:**
- **Validate**: Terraform format check and validation
- **PlanDev/PlanProd**: Create Terraform plans
- **ApplyDev/ApplyProd**: Apply infrastructure changes

## Setup Instructions

### 1. Create Azure DevOps Project

1. Go to https://dev.azure.com
2. Create a new organization (if needed)
3. Create a new project named "ReportScheduler"

### 2. Configure Service Connections

#### Azure Resource Manager Connections

Create service connections for each environment:

1. Go to Project Settings → Service connections
2. Click "New service connection" → "Azure Resource Manager"
3. Select "Service principal (automatic)"
4. Configure:
   - **Name**: `Azure-ServiceConnection-Dev`
   - **Scope**: Subscription
   - **Resource group**: `rg-reportscheduler-dev`
   
5. Repeat for production:
   - **Name**: `Azure-ServiceConnection-Prod`
   - **Resource group**: `rg-reportscheduler-prod`

#### Azure Container Registry Connection

1. Create new service connection → "Docker Registry"
2. Configure:
   - **Registry type**: Azure Container Registry
   - **Connection name**: `ACR-ServiceConnection`
   - **Azure subscription**: Select your subscription
   - **Azure container registry**: Select your ACR

### 3. Create Variable Groups

#### reportscheduler-variables

1. Go to Pipelines → Library → + Variable group
2. Name: `reportscheduler-variables`
3. Add variables:
   - `ACR_LOGIN_SERVER`: `crreportscheduler.azurecr.io`
   - `VITE_API_BASE_URL_DEV`: Dev API URL
   - `VITE_API_BASE_URL_PROD`: Prod API URL
   - `AZURE_STATIC_WEB_APPS_API_TOKEN_DEV`: Dev token (secret)
   - `AZURE_STATIC_WEB_APPS_API_TOKEN_PROD`: Prod token (secret)

#### reportscheduler-terraform

1. Create another variable group
2. Name: `reportscheduler-terraform`
3. Add variables:
   - `ARM_CLIENT_ID`: Dev service principal client ID (secret)
   - `ARM_CLIENT_SECRET`: Dev service principal secret (secret)
   - `ARM_CLIENT_ID_PROD`: Prod service principal client ID (secret)
   - `ARM_CLIENT_SECRET_PROD`: Prod service principal secret (secret)
   - `ARM_SUBSCRIPTION_ID`: Azure subscription ID
   - `ARM_TENANT_ID`: Azure tenant ID
   - `AZURE_TENANT_ID`: Same as ARM_TENANT_ID

### 4. Create Environments

1. Go to Pipelines → Environments
2. Create environments:
   - `development`
   - `production`
3. For production, add approvals:
   - Click on environment → 3-dot menu → Approvals and checks
   - Add "Approvals" → Select approvers

### 5. Create Pipelines

#### Backend Pipeline

1. Go to Pipelines → New pipeline
2. Select "Azure Repos Git" (or your repo location)
3. Select your repository
4. Choose "Existing Azure Pipelines YAML file"
5. Select `/pipelines/azure-pipelines-backend.yml`
6. Save and run

#### Frontend Pipeline

1. Repeat steps above
2. Select `/pipelines/azure-pipelines-frontend.yml`

#### Infrastructure Pipeline

1. Repeat steps above
2. Select `/pipelines/azure-pipelines-infrastructure.yml`

### 6. Configure Branch Policies

1. Go to Repos → Branches
2. Click on `main` branch → Branch policies
3. Enable:
   - Require minimum number of reviewers: 1
   - Check for linked work items
   - Check for comment resolution
   - Build validation: Add all three pipelines

4. Repeat for `develop` branch

## Pipeline Triggers

### Backend Pipeline
- **Trigger**: Pushes to `main` or `develop` affecting `backend/**`
- **PR**: PRs to `main` or `develop` affecting `backend/**`

### Frontend Pipeline
- **Trigger**: Pushes to `main` or `develop` affecting `frontend/**`
- **PR**: PRs to `main` or `develop` affecting `frontend/**`

### Infrastructure Pipeline
- **Trigger**: Pushes to `main` or `develop` affecting `infrastructure/**`
- **PR**: PRs to `main` or `develop` affecting `infrastructure/**`

## Running Pipelines

### Manual Run

1. Go to Pipelines
2. Select the pipeline
3. Click "Run pipeline"
4. Select branch
5. Click "Run"

### Automatic Triggers

Pipelines run automatically on:
- Push to `main` → Production deployment
- Push to `develop` → Development deployment
- Pull request → Test and validation only

## Monitoring

### Pipeline Runs

1. Go to Pipelines
2. Click on pipeline name
3. View recent runs
4. Click on run for detailed logs

### Build Status

Add badges to README.md:

```markdown
[![Backend Build](https://dev.azure.com/{org}/{project}/_apis/build/status/backend-pipeline)](https://dev.azure.com/{org}/{project}/_build)
[![Frontend Build](https://dev.azure.com/{org}/{project}/_apis/build/status/frontend-pipeline)](https://dev.azure.com/{org}/{project}/_build)
```

## Troubleshooting

### Service Connection Failures

**Issue**: Pipeline fails with "Service connection not found"

**Solution**:
1. Verify service connection name matches YAML
2. Check service connection permissions
3. Ensure service connection is authorized for pipeline

### Terraform State Lock

**Issue**: "Error acquiring state lock"

**Solution**:
```bash
# Force unlock (use with caution)
az storage blob delete \
  --account-name sttfstatereportscheduler \
  --container-name tfstate \
  --name dev.tfstate.lock
```

### Container App Update Failures

**Issue**: Container app update fails with image not found

**Solution**:
1. Verify image exists in ACR: `az acr repository show-tags --name crreportscheduler --repository reportscheduler-api`
2. Check service connection has ACR pull permissions
3. Verify image tag in pipeline variables

### Static Web App Deployment Failures

**Issue**: Frontend deployment fails with token error

**Solution**:
1. Get new deployment token from Azure Portal
2. Update variable group with new token
3. Ensure token is marked as secret

## Best Practices

1. **Use variable groups** for shared configuration
2. **Enable branch policies** to prevent direct pushes
3. **Use environments** for deployment approvals
4. **Monitor pipeline runs** regularly
5. **Keep service connections secure** with least privilege
6. **Use service principal authentication** for Azure
7. **Tag successful deployments** for rollback capability
8. **Enable retention policies** for artifacts
9. **Use YAML pipelines** instead of classic UI
10. **Document custom variables** in README

## Migration from GitHub Actions

If migrating from GitHub Actions:

1. Create Azure DevOps project
2. Import repository or connect to GitHub
3. Configure service connections (equivalent to GitHub secrets)
4. Create variable groups
5. Set up pipelines using YAML files
6. Configure branch policies
7. Test pipelines on feature branch
8. Enable automatic triggers

## Cost Considerations

Azure DevOps pricing:
- **Free tier**: 1 Microsoft-hosted parallel job (1800 minutes/month)
- **Additional jobs**: ~$40/month per parallel job
- **Self-hosted agents**: Free (infrastructure costs only)

## Advanced Features

### Multi-stage Approvals

Add manual approval between stages:

```yaml
- stage: DeployProd
  dependsOn: Build
  jobs:
    - deployment: DeployProdJob
      environment: 'production'  # Requires manual approval
```

### Conditional Deployments

Deploy only on specific conditions:

```yaml
condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
```

### Parallel Jobs

Run jobs in parallel:

```yaml
jobs:
  - job: TestBackend
    # ...
  - job: TestFrontend
    dependsOn: []  # No dependency, runs in parallel
    # ...
```

### Custom Tasks

Create custom tasks for repetitive operations:

```yaml
- template: templates/deploy-containerapp.yml
  parameters:
    appName: 'ca-reportscheduler-api-dev'
    resourceGroup: 'rg-reportscheduler-dev'
```

## Support

For issues or questions:
1. Check Azure DevOps documentation
2. Review pipeline logs
3. Check service connection status
4. Verify variable group values
5. Contact Azure DevOps support
