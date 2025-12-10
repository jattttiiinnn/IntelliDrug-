"""
visualization_components.py

Contains functions for creating interactive visualizations for the dashboard.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, Any, List, Optional

def create_risk_radar(analysis_results: Dict[str, Any]) -> go.Figure:
    """
    Create a radar chart showing risk breakdown across different categories.
    
    Args:
        analysis_results: Dictionary containing analysis results from all agents
        
    Returns:
        plotly.graph_objects.Figure: Interactive radar chart
    """
    # Extract risk scores from agent outputs
    risk_scores = {
        'Patent Risk': analysis_results.get('patent_analysis', {}).get('risk_score', 50),
        'Clinical Risk': analysis_results.get('clinical_analysis', {}).get('risk_score', 50),
        'Market Risk': analysis_results.get('market_analysis', {}).get('risk_score', 50),
        'Safety Risk': analysis_results.get('safety_analysis', {}).get('risk_score', 50),
        'Competition': analysis_results.get('market_analysis', {}).get('competition_score', 50),
        'Strategic Fit': analysis_results.get('internal_analysis', {}).get('strategic_fit_score', 50)
    }
    
    categories = list(risk_scores.keys())
    values = list(risk_scores.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],  # Close the radar
        theta=categories + [categories[0]],  # Close the radar
        fill='toself',
        name='Risk Score',
        line=dict(color='#636EFA'),
        hovertemplate='%{theta}: %{r:.1f}%<extra></extra>'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[0, 25, 50, 75, 100],
                ticktext=['0%', '25%', '50%', '75%', '100%'],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                rotation=90,
                direction="clockwise"
            )
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        height=400
    )
    
    return fig

def create_timeline_gantt(analysis_results: Dict[str, Any]) -> go.Figure:
    """
    Create a Gantt chart showing the development timeline.
    
    Args:
        analysis_results: Dictionary containing analysis results
        
    Returns:
        plotly.graph_objects.Figure: Interactive Gantt chart
    """
    # Extract timeline data from clinical trials agent
    clinical_data = analysis_results.get('clinical_analysis', {})
    
    # Default timeline estimates (in months from now)
    phases = [
        dict(Task="Preclinical", Start=0, Finish=12, Resource="Phase"),
        dict(Task="Phase 1", Start=12, Finish=24, Resource="Phase"),
        dict(Task="Phase 2", Start=24, Finish=36, Resource="Phase"),
        dict(Task="Phase 3", Start=36, Finish=60, Resource="Phase"),
        dict(Task="FDA Review", Start=60, Finish=72, Resource="Phase")
    ]
    
    # Update with actual data if available
    if 'estimated_timeline' in clinical_data:
        # Convert timeline estimates to months from now
        # This is a simplified example - adjust based on your actual data structure
        pass
    
    df = pd.DataFrame(phases)
    
    # Define colors for each phase
    colors = {
        'Preclinical': '#636EFA',
        'Phase 1': '#EF553B',
        'Phase 2': '#00CC96',
        'Phase 3': '#AB63FA',
        'FDA Review': '#FFA15A'
    }
    
    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Task",
        color_discrete_map=colors,
        title="Development Timeline"
    )
    
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
        xaxis_title="Months from Now",
        yaxis_title=""
    )
    
    return fig

def create_market_funnel(analysis_results: Dict[str, Any]) -> go.Figure:
    """
    Create a funnel chart showing market opportunity.
    
    Args:
        analysis_results: Dictionary containing analysis results
        
    Returns:
        plotly.graph_objects.Figure: Interactive funnel chart
    """
    market_data = analysis_results.get('market_analysis', {})
    
    # Default values (in billions)
    total_market = market_data.get('total_market_size', 50)  # Default $50B
    addressable_market = total_market * 0.3  # 30% of total market
    target_segment = addressable_market * 0.2  # 20% of addressable market
    
    fig = go.Figure(go.Funnel(
        y=["Total Market", "Addressable Market", "Target Segment"],
        x=[total_market, addressable_market, target_segment],
        textposition="inside",
        textinfo="value+percent initial",
        opacity=0.8,
        marker={"color": ["#636EFA", "#00CC96", "#FFA15A"]},
        connector={"line": {"color": "#7fafdf", "width": 2}},
        textfont={"family": "Arial", "size": 14},
        hovertemplate="%{y}: $%{x:,.2f}B<extra></extra>"
    ))
    
    fig.update_layout(
        title="Market Opportunity (Billions USD)",
        height=400,
        margin=dict(l=40, r=40, t=40, b=40),
        yaxis_title="",
        xaxis_title="Market Size (Billions USD)",
        showlegend=False
    )
    
    return fig

def export_dashboard(figures: Dict[str, go.Figure], filename: str = "dashboard.html") -> str:
    """
    Export the dashboard figures to an interactive HTML file.
    
    Args:
        figures: Dictionary of {figure_name: figure_object}
        filename: Output filename
        
    Returns:
        str: Path to the exported HTML file
    """
    import plotly.io as pio
    from pathlib import Path
    
    # Create HTML content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Drug Repurposing Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .dashboard-container { max-width: 1200px; margin: 0 auto; }
            .dashboard-row { display: flex; margin-bottom: 20px; }
            .dashboard-col { flex: 1; margin: 0 10px; }
            .dashboard-widget { 
                background: white; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                padding: 15px;
                margin-bottom: 20px;
            }
            .widget-title { 
                font-size: 18px; 
                font-weight: bold; 
                margin-bottom: 15px;
                color: #2c3e50;
            }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <h1>Drug Repurposing Analysis Dashboard</h1>
            <div class="dashboard-row">
                <div class="dashboard-col">
                    <div class="dashboard-widget">
                        <div class="widget-title">Risk Breakdown</div>
                        <div id="risk-radar"></div>
                    </div>
                </div>
                <div class="dashboard-col">
                    <div class="dashboard-widget">
                        <div class="widget-title">Market Opportunity</div>
                        <div id="market-funnel"></div>
                    </div>
                </div>
            </div>
            <div class="dashboard-row">
                <div class="dashboard-col">
                    <div class="dashboard-widget">
                        <div class="widget-title">Development Timeline</div>
                        <div id="timeline-gantt"></div>
                    </div>
                </div>
            </div>
        </div>
        <script>
    """
    
    # Add figure data to the HTML
    for fig_name, fig in figures.items():
        fig_json = fig.to_json()
        html_content += f"var {fig_name} = {fig_json};\n"
    
    # Add plotly initialization
    html_content += """
            // Initialize all plots when the page loads
            document.addEventListener('DOMContentLoaded', function() {
    """
    
    # Add plot initialization for each figure
    for fig_name in figures.keys():
        div_id = fig_name.replace('_', '-')  # Convert to HTML ID format
        html_content += f"""
                Plotly.newPlot('{div_id}', {fig_name}.data, {fig_name}.layout);
        """
    
    # Close the script and HTML
    html_content += """
            });
        </script>
    </body>
    </html>
    """
    
    # Create output directory if it doesn't exist
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)
    
    # Write to file
    output_path = output_dir / filename
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return str(output_path.absolute())
