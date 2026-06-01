import React, { useEffect, useState } from 'react'
import { getSpeakers, getLines } from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'

export default function SpeakersPage() {
  const [speakers, setSpeakers] = useState([])
  const [selectedSpeaker, setSelectedSpeaker] = useState(null)
  const [speakerLines, setSpeakerLines] = useState([])
  const [sortBy, setSortBy] = useState('line_count')

  useEffect(() => {
    getSpeakers().then(r => {
      let list = r.data || []
      setSpeakers(list)
    })
  }, [])

  useEffect(() => {
    if (selectedSpeaker) {
      getLines({ speaker: selectedSpeaker, limit: 20 }).then(r => setSpeakerLines(r.data || []))
    } else {
      setSpeakerLines([])
    }
  }, [selectedSpeaker])

  const sortedSpeakers = [...speakers].sort((a, b) => (b[sortBy] || 0) - (a[sortBy] || 0))

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <span className="text-xs uppercase tracking-widest text-muted">Sort by:</span>
        <select
          className="bg-panel border border-accent2/30 rounded-md px-3 py-1 text-sm"
          value={sortBy}
          onChange={(e) => setSortBy(e.target.value)}
        >
          <option value="line_count">Lines</option>
          <option value="word_count">Words</option>
          <option value="avg_sentiment">Avg Sentiment</option>
          <option value="avg_wpm">Avg WPM</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-panel rounded-xl p-4 border border-accent2/20">
          <h3 className="text-sm uppercase tracking-widest text-accent2 mb-4">Speakers</h3>
          <div className="h-64 mb-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sortedSpeakers.slice(0, 20)} layout="vertical">
                <XAxis type="number" hide />
                <YAxis
                  dataKey="speaker"
                  type="category"
                  width={120}
                  tick={{ fill: '#c5c6c7', fontSize: 11 }}
                />
                <Tooltip
                  contentStyle={{ background: '#1f2833', border: '1px solid #45a29e', borderRadius: 8 }}
                  itemStyle={{ color: '#c5c6c7' }}
                  cursor={{ fill: 'rgba(102,252,241,0.05)' }}
                />
                <Bar dataKey={sortBy} radius={[0, 4, 4, 0]} onClick={(data) => setSelectedSpeaker(data?.payload?.speaker)}>
                  {sortedSpeakers.slice(0, 20).map((_, i) => (
                    <Cell key={i} fill={i % 2 === 0 ? '#66fcf1' : '#45a29e'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wider text-muted border-b border-accent2/20">
                  <th className="pb-2">Speaker</th>
                  <th className="pb-2">Lines</th>
                  <th className="pb-2">Words</th>
                  <th className="pb-2">Unique</th>
                  <th className="pb-2">Avg Sentiment</th>
                  <th className="pb-2">Avg WPM</th>
                </tr>
              </thead>
              <tbody>
                {sortedSpeakers.map((s) => (
                  <tr
                    key={s.speaker}
                    className={`border-b border-accent2/10 hover:bg-accent/5 cursor-pointer transition-colors ${selectedSpeaker === s.speaker ? 'bg-accent/10' : ''}`}
                    onClick={() => setSelectedSpeaker(s.speaker)}
                  >
                    <td className="py-2 text-accent font-bold">{s.speaker}</td>
                    <td className="py-2">{s.line_count}</td>
                    <td className="py-2">{s.word_count}</td>
                    <td className="py-2">{s.unique_word_count}</td>
                    <td className="py-2">{s.avg_sentiment != null ? s.avg_sentiment.toFixed(3) : '—'}</td>
                    <td className="py-2">{s.avg_wpm != null ? Math.round(s.avg_wpm) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-panel rounded-xl p-4 border border-accent2/20">
          <h3 className="text-sm uppercase tracking-widest text-accent2 mb-4">
            {selectedSpeaker ? `${selectedSpeaker}'s Lines` : 'Select a speaker'}
          </h3>
          {selectedSpeaker ? (
            speakerLines.length === 0 ? (
              <p className="text-muted">Loading...</p>
            ) : (
              <div className="space-y-3 max-h-[28rem] overflow-y-auto pr-2">
                {speakerLines.map((line) => (
                  <div key={line.idx} className="bg-surface rounded-lg p-3 border border-accent2/10">
                    <div className="flex items-center justify-between text-xs text-muted mb-1">
                      <span>#{line.idx}</span>
                      <span>{fmtTime(line.start_time)} - {fmtTime(line.end_time)}</span>
                    </div>
                    <p className="text-sm leading-relaxed">{line.raw_text}</p>
                    {line.sentiment_compound != null && (
                      <div className="mt-2 text-xs">
                        Sentiment:
                        <span
                          className={`ml-1 px-2 py-0.5 rounded-full ${getSentimentBadge(line.sentiment_compound)}`}
                        >
                          {line.sentiment_compound.toFixed(3)}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )
          ) : (
            <p className="text-muted">Click a speaker from the table or chart to see their dialogue.</p>
          )}
        </div>
      </div>
    </div>
  )
}

function fmtTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.floor(totalSeconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

function getSentimentBadge(compound) {
  if (compound >= 0.5) return 'bg-success/20 text-success'
  if (compound > 0.1) return 'bg-success/10 text-success'
  if (compound >= -0.1) return 'bg-muted/20 text-muted'
  if (compound >= -0.5) return 'bg-danger/10 text-danger'
  return 'bg-danger/20 text-danger'
}
