const { useState, useEffect, useRef, useCallback, useMemo } = React;

// Generate realistic mock data for movies
const generateMovieData = (title, seed) =>> ({
  title,
  duration: 7200 + seed * 600,
  scenes: Array.from({ length: 40 + seed * 5 }, (_, i) => {
    const progress = i / (40 + seed * 5);
    let sentiment, intensity;
    
    if (seed === 1) { // The Martian - survival arc
      sentiment = -0.4 + progress * 0.8 + (Math.random() - 0.5) * 0.2;
      intensity = progress > 0.8 ? 0.9 : 0.4 + progress * 0.3;
    } else { // Hail Mary - discovery arc
      sentiment = Math.sin(progress * Math.PI * 2) * 0.4 + (Math.random() - 0.5) * 0.2;
      intensity = (1 - Math.abs(progress - 0.5) * 2) * 0.6 + Math.random() * 0.3;
    }
    
    return {
      id: i + seed * 1000,
      startTime: i * (7200 + seed * 600) / (40 + seed * 5),
      endTime: (i + 1) * (7200 + seed * 600) / (40 + seed * 5),
      sentiment: Math.max(-1, Math.min(1, sentiment)),
      intensity: Math.max(0, Math.min(1, intensity)),
      characters: seed === 0 
        ? (i % 3 === 0 ? ['Grace', 'Rocky'] : i % 5 === 0 ? ['Stratt'] : ['Grace'])
        : (i % 4 === 0 ? ['Watney', 'NASA'] : ['Watney']),
      dialogueCount: Math.floor(Math.random() * 12) + 3,
      type: i % 4 === 0 ? 'action' : 'dialogue'
    };
  }),
  characters: seed === 0 ? [
    { id: 'grace', name: 'Grace', color: '#60a5fa', screenTime: 0.65 },
    { id: 'rocky', name: 'Rocky', color: '#a78bfa', screenTime: 0.45 },
    { id: 'stratt', name: 'Stratt', color: '#f472b6', screenTime: 0.25 },
    { id: 'duy', name: 'Dr. Duy', color: '#34d399', screenTime: 0.15 }
  ] : [
    { id: 'watney', name: 'Watney', color: '#f97316', screenTime: 0.72 },
    { id: 'nasa', name: 'NASA Team', color: '#3b82f6', screenTime: 0.38 },
    { id: 'teddy', name: 'Teddy', color: '#10b981', screenTime: 0.22 },
    { id: 'venkat', name: 'Venkat', color: '#8b5cf6', screenTime: 0.18 }
  ],
  relationships: seed === 0 ? [
    { source: 'grace', target: 'rocky', strength: 0.95, type: 'partnership' },
    { source: 'grace', target: 'stratt', strength: 0.4, type: 'authority' },
    { source: 'grace', target: 'duy', strength: 0.3, type: 'colleague' },
    { source: 'rocky', target: 'stratt', strength: 0.1, type: 'distant' }
  ] : [
    { source: 'watney', target: 'nasa', strength: 0.85, type: 'rescue' },
    { source: 'watney', target: 'teddy', strength: 0.25, type: 'authority' },
    { source: 'nasa', target: 'teddy', strength: 0.6, type: 'command' },
    { source: 'nasa', target: 'venkat', strength: 0.5, type: 'science' }
  ]
});

const mockMovieData = generateMovieData("Project Hail Mary", 0);
const mockMartianData = generateMovieData("The Martian", 1);

