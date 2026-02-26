import { fetchApi } from './client'
import type {
  DuplicateCandidate,
  DuplicateCheckPayload,
  PaginatedResponse,
  PlaceBrief,
  PlaceCreatePayload,
  PlaceCreateResponse,
  PlaceDetail,
  PlaceResponse,
  PlaceUpdatePayload,
} from './types'

interface ListPlacesParams {
  cursor?: string
  limit?: number
  categoryPrimary?: string
  isFavorite?: boolean
}

export async function listPlaces(
  params: ListPlacesParams = {},
): Promise<PaginatedResponse<PlaceBrief>> {
  const query = new URLSearchParams()

  if (params.cursor) query.set('cursor', params.cursor)
  if (params.limit) query.set('limit', String(params.limit))
  if (params.categoryPrimary) query.set('category_primary', params.categoryPrimary)
  if (params.isFavorite !== undefined) query.set('is_favorite', String(params.isFavorite))

  const suffix = query.toString() ? `?${query.toString()}` : ''
  return fetchApi<PaginatedResponse<PlaceBrief>>(`/api/v1/places${suffix}`)
}

export async function getPlaceDetail(placeId: string): Promise<PlaceDetail> {
  return fetchApi<PlaceDetail>(`/api/v1/places/${placeId}`)
}

export async function checkDuplicates(
  payload: DuplicateCheckPayload,
): Promise<DuplicateCandidate[]> {
  return fetchApi<DuplicateCandidate[]>('/api/v1/places/check-duplicates', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function createPlace(
  payload: PlaceCreatePayload,
): Promise<PlaceCreateResponse> {
  return fetchApi<PlaceCreateResponse>('/api/v1/places', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function updatePlace(
  placeId: string,
  payload: PlaceUpdatePayload,
): Promise<PlaceResponse> {
  return fetchApi<PlaceResponse>(`/api/v1/places/${placeId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  })
}
