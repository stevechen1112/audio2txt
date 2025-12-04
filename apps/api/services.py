"""
Processing Service for Audio2txt v4.0 Enterprise
Handles audio transcription and analysis using cloud APIs
"""
import uuid
from pathlib import Path
from typing import Dict, Any, List
import textwrap
import os

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from fastapi import UploadFile

from .database import db
from .engines.assemblyai_engine import AssemblyAIEngine
from .engines.deepgram_engine import DeepgramEngine
from .engines.openai_engine import OpenAISummaryEngine
from .engines.chinese_processor import ChineseTextProcessor
from .notifications import notification_manager
from packages.core.audio2txt.utils.config import Config

class ProcessingService:
    _instance = None
    
    def __init__(self):
        """Initialize processing service with cloud engines"""
        self.upload_dir = Path("uploads")
        self.output_dir = Path("output/api_results")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config for templates and API keys
        self.config = Config()
        
        # Initialize STT engine based on configuration
        stt_engine = self.config.stt_engine.lower()
        
        if stt_engine == "deepgram":
            # Use Deepgram (recommended for Chinese)
            api_key = self.config.deepgram_api_key
            if not api_key:
                raise RuntimeError("DEEPGRAM_API_KEY is not configured. Please add it to .env file.")
            self.stt_engine = DeepgramEngine(api_key=api_key)
            print("✅ Using Deepgram STT Engine (optimized for Chinese)")
        else:
            # Fallback to AssemblyAI
            api_key = self.config.assemblyai_api_key
            if not api_key:
                raise RuntimeError("ASSEMBLYAI_API_KEY is not configured in environment variables or .env file.")
            self.stt_engine = AssemblyAIEngine(api_key=api_key)
            print("⚠️  Using AssemblyAI STT Engine (consider switching to Deepgram for better Chinese support)")
        
        # Initialize OpenAI engine for Chinese summarization
        openai_key = self.config.openai_api_key
        if openai_key:
            self.openai_engine = OpenAISummaryEngine(api_key=openai_key)
        else:
            self.openai_engine = None
            print("Warning: OPENAI_API_KEY not configured. Summary generation will use AssemblyAI's English summary.")
        
        # Initialize Chinese text processor
        self.chinese_processor = ChineseTextProcessor()
        
    @classmethod
    def get_instance(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def save_upload(self, file: UploadFile) -> str:
        """
        Save uploaded file to disk
        
        Args:
            file: Uploaded file
            
        Returns:
            Path to saved file
        """
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        file_path = self.upload_dir / f"{file_id}{file_ext}"
        
        # Save file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
            
        return str(file_path)
    
    async def process_audio(self, task_id: str, file_path: str, template_id: str):
        """
        Background processing task using AssemblyAI
        
        Args:
            task_id: Unique task identifier
            file_path: Path to audio file
            template_id: Template ID for summary generation
        """
        try:
            db.update_task(task_id, "processing", 10)
            
            # Fetch vocabulary for better accuracy
            vocab_list = db.get_vocabulary()
            
            # 1. Transcription & Diarization using configured STT engine
            db.update_task(task_id, "transcribing", 20)
            
            result = await self.stt_engine.transcribe_with_diarization(
                audio_path=file_path,
                language="zh",  # Chinese
                vocabulary=vocab_list or None,
            )
            
            # 1.5. Post-process Chinese text to improve quality
            db.update_task(task_id, "post-processing", 50)
            result["segments"] = self.chinese_processor.process_segments(result["segments"])
            result["formatted_text"] = self.chinese_processor.format_transcript(result["segments"])
            
            db.update_task(task_id, "analyzing", 60)
            
            # 2. Generate summary using GPT-5 nano (preferred) or AssemblyAI
            if self.openai_engine:
                # Use GPT-5 nano for high-quality Chinese summary
                summary = await self.openai_engine.generate_summary(
                    transcript_text=result["formatted_text"],
                    template_id=template_id
                )
            else:
                # Fallback to AssemblyAI's built-in summary
                summary = await self.assemblyai_engine.generate_summary(
                    audio_path=file_path
                )
            
            db.update_task(task_id, "finalizing", 90)
            
            # 3. Save Results
            output_base = self.output_dir / task_id
            output_base.mkdir(exist_ok=True)
            
            # Save Transcript
            with open(output_base / "transcript.txt", "w", encoding="utf-8") as f:
                f.write(result["formatted_text"])
                
            # Save Report (using template format)
            report_content = self._format_report(result, summary, template_id)
            report_path = output_base / "report.md"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_content)

            pdf_path = output_base / "report.pdf"
            self._export_report_pdf(report_content, pdf_path)
                
            result_data = {
                "transcript_path": str(output_base / "transcript.txt"),
                "report_path": str(report_path),
                "report_pdf_path": str(pdf_path),
                "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                "speakers": len(result["speakers"]),
                "duration": result["audio_duration"],
                "highlights": self._extract_highlights(result),
            }
            
            db.update_task(task_id, "completed", 100, result=result_data)
            notification_manager.send_task_update("completed", task_id, result_data)
            
        except Exception as e:
            db.update_task(task_id, "failed", 0, error=str(e))
            notification_manager.send_task_update(
                "failed",
                task_id,
                {"error": str(e), "file_path": file_path, "template_id": template_id},
            )
            print(f"Task {task_id} failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _format_report(self, transcript_result: Dict, summary: str, template_id: str) -> str:
        """
        Format report using template
        
        Args:
            transcript_result: Transcription result from AssemblyAI
            summary: AI-generated summary
            template_id: Template identifier
            
        Returns:
            Formatted markdown report
        """
        # Template mapping
        template_names = {
            "legal_consultation": "法律諮詢記錄",
            "client_interview": "客戶需求訪談",
            "executive_meeting": "高層決策會議",
            "universal_summary": "會議記錄",
            "concise_minutes": "精簡逐字稿",
        }
        
        template_name = template_names.get(template_id, "會議記錄")
        
        # Build report
        report = f"# {template_name}\n\n"
        report += f"**處理時間**: {self._get_current_time()}\n\n"
        report += f"**音訊長度**: {transcript_result['audio_duration']:.1f} 秒\n\n"
        report += f"**說話人數**: {len(transcript_result['speakers'])}\n\n"
        report += "---\n\n"
        
        if template_id == "concise_minutes":
            report += self._build_concise_minutes(transcript_result)
        else:
            # Add summary
            report += "## 📋 會議摘要\n\n"
            report += summary + "\n\n"
            report += "---\n\n"
            
            # Add speaker statistics
            report += "## 👥 說話人統計\n\n"
            for speaker in transcript_result['speakers']:
                minutes = int(speaker['total_time'] // 60)
                seconds = int(speaker['total_time'] % 60)
                report += f"- **{speaker['name']}**: {minutes}分{seconds}秒 ({speaker['segment_count']} 段發言)\n"
            
            report += "\n---\n\n"
            
            # Add full transcript
            report += "## 📝 完整逐字稿\n\n"
            report += transcript_result['formatted_text']
        
        return report
    
    def _build_concise_minutes(self, transcript_result: Dict) -> str:
        """Create a concise style report without redundant transcript"""
        segments = transcript_result.get("segments", [])
        lines = ["## 🔍 精簡重點\n"]
        highlights = self._extract_highlights(transcript_result, limit=6)
        if highlights:
            for item in highlights:
                lines.append(
                    f"- {item['start']} - {item['speaker']}: {item['text']}"
                )
        else:
            lines.append("- 尚無可用重點")
        
        lines.append("\n---\n")
        lines.append("## ✅ 行動項目\n")
        actions = self._extract_action_points(segments)
        if actions:
            lines.extend(actions)
        else:
            lines.append("- 無明確行動項目（請人工補充）")
        
        lines.append("\n---\n")
        lines.append("## 👥 說話人統計\n")
        for speaker in transcript_result['speakers']:
            minutes = int(speaker['total_time'] // 60)
            seconds = int(speaker['total_time'] % 60)
            lines.append(f"- {speaker['name']}: {minutes}分{seconds}秒 / {speaker['segment_count']} 段")
        
        lines.append("\n---\n")
        lines.append("## 🗣️ 精華逐字稿\n")
        short_segments = self._extract_short_transcript(segments)
        lines.extend(short_segments if short_segments else ["- 無精華內容"])
        
        return "\n".join(lines)
    
    def _extract_action_points(self, segments: List[Dict]) -> List[str]:
        keywords = ["需要", "請", "必須", "確認", "安排", "交付", "follow"]
        actions: List[str] = []
        for seg in segments:
            text = seg["text"]
            if any(key in text for key in keywords):
                actions.append(
                    f"- {self._format_time(seg['start'])} {seg['speaker']}: {text}"
                )
            if len(actions) >= 5:
                break
        return actions
    
    def _extract_short_transcript(self, segments: List[Dict]) -> List[str]:
        if not segments:
            return []
        short_lines = []
        step = max(1, len(segments) // 8)
        for seg in segments[::step][:8]:
            preview = seg["text"]
            if len(preview) > 160:
                preview = preview[:160] + "..."
            short_lines.append(
                f"- {self._format_time(seg['start'])} {seg['speaker']}: {preview}"
            )
        return short_lines
    
    def _extract_highlights(self, transcript_result: Dict, limit: int = 5) -> List[Dict[str, str]]:
        segments = transcript_result.get("segments", [])
        if not segments:
            return []
        step = max(1, len(segments) // limit)
        highlights = []
        for seg in segments[::step][:limit]:
            preview = seg["text"]
            if len(preview) > 120:
                preview = preview[:120] + "..."
            highlights.append(
                {
                    "speaker": seg["speaker"],
                    "start": self._format_time(seg["start"]),
                    "end": self._format_time(seg["end"]),
                    "text": preview,
                }
            )
        return highlights
    
    def _export_report_pdf(self, report_content: str, pdf_path: Path) -> None:
        """Export markdown text into a PDF document with Chinese support"""
        pdf_path.parent.mkdir(parents=True, exist_ok=True)
        c = canvas.Canvas(str(pdf_path), pagesize=letter)
        
        # Register Chinese font
        font_name = "Helvetica"  # Default fallback
        try:
            # Try Windows font (Microsoft JhengHei)
            font_path = r"C:\Windows\Fonts\msjh.ttc"
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('MicrosoftJhengHei', font_path))
                font_name = "MicrosoftJhengHei"
            else:
                print(f"Warning: Chinese font not found at {font_path}")
        except Exception as e:
            print(f"Warning: Could not load Chinese font: {e}")
            
        c.setFont(font_name, 10)
        
        width, height = letter
        x_margin = 40
        y = height - 50
        line_height = 14
        
        for line in report_content.splitlines():
            # Simple wrapping (Note: textwrap counts chars, not visual width)
            # Reducing width to 50 chars to account for wider Chinese characters
            chunks = textwrap.wrap(line, 50) or [""]
            for chunk in chunks:
                if y <= 50:
                    c.showPage()
                    c.setFont(font_name, 10)  # Reset font on new page
                    y = height - 50
                c.drawString(x_margin, y, chunk)
                y -= line_height
        c.save()
    
    def _format_time(self, seconds: float | str) -> str:
        """Format seconds to HH:MM:SS"""
        try:
            seconds = float(seconds)
        except (ValueError, TypeError):
            return str(seconds)
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _get_current_time(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Lazy initialization - don't create instance at module import
service = None


def get_service():
    """Get or create service instance (lazy initialization)"""
    global service
    if service is None:
        service = ProcessingService.get_instance()
    return service
