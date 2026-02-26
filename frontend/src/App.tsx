import { Navigate, NavLink, Route, Routes } from 'react-router-dom'

import { AddPlacePage } from './pages/AddPlacePage'
import { EditPlacePage } from './pages/EditPlacePage'
import { PlaceDetailLitePage } from './pages/PlaceDetailLitePage'
import { RecentPlacesPage } from './pages/RecentPlacesPage'

function NotFoundPage() {
  return (
    <section className="page">
      <h1>페이지를 찾을 수 없습니다.</h1>
      <NavLink className="button" to="/places/recent">
        최근 목록으로 이동
      </NavLink>
    </section>
  )
}

function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink className="brand" to="/places/recent">
          MySpot
        </NavLink>
        <nav className="nav-row">
          <NavLink
            to="/places/recent"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          >
            최근 조회
          </NavLink>
          <NavLink
            to="/places/add"
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          >
            장소 입력
          </NavLink>
        </nav>
      </header>

      <main className="app-main">
        <Routes>
          <Route path="/" element={<Navigate to="/places/recent" replace />} />
          <Route path="/places/recent" element={<RecentPlacesPage />} />
          <Route path="/places/add" element={<AddPlacePage />} />
          <Route path="/places/:placeId/edit" element={<EditPlacePage />} />
          <Route path="/places/:placeId" element={<PlaceDetailLitePage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
