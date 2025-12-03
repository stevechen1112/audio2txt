"""
OpenAI GPT-5 nano Engine for Chinese Summarization
Optimized for cost-effective, high-quality Chinese text summarization
"""
from typing import Optional, Dict, Any
from openai import AsyncOpenAI

class OpenAISummaryEngine:
    """
    OpenAI GPT-5 nano engine for generating Chinese summaries
    
    GPT-5 nano pricing:
    - Input: $0.050 / 1M tokens
    - Output: $0.400 / 1M tokens
    - Cached input: $0.005 / 1M tokens
    
    Perfect for summarization tasks with excellent Chinese language support
    """
    
    def __init__(self, api_key: str):
        """
        Initialize OpenAI engine
        
        Args:
            api_key: OpenAI API key
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-5-nano"  # Latest, most cost-effective model
        
    async def generate_summary(
        self,
        transcript_text: str,
        template_id: str = "universal_summary",
        max_tokens: int = 1000
    ) -> str:
        """
        Generate Chinese summary using GPT-5 nano
        
        Args:
            transcript_text: Full transcript text
            template_id: Template identifier for different summary styles
            max_tokens: Maximum tokens for summary (default: 1000)
            
        Returns:
            Generated Chinese summary
        """
        # Template-based prompts
        prompts = {
            "legal_consultation": """你是專業的法律文件整理專家。請根據以下逐字稿,生成一份專業的法律諮詢摘要。

摘要應包含:
1. 案件背景與主要爭議點
2. 當事人主要訴求
3. 法律意見與建議
4. 後續行動項目

要求:
- 使用繁體中文
- 保持專業法律用語
- 條理清晰,重點突出
- 字數約500-800字

逐字稿內容:
{transcript}

請生成摘要:""",

            "client_interview": """你是專業的客戶訪談分析師。請根據以下訪談逐字稿,生成一份客戶需求分析摘要。

摘要應包含:
1. 客戶背景與主要需求
2. 痛點與挑戰
3. 期望的解決方案
4. 關鍵決策因素
5. 後續跟進事項

要求:
- 使用繁體中文
- 突出客戶關鍵需求
- 結構化呈現
- 字數約600-1000字

逐字稿內容:
{transcript}

請生成摘要:""",

            "executive_meeting": """你是企業高階主管助理。請根據以下會議逐字稿,生成一份高層決策會議紀錄。

摘要應包含:
1. 會議主要議題
2. 討論重點與不同觀點
3. 決策結論
4. 行動項目與負責人
5. 時程規劃

要求:
- 使用繁體中文
- 突出決策與行動項目
- 精簡扼要
- 字數約700-1000字

逐字稿內容:
{transcript}

請生成摘要:""",

            "universal_summary": """你是專業的會議記錄整理專家。請根據以下會議逐字稿,生成一份完整的會議摘要。

摘要應包含:
1. 會議主題與目的
2. 主要討論內容
3. 重要決議事項
4. 行動項目
5. 下次會議安排(如有)

要求:
- 使用繁體中文
- 條理清晰,重點突出
- 保留重要數據與專有名詞
- 字數約600-1000字

逐字稿內容:
{transcript}

請生成摘要:""",

            "concise_minutes": """你是精簡會議記錄專家。請根據以下逐字稿,生成一份精簡的重點摘要。

摘要應包含:
1. 核心議題(3-5點)
2. 重要決議(3-5點)
3. 行動項目(列出負責人與期限,如有)

要求:
- 使用繁體中文
- 極度精簡,每點不超過50字
- 使用條列式
- 總字數約300-500字

逐字稿內容:
{transcript}

請生成摘要:"""
        }
        
        # Get prompt template
        prompt_template = prompts.get(template_id, prompts["universal_summary"])
        
        # Truncate transcript if too long (to save tokens)
        max_transcript_length = 10000  # ~2500 tokens
        if len(transcript_text) > max_transcript_length:
            # Take first 70% and last 30% to preserve context
            split_point = int(max_transcript_length * 0.7)
            transcript_text = (
                transcript_text[:split_point] + 
                "\n\n[... 中間部分省略 ...]\n\n" + 
                transcript_text[-int(max_transcript_length * 0.3):]
            )
        
        # Format prompt with transcript
        prompt = prompt_template.format(transcript=transcript_text)
        
        try:
            # Call GPT-5 nano API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位專業的會議記錄與文件整理專家,擅長將冗長的逐字稿整理成結構化、易讀的摘要。你的摘要總是使用繁體中文,條理清晰,重點突出。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more consistent summaries
                top_p=0.9
            )
            
            summary = response.choices[0].message.content.strip()
            
            # Add metadata
            usage = response.usage
            summary += f"\n\n---\n*本摘要由 GPT-5 nano 生成 | 使用 {usage.total_tokens} tokens (輸入: {usage.prompt_tokens}, 輸出: {usage.completion_tokens})*"
            
            return summary
            
        except Exception as e:
            # Fallback error message
            return f"摘要生成失敗: {str(e)}\n\n請檢查 OpenAI API key 是否正確配置。"
    
    async def extract_action_items(self, transcript_text: str) -> list[str]:
        """
        Extract action items from transcript using GPT-5 nano
        
        Args:
            transcript_text: Full transcript text
            
        Returns:
            List of action items
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是專業的會議分析師,擅長從逐字稿中提取明確的行動項目。"
                    },
                    {
                        "role": "user",
                        "content": f"""請從以下逐字稿中提取所有行動項目(action items)。

要求:
- 每個行動項目獨立一行
- 格式: "- [負責人/部門]: 具體行動內容 (期限:如有)"
- 只提取明確的待辦事項
- 使用繁體中文
- 最多提取10個最重要的項目

逐字稿:
{transcript_text[:5000]}

請列出行動項目:"""
                    }
                ],
                max_tokens=500,
                temperature=0.2
            )
            
            content = response.choices[0].message.content.strip()
            # Parse action items
            action_items = [
                line.strip() 
                for line in content.split('\n') 
                if line.strip() and line.strip().startswith('-')
            ]
            
            return action_items[:10]  # Limit to 10 items
            
        except Exception as e:
            return [f"- 行動項目提取失敗: {str(e)}"]
