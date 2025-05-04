import psutil
import time
import logging
from datetime import datetime
import subprocess

# 設置日誌
logging.basicConfig(
    filename='360_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

def find_and_kill_360():
    """查找並結束360安全衛士的Linux進程"""
    # Linux版本的360相關進程名稱
    target_processes = ['360safe', '360tray', '360sd', '360protection']
    
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            proc_name = proc.info['name'].lower()
            proc_cmdline = ' '.join(proc.info['cmdline']).lower() if proc.info['cmdline'] else ''

            # 檢查進程名稱或命令行是否包含360相關字串
            if any(target in proc_name for target in target_processes) or \
               any(target in proc_cmdline for target in target_processes):
                # 使用kill命令確保進程被終止
                subprocess.run(['kill', '-9', str(proc.pid)], check=False)
                logging.info(f"已結束進程: {proc_name} (PID: {proc.pid})")
                print(f"已結束進程: {proc_name} (PID: {proc.pid})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception as e:
            logging.error(f"處理進程時發生錯誤: {str(e)}")

def check_root_privileges():
    """檢查是否具有root權限"""
    return os.geteuid() == 0

def main():
    print("360安全衛士監控程序已啟動...")
    logging.info("監控程序已啟動")
    
    if not check_root_privileges():
        print("警告：建議使用root權限運行此程序以確保可以終止所有360相關進程")
        logging.warning("程序未使用root權限運行")
    
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