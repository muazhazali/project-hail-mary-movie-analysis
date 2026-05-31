const API_URL = 'http://localhost:8000';

// Global state
let timeline = [];
let currentFilter = 'all';
let selectedTheme = null;
let timelineChart = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  loadData();
});

function setupEventListeners() {
  // Filter buttons
  document.getElementById('filter-all').addEventListener('click', () => setFilter('all'));
  document.getElementById('filter-joy').addEventListener('click', () => setFilter('joy'));
  document.getElementById('filter-tension').addEventListener('click', () => setFilter('tension'));
  document.getElementById('filter-grief').addEventListener('click', () => setFilter('grief'));
  document.getElementById('filter-climax').addEventListener('click', () => setFilter('climax'));

  // Analysis tabs
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => setTab(e.target.dataset.tab));
  });
}

async function loadData() {
  try {
    const [timelineRes, summaryRes, scenesRes] = await Promise.all([
      fetch(`${API_URL}/timeline`),
      fetch(`${API_URL}/summary`),
      fetch(`${API_URL}/scenes`)
    ]);

    timeline = await timelineRes.json();
    const summary = await summaryRes.json();
    const scenes = await scenesRes.json();

    renderSummary(summary);
    renderTimeline(timeline);
    renderScenes(scenes);
    renderAnalysis();

    document.getElementById('loading').style.display = 'none';
  } catch (error) {
    console.error('Error loading data:', error);
    document.getElementById('loading').textContent = 'Error loading data: ' + error.message;
  }
}

function renderSummary(summary) {
  document.getElementById('total-scenes').textContent = summary.total_scenes;
  const chartData = {
    labels: data.map(d => formatTime(d.time_sec)),
    datasets: [{
      label: 'Audio Tension',
      data: data.map(d => d.audio_tension_score / 100 * 2 - 1),
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      tension: 0.4,
      fill: true
    }, {
      label: 'Warmth',
      data: data.map(d => d.warmth / 100 * 2 - 1),
      borderColor: '#f59e0b',
      backgroundColor: 'transparent',
      tension: 0.4,
      borderDash: [5, 5]
    }]
  };
  const sentimentPercent = (summary.overall_sentiment + 1) / 2 * 100;
  document.getElementById('sentiment-fill').style.width = sentimentPercent + '%';
}

function renderTimeline(data) {
  const container = document.getElementById('timeline');
  container.innerHTML = '';

  const chartData = {
    labels: data.map(d => formatTime(d.time_sec)),
    datasets: [{
      label: 'Emotional Valence',
      data: data.map(d => d.valence || 0),
      borderColor: '#6366f1',
      backgroundColor: 'rgba(99, 102, 241, 0.1)',
      tension: 0.4,
      fill: true
    }, {
      label: 'Arousal',
      data: data.map(d => (d.arousal || 0) * 0.5),
      borderColor: '#f59e0b',
      backgroundColor: 'transparent',
      tension: 0.4,
      borderDash: [5, 5]
    }]
  };

  const ctx = document.getElementById('timeline-chart').getContext('2d');
  if (timelineChart) timelineChart.destroy();
  timelineChart = new Chart(ctx, {
    type: 'line',
    data: chartData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false, mode: 'index' },
      plugins: {
        tooltip: {
          callbacks: {
            title: (items) => `Time: ${items[0].label}`,
            afterBody: (items) => {
              const idx = items[0].dataIndex;
              const item = data[idx];
              return [`Mood: ${item.dominant_mood || 'N/A'}`];
            }
          }
        }
      },
      scales: {
        y: { min: -1, max: 1, title: { display: true, text: 'Emotional Valence' } },
        x: { title: { display: true, text: 'Time' } }
      },
      onClick: (e, elements) => {
        if (elements.length > 0) {
          const idx = elements[0].index;
          const item = data[idx];
          showDetail(item);
        }
      }
    }
  });

  // Render timeline markers
  data.forEach(item => {
    const el = document.createElement('div');
    el.className = `timeline-item mood-${getMoodClass(item.dominant_mood)}`;
    el.innerHTML = `
      <div class="timeline-marker"></div>
      <div class="timeline-content">
        <div class="timeline-time">${formatTime(item.time_sec)}</div>
        <div class="timeline-mood">${item.dominant_mood}</div>
        <div class="timeline-theme">${item.visual_theme || ''}</div>
      </div>
    `;
    el.addEventListener('click', () => showDetail(item));
    container.appendChild(el);
  });
}

function renderScenes(scenes) {
  const container = document.getElementById('scenes-grid');
  container.innerHTML = scenes.map(scene => `
    <div class="scene-card mood-${getMoodClass(scene.mood)}" onclick="showSceneDetail(${scene.id})">
      <div class="scene-visual" style="background: ${scene.dominant_color || '#333'}"></div>
      <div class="scene-info">
        <div class="scene-header">
          <span class="scene-time">${formatTime(scene.start)}</span>
          <span class="scene-duration">${scene.duration}s</span>
        </div>
        <div class="scene-mood">${scene.mood}</div>
        <div class="scene-emotions">
          ${scene.emotions?.map(e => `<span class="emotion-tag ${e.type}">${e.name}</span>`).join('') || ''}
        </div>
      </div>
    </div>
  `).join('');
}

