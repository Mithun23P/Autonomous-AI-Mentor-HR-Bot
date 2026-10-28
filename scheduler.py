import asyncio
from apscheduler.schedulers.blocking import BlockingScheduler
from meet_live_audio import start_gmeet_session

MEET_URL = "https://meet.google.com/fuz-cncx-nir"

def run_scheduled_review():
    print("\n[⏰] Scheduled Review Triggered! Booting Priya for Google Meet...")
    asyncio.run(start_gmeet_session(MEET_URL))

if __name__ == "__main__":
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # Schedule: Every Tuesday and Friday at 10:00 AM
    scheduler.add_job(run_scheduled_review, 'cron', day_of_week='tue,fri', hour=10, minute=0)

    print("[+] Scheduler active! Priya is scheduled to run every Tuesday & Friday at 10:00 AM IST.")
    print("[*] Press Ctrl+C to exit.")
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("\n[-] Scheduler stopped.")