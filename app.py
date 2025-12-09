# # app.py
# import streamlit as st
# import asyncio
# import time
# from streamlit_extras.stylable_container import stylable_container
# import base64
# from datetime import datetime
# from master_agent import MasterAgent

# # -----------------------
# # Streamlit Page Settings
# # -----------------------
# st.set_page_config(
#     page_title="IntelliDrug AI",
#     page_icon="🧬",
#     layout="wide",
#     initial_sidebar_state="collapsed"
# )

# st.title("🧬 IntelliDrug AI - Drug Repurposing Analysis")
# st.markdown("""
# Automated multi-agent analysis of molecules for drug repurposing.
# """)

# # -----------------------
# # Sidebar
# # -----------------------
# st.sidebar.header("Settings")
# st.sidebar.markdown("### Quick Stats")
# st.sidebar.metric("Analyses this month", "60")
# st.sidebar.markdown("---")
# st.sidebar.markdown("### About")
# st.sidebar.info(
#     "IntelliDrug AI leverages multiple intelligent agents "
#     "to analyze patent, clinical, market, and internal company data."
# )

# # -----------------------
# # Input Fields
# # -----------------------
# molecule_name = st.text_input("Molecule Name", value="Metformin")
# disease_name = st.text_input("Disease Name", value="NASH")
# analyze_button = st.button("Run Analysis")

# # -----------------------
# # Initialize MasterAgent
# # -----------------------
# master_agent = MasterAgent()

# # -----------------------
# # Run Analysis
# # -----------------------
# if analyze_button:
#     if not molecule_name or not disease_name:
#         st.warning("Please enter both molecule and disease.")
#     else:
#         st.info(f"Starting analysis for **{molecule_name}** and **{disease_name}**...")
        
#         # Placeholder for real-time progress
#         progress_placeholders = {}
#         for agent in master_agent.agents.keys():
#             progress_placeholders[agent] = st.empty()

#         progress_bar = st.sidebar.progress(0)
#         status_text = st.sidebar.empty()

#         async def run_analysis():
#             # Run MasterAgent asynchronously
#             task = asyncio.create_task(
#                 master_agent.analyze_repurposing_async(molecule_name, disease_name)
#             )

#             # Update progress periodically
#             while not task.done():
#                 progress = master_agent.get_analysis_progress()
#                 completed = sum([1 for s in progress.values() if s == "Complete"])
#                 total = len(progress)
#                 percent = int((completed / total) * 100)
#                 progress_bar.progress(percent)
#                 status_text.text(f"Progress: {percent}%")
                
#                 # Update each agent box
#                 for name, ph in progress_placeholders.items():
#                     state = progress.get(name, "Pending")
#                     if state == "Complete":
#                         emoji = "✅"
#                     elif state == "Running":
#                         emoji = "⏳"
#                     elif state == "Failed":
#                         emoji = "❌"
#                     else:
#                         emoji = "⏸️"
#                     ph.markdown(f"**{name.replace('_',' ').title()}** {emoji} {state}")
                
#                 await asyncio.sleep(0.5)

#             # Ensure last update
#             progress = master_agent.get_analysis_progress()
#             for name, ph in progress_placeholders.items():
#                 state = progress.get(name, "Pending")
#                 emoji = "✅" if state=="Complete" else ("❌" if state=="Failed" else "⏸️")
#                 ph.markdown(f"**{name.replace('_',' ').title()}** {emoji} {state}")

#             return await task

#         # Run asyncio loop in Streamlit
#         all_results = asyncio.run(run_analysis())

#         st.success("✅ Analysis Complete!")
#         progress_bar.progress(100)
#         status_text.text("All agents finished.")

#         # -----------------------
#         # Display Results in Tabs
#         # -----------------------
#         tabs = st.tabs(["Executive Summary", "Detailed Analysis", "Risk Assessment", "Report Download"])

