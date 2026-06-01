import React, { useEffect, useState } from 'react'
import { getStats, getSentimentDistribution, getTopWords, getDurationStats } from '../api'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

/* eslint-disable react-refresh/only-export-components */

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-panel rounded-xl p-6 border border-accent2/20 hover:border-accent/40 transition-colors">
      <div className="text-3xl font-display text-accent mb-1">{value}</div>
      <div className="text-xs uppercase tracking-widest text-muted">{label}</div>
      {sub && <div className="text-[10px] text-muted mt-1">{sub}</div>}
    </div>
  )
}

function Section({ title, children }) {
  return (
    <div className="mb-10">
      <h2 className="text-xl font-display text-accent2 mb-4 tracking-wide">{title}</h2>
      {children}
    </div>
  )
}

const SENTIMENT_COLORS = {
  very_negative: '#e74c3c',
  negative: '#e67e22',
  neutral: '#f1c40f',
  positive: '#2ecc71',
  very_positive: '#27ae60',
}

export default function Overview() {
  const [stats, setStats] = useState(null)
  const [sentiment, setSentiment] = useState(null)
  const [words, setWords] = useState([])
  const [duration, setDuration] = useState(null)

  useEffect(() => {
    getStats().then(r => setStats(r.data))
    getSentimentDistribution().then(r => setSentiment(r.data))
    getTopWords({ limit: 50 }).then(r => setWords(r.data || []))
    getDurationStats().then(r => setDuration(r.data))
  }, [])

  const pieData = sentiment
    ? Object.entries(sentiment).filter(([, v]) => v > 0).map(([k, v]) => ({
        name: k.replace('_', ' '),
        value: v,
        color: SENTIMENT_COLORS[k],
      }))
    : []

  return (
    <div className="space-y-8">
      <Section title="Mission Overview">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Lines" value={stats?.total_lines ?? '—'} />
          <StatCard label="Total Words" value={stats?.total_words?.toLocaleString() ?? '—'} />
          <StatCard label="Unique Speakers" value={stats?.unique_speakers ?? '—'} />
          <StatCard label="Avg Sentiment" value={stats?.avg_sentiment != null ? stats.avg_sentiment.toFixed(3) : '—'} />
        </div>
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <StatCard label="Runtime" value={duration?.runtime_human ?? '—'} sub={`${duration?.runtime_seconds ?? 0}s`} />
          <StatCard label="Dialogue Time" value={duration?.total_dialogue_human ?? '—'} sub={`${duration?.total_dialogue_seconds ?? 0}s`} />
        </div>
      </Section>

      <Section title="Sentiment Distribution">
        <div className="bg-panel rounded-xl p-4 border border-accent2/20 flex flex-col md:flex-row items-center gap-6">
          <div className="w-full md:w-1/2 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  stroke="#0b0c10"
                  strokeWidth={2}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1f2833', border: '1px solid #45a29e', borderRadius: 8 }}
                  itemStyle={{ color: '#c5c6c7' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="w-full md:w-1/2 flex flex-wrap gap-3">
            {pieData.map((d) => (
              <div key={d.name} className="flex items-center gap-2 bg-surface rounded-md px-3 py-2">
                <span className="w-3 h-3 rounded-full inline-block" style={{ backgroundColor: d.color }} />
                <span className="text-sm capitalize">{d.name}</span>
                <span className="text-xs text-muted">({d.value})</span>
              </div>
            ))}
          </div>
        </div>
      </Section>

      <Section title="Top Words">
        <div className="bg-panel rounded-xl p-6 border border-accent2/20">
          <div className="flex flex-wrap gap-3">
            {words.length === 0 && <p className="text-muted">Loading...</p>}
            {words.map((w) => {
              const size = Math.max(0.75, Math.min(2.5, 0.75 + (w.count / Math.max(...words.map(x => x.count))) * 1.75))
              return (
                <span
                  key={w.word}
                  className="inline-block px-3 py-1 rounded-full border border-accent2/30 text-accent hover:bg-accent hover:text-surface transition-colors cursor-default"
                  style={{ fontSize: `${size}rem` }}
                  title={`${w.count} occurrences`}
                >
                  {w.word}
                </span>
              )
            })}
          </div>
        </div>
      </Section>
    </div>
  )
}
