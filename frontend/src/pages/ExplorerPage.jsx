import React, { useEffect, useState } from 'react'
import { getLines } from '../api'

export default function ExplorerPage() {
  const [lines, setLines] = useState([])
  const [skip, setSkip] = useState(0)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const limit = 50

  const load = async (offset) => {
    setLoading(true)
    try {
      const res = await getLines({ skip: offset, limit })
      const data = res.data || []
      if (offset === 0) {
        setLines(data)
      } else {
        setLines((prev) => [...prev, ...data])
      }
      setHasMore(data.length === limit)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load(0)
  }, [])

  const handleLoadMore = () => {
    const next = skip + limit
    setSkip(next)
    load(next)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-display text-accent2 tracking-wide">Subtitle Explorer</h2>
        <span className="text-xs text-muted">{lines.length} lines shown</span>
      </div>

      <div className="bg-panel rounded-xl border border-accent2/20 overflow-hidden">
        <div className="max-h-[32rem] overflow-y-auto p-4 space-y-2">
          {lines.map((line) => (
            <div
              key={line.idx}
              className="rounded-lg border border-accent2/10 hover:border-accent/30 transition-colors p-3 bg-surface/40"
            >
              <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-muted mb-1">
                <span className="text-accent">#{line.idx}</span>
                <span>•</span>
                <span>{fmtTime(line.start_time)} - {fmtTime(line.end_time)}</span>
                {line.speaker && <>
                  <span>•</span>
                  <span className="text-accent2">{line.speaker}</span>
                </>}
                <span>•</span>
                <span>{typeLabel(line.line_type)}</span>
              </div>
              <p className="text-sm leading-relaxed">{line.raw_text}</p>
              {line.sentiment_compound != null && (
                <div className="mt-2 flex items-center gap-2">
                  <div className="w-24 h-1.5 rounded-full bg-muted/20 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-accent"
                      style={{
                        width: `${((line.sentiment_compound + 1) / 2) * 100}%`,
                        backgroundColor: sentimentColor(line.sentiment_compound),
                      }}
                    />
                  </div>
                  <span className="text-[10px] text-muted">{line.sentiment_compound.toFixed(3)}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <button
          onClick={handleLoadMore}
          disabled={loading || !hasMore}
          className={`px-6 py-2 rounded-md text-sm font-bold tracking-wide ${
            loading || !hasMore
              ? 'bg-muted/20 text-muted cursor-not-allowed'
              : 'bg-panel border border-accent2/30 text-accent hover:border-accent'
          }`}
        >
          {loading ? 'Loading...' : hasMore ? 'Load More' : 'End of transcript'}
        </button>
      </div>
    </div>
  )
}

function fmtTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.floor(totalSeconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function typeLabel(type) {
  const map = {
    dialogue: 'Dialogue',
    sound_effect: 'SFX',
    narration: 'Narration',
    song: 'Song',
    other: 'Other',
  }
  return map[type] || type
}

function sentimentColor(v) {
  if (v >= 0.5) return '#2ecc71'
  if (v >= 0.1) return '#45a29e'
  if (v >= -0.1) return '#c5c6c7'
  if (v >= -0.5) return '#e67e22'
  return '#e74c3c'
}
