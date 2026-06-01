import React, { useState } from 'react'
import { searchSemantic, searchText, getSpeakers } from '../api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [mode, setMode] = useState('semantic') // semantic | text
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState(null)
  const [speakers, setSpeakers] = useState([])
  const [selectedSpeaker, setSelectedSpeaker] = useState('')

  React.useEffect(() => {
    getSpeakers().then(r => setSpeakers(r.data || []))
  }, [])

  const runSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const params = { q: query.trim(), limit: 15, speaker: selectedSpeaker || undefined }
      const res = mode === 'semantic' ? await searchSemantic(params) : await searchText(params)
      setResults(res.data)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={runSearch} className="bg-panel rounded-xl p-4 border border-accent2/20 space-y-4">
        <div className="flex flex-col md:flex-row gap-3">
          <div className="flex-1">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across subtitles..."
              className="w-full bg-surface border border-accent2/30 rounded-md px-4 py-3 text-sm focus:outline-none focus:border-accent placeholder:text-muted"
            />
          </div>
          <select
            className="bg-surface border border-accent2/30 rounded-md px-3 py-3 text-sm"
            value={selectedSpeaker}
            onChange={(e) => setSelectedSpeaker(e.target.value)}
          >
            <option value="">All Speakers</option>
            {speakers.map((s) => (
              <option key={s.speaker} value={s.speaker}>{s.speaker}</option>
            ))}
          </select>
          <button
            type="submit"
            disabled={loading}
            className={`px-6 py-3 rounded-md text-sm font-bold tracking-wide ${
              loading
                ? 'bg-muted/20 text-muted cursor-not-allowed'
                : 'bg-accent text-surface hover:bg-accent2'
            }`}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        <div className="flex gap-2">
          {['semantic', 'text'].map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={
                `px-3 py-1.5 rounded-md text-xs font-bold border transition-colors uppercase tracking-wider ` +
                (mode === m
                  ? 'bg-accent text-surface border-accent'
                  : 'bg-surface text-muted border-accent2/30 hover:text-accent')
              }
            >
              {m === 'semantic' ? 'Semantic (pgvector)' : 'Text Match'}
            </button>
          ))}
        </div>
      </form>

      {results && (
        <div className="space-y-3">
          <div className="text-xs uppercase tracking-widest text-muted">
            {results.results.length} result{results.results.length !== 1 ? 's' : ''} for "{results.query}"
          </div>
          {results.results.map((r) => (
            <div key={r.idx} className="bg-panel rounded-xl p-4 border border-accent2/20 hover:border-accent/40 transition-colors">
              <div className="flex items-center justify-between text-xs text-muted mb-2">
                <div className="flex items-center gap-2">
                  <span className="bg-accent/10 text-accent px-2 py-0.5 rounded-md">#{r.idx}</span>
                  {r.speaker && <span className="bg-accent2/10 text-accent2 px-2 py-0.5 rounded-md">{r.speaker}</span>}
                  {r.similarity != null && (
                    <span className="bg-success/10 text-success px-2 py-0.5 rounded-md">
                      similarity {(r.similarity * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                <span>{fmtTime(r.start_time)} - {fmtTime(r.end_time)}</span>
              </div>
              <p className="text-sm leading-relaxed mb-1">{r.raw_text}</p>
              <p className="text-xs text-muted italic">{r.clean_text}</p>
            </div>
          ))}
        </div>
      )}

      {!results && !loading && (
        <div className="bg-panel rounded-xl p-8 border border-accent2/20 text-center text-muted">
          <p className="mb-2">Try searching for concepts like:</p>
          <div className="flex flex-wrap justify-center gap-2">
            {["spaceship", "failure", "velocity", " question", " oxygen", "sun"].map((s) => (
              <button
                key={s}
                onClick={() => { setQuery(s); setResults(null) }}
                className="text-xs bg-surface border border-accent2/20 px-3 py-1 rounded-full hover:border-accent hover:text-accent transition-colors"
              >
                {s.trim()}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function fmtTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.floor(totalSeconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}
