"""
Hyper-Personalized Butler - Automated Pipeline Demo
Simulates hotel reservation system triggering AI briefings for arriving VIP guests.

Usage:
    python demo_trigger.py              # Process today's arriving VIPs
    python demo_trigger.py --all        # Process all 16 guests
    python demo_trigger.py --guest "James Rodriguez"   # Single guest
    python demo_trigger.py --no-save    # Don't save to files
"""

import argparse
import asyncio
import json
import os
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# ── ANSI Colors ──────────────────────────────────────────────────────────────
R = "\033[0m"       # Reset
GOLD = "\033[93m"   # Yellow/Gold
CYAN = "\033[96m"   # Cyan
GREEN = "\033[92m"  # Green
RED = "\033[91m"    # Red
DIM = "\033[2m"     # Dim
BOLD = "\033[1m"    # Bold
BLUE = "\033[94m"   # Blue
MAGENTA = "\033[95m"

# ── Data helpers ──────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "personalized_butler" / "data" / "guests.json"


def load_guests() -> list[dict]:
    with open(DATA_PATH) as f:
        return json.load(f)["guests"]


def get_arriving_guests() -> list[dict]:
    return [g for g in load_guests() if g.get("arriving_tomorrow")]


# ── Visual helpers ────────────────────────────────────────────────────────────
def clear_line():
    print("\033[2K\033[1G", end="", flush=True)


def print_banner():
    print(f"""
{GOLD}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║      ★  THE VENETIAN LAS VEGAS  ★  VIP BUTLER INTELLIGENCE  ★       ║
║                                                                      ║
║         Hyper-Personalized Guest Briefing System  |  Powered by ADK ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{R}
""")


def print_reservation_feed(guests: list[dict]):
    print(f"{BOLD}{CYAN}┌─ RESERVATION SYSTEM FEED {'─'*45}┐{R}")
    print(f"{CYAN}│{R}  {DIM}[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Incoming arrival manifest{R}")
    print(f"{CYAN}│{R}")
    for g in guests:
        tier_color = GOLD if "Diamond" in g["loyalty_tier"] else CYAN
        print(f"{CYAN}│{R}  {GREEN}▶{R}  {BOLD}{g['name']:<28}{R} {tier_color}{g['loyalty_tier']:<22}{R} {DIM}Guest ID: {g['guest_id']}{R}")
    print(f"{CYAN}│{R}")
    print(f"{CYAN}│{R}  {BOLD}{len(guests)} VIP guests arriving{R}  {DIM}→ Triggering Butler Pipeline...{R}")
    print(f"{CYAN}└{'─'*71}┘{R}")
    print()


def print_pipeline_stage(stage: str, agent: str, status: str = "running"):
    icons = {"running": f"{CYAN}⟳{R}", "done": f"{GREEN}✓{R}", "error": f"{RED}✗{R}"}
    icon = icons.get(status, "•")
    print(f"  {icon}  {DIM}{stage:<20}{R}  {MAGENTA}{agent}{R}", flush=True)


def print_guest_header(guest: dict, index: int, total: int):
    tier_color = GOLD if "Diamond" in guest["loyalty_tier"] else CYAN
    name = guest["name"]
    tier = guest["loyalty_tier"]
    gid = guest["guest_id"]
    print(f"\n{GOLD}{'═'*72}{R}")
    print(f"{BOLD}  [{index}/{total}] Processing: {name}{R}  {tier_color}{tier}{R}  {DIM}({gid}){R}")
    print(f"{GOLD}{'─'*72}{R}")


def print_summary(results: list[dict], total_time: float):
    success = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "error"]

    print(f"\n{GOLD}╔══════════════════════════════════════════════════════════════════════╗{R}")
    print(f"{GOLD}║{R}  {BOLD}PIPELINE COMPLETE{R}{' '*52}{GOLD}║{R}")
    print(f"{GOLD}╠══════════════════════════════════════════════════════════════════════╣{R}")
    print(f"{GOLD}║{R}  {GREEN}✓{R} Briefings generated : {BOLD}{len(success):<4}{R}                                      {GOLD}║{R}")
    if failed:
        print(f"{GOLD}║{R}  {RED}✗{R} Failed              : {BOLD}{RED}{len(failed):<4}{R}                                      {GOLD}║{R}")
    print(f"{GOLD}║{R}  {CYAN}⏱{R} Total pipeline time : {BOLD}{total_time:.1f}s{R}  ({total_time/len(results):.1f}s avg per guest)     {GOLD}║{R}")
    print(f"{GOLD}╠══════════════════════════════════════════════════════════════════════╣{R}")

    if success:
        output_dir = Path("insight_cards")
        print(f"{GOLD}║{R}  {DIM}Insight cards saved to: ./{output_dir}/  {R}                            {GOLD}║{R}")
        print(f"{GOLD}║{R}  {DIM}For live agent demo: adk web personalized_butler{R}                    {GOLD}║{R}")

    print(f"{GOLD}╚══════════════════════════════════════════════════════════════════════╝{R}")


