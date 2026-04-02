import schedule
import time
from datetime import datetime
from typing import Callable
from automation_engine import ScheduledJobs
from database import Database
from config import CONFIG

class CronScheduler:
    def __init__(self, db: Database):
        self.db = db
        self.jobs = ScheduledJobs(db)
        self.active_stores = []
    
    def load_active_stores(self):
        """Load list of active stores"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM stores WHERE status = 'active'")
        self.active_stores = [row[0] for row in cursor.fetchall()]
        conn.close()
        print(f"Loaded {len(self.active_stores)} active stores")
    
    def schedule_daily_jobs(self):
        """Schedule daily maintenance jobs"""
        # Run at 2 AM daily
        schedule.every().day.at("02:00").do(self.run_daily_jobs)
    
    def schedule_weekly_jobs(self):
        """Schedule weekly maintenance jobs"""
        # Run every Sunday at 3 AM
        schedule.every().sunday.at("03:00").do(self.run_weekly_jobs)
    
    def schedule_monthly_jobs(self):
        """Schedule monthly maintenance jobs"""
        # Run on 1st of each month at 4 AM
        schedule.every().day.at("04:00").do(self.check_and_run_monthly_jobs)
    
    def run_daily_jobs(self):
        """Execute all daily jobs"""
        print(f"[{datetime.now()}] Starting daily jobs")
        self.load_active_stores()
        
        for store_id in self.active_stores:
            try:
                # Sync inventory
                self.jobs.sync_inventory_daily(store_id)
                
                # Check payment statuses
                self.jobs.check_payment_status(store_id)
                
                # Remove out of stock products
                self.jobs.remove_out_of_stock(store_id)
                
                print(f"Daily jobs completed for store {store_id}")
            except Exception as e:
                print(f"Daily jobs failed for store {store_id}: {e}")
                self.db.log_automation(
                    store_id,
                    'daily_jobs',
                    'error',
                    'Daily jobs failed',
                    str(e)
                )
    
    def run_weekly_jobs(self):
        """Execute all weekly jobs"""
        print(f"[{datetime.now()}] Starting weekly jobs")
        self.load_active_stores()
        
        for store_id in self.active_stores:
            try:
                # Update winning products
                self.jobs.update_winning_products_weekly(store_id)
                
                # Adjust pricing
                self.jobs.adjust_prices_weekly(store_id)
                
                print(f"Weekly jobs completed for store {store_id}")
            except Exception as e:
                print(f"Weekly jobs failed for store {store_id}: {e}")
                self.db.log_automation(
                    store_id,
                    'weekly_jobs',
                    'error',
                    'Weekly jobs failed',
                    str(e)
                )
    
    def check_and_run_monthly_jobs(self):
        """Check if it's the 1st of the month and run monthly jobs"""
        if datetime.now().day == 1:
            self.run_monthly_jobs()
    
    def run_monthly_jobs(self):
        """Execute all monthly jobs"""
        print(f"[{datetime.now()}] Starting monthly jobs")
        self.load_active_stores()
        
        for store_id in self.active_stores:
            try:
                # Backup store data
                self.jobs.backup_store_data_monthly(store_id)
                
                # Generate performance report
                self.jobs.generate_performance_report_monthly(store_id)
                
                print(f"Monthly jobs completed for store {store_id}")
            except Exception as e:
                print(f"Monthly jobs failed for store {store_id}: {e}")
                self.db.log_automation(
                    store_id,
                    'monthly_jobs',
                    'error',
                    'Monthly jobs failed',
                    str(e)
                )
    
    def run_continuously(self):
        """Run scheduler continuously"""
        print("Starting cron scheduler...")
        
        # Schedule all job types
        self.schedule_daily_jobs()
        self.schedule_weekly_jobs()
        self.schedule_monthly_jobs()
        
        # Initial load of stores
        self.load_active_stores()
        
        print("Scheduler running. Press Ctrl+C to stop.")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def setup_systemd_service():
    """Generate systemd service file for production deployment"""
    service_content = f"""[Unit]
Description=Auto Store Automation Cron Scheduler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/claude
Environment="DB_PATH={CONFIG.DB_PATH}"
ExecStart=/usr/bin/python3 /home/claude/cron_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    with open('/home/claude/auto-store-cron.service', 'w') as f:
        f.write(service_content)
    
    print("Systemd service file created: auto-store-cron.service")
    print("\nTo install:")
    print("1. sudo cp auto-store-cron.service /etc/systemd/system/")
    print("2. sudo systemctl daemon-reload")
    print("3. sudo systemctl enable auto-store-cron")
    print("4. sudo systemctl start auto-store-cron")


def setup_crontab():
    """Generate crontab entries for manual setup"""
    crontab_entries = f"""
# Auto Store Automation Cron Jobs
# Daily jobs at 2 AM
0 2 * * * cd /home/claude && python3 -c "from cron_scheduler import CronScheduler; from database import Database; from config import CONFIG; db = Database(CONFIG.DB_PATH); scheduler = CronScheduler(db); scheduler.run_daily_jobs()"

# Weekly jobs every Sunday at 3 AM
0 3 * * 0 cd /home/claude && python3 -c "from cron_scheduler import CronScheduler; from database import Database; from config import CONFIG; db = Database(CONFIG.DB_PATH); scheduler = CronScheduler(db); scheduler.run_weekly_jobs()"

# Monthly jobs on 1st of month at 4 AM
0 4 1 * * cd /home/claude && python3 -c "from cron_scheduler import CronScheduler; from database import Database; from config import CONFIG; db = Database(CONFIG.DB_PATH); scheduler = CronScheduler(db); scheduler.run_monthly_jobs()"
"""
    
    with open('/home/claude/crontab.txt', 'w') as f:
        f.write(crontab_entries)
    
    print("Crontab entries saved to crontab.txt")
    print("\nTo install:")
    print("crontab crontab.txt")


if __name__ == '__main__':
    import sys
    
    db = Database(CONFIG.DB_PATH)
    scheduler = CronScheduler(db)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'daily':
            scheduler.run_daily_jobs()
        elif command == 'weekly':
            scheduler.run_weekly_jobs()
        elif command == 'monthly':
            scheduler.run_monthly_jobs()
        elif command == 'setup-systemd':
            setup_systemd_service()
        elif command == 'setup-crontab':
            setup_crontab()
        else:
            print("Usage: python cron_scheduler.py [daily|weekly|monthly|setup-systemd|setup-crontab]")
    else:
        # Run continuously
        scheduler.run_continuously()
