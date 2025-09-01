from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.database.models import Place, Category, Media, Review
from core.schemas.place import PlaceCreate, PlaceUpdate, PlaceInDB
from core.schemas.category import CategoryCreate, CategoryInDB

class CatalogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ===== PLACES =====
    
    async def create_place(self, place_data: PlaceCreate, owner_id: int) -> PlaceInDB:
        """Создание нового заведения"""
        db_place = Place(
            name=place_data.name,
            description=place_data.description,
            address=place_data.address,
            phone=place_data.phone,
            email=place_data.email,
            website=place_data.website,
            working_hours=place_data.working_hours,
            owner_id=owner_id
        )
        
        # Добавляем категории, если они указаны
        if place_data.category_ids:
            categories = await self.get_categories_by_ids(place_data.category_ids)
            db_place.categories = categories
        
        self.db.add(db_place)
        await self.db.commit()
        await self.db.refresh(db_place)
        
        return PlaceInDB.from_orm(db_place)

    async def get_place(self, place_id: int) -> Optional[PlaceInDB]:
        """Получение заведения по ID"""
        result = await self.db.execute(
            select(Place)
            .options(
                selectinload(Place.categories),
                selectinload(Place.media),
                selectinload(Place.reviews)
            )
            .where(Place.id == place_id)
        )
        place = result.scalars().first()
        return PlaceInDB.from_orm(place) if place else None

    async def update_place(
        self, place_id: int, place_data: PlaceUpdate, owner_id: Optional[int] = None
    ) -> Optional[PlaceInDB]:
        """Обновление данных заведения"""
        # Проверяем существование места и права доступа
        query = select(Place).where(Place.id == place_id)
        if owner_id:
            query = query.where(Place.owner_id == owner_id)
            
        result = await self.db.execute(query)
        db_place = result.scalars().first()
        
        if not db_place:
            return None
            
        # Обновляем поля
        update_data = place_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field != 'category_ids':
                setattr(db_place, field, value)
        
        # Обновляем категории, если они указаны
        if 'category_ids' in update_data:
            categories = await self.get_categories_by_ids(update_data['category_ids'])
            db_place.categories = categories
        
        db_place.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(db_place)
        
        return PlaceInDB.from_orm(db_place)

    async def delete_place(self, place_id: int, owner_id: Optional[int] = None) -> bool:
        """Удаление заведения"""
        query = delete(Place).where(Place.id == place_id)
        if owner_id:
            query = query.where(Place.owner_id == owner_id)
            
        result = await self.db.execute(query)
        await self.db.commit()
        
        return result.rowcount > 0

    async def list_places(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[int] = None,
        search: Optional[str] = None,
        is_verified: Optional[bool] = None,
        owner_id: Optional[int] = None
    ) -> List[PlaceInDB]:
        """Получение списка заведений с фильтрацией"""
        query = select(Place).options(
            selectinload(Place.categories),
            selectinload(Place.media).load_only("id", "url", "is_cover")
        )
        
        # Применяем фильтры
        if category_id is not None:
            query = query.join(Place.categories).where(Category.id == category_id)
            
        if search:
            search = f"%{search}%"
            query = query.where(
                or_(
                    Place.name.ilike(search),
                    Place.description.ilike(search),
                    Place.address.ilike(search)
                )
            )
            
        if is_verified is not None:
            query = query.where(Place.is_verified == is_verified)
            
        if owner_id is not None:
            query = query.where(Place.owner_id == owner_id)
        
        # Применяем пагинацию
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        places = result.scalars().all()
        
        return [PlaceInDB.from_orm(place) for place in places]

    # ===== CATEGORIES =====
    
    async def create_category(self, category_data: CategoryCreate) -> CategoryInDB:
        """Создание новой категории"""
        db_category = Category(**category_data.dict())
        self.db.add(db_category)
        await self.db.commit()
        await self.db.refresh(db_category)
        return CategoryInDB.from_orm(db_category)

    async def get_category(self, category_id: int) -> Optional[CategoryInDB]:
        """Получение категории по ID"""
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        category = result.scalars().first()
        return CategoryInDB.from_orm(category) if category else None

    async def get_categories_by_ids(self, category_ids: List[int]) -> List[Category]:
        """Получение списка категорий по ID"""
        if not category_ids:
            return []
            
        result = await self.db.execute(
            select(Category).where(Category.id.in_(category_ids))
        )
        return result.scalars().all()

    async def list_categories(
        self, skip: int = 0, limit: int = 100, is_active: bool = True
    ) -> List[CategoryInDB]:
        """Получение списка категорий"""
        query = select(Category)
        
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
            
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        return [CategoryInDB.from_orm(cat) for cat in categories]

    # ===== MEDIA =====
    
    async def add_media(
        self, place_id: int, file_id: str, file_type: str, url: str, uploaded_by: int, is_cover: bool = False
    ) -> Dict[str, Any]:
        """Добавление медиа-файла к заведению"""
        # Если новая обложка, снимаем флаг с предыдущей
        if is_cover:
            await self.db.execute(
                update(Media)
                .where(and_(Media.place_id == place_id, Media.is_cover == True))
                .values(is_cover=False)
            )
        
        db_media = Media(
            file_id=file_id,
            file_type=file_type,
            url=url,
            place_id=place_id,
            uploaded_by=uploaded_by,
            is_cover=is_cover
        )
        
        self.db.add(db_media)
        await self.db.commit()
        await self.db.refresh(db_media)
        
        return {
            "id": db_media.id,
            "url": db_media.url,
            "is_cover": db_media.is_cover
        }

    async def set_cover_media(self, media_id: int, place_id: int, user_id: int) -> bool:
        """Установка медиа-файла в качестве обложки"""
        # Снимаем флаг обложки со всех файлов места
        await self.db.execute(
            update(Media)
            .where(and_(
                Media.place_id == place_id,
                Media.is_cover == True
            ))
            .values(is_cover=False)
        )
        
        # Устанавливаем новый файл как обложку
        result = await self.db.execute(
            update(Media)
            .where(and_(
                Media.id == media_id,
                Media.place_id == place_id,
                Media.uploaded_by == user_id
            ))
            .values(is_cover=True)
            .returning(Media.id)
        )
        
        await self.db.commit()
        return result.scalar() is not None

    async def delete_media(self, media_id: int, user_id: int) -> bool:
        """Удаление медиа-файла"""
        # TODO: Добавить удаление файла из хранилища
        result = await self.db.execute(
            delete(Media)
            .where(and_(
                Media.id == media_id,
                Media.uploaded_by == user_id
            ))
        )
        await self.db.commit()
        return result.rowcount > 0

    # ===== REVIEWS =====
    
    async def create_review(
        self, place_id: int, user_id: int, rating: int, comment: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создание отзыва о заведении"""
        # Проверяем, не оставлял ли пользователь отзыв ранее
        existing = await self.db.execute(
            select(Review)
            .where(and_(
                Review.place_id == place_id,
                Review.user_id == user_id
            ))
        )
        
        if existing.scalars().first():
            raise ValueError("Вы уже оставляли отзыв об этом заведении")
        
        # Создаем отзыв
        db_review = Review(
            place_id=place_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )
        
        self.db.add(db_review)
        
        # Обновляем рейтинг заведения
        await self.update_place_rating(place_id)
        
        await self.db.commit()
        await self.db.refresh(db_review)
        
        return {
            "id": db_review.id,
            "rating": db_review.rating,
            "comment": db_review.comment,
            "created_at": db_review.created_at
        }
    
    async def update_place_rating(self, place_id: int) -> None:
        """Обновление рейтинга заведения на основе отзывов"""
        # Получаем средний рейтинг и количество отзывов
        result = await self.db.execute(
            select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("reviews_count")
            )
            .where(Review.place_id == place_id)
        )
        
        stats = result.first()
        
        # Обновляем запись заведения
        if stats and stats.avg_rating is not None:
            await self.db.execute(
                update(Place)
                .where(Place.id == place_id)
                .values(
                    rating=float(stats.avg_rating),
                    reviews_count=stats.reviews_count
                )
            )
            
        await self.db.commit()
