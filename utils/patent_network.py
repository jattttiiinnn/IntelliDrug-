"""
utils/patent_network.py

This module provides a D3.js-based interactive network graph for visualizing
patent landscapes, relationships, and FTO risks.
"""

import json
import streamlit.components.v1 as components
from typing import List, Dict, Any

def render_patent_network(patents: List[Dict[str, Any]], molecule_name: str, height: int = 600):
    """
    Renders an interactive D3.js network graph of patents.
    
    Args:
        patents: List of patent dictionaries (from PatentAgent).
        molecule_name: Name of the central drug molecule.
        height: Height of the component in pixels.
    """
    
    # 1. Transform Data for D3
    nodes = []
    links = []
    
    # Central Node (The Drug)
    nodes.append({
        "id": "CENTER",
        "label": molecule_name,
        "type": "drug",
        "risk": "none",
        "radius": 20,
        "color": "#2E86C1" # Strong Blue
    })
    
    # Patent Nodes
    for p in patents:
        p_id = p.get('patent_number', 'Unknown')
        
        # Determine Color based on Risk/Status
        # Logic: Expired -> Green, Active + High Risk (hypothetical field) -> Red, Active -> Orange
        # Since we might not have explicit "risk" field in simple list, we infer or use defaults
        # If 'fto_status' was passed per patent it would be better, but we often get it aggregate.
        # We'll assume if it's in the list it's relevant.
        
        status = p.get('status', 'Active')
        color = "#F1C40F" # Yellow/Orange (Caution)
        
        if status == "Expired":
            color = "#27AE60" # Green (Safe)
        elif "High" in p.get('risk_level', ''): # Hypothetical field if available
            color = "#E74C3C" # Red (Danger)
            
        # Tooltip content
        tooltip = f"Patent: {p_id}\nTitle: {p.get('title')}\nAssignee: {p.get('assignee')}\nExpires: {p.get('expiration_date')}"
            
        nodes.append({
            "id": p_id,
            "label": p_id,
            "type": "patent",
            "risk": "medium", # Placeholder
            "radius": 12,
            "color": color,
            "tooltip": tooltip,
            "url": p.get('url', '#')
        })
        
        # Link to Center
        links.append({
            "source": "CENTER",
            "target": p_id,
            "value": 1
        })
        
    graph_data = {"nodes": nodes, "links": links}
    json_data = json.dumps(graph_data)

    # 2. D3.js HTML Template
    html_code = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <script src="https://d3js.org/d3.v6.min.js"></script>
        <style>
          body {{ margin: 0; background-color: #0E1117; font-family: sans-serif; overflow: hidden; }}
          .tooltip {{
            position: absolute;
            text-align: left;
            padding: 8px;
            font-size: 12px;
            background: rgba(0, 0, 0, 0.8);
            color: #fff;
            border-radius: 4px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            max-width: 300px;
            z-index: 10;
          }}
          svg {{ width: 100%; height: 100%; }}
          circle {{ stroke: #fff; stroke-width: 1.5px; cursor: pointer; }}
          line {{ stroke: #999; stroke-opacity: 0.6; }}
          text {{ fill: #ddd; font-size: 10px; pointer-events: none; }}
          
          /* Legend */
          .legend {{ position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.1); padding: 10px; border-radius: 5px; }}
          .legend-item {{ display: flex; align-items: center; margin-bottom: 5px; color: #eee; font-size: 12px; }}
          .legend-color {{ width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }}
        </style>
      </head>
      <body>
        <div id="graph-container" style="width:100%; height:{height}px;"></div>
        <div id="debug-status" style="position:absolute; top:50px; left:10px; color:#ffcc00; font-family:monospace; font-size:12px; pointer-events:none;">Initializing...</div>
        <div class="tooltip" id="tooltip"></div>
        
        <div class="legend">
            <div class="legend-item"><div class="legend-color" style="background:#2E86C1"></div>Target Molecule</div>
            <div class="legend-item"><div class="legend-color" style="background:#F1C40F"></div>Active Patent (Caution)</div>
            <div class="legend-item"><div class="legend-color" style="background:#27AE60"></div>Expired/Low Risk</div>
            <div class="legend-item"><div class="legend-color" style="background:#E74C3C"></div>High Risk</div>
        </div>

        <script>
          const statusDiv = document.getElementById('debug-status');
          function log(msg) {{ statusDiv.innerHTML += "<br>" + msg; }}
          
          window.onerror = function(message, source, lineno, colno, error) {{
              log("JS Error: " + message + " at line " + lineno);
          }};

          try {{
              if (typeof d3 === 'undefined') {{
                  log("Error: D3.js library failed to load.");
                  throw new Error("D3 missing");
              }}
              
              const data = {json_data};
              const width = window.innerWidth || 800; // Fallback width
              const height = {height};
              
              log("Data loaded. Nodes: " + data.nodes.length + ", Width: " + width);

              const svg = d3.select("#graph-container").append("svg")
                  .attr("viewBox", [0, 0, width, height]);
                  
              // Zoom capability
              const g = svg.append("g");
              svg.call(d3.zoom()
                  .extent([[0, 0], [width, height]])
                  .scaleExtent([0.1, 8])
                  .on("zoom", ({{transform}}) => g.attr("transform", transform)));

              const simulation = d3.forceSimulation(data.nodes)
                  .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
                  .force("charge", d3.forceManyBody().strength(-300))
                  .force("center", d3.forceCenter(width / 2, height / 2))
                  .force("collide", d3.forceCollide().radius(d => d.radius + 5));

              const link = g.append("g")
                  .attr("stroke", "#999")
                  .attr("stroke-opacity", 0.6)
                .selectAll("line")
                .data(data.links)
                .join("line")
                  .attr("stroke-width", d => Math.sqrt(d.value));

              const node = g.append("g")
                  .attr("stroke", "#fff")
                  .attr("stroke-width", 1.5)
                .selectAll("circle")
                .data(data.nodes)
                .join("circle")
                  .attr("r", d => d.radius)
                  .attr("fill", d => d.color)
                  .call(drag(simulation));

              // Labels
              const labels = g.append("g")
                .selectAll("text")
                .data(data.nodes)
                .join("text")
                .text(d => d.label)
                .attr("dx", 15)
                .attr("dy", 4);

              // Tooltip logic
              const tooltip = d3.select("#tooltip");
              
              node.on("mouseover", (event, d) => {{
                  tooltip.transition().duration(200).style("opacity", .9);
                  tooltip.html(d.tooltip ? d.tooltip.replace(/\\n/g, "<br>") : d.id)
                    .style("left", (event.pageX + 10) + "px")
                    .style("top", (event.pageY - 28) + "px");
                  
                  // Highlight connections
                  link.attr("stroke", l => (l.source === d || l.target === d) ? "#fff" : "#999")
                      .attr("stroke-opacity", l => (l.source === d || l.target === d) ? 1 : 0.1);
              }})
              .on("mouseout", d => {{
                  tooltip.transition().duration(500).style("opacity", 0);
                  link.attr("stroke", "#999").attr("stroke-opacity", 0.6);
              }})
              .on("click", (event, d) => {{
                  if (d.url && d.url !== '#') {{
                      window.open(d.url, '_blank');
                  }}
              }});

              simulation.on("tick", () => {{
                link
                    .attr("x1", d => d.source.x)
                    .attr("y1", d => d.source.y)
                    .attr("x2", d => d.target.x)
                    .attr("y2", d => d.target.y);

                node
                    .attr("cx", d => d.x)
                    .attr("cy", d => d.y);
                    
                labels
                    .attr("x", d => d.x)
                    .attr("y", d => d.y);
              }});

              function drag(simulation) {{
                function dragstarted(event) {{
                  if (!event.active) simulation.alphaTarget(0.3).restart();
                  event.subject.fx = event.subject.x;
                  event.subject.fy = event.subject.y;
                }}
                
                function dragged(event) {{
                  event.subject.fx = event.x;
                  event.subject.fy = event.y;
                }}
                
                function dragended(event) {{
                  if (!event.active) simulation.alphaTarget(0);
                  event.subject.fx = null;
                  event.subject.fy = null;
                }}
                
                return d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended);
              }}
              
              log("Render complete.");
              
          }} catch (e) {{
              log("Exec Error: " + e.message);
          }}
        </script>
      </body>
    </html>
    """
    
    # Render component
    components.html(html_code, height=height, scrolling=False)
