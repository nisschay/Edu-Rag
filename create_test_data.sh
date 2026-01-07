#!/bin/bash

# Education RAG - Quick Test Script
# This creates sample data for testing the UI

echo "🚀 Education RAG - Creating Test Data"
echo "======================================"
echo ""

BASE_URL="http://localhost:8000/api/v1"
USER_ID=1

echo "Step 1: Creating user..."
curl -s -X POST "$BASE_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com"}' | jq '.'

echo ""
echo "Step 2: Creating subject 'Introduction to Algorithms'..."
SUBJECT=$(curl -s -X POST "$BASE_URL/subjects" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"name": "Introduction to Algorithms", "description": "Computer Science fundamentals"}')
SUBJECT_ID=$(echo $SUBJECT | jq -r '.id')
echo "Created subject ID: $SUBJECT_ID"

echo ""
echo "Step 3: Creating unit 'Sorting Algorithms'..."
UNIT=$(curl -s -X POST "$BASE_URL/subjects/$SUBJECT_ID/units" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"title": "Sorting Algorithms", "description": "Comparison and non-comparison based sorting"}')
UNIT_ID=$(echo $UNIT | jq -r '.id')
echo "Created unit ID: $UNIT_ID"

echo ""
echo "Step 4: Creating topic 'Quick Sort'..."
TOPIC=$(curl -s -X POST "$BASE_URL/subjects/$SUBJECT_ID/units/$UNIT_ID/topics" \
  -H "Content-Type: application/json" \
  -H "X-User-Id: $USER_ID" \
  -d '{"title": "Quick Sort"}')
TOPIC_ID=$(echo $TOPIC | jq -r '.id')
echo "Created topic ID: $TOPIC_ID"

echo ""
echo "Step 5: Creating sample content file..."
cat > /tmp/quicksort.txt << 'EOF'
Quick Sort Algorithm

Quick sort is a divide-and-conquer sorting algorithm. It works by selecting a 'pivot' element from the array and partitioning the other elements into two sub-arrays, according to whether they are less than or greater than the pivot.

Time Complexity:
- Best case: O(n log n)
- Average case: O(n log n)
- Worst case: O(n²)

Space Complexity: O(log n)

The algorithm consists of three main steps:
1. Choose a pivot element from the array
2. Partition the array around the pivot
3. Recursively apply quick sort to the sub-arrays

Example:
Given array: [3, 6, 8, 10, 1, 2, 1]
Choose pivot: 3
After partition: [2, 1, 1, 3, 6, 8, 10]
Recursively sort left and right sub-arrays

Quick sort is widely used because it's efficient and works in-place.
EOF

echo ""
echo "Step 6: Uploading sample file..."
curl -s -X POST "$BASE_URL/subjects/$SUBJECT_ID/units/$UNIT_ID/topics/$TOPIC_ID/files" \
  -H "X-User-Id: $USER_ID" \
  -F "file=@/tmp/quicksort.txt" | jq '.'

echo ""
echo "Step 7: Processing content (chunking)..."
curl -s -X POST "$BASE_URL/subjects/$SUBJECT_ID/units/$UNIT_ID/topics/$TOPIC_ID/chunk" \
  -H "X-User-Id: $USER_ID" | jq '.'

echo ""
echo "Step 8: Generating embeddings..."
curl -s -X POST "$BASE_URL/subjects/$SUBJECT_ID/units/$UNIT_ID/topics/$TOPIC_ID/embed" \
  -H "X-User-Id: $USER_ID" | jq '.'

echo ""
echo "Step 9: Generating topic summary..."
curl -s -X POST "$BASE_URL/subjects/$SUBJECT_ID/units/$UNIT_ID/topics/$TOPIC_ID/summarize" \
  -H "X-User-Id: $USER_ID" | jq -r '.summary_text' | head -c 200
echo "..."

echo ""
echo ""
echo "✅ Test data created successfully!"
echo ""
echo "📋 Summary:"
echo "  - Subject ID: $SUBJECT_ID"
echo "  - Unit ID: $UNIT_ID"
echo "  - Topic ID: $TOPIC_ID"
echo ""
echo "🌐 Now open your browser to: http://localhost:5173"
echo "   1. Click the refresh button in the sidebar"
echo "   2. Expand 'Introduction to Algorithms'"
echo "   3. Expand 'Sorting Algorithms'"
echo "   4. Click on 'Quick Sort'"
echo "   5. Start asking questions!"
echo ""
echo "Example questions:"
echo '  - "What is quick sort?"'
echo '  - "Explain the time complexity"'
echo '  - "How does the partitioning work?"'
echo ""