#         # --- Tab 1: Executive Summary ---
#         with tabs[0]:
#             st.subheader("Overall Recommendation")
#             rec = all_results.get("master_synthesis", {}).get("recommendation", "N/A")
#             confidence = all_results.get("master_synthesis", {}).get("overall_confidence", 0)
            
#             # Color-coded badge
#             color = {"PROCEED":"#28a745","CAUTION":"#ffc107","REJECT":"#dc3545"}.get(rec,"#6c757d")
#             st.markdown(f"<h1 style='color:{color}'>{rec}</h1>", unsafe_allow_html=True)
#             st.markdown(f"**Confidence Score:** {confidence*100:.1f}%")

#             key_factors = all_results.get("master_synthesis", {}).get("key_factors", [])
#             if key_factors:
#                 st.markdown("**Key Factors:**")
#                 for item in key_factors:
#                     st.markdown(f"- {item}")

#         # --- Tab 2: Detailed Analysis ---
#         with tabs[1]:
#             for agent_name, result in all_results.items():
#                 if agent_name in master_agent.agents:
#                     with st.expander(agent_name.replace("_"," ").title()):
#                         conf = result.get("confidence","N/A")
#                         st.write(f"**Confidence:** {conf}")
#                         if "error" in result:
#                             st.error(f"Error: {result['error']}")
#                         else:
#                             for k,v in result.items():
#                                 st.write(f"**{k}:** {v}")

#         # --- Tab 3: Risk Assessment ---
#         with tabs[2]:
#             risks = []
#             for agent_name, result in all_results.items():
#                 if isinstance(result, dict) and "risks" in result:
#                     risks.extend(result["risks"])
#             if risks:
#                 st.markdown("### Identified Risks")
#                 for r in risks:
#                     st.markdown(f"- ⚠️ {r}")
#             else:
#                 st.markdown("No significant risks identified.")

#         # --- Tab 4: Report Download ---
#         with tabs[3]:
#             pdf_file = all_results.get("pdf_report")
#             if pdf_file:
#                 st.markdown("### Download Full PDF Report")
#                 with open(pdf_file, "rb") as f:
#                     st.download_button("📄 Download PDF", f, file_name=pdf_file.split("/")[-1])
# app.py - Modern IntelliDrug AI with Beautiful UI
import streamlit as st
import asyncio
from datetime import datetime
from master_agent import MasterAgent

