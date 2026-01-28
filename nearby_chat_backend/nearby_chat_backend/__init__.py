from apscheduler.schedulers.background import BackgroundScheduler
from rooms.tasks import delete_expired_rooms, send_expiry_notifications

scheduler = BackgroundScheduler()
scheduler.add_job(delete_expired_rooms, 'interval', minutes=5)
scheduler.add_job(send_expiry_notifications, 'interval', minutes=5)
scheduler.start()
