import { useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'

import { checkDuplicates, createPlace } from '../api/places'
import type { DuplicateCandidate, PlaceCreatePayload } from '../api/types'

interface AddPlaceFormState {
  canonicalName: string
  addressRoad: string
  phone: string
  categoryPrimary: string
  lat: string
  lng: string
  tags: string
  notes: string
}

const initialState: AddPlaceFormState = {
  canonicalName: '',
  addressRoad: '',
  phone: '',
  categoryPrimary: '',
  lat: '',
  lng: '',
  tags: '',
  notes: '',
}

function splitComma(value: string): string[] {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function splitLines(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function AddPlacePage() {
  const navigate = useNavigate()

  const [form, setForm] = useState<AddPlaceFormState>(initialState)
  const [duplicates, setDuplicates] = useState<DuplicateCandidate[]>([])
  const [isCheckingDuplicates, setIsCheckingDuplicates] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const payload = useMemo<PlaceCreatePayload | null>(() => {
    if (!form.canonicalName.trim()) return null

    const lat = form.lat.trim() ? Number(form.lat.trim()) : undefined
    const lng = form.lng.trim() ? Number(form.lng.trim()) : undefined

    return {
      canonical_name: form.canonicalName.trim(),
      address_road: form.addressRoad.trim() || undefined,
      phone: form.phone.trim() || undefined,
      category_primary: form.categoryPrimary.trim() || undefined,
      lat: Number.isFinite(lat) ? lat : undefined,
      lng: Number.isFinite(lng) ? lng : undefined,
      tags: splitComma(form.tags),
      notes: splitLines(form.notes),
    }
  }, [form])

  async function onCheckDuplicates(): Promise<void> {
    if (!payload) {
      setError('장소명은 필수입니다.')
      return
    }

    setError(null)
    setIsCheckingDuplicates(true)

    try {
      const candidates = await checkDuplicates({
        canonical_name: payload.canonical_name,
        address_road: payload.address_road,
        phone: payload.phone,
        lat: payload.lat,
        lng: payload.lng,
      })
      setDuplicates(candidates)
    } catch (checkError) {
      setError(checkError instanceof Error ? checkError.message : '중복 확인 실패')
    } finally {
      setIsCheckingDuplicates(false)
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault()
    if (!payload) {
      setError('장소명은 필수입니다.')
      return
    }

    setError(null)
    setIsSaving(true)

    try {
      const result = await createPlace(payload)
      setDuplicates(result.duplicate_candidates)
      navigate(`/places/${result.place.id}`)
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : '장소 저장 실패')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <section className="page">
      <header className="page-header">
        <h1>장소 수동 입력</h1>
      </header>

      <form className="form" onSubmit={onSubmit}>
        <label>
          장소명 *
          <input
            value={form.canonicalName}
            onChange={(event) => setForm((prev) => ({ ...prev, canonicalName: event.target.value }))}
            placeholder="예: 합정 모모카페"
            required
          />
        </label>

        <label>
          도로명 주소
          <input
            value={form.addressRoad}
            onChange={(event) => setForm((prev) => ({ ...prev, addressRoad: event.target.value }))}
            placeholder="예: 서울 마포구 ..."
          />
        </label>

        <label>
          전화번호
          <input
            value={form.phone}
            onChange={(event) => setForm((prev) => ({ ...prev, phone: event.target.value }))}
            placeholder="예: 02-123-4567"
          />
        </label>

        <label>
          1차 카테고리
          <input
            value={form.categoryPrimary}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, categoryPrimary: event.target.value }))
            }
            placeholder="예: 카페"
          />
        </label>

        <div className="grid-two">
          <label>
            위도 (lat)
            <input
              value={form.lat}
              onChange={(event) => setForm((prev) => ({ ...prev, lat: event.target.value }))}
              placeholder="예: 37.551"
            />
          </label>
          <label>
            경도 (lng)
            <input
              value={form.lng}
              onChange={(event) => setForm((prev) => ({ ...prev, lng: event.target.value }))}
              placeholder="예: 126.922"
            />
          </label>
        </div>

        <label>
          태그 (쉼표 구분)
          <input
            value={form.tags}
            onChange={(event) => setForm((prev) => ({ ...prev, tags: event.target.value }))}
            placeholder="예: 조용함, 데이트"
          />
        </label>

        <label>
          메모 (줄바꿈 구분)
          <textarea
            value={form.notes}
            onChange={(event) => setForm((prev) => ({ ...prev, notes: event.target.value }))}
            rows={5}
            placeholder={'예:\n좌석 간격 넓음\n주말 혼잡'}
          />
        </label>

        {error ? <p className="error">{error}</p> : null}

        <div className="button-row">
          <button type="button" className="button" onClick={onCheckDuplicates} disabled={isCheckingDuplicates}>
            {isCheckingDuplicates ? '중복 확인 중...' : '중복 확인'}
          </button>
          <button type="submit" className="button button-primary" disabled={isSaving}>
            {isSaving ? '저장 중...' : '저장'}
          </button>
        </div>
      </form>

      <section className="section-box">
        <h2>중복 후보</h2>
        {duplicates.length === 0 ? (
          <p className="muted">중복 후보 없음</p>
        ) : (
          <ul>
            {duplicates.map((candidate) => (
              <li key={candidate.place_id}>
                <strong>{candidate.canonical_name}</strong> (score: {candidate.score}) /{' '}
                {candidate.reasons.join(', ')}
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  )
}
