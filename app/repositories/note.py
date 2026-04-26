"""Note repository with search and filtering."""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func, desc
from sqlalchemy.dialects.postgresql import array

from app.models.note import Note
from app.repositories.base import BaseRepository


class NoteRepository(BaseRepository[Note]):
    """Repository for Note entity with advanced queries."""
    
    def __init__(self, db: Session):
        super().__init__(Note, db)
    
    def get_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
        is_archived: Optional[bool] = None,
        is_pinned: Optional[bool] = None,
        category_id: Optional[str] = None,
        tag_ids: Optional[List[str]] = None,
        search_query: Optional[str] = None
    ) -> tuple[List[Note], int]:
        """Get notes by user with filtering and pagination."""
        query = self.db.query(Note).filter(Note.user_id == user_id)
        
        # Apply filters
        if is_archived is not None:
            query = query.filter(Note.is_archived == is_archived)
        if is_pinned is not None:
            query = query.filter(Note.is_pinned == is_pinned)
        if category_id:
            query = query.filter(Note.category_id == category_id)
        if tag_ids:
            query = query.filter(Note.tags.any(Note.tags.id.in_(tag_ids)))
        
        # Full-text search
        if search_query:
            search_vector = func.to_tsquery('english', search_query + ':*')
            query = query.filter(Note.search_vector.op('@@')(search_vector))
        
        # Get total count
        total = query.count()
        
        # Order: pinned first, then by updated_at
        query = query.order_by(
            desc(Note.is_pinned),
            desc(Note.updated_at)
        )
        
        notes = query.offset(skip).limit(limit).all()
        return notes, total
    
    def get_pinned_by_user(self, user_id: str) -> List[Note]:
        """Get pinned notes for user."""
        return self.db.query(Note).filter(
            Note.user_id == user_id,
            Note.is_pinned == True,
            Note.is_archived == False
        ).order_by(desc(Note.pinned_at)).all()
    
    def get_archived_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Note], int]:
        """Get archived notes with pagination."""
        query = self.db.query(Note).filter(
            Note.user_id == user_id,
            Note.is_archived == True
        )
        total = query.count()
        notes = query.order_by(desc(Note.archived_at)).offset(skip).limit(limit).all()
        return notes, total
    
    def search_notes(
        self,
        user_id: str,
        query: str,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Note], int]:
        """Full-text search notes."""
        search_vector = func.plainto_tsquery('english', query)
        
        db_query = self.db.query(Note).filter(
            Note.user_id == user_id,
            Note.is_archived == False,
            Note.search_vector.op('@@')(search_vector)
        )
        
        # Add relevance ranking
        db_query = db_query.order_by(
            func.ts_rank_cd(Note.search_vector, search_vector).desc()
        )
        
        total = db_query.count()
        notes = db_query.offset(skip).limit(limit).all()
        return notes, total
    
    def get_with_relations(self, note_id: str) -> Optional[Note]:
        """Get note with tags and category loaded."""
        return self.db.query(Note).options(
            joinedload(Note.tags),
            joinedload(Note.category)
        ).filter(Note.id == note_id).first()