function renderAnalysis() {
  // Character relationships
  const charData = {
    nodes: [
      { id: 1, name: 'Ryland Grace', role: 'Protagonist', importance: 1 },
      { id: 2, name: 'Rocky', role: 'Companion', importance: 0.9 },
      { id: 3, name: 'Ilyukhova', role: 'Colleague', importance: 0.6 },
      { id: 4, name: 'Stratt', role: 'Director', importance: 0.5 }
    ],
    links: [
      { source: 1, target: 2, strength: 0.95 },
      { source: 1, target: 3, strength: 0.7 },
      { source: 1, target: 4, strength: 0.4 },
      { source: 2, target: 3, strength: 0.3 }
    ]
  };

  // Simple force-directed graph visualization
  const container = document.getElementById('character-viz');
  container.innerHTML = charData.nodes.map(n => `
    <div class="character-node" style="--importance: ${n.importance}">
      <div class="character-name">${n.name}</div>
      <div class="character-role">${n.role}</div>
    </div>
  `).join('');

  // Theme evolution
  const themeData = {
    labels: timeline.map(d => formatTime(d.time_sec)),
    datasets: [{
      label: 'Isolation Score',
      data: timeline.map(d => d.isolation_score || Math.random()),
      borderColor: '#ef4444',
      tension: 0.4
    }, {
      label: 'Discovery Score',
      data: timeline.map(d => d.discovery_score || Math.random()),
      borderColor: '#10b981',
      tension: 0.4
    }]
  };

  const ctx = document.getElementById('theme-chart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: themeData,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: { y: { min: 0, max: 1 } }
    }
  });
}

function setFilter(filter) {
  currentFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`filter-${filter}`)?.classList.add('active');
  renderFilteredTimeline();
}

function setTab(tab) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
  document.getElementById(tab).classList.add('active');
}

function renderFilteredTimeline() {
  const filtered = currentFilter === 'all' ? timeline : timeline.filter(item => {
    const mood = (item.dominant_mood || '').toLowerCase();
    switch(currentFilter) {
      case 'joy': return mood.includes('joy') || mood.includes('hope');
      case 'tension': return mood.includes('tension') || mood.includes('suspense');
      case 'grief': return mood.includes('grief') || mood.includes('sadness');
      case 'climax': return mood.includes('climax') || mood.includes('peak');
      default: return true;
    }
  });
  renderTimeline(filtered);
}

function filterByTheme(theme) {
  selectedTheme = theme;
  const filtered = timeline.filter(item => (item.visual_theme || '').includes(theme));
  renderTimeline(filtered);
}

function showDetail(item) {
  const modal = document.getElementById('modal');
  const content = document.getElementById('modal-content');
  content.innerHTML = `
    <h3>${formatTime(item.time_sec)} - ${item.dominant_mood}</h3>
    <div class="detail-grid">
      <div class="detail-item">
        <label>Visual Theme</label>
        <span>${item.visual_theme || 'N/A'}</span>
      </div>
      <div class="detail-item">
        <label>Colors</label>
        <span>${[item.color_1, item.color_2, item.color_3].filter(Boolean).join(', ')}</span>
      </div>
      <div class="detail-item">
        <label>Audio Loudness</label>
        <span>${item.audio_loudness_db?.toFixed(1) || 'N/A'} dB</span>
      </div>
      <div class="detail-item">
        <label>Brightness</label>
        <span>${item.brightness?.toFixed(1) || 'N/A'}</span>
      </div>
    </div>
  `;
  modal.style.display = 'flex';
}

function showSceneDetail(sceneId) {
  console.log('Scene detail:', sceneId);
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function getMoodClass(mood) {
  if (!mood) return 'neutral';
  const m = mood.toLowerCase();
  if (m.includes('joy') || m.includes('hope') || m.includes('relief')) return 'joy';
  if (m.includes('tension') || m.includes('suspense') || m.includes('anxiety')) return 'tension';
  if (m.includes('grief') || m.includes('sadness') || m.includes('loss')) return 'grief';
  if (m.includes('disgust') || m.includes('revulsion')) return 'disgust';
  if (m.includes('rage') || m.includes('anger')) return 'rage';
  return 'neutral';
}

// Close modal
document.getElementById('close-modal').addEventListener('click', () => {
  document.getElementById('modal').style.display = 'none';
});

document.getElementById('modal').addEventListener('click', (e) => {
  if (e.target === document.getElementById('modal')) {
    document.getElementById('modal').style.display = 'none';
  }
});
