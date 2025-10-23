#!/bin/bash
# Frontend Deployment Script for S3 + CloudFront
# This script builds and deploys the Next.js frontend to AWS

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
TERRAFORM_DIR="$PROJECT_ROOT/deployment/aws"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        print_error "$1 is required but not installed."
        exit 1
    fi
}

# Function to get Terraform output
get_terraform_output() {
    local output_name=$1
    cd "$TERRAFORM_DIR"
    terraform output -raw "$output_name" 2>/dev/null || echo ""
}

# Check required tools
print_status "Checking required tools..."
check_command "node"
check_command "npm"
check_command "terraform"
check_command "aws"

# Check if we're in the right directory
if [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
    print_error "Frontend directory not found at $FRONTEND_DIR"
    exit 1
fi

if [[ ! -f "$TERRAFORM_DIR/main.tf" ]]; then
    print_error "Terraform directory not found at $TERRAFORM_DIR"
    exit 1
fi

# Get deployment info from Terraform
print_status "Getting deployment configuration from Terraform..."
S3_BUCKET=$(get_terraform_output "s3_bucket_name")
CLOUDFRONT_DISTRIBUTION_ID=$(get_terraform_output "cloudfront_distribution_id")
CLOUDFRONT_DOMAIN=$(get_terraform_output "cloudfront_domain_name")
BACKEND_URL=$(get_terraform_output "app_url")

if [[ -z "$S3_BUCKET" ]]; then
    print_error "Could not get S3 bucket name from Terraform. Make sure infrastructure is deployed."
    exit 1
fi

if [[ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]]; then
    print_error "Could not get CloudFront distribution ID from Terraform."
    exit 1
fi

print_status "Deployment Configuration:"
echo "  S3 Bucket: $S3_BUCKET"
echo "  CloudFront Distribution: $CLOUDFRONT_DISTRIBUTION_ID"
echo "  CloudFront Domain: $CLOUDFRONT_DOMAIN"
echo "  Backend URL: $BACKEND_URL"
echo

# Check AWS credentials
print_status "Checking AWS credentials..."
if ! aws sts get-caller-identity &>/dev/null; then
    print_error "AWS credentials not configured. Run 'aws configure' or set environment variables."
    exit 1
fi

# Navigate to frontend directory
cd "$FRONTEND_DIR"

# Install dependencies
print_status "Installing frontend dependencies..."
npm ci

# Create production environment file
print_status "Creating production environment configuration..."
cat > .env.production << EOF
NEXT_PUBLIC_API_URL=$BACKEND_URL
NEXT_PUBLIC_APP_ENV=production
NEXT_PUBLIC_SPA_MODE=true
NEXT_PUBLIC_VERSION=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
EOF

# Build the application
print_status "Building Next.js application for production..."
npm run build

# Check if build output exists
if [[ ! -d "out" ]]; then
    print_error "Build output directory 'out' not found. Make sure Next.js is configured for static export."
    print_warning "Ensure next.config.mjs has: output: 'export'"
    exit 1
fi

# Sync files to S3
print_status "Uploading files to S3 bucket: $S3_BUCKET"
aws s3 sync out/ s3://$S3_BUCKET/ \
    --delete \
    --exclude "*.DS_Store" \
    --cache-control "public, max-age=31536000, immutable" \
    --metadata-directive REPLACE

# Set specific cache control for HTML files
print_status "Setting cache control for HTML files..."
aws s3 cp s3://$S3_BUCKET/ s3://$S3_BUCKET/ \
    --recursive \
    --exclude "*" \
    --include "*.html" \
    --cache-control "public, max-age=300" \
    --metadata-directive REPLACE

# Invalidate CloudFront cache
print_status "Creating CloudFront invalidation..."
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

print_status "CloudFront invalidation created: $INVALIDATION_ID"
print_status "Waiting for invalidation to complete..."

# Wait for invalidation (optional - can be skipped for faster deployments)
if [[ "${WAIT_FOR_INVALIDATION:-false}" == "true" ]]; then
    aws cloudfront wait invalidation-completed \
        --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
        --id $INVALIDATION_ID
    print_status "CloudFront invalidation completed!"
else
    print_warning "Not waiting for invalidation to complete (set WAIT_FOR_INVALIDATION=true to wait)"
fi

# Cleanup
rm -f .env.production

# Success message
print_status "Frontend deployment completed successfully!"
echo
echo "🚀 Your application is now live at:"
echo "   CloudFront URL: https://$CLOUDFRONT_DOMAIN"

# If custom domain is configured
CUSTOM_DOMAIN=$(get_terraform_output "frontend_url")
if [[ "$CUSTOM_DOMAIN" != "https://$CLOUDFRONT_DOMAIN" ]]; then
    echo "   Custom Domain:  $CUSTOM_DOMAIN"
fi

echo
echo "📊 Deployment Summary:"
echo "   - Files uploaded to S3: $S3_BUCKET"
echo "   - CloudFront invalidation: $INVALIDATION_ID"
echo "   - Backend API: $BACKEND_URL"
echo
print_status "Deployment complete! 🎉"
