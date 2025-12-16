
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

def render_competitor_dashboard(competitor_data: dict):
    """
    Renders the Competitive Intelligence Dashboard.
    
    Args:
        competitor_data: Dictionary containing 'competitor_analysis' output from CompetitorAgent.
    """
    if not competitor_data or "competitor_analysis" not in competitor_data:
        st.info("No competitor data available. Run analysis to view intelligence.")
        return

    data = competitor_data["competitor_analysis"]
    
    # --- Custom CSS ---
    st.markdown("""
    <style>
    .comp-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
    }
    .comp-score-high { border-left: 4px solid #ff4b4b; }
    .comp-score-med { border-left: 4px solid #ffa421; }
    .comp-score-low { border-left: 4px solid #21c354; }
    
    .metric-container {
        display: flex;
        justify-content: space-between;
        margin-bottom: 20px;
    }
    .metric-box {
        text-align: center;
        background: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 8px;
        width: 30%;
    }
    .metric-value { font-size: 24px; font-weight: bold; }
    .metric-label { font-size: 14px; opacity: 0.8; }
    
    .alert-badge {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-high { background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; }
    .badge-med { background-color: rgba(255, 164, 33, 0.2); color: #ffa421; }
    .badge-low { background-color: rgba(33, 195, 84, 0.2); color: #21c354; }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🔍 Competitive Landscape")
    
    tabs = st.tabs(["📊 Overview", "⏳ Timeline", "🚨 Alerts", "🌡️ Heatmap"])
    
    # --- 1. OVERVIEW TAB ---
    with tabs[0]:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Metrics
            total_active = data.get("total_active_trials", 0)
            top_comp_count = len(data.get("top_competitors", []))
            alerts_count = len(data.get("alerts", []))
            
            st.markdown(f"""
            <div class="metric-container">
                <div class="metric-box">
                    <div class="metric-value">{total_active}</div>
                    <div class="metric-label">Active Trials</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value">{top_comp_count}</div>
                    <div class="metric-label">Key Competitors</div>
                </div>
                <div class="metric-box">
                    <div class="metric-value" style="color: {'#ff4b4b' if alerts_count > 0 else 'inherit'}">{alerts_count}</div>
                    <div class="metric-label">New Alerts</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Phase Breakdown Chart
            phases = data.get("phase_breakdown", {})
            if phases:
                df_ph = pd.DataFrame(list(phases.items()), columns=["Phase", "Count"])
                fig_pie = px.pie(df_ph, values="Count", names="Phase", title="Trials by Phase", hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No phase data available.")

        with col2:
            st.markdown("### Top Competitors")
            for comp in data.get("top_competitors", []):
                # We don't have the pre-calculated score passed directly in top_competitors dict usually,
                # unless we updated the Analyze method to include it. Data from agent has: {'name': 'X', 'trial_count': Y}
                # We can mock a visual score or simple bar.
                name = comp.get("drug", comp.get("name", "Unknown"))
                count = comp.get("trial_count", 0)
                
                # Heuristic color
                border_class = "comp-score-low"
                if count > 5: border_class = "comp-score-high"
                elif count > 2: border_class = "comp-score-med"
                
                st.markdown(f"""
                <div class="comp-card {border_class}">
                    <div style="font-weight:bold;">{name}</div>
                    <div style="font-size:12px; opacity:0.7;">{count} Active Trials</div>
                </div>
                """, unsafe_allow_html=True)

    # --- 2. TIMELINE TAB ---
    with tabs[1]:
        st.markdown("### 📅 Trial Activity Timeline")
        details = data.get("details", [])
        if details:
            timeline_data = []
            for d in details:
                start = d.get("start_date", "Unknown")
                if start != "Unknown" and start:
                    # Fix partial dates
                    if len(start.split('-')) == 2: start += "-01"
                    if len(start.split('-')) == 1: start += "-01-01"
                    
                    timeline_data.append({
                        "Task": d.get("drug_name", "Unknown"),
                        "Start": start,
                        "Finish": datetime.now().strftime("%Y-%m-%d"), # Assume active helps visualization
                        "Phase": d.get("phase", "Unknown"),
                        "Title": d.get("title", "")
                    })
            
            if timeline_data:
                df_tl = pd.DataFrame(timeline_data)
                fig_tl = px.timeline(df_tl, x_start="Start", x_end="Finish", y="Task", color="Phase", hover_data=["Title"],
                                     title="Active Trials Timeline (Start Date to Present)")
                fig_tl.update_yaxes(autorange="reversed")
                fig_tl.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_tl, use_container_width=True)
            else:
                st.info("No valid dates found for timeline.")
        else:
            st.info("No detailed trial data available.")

    # --- 3. ALERTS TAB ---
    with tabs[2]:
        st.markdown("### 🚨 Competitive Alerts")
        alerts = data.get("alerts", [])
        if alerts:
            for alert in alerts:
                sev = alert.get("severity", "Low")
                badge_class = f"badge-{sev.lower()}"
                icon = "🔴" if sev == "High" else "🟡" if sev == "Medium" else "🟢"
                
                with st.expander(f"{icon} {alert.get('action_type')} - {alert.get('drug_name')}"):
                    st.markdown(f"""
                    <span class="alert-badge {badge_class}">{sev.upper()} PRIORITY</span>
                    <br><br>
                    **Date:** {alert.get('date')}<br>
                    **Competitor:** {alert.get('competitor_name')}<br>
                    **Details:** {alert.get('details')}
                    """, unsafe_allow_html=True)
        else:
            st.success("✅ No recent alerts detected.")

    # --- 4. HEATMAP TAB ---
    with tabs[3]:
        st.markdown("### 🔥 Competitive Threat Heatmap")
        
        # Mocking a heatmap based on phases
        # For a real app, this would be computed by the agent.
        # Matrix: Drug vs Phase
        
        if details:
            # Aggregate data for heatmap
            heatmap_data = []
            for d in details:
                heatmap_data.append({
                    "Drug": d.get("drug_name"),
                    "Phase": d.get("phase"),
                    "Count": 1
                })
            
            if heatmap_data:
                df_hm = pd.DataFrame(heatmap_data)
                df_pivot = df_hm.pivot_table(index="Drug", columns="Phase", values="Count", aggfunc='count', fill_value=0)
                
                fig_hm = px.imshow(df_pivot, text_auto=True, aspect="auto", color_continuous_scale="Reds",
                                   title="Trial Concentration by Phase")
                fig_hm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_hm, use_container_width=True)
            else:
                st.info("Not enough data for heatmap.")
        else:
            st.info("No data available.")

