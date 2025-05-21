import psutil
import time
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(
    filename='360_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def find_and_kill_360():
    """查找並結束360安全衛士的進程"""
    target_processes = ['360safe.exe', '360tray.exe', '360sd.exe']
    
    for proc in psutil.process_iter(['name']):
        try:
            # 檢查進程名稱是否在目標列表中
            if proc.info['name'].lower() in target_processes:
                proc.kill()
                logging.info(f"已結束進程: {proc.info['name']}")
                print(f"已結束進程: {proc.info['name']}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def main():
    print("360安全衛士監控程序已啟動...")
    logging.info("監控程序已啟動")
    
    try:
        while True:
            find_and_kill_360()
            # 每5秒檢查一次
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n程序已停止")
        logging.info("監控程序已停止")

if __name__ == "__main__":
    main()
