# Butler Demo Guide

## Quick Start (Local)

```bash
# 1. Install
pip install google-adk python-dotenv

# 2. Set API key in .env
echo "GOOGLE_API_KEY=your_key_here" > .env

# 3a. Automated pipeline demo (today's arriving VIPs)
python demo_trigger.py

# 3b. All 16 guests
python demo_trigger.py --all

# 3c. Single guest
python demo_trigger.py --guest "James Rodriguez"

# 3d. Interactive Web UI (shows agent orchestration visually)
adk web personalized_butler
```

## GitHub Codespaces (Remote)

1. Open repo on GitHub → click **Code** → **Codespaces** → **Create codespace**
2. Wait ~60 seconds for setup
3. In the terminal, set your API key:
   ```bash
   echo "GOOGLE_API_KEY=your_key_here" > .env
   ```
4. Run the demo:
   ```bash
   python demo_trigger.py
   # or
   adk web personalized_butler
   ```

## Test Queries (for adk web)

- `"Mr. Chen is arriving tomorrow, prepare his full briefing"`
- `"What wine should we recommend for Ms. Kim tonight?"`
- `"James Rodriguez anniversary trip - give me every upsell opportunity"`
- `"Abdullah Al-Rashid group arriving - what do I need to prepare?"`
- `"Who are our highest-value guests this week?"`
