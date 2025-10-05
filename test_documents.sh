#!/bin/bash
# Test Documents Tab Functionality

echo "🧪 Testing Documents Tab Functionality"
echo "====================================="

# Check if server is running
echo "1. Checking if API server is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ API server is running"
else
    echo "   ❌ API server is NOT running"
    echo "   💡 Starting API server..."
    cd /Users/mmultra21/Documents/retro21_finance
    source .venv/bin/activate 2>/dev/null || echo "   (no virtual environment found)"
    python -m personal-finance.api.main &
    SERVER_PID=$!
    echo "   🚀 API server started with PID: $SERVER_PID"
    sleep 3
fi

# Test document endpoints
echo "2. Testing document endpoints..."

# Test documents list endpoint
echo "   Testing GET /documents..."
if curl -s http://localhost:8000/documents | grep -q '"documents"'; then
    echo "   ✅ Documents list endpoint working"
else
    echo "   ❌ Documents list endpoint failed"
fi

# Test document upload endpoint (without file)
echo "   Testing POST /documents/upload (metadata only)..."
if curl -s -X POST http://localhost:8000/documents/upload | grep -q "Field required"; then
    echo "   ✅ Upload endpoint responding (requires file)"
else
    echo "   ❌ Upload endpoint not responding"
fi

# Test document ask endpoint
echo "   Testing POST /documents/ask..."
RESPONSE=$(curl -s -X POST http://localhost:8000/documents/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Test question"}')

if echo "$RESPONSE" | grep -q '"success"'; then
    echo "   ✅ Document ask endpoint working"
else
    echo "   ❌ Document ask endpoint failed"
fi

# Test frontend files
echo "3. Testing frontend file accessibility..."
for file in "app.js" "documents.js" "chat.js" "manage.js"; do
    if curl -s -I "http://localhost:8000/static/js/$file" | head -1 | grep -q "200"; then
        echo "   ✅ $file accessible"
    else
        echo "   ❌ $file not accessible"
    fi
done

# Test main page
echo "4. Testing main page..."
if curl -s http://localhost:8000/ | grep -q "Personal Finance Dashboard"; then
    echo "   ✅ Main page loading"
else
    echo "   ❌ Main page not loading"
fi

echo ""
echo "🌐 Open your browser and go to: http://localhost:8000"
echo "📋 Then:"
echo "   1. Click on the 'Documents' tab"
echo "   2. Try uploading a small text or PDF file"
echo "   3. Check browser DevTools console for any errors"
echo "   4. Try asking a question in the Q&A section"
echo ""
echo "🔧 If issues persist:"
echo "   - Check browser DevTools → Console for JavaScript errors"
echo "   - Check DevTools → Network for failed API calls"
echo "   - Run: tail -f logs/api_server.log (if logging is configured)"