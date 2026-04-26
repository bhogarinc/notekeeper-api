"""Note service with business logic and validation."""
from typing import List, Optional, Dict, Any
from datetime import datetime
import re
import markdown
from bleach import clean
import logging

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.note import Note, NoteVersion
from app.repositories.note import NoteRepository
from app.schemas.note import NoteCreate, NoteUpdate

logger = logging.getLogger(__name__)


class NoteService:
    """Service layer for note operations."""
    
    ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'h1', 'h2', 'h3', 'h4', 'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'a', 'img']
    ALLOWED_ATTRIBUTES = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title']
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = NoteRepository(db)
    
    def create_note(self, user_id: str, note_data: NoteCreate) -> Note:
        """Create new note with validation and processing."""
        # Validate title
        if not note_data.title or len(note_data.title.strip()) == 0:
            note_data.title = "Untitled Note"
        
        if len(note_data.title) > 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Title must be less than 200 characters"
            )
        
        # Process content
        content_html = self._render_markdown(note_data.content) if note_data.content else ""
        
        # Prepare data
        data = {
            "user_id": user_id,
            "title": note_data.title.strip(),
            "content": note_data.content or "",
            "content_html": content_html,
            "category_id": note_data.category_id,
            "is_pinned": note_data.is_pinned,
            "color": note_data.color or "#6366f1",
        }
        
        note = self.repository.create(data)
        
        # Add tags if provided
        if note_data.tag_ids:
            self._attach_tags(note, note_data.tag_ids)
        
        # Update search vector
        self._update_search_vector(note)
        
        logger.info(f"Note created: {note.id} by user {user_id}")
        return note
    
    def update_note(self, user_id: str, note_id: str, note_data: NoteUpdate) -> Note:
        """Update note with versioning."""
        note = self.repository.get_by_id(note_id)
        
        if not note or str(note.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        # Create version backup
        self._create_version(note)
        
        # Prepare update data
        update_data = {}
        
        if note_data.title is not None:
            if len(note_data.title) > 200:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Title must be less than 200 characters"
                )
            update_data["title"] = note_data.title.strip()
        
        if note_data.content is not None:
            update_data["content"] = note_data.content
            update_data["content_html"] = self._render_markdown(note_data.content)
        
        if note_data.category_id is not None:
            update_data["category_id"] = note_data.category_id
        
        if note_data.color is not None:
            update_data["color"] = note_data.color
        
        if note_data.is_pinned is not None:
            update_data["is_pinned"] = note_data.is_pinned
            update_data["pinned_at"] = datetime.utcnow() if note_data.is_pinned else None
        
        # Apply updates
        note = self.repository.update(note, update_data)
        
        # Update tags
        if note_data.tag_ids is not None:
            self._sync_tags(note, note_data.tag_ids)
        
        # Update search vector
        self._update_search_vector(note)
        
        logger.info(f"Note updated: {note_id}")
        return note
    
    def delete_note(self, user_id: str, note_id: str) -> None:
        """Soft or hard delete note."""
        note = self.repository.get_by_id(note_id)
        
        if not note or str(note.user_id) != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )
        
        self.repository.delete(note)
        logger.info(f"Note deleted: {note_id}")
    
    def pin_note(self, user_id: str, note_id: str) -> Note:
        """Pin a note."""
        note = self.repository.get_by_id(note_id)
        
        if not note or str(note.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Note not found")
        
        if note.is_archived:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot pin archived notes"
            )
        
        return self.repository.update(note, {
            "is_pinned": True,
            "pinned_at": datetime.utcnow()
        })
    
    def archive_note(self, user_id: str, note_id: str) -> Note:
        """Archive a note."""
        note = self.repository.get_by_id(note_id)
        
        if not note or str(note.user_id) != user_id:
            raise HTTPException(status_code=404, detail="Note not found")
        
        return self.repository.update(note, {
            "is_archived": True,
            "is_pinned": False,
            "archived_at": datetime.utcnow(),
            "pinned_at": None
        })
    
    def _render_markdown(self, content: str) -> str:
        """Render markdown to HTML with sanitization."""
        if not content:
            return ""
        
        html = markdown.markdown(content, extensions=['fenced_code', 'tables'])
        return clean(html, tags=self.ALLOWED_TAGS, attributes=self.ALLOWED_ATTRIBUTES)
    
    def _update_search_vector(self, note: Note) -> None:
        """Update PostgreSQL full-text search vector."""
        from sqlalchemy import func
        note.search_vector = func.to_tsvector(
            'english',
            f"{note.title} {note.content}"
        )
        self.db.commit()
    
    def _create_version(self, note: Note) -> None:
        """Create version backup before update."""
        version = NoteVersion(
            note_id=note.id,
            version_number=note.version,
            title=note.title,
            content=note.content,
            created_by=note.user_id
        )
        self.db.add(version)
        note.version += 1
        self.db.commit()
    
    def _attach_tags(self, note: Note, tag_ids: List[str]) -> None:
        """Attach tags to note."""
        from app.models.tag import Tag
        tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        note.tags.extend(tags)
        self.db.commit()
    
    def _sync_tags(self, note: Note, tag_ids: List[str]) -> None:
        """Sync tags (replace all)."""
        from app.models.tag import Tag
        note.tags = self.db.query(Tag).filter(Tag.id.in_(tag_ids)).all()
        self.db.commit()
