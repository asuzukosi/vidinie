#!/bin/bash

# Stripe Webhook Event Trigger Script
# This script triggers common Stripe webhook events for testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Stripe Webhook Event Trigger${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Stripe CLI is installed
if ! command -v stripe &> /dev/null; then
    echo -e "${RED}Error: Stripe CLI is not installed.${NC}"
    echo -e "${YELLOW}Install it from: https://stripe.com/docs/stripe-cli${NC}"
    exit 1
fi

# Function to trigger an event
trigger_event() {
    local event_name=$1
    local description=$2
    
    echo -e "${YELLOW}Triggering: ${description}${NC}"
    echo -e "${BLUE}Event: ${event_name}${NC}"
    
    if stripe trigger "$event_name" 2>/dev/null; then
        echo -e "${GREEN}✓ Event triggered successfully${NC}"
    else
        echo -e "${RED}✗ Failed to trigger event${NC}"
    fi
    echo ""
}

# Menu
echo -e "${GREEN}Select an event to trigger:${NC}"
echo ""
echo "1) customer.subscription.created"
echo "2) customer.subscription.updated"
echo "3) customer.subscription.deleted"
echo "4) checkout.session.completed"
echo "5) invoice.payment_succeeded"
echo "6) invoice.payment_failed"
echo "7) customer.created"
echo "8) payment_intent.succeeded"
echo "9) All subscription events (1-3)"
echo "0) Exit"
echo ""

read -p "Enter your choice [0-9]: " choice

case $choice in
    1)
        trigger_event "customer.subscription.created" "Subscription Created"
        ;;
    2)
        trigger_event "customer.subscription.updated" "Subscription Updated"
        ;;
    3)
        trigger_event "customer.subscription.deleted" "Subscription Deleted"
        ;;
    4)
        trigger_event "checkout.session.completed" "Checkout Session Completed"
        ;;
    5)
        trigger_event "invoice.payment_succeeded" "Invoice Payment Succeeded"
        ;;
    6)
        trigger_event "invoice.payment_failed" "Invoice Payment Failed"
        ;;
    7)
        trigger_event "customer.created" "Customer Created"
        ;;
    8)
        trigger_event "payment_intent.succeeded" "Payment Intent Succeeded"
        ;;
    9)
        echo -e "${BLUE}Triggering all subscription events...${NC}"
        echo ""
        trigger_event "customer.subscription.created" "Subscription Created"
        sleep 1
        trigger_event "customer.subscription.updated" "Subscription Updated"
        sleep 1
        trigger_event "customer.subscription.deleted" "Subscription Deleted"
        ;;
    0)
        echo -e "${YELLOW}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Done! Check your application logs and Stripe CLI output.${NC}"

