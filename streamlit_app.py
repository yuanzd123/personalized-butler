"""
Hyper-Personalized Butler — Streamlit Web UI
The Venetian Las Vegas · VIP Host Intelligence Platform
"""

import asyncio
import json
import os
import threading
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ── API Key: support both local .env and Streamlit Cloud secrets ──────────────
try:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
except Exception:
    load_dotenv()

# ── Page config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="VIP Butler Intelligence | The Venetian",
    page_icon="♦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(160deg, #0d0b08 0%, #1a1408 100%);
}
[data-testid="stSidebar"] {
    background: #0f0e09;
    border-right: 1px solid #C9A96E33;
}
[data-testid="stSidebar"] * { color: #e8d5a3 !important; }
.gold { color: #C9A96E; }
.dim  { color: #666; font-size: 12px; }
hr.gold { border: none; border-top: 1px solid #C9A96E33; margin: 12px 0; }

.header-title {
    color: #C9A96E;
    font-family: Georgia, serif;
    font-size: 26px;
    letter-spacing: 4px;
    text-transform: uppercase;
    text-align: center;
}
.header-sub {
    color: #7a6a4a;
    font-size: 11px;
    letter-spacing: 6px;
    text-transform: uppercase;
    text-align: center;
    margin-top: 2px;
    margin-bottom: 16px;
}

.guest-card {
    background: #1a1810;
    border: 1px solid #C9A96E33;
    border-radius: 6px;
    padding: 12px 16px;
    margin: 6px 0;
    transition: border 0.2s;
}
.guest-card:hover { border-color: #C9A96E88; }

.arriving-pill {
    background: #1a2e1a;
    border: 1px solid #4CAF5066;
    color: #81C784;
    border-radius: 20px;
    padding: 1px 10px;
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.alert-pill {
    background: #2e1a1a;
    border: 1px solid #ff444455;
    color: #ff9999;
    border-radius: 20px;
    padding: 1px 10px;
    font-size: 10px;
}
.insight-card {
    background: #1a1810;
    border: 1px solid #C9A96E44;
    border-left: 3px solid #C9A96E;
    border-radius: 6px;
    padding: 28px 32px;
    line-height: 1.8;
    margin-top: 8px;
    font-size: 14px;
}
.pipeline-header {
    color: #C9A96E;
    font-family: Georgia, serif;
    font-size: 18px;
    border-bottom: 1px solid #C9A96E33;
    padding-bottom: 8px;
    margin-bottom: 4px;
}

/* Gold buttons */
.stButton > button {
    background: linear-gradient(135deg, #C9A96E 0%, #8B6914 100%);
    color: #0d0b08 !important;
    font-weight: bold;
    border: none;
    letter-spacing: 1px;
    text-transform: uppercase;
    width: 100%;
    padding: 10px;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #e8c882 0%, #C9A96E 100%);
}

/* Metrics */
[data-testid="stMetric"] {
    background: #1a1810;
    border: 1px solid #C9A96E22;
    border-radius: 6px;
    padding: 12px 16px;
}
[data-testid="stMetricValue"] { color: #C9A96E !important; }

/* Hide default chrome */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_guests() -> list[dict]:
    path = Path(__file__).parent / "personalized_butler" / "data" / "guests.json"
    return json.load(open(path))["guests"]


# ── ADK Runner (threaded, avoids Streamlit async conflicts) ───────────────────
def run_butler_agent(guest_name: str, guest_id: str) -> str:
    """Execute the full ADK multi-agent pipeline in an isolated thread."""
    from personalized_butler.agent import root_agent
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    result: dict = {"output": "", "error": None}

    async def _run():
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="personalized_butler",
            session_service=session_service,
        )
        session = await session_service.create_session(
            app_name="personalized_butler",
            user_id=guest_id,
        )
        query = (
            f"Prepare a complete VIP Insight Card for {guest_name} "
            f"(Guest ID: {guest_id}). Include profile analysis, F&B preferences, "
            f"stay history, personalization moves, and specific upsell opportunities "
            f"with estimated revenue impact."
        )
        content = types.Content(role="user", parts=[types.Part(text=query)])

        async for event in runner.run_async(
            user_id=guest_id,
            session_id=session.id,
            new_message=content,
        ):
            if hasattr(event, "is_final_response") and event.is_final_response():
                if event.content and event.content.parts:
                    result["output"] = event.content.parts[0].text
                break

    def _in_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_run())
        except Exception as e:
            result["error"] = str(e)
        finally:
            loop.close()

    t = threading.Thread(target=_in_thread)
    t.start()
    t.join(timeout=120)

    if result["error"]:
        raise RuntimeError(result["error"])
    return result["output"]


# ── Pipeline visualization + execution ───────────────────────────────────────
def run_pipeline(guest: dict) -> str | None:
    name = guest["name"]
    gid = guest["guest_id"]
    tier = guest["loyalty_tier"]
    tier_color = "#C9A96E" if "Diamond" in tier else "#b0c4de" if "Platinum" in tier else "#ffd700"

    st.markdown(
        f'<div class="pipeline-header">◆ {name} '
        f'<span style="color:{tier_color};font-size:13px;font-family:sans-serif">'
        f'{tier}</span>'
        f'<span style="color:#555;font-size:12px;font-family:sans-serif"> · {gid}</span></div>',
        unsafe_allow_html=True,
    )

    # Launch ADK pipeline in background immediately
    from concurrent.futures import ThreadPoolExecutor
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(run_butler_agent, name, gid)

    # Show pipeline stages while agent runs
    with st.status("🤖 Butler Agent Pipeline", expanded=True) as status:
        st.write("🔍 **profile_agent** — Retrieving guest profile & GSA notes...")
        time.sleep(1.5)
        st.write("🍽️ **fnb_agent** — Mining F&B history & dining patterns...")
        time.sleep(1.2)
        st.write("💡 **insight_agent** — Synthesizing Insight Card + upsell ops...")

        try:
            output = future.result(timeout=120)
            status.update(label="✅ Briefing Ready", state="complete", expanded=False)
            return output
        except Exception as e:
            status.update(label="❌ Pipeline Error", state="error", expanded=True)
            st.error(f"**Error:** {e}")
            if "gemini-3.1-flash-lite-preview" in str(e).lower() or "model" in str(e).lower():
                st.warning("Model not found. Try changing to `gemini-2.0-flash` in `agent.py`.")
            return None


# ── Sidebar ───────────────────────────────────────────────────────────────────
def render_sidebar(guests: list[dict]):
    with st.sidebar:
        st.markdown('<div class="header-title" style="font-size:18px">♦ The Venetian</div>', unsafe_allow_html=True)
        st.markdown('<div class="header-sub" style="font-size:9px">VIP Butler Intelligence</div>', unsafe_allow_html=True)
        st.markdown('<hr class="gold">', unsafe_allow_html=True)

        arriving = [g for g in guests if g.get("arriving_tomorrow")]
        st.markdown(f'**Today\'s Arrivals** <span class="arriving-pill">LIVE</span>', unsafe_allow_html=True)
        for g in arriving:
            st.markdown(
                f'<div style="color:#C9A96E;font-size:13px">▶ {g["name"]}</div>'
                f'<div class="dim" style="margin-bottom:4px">{g["loyalty_tier"]}</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="gold">', unsafe_allow_html=True)

        mode = st.radio(
            "Run mode",
            ["Today's Arrivals (Batch)", "Single Guest Query"],
            index=0,
        )

        selected = None
        if mode == "Single Guest Query":
            name = st.selectbox("Guest", [g["name"] for g in guests])
            selected = next(g for g in guests if g["name"] == name)

        custom_query = None
        if mode == "Single Guest Query":
            st.markdown('<hr class="gold">', unsafe_allow_html=True)
            custom_query = st.text_area(
                "Custom question (optional)",
                placeholder="e.g. What wine should we recommend tonight?",
                height=80,
            )

        st.markdown('<hr class="gold">', unsafe_allow_html=True)
        run = st.button("⚡  Generate Briefings")

        st.markdown('<hr class="gold">', unsafe_allow_html=True)
        st.markdown(
            '<div class="dim">Powered by Google ADK<br>'
            'Multi-Agent Orchestration<br>'
            f'16 VIP profiles · {len(arriving)} arriving today</div>',
            unsafe_allow_html=True,
        )

    return mode, selected, custom_query, run


# ── Idle state: arrival manifest ──────────────────────────────────────────────
def render_arrival_manifest(guests: list[dict]):
    arriving = [g for g in guests if g.get("arriving_tomorrow")]
    st.markdown("### Arrival Manifest — Today")
    cols = st.columns(2)
    for i, g in enumerate(arriving):
        tier_color = "#C9A96E" if "Diamond" in g["loyalty_tier"] else "#b0c4de"
        allergies = [a for a in g["profile"].get("allergies", []) if "None" not in a]
        alert_html = " ".join(f'<span class="alert-pill">⚠ {a}</span>' for a in allergies)
        gaming = g.get("gaming_summary", {}).get("avg_trip_value", 0)
        suite = g["profile"]["room_preferences"].get("preferred_suite", "—")

        with cols[i % 2]:
            st.markdown(f"""
<div class="guest-card">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <span style="color:{tier_color};font-weight:bold;font-size:15px">{g['name']}</span>
    <span class="arriving-pill">ARRIVING</span>
  </div>
  <div class="dim">{g['loyalty_tier']} · {g['guest_id']}</div>
  <div class="dim" style="margin-top:4px">{g.get('nationality','')} · Languages: {g.get('language','')}</div>
  <div class="dim">Preferred: {suite}</div>
  <div style="margin-top:6px">{alert_html if alert_html else '<span class="dim">No active alerts</span>'}</div>
  <div style="color:#C9A96E;font-size:12px;margin-top:6px">Avg Gaming Value: <b>${gaming:,}</b>/trip</div>
</div>""", unsafe_allow_html=True)

    st.markdown(
        '<div style="color:#444;text-align:center;margin-top:24px;font-size:13px">'
        '← Click ⚡ Generate Briefings to run the Butler Agent Pipeline</div>',
        unsafe_allow_html=True,
    )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    guests = load_guests()

    # Check API key
    if not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "your_google_api_key_here":
        st.error("**GOOGLE_API_KEY not configured.** Add it to `.env` (local) or Streamlit secrets (deployed).")
        st.code('GOOGLE_API_KEY = "your_key_here"', language="toml")
        st.markdown("Get your key at [aistudio.google.com](https://aistudio.google.com)")
        st.stop()

    # Header
    st.markdown('<div class="header-title">VIP Butler Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="header-sub">The Venetian Las Vegas · Host Intelligence Platform · Google ADK</div>',
        unsafe_allow_html=True,
    )

    # Metrics row
    arriving = [g for g in guests if g.get("arriving_tomorrow")]
    diamond = [g for g in guests if "Diamond" in g.get("loyalty_tier", "")]
    gaming_today = sum(g.get("gaming_summary", {}).get("avg_trip_value", 0) for g in arriving)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Arriving Today", len(arriving))
    c2.metric("Diamond+ Guests", len(diamond))
    c3.metric("Est. Gaming Value Today", f"${gaming_today:,.0f}")
    c4.metric("Total VIP Profiles", len(guests))

    st.markdown("---")

    mode, selected, custom_query, run = render_sidebar(guests)

    if not run:
        render_arrival_manifest(guests)
        return

    # ── Run pipeline ──────────────────────────────────────────
    if mode == "Today's Arrivals (Batch)":
        targets = [g for g in guests if g.get("arriving_tomorrow")]
        st.markdown(f"### 🚀 Running Pipeline: {len(targets)} VIPs Arriving Today")
        st.caption("Butler Agent orchestrating profile_agent → fnb_agent → insight_agent for each guest")
        st.markdown("---")

        success = 0
        for guest in targets:
            output = run_pipeline(guest)
            if output:
                with st.expander(f"📋 Insight Card — {guest['name']}", expanded=True):
                    st.markdown(f'<div class="insight-card">{output}</div>', unsafe_allow_html=True)
                success += 1
            st.markdown("---")

        if success == len(targets):
            st.success(f"✅ All {success} briefings generated. Hosts are ready.")
        else:
            st.warning(f"⚠ {success}/{len(targets)} briefings generated.")

    else:
        guest = selected
        st.markdown(f"### 🚀 Briefing: {guest['name']}")
        if custom_query:
            st.caption(f"Custom query: *{custom_query}*")
        st.markdown("---")

        output = run_pipeline(guest)
        if output:
            st.markdown("### 📋 Insight Card")
            st.markdown(f'<div class="insight-card">{output}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
