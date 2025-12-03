import sys
from pathlib import Path
import subprocess

# 將專案根目錄加入 Python 路徑
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    print(f"Starting Audio2txt Enterprise Web Interface...")
    
    # 使用 subprocess 啟動 streamlit
    # streamlit run apps/web/app.py
    cmd = ["streamlit", "run", "apps/web/app.py"]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStopping Web Interface...")
