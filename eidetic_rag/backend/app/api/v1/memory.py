"""
Memory API endpoints for persistent memory management
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import sys
import json
# Add parent to path to import core modules
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

try:
    # Import memory-related modules if they exist
    import sqlite3
    from datetime import datetime
except ImportError:
    sqlite3 = None
    datetime = None

router = APIRouter()

MEMORY_DB_PATH = Path("./memory.db")


@router.get("/")
async def get_all_memories():
    """Get all stored memories"""
    if not sqlite3:
        raise HTTPException(
            status_code=500,
            detail="SQLite module not available"
        )

    try:
        if not MEMORY_DB_PATH.exists():
            return {"memories": [], "count": 0}

        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()

        query = "SELECT id, content, metadata, created_at FROM memories ORDER BY created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "content": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            })

        return {"memories": memories, "count": len(memories)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{memory_id}")
async def get_memory(memory_id: str):
    """Get a specific memory by ID"""
    if not sqlite3:
        raise HTTPException(
            status_code=500,
            detail="SQLite module not available"
        )

    try:
        if not MEMORY_DB_PATH.exists():
            raise HTTPException(status_code=404, detail="Memory database not found")

        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT id, content, metadata, created_at FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {
            "id": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else {},
            "created_at": row[3]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{memory_id}")
async def delete_memory(memory_id: str):
    """Delete a specific memory by ID"""
    if not sqlite3:
        raise HTTPException(
            status_code=500,
            detail="SQLite module not available"
        )

    try:
        if not MEMORY_DB_PATH.exists():
            raise HTTPException(status_code=404, detail="Memory database not found")

        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()

        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Memory not found")

        return {"status": "success", "message": f"Memory {memory_id} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_memory(request: dict):
    """Create a new memory"""
    if not sqlite3:
        raise HTTPException(
            status_code=500,
            detail="SQLite module not available"
        )

    try:
        content = request.get("content", "")
        tags = request.get("tags", [])
        metadata = request.get("metadata", {})

        if not content:
            raise HTTPException(status_code=400, detail="Content is required")

        if not MEMORY_DB_PATH.exists():
            # Create the database if it doesn't exist
            conn = sqlite3.connect(MEMORY_DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE memories (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()

        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()

        memory_id = f"mem_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(content) % 10000}"
        created_at = datetime.now().isoformat()

        cursor.execute(
            "INSERT INTO memories (id, content, metadata, created_at) VALUES (?, ?, ?, ?)",
            (memory_id, content, json.dumps(metadata) if metadata else None, created_at)
        )
        conn.commit()
        conn.close()

        return {
            "id": memory_id,
            "content": content,
            "metadata": metadata,
            "tags": tags,
            "created_at": created_at
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{memory_id}")
async def update_memory(memory_id: str, request: dict):
    """Update a specific memory by ID"""
    if not sqlite3:
        raise HTTPException(
            status_code=500,
            detail="SQLite module not available"
        )

    try:
        if not MEMORY_DB_PATH.exists():
            raise HTTPException(status_code=404, detail="Memory database not found")

        # Check if memory exists first
        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM memories WHERE id = ?", (memory_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Memory not found")

        # Update the memory
        content = request.get("content", "")
        importance_score = request.get("importance_score", 0.5)
        metadata = request.get("metadata", {})

        # Update metadata to include importance_score if provided
        if importance_score is not None:
            metadata["importance_score"] = importance_score

        cursor.execute(
            "UPDATE memories SET content = ?, metadata = ? WHERE id = ?",
            (content, json.dumps(metadata) if metadata else None, memory_id)
        )
        conn.commit()
        conn.close()

        return {"status": "success", "message": f"Memory {memory_id} updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/json")
async def export_memories_json():
    """Export all memories as JSON"""
    if not sqlite3:
        raise HTTPException(
            status_code=500,
            detail="SQLite module not available"
        )

    try:
        if not MEMORY_DB_PATH.exists():
            return {"memories": [], "count": 0, "exported_at": datetime.now().isoformat()}

        conn = sqlite3.connect(MEMORY_DB_PATH)
        cursor = conn.cursor()

        query = "SELECT id, content, metadata, created_at FROM memories ORDER BY created_at DESC"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        memories = []
        for row in rows:
            memories.append({
                "id": row[0],
                "content": row[1],
                "metadata": json.loads(row[2]) if row[2] else {},
                "created_at": row[3]
            })

        return {
            "memories": memories,
            "count": len(memories),
            "exported_at": datetime.now().isoformat() if datetime else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
