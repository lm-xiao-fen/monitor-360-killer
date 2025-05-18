import psutil
import time
import logging
import os
import signal
import subprocess
from datetime import datetime
from pathlib import Path
import plistlib
import pwd

# 設置日誌
logging.basicConfig(
    filename='360_monitor.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_current_user():
    """獲取當前用戶名稱"""
    return pwd.getpwuid(os.getuid()).pw_name

def check_root_privileges():
    """檢查是否具有root權限"""
    return os.geteuid() == 0

def get_application_paths():
    """獲取可能的360應用程序路徑"""
    paths = [
        '/Applications',
        f'/Users/{get_current_user()}/Applications',
        '/Library/Application Support'
    ]
    return paths

def find_360_apps():
    """查找系統中安裝的360應用"""
    found_apps = []
    for base_path in get_application_paths():
        try:
            for root, dirs, files in os.walk(base_path):
                for item in dirs + files:
                    if '360' in item and item.endswith('.app'):
                        full_path = os.path.join(root, item)
                        found_apps.append(full_path)
                        logging.info(f"發現360應用: {full_path}")
        except (PermissionError, FileNotFoundError) as e:
            logging.warning(f"搜索路徑時出錯 {base_path}: {str(e)}")
    return found_apps

def get_bundle_identifier(app_path):
    """獲取應用程序的Bundle Identifier"""
    try:
        plist_path = os.path.join(app_path, 'Contents/Info.plist')
        if os.path.exists(plist_path):
            with open(plist_path, 'rb') as f:
                plist_data = plistlib.load(f)
                return plist_data.get('CFBundleIdentifier', '')
    except Exception as e:
        logging.error(f"讀取plist文件時出錯 {app_path}: {str(e)}")
    return None

def find_and_kill_360():
    """查找並結束360相關進程"""
    # 常見的360相關進程名稱
    target_processes = [
        '360safe', '360tray', '360sd', 
        '360protection', '360se', 'SafeDaemon',
        '360SafeManager', '360Browser', '360Chrome'
    ]
    
    # 查找已安裝的360應用的Bundle Identifiers
    bundle_ids = []
    for app in find_360_apps():
        bundle_id = get_bundle_identifier(app)
        if bundle_id:
            bundle_ids.append(bundle_id)
            logging.info(f"發現360應用 Bundle ID: {bundle_id}")
    
    killed_processes = []
    
    for proc in psutil.process_iter(['name', 'pid', 'create_time', 'cmdline']):
        try:
            proc_info = proc.info
            proc_name = proc_info['name'].lower()
            proc_cmdline = ' '.join(proc_info['cmdline']).lower() if proc_info['cmdline'] else ''
            
            # 檢查進程是否與360相關
            is_target = (
                any(target in proc_name for target in target_processes) or
                any(target in proc_cmdline for target in target_processes) or
                any(bid in proc_cmdline for bid in bundle_ids)
            )
            
            if is_target:
                # 記錄進程信息
                process_age = time.time() - proc_info['create_time']
                logging.info(f"發現360相關進程: {proc_name} (PID: {proc_info['pid']}, 運行時間: {process_age:.2f}秒)")
                
                try:
                    # 先嘗試正常終止
                    proc.terminate()
                    proc.wait(timeout=3)
                except psutil.TimeoutExpired:
                    # 如果正常終止失敗，使用SIGKILL
                    proc.kill()
                
                killed_processes.append(f"{proc_name} (PID: {proc_info['pid']})")
                logging.info(f"已終止進程: {proc_name} (PID: {proc_info['pid']})")
                
                # 檢查是否有相關的launch agents
                check_and_remove_launch_agents(proc_name)
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logging.warning(f"處理進程時出現警告: {str(e)}")
        except Exception as e:
            logging.error(f"處理進程時發生錯誤: {str(e)}", exc_info=True)
    
    return killed_processes

def check_and_remove_launch_agents(process_name):
    """檢查並移除相關的Launch Agents"""
    launch_agent_paths = [
        f'/Library/LaunchAgents',
        f'/Library/LaunchDaemons',
        f'/Users/{get_current_user()}/Library/LaunchAgents'
    ]
    
    for path in launch_agent_paths:
        try:
            if not os.path.exists(path):
                continue
                
            for filename in os.listdir(path):
                if '360' in filename.lower() or process_name.lower() in filename.lower():
                    plist_path = os.path.join(path, filename)
                    logging.info(f"發現360相關啟動項: {plist_path}")
                    
                    try:
                        # 嘗試卸載啟動項
                        subprocess.run(['launchctl', 'unload', plist_path], check=False)
                        
                        if check_root_privileges():
                            os.remove(plist_path)
                            logging.info(f"已刪除啟動項: {plist_path}")
                        else:
                            logging.warning(f"需要root權限才能刪除啟動項: {plist_path}")
                            
                    except Exception as e:
                        logging.error(f"處理啟動項時發生錯誤 {plist_path}: {str(e)}")
                        
        except Exception as e:
            logging.error(f"檢查啟動項目錄時發生錯誤 {path}: {str(e)}")

def signal_handler(signum, frame):
    """處理程序終止信號"""
    logging.info("收到終止信號，程序正在停止...")
    print("\n程序正在停止...")
    exit(0)

def main():
    # 註冊信號處理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("360安全衛士 macOS 監控程序已啟動...")
    print(f"日誌文件位置: {os.path.abspath('360_monitor.log')}")
    logging.info("監控程序已啟動")
    
    if not check_root_privileges():
        warning_msg = "警告：建議使用root權限運行此程序以確保可以終止所有360相關進程"
        print(warning_msg)
        logging.warning(warning_msg)
    
    # 初始掃描安裝的360應用
    print("\n正在掃描系統中的360應用...")
    apps = find_360_apps()
    if apps:
        print("發現以下360應用:")
        for app in apps:
            print(f"- {app}")
    else:
        print("未發現已安裝的360應用")
    
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