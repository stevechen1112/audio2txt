from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])

class VocabularyItem(BaseModel):
    word: str
    category: str = "general"

@router.get("/", response_model=List[str])
async def get_vocabulary():
    """Get all custom vocabulary words"""
    return db.get_vocabulary()

@router.post("/")
async def add_vocabulary(item: VocabularyItem):
    """Add a new word to vocabulary"""
    success = db.add_vocabulary(item.word, item.category)
    if not success:
        raise HTTPException(status_code=400, detail="Word already exists")
    return {"status": "success", "word": item.word}

@router.delete("/{word}")
async def delete_vocabulary(word: str):
    """Delete a word from vocabulary"""
    db.delete_vocabulary(word)
    return {"status": "success"}
