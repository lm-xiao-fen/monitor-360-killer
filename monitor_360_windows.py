import psutil
import time
import logging
import os
import signal
import ctypes
import sys
from datetime import datetime

# 設置日誌
logging.basicConfig(
    filename='360_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def is_admin():
    """檢查是否具有管理員權限"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def signal_handler(signum, frame):
    """處理程序終止信號"""
    logging.info("收到終止信號，程序正在停止...")
    print("\n程序正在停止...")
    sys.exit(0)

def find_and_kill_360():
    """查找並結束360安全衛士的進程"""
    target_processes = [
        '360safe.exe', '360tray.exe', '360sd.exe', 
        '360rp.exe', '360protection.exe', '360se.exe',
        '360chrome.exe', '360wallpaper.exe'
    ]
    
    killed_processes = []
    
    for proc in psutil.process_iter(['name', 'pid', 'create_time']):
        try:
            proc_info = proc.info
            proc_name = proc_info['name'].lower()
            
            # 檢查進程名稱是否在目標列表中
            if proc_name in [p.lower() for p in target_processes]:
                # 記錄進程信息
                process_age = time.time() - proc_info['create_time']
                logging.info(f"發現360相關進程: {proc_name} (PID: {proc_info['pid']}, 運行時間: {process_age:.2f}秒)")
                
                try:
                    # 先嘗試正常終止
                    proc.terminate()
                    proc.wait(timeout=3)  # 等待進程終止
                except psutil.TimeoutExpired:
                    # 如果正常終止失敗，使用kill
                    proc.kill()
                
                killed_processes.append(f"{proc_name} (PID: {proc_info['pid']})")
                logging.info(f"已終止進程: {proc_name} (PID: {proc_info['pid']})")
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.warning(f"處理進程時出現警告: {str(e)}")
        except Exception as e:
            logging.error(f"處理進程時發生錯誤: {str(e)}", exc_info=True)
    
    return killed_processes

def main():
    # 檢查管理員權限
    if not is_admin():
        warning_msg = "警告：建議使用管理員權限運行此程序以確保可以終止所有360相關進程"
        print(warning_msg)
        logging.warning(warning_msg)
    
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("360安全衛士監控程序已啟動...")
    print(f"日誌文件位置: {os.path.abspath('360_monitor.log')}")
    logging.info("監控程序已啟動")
    
    try:
        while True:
            killed_processes = find_and_kill_360()
            if killed_processes:
                print(f"\n時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("已終止的進程:")
                for proc in killed_processes:
                    print(f"- {proc}")
            time.sleep(5)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logging.error(f"程序運行時發生錯誤: {str(e)}", exc_info=True)
        print(f"\n程序發生錯誤: {str(e)}")
        raise

if __name__ == "__main__":
    main()