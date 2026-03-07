"""Tool functions for the Personalized Butler agents."""

import json
from pathlib import Path

_DATA_PATH = Path(__file__).parent / "data" / "guests.json"


def _load_guests() -> list[dict]:
    with open(_DATA_PATH) as f:
        return json.load(f)["guests"]


def lookup_guest_profile(guest_name: str) -> dict:
    """Look up a guest profile by name (fuzzy match).

    Args:
        guest_name: Full or partial name of the guest to search for.

    Returns:
        A dict with guest basic info, loyalty tier, preferences, and allergies.
        Returns an error message if no guest is found.
    """
    guests = _load_guests()
    query = guest_name.lower()

    for guest in guests:
        if query in guest["name"].lower():
            return {
                "guest_id": guest["guest_id"],
                "name": guest["name"],
                "loyalty_tier": guest["loyalty_tier"],
                "loyalty_number": guest["loyalty_number"],
                "nationality": guest["nationality"],
                "language": guest["language"],
                "date_of_birth": guest["date_of_birth"],
                "spouse": guest.get("spouse"),
                "spouse_birthday": guest.get("spouse_birthday"),
                "profile": guest["profile"],
                "gaming_summary": guest.get("gaming_summary"),
            }

    return {"error": f"No guest found matching '{guest_name}'"}


def get_gsa_notes(guest_id: str) -> dict:
    """Retrieve all GSA (Guest Service Agent) notes for a guest.

    Args:
        guest_id: The unique guest identifier (e.g. 'VIP-001').

    Returns:
        A dict containing the guest name and their chronological GSA notes.
    """
    guests = _load_guests()

    for guest in guests:
        if guest["guest_id"] == guest_id:
            return {
                "guest_id": guest_id,
                "guest_name": guest["name"],
                "notes": guest["gsa_notes"],
            }

    return {"error": f"No guest found with ID '{guest_id}'"}


def get_fnb_history(guest_id: str) -> dict:
    """Retrieve the F&B (Food & Beverage) dining history for a guest.

    Args:
        guest_id: The unique guest identifier (e.g. 'VIP-001').

    Returns:
        A dict containing the guest name, their dining history, and summary stats.
    """
    guests = _load_guests()

    for guest in guests:
        if guest["guest_id"] == guest_id:
            history = guest["fnb_history"]
            total_spend = sum(r["total"] for r in history)
            avg_spend = total_spend / len(history) if history else 0
            restaurants = list({r["restaurant"] for r in history})

            return {
                "guest_id": guest_id,
                "guest_name": guest["name"],
                "dining_history": history,
                "summary": {
                    "total_spend": total_spend,
                    "average_per_visit": round(avg_spend, 2),
                    "total_visits": len(history),
                    "frequent_restaurants": restaurants,
                },
            }

    return {"error": f"No guest found with ID '{guest_id}'"}


def get_stay_history(guest_id: str) -> dict:
    """Retrieve the stay/accommodation history for a guest.

    Args:
        guest_id: The unique guest identifier (e.g. 'VIP-001').

    Returns:
        A dict containing the guest name, stay history, and summary.
    """
    guests = _load_guests()

    for guest in guests:
        if guest["guest_id"] == guest_id:
            stays = guest["stay_history"]
            all_issues = [
                issue for stay in stays for issue in stay.get("issues", [])
            ]
            avg_satisfaction = (
                sum(s["satisfaction"] for s in stays) / len(stays) if stays else 0
            )

            return {
                "guest_id": guest_id,
                "guest_name": guest["name"],
                "stay_history": stays,
                "summary": {
                    "total_stays": len(stays),
                    "average_satisfaction": round(avg_satisfaction, 1),
                    "preferred_room_type": stays[0]["room_type"] if stays else None,
                    "past_issues": all_issues,
                },
            }

    return {"error": f"No guest found with ID '{guest_id}'"}
