"""
Chinese Text Post-Processor for Audio2txt v4.0
Fixes over-segmentation and adds proper punctuation to improve readability
"""
import re
from typing import List, Dict


class ChineseTextProcessor:
    """
    Post-process Chinese transcription text to improve quality
    
    Fixes:
    - Over-segmentation (excessive spaces between characters)
    - Missing punctuation
    - Improper sentence boundaries
    """
    
    def __init__(self):
        """Initialize processor"""
        # Common sentence-ending patterns in Chinese
        self.sentence_enders = ['嗎', '嗎?', '吧', '啊', '呢', '了', '的']
        
        # Pause indicators
        self.pause_words = ['那', '那個', '然後', '所以', '因為', '但是', '不過', '其實', '就是']
        
    def process_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Process transcript segments to improve Chinese text quality
        
        Args:
            segments: List of segment dicts with 'text' field
            
        Returns:
            Processed segments with better formatting
        """
        processed_segments = []
        
        for segment in segments:
            original_text = segment['text']
            
            # Step 1: Remove excessive spaces
            cleaned_text = self._remove_excessive_spaces(original_text)
            
            # Step 2: Add punctuation
            punctuated_text = self._add_punctuation(cleaned_text)
            
            # Update segment
            segment['text'] = punctuated_text
            processed_segments.append(segment)
        
        return processed_segments
    
    def _remove_excessive_spaces(self, text: str) -> str:
        """
        Remove excessive spaces between Chinese characters
        
        AssemblyAI tends to add space after every character, which is unnatural in Chinese.
        Keep spaces only between phrases/words.
        """
        # Remove spaces between individual Chinese characters
        # Pattern: Chinese char + space + Chinese char -> merge
        text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)
        
        # Keep spaces after punctuation and numbers
        text = re.sub(r'([。，、！？])\s+', r'\1 ', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _add_punctuation(self, text: str) -> str:
        """
        Add appropriate Chinese punctuation
        
        Uses common patterns to insert commas and periods
        """
        # Add comma after pause words if not already punctuated
        for pause_word in self.pause_words:
            # Pattern: pause_word followed by non-punctuation
            pattern = rf'({pause_word})([^，。！？、\s])'
            text = re.sub(pattern, r'\1，\2', text)
        
        # Add period at sentence endings
        for ender in self.sentence_enders:
            if ender.endswith('?'):
                # Question pattern
                pattern = rf'({ender[:-1]})(\s+)'
                text = re.sub(pattern, r'\1？\2', text)
            else:
                # Statement pattern - add period if next char is capital or Chinese
                pattern = rf'({ender})(\s+[A-Z\u4e00-\u9fff])'
                text = re.sub(pattern, r'\1。\2', text)
        
        # Ensure sentence ends with punctuation
        if text and not text[-1] in '。！？，、':
            text += '。'
        
        return text
    
    def format_transcript(self, segments: List[Dict]) -> str:
        """
        Format full transcript with improved readability
        
        Args:
            segments: Processed segments
            
        Returns:
            Formatted transcript text
        """
        lines = []
        
        for segment in segments:
            speaker = segment.get('speaker', 'SPEAKER_0')
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '')
            
            # Format time
            start_time = self._format_time(start)
            end_time = self._format_time(end)
            
            # Format line
            line = f"[{speaker}] ({start_time} - {end_time})\n{text}"
            lines.append(line)
        
        return "\n\n".join(lines)
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