# ======================================================================================
# PAGE CONFIGURATION
# ======================================================================================
st.set_page_config(
    page_title="IntelliDrug AI - Drug Repurposing",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ======================================================================================
# CUSTOM CSS - MODERN DESIGN WITH ANIMATIONS
# ======================================================================================
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    /* ==================== GLOBAL STYLES ==================== */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit branding and sidebar */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display: none;}
    section[data-testid="stSidebar"] {display: none;}
    
    /* Remove default padding */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    /* ==================== ANIMATED GRADIENT BACKGROUND ==================== */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* ==================== FLOATING PARTICLES BACKGROUND ==================== */
    .particle {
        position: fixed;
        width: 3px;
        height: 3px;
        background: rgba(78, 205, 196, 0.4);
        border-radius: 50%;
        pointer-events: none;
        z-index: 0;
    }
    
    /* ==================== HERO SECTION ==================== */
    .hero-section {
        text-align: center;
        padding: 60px 20px;
        margin-bottom: 40px;
        position: relative;
        z-index: 1;
    }
    
    .hero-title {
        font-size: 4rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
        animation: fadeInDown 1s ease;
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: rgba(255, 255, 255, 0.8);
        font-weight: 300;
        animation: fadeInUp 1s ease 0.2s both;
    }
    
    .hero-description {
        font-size: 1.1rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 15px;
        animation: fadeInUp 1s ease 0.4s both;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* ==================== GLASSMORPHISM CARDS ==================== */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 30px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: all 0.3s ease;
        animation: fadeIn 0.8s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(78, 205, 196, 0.2);
        border-color: rgba(78, 205, 196, 0.3);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
    
    /* ==================== INPUT FIELDS ==================== */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.08);
        border: 2px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        color: white;
        font-size: 16px;
        padding: 15px 20px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        background: rgba(255, 255, 255, 0.12);
        border-color: #4ECDC4;
        box-shadow: 0 0 20px rgba(78, 205, 196, 0.4);
        transform: scale(1.02);
    }
    
    .stTextInput > label {
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 600;
        font-size: 1.1rem;
        margin-bottom: 8px;
    }
    
    /* ==================== BUTTONS ==================== */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 15px 40px;
        font-size: 18px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        cursor: pointer;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(102, 126, 234, 0.6);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* ==================== PROGRESS SECTION ==================== */
    .agent-status {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #4ECDC4;
        transition: all 0.3s ease;
        animation: slideInLeft 0.5s ease;
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .agent-status.running {
        border-left-color: #ffc107;
        animation: pulse 2s ease infinite;
    }
    
    .agent-status.complete {
        border-left-color: #28a745;
    }
    
    .agent-status.failed {
        border-left-color: #dc3545;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    /* ==================== PROGRESS BAR ==================== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #4ECDC4, #44A08D);
        border-radius: 10px;
    }
    
    /* ==================== TABS ==================== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.05);
        padding: 10px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.7);
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.1);
        color: white;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
    }
    
    /* ==================== RECOMMENDATION BADGE ==================== */
    .recommendation-badge {
        padding: 40px;
        border-radius: 20px;
        text-align: center;
        font-size: 3rem;
        font-weight: 700;
        margin: 30px 0;
        animation: fadeInScale 0.6s ease;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    }
    
    .recommendation-proceed {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
    }
    
    .recommendation-caution {
        background: linear-gradient(135deg, #ffc107 0%, #ff9800 100%);
        color: white;
    }
    
    .recommendation-reject {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
    }
    
    @keyframes fadeInScale {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    /* ==================== METRIC CARDS ==================== */
    .metric-card {
        background: rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: rgba(78, 205, 196, 0.5);
        box-shadow: 0 8px 30px rgba(78, 205, 196, 0.2);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4ECDC4;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 1rem;
        color: rgba(255, 255, 255, 0.7);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* ==================== EXPANDER ==================== */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        color: white;
        font-weight: 600;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.1);
    }
    
    /* ==================== SUCCESS/WARNING/ERROR MESSAGES ==================== */
    .stSuccess, .stWarning, .stError, .stInfo {
        border-radius: 12px;
        backdrop-filter: blur(10px);
    }
    
    /* ==================== LOADING ANIMATION ==================== */
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-top-color: #4ECDC4;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
</style>
""", unsafe_allow_html=True)

# ======================================================================================
# FLOATING PARTICLES BACKGROUND
# ======================================================================================
# ======================================================================================
# FLOATING PARTICLES BACKGROUND (Pure CSS - No HTML Generation)
# ======================================================================================
st.markdown("""
<style>
/* Animated particle effect using CSS only */
.stApp::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: 
        radial-gradient(2px 2px at 20% 30%, rgba(78, 205, 196, 0.4), transparent),
        radial-gradient(2px 2px at 60% 70%, rgba(78, 205, 196, 0.3), transparent),
        radial-gradient(3px 3px at 50% 50%, rgba(78, 205, 196, 0.4), transparent),
        radial-gradient(2px 2px at 80% 10%, rgba(78, 205, 196, 0.3), transparent),
        radial-gradient(2px 2px at 90% 60%, rgba(78, 205, 196, 0.4), transparent),
        radial-gradient(3px 3px at 30% 80%, rgba(78, 205, 196, 0.3), transparent),
        radial-gradient(2px 2px at 15% 90%, rgba(78, 205, 196, 0.4), transparent),
        radial-gradient(3px 3px at 75% 25%, rgba(78, 205, 196, 0.3), transparent),
        radial-gradient(2px 2px at 40% 60%, rgba(78, 205, 196, 0.4), transparent),
        radial-gradient(2px 2px at 95% 85%, rgba(78, 205, 196, 0.3), transparent);
    background-size: 200% 200%;
    animation: particleFloat 25s ease-in-out infinite;
    pointer-events: none;
    z-index: 0;
    opacity: 0.5;
}

@keyframes particleFloat {
    0%, 100% { 
        background-position: 0% 0%, 100% 100%, 50% 50%, 100% 0%, 0% 100%, 75% 25%, 25% 75%, 60% 40%, 40% 60%, 90% 10%;
        transform: translateY(0);
    }
    50% { 
        background-position: 100% 100%, 0% 0%, 75% 75%, 50% 50%, 100% 0%, 25% 75%, 75% 25%, 40% 60%, 60% 40%, 10% 90%;
        transform: translateY(-20px);
    }
}
</style>
""", unsafe_allow_html=True)

# ======================================================================================
# HERO SECTION
# ======================================================================================
st.markdown("""
<div class="hero-section">
    <div class="hero-title">🧬 IntelliDrug AI</div>
    <div class="hero-subtitle">Accelerating Drug Discovery with Multi-Agent Intelligence</div>
    <div class="hero-description">Transform 90 days of research into 4 hours with AI-powered analysis</div>
</div>
""", unsafe_allow_html=True)

# ======================================================================================
# INPUT SECTION - GLASSMORPHISM CARDS
# ======================================================================================
st.markdown('<div class="glass-card">', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 💊 Molecule Name")
    molecule_name = st.text_input(
        "Molecule Name",
        value="Metformin",
        placeholder="e.g., Metformin, Aspirin, Semaglutide",
        label_visibility="collapsed"
    )

with col2:
    st.markdown("### 🦠 Disease Target")
    disease_name = st.text_input(
        "Disease Name",
        value="NASH",
        placeholder="e.g., NASH, Diabetes, Cancer",
        label_visibility="collapsed"
    )

st.markdown("</div>", unsafe_allow_html=True)

# ======================================================================================
# ANALYZE BUTTON
# ======================================================================================
analyze_button = st.button("▶ Run Comprehensive Analysis", use_container_width=True)

# ======================================================================================
# INITIALIZE MASTER AGENT
# ======================================================================================
master_agent = MasterAgent()

# ======================================================================================
# RUN ANALYSIS
# ======================================================================================
if analyze_button:
    if not molecule_name or not disease_name:
        st.warning("⚠️ Please enter both molecule and disease names to proceed.")
    else:
        # ======================================================================================
        # PROGRESS SECTION
        # ======================================================================================
        st.markdown(f"""
        <div class="glass-card" style="text-align: center;">
            <h3 style="margin: 0; color: white;">🔬 Analyzing <strong>{molecule_name}</strong> for <strong>{disease_name}</strong></h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Create placeholders for agent status (no wrapper needed)
        progress_placeholders = {}
        for agent_key in master_agent.agents.keys():
            progress_placeholders[agent_key] = st.empty()
        
        # Progress bar
        progress_bar = st.progress(0)
        
        # ======================================================================================
        # ASYNC ANALYSIS WITH REAL-TIME UPDATES
        # ======================================================================================
        async def run_analysis():
            task = asyncio.create_task(
                master_agent.analyze_repurposing_async(molecule_name, disease_name)
            )
            
            while not task.done():
                progress = master_agent.get_analysis_progress()
                completed = sum([1 for s in progress.values() if s == "Complete"])
                total = len(progress)
                percent = int((completed / total) * 100)
                progress_bar.progress(percent)
                
                # Update each agent status with styling
                for agent_key, placeholder in progress_placeholders.items():
                    state = progress.get(agent_key, "Pending")
                    agent_name = agent_key.replace("_", " ").title()
                    
                    if state == "Complete":
                        emoji = "✅"
                        status_class = "complete"
                    elif state == "Running":
                        emoji = "⏳"
                        status_class = "running"
                    elif state == "Failed":
                        emoji = "❌"
                        status_class = "failed"
                    else:
                        emoji = "⏸️"
                        status_class = ""
                    
                    placeholder.markdown(
                        f'<div class="agent-status {status_class}">'
                        f'<strong>{emoji} {agent_name}</strong> - {state}'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                
                await asyncio.sleep(0.5)
            
            # Final update
            progress_bar.progress(100)
            return await task
        
        # Run analysis
        all_results = asyncio.run(run_analysis())
        
        st.success("✅ Analysis Complete! Review your results below.")
        
        # ======================================================================================
        # RESULTS SECTION WITH TABS
        # ======================================================================================
        tabs = st.tabs(["📊 Executive Summary", "🔍 Detailed Analysis", "⚠️ Risk Assessment", "📄 Download Report"])
        
        # ==================== TAB 1: EXECUTIVE SUMMARY ====================
        with tabs[0]:
            synthesis = all_results.get("master_synthesis", {})
            recommendation = synthesis.get("recommendation", "N/A")
            confidence = synthesis.get("overall_confidence", 0)
            
            # Recommendation Badge
            badge_class = f"recommendation-{recommendation.lower()}"
            st.markdown(
                f'<div class="recommendation-badge {badge_class}">{recommendation}</div>',
                unsafe_allow_html=True
            )
            
            # Metric Cards
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-label">Confidence Score</div>'
                    f'<div class="metric-value">{confidence*100:.1f}%</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            with col2:
                trials = all_results.get("clinical_analysis", {}).get("active_trials", "N/A")
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-label">Active Trials</div>'
                    f'<div class="metric-value">{trials}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            with col3:
                market_size = all_results.get("market_analysis", {}).get("market_size", "N/A")
                st.markdown(
                    f'<div class="metric-card">'
                    f'<div class="metric-label">Market Size</div>'
                    f'<div class="metric-value">{market_size}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            
            # Key Findings
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### 🎯 Key Findings")
            key_factors = synthesis.get("key_factors", [])
            if key_factors:
                for item in key_factors:
                    st.markdown(f"✦ {item}")
            else:
                st.markdown("No key findings available.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # ==================== TAB 2: DETAILED ANALYSIS ====================
        with tabs[1]:
            for agent_key, result in all_results.items():
                if agent_key in master_agent.agents:
                    agent_name = agent_key.replace("_", " ").title()
                    with st.expander(f"🔬 {agent_name}"):
                        if isinstance(result, dict):
                            conf = result.get("confidence", "N/A")
                            st.markdown(f"**Confidence:** {conf}")
                            
                            if "error" in result:
                                st.error(f"❌ Error: {result['error']}")
                            else:
                                for k, v in result.items():
                                    if k != "confidence":
                                        st.markdown(f"**{k.replace('_', ' ').title()}:** {v}")
        
        # ==================== TAB 3: RISK ASSESSMENT ====================
        with tabs[2]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            risks = synthesis.get("risks", [])
            if risks and risks != ["No major risks identified"]:
                st.markdown("### ⚠️ Identified Risks")
                for risk in risks:
                    st.markdown(f"🔴 {risk}")
            else:
                st.success("✅ No significant risks identified")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # ==================== TAB 4: REPORT DOWNLOAD ====================
        with tabs[3]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            pdf_file = all_results.get("pdf_report")
            if pdf_file:
                st.markdown("### 📄 Download Comprehensive Report")
                st.markdown("Your detailed analysis report is ready for download.")
                try:
                    with open(pdf_file, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF Report",
                            data=f,
                            file_name=f"{molecule_name}_{disease_name}_analysis.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"Error loading PDF: {e}")
            else:
                st.warning("PDF report not available.")
            st.markdown("</div>", unsafe_allow_html=True)

# ======================================================================================
# FOOTER
# ======================================================================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: rgba(255, 255, 255, 0.5); padding: 20px;">
        <p>IntelliDrug AI © 2025 | Powered by Multi-Agent Systems & Google Gemini</p>
        <p style="font-size: 0.9rem;">Accelerating pharmaceutical innovation through artificial intelligence</p>
    </div>
    """,
    unsafe_allow_html=True
)