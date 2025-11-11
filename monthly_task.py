from datetime import datetime,timedelta
from app import summarize_last_month_data, delete_old_data
# DEBUG : 06.18 추가 함수 매월 1일 자동 실행을 위한

def log_start(file_path, message):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a") as f:
        f.write(f"[{now}] {message}\n")

def main():
    print("Montly task started")
    summarize_last_month_data()
    delete_old_data()
    
    with open('/home/pi/cron_execution_check.log', 'a') as f :
        f.write(f"[{datetime.now()}] Monthly_task.py \n")
    
if __name__ ==  '__main__':
    log_start("/home/pi/monthly_log.txt", "✅ RoPSy_main_v5_1.py auto-execution completed")
    main()
