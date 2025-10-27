#!/bin/bash
# Bot Review Monitor - Check for new reviews on latest commits

TOKEN="${GITHUB_TOKEN:-}"
if [ -z "$TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable not set"
    echo "Usage: export GITHUB_TOKEN='your_token_here' && ./check_bot_reviews.sh"
    exit 1
fi

REPO="jerryzhao173985/music_rag"
PR_NUM="1"

echo "================================"
echo "Bot Review Monitor"
echo "================================"
echo "Checking PR #$PR_NUM for new reviews..."
echo ""

# Get latest reviews
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$REPO/pulls/$PR_NUM/reviews" | \
  python3 -c "
import sys, json
reviews = json.load(sys.stdin)
print(f'Total reviews: {len(reviews)}')
print('\nLatest 3 reviews:\n')
for r in reversed(reviews[-3:]):
    print(f'  {r[\"submitted_at\"]} | {r[\"user\"][\"login\"]} | Commit: {r[\"commit_id\"][:7]}')
    if 'Actionable comments posted:' in r.get('body', ''):
        import re
        match = re.search(r'Actionable comments posted: (\d+)', r['body'])
        if match:
            print(f'  → Actionable: {match.group(1)}')
    print()
"

# Get current PR head
echo "================================"
echo "Current PR Status:"
echo "================================"
curl -s -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/$REPO/pulls/$PR_NUM" | \
  python3 -c "
import sys, json
pr = json.load(sys.stdin)
print(f'PR HEAD: {pr[\"head\"][\"sha\"][:7]}')
print(f'Updated: {pr[\"updated_at\"]}')
print(f'State: {pr[\"state\"]}')
print(f'Review Comments: {pr[\"review_comments\"]}')
"

echo ""
echo "================================"
echo "To manually trigger bot review:"
echo "================================"
echo "Comment on PR: '@coderabbitai review'"
echo "Or: '@codex review'"
