import { useQuery } from '@tanstack/react-query'
import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { getPlaceDetail, updatePlace } from '../api/places'
import type { PlaceDetail, PlaceUpdatePayload } from '../api/types'

interface EditPlaceFormState {
  canonicalName: string
  addressRoad: string
  phone: string
  categoryPrimary: string
  lat: string
  lng: string
  tags: string
  isFavorite: boolean
  userRating: string
}

const initialState: EditPlaceFormState = {
  canonicalName: '',
  addressRoad: '',
  phone: '',
  categoryPrimary: '',
  lat: '',
  lng: '',
  tags: '',
  isFavorite: false,
  userRating: '',
}

function splitComma(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function toForm(place: PlaceDetail): EditPlaceFormState {
  return {
    canonicalName: place.canonical_name,
    addressRoad: place.address_road ?? '',
    phone: place.phone ?? '',
    categoryPrimary: place.category_primary ?? '',
    lat: '',
    lng: '',
    tags: place.tags.map((tag) => tag.name).join(', '),
    isFavorite: place.is_favorite,
    userRating: place.user_rating ? String(place.user_rating) : '',
  }
}

export function EditPlacePage() {
  const { placeId } = useParams<{ placeId: string }>()
  const navigate = useNavigate()

  const [form, setForm] = useState<EditPlaceFormState>(initialState)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const query = useQuery({
    queryKey: ['place', placeId],
    queryFn: () => getPlaceDetail(placeId ?? ''),
    enabled: Boolean(placeId),
  })

  useEffect(() => {
    if (query.data) {
      setForm(toForm(query.data))
    }
  }, [query.data])

  const payload = useMemo<PlaceUpdatePayload | null>(() => {
    const lat = form.lat.trim() ? Number(form.lat.trim()) : undefined
    const lng = form.lng.trim() ? Number(form.lng.trim()) : undefined
    const userRating = form.userRating.trim() ? Number(form.userRating.trim()) : undefined

    return {
      canonical_name: form.canonicalName.trim() || undefined,
      address_road: form.addressRoad.trim() || undefined,
      phone: form.phone.trim() || undefined,
      category_primary: form.categoryPrimary.trim() || undefined,
      lat: Number.isFinite(lat) ? lat : undefined,
      lng: Number.isFinite(lng) ? lng : undefined,
      tags: splitComma(form.tags),
      is_favorite: form.isFavorite,
      user_rating: Number.isFinite(userRating) ? userRating : undefined,
    }
  }, [form])

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()

    if (!placeId) return
    if (!payload?.canonical_name) {
      setError('장소명은 필수입니다.')
      return
    }

    setError(null)
    setIsSaving(true)

    try {
      await updatePlace(placeId, payload)
      navigate(`/places/${placeId}`)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : '수정 실패')
    } finally {
      setIsSaving(false)
    }
  }

  if (!placeId) {
    return <p className="error">잘못된 접근입니다.</p>
  }

  if (query.isLoading) {
    return <p>수정 데이터를 불러오는 중...</p>
  }

  if (query.isError) {
    return <p className="error">조회 실패: {query.error.message}</p>
  }

  return (
    <section className="page">
      <header className="page-header">
        <h1>장소 정보 수정</h1>
        <Link className="button" to={`/places/${placeId}`}>
          상세로
        </Link>
      </header>

      <form className="form" onSubmit={onSubmit}>
        <label>
          장소명 *
          <input
            value={form.canonicalName}
            onChange={(event) => setForm((prev) => ({ ...prev, canonicalName: event.target.value }))}
            required
          />
        </label>

        <label>
          도로명 주소
          <input
            value={form.addressRoad}
            onChange={(event) => setForm((prev) => ({ ...prev, addressRoad: event.target.value }))}
          />
        </label>

        <label>
          전화번호
          <input
            value={form.phone}
            onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
          />
        </label>

        <label>
          1차 카테고리
          <input
            value={form.categoryPrimary}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, categoryPrimary: event.target.value }))
            }
          />
        </label>

        <div className="grid-two">
          <label>
            위도 (선택)
            <input
              value={form.lat}
              onChange={(event) => setForm((prev) => ({ ...prev, lat: event.target.value }))}
              placeholder="새 좌표를 입력할 때만 작성"
            />
          </label>
          <label>
            경도 (선택)
            <input
              value={form.lng}
              onChange={(event) => setForm((prev) => ({ ...prev, lng: event.target.value }))}
              placeholder="새 좌표를 입력할 때만 작성"
            />
          </label>
        </div>

        <label>
          태그 (쉼표 구분)
          <input
            value={form.tags}
            onChange={(event) => setForm((prev) => ({ ...prev, tags: event.target.value }))}
          />
        </label>

        <div className="grid-two">
          <label>
            즐겨찾기
            <input
              type="checkbox"
              checked={form.isFavorite}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, isFavorite: event.target.checked }))
              }
            />
          </label>
          <label>
            사용자 평점 (1~5)
            <input
              value={form.userRating}
              onChange={(event) => setForm((prev) => ({ ...prev, userRating: event.target.value }))}
              placeholder="예: 4"
            />
          </label>
        </div>

        {error ? <p className="error">{error}</p> : null}

        <div className="button-row">
          <button type="submit" className="button button-primary" disabled={isSaving}>
            {isSaving ? '저장 중...' : '수정 저장'}
          </button>
        </div>
      </form>
    </section>
  )
}
