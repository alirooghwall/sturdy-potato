"""Entity management endpoints."""

from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.models.domain import Entity, GeoPoint
from src.models.enums import EntityStatus, EntityType
from src.schemas.api import (
    ApiResponse,
    EntityCreateSchema,
    EntityResponseSchema,
    EntityUpdateSchema,
    GeoPointSchema,
    LinksSchema,
    MetaSchema,
    PaginationSchema,
)

from .auth import get_current_user_payload, require_permission

router = APIRouter()

# In-memory storage for demo (use database in production)
_entities: dict[UUID, Entity] = {}


def _entity_to_response(entity: Entity) -> EntityResponseSchema:
    """Convert domain entity to response schema."""
    position = None
    if entity.current_position:
        position = GeoPointSchema(
            latitude=entity.current_position.latitude,
            longitude=entity.current_position.longitude,
            altitude=entity.current_position.altitude,
            accuracy=entity.current_position.accuracy,
        )

    return EntityResponseSchema(
        entity_id=entity.entity_id,
        entity_type=entity.entity_type,
        entity_subtype=entity.entity_subtype,
        display_name=entity.display_name,
        status=entity.status,
        confidence_score=entity.confidence_score,
        first_observed=entity.first_observed,
        last_observed=entity.last_observed,
        current_position=position,
        attributes=entity.attributes,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get("", response_model=ApiResponse[list[EntityResponseSchema]])
async def list_entities(
    user: Annotated[dict, Depends(require_permission("entity:read"))],
    entity_type: EntityType | None = None,
    status: EntityStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[EntityResponseSchema]]:
    """List entities with optional filtering."""
    # Filter entities
    filtered = list(_entities.values())

    if entity_type:
        filtered = [e for e in filtered if e.entity_type == entity_type]

    if status:
        filtered = [e for e in filtered if e.status == status]

    # Paginate
    total = len(filtered)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = filtered[start:end]

    # Convert to response
    entities = [_entity_to_response(e) for e in paginated]

    return ApiResponse(
        data=entities,
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
            pagination=PaginationSchema(
                page=page,
                page_size=page_size,
                total_items=total,
                total_pages=(total + page_size - 1) // page_size,
            ),
        ),
    )


@router.post("", response_model=ApiResponse[EntityResponseSchema], status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity_data: EntityCreateSchema,
    user: Annotated[dict, Depends(require_permission("entity:read"))],
) -> ApiResponse[EntityResponseSchema]:
    """Create a new entity."""
    # Create position if provided
    position = None
    if entity_data.current_position:
        position = GeoPoint(
            latitude=entity_data.current_position.latitude,
            longitude=entity_data.current_position.longitude,
            altitude=entity_data.current_position.altitude,
            accuracy=entity_data.current_position.accuracy,
        )

    # Create entity
    entity = Entity(
        entity_id=uuid4(),
        entity_type=entity_data.entity_type,
        entity_subtype=entity_data.entity_subtype,
        display_name=entity_data.display_name,
        status=entity_data.status,
        confidence_score=entity_data.confidence_score,
        current_position=position,
        attributes=entity_data.attributes,
    )

    # Store entity
    _entities[entity.entity_id] = entity

    return ApiResponse(
        data=_entity_to_response(entity),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.get("/{entity_id}", response_model=ApiResponse[EntityResponseSchema])
async def get_entity(
    entity_id: UUID,
    user: Annotated[dict, Depends(require_permission("entity:read"))],
) -> ApiResponse[EntityResponseSchema]:
    """Get entity by ID."""
    entity = _entities.get(entity_id)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )

    return ApiResponse(
        data=_entity_to_response(entity),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.patch("/{entity_id}", response_model=ApiResponse[EntityResponseSchema])
async def update_entity(
    entity_id: UUID,
    entity_data: EntityUpdateSchema,
    user: Annotated[dict, Depends(require_permission("entity:read"))],
) -> ApiResponse[EntityResponseSchema]:
    """Update an entity."""
    entity = _entities.get(entity_id)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )

    # Update fields
    if entity_data.entity_subtype is not None:
        entity.entity_subtype = entity_data.entity_subtype

    if entity_data.display_name is not None:
        entity.display_name = entity_data.display_name

    if entity_data.status is not None:
        entity.status = entity_data.status

    if entity_data.confidence_score is not None:
        entity.confidence_score = entity_data.confidence_score

    if entity_data.current_position is not None:
        entity.current_position = GeoPoint(
            latitude=entity_data.current_position.latitude,
            longitude=entity_data.current_position.longitude,
            altitude=entity_data.current_position.altitude,
            accuracy=entity_data.current_position.accuracy,
        )

    if entity_data.attributes is not None:
        entity.attributes.update(entity_data.attributes)

    entity.updated_at = datetime.utcnow()
    entity.last_observed = datetime.utcnow()

    return ApiResponse(
        data=_entity_to_response(entity),
        meta=MetaSchema(
            request_id=str(uuid4()),
            timestamp=datetime.utcnow(),
        ),
    )


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entity(
    entity_id: UUID,
    user: Annotated[dict, Depends(require_permission("entity:read"))],
) -> None:
    """Delete an entity (soft delete)."""
    entity = _entities.get(entity_id)

    if not entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found",
        )

    # Soft delete
    entity.status = EntityStatus.ARCHIVED
    entity.updated_at = datetime.utcnow()
