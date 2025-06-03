#!/bin/bash

# End-to-end testing script for AI Content Generation System

echo "Starting end-to-end tests for AI Content Generation System..."

# Check if backend is running
echo "Checking backend status..."
if ! curl -s http://localhost:5000/api/health > /dev/null; then
  echo "Backend is not running. Starting backend..."
  cd /home/ubuntu/ai-content-system/backend/ai_content_backend
  source venv/bin/activate
  python -m src.main &
  BACKEND_PID=$!
  echo "Backend started with PID: $BACKEND_PID"
  sleep 5  # Wait for backend to initialize
else
  echo "Backend is already running."
fi

# Check if frontend is running
echo "Checking frontend status..."
if ! curl -s http://localhost:3000 > /dev/null; then
  echo "Frontend is not running. Starting frontend..."
  cd /home/ubuntu/ai-content-system/frontend/ai_content_frontend
  pnpm run dev &
  FRONTEND_PID=$!
  echo "Frontend started with PID: $FRONTEND_PID"
  sleep 5  # Wait for frontend to initialize
else
  echo "Frontend is already running."
fi

# Test user registration and authentication
echo "Testing user registration and authentication..."
REGISTER_RESPONSE=$(curl -s -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"password123"}')

if echo "$REGISTER_RESPONSE" | grep -q "User registered successfully"; then
  echo "✅ User registration successful"
else
  echo "❌ User registration failed"
  echo "$REGISTER_RESPONSE"
fi

LOGIN_RESPONSE=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username_or_email":"testuser","password":"password123"}')

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -n "$ACCESS_TOKEN" ]; then
  echo "✅ User login successful"
else
  echo "❌ User login failed"
  echo "$LOGIN_RESPONSE"
fi

# Test AI provider management
echo "Testing AI provider management..."
PROVIDER_RESPONSE=$(curl -s -X GET http://localhost:5000/api/providers \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$PROVIDER_RESPONSE" | grep -q "providers"; then
  echo "✅ Provider listing successful"
else
  echo "❌ Provider listing failed"
  echo "$PROVIDER_RESPONSE"
fi

# Test task creation
echo "Testing task creation..."
TASK_RESPONSE=$(curl -s -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"title":"Test Task","task_type":"image","priority":3,"description_data":{"prompt":"A test image of a cat"}}')

TASK_ID=$(echo "$TASK_RESPONSE" | grep -o '"id":"[^"]*' | cut -d'"' -f4)

if [ -n "$TASK_ID" ]; then
  echo "✅ Task creation successful"
else
  echo "❌ Task creation failed"
  echo "$TASK_RESPONSE"
fi

# Test task retrieval
echo "Testing task retrieval..."
TASK_GET_RESPONSE=$(curl -s -X GET "http://localhost:5000/api/tasks/$TASK_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$TASK_GET_RESPONSE" | grep -q "$TASK_ID"; then
  echo "✅ Task retrieval successful"
else
  echo "❌ Task retrieval failed"
  echo "$TASK_GET_RESPONSE"
fi

# Test task cancellation
echo "Testing task cancellation..."
CANCEL_RESPONSE=$(curl -s -X POST "http://localhost:5000/api/tasks/$TASK_ID/cancel" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$CANCEL_RESPONSE" | grep -q "cancelled"; then
  echo "✅ Task cancellation successful"
else
  echo "❌ Task cancellation failed"
  echo "$CANCEL_RESPONSE"
fi

# Test token management
echo "Testing token management..."
TOKEN_RESET_RESPONSE=$(curl -s -X POST http://localhost:5000/api/tokens/reset \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$TOKEN_RESET_RESPONSE" | grep -q "reset"; then
  echo "✅ Token reset successful"
else
  echo "❌ Token reset failed"
  echo "$TOKEN_RESET_RESPONSE"
fi

# Clean up
echo "Cleaning up test resources..."
if [ -n "$BACKEND_PID" ]; then
  kill $BACKEND_PID
  echo "Backend stopped."
fi

if [ -n "$FRONTEND_PID" ]; then
  kill $FRONTEND_PID
  echo "Frontend stopped."
fi

echo "End-to-end tests completed."
