import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path.cwd()))

from apps.api.services import get_service

async def main():
    service = get_service()
    
    # Use the existing report content from the previous run
    report_path = Path(r"C:\Users\User\Desktop\audio2txt\output\api_results\04e0414d-c8bf-4281-8ae7-7b9a017a4d18\report.md")
    if not report_path.exists():
        print("Report file not found")
        return
        
    content = report_path.read_text(encoding='utf-8')
    
    # Output PDF path
    pdf_path = report_path.parent / "report_fixed.pdf"
    
    print(f"Regenerating PDF to: {pdf_path}")
    try:
        service._export_report_pdf(content, pdf_path)
        print("PDF generation successful")
    except Exception as e:
        print(f"PDF generation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
