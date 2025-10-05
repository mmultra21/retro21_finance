#!/bin/bash
# JavaScript Function Debug Script
# Run this to check for common gotchas

echo "🔍 JavaScript Function Debugging Checklist"
echo "==========================================="

# 1. Check if server is running
echo "1. Checking API server status..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ API server is running on port 8000"
else
    echo "   ❌ API server is NOT running on port 8000"
    echo "   💡 Start with: cd /path/to/project && python -m personal-finance.api.main"
fi

# 2. Check static file serving
echo "2. Checking static file accessibility..."
for file in "app.js" "documents.js" "chat.js" "manage.js"; do
    if curl -s -I "http://localhost:8000/static/js/$file" | head -1 | grep -q "200"; then
        echo "   ✅ $file is accessible"
    else
        echo "   ❌ $file is NOT accessible (404 or server down)"
    fi
done

# 3. Check function definitions
echo "3. Checking function definitions in JS files..."
if grep -q "function clearDocChat" frontend/static/js/documents.js; then
    echo "   ✅ clearDocChat function is defined in documents.js"
else
    echo "   ❌ clearDocChat function NOT found in documents.js"
fi

if grep -q "function clearChat" frontend/static/js/chat.js; then
    echo "   ✅ clearChat function is defined in chat.js"
else
    echo "   ❌ clearChat function NOT found in chat.js"
fi

# 4. Check HTML onclick handlers
echo "4. Checking HTML onclick handlers..."
if grep -q 'onclick="clearDocChat()"' frontend/index.html; then
    echo "   ✅ clearDocChat onclick handler found in HTML"
else
    echo "   ❌ clearDocChat onclick handler NOT found in HTML"
fi

# 5. Check script loading order
echo "5. Checking script loading order..."
echo "   Script order in HTML:"
grep -n "<script.*src=" frontend/index.html | sed 's/^/   /'

# 6. Check for cache busting
echo "6. Checking cache busting..."
if grep -q "\.js?t=" frontend/index.html; then
    echo "   ✅ Cache busting parameters found"
else
    echo "   ⚠️  No cache busting - browsers might cache old JS"
fi

echo ""
echo "🔧 Quick Fixes:"
echo "- If server is down: Start FastAPI server"
echo "- If 404 on JS files: Check FastAPI static file mounting"
echo "- If function not found: Check JS file syntax and loading"
echo "- If still broken: Check browser DevTools Console for errors"
echo ""
echo "📱 Browser DevTools Checklist:"
echo "1. Open DevTools (F12)"
echo "2. Check Network tab for failed JS loads (red entries)"
echo "3. Check Console tab for JavaScript errors"
echo "4. Try: typeof clearDocChat (should return 'function')"
echo "5. Try: window.clearDocChat (should show function code)"