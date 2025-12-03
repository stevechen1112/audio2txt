import sys
from pathlib import Path
import uvicorn

# 將專案根目錄加入 Python 路徑，以便導入 packages
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

if __name__ == "__main__":
    # 啟動 API 伺服器
    # host="0.0.0.0" 允許區域網路內其他電腦連線
    print(f"Starting Audio2txt Enterprise Server...")
    print(f"API Docs available at: http://localhost:8000/docs")
    
    uvicorn.run(
        "apps.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 開發模式下自動重載
        workers=1
    )
