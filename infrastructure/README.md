# Report Scheduler Infrastructure

Terraform configuration for Azure infrastructure provisioning with integrated secrets management via Azure Key Vault.

## Quick Start

```powershell
# Using the deployment script (recommended)
.\deploy.ps1 -Environment dev -Action init
.\deploy.ps1 -Environment dev -Action plan
.\deploy.ps1 -Environment dev -Action apply

# Or manually
cd environments/dev
terraform init
terraform plan
terraform apply

# View outputs
.\deploy.ps1 -Environment dev -Action output
```

## Structure

```
infrastructure/
├── modules/
│   ├── network/          # VNet, subnets, NSGs, private endpoints
│   ├── compute/          # Container Apps, scale rules
│   ├── database/         # PostgreSQL Flexible Server, read replicas
│   ├── storage/          # Blob Storage, lifecycle policies
│   ├── messaging/        # Service Bus Premium (topics, subscriptions)
│   └── monitoring/       # Application Insights, Log Analytics
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── terraform.tfvars
│   │   └── backend.tf
│   ├── staging/
│   └── prod/
└── README.md
```

## Environments

### Development
- Minimal resources (B-series VMs, basic tiers)
- Single region (East US)
- Synthetic data
- Access: All engineers

### Staging
- Scaled-down production mirror
- Masked production data subset
- Multi-region (active-passive)
- Access: Engineers + QA

### Production
- Full scale (1000+ tenants, 300 concurrent workers)
- Multi-region active-active (East US, West Europe, Southeast Asia)
- Azure DDoS Protection Standard
- Traffic Manager for geo-routing
- Access: Limited (ops team + break-glass)

### Performance (Optional)
- On-demand large-scale load testing
- Synthetic high-volume data

## Architecture Overview

The infrastructure deploys a complete Azure solution:

### Backend Components
- **Container Apps**: Backend API and Celery workers with auto-scaling
- **PostgreSQL Flexible Server**: Primary database with zone-redundancy (prod)
- **Redis Cache**: Report caching and Celery broker
- **Service Bus**: Message queuing for async tasks
- **Blob Storage**: Report artifact storage with lifecycle policies

### Frontend Components
- **Static Web App**: Vue.js frontend with CDN and custom domain support

### Shared Services
- **Virtual Network**: Isolated networking with subnets
- **Key Vault**: Centralized secrets management
- **Application Insights**: Monitoring and telemetry
- **Log Analytics**: Centralized logging

## Prerequisites

