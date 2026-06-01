import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
})

export const getHealth = () => api.get('/health')
export const getStats = () => api.get('/subtitles/stats')
export const getTimeline = (params) => api.get('/subtitles/timeline', { params })
export const getSpeakers = () => api.get('/subtitles/speakers')
export const getLines = (params) => api.get('/subtitles/lines', { params })
export const searchSemantic = (params) => api.get('/search/semantic', { params })
export const searchText = (params) => api.get('/search/text', { params })
export const getTopWords = (params) => api.get('/analytics/top-words', { params })
export const getSentimentDistribution = () => api.get('/analytics/sentiment-distribution')
export const getDurationStats = () => api.get('/analytics/duration-stats')
