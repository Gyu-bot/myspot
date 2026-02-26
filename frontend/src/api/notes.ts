import { fetchApi } from './client'
import type { NoteCreatePayload, NoteResponse, NoteUpdatePayload } from './types'

export async function createNote(payload: NoteCreatePayload): Promise<NoteResponse> {
  return fetchApi<NoteResponse>('/api/v1/notes', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updateNote(
  noteId: string,
  payload: NoteUpdatePayload,
): Promise<NoteResponse> {
  return fetchApi<NoteResponse>(`/api/v1/notes/${noteId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
