#!/bin/bash

# Stripe Webhook Testing Script
# This script forwards Stripe webhooks to your local development server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
WEBHOOK_URL="${WEBHOOK_URL:-localhost:3000/api/auth/stripe/webhook}"
PORT="${PORT:-3000}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stripe Webhook Testing${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}Webhook Endpoint:${NC} http://${WEBHOOK_URL}"
echo -e "${YELLOW}Port:${NC} ${PORT}"
echo ""

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo -e "${RED}Error: Stripe CLI is not installed.${NC}"
    echo -e "${YELLOW}Install it from: https://stripe.com/docs/stripe-cli${NC}"
    exit 1
fi

# Check if user is logged in to Stripe CLI
if ! stripe config --list &> /dev/null; then
    echo -e "${YELLOW}Warning: You may not be logged in to Stripe CLI.${NC}"
    echo -e "${YELLOW}Run 'stripe login' first if you encounter issues.${NC}"
    echo ""
fi

# Check if server is running
echo -e "${YELLOW}Checking if server is running...${NC}"
if curl -s -f -o /dev/null "http://localhost:${PORT}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Server is running on port ${PORT}${NC}"
else
    echo -e "${RED}✗ Server is not running on port ${PORT}${NC}"
    echo -e "${YELLOW}Please start your Next.js server first:${NC}"
    echo -e "${BLUE}   cd frontend && npm run dev${NC}"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
fi

echo ""
echo -e "${GREEN}Starting Stripe webhook listener...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}IMPORTANT:${NC}"
echo -e "1. Copy the webhook signing secret (whsec_...) shown below"
echo -e "2. Add it to your .env or .env.local file as: NEXT_PUBLIC_STRIPE_WEBHOOK_SECRET"
echo -e "3. Restart your development server after updating the secret"
echo -e "4. Watch your Next.js server console for webhook handler logs"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${YELLOW}The Stripe CLI will automatically forward webhooks to your local server.${NC}"
echo -e "${YELLOW}You don't need ngrok or any other tunneling service.${NC}"
echo ""

# Forward webhooks
stripe listen --forward-to "http://${WEBHOOK_URL}"
