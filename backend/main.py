import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import sqlite3
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 允许所有网页来源访问
    allow_credentials=True,
    allow_methods=["*"],      # 允许所有请求方法 (GET, POST, OPTIONS)
    allow_headers=["*"],
)

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")

client = OpenAI(
    api_key=openai_api_key,
    base_url=os.getenv("OPENAI_API_BASE_URL", "https://api.deepseek.com")
)

class NoteRequest(BaseModel):
    text: str


def translate_text(original_text: str) -> str:
    system_prompt = (
        "你是一个精通语言降维解释的阅读助手。你的任务是帮助读者理解晦涩的长难句或段落。\n"
        "要求：\n"
        "1. 坚决不要出现生僻字和高级词汇，要用最通俗易懂的‘大白话’和‘小学生都能听懂的概念’解释这段话的核心意思。\n"
        "2. 语言要精炼，控制在 50-100 字以内。"
    )
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": original_text}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"【AI助理暂时掉线,错误原因: {str(e)}】"

@app.get("/")
def read_root():
    return {"message": "EasyRead 后端已经成功启动啦！"}

@app.post("/api/notes")
def create_note(request: NoteRequest):

    original_text = request.text

    system_prompt = (
        "你是一个精通语言降维解释的阅读助手。你的任务是帮助读者理解晦涩的长难句或段落。\n"
        "要求：\n"
        "1. 坚决不要出现生僻字和高级词汇，要用最通俗易懂的‘大白话’和‘小学生都能听懂的概念’解释这段话的核心意思。\n"
        "2. 语言要精炼，控制在 50-100 字以内。"
    )
    
    ai_summary = translate_text(original_text)
    # ==========================================

    conn = sqlite3.connect("easyread.db")
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO notes (original_text, ai_summary) VALUES (?, ?)", 
        (original_text, ai_summary)
    )

    conn.commit()
    conn.close()

    return {
        "status":"success",
        "original":original_text,
        "summary": ai_summary
    }

# ==================== 新增：获取所有历史记录的接口 ====================
@app.get("/api/notes")
def get_all_notes(query: Optional[str] = None):
    # 1. 连接数据库
    conn = sqlite3.connect("easyread.db")
    cursor = conn.cursor()
    
    # 2. 从 notes 表中按时间倒序提取所有数据
    if query:
        like_query = f"%{query}%"
        cursor.execute(
            "SELECT id, original_text, ai_summary, created_at FROM notes WHERE original_text LIKE ? OR ai_summary LIKE ? ORDER BY id DESC",
            (like_query, like_query)
        )
    else:
        cursor.execute("SELECT id, original_text, ai_summary, created_at FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    # 3. 把提取出来的数据打包成列表返回给前端
    notes_list = []
    for row in rows:
        notes_list.append({
            "id": row[0],
            "original_text": row[1],
            "ai_summary": row[2],
            "created_at": row[3]
        })
        
    return notes_list

@app.put("/api/notes/{note_id}")
def update_note(note_id: int, request: NoteRequest):
    original_text = request.text
    ai_summary = translate_text(original_text)

    conn = sqlite3.connect("easyread.db")
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE notes SET original_text = ?, ai_summary = ? WHERE id = ?",
        (original_text, ai_summary, note_id)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="记录不存在")

    conn.commit()
    conn.close()
    return {
        "status": "success",
        "id": note_id,
        "original": original_text,
        "summary": ai_summary
    }

@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    conn = sqlite3.connect("easyread.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    if deleted == 0:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {"status": "success", "deleted_id": note_id}