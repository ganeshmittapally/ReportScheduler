#!/usr/bin/env pwsh
# Terraform deployment script for ReportScheduler infrastructure

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('init', 'plan', 'apply', 'destroy', 'output')]
    [string]$Action = 'plan',
    
    [Parameter(Mandatory=$false)]
    [switch]$AutoApprove
)

$ErrorActionPreference = "Stop"

# Configuration
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$ENV_DIR = Join-Path $SCRIPT_DIR "environments" $Environment

Write-Host "=== ReportScheduler Terraform Deployment ===" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Action: $Action" -ForegroundColor Yellow
Write-Host ""

# Check if environment directory exists
if (-not (Test-Path $ENV_DIR)) {
    Write-Host "Error: Environment directory not found: $ENV_DIR" -ForegroundColor Red
    exit 1
}

# Check if terraform.tfvars exists
$TFVARS_FILE = Join-Path $ENV_DIR "terraform.tfvars"
if (-not (Test-Path $TFVARS_FILE)) {
    Write-Host "Warning: terraform.tfvars not found" -ForegroundColor Yellow
    Write-Host "Please create it from terraform.tfvars.example" -ForegroundColor Yellow
    Write-Host ""
}

# Check Azure CLI login
Write-Host "Checking Azure CLI authentication..." -ForegroundColor Cyan
try {
    $account = az account show | ConvertFrom-Json
    Write-Host "✓ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "✓ Subscription: $($account.name)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "Error: Not logged in to Azure CLI" -ForegroundColor Red
    Write-Host "Run: az login" -ForegroundColor Yellow
    exit 1
}

# Navigate to environment directory
Push-Location $ENV_DIR

try {
    switch ($Action) {
        'init' {
            Write-Host "Running terraform init..." -ForegroundColor Cyan
            terraform init -upgrade
        }
        'plan' {
            Write-Host "Running terraform plan..." -ForegroundColor Cyan
            terraform plan -out=tfplan
        }
        'apply' {
            Write-Host "Running terraform apply..." -ForegroundColor Cyan
            if ($AutoApprove) {
                terraform apply -auto-approve
            } else {
                if (Test-Path "tfplan") {
                    terraform apply tfplan
                } else {
                    terraform apply
                }
            }
        }
        'destroy' {
            Write-Host "Running terraform destroy..." -ForegroundColor Red
            if ($Environment -eq 'prod') {
                Write-Host "WARNING: You are about to destroy PRODUCTION infrastructure!" -ForegroundColor Red
                $confirmation = Read-Host "Type 'destroy-prod' to confirm"
                if ($confirmation -ne 'destroy-prod') {
                    Write-Host "Destroy cancelled" -ForegroundColor Yellow
                    exit 0
                }
            }
            if ($AutoApprove) {
                terraform destroy -auto-approve
            } else {
                terraform destroy
            }
        }
        'output' {
            Write-Host "Terraform outputs:" -ForegroundColor Cyan
            terraform output
        }
    }
    
    Write-Host ""
    Write-Host "✓ Terraform $Action completed successfully!" -ForegroundColor Green
    
} catch {
    Write-Host ""
    Write-Host "✗ Terraform $Action failed!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
} finally {
    Pop-Location
}
