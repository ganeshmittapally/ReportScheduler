# Terraform Infrastructure Setup Guide

## What Was Created

A complete Terraform infrastructure-as-code setup for both backend and frontend:

### Modules Structure
```
modules/
├── network/           # VNet, subnets, NSGs
├── monitoring/        # App Insights, Log Analytics, alerts
├── keyvault/         # Azure Key Vault for secrets management
├── database/         # PostgreSQL Flexible Server with HA
├── cache/            # Redis Cache
├── storage/          # Blob Storage with lifecycle policies
├── messaging/        # Service Bus queues
└── compute/
    ├── backend/      # Container Apps (API + Worker)
    └── frontend/     # Static Web App
```

### Environment Configurations
- `environments/dev/` - Development environment
- `environments/prod/` - Production environment (can add staging similarly)

## Key Features

### 1. Secrets Management with Azure Key Vault
- Centralized secret storage
- Automatic secret rotation support
- RBAC-based access control
- Private endpoint for production
- Secrets automatically injected into Container Apps

### 2. Backend Infrastructure
- **Container Apps**: Auto-scaling API and Celery workers
- **PostgreSQL**: Managed database with automated backups
- **Redis**: Caching and message broker
- **Service Bus**: Reliable message queuing
- **Blob Storage**: Artifact storage with auto-delete policies

### 3. Frontend Infrastructure
- **Static Web App**: CDN-backed Vue.js hosting
- Free tier for dev, Standard for prod
- Automatic HTTPS
- Custom domain support (configurable)

### 4. Monitoring & Observability
- Application Insights for telemetry
- Log Analytics for centralized logs
- Metric alerts for proactive monitoring
- Action groups for notifications

### 5. Security
- Network isolation with VNet
- Private endpoints for sensitive services
- TLS 1.2+ enforcement
- Managed identities for authentication
- Geo-redundant backups (prod)

## Quick Start

1. **Prerequisites**
   ```powershell
   # Install if needed
   choco install terraform azure-cli pwsh
   
   # Login
   az login
   ```

2. **Create Terraform Backend Storage**
   ```powershell
   az group create --name rg-terraform-state --location eastus
   az storage account create --name sttfstatereportscheduler --resource-group rg-terraform-state --location eastus --sku Standard_LRS
   az storage container create --name tfstate --account-name sttfstatereportscheduler
   ```

3. **Configure Environment**
   ```powershell
   cd environments/dev
   cp terraform.tfvars.example terraform.tfvars
   
   # Edit terraform.tfvars:
   # - Set tenant_id (from: az account show --query tenantId -o tsv)
   # - Update container image URLs after building
   ```

4. **Deploy**
   ```powershell
   cd ../..
   .\deploy.ps1 -Environment dev -Action init
   .\deploy.ps1 -Environment dev -Action plan
   .\deploy.ps1 -Environment dev -Action apply
   ```

5. **Get Outputs**
   ```powershell
   .\deploy.ps1 -Environment dev -Action output
   ```

## Configuration Steps

### Step 1: Set Tenant ID
```powershell
# Get your tenant ID
az account show --query tenantId -o tsv

# Add to environments/dev/terraform.tfvars
tenant_id = "your-tenant-id-here"
```

### Step 2: Build and Push Container Images

Before deploying, build your Docker images:

```powershell
# Build backend API
cd backend
docker build -f Dockerfile -t yourregistry.azurecr.io/reportscheduler-api:dev .

# Build backend worker
docker build -f Dockerfile.worker -t yourregistry.azurecr.io/reportscheduler-worker:dev .

# Login to ACR
az acr login --name yourregistry

# Push images
docker push yourregistry.azurecr.io/reportscheduler-api:dev
docker push yourregistry.azurecr.io/reportscheduler-worker:dev

# Update terraform.tfvars with image URLs
```

### Step 3: Configure Secrets After Deployment

Some secrets need manual configuration:

```powershell
# Get Key Vault name from outputs
$KV_NAME = (terraform output -raw key_vault_name)

# Set Azure Communication Services connection string
az keyvault secret set `
  --vault-name $KV_NAME `
  --name acs-connection-string `
  --value "your-acs-connection-string"
```

### Step 4: Deploy Frontend

After backend is deployed:

```powershell
# Get Static Web App deployment token
$DEPLOYMENT_TOKEN = (terraform output -raw static_web_app_deployment_token)

# Build frontend
cd frontend
npm run build

# Deploy to Static Web App (via GitHub Actions or Azure CLI)
# Configure DEPLOYMENT_TOKEN as GitHub secret for CI/CD
```

## Environment Differences

### Development
- Minimal resources (Basic/Standard tiers)
- Single region
- No high availability
- 7-30 day retention
- ~$100-200/month

### Production
- Premium tiers
- Zone-redundant HA
- Geo-redundant backups
- 35-90 day retention
- Auto-scaling enabled
- Private endpoints
- ~$800-1500/month

## Cost Breakdown (Approximate)

### Dev Environment (~$150/month)
- PostgreSQL Basic: $25
- Redis Basic: $15
- Container Apps: $50
- Storage: $5
- Service Bus: $10
- Static Web App: Free
- Monitoring: $25
- Networking: $20

### Prod Environment (~$1200/month)
- PostgreSQL Premium: $400
- Redis Premium: $150
- Container Apps: $300
- Storage GRS: $30
- Service Bus Premium: $150
- Static Web App Standard: $10
- Monitoring: $100
- Networking: $60

## Maintenance

### Updating Infrastructure

```powershell
# Make changes to .tf files
# Test in dev first
.\deploy.ps1 -Environment dev -Action plan
.\deploy.ps1 -Environment dev -Action apply

# Then promote to prod
.\deploy.ps1 -Environment prod -Action plan
.\deploy.ps1 -Environment prod -Action apply
```

### Backing Up State

```powershell
# State is automatically backed up in Azure Storage
# To download local copy:
cd environments/dev
terraform state pull > backup.tfstate
```

### Disaster Recovery

Production setup includes:
- Geo-redundant storage
- PostgreSQL daily backups (35 days)
- Key Vault soft-delete (90 days)
- Container logs in Log Analytics

## Next Steps

1. Set up CI/CD pipelines (GitHub Actions / Azure DevOps)
2. Configure custom domains for frontend
3. Set up Azure AD authentication
4. Configure budget alerts
5. Set up staging environment
6. Implement multi-region deployment

## Support

See the main README.md in infrastructure/ for detailed documentation.
