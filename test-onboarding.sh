#!/bin/bash

# Test onboarding flow for a new user
echo "Testing onboarding flow..."

# 1. Register new user
echo "1. Registering new user..."
REGISTER_RESPONSE=$(curl -s -X POST http://10.0.27.159:8000/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "onboard-test@example.com", "username": "onboardtest", "password": "TestPass123!", "full_name": "Onboard Test"}')

echo "Registration response: $REGISTER_RESPONSE"

# 2. Login to get token
echo "2. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST http://10.0.27.159:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email_or_username": "onboardtest", "password": "TestPass123!"}')

echo "Login response: $LOGIN_RESPONSE"

# Extract token (basic extraction, assumes no errors)
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
    echo "3. Token obtained: ${TOKEN:0:50}..."
    
    # 3. Check onboarding status
    echo "4. Checking onboarding status..."
    ONBOARDING_STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
        http://10.0.27.159:8000/onboarding/status)
    
    echo "Onboarding status: $ONBOARDING_STATUS"
    
    # 4. Check if user object includes onboarding status
    echo "5. Checking user info..."
    USER_INFO=$(curl -s -H "Authorization: Bearer $TOKEN" \
        http://10.0.27.159:8000/auth/me)
    
    echo "User info: $USER_INFO"
    
else
    echo "Failed to get token"
fi