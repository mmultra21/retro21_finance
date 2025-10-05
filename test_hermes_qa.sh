#!/bin/bash
# Test Document Q&A with Live Hermes3

echo "🧪 Testing Document Q&A with Live Hermes3"
echo "========================================"

# Check if Hermes3 is running
echo "1. Checking Hermes3 LLM server..."
if curl -s http://127.0.0.1:11434/health > /dev/null 2>&1; then
    echo "   ✅ Hermes3 server is running"
else
    echo "   ❌ Hermes3 server is NOT running"
    echo "   💡 Starting Hermes3..."
    if [ -f "./run_hermes3.sh" ]; then
        ./run_hermes3.sh &
        echo "   🚀 Hermes3 starting... (this may take a moment)"
        echo "   ⏳ Waiting 10 seconds for startup..."
        sleep 10
    else
        echo "   ❌ run_hermes3.sh not found. Please start Hermes3 manually:"
        echo "      ./run_hermes3.sh"
        exit 1
    fi
fi

# Check API server
echo "2. Checking API server..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ API server is running"
else
    echo "   ❌ API server is NOT running"
    echo "   💡 Please start the API server:"
    echo "      python -m personal-finance.api.main"
    exit 1
fi

# Test document Q&A endpoint with a sample question
echo "3. Testing document Q&A with Hermes3..."

SAMPLE_QUESTION="What is my total income this year?"

echo "   Asking: '$SAMPLE_QUESTION'"

RESPONSE=$(curl -s -X POST http://localhost:8000/documents/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"$SAMPLE_QUESTION\"}")

echo "   Response received:"
echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"

# Check if the response indicates Hermes3 is working
if echo "$RESPONSE" | grep -q '"success": true'; then
    echo "   ✅ Document Q&A endpoint working"
    
    if echo "$RESPONSE" | grep -q "LLM server is not responding"; then
        echo "   ⚠️  Hermes3 integration issue detected"
    else
        echo "   ✅ Hermes3 integration appears to be working"
    fi
else
    echo "   ❌ Document Q&A endpoint failed"
fi

# Test with a simple text document upload
echo "4. Testing document upload..."

# Create a test financial document
cat > /tmp/test_financial_doc.txt << 'EOF'
Financial Summary for John Doe - 2024

INCOME:
- Salary: $75,000
- Freelance work: $12,000
- Investment dividends: $2,500
Total Income: $89,500

EXPENSES:
- Housing: $24,000 (rent and utilities)
- Food: $8,000
- Transportation: $6,000
- Healthcare: $3,500
- Entertainment: $2,500
Total Expenses: $44,000

NET SAVINGS: $45,500
Savings Rate: 50.8%

INVESTMENTS:
- 401k contribution: $19,500
- Roth IRA contribution: $6,000
- Taxable brokerage: $20,000

TAX INFORMATION:
- Federal income tax paid: $15,000
- State income tax paid: $4,500
- Total tax rate: 21.8%
EOF

echo "   Uploading test document..."
UPLOAD_RESPONSE=$(curl -s -X POST http://localhost:8000/documents/upload \
  -F "file=@/tmp/test_financial_doc.txt" \
  -F "category=test")

if echo "$UPLOAD_RESPONSE" | grep -q '"success": true'; then
    echo "   ✅ Document upload successful"
    
    # Extract document ID for testing
    DOC_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_id', ''))" 2>/dev/null)
    
    if [ ! -z "$DOC_ID" ]; then
        echo "   📄 Document ID: $DOC_ID"
        
        # Test Q&A with the uploaded document
        echo "5. Testing Q&A with uploaded document..."
        
        SPECIFIC_QUESTION="What was my total income and savings rate?"
        echo "   Asking: '$SPECIFIC_QUESTION'"
        
        QA_RESPONSE=$(curl -s -X POST http://localhost:8000/documents/ask \
          -H "Content-Type: application/json" \
          -d "{\"question\": \"$SPECIFIC_QUESTION\"}")
        
        echo "   Response:"
        echo "$QA_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$QA_RESPONSE"
        
        if echo "$QA_RESPONSE" | grep -q "89,500\|45,500\|50.8"; then
            echo "   🎉 SUCCESS! Hermes3 found specific information from the document"
        else
            echo "   ⚠️  Document Q&A working but may need tuning"
        fi
    fi
else
    echo "   ❌ Document upload failed"
    echo "$UPLOAD_RESPONSE"
fi

# Clean up test file
rm -f /tmp/test_financial_doc.txt

echo ""
echo "📋 Summary:"
echo "   - Hermes3 server: $(curl -s http://127.0.0.1:11434/health > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Not running")"
echo "   - API server: $(curl -s http://localhost:8000/health > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Not running")"
echo "   - Document Q&A: Test completed (check output above)"
echo ""
echo "🌐 Open your browser to test manually:"
echo "   http://localhost:8000"
echo "   → Go to Documents tab"
echo "   → Upload a financial document"
echo "   → Ask questions about it"