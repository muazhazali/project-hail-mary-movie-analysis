import React, { useEffect, useState } from 'react'
import { getTimeline, getSpeakers } from '../api'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

function fmtTime(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.floor(totalSeconds % 60)
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

export default function TimelinePage() {
  const [points, setPoints] = useState([])
  const [speakers, setSpeakers] = useState([])
  const [selectedSpeaker, setSelectedSpeaker] = useState('')
  const [metric, setMetric] = useState('sentiment') // sentiment | wpm | word_count

  useEffect(() => {
    getSpeakers().then(r => setSpeakers(r.data || []))
  }, [])

  useEffect(() => {
    getTimeline({ speaker: selectedSpeaker || undefined, window: 60 }).then(r => {
      const arr = (r.data || []).map(p => ({
        ...p,
        timeLabel: fmtTime(p.start_time),
      }))
      setPoints(arr)
    })
  }, [selectedSpeaker])

  const metricConfig = {
    sentiment: { label: 'Sentiment', color: '#66fcf1', domain: [-1, 1] },
    wpm: { label: 'Words/min', color: '#e74c3c', domain: [0, 'auto'] },
    word_count: { label: 'Words', color: '#f1c40f', domain: [0, 'auto'] },
  }

  const cfg = metricConfig[metric]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-4">
        <div>
          <label className="block text-xs uppercase tracking-widest text-muted mb-1">Speaker</label>
          <select
            className="bg-panel border border-accent2/30 rounded-md px-3 py-2 text-sm focus:outline-none focus:border-accent"
            value={selectedSpeaker}
            onChange={(e) => setSelectedSpeaker(e.target.value)}
          >
            <option value="">All Speakers</option>
            {speakers.map((s) => (
              <option key={s.speaker} value={s.speaker}>{s.speaker}</option>
            ))}
          </select>
        </div>

        <div className="flex gap-1">
          {(['sentiment', 'wpm', 'word_count']).map((m) => (
            <button
              key={m}
              onClick={() => setMetric(m)}
              className={
                `px-3 py-2 rounded-md text-sm font-bold border transition-colors ` +
                (metric === m
                  ? 'bg-accent text-surface border-accent'
                  : 'bg-panel text-muted border-accent2/30 hover:text-accent')
              }
            >
              {metricConfig[m].label}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-panel rounded-xl p-4 border border-accent2/20">
        <div className="h-[28rem]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a3b4c" />
              <XAxis
                dataKey="timeLabel"
                tick={{ fill: '#8d99ae', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={60}
                interval={Math.floor(points.length / 20)}
              />
              <YAxis
                domain={cfg.domain}
                tick={{ fill: '#8d99ae', fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{ background: '#1f2833', border: '1px solid #45a29e', borderRadius: 8 }}
                itemStyle={{ color: '#c5c6c7' }}
                formatter={(value) => [value?.toFixed(3) ?? value, cfg.label]}
                labelFormatter={(label) => `Time: ${label}`}
              />
              {metric === 'sentiment' && (
                <>
                  <ReferenceLine y={0} stroke="#8d99ae" strokeDasharray="3 3" />
                  <ReferenceLine y={0.5} stroke="#2ecc71" strokeDasharray="6 2" />
                  <ReferenceLine y={-0.5} stroke="#e74c3c" strokeDasharray="6 2" />
                </>
              )}
              <Line
                type="monotone"
                dataKey={metric}
                stroke={cfg.color}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 5, fill: cfg.color, stroke: '#0b0c10', strokeWidth: 2 }}
                connectNulls
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