- **Azure CLI** (`az login`) - [Install](https://docs.microsoft.com/cli/azure/install-azure-cli)
- **Terraform >= 1.5.0** - [Install](https://www.terraform.io/downloads)
- **PowerShell 7+** (for deployment script) - [Install](https://github.com/PowerShell/PowerShell)
- **Azure subscription** with Contributor role
- **Backend storage account** for Terraform state (see setup below)

## Initial Setup

### 1. Create Terraform State Storage

```powershell
# Login to Azure
az login

# Create resource group for Terraform state
az group create --name rg-terraform-state --location eastus

# Create storage account (must be globally unique)
az storage account create `
  --name sttfstatereportscheduler `
  --resource-group rg-terraform-state `
  --location eastus `
  --sku Standard_LRS `
  --encryption-services blob

# Create blob container
az storage container create `
  --name tfstate `
  --account-name sttfstatereportscheduler
```

### 2. Configure Environment Variables

Copy the example tfvars file and update with your values:

```powershell
cd environments/dev
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
# - tenant_id: Get from 'az account show'
# - api_image/worker_image: Your container registry images
```

### 3. Get Your Tenant ID

```powershell
az account show --query tenantId -o tsv
```

## Backend Configuration

Terraform remote state stored in Azure Storage:

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "sttfstatereportscheduler"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}
```

## Deployment Workflow

### Using Deployment Script (Recommended)

```powershell
# Initialize (first time only)
.\deploy.ps1 -Environment dev -Action init

# Plan changes
.\deploy.ps1 -Environment dev -Action plan

# Apply changes (interactive)
.\deploy.ps1 -Environment dev -Action apply

# Apply with auto-approve (use with caution)
.\deploy.ps1 -Environment dev -Action apply -AutoApprove

# View outputs
.\deploy.ps1 -Environment dev -Action output

# Destroy (requires confirmation for prod)
.\deploy.ps1 -Environment dev -Action destroy
```

### Manual Deployment

```powershell
cd environments/dev
terraform init
terraform plan -out=tfplan
terraform apply tfplan
terraform output
```

### CI/CD Pipeline

1. Make infrastructure changes in `modules/` or `environments/`
2. Create PR with `terraform plan` output
3. Review plan for unexpected changes
4. Merge PR
5. CI/CD pipeline runs `terraform apply` (manual approval for prod)

## Secrets Management

All sensitive values are stored in Azure Key Vault:

### Automatic Secret Creation

The Key Vault module creates placeholder secrets that are automatically populated during deployment:

- `postgres-admin-password`: PostgreSQL admin password (auto-generated)
- `redis-primary-key`: Redis access key (auto-populated)
- `storage-connection-string`: Blob Storage connection string
- `servicebus-connection-string`: Service Bus connection string
- `acs-connection-string`: Azure Communication Services (manual)

### Accessing Secrets

```powershell
# List all secrets
az keyvault secret list --vault-name kv-reportscheduler-dev

# Get specific secret
az keyvault secret show --vault-name kv-reportscheduler-dev --name postgres-admin-password

# Set custom secret
az keyvault secret set --vault-name kv-reportscheduler-dev --name acs-connection-string --value "YOUR_VALUE"
```

### Container App Secret References

Container Apps automatically inject secrets as environment variables using Key Vault references.

## Tagging Strategy

All resources tagged with:
- `environment`: dev/staging/prod
- `project`: reportscheduler
- `owner`: platform-team
- `cost_center`: engineering
- `terraform`: true

## Cost Monitoring

- Budget alerts configured per environment
- Cost analysis dashboards in Azure Portal
- Monthly cost review: `az consumption usage list`

## Security

- **Azure Key Vault**: Centralized secrets management with RBAC
- **Managed Identities**: Service-to-service authentication without credentials
- **Private Endpoints**: Database and Key Vault isolated in VNet (prod)
- **Network Security Groups**: Restrict inbound/outbound traffic
- **TLS 1.2+**: Enforced on all services
- **Soft Delete**: Enabled on Key Vault (90 days prod, 7 days dev)
- **Geo-redundant Backups**: PostgreSQL and Storage in production

## Configuration Reference

### Resource Naming Convention

```
<resource-type>-<project>-<component>-<environment>
Example: ca-reportscheduler-api-dev
```

### Environment-Specific Settings

| Resource | Dev | Prod |
|----------|-----|------|
| PostgreSQL SKU | B_Standard_B1ms | GP_Standard_D4s_v3 |
| PostgreSQL Storage | 32 GB | 128 GB |
| PostgreSQL HA | Disabled | ZoneRedundant |
| Redis SKU | Basic C0 | Premium P1 |
| Storage Replication | LRS | GRS |
| Service Bus SKU | Standard | Premium |
| API Replicas | 1-3 | 3-20 |
| Worker Replicas | 1-10 | 5-50 |
| Log Retention | 30 days | 90 days |
| Backup Retention | 7 days | 35 days |

## Troubleshooting

### Common Issues

**Error: Backend storage not found**
```powershell
# Create the backend storage manually first
az storage account create --name sttfstatereportscheduler --resource-group rg-terraform-state
```

**Error: Tenant ID not set**
```powershell
# Add to terraform.tfvars
tenant_id = "your-tenant-id-here"
```

**Error: Container image not found**
```powershell
# Build and push images first, then update terraform.tfvars
# api_image = "yourregistry.azurecr.io/reportscheduler-api:dev"
```

### Viewing Logs

```powershell
# Container App logs
az containerapp logs show --name ca-reportscheduler-api-dev --resource-group rg-reportscheduler-dev

# Application Insights query
az monitor app-insights query --app appi-reportscheduler-dev --analytics-query "requests | limit 10"
```

## Cost Optimization

- **Dev**: Use Basic/Standard tiers (~$100-200/month)
- **Prod**: Premium tiers with HA (~$800-1500/month)
- Enable auto-scaling to scale down during low usage
- Set lifecycle policies to auto-delete old blobs
- Use reserved instances for predictable workloads (20-30% savings)
