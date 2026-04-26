"""Base repository with CRUD operations, pagination, and filtering."""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session, Query
from sqlalchemy import func, desc, asc
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status
import logging

from app.models.base import Base

T = TypeVar('T', bound=Base)
logger = logging.getLogger(__name__)


class BaseRepository(Generic[T]):
    """Generic repository with standard CRUD operations."""
    
    def __init__(self, model: Type[T], db: Session):
        self.model = model
        self.db = db
    
    def get_by_id(self, id: Any) -> Optional[T]:
        """Get entity by primary key."""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_by_id_or_404(self, id: Any) -> T:
        """Get entity by ID or raise 404."""
        entity = self.get_by_id(id)
        if not entity:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{self.model.__name__} with id {id} not found"
            )
        return entity
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[T]:
        """Get all entities with pagination."""
        query = self.db.query(self.model)
        
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            query = query.order_by(desc(order_column) if order_desc else asc(order_column))
        
        return query.offset(skip).limit(limit).all()
    
    def create(self, obj_data: Dict[str, Any]) -> T:
        """Create new entity."""
        try:
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Create failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create {self.model.__name__}"
            )
    
    def update(self, db_obj: T, obj_data: Dict[str, Any]) -> T:
        """Update entity."""
        try:
            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
            
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Update failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update {self.model.__name__}"
            )
    
    def delete(self, db_obj: T) -> None:
        """Delete entity."""
        try:
            self.db.delete(db_obj)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Delete failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to delete {self.model.__name__}"
            )
    
    def count(self, **filters) -> int:
        """Count entities with optional filters."""
        query = self.db.query(func.count(self.model.id))
        for key, value in filters.items():
            if hasattr(self.model, key):
                query = query.filter(getattr(self.model, key) == value)
        return query.scalar()