# ── ADK Runner ────────────────────────────────────────────────────────────────
async def run_butler(guest: dict, session_service: InMemorySessionService, runner: Runner) -> str:
    """Run the Butler agent for a single guest and return the insight card."""
    from google.genai import types as gtypes

    session = await session_service.create_session(
        app_name="personalized_butler",
        user_id=guest["guest_id"],
    )

    query = (
        f"Prepare a complete VIP briefing and Insight Card for {guest['name']} "
        f"({guest['loyalty_tier']}, Guest ID: {guest['guest_id']}) who is arriving. "
        f"Include profile analysis, F&B preferences, stay history, and specific upsell opportunities with estimated revenue."
    )

    content = gtypes.Content(role="user", parts=[gtypes.Part(text=query)])

    final_response = ""
    async for event in runner.run_async(
        user_id=guest["guest_id"],
        session_id=session.id,
        new_message=content,
    ):
        if hasattr(event, "is_final_response") and event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text
                break

    return final_response


async def process_guest(
    guest: dict,
    index: int,
    total: int,
    session_service: InMemorySessionService,
    runner: Runner,
    save: bool,
) -> dict:
    """Process a single guest: run pipeline, display, optionally save."""
    print_guest_header(guest, index, total)

    print(f"\n{DIM}  Agents activated:{R}")
    print_pipeline_stage("Profile Analysis", "profile_agent")
    print_pipeline_stage("F&B Pattern Mining", "fnb_agent")
    print_pipeline_stage("Insight Synthesis", "insight_agent")

    start = time.time()
    spinner_chars = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
    spinner_task = None

    try:
        # Run the agent
        task = asyncio.create_task(
            run_butler(guest, session_service, runner)
        )

        # Show spinner while waiting
        i = 0
        while not task.done():
            print(f"\r  {CYAN}{spinner_chars[i % len(spinner_chars)]}{R}  {DIM}Butler pipeline running...{R}", end="", flush=True)
            await asyncio.sleep(0.1)
            i += 1

        clear_line()
        result = await task
        elapsed = time.time() - start

        print(f"  {GREEN}✓{R}  {DIM}Pipeline complete in {elapsed:.1f}s{R}\n")

        # Display insight card
        print(result)

        # Save to file
        if save and result:
            output_dir = Path("insight_cards")
            output_dir.mkdir(exist_ok=True)
            safe_name = guest["name"].lower().replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = output_dir / f"{safe_name}_{timestamp}.md"
            filepath.write_text(result, encoding="utf-8")
            print(f"\n  {DIM}💾 Saved: {filepath}{R}")

        return {"guest": guest["name"], "status": "success", "time": elapsed}

    except Exception as e:
        elapsed = time.time() - start
        clear_line()
        print(f"  {RED}✗{R}  Pipeline error: {e}")
        return {"guest": guest["name"], "status": "error", "error": str(e), "time": elapsed}


# ── Main ──────────────────────────────────────────────────────────────────────
async def main():
    parser = argparse.ArgumentParser(description="Butler Pipeline Demo")
    parser.add_argument("--all", action="store_true", help="Process all 16 guests")
    parser.add_argument("--guest", type=str, help="Process a specific guest by name")
    parser.add_argument("--no-save", action="store_true", help="Don't save insight cards to files")
    args = parser.parse_args()

    # Import agent here to ensure env is loaded first
    from personalized_butler.agent import root_agent

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_google_api_key_here":
        print(f"\n{RED}ERROR: GOOGLE_API_KEY not set in .env file{R}")
        print(f"{DIM}Get your key at: aistudio.google.com → Get API key{R}\n")
        return

    # Select guests
    all_guests = load_guests()
    if args.guest:
        query = args.guest.lower()
        guests = [g for g in all_guests if query in g["name"].lower()]
        if not guests:
            print(f"{RED}No guest found matching '{args.guest}'{R}")
            return
    elif args.all:
        guests = all_guests
    else:
        guests = get_arriving_guests()
        if not guests:
            print(f"{GOLD}No guests marked as arriving tomorrow in the dataset.{R}")
            print(f"{DIM}Use --all to process all guests, or --guest <name> for a specific guest.{R}")
            return

    print_banner()
    print_reservation_feed(guests)

    # Confirm before running (skip in demo mode)
    if len(guests) > 3 and not args.guest:
        print(f"{DIM}Processing {len(guests)} guests. Press Enter to start, Ctrl+C to cancel...{R}", end="")
        try:
            input()
        except KeyboardInterrupt:
            print(f"\n{DIM}Cancelled.{R}")
            return

    # Setup ADK runner
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="personalized_butler",
        session_service=session_service,
    )

    pipeline_start = time.time()
    results = []

    for i, guest in enumerate(guests, 1):
        result = await process_guest(
            guest=guest,
            index=i,
            total=len(guests),
            session_service=session_service,
            runner=runner,
            save=not args.no_save,
        )
        results.append(result)

        # Brief pause between guests for readability
        if i < len(guests):
            await asyncio.sleep(1)

    total_time = time.time() - pipeline_start
    print_summary(results, total_time)


if __name__ == "__main__":
    asyncio.run(main())
