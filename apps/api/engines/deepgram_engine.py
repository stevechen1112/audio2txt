"""
Deepgram Engine for Audio2txt v4.0 Enterprise
Provides superior Chinese transcription with automatic punctuation
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any


class DeepgramEngine:
    """
    Deepgram cloud transcription engine with excellent Chinese support
    
    Advantages over AssemblyAI:
    - Better Chinese word segmentation
    - Automatic punctuation
    - 78% cost reduction ($0.0043/min vs $0.02/min)
    - 2-3x faster processing
    - Superior speaker diarization
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Deepgram engine
        
        Args:
            api_key: Deepgram API key
        """
        # Set environment variable BEFORE importing DeepgramClient
        if api_key:
            os.environ["DEEPGRAM_API_KEY"] = api_key
        
        # Dynamic import after environment variable is set
        from deepgram import DeepgramClient
        
        # Initialize client (reads from environment)
        self.client = DeepgramClient()
        
    def transcribe_with_diarization(
        self,
        audio_path: str | Path,
        language: str = "zh",
        num_speakers: Optional[int] = None,
        vocabulary: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio with speaker diarization using Deepgram
        
        Args:
            audio_path: Path to audio file
            language: Language code (zh, zh-CN, zh-TW)
            num_speakers: Expected number of speakers (optional)
            vocabulary: Custom vocabulary list for better accuracy
            
        Returns:
            Dict containing transcript and speaker information
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Configure transcription options
        options = {
            "model": "nova-2",  # Latest model with best Chinese support
            "language": language,
            "punctuate": True,  # Automatic punctuation (huge improvement!)
            "diarize": True,  # Speaker diarization
            "smart_format": True,  # Better formatting
            "utterances": True,  # Get speaker-separated segments
        }
        
        # Add custom vocabulary if provided
        if vocabulary and len(vocabulary) > 0:
            # Deepgram supports up to 1000 keywords
            options["keywords"] = vocabulary[:1000]
        
        # Read audio file
        with open(audio_path, "rb") as audio_file:
            buffer_data = audio_file.read()
        
        payload = {"buffer": buffer_data}
        
        # Run transcription (Deepgram SDK v5 API)
        response = self.client.listen.v1.media.transcribe_file(
            payload,
            options,
        )
        
        # Parse results
        return self._parse_transcript(response)
    
    def _parse_transcript(self, response) -> Dict[str, Any]:
        """
        Parse Deepgram response into our format
        
        Args:
            response: Deepgram API response
            
        Returns:
            Dict with segments and speakers
        """
        result = response.results
        
        if not result or not result.channels:
            raise Exception("No transcription results returned")
        
        channel = result.channels[0]
        alternative = channel.alternatives[0]
        
        # Extract full text
        full_text = alternative.transcript
        
        # Extract utterances (speaker-separated segments)
        utterances = alternative.words if hasattr(alternative, 'words') else []
        
        segments = []
        speakers = {}
        
        # Group words by speaker into utterances
        if hasattr(alternative, 'words') and alternative.words:
            current_speaker = None
            current_start = None
            current_end = None
            current_words = []
            
            for word in alternative.words:
                speaker_id = f"SPEAKER_{getattr(word, 'speaker', 0)}"
                
                # New speaker or first word
                if speaker_id != current_speaker:
                    # Save previous segment
                    if current_speaker and current_words:
                        segment_text = " ".join(current_words)
                        segments.append({
                            "start": current_start,
                            "end": current_end,
                            "text": segment_text,
                            "speaker": current_speaker,
                            "confidence": 1.0,
                        })
                        
                        # Update speaker stats
                        duration = current_end - current_start
                        if current_speaker not in speakers:
                            speakers[current_speaker] = {
                                "id": current_speaker,
                                "name": current_speaker,
                                "total_time": 0,
                                "segment_count": 0
                            }
                        speakers[current_speaker]["total_time"] += duration
                        speakers[current_speaker]["segment_count"] += 1
                    
                    # Start new segment
                    current_speaker = speaker_id
                    current_start = word.start
                    current_end = word.end
                    current_words = [word.word]
                else:
                    current_words.append(word.word)
                    current_end = word.end
            
            # Save last segment
            if current_speaker and current_words:
                segment_text = " ".join(current_words)
                segments.append({
                    "start": current_start,
                    "end": current_end,
                    "text": segment_text,
                    "speaker": current_speaker,
                    "confidence": 1.0,
                })
                
                duration = current_end - current_start
                if current_speaker not in speakers:
                    speakers[current_speaker] = {
                        "id": current_speaker,
                        "name": current_speaker,
                        "total_time": 0,
                        "segment_count": 0
                    }
                speakers[current_speaker]["total_time"] += duration
                speakers[current_speaker]["segment_count"] += 1
        
        # Format full text with speaker labels
        formatted_text = "\n\n".join([
            f"[{seg['speaker']}] ({self._format_time(seg['start'])} - {self._format_time(seg['end'])})\n{seg['text']}"
            for seg in segments
        ])
        
        # Get audio duration
        audio_duration = alternative.words[-1].end if alternative.words else 0
        
        return {
            "text": full_text,
            "formatted_text": formatted_text,
            "segments": segments,
            "speakers": list(speakers.values()),
            "language": getattr(channel, 'detected_language', 'zh'),
            "audio_duration": audio_duration,
        }
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    async def generate_summary(
        self,
        audio_path: str | Path,
        summary_type: str = "bullets",
    ) -> str:
        """
        Generate AI summary using Deepgram's summarization
        
        Args:
            audio_path: Path to audio file
            summary_type: Type of summary
            
        Returns:
            Summary text (English only, recommend using GPT-5 nano for Chinese)
        """
        # Deepgram's summarization is English-only
        # We should use GPT-5 nano for Chinese summaries
        return "Deepgram 摘要功能僅支援英文，請使用 GPT-5 nano 生成中文摘要。"
