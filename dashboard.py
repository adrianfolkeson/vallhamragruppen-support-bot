"""
SUPPORT STARTER AI - ADMIN DASHBOARD
====================================
Streamlit dashboard for analytics and monitoring
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os

# Page config
st.set_page_config(
    page_title="Support Starter AI - Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    .stMetric {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "db" not in st.session_state:
    from persistent_memory import get_persistent_memory
    st.session_state.db = get_persistent_memory()


def load_metrics():
    """Load metrics from database"""
    return st.session_state.db.get_metrics(days=30)


def load_recent_conversations():
    """Load recent conversations"""
    return st.session_state.db.get_recent_conversations(limit=50)


def load_recent_escalations():
    """Load recent escalations"""
    return st.session_state.db.get_recent_escalations(limit=50)


def load_recent_leads():
    """Load recent leads"""
    return st.session_state.db.get_recent_leads(limit=50)


# Sidebar
with st.sidebar:
    st.title("Support Starter AI")
    st.caption("v2.0 - Vallhamragruppen AB")

    st.divider()

    page = st.radio(
        "Navigation",
        ["Dashboard", "Conversations", "Escalations", "Leads", "Settings"],
        icons=["graph-up", "chat", "exclamation-triangle", "person", "gear"]
    )

    st.divider()

    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

    if st.button("Refresh Data", use_container_width=True):
        st.rerun()


# Dashboard Page
if page == "Dashboard":
    st.title("Dashboard")

    # Load metrics
    metrics = load_metrics()

    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Total Conversations",
            metrics["total_conversations"],
            delta="Last 30 days"
        )

    with col2:
        st.metric(
            "Escalations",
            metrics["escalations"],
            delta=f"{metrics['escalations']} cases"
        )

    with col3:
        high_leads = sum(1 for score, count in metrics["leads_by_score"].items() if int(score) >= 4)
        st.metric(
            "Hot Leads",
            high_leads,
            delta="Score 4-5"
        )

    with col4:
        esc_rate = (metrics["escalations"] / max(metrics["total_conversations"], 1)) * 100
        st.metric(
            "Escalation Rate",
            f"{esc_rate:.1f}%",
            delta="Target: <10%"
        )

    st.divider()

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Intents")
        if metrics["top_intents"]:
            intent_df = pd.DataFrame(metrics["top_intents"])
            st.bar_chart(intent_df.set_index("intent")["count"])
        else:
            st.info("No intent data yet")

    with col2:
        st.subheader("Sentiment Distribution")
        if metrics["sentiment_distribution"]:
            sentiment_df = pd.DataFrame(metrics["sentiment_distribution"])
            st.bar_chart(sentiment_df.set_index("sentiment")["count"])
        else:
            st.info("No sentiment data yet")

    st.divider()

    # Lead Score Distribution
    st.subheader("Lead Score Distribution")
    if metrics["leads_by_score"]:
        score_labels = {k: f"Score {k}" for k in metrics["leads_by_score"].keys()}
        score_data = {"Score": list(score_labels.values()), "Count": list(metrics["leads_by_score"].values())}
        score_df = pd.DataFrame(score_data)
        st.bar_chart(score_df.set_index("Score")["Count"])
    else:
        st.info("No lead data yet")


# Conversations Page
elif page == "Conversations":
    st.title("Recent Conversations")

    conversations = load_recent_conversations()

    if conversations:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            search = st.text_input("Search", placeholder="Session ID or name...")
        with col2:
            date_filter = st.date_input("From date", value=datetime.now() - timedelta(days=7))
        with col3:
            min_sessions = st.number_input("Min messages", min_value=1, value=1)

        # Display conversations
        for conv in conversations:
            with st.expander(f"Session: {conv['session_id']} - {conv.get('name', 'Unknown')}"):
                col1, col2, col3 = st.columns(3)
                col1.write(f"**Created:** {conv['created_at']}")
                col2.write(f"**Last Update:** {conv['last_updated']}")
                col3.write(f"**Email:** {conv.get('email', 'N/A')}")

                # Load messages
                messages = st.session_state.db.get_session_messages(conv['session_id'])
                if messages:
                    st.write("**Messages:**")
                    for msg in messages[-5:]:  # Show last 5
                        role = msg.get('role', 'unknown').upper()
                        content = msg.get('content', '')
                        if role == 'USER':
                            st.chat_message("user").write(content)
                        else:
                            st.chat_message("assistant").write(content)
    else:
        st.info("No conversations yet")


# Escalations Page
elif page == "Escalations":
    st.title("Escalations")

    escalations = load_recent_escalations()

    if escalations:
        # Priority filter
        priority_filter = st.multiselect(
            "Filter by Priority",
            ["critical", "high", "medium", "low"],
            default=["critical", "high", "medium", "low"]
        )

        for esc in escalations:
            if esc["priority"] in priority_filter:
                # Color code by priority
                color = {
                    "critical": "red",
                    "high": "orange",
                    "medium": "yellow",
                    "low": "green"
                }.get(esc["priority"], "gray")

                with st.expander(f"{esc['priority'].upper()}: {esc['escalation_id']}"):
                    col1, col2, col3 = st.columns(3)
                    col1.write(f"**Reason:** {esc['reason']}")
                    col2.write(f"**Sentiment:** {esc['sentiment']}")
                    col3.write(f"**Lead Score:** {esc['lead_score']}")

                    st.write(f"**Summary:** {esc['summary']}")
                    st.write(f"**Issue:** {esc['customer_issue']}")

                    if st.button(f"Mark Resolved", key=f"resolve_{esc['id']}"):
                        st.session_state.db.conn.execute(
                            "UPDATE escalations SET resolved=1 WHERE id=?",
                            (esc['id'],)
                        )
                        st.session_state.db.conn.commit()
                        st.rerun()
    else:
        st.info("No escalations yet")


# Leads Page
elif page == "Leads":
    st.title("Leads")

    leads = load_recent_leads()

    if leads:
        # Score filter
        min_score = st.slider("Minimum Lead Score", 1, 5, 3)

        for lead in leads:
            if lead["lead_score"] >= min_score:
                with st.expander(f"Score {lead['lead_score']}/5 - {lead.get('name', 'Unknown')}"):
                    col1, col2, col3, col4 = st.columns(4)
                    col1.write(f"**Email:** {lead.get('email', 'N/A')}")
                    col2.write(f"**Phone:** {lead.get('phone', 'N/A')}")
                    col3.write(f"**Company:** {lead.get('company', 'N/A')}")
                    col4.write(f"**Stage:** {lead['lead_stage']}")

                    signals = json.loads(lead.get('triggered_signals', '[]'))
                    if signals:
                        st.write("**Buying Signals:**")
                        for signal in signals:
                            st.caption(f"- {signal}")

                    services = json.loads(lead.get('interested_services', '[]'))
                    if services:
                        st.write("**Interested In:**")
                        for service in services:
                            st.caption(f"- {service}")
    else:
        st.info("No leads yet")


# Settings Page
elif page == "Settings":
    st.title("Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Configuration")

        st.text_input("Company Name", value="Vallhamragruppen AB", disabled=True)
        st.text_input("Phone", value="0793-006638", disabled=True)
        st.text_input("Email", value="info@vallhamragruppen.se", disabled=True)

        st.divider()

        st.subheader("API Status")
        api_key_set = bool(os.getenv("ANTHROPIC_API_KEY"))
        if api_key_set:
            st.success("Anthropic API: Connected")
        else:
            st.warning("Anthropic API: Not configured (using local fallback)")

    with col2:
        st.subheader("Database")

        db_info = st.session_state.db.conn.execute(
            "SELECT COUNT(*) as count FROM conversations"
        ).fetchone()

        st.metric("Total Sessions", db_info["count"])

        db_size = os.path.getsize(st.session_state.db.db_path) if hasattr(st.session_state.db, 'db_path') else 0
        st.metric("Database Size", f"{db_size / 1024:.1f} KB")

        st.divider()

        st.subheader("Actions")

        if st.button("Clean Old Sessions (30+ days)"):
            deleted = st.session_state.db.cleanup_old_sessions(days=30)
            st.success(f"Deleted {deleted} old sessions")

    st.divider()
    st.subheader("Export Data")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("Export Conversations"):
            convs = load_recent_conversations()
            st.download_button(
                "Download JSON",
                json.dumps(convs, indent=2, default=str),
                "conversations.json",
                "application/json"
            )

    with col2:
        if st.button("Export Escalations"):
            escalations = load_recent_escalations()
            st.download_button(
                "Download JSON",
                json.dumps(escalations, indent=2, default=str),
                "escalations.json",
                "application/json"
            )

    with col3:
        if st.button("Export Leads"):
            leads = load_recent_leads()
            st.download_button(
                "Download JSON",
                json.dumps(leads, indent=2, default=str),
                "leads.json",
                "application/json"
            )


# Footer
st.divider()
st.caption("Support Starter AI v2.0 | Vallhamragruppen AB")
