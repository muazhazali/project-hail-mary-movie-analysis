import os
import pandas as pd
import spacy
import networkx as nx
from pyvis.network import Network
import plotly.express as px
import itertools
from collections import Counter
import warnings

def time_to_seconds(t_str):
    try:
        h, m, s = t_str.split(':')
        s, ms = s.split('.')
        return int(h) * 3600 + int(m) * 60 + int(s) + float(ms) / 1000.0
    except:
        return 0

def main():
    warnings.filterwarnings('ignore')
    
    base_dir = os.path.dirname(os.path.dirname(__file__))
    data_path = os.path.join(base_dir, 'outputs', 'subtitles.csv')
    visuals_dir = os.path.join(base_dir, 'outputs', 'visuals')
    os.makedirs(visuals_dir, exist_ok=True)
    
    print(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    df['time_sec'] = df['start_time'].apply(time_to_seconds)
    # 2 minute windows
    window_size = 120 
    df['window'] = df['time_sec'] // window_size
    
    # Initialize SpaCy
    print("Loading SpaCy NER model...")
    nlp = spacy.load("en_core_web_sm")
    
    # Process text per window
    print("Extracting characters per time window...")
    window_characters = {}
    
    # Common false positive PERSON names in subtitles
    ignore_names = {'Yeah', 'Hey', 'Oh', 'Okay', 'Yes', 'No', 'Right'}
    
    # Group by window and concatenate text
    for window, group in df.groupby('window'):
        text = " ".join(group['text'].fillna("").tolist())
        doc = nlp(text)
        
        # Extract unique persons in this window
        people = set()
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                # clean up the name a bit
                name = ent.text.strip().title()
                # filter out very short names or obvious false positives
                if len(name) > 2 and name not in ignore_names:
                    people.add(name)
        
        if people:
            window_characters[window] = list(people)
            
    # Build Edges (Co-occurrences)
    print("Building interaction network...")
    edges = []
    character_mentions = Counter()
    
    for window, chars in window_characters.items():
        for char in chars:
            character_mentions[char] += 1
            
        # Add edges for any pair of characters in the same window
        if len(chars) > 1:
            for pair in itertools.combinations(sorted(chars), 2):
                edges.append(pair)
                
    # Filter to top 20 characters to keep the graph readable
    top_characters = set([char for char, count in character_mentions.most_common(20)])
    
    filtered_edges = [edge for edge in edges if edge[0] in top_characters and edge[1] in top_characters]
    edge_counts = Counter(filtered_edges)
    
    # Create NetworkX Graph
    G = nx.Graph()
    for (char1, char2), weight in edge_counts.items():
        G.add_edge(char1, char2, weight=weight)
        
    print(f"Graph constructed with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    if G.number_of_nodes() == 0:
        print("No characters detected. Graph is empty.")
        return
        
    # Calculate Centrality
    degree_cent = nx.degree_centrality(G)
    
    # Eigenvector centrality can fail to converge if the graph is completely disconnected
    try:
        eigen_cent = nx.eigenvector_centrality(G, max_iter=1000)
    except:
        eigen_cent = degree_cent
        
    # Export Interactive Graph using Pyvis
    print("Generating Pyvis Interactive Network...")
    net = Network(height='600px', width='100%', bgcolor='#111827', font_color='white')
    
    # Add nodes with size based on degree centrality
    for node in G.nodes():
        size = degree_cent[node] * 50 + 10  # Scale for visual
        title = f"{node}<br>Interactions: {character_mentions[node]}<br>Dominance: {eigen_cent[node]:.2f}"
        net.add_node(node, label=node, title=title, size=size, color="#9061F9")
        
    # Add edges with width based on weight
    for source, target, data in G.edges(data=True):
        weight = data['weight']
        net.add_edge(source, target, value=weight, title=f"Weight: {weight}", color="#4B5563")
        
    # Set physics layout options
    net.set_options("""
    var options = {
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -50,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based"
      }
    }
    """)
    
    net_path = os.path.join(visuals_dir, 'network_graph.html')
    net.write_html(net_path)
    
    # Export Plotly Heatmap
    print("Generating Plotly Interaction Heatmap...")
    # Convert edge counts to a matrix dataframe
    nodes = list(G.nodes())
    heatmap_data = pd.DataFrame(0, index=nodes, columns=nodes)
    
    for (char1, char2), weight in edge_counts.items():
        heatmap_data.loc[char1, char2] = weight
        heatmap_data.loc[char2, char1] = weight  # symmetric matrix
        
    fig = px.imshow(heatmap_data, 
                    labels=dict(x="Character", y="Character", color="Interactions"),
                    x=nodes, y=nodes,
                    color_continuous_scale="Purples",
                    title="Character Interaction Heatmap")
    
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    
    hm_path = os.path.join(visuals_dir, 'interaction_heatmap.html')
    fig.write_html(hm_path)
    
    print("Stage 4 complete!")

if __name__ == "__main__":
    main()
