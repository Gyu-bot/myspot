import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { createNote, updateNote } from '../api/notes'
import { getPlaceDetail } from '../api/places'

function renderList(items: string[] | null): string {
  if (!items || items.length === 0) return '-'
  return items.join(', ')
}

export function PlaceDetailLitePage() {
  const { placeId } = useParams<{ placeId: string }>()

  const [editingNoteId, setEditingNoteId] = useState<string | null>(null)
  const [noteDraft, setNoteDraft] = useState('')
  const [newNoteDraft, setNewNoteDraft] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [noteError, setNoteError] = useState<string | null>(null)

  const query = useQuery({
    queryKey: ['place', placeId],
    queryFn: () => getPlaceDetail(placeId ?? ''),
    enabled: Boolean(placeId),
  })

  async function saveNoteEdit(noteId: string): Promise<void> {
    if (!noteDraft.trim()) {
      setNoteError('메모 내용은 비울 수 없습니다.')
      return
    }

    setIsSubmitting(true)
    setNoteError(null)

    try {
      await updateNote(noteId, { content: noteDraft.trim() })
      await query.refetch()
      setEditingNoteId(null)
      setNoteDraft('')
    } catch (error) {
      setNoteError(error instanceof Error ? error.message : '메모 수정 실패')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function addNote(): Promise<void> {
    if (!placeId) return
    if (!newNoteDraft.trim()) return

    setIsSubmitting(true)
    setNoteError(null)

    try {
      await createNote({ place_id: placeId, content: newNoteDraft.trim() })
      await query.refetch()
      setNewNoteDraft('')
    } catch (error) {
      setNoteError(error instanceof Error ? error.message : '메모 추가 실패')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!placeId) {
    return <p className="error">잘못된 접근입니다.</p>
  }

  if (query.isLoading) {
    return <p>상세 정보를 불러오는 중...</p>
  }

  if (query.isError) {
    return <p className="error">상세 조회 실패: {query.error.message}</p>
  }

  const place = query.data
  if (!place) {
    return <p>데이터가 없습니다.</p>
  }

  return (
    <section className="page">
      <header className="page-header">
        <h1>{place.canonical_name}</h1>
        <div className="button-row">
          <Link className="button" to="/places/recent">
            목록으로
          </Link>
          <Link className="button button-primary" to={`/places/${place.id}/edit`}>
            정보 수정
          </Link>
        </div>
      </header>

      <div className="detail-grid">
        <p>
          <strong>주소:</strong> {place.address_road ?? place.address_jibun ?? '-'}
        </p>
        <p>
          <strong>전화번호:</strong> {place.phone ?? '-'}
        </p>
        <p>
          <strong>카테고리:</strong> {place.category_primary ?? '-'} / {place.category_secondary ?? '-'}
        </p>
        <p>
          <strong>평점:</strong> {place.user_rating ?? '-'}
        </p>
        <p>
          <strong>무드:</strong> {renderList(place.mood)}
        </p>
        <p>
          <strong>상황:</strong> {renderList(place.situations)}
        </p>
      </div>

      <section className="section-box">
        <h2>태그</h2>
        {place.tags.length === 0 ? (
          <p className="muted">태그 없음</p>
        ) : (
          <div className="tag-wrap">
            {place.tags.map((tag) => (
              <span key={tag.id} className="pill">
                {tag.name}
              </span>
            ))}
          </div>
        )}
      </section>

      <section className="section-box">
        <h2>메모</h2>
        {noteError ? <p className="error">{noteError}</p> : null}

        {place.notes.length === 0 ? <p className="muted">메모 없음</p> : null}
        <ul>
          {place.notes.map((note) => (
            <li key={note.id}>
              {editingNoteId === note.id ? (
                <div className="form-inline">
                  <textarea
                    rows={3}
                    value={noteDraft}
                    onChange={(event) => setNoteDraft(event.target.value)}
                  />
                  <div className="button-row">
                    <button
                      className="button button-primary"
                      type="button"
                      onClick={() => saveNoteEdit(note.id)}
                      disabled={isSubmitting}
                    >
                      저장
                    </button>
                    <button
                      className="button"
                      type="button"
                      onClick={() => {
                        setEditingNoteId(null)
                        setNoteDraft('')
                      }}
                      disabled={isSubmitting}
                    >
                      취소
                    </button>
                  </div>
                </div>
              ) : (
                <div className="note-row">
                  <span>{note.content}</span>
                  <button
                    className="button"
                    type="button"
                    onClick={() => {
                      setEditingNoteId(note.id)
                      setNoteDraft(note.content)
                    }}
                  >
                    수정
                  </button>
                </div>
              )}
            </li>
          ))}
        </ul>

        <div className="form-inline">
          <textarea
            rows={3}
            value={newNoteDraft}
            onChange={(event) => setNewNoteDraft(event.target.value)}
            placeholder="새 메모 추가"
          />
          <div className="button-row">
            <button
              className="button button-primary"
              type="button"
              onClick={addNote}
              disabled={isSubmitting || !newNoteDraft.trim()}
            >
              메모 추가
            </button>
          </div>
        </div>
      </section>

      <section className="section-box">
        <h2>근거 자료</h2>
        {place.sources.length === 0 ? (
          <p className="muted">근거 자료 없음</p>
        ) : (
          <ul>
            {place.sources.map((source) => (
              <li key={source.id}>
                {source.title ?? source.url ?? source.type}
                {source.url ? (
                  <>
                    {' '}
                    <a href={source.url} target="_blank" rel="noreferrer">
                      링크
                    </a>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="section-box">
        <h2>방문 기록</h2>
        {place.visits.length === 0 ? (
          <p className="muted">방문 기록 없음</p>
        ) : (
          <ul>
            {place.visits.map((visit) => (
              <li key={visit.id}>
                {visit.visited_at} / 평점 {visit.rating ?? '-'} / 메모 {visit.memo ?? '-'}
              </li>
            ))}
          </ul>
        )}
      </section>
    </section>
  )
}
