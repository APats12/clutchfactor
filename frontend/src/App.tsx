import { Route, Routes } from 'react-router-dom'
import { Layout } from './components/layout/Layout'
import { GamesPage } from './pages/GamesPage'
import { GameDetailPage } from './pages/GameDetailPage'

export function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<GamesPage />} />
        <Route path="/games/:id" element={<GameDetailPage />} />
      </Routes>
    </Layout>
  )
}
