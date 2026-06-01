import React from 'react'
import { Routes, Route, NavLink } from 'react-router-dom'
import Overview from './pages/Overview'
import TimelinePage from './pages/TimelinePage'
import SpeakersPage from './pages/SpeakersPage'
import SearchPage from './pages/SearchPage'
import ExplorerPage from './pages/ExplorerPage'

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-4 py-2 rounded-md text-sm font-bold tracking-wide transition-colors ` +
        (isActive
          ? 'bg-accent text-surface'
          : 'text-muted hover:text-accent hover:bg-panel')
      }
    >
      {children}
    </NavLink>
  )
}

export default function App() {
  return (
    <div className="min-h-screen grid-bg flex flex-col">
      <header className="border-b border-panel bg-surface/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent to-accent2 flex items-center justify-center text-surface font-black text-lg">
              H
            </div>
            <div>
              <h1 className="text-accent text-lg leading-none tracking-wider font-display">
                PROJECT HAIL MARY
              </h1>
              <p className="text-[10px] text-muted tracking-[0.2em] uppercase">
                Subtitle Intelligence Dashboard
              </p>
            </div>
          </div>
          <nav className="hidden md:flex items-center gap-1">
            <NavItem to="/">Overview</NavItem>
            <NavItem to="/timeline">Timeline</NavItem>
            <NavItem to="/speakers">Speakers</NavItem>
            <NavItem to="/search">Search</NavItem>
            <NavItem to="/explorer">Explorer</NavItem>
          </nav>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 py-6">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/timeline" element={<TimelinePage />} />
          <Route path="/speakers" element={<SpeakersPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/explorer" element={<ExplorerPage />} />
        </Routes>
      </main>

      <footer className="border-t border-panel bg-surface/80 backdrop-blur mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between text-xs text-muted">
          <span>FastAPI + React + pgvector</span>
          <span>Self-hosted on Proxmox LXC</span>
        </div>
      </footer>
    </div>
  )
}
