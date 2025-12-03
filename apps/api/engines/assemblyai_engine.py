"""
AssemblyAI Engine for Audio2txt v4.0 Enterprise
Provides cloud-based transcription with speaker diarization
"""
import assemblyai as aai
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio

class AssemblyAIEngine:
    """
    Cloud-based transcription engine using AssemblyAI API
    Replaces local Whisper + Pyannote for lightweight deployment
    """
    
    def __init__(self, api_key: str):
        """
        Initialize AssemblyAI engine
        
        Args:
            api_key: AssemblyAI API key
        """
        aai.settings.api_key = api_key
        self.transcriber = aai.Transcriber()
        
    async def transcribe_with_diarization(
        self,
        audio_path: str | Path,
        language: str = "zh",
        num_speakers: Optional[int] = None,
        vocabulary: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Transcribe audio with speaker diarization
        
        Args:
            audio_path: Path to audio file
            language: Language code (zh for Chinese)
            num_speakers: Expected number of speakers (optional)
            
        Returns:
            Dict containing transcript and speaker information
        """
        audio_path = Path(audio_path)
        
        # Configure transcription
        config_kwargs = {
            "language_code": language,
            "speaker_labels": True,
            "speakers_expected": num_speakers,
            "punctuate": True,
            "format_text": True,
        }
        
        if vocabulary:
            # AssemblyAI allows boosting key terms to improve accuracy
            config_kwargs["word_boost"] = vocabulary[:200]  # Hard limit per API docs
            config_kwargs["boost_param"] = aai.BoostParam.high
        
        config = aai.TranscriptionConfig(**config_kwargs)
        
        # Run transcription (blocking call, so we use run_in_executor)
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None,
            lambda: self.transcriber.transcribe(str(audio_path), config=config)
        )
        
        # Check for errors
        if transcript.status == aai.TranscriptStatus.error:
            raise Exception(f"Transcription failed: {transcript.error}")
        
        # Parse results
        return self._parse_transcript(transcript)
    
    def _parse_transcript(self, transcript: aai.Transcript) -> Dict[str, Any]:
        """
        Parse AssemblyAI transcript into our format
        
        Args:
            transcript: AssemblyAI transcript object
            
        Returns:
            Dict with segments and speakers
        """
        segments = []
        speakers = {}
        
        # Process utterances (speaker-separated segments)
        for utterance in transcript.utterances:
            speaker_id = f"SPEAKER_{utterance.speaker}"
            
            # Track speakers
            if speaker_id not in speakers:
                speakers[speaker_id] = {
                    "id": speaker_id,
                    "name": speaker_id,
                    "total_time": 0,
                    "segment_count": 0
                }
            
            # Calculate duration
            duration = (utterance.end - utterance.start) / 1000.0  # Convert ms to seconds
            speakers[speaker_id]["total_time"] += duration
            speakers[speaker_id]["segment_count"] += 1
            
            # Add segment
            segments.append({
                "start": utterance.start / 1000.0,  # Convert ms to seconds
                "end": utterance.end / 1000.0,
                "text": utterance.text,
                "speaker": speaker_id,
                "confidence": utterance.confidence,
            })
        
        # Format full text with speaker labels
        formatted_text = "\n\n".join([
            f"[{seg['speaker']}] ({self._format_time(seg['start'])} - {self._format_time(seg['end'])})\n{seg['text']}"
            for seg in segments
        ])
        
        return {
            "text": transcript.text,  # Full text without speakers
            "formatted_text": formatted_text,  # Text with speaker labels
            "segments": segments,
            "speakers": list(speakers.values()),
            "language": getattr(transcript, "language_code", "unknown"),
            "audio_duration": getattr(transcript, "audio_duration", 0),
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
        Generate AI summary using AssemblyAI's summarization
        
        Args:
            audio_path: Path to audio file
            summary_type: Type of summary (bullets, paragraph, headline)
            
        Returns:
            Summary text
        """
        config = aai.TranscriptionConfig(
            summarization=True,
            summary_model=aai.SummarizationModel.informative,
            summary_type=aai.SummarizationType.bullets,
        )
        
        loop = asyncio.get_event_loop()
        transcript = await loop.run_in_executor(
            None,
            lambda: self.transcriber.transcribe(str(audio_path), config=config)
        )
        
        return transcript.summary or ""
