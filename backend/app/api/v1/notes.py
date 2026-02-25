"""Notes API endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteResponse, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(payload: NoteCreate, db: AsyncSession = Depends(get_db)) -> NoteResponse:
    """Create note."""
    note = Note(**payload.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.get("", response_model=list[NoteResponse])
async def list_notes(place_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> list[NoteResponse]:
    """List notes by place."""
    stmt = select(Note).where(Note.place_id == place_id).order_by(Note.created_at.desc(), Note.id.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [NoteResponse.model_validate(row) for row in rows]


@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: uuid.UUID, payload: NoteUpdate, db: AsyncSession = Depends(get_db)) -> NoteResponse:
    """Update note content."""
    note = await db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    note.content = payload.content
    await db.commit()
    await db.refresh(note)
    return NoteResponse.model_validate(note)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Response:
    """Delete note."""
    note = await db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")

    await db.delete(note)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
