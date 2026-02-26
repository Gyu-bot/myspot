import { useInfiniteQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'

import { listPlaces } from '../api/places'
import type { PlaceBrief } from '../api/types'

function formatDate(value: string): string {
  return new Date(value).toLocaleString('ko-KR')
}

export function RecentPlacesPage() {
  const query = useInfiniteQuery({
    queryKey: ['places', 'recent'],
    queryFn: ({ pageParam }) => listPlaces({ cursor: pageParam, limit: 20 }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
  })

  const places: PlaceBrief[] = query.data?.pages.flatMap((page) => page.items) ?? []

  return (
    <section className="page">
      <header className="page-header">
        <h1>최근 입력 장소</h1>
        <Link to="/places/add" className="button button-primary">
          장소 추가
        </Link>
      </header>

      {query.isLoading ? <p>로딩 중...</p> : null}
      {query.isError ? (
        <p className="error">목록을 불러오지 못했습니다: {query.error.message}</p>
      ) : null}

      {!query.isLoading && !query.isError && places.length === 0 ? (
        <p>아직 저장된 장소가 없습니다.</p>
      ) : null}

      <div className="card-list">
        {places.map((place) => (
          <article key={place.id} className="card">
            <div className="card-head">
              <h2>{place.canonical_name}</h2>
              {place.is_favorite ? <span className="pill">즐겨찾기</span> : null}
            </div>
            <p className="muted">카테고리: {place.category_primary ?? '미분류'}</p>
            <p className="muted">평점: {place.user_rating ?? '-'}</p>
            <p className="muted">등록: {formatDate(place.created_at)}</p>
            <Link className="link" to={`/places/${place.id}`}>
              상세 보기
            </Link>
          </article>
        ))}
      </div>

      {query.hasNextPage ? (
        <button
          className="button"
          type="button"
          onClick={() => query.fetchNextPage()}
          disabled={query.isFetchingNextPage}
        >
          {query.isFetchingNextPage ? '불러오는 중...' : '더 보기'}
        </button>
      ) : null}
    </section>
  )
}