const formatTime = (seconds) => {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}:${m.toString().padStart(2, '0')}`;
};

// Comparison View Component
const ComparisonView = ({ movies }) => {
  const [selectedMetric, setSelectedMetric] = useState('sentiment');
  const metrics = [
    { id: 'sentiment', label: 'Sentiment Arc', color: '#60a5fa' },
    { id: 'intensity', label: 'Scene Intensity', color: '#a78bfa' }
  ];
  
  const normalizedScenes = useMemo(() => movies.map(movie => ({
    ...movie,
    normalizedScenes: movie.scenes.map((s, i, arr) => ({ ...s, progress: i / arr.length }))
  })), [movies]);
  
  return (
    <div className="glass rounded-xl p-6 glow">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-6 gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white mb-1">The Adaptation Arc</h3>
          <p className="text-sm text-zinc-500">Comparing science fiction adaptations</p>
        </div>
        <div className="flex gap-2">
          {metrics.map(m => (
            <button
              key={m.id}
              onClick={() => setSelectedMetric(m.id)}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-all ${
                selectedMetric === m.id ? 'bg-zinc-700 text-white' : 'text-zinc-400 hover:text-white'
              }`}
            >
              <span className="w-2 h-2 rounded-full inline-block mr-2" style={{ backgroundColor: m.color }} />
              {m.label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="relative space-y-6">
        {normalizedScenes.map((movie, idx) => {
          const avgValue = movie.scenes.reduce((a, s) => a + (s[selectedMetric] || 0), 0) / movie.scenes.length;
          const color = ['#60a5fa', '#f97316'][idx % 2];
          
          return (
            <div key={movie.title}>
              <div className="flex items-center gap-4 mb-3">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                <span className="text-sm font-medium text-zinc-300">{movie.title}</span>
                <span className="text-xs text-zinc-600 ml-auto mono">Avg: {(avgValue * 100).toFixed(0)}%</span>
              </div>
              
              <div className="h-24 relative bg-zinc-900/30 rounded-lg overflow-hidden">
                <svg className="w-full h-full" preserveAspectRatio="none">
                  <defs>
                    <linearGradient id={`grad-${idx}`} x1="0%" y1="0%" x2="0%" y2="100%">
                      <stop offset="0%" stopColor={color} stopOpacity="0.6" />
                      <stop offset="100%" stopColor={color} stopOpacity="0.05" />
                    </linearGradient>
                  </defs>
                  
                  <path
                    d={`M0,96 ${movie.normalizedScenes.map(s => {
                      const x = s.progress * 100;
                      const val = Math.abs(s[selectedMetric] || 0);
                      const y = 96 - val * 80;
                      return `L${x},${y}`;
                    }).join(' ')} L100,96 Z`}
                    fill={`url(#grad-${idx})`}
                  />
                  <path
                    d={`M0,48 ${movie.normalizedScenes.map(s => {
                      const x = s.progress * 100;
                      const val = s[selectedMetric] || 0;
                      const y = 48 - val * 40;
                      return `L${x},${y}`;
                    }).join(' ')}`}
                    fill="none"
                    stroke={color}
                    strokeWidth={0.5}
                    vectorEffect="non-scaling-stroke"
                  />
                </svg>
                
                <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
                  {[25, 50, 75].map((pos, i) => (
                    <div key={i} className="absolute top-0 h-full border-l border-zinc-700/30" style={{ left: `${pos}%` }}>
                      <span className="absolute top-1 left-1 text-[10px] text-zinc-600">{['Act 1 End', 'Midpoint', 'Act 2 End'][i]}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Reddit Insights Component
const RedditInsights = ({ scenes }) => {
  const [controversialScenes] = useState(() => scenes
    .map(s => ({ 
      ...s, 
      controversyScore: Math.abs(s.sentiment) * s.intensity * (0.5 + 0.5 * Math.random()),
      redditMentions: Math.floor(Math.random() * 500 + 50)
    }))
    .sort((a, b) => b.controversyScore - a.controversyScore)
    .slice(0, 5)
  );
  
  return (
    <div className="glass rounded-xl p-6 glow">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-orange-500" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.75.806 1.75 1.8 0 .891-.66 1.624-1.516 1.764-.207.552-.368 1.123-.465 1.713-.104.617-.15 1.247-.15 1.879 0 1.23.157 2.391.458 3.456.967.214 1.687 1.074 1.687 2.122 0 1.183-.986 2.14-2.202 2.14H8.01c-1.216 0-2.202-.957-2.202-2.14 0-1.048.72-1.908 1.687-2.122.301-1.065.458-2.226.458-3.456 0-.632-.046-1.262-.15-1.879-.097-.59-.258-1.161-.465-1.713-.856-.14-1.516-.873-1.516-1.764 0-.994.782-1.8 1.75-1.8.477 0 .899.182 1.207.491 1.194-.856 2.85-1.418 4.674-1.488l-.8-3.747-2.597.547a1.25 1.25 0 0 1-2.498-.056c0-.688.562-1.249 1.25-1.249l3.25-.686a1.25 1.25 0 0 1 1.494.936l.548 2.575c.876.037 1.732.156 2.548.349l.63-2.956a1.25 1.25 0 0 1 1.494-.936l3.25.686z" />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-white">Reddit Intelligence</h3>
          <p className="text-sm text-zinc-500">Scenes generating discussion</p>
        </div>
      </div>
      
      <div className="space-y-3">
        {controversialScenes.map((scene, i) => (
          <div key={scene.id} className="flex items-start gap-3 p-3 bg-zinc-900/50 rounded-lg border border-zinc-800 hover:border-zinc-700 transition-colors">
            <div className="flex flex-col items-center gap-1 min-w-[40px]">
              <span className="text-lg font-bold mono text-zinc-500">#{i + 1}</span>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                scene.controversyScore > 0.4 ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'
              }`}>
                {(scene.controversyScore * 100).toFixed(0)}
              </div>
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="mono text-xs text-zinc-500">{formatTime(scene.startTime)}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-400">{scene.redditMentions} mentions</span>
              </div>
              
              <p className="text-sm text-zinc-300 truncate">{scene.characters.slice(0, 2).join(' & ')} · {scene.dialogueCount} lines</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Timeline Scrubber Component
const TimelineScrubber = ({ data, currentTime, onTimeChange, width = 680, height = 140 }) => {
  const svgRef = useRef(null);
  const [hoverTime, setHoverTime] = useState(null);
  
  const xScale = useMemo(() => d3.scaleLinear().domain([0, data.duration]).range([0, width - 80]), [data.duration, width]);
  const yScale = useMemo(() => d3.scaleLinear().domain([-1, 1]).range([height - 50, 20]), [height]);
  
  const handleMouseMove = useCallback((e) => {
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - 40;
    const time = xScale.invert(x);
    if (time >= 0 && time <= data.duration) setHoverTime(time);
  }, [xScale, data.duration]);
  
  const handleClick = useCallback((e) => {
    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left - 40;
    onTimeChange(Math.max(0, Math.min(data.duration, xScale.invert(x))));
  }, [xScale, data.duration, onTimeChange]);
  
  const sentimentPoints = useMemo(() => data.scenes.map(s => ({ x: xScale((s.startTime + s.endTime) / 2), y: yScale(s.sentiment) })), [data.scenes, xScale, yScale]);
  const intensityPoints = useMemo(() => data.scenes.map(s => ({ x: xScale((s.startTime + s.endTime) / 2), y: height - 35 - s.intensity * 30 })), [data.scenes, xScale, height]);
  
  const sentimentPath = useMemo(() => sentimentPoints.length > 0 ? d3.line().x(d => d.x).y(d => d.y).curve(d3.curveMonotoneX)(sentimentPoints) : '', [sentimentPoints]);
  const intensityArea = useMemo(() => intensityPoints.length > 0 ? d3.area().x(d => d.x).y0(height - 35).y1(d => d.y).curve(d3.curveMonotoneX)(intensityPoints) : '', [intensityPoints, height]);
  
  return (
    <div className="glass rounded-xl p-5 glow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-white">Narrative Timeline</h3>
        <div className="flex items-center gap-4 text-xs text-zinc-500">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-blue-400" /> Sentiment</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-purple-400 opacity-60" /> Intensity</span>
        </div>
      </div>
      
      <div className="relative">
        <svg ref={svgRef} width={width} height={height} onMouseMove={handleMouseMove} onMouseLeave={() => setHoverTime(null)} onClick={handleClick} className="cursor-crosshair">
          <g transform="translate(40, 0)">
            <path d={intensityArea} fill="url(#intensityGrad)" opacity={0.4} />
            <path d={sentimentPath} fill="none" stroke="#60a5fa" strokeWidth={2} />
            
            {data.scenes.filter((_, i) => i % 3 === 0).map(scene => (
              <circle key={scene.id} cx={xScale((scene.startTime + scene.endTime) / 2)} cy={yScale(scene.sentiment)} r={2 + scene.dialogueCount * 0.3}
                fill={scene.sentiment > 0.2 ? '#22c55e' : scene.sentiment < -0.2 ? '#ef4444' : '#6b7280'} opacity={0.7} />
            ))}
            
            <line x1={xScale(currentTime)} y1={10} x2={xScale(currentTime)} y2={height - 25} stroke="#fff" strokeWidth={2} />
            <circle cx={xScale(currentTime)} cy={yScale(data.scenes.find(s => currentTime >= s.startTime && currentTime < s.endTime)?.sentiment || 0)} r={5} fill="#fff" stroke="#60a5fa" strokeWidth={2} />
            
            {hoverTime !== null && <line x1={xScale(hoverTime)} y1={0} x2={xScale(hoverTime)} y2={height - 25} stroke="#a78bfa" strokeWidth={1} strokeDasharray="3,3" />}
            
            <defs>
              <linearGradient id="intensityGrad" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.5} />
                <stop offset="100%" stopColor="#a78bfa" stopOpacity={0} />
              </linearGradient>
            </defs>
          </g>
          
          <g transform={`translate(40, ${height - 25})`}>
            {xScale.ticks(6).map(tick => (
              <g key={tick} transform={`translate(${xScale(tick)}, 0)`}>
                <line y1={0} y2={4} stroke="#3f3f46" />
                <text y={14} textAnchor="middle" fontSize={10} fill="#71717a" className="mono">{formatTime(tick)}</text>
              </g>
            ))}
          </g>
        </svg>
        
        <div className="absolute top-2 right-2 glass px-3 py-1 rounded text-sm mono">{formatTime(hoverTime ?? currentTime)}</div>
      </div>
    </div>
  );
};

// Character Constellation Component
const CharacterConstellation = ({ characters, relationships, width = 380, height = 280 }) => {
  const [hoveredNode, setHoveredNode] = useState(null);
  
  const nodes = useMemo(() => {
    const angleStep = (2 * Math.PI) / characters.length;
    const radius = Math.min(width, height) * 0.28;
    return characters.map((char, i) => ({
      ...char,
      x: width / 2 + Math.cos(i * angleStep - Math.PI / 2) * radius,
      y: height / 2 + Math.sin(i * angleStep - Math.PI / 2) * radius
    }));
  }, [characters, width, height]);
  
  const links = useMemo(() => relationships.map(rel => {
    const source = nodes.find(n => n.id === rel.source);
    const target = nodes.find(n => n.id === rel.target);
    return source && target ? { ...rel, source, target } : null;
  }).filter(Boolean), [relationships, nodes]);
  
  return (
    <div className="glass rounded-xl p-5 glow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-white">Character Network</h3>
        <span className="text-xs text-zinc-500">{characters.length} characters</span>
      </div>
      
      <svg width={width} height={height} className="mx-auto">
        <g>
          {links.map((link, i) => (
            <g key={i} opacity={hoveredNode ? (hoveredNode === link.source.id || hoveredNode === link.target.id ? 1 : 0.2) : 1}>
              <line x1={link.source.x} y1={link.source.y} x2={link.target.x} y2={link.target.y}
                stroke="rgba(96, 165, 250, 0.4)" strokeWidth={link.strength * 4} strokeLinecap="round" />
              <circle cx={(link.source.x + link.target.x) / 2} cy={(link.source.y + link.target.y) / 2} r={3} fill="#fff" opacity={link.strength} />
            </g>
          ))}
          
          {nodes.map(node => (
            <g key={node.id} transform={`translate(${node.x}, ${node.y})`} className="cursor-pointer"
              onMouseEnter={() => setHoveredNode(node.id)} onMouseLeave={() => setHoveredNode(null)}
              opacity={hoveredNode && hoveredNode !== node.id && !links.some(l => (l.source.id === hoveredNode && l.target.id === node.id) || (l.target.id === hoveredNode && l.source.id === node.id)) ? 0.4 : 1}
            >
              <circle r={28 + node.screenTime * 20} fill={node.color} opacity={0.15} />
              <circle r={22 + node.screenTime * 15} fill={node.color} opacity={0.85} />
              <text textAnchor="middle" dominantBaseline="central" fill="#fff" fontSize={13} fontWeight={600}>{node.name.slice(0, 2)}</text>
              <text y={38} textAnchor="middle" fill="#a1a1aa" fontSize={11}>{node.name}</text>
            </g>
          ))}
        </g>
      </svg>
    </div>
  );
};

// Scene Explorer Component
const SceneExplorer = ({ scenes, currentTime, onSceneSelect }) => {
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  
  const filteredScenes = useMemo(() => scenes.filter(s => {
    if (filter !== 'all' && s.type !== filter) return false;
    if (search && !s.characters.some(c => c.toLowerCase().includes(search.toLowerCase()))) return false;
    return true;
  }), [scenes, filter, search]);
  
  const currentScene = useMemo(() => scenes.find(s => currentTime >= s.startTime && currentTime <= s.endTime), [scenes, currentTime]);
  
  return (
    <div className="glass rounded-xl p-5 glow">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 gap-3">
        <h3 className="text-base font-semibold text-white">Scene Explorer</h3>
        <div className="flex gap-2">
          {['all', 'dialogue', 'action'].map(type => (
            <button key={type} onClick={() => setFilter(type)}
              className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                filter === type ? 'bg-blue-500 text-white' : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700'
              }`}
            >{type.charAt(0).toUpperCase() + type.slice(1)}</button>
          ))}
        </div>
      </div>
      
      <input type="text" placeholder="Filter by character..." value={search} onChange={(e) => setSearch(e.target.value)}
        className="w-full px-4 py-2 mb-4 bg-zinc-900/50 border border-zinc-800 rounded-lg text-sm text-zinc-300 placeholder-zinc-600 focus:outline-none focus:border-blue-500" />
      
      <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
        {filteredScenes.slice(0, 15).map(scene => (
          <div key={scene.id} onClick={() => onSceneSelect(scene.startTime)}
            className={`p-3 rounded-lg border cursor-pointer transition-all ${
              currentScene?.id === scene.id ? 'border-blue-500 bg-blue-500/10' : 'border-zinc-800 bg-zinc-900/30 hover:border-zinc-700'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="mono text-xs text-zinc-500">{formatTime(scene.startTime)}</span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                  scene.sentiment > 0.2 ? 'bg-green-500/20 text-green-400' : scene.sentiment < -0.2 ? 'bg-red-500/20 text-red-400' : 'bg-zinc-700 text-zinc-400'
                }`}>
                  {scene.sentiment > 0.2 ? '+' : scene.sentiment < -0.2 ? '−' : '○'}
                </span>
              </div>
              <span className="text-xs text-zinc-500">{scene.dialogueCount} lines</span>
            </div>
            
            <p className="text-sm text-zinc-400 mt-1 truncate">{scene.characters.join(', ') || 'No dialogue'}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

// Metrics Panel
const MetricsPanel = ({ data }) => {
  const stats = useMemo(() => {
    const totalScenes = data.scenes.length;
    const avgSentiment = data.scenes.reduce((a, b) => a + b.sentiment, 0) / totalScenes;
    const dialogueScenes = data.scenes.filter(s => s.dialogueCount > 5).length;
    const dominant = data.characters.reduce((a, b) => a.screenTime > b.screenTime ? a : b);
    
    return [
      { label: 'Scenes', value: totalScenes, suffix: '', color: 'text-white' },
      { label: 'Sentiment', value: (avgSentiment * 100).toFixed(0), suffix: '%', color: avgSentiment > 0 ? 'text-green-400' : 'text-red-400' },
      { label: 'Dialogue', value: dialogueScenes, suffix: '', color: 'text-blue-400' },
      { label: 'Protagonist', value: dominant.name, suffix: '', color: 'text-purple-400' }
    ];
  }, [data]);
  
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat, i) => (
        <div key={i} className="glass rounded-xl p-4">
          <p className="text-[10px] text-zinc-500 uppercase tracking-wider mb-1">{stat.label}</p>
          <p className={`text-xl font-bold mono ${stat.color}`}>{stat.value}{stat.suffix}</p>
        </div>
      ))}
    </div>
  );
};

// Tab Navigation
const TabNav = ({ activeTab, onChange }) => {
  const tabs = [
    { id: 'overview', label: 'Overview' },
    { id: 'comparison', label: 'Comparison' },
    { id: 'audience', label: 'Audience' }
  ];
  
  return (
    <div className="flex gap-1 mb-6">
      {tabs.map(tab => (
        <button key={tab.id} onClick={() => onChange(tab.id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
            activeTab === tab.id ? 'bg-zinc-800 text-white' : 'text-zinc-500 hover:text-zinc-300'
          }`}
        >{tab.label}</button>
      ))}
    </div>
  );
};

// Main Dashboard
const Dashboard = () => {
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setCurrentTime(t => {
        if (t >= mockMovieData.duration) { setIsPlaying(false); return 0; }
        return t + 8;
      });
    }, 100);
    return () => clearInterval(interval);
  }, [isPlaying]);
  
  const renderContent = () => {
    switch (activeTab) {
      case 'comparison':
        return (
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="lg:col-span-2">
              <ComparisonView movies={[mockMovieData, mockMartianData]} />
            </div>
          </div>
        );
      case 'audience':
        return (
          <div className="grid lg:grid-cols-2 gap-6">
            <RedditInsights scenes={mockMovieData.scenes} />
            <div className="glass rounded-xl p-6 glow">
              <h3 className="text-lg font-semibold text-white mb-4">Sentiment Distribution</h3>
              <div className="h-64 flex items-end justify-around gap-2">
                {mockMovieData.scenes.slice(0, 20).map((s, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1">
                    <div className="w-full rounded-t transition-all" style={{ height: `${Math.abs(s.sentiment) * 100}%`, backgroundColor: s.sentiment > 0 ? '#22c55e' : '#ef4444', opacity: 0.7 }} />
                    <span className="text-[8px] text-zinc-600">{i + 1}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        );
      default:
        return (
          <>
            <section className="mb-8"><MetricsPanel data={mockMovieData} /></section>
            
            <section className="grid lg:grid-cols-3 gap-6 mb-8">
              <div className="lg:col-span-2"><TimelineScrubber data={mockMovieData} currentTime={currentTime} onTimeChange={setCurrentTime} width={680} /></div>
              <div><CharacterConstellation characters={mockMovieData.characters} relationships={mockMovieData.relationships} /></div>
            </section>
            
            <section className="grid lg:grid-cols-2 gap-6">
              <SceneExplorer scenes={mockMovieData.scenes} currentTime={currentTime} onSceneSelect={setCurrentTime} />
              
              <div className="glass rounded-xl p-5 glow">
                <h3 className="text-base font-semibold text-white mb-4">Character Screen Time</h3>
                <div className="space-y-4">
                  {mockMovieData.characters.map(char => (
                    <div key={char.id}>
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: char.color }} />
                          <span className="text-sm text-zinc-300">{char.name}</span>
                        </div>
                        <span className="text-sm mono text-zinc-500">{(char.screenTime * 100).toFixed(0)}%</span>
                      </div>
                      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all duration-500" style={{ width: `${char.screenTime * 100}%`, backgroundColor: char.color }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </>
        );
    }
  };
  
  return (
    <div className="min-h-screen bg-[#0a0a0f]">
      <header className="border-b border-zinc-800/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">Movie Intelligence</h1>
                <p className="text-sm text-zinc-500">{mockMovieData.title}</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {activeTab === 'overview' && (
                <button onClick={() => setIsPlaying(!isPlaying)}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 rounded-lg text-white font-medium transition-all shadow-lg shadow-blue-500/20"
                >
                  {isPlaying ? (
                    <><svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" /></svg>Pause</>
                  ) : (
                    <><svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>Analyze</>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-6 py-8">
        <TabNav activeTab={activeTab} onChange={setActiveTab} />
        {renderContent()}
      </main>
      
      <footer className="border-t border-zinc-800/50 mt-12 py-8">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center text-sm text-zinc-600">Movie Intelligence Platform · NLP + Computer Vision Analytics</p>
        </div>
      </footer>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<React.StrictMode><Dashboard /></React.StrictMode>
);