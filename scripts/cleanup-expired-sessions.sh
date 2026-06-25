#!/bin/bash
# =============================================================================
# Demo Expired Session Cleanup Script
# =============================================================================
# Deletes unclaimed demo sessions (status='active') older than N days.
#
# Usage:
#   ./cleanup-expired-sessions.sh [days]
#
# Examples:
#   ./cleanup-expired-sessions.sh        # default: 30 days (production)
#   ./cleanup-expired-sessions.sh 2      # 2 days (testing)
#   ./cleanup-expired-sessions.sh 7      # 7 days
#
# =============================================================================

# Default cleanup days
DAYS=${1:-30}

# Database connection (from environment or default)
DATABASE_URL=${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/postgres}

echo "=========================================="
echo "Demo Session Cleanup"
echo "=========================================="
echo "Deleting unclaimed sessions older than ${DAYS} days..."
echo ""

# Count sessions before cleanup
BEFORE_COUNT=$(psql "$DATABASE_URL" -t -c "
    SELECT COUNT(*) 
    FROM ai_proposal_platform.demo 
    WHERE status = 'active' 
      AND created_at < NOW() - INTERVAL '${DAYS} days';
" 2>/dev/null || echo "0")

BEFORE_COUNT=$(echo "$BEFORE_COUNT" | tr -d ' ')

if [ "$BEFORE_COUNT" -gt "0" ] 2>/dev/null; then
    echo "Found ${BEFORE_COUNT} expired session(s) to delete."
    echo ""
    
    # Run cleanup
    DELETED=$(psql "$DATABASE_URL" -t -c "
        SELECT ai_proposal_platform.cleanup_expired_demo_sessions(${DAYS});
    " 2>/dev/null || echo "0")
    
    DELETED=$(echo "$DELETED" | tr -d ' ')
    echo "Deleted ${DELETED} expired session(s)."
    echo "Cleanup completed successfully."
else
    echo "No expired sessions found."
    echo "Cleanup completed (nothing to delete)."
fi

echo ""
echo "=========================================="
echo "Current session count:"
psql "$DATABASE_URL" -c "
    SELECT status, COUNT(*) as count 
    FROM ai_proposal_platform.demo 
    GROUP BY status 
    ORDER BY status;
" 2>/dev/null || echo "Could not query status."
echo "=========================================="
