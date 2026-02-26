export interface PaginatedResponse<T> {
  items: T[]
  next_cursor: string | null
  total: number | null
}

export interface TagResponse {
  id: string
  name: string
  type: string
  created_at: string
  updated_at: string
}

export interface ProviderLinkResponse {
  id: string
  provider: string
  provider_place_id: string | null
  provider_url: string | null
}

export interface SourceResponse {
  id: string
  place_id: string
  type: string
  url: string | null
  title: string | null
  snippet: string | null
  raw_text: string | null
  captured_at: string | null
  created_at: string
  updated_at: string
}

export interface NoteResponse {
  id: string
  place_id: string
  content: string
  created_at: string
  updated_at: string
}

export interface VisitResponse {
  id: string
  place_id: string
  visited_at: string
  rating: number | null
  with_whom: string | null
  situation: string | null
  memo: string | null
  revisit: boolean | null
  created_at: string
  updated_at: string
}

export interface PlaceBrief {
  id: string
  canonical_name: string
  category_primary: string | null
  is_favorite: boolean
  user_rating: number | null
  created_at: string
}

export interface PlaceResponse {
  id: string
  canonical_name: string
  normalized_name: string
  address_road: string | null
  address_jibun: string | null
  region_depth1: string | null
  region_depth2: string | null
  region_depth3: string | null
  phone: string | null
  category_primary: string | null
  category_secondary: string | null
  parking: boolean | null
  reservation: string | null
  price_range: string | null
  mood: string[] | null
  companions: string[] | null
  situations: string[] | null
  is_favorite: boolean
  user_rating: number | null
  created_at: string
  updated_at: string
  provider_links: ProviderLinkResponse[]
  tags: TagResponse[]
}

export interface PlaceDetail extends PlaceResponse {
  sources: SourceResponse[]
  notes: NoteResponse[]
  visits: VisitResponse[]
}

export interface DuplicateCandidate {
  place_id: string
  canonical_name: string
  score: number
  reasons: string[]
}

export interface PlaceCreateResponse {
  place: PlaceResponse
  duplicate_candidates: DuplicateCandidate[]
}

export interface PlaceCreatePayload {
  canonical_name: string
  address_road?: string
  address_jibun?: string
  region_depth1?: string
  region_depth2?: string
  region_depth3?: string
  lat?: number
  lng?: number
  phone?: string
  category_primary?: string
  category_secondary?: string
  parking?: boolean
  reservation?: string
  price_range?: string
  mood?: string[]
  companions?: string[]
  situations?: string[]
  is_favorite?: boolean
  user_rating?: number
  tags?: string[]
  notes?: string[]
}

export interface PlaceUpdatePayload {
  canonical_name?: string
  address_road?: string
  address_jibun?: string
  region_depth1?: string
  region_depth2?: string
  region_depth3?: string
  lat?: number
  lng?: number
  phone?: string
  category_primary?: string
  category_secondary?: string
  parking?: boolean
  reservation?: string
  price_range?: string
  mood?: string[]
  companions?: string[]
  situations?: string[]
  is_favorite?: boolean
  user_rating?: number
  tags?: string[]
}

export interface DuplicateCheckPayload {
  canonical_name: string
  address_road?: string
  lat?: number
  lng?: number
  phone?: string
}

export interface NoteCreatePayload {
  place_id: string
  content: string
}

export interface NoteUpdatePayload {
  content: string
}
