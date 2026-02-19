"""
SUPPORT STARTER AI - PERSISTENT MEMORY
======================================
SQLite-based persistent conversation and user memory
"""

import os
import sqlite3
import json
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict


@dataclass
class UserSession:
    """User session data"""
    session_id: str
    user_id: Optional[str]
    messages: List[Dict[str, str]]
    user_data: Dict[str, Any]
    created_at: str
    last_updated: str


class PersistentMemory:
    """
    SQLite-based persistent storage for conversations and user data
    """
    def __init__(self, db_path: str = "support_memory.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def _init_db(self):
        """Initialize database tables"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

        # Conversations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                user_id TEXT,
                messages TEXT,
                user_data TEXT,
                intent_history TEXT,
                sentiment_history TEXT,
                lead_score_history TEXT,
                created_at TIMESTAMP,
                last_updated TIMESTAMP
            )
        """)

        # Users table for cross-session data
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                total_sessions INTEGER DEFAULT 1,
                properties TEXT
            )
        """)

        # Metrics table for analytics
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                session_id TEXT,
                user_id TEXT,
                data TEXT,
                timestamp TIMESTAMP
            )
        """)

        # Escalations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                escalation_id TEXT,
                session_id TEXT,
                priority TEXT,
                reason TEXT,
                summary TEXT,
                customer_issue TEXT,
                intent TEXT,
                sentiment TEXT,
                lead_score INTEGER,
                timestamp TIMESTAMP,
                resolved BOOLEAN DEFAULT 0
            )
        """)

        # Leads table for high-value prospects
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT,
                session_id TEXT,
                user_id TEXT,
                lead_score INTEGER,
                lead_stage TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                triggered_signals TEXT,
                interested_services TEXT,
                created_at TIMESTAMP,
                notified BOOLEAN DEFAULT 0
            )
        """)

        self.conn.commit()

    def save_session(self, session_id: str, messages: List[Dict],
                    user_data: Dict, intent_history: List[str] = None,
                    sentiment_history: List[str] = None,
                    lead_score_history: List[int] = None,
                    user_id: Optional[str] = None) -> None:
        """Save or update a conversation session"""
        now = datetime.now().isoformat()

        # Check if session exists
        existing = self.conn.execute(
            "SELECT created_at FROM conversations WHERE session_id=?",
            (session_id,)
        ).fetchone()

        if existing:
            # Update existing
            self.conn.execute("""
                UPDATE conversations
                SET messages=?, user_data=?, intent_history=?, sentiment_history=?,
                    lead_score_history=?, last_updated=?, user_id=?
                WHERE session_id=?
            """, (
                json.dumps(messages), json.dumps(user_data),
                json.dumps(intent_history or []),
                json.dumps(sentiment_history or []),
                json.dumps(lead_score_history or []),
                now, user_id, session_id
            ))
        else:
            # Insert new
            self.conn.execute("""
                INSERT INTO conversations
                (session_id, user_id, messages, user_data, intent_history,
                 sentiment_history, lead_score_history, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, user_id, json.dumps(messages),
                json.dumps(user_data), json.dumps(intent_history or []),
                json.dumps(sentiment_history or []),
                json.dumps(lead_score_history or []), now, now
            ))

        self.conn.commit()

    def load_session(self, session_id: str) -> Optional[UserSession]:
        """Load a conversation session"""
        row = self.conn.execute(
            "SELECT * FROM conversations WHERE session_id=?",
            (session_id,)
        ).fetchone()

        if row:
            return UserSession(
                session_id=row["session_id"],
                user_id=row["user_id"],
                messages=json.loads(row["messages"]) if row["messages"] else [],
                user_data=json.loads(row["user_data"]) if row["user_data"] else {},
                created_at=row["created_at"],
                last_updated=row["last_updated"]
            )
        return None

    def get_session_messages(self, session_id: str) -> List[Dict]:
        """Get messages for a session"""
        row = self.conn.execute(
            "SELECT messages FROM conversations WHERE session_id=?",
            (session_id,)
        ).fetchone()

        if row:
            return json.loads(row["messages"]) if row["messages"] else []
        return []

    def update_user(self, user_id: Optional[str], **kwargs) -> None:
        """Update or create user record"""
        if not user_id:
            return

        now = datetime.now().isoformat()
        existing = self.conn.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

        if existing:
            # Update
            updates = []
            values = []
            for key, value in kwargs.items():
                if value is not None:
                    updates.append(f"{key}=?")
                    values.append(value)

            if updates:
                values.append(now)
                values.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)}, last_seen=? WHERE user_id=?"
                self.conn.execute(query, values)

                # Increment session count if it's a new session
                self.conn.execute(
                    "UPDATE users SET total_sessions=total_sessions+1 WHERE user_id=?",
                    (user_id,)
                )
        else:
            # Insert new
            self.conn.execute("""
                INSERT INTO users
                (user_id, name, email, phone, company, first_seen, last_seen, properties)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, kwargs.get("name"), kwargs.get("email"),
                kwargs.get("phone"), kwargs.get("company"), now, now,
                json.dumps(kwargs.get("properties", {}))
            ))

        self.conn.commit()

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data"""
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id=?", (user_id,)
        ).fetchone()

        if row:
            return dict(row)
        return None

    def get_user_history(self, user_id: str, limit: int = 5) -> List[Dict]:
        """Get conversation history for a user"""
        rows = self.conn.execute("""
            SELECT session_id, messages, created_at, last_updated
            FROM conversations
            WHERE user_id=?
            ORDER BY last_updated DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()

        return [dict(row) for row in rows]

    def log_event(self, event_type: str, session_id: str,
                 user_id: Optional[str], data: Dict) -> None:
        """Log an event"""
        self.conn.execute("""
            INSERT INTO events (event_type, session_id, user_id, data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (event_type, session_id, user_id, json.dumps(data), datetime.now().isoformat()))
        self.conn.commit()

    def save_escalation(self, escalation_data: Dict) -> None:
        """Save escalation record"""
        self.conn.execute("""
            INSERT INTO escalations
            (escalation_id, session_id, priority, reason, summary,
             customer_issue, intent, sentiment, lead_score, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            escalation_data.get("escalation_id"),
            escalation_data.get("session_id"),
            escalation_data.get("priority"),
            escalation_data.get("reason"),
            escalation_data.get("summary"),
            escalation_data.get("customer_issue"),
            escalation_data.get("intent"),
            escalation_data.get("sentiment"),
            escalation_data.get("lead_score"),
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def save_lead(self, lead_data: Dict) -> None:
        """Save lead record"""
        self.conn.execute("""
            INSERT INTO leads
            (lead_id, session_id, user_id, lead_score, lead_stage,
             name, email, phone, company, triggered_signals, interested_services, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_data.get("lead_id"),
            lead_data.get("session_id"),
            lead_data.get("user_id"),
            lead_data.get("lead_score"),
            lead_data.get("lead_stage"),
            lead_data.get("name"),
            lead_data.get("email"),
            lead_data.get("phone"),
            lead_data.get("company"),
            json.dumps(lead_data.get("triggered_signals", [])),
            json.dumps(lead_data.get("interested_services", [])),
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def get_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get metrics for the past N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        # Total conversations
        total_convs = self.conn.execute("""
            SELECT COUNT(*) FROM conversations WHERE created_at > ?
        """, (cutoff,)).fetchone()[0]

        # Escalations
        escalations = self.conn.execute("""
            SELECT COUNT(*) FROM escalations WHERE timestamp > ?
        """, (cutoff,)).fetchone()[0]

        # Leads by score
        leads_by_score = self.conn.execute("""
            SELECT lead_score, COUNT(*) FROM leads WHERE created_at > ?
            GROUP BY lead_score
        """, (cutoff,)).fetchall()

        # Top intents
        intents = self.conn.execute("""
            SELECT intent, COUNT(*) as count FROM events
            WHERE event_type='intent' AND timestamp > ?
            GROUP BY intent ORDER BY count DESC LIMIT 10
        """, (cutoff,)).fetchall()

        # Sentiment distribution
        sentiments = self.conn.execute("""
            SELECT sentiment, COUNT(*) as count FROM events
            WHERE event_type='sentiment' AND timestamp > ?
            GROUP BY sentiment
        """, (cutoff,)).fetchall()

        return {
            "period_days": days,
            "total_conversations": total_convs,
            "escalations": escalations,
            "leads_by_score": dict(leads_by_score),
            "top_intents": [dict(r) for r in intents],
            "sentiment_distribution": [dict(r) for r in sentiments]
        }

    def get_recent_conversations(self, limit: int = 20) -> List[Dict]:
        """Get recent conversations"""
        rows = self.conn.execute("""
            SELECT session_id, user_id, created_at, last_updated,
                   json_extract(user_data, '$.customer_name') as name,
                   json_extract(user_data, '$.customer_email') as email
            FROM conversations
            ORDER BY last_updated DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def get_recent_escalations(self, limit: int = 20) -> List[Dict]:
        """Get recent escalations"""
        rows = self.conn.execute("""
            SELECT * FROM escalations
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def get_recent_leads(self, limit: int = 20) -> List[Dict]:
        """Get recent leads"""
        rows = self.conn.execute("""
            SELECT * FROM leads
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Remove sessions older than N days"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        cursor = self.conn.execute(
            "DELETE FROM conversations WHERE last_updated < ?", (cutoff,)
        )
        self.conn.commit()

        return cursor.rowcount

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# Global instance
_persistent_memory: Optional[PersistentMemory] = None


def get_persistent_memory(db_path: str = "support_memory.db") -> PersistentMemory:
    """Get or create persistent memory instance"""
    global _persistent_memory
    if _persistent_memory is None:
        _persistent_memory = PersistentMemory(db_path)
    return _persistent_memory


if __name__ == "__main__":
    # Test the persistent memory
    print("=" * 60)
    print("PERSISTENT MEMORY - TEST")
    print("=" * 60)

    mem = PersistentMemory(":memory:")  # In-memory for testing

    # Save a session
    mem.save_session(
        session_id="test_123",
        user_id="user_1",
        messages=[
            {"role": "user", "content": "Hej!"},
            {"role": "bot", "content": "Välkommen!"}
        ],
        user_data={"customer_name": "Test"},
        intent_history=["greeting"],
        sentiment_history=["positive"],
        lead_score_history=[1]
    )

    # Load it back
    session = mem.load_session("test_123")
    print(f"Loaded session: {session.session_id}")
    print(f"Messages: {session.messages}")

    # Get metrics
    metrics = mem.get_metrics()
    print(f"\nMetrics: {metrics}")
