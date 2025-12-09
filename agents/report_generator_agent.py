import os
import logging
from datetime import datetime
from typing import Dict, Any
from fpdf import FPDF

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReportGeneratorAgent:
    """
    Agent responsible for generating structured PDF reports
    summarizing all IntelliDrug AI analyses.
    """

    def __init__(self, output_dir: str = "reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------
    # Utility: Add section header
    # -------------------------------------------------------
    def _add_section_header(self, pdf: FPDF, title: str, color: tuple = (0, 51, 102)):
        pdf.set_fill_color(*color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 13)  # Reduced from 14
        pdf.cell(0, 9, f"  {title}", ln=True, fill=True)
        pdf.ln(3)
        pdf.set_text_color(0, 0, 0)

    # -------------------------------------------------------
    # Utility: Add bullet points
    # -------------------------------------------------------
    def _add_bullets(self, pdf: FPDF, items):
        pdf.set_font("Arial", "", 11)
        if not items:
            return
        for item in items:
            if item:
                clean_item = str(item).strip()
                if clean_item:
                    try:
                        # Use write() instead of multi_cell() to avoid space bug
                        pdf.write(7, f"- {clean_item}")
                        pdf.ln(8)
                    except Exception as e:
                        logger.warning(f"Could not add bullet: {e}")
        pdf.ln(3)

    # -------------------------------------------------------
    # Utility: Add key-value data block
    # -------------------------------------------------------
    def _add_kv_block(self, pdf: FPDF, data: Dict[str, Any]):
        pdf.set_font("Arial", "", 12)  # Changed from Helvetica to Arial
        for k, v in data.items():
            try:
                key_text = str(k)[:100]  # Limit key length
                value_text = str(v)[:500] if v is not None else "N/A"  # Handle None values
                
                # Use single multi_cell to avoid horizontal space issues
                combined_text = f"{key_text}: {value_text}"
                pdf.multi_cell(0, 8, combined_text)
                
            except Exception as e:
                logger.warning(f"Could not add key-value pair {k}: {e}")
                try:
                    pdf.ln(8)
                except:
                    pass
        pdf.ln(4)

    # -------------------------------------------------------
    # Helper: Determine recommendation color
    # -------------------------------------------------------
    def _recommendation_color(self, recommendation: str):
        rec = recommendation.upper()
        if rec == "PROCEED":
            return (0, 153, 0)
        elif rec == "CAUTION":
            return (255, 204, 0)
        elif rec == "REJECT":
            return (204, 0, 0)
        return (128, 128, 128)

    # -------------------------------------------------------
    # Main: Generate PDF Report
    # -------------------------------------------------------
    def generate_report(self, molecule_name: str, disease_name: str, all_agent_results: Dict[str, Any]) -> str:
        """
        Generate a multi-page PDF summarizing all agent analyses.
        Returns the filepath to the generated PDF.
        """
        logger.info(f"Generating report for {molecule_name} - {disease_name}")

        pdf = FPDF()
        # Set minimal margins for maximum space
        pdf.set_left_margin(10)
        pdf.set_right_margin(10)
        pdf.set_top_margin(10)
        pdf.set_auto_page_break(auto=True, margin=10)

        # -----------------------------
        # PAGE 1: Cover Page
        # -----------------------------
        pdf.add_page()
        pdf.set_font("Arial", "B", 24)  # Reduced from 28
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 18, "IntelliDrug AI Analysis Report", ln=True, align="C")
        pdf.ln(8)
        pdf.set_font("Arial", "", 18)  # Reduced from 20
        pdf.cell(0, 12, f"{molecule_name} for {disease_name}", ln=True, align="C")
        pdf.ln(15)

        # Date
        pdf.set_font("Arial", "I", 12)  # Changed from Helvetica
        pdf.cell(0, 10, f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", ln=True, align="C")
        pdf.ln(20)

        # Overall Confidence and Recommendation
        master = all_agent_results.get("master_synthesis", {})
        
        # Handle case where master might be a coroutine
        import inspect
        if inspect.iscoroutine(master):
            logger.error("master_synthesis is a coroutine - forgot to await?")
            master = {}
        
        overall_confidence = master.get("overall_confidence", 0)
        recommendation = master.get("recommendation", "Unknown")

        color = self._recommendation_color(recommendation)
        pdf.set_font("Arial", "B", 22)  # Changed from Helvetica
        pdf.set_text_color(*color)
        pdf.cell(0, 15, f"Recommendation: {recommendation}", ln=True, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(10)
        pdf.set_font("Arial", "", 16)  # Changed from Helvetica
        pdf.cell(0, 10, f"Overall Confidence: {overall_confidence:.2f}", ln=True, align="C")

        # -----------------------------
        # PAGE 2: Executive Summary
        # -----------------------------
        pdf.add_page()
        self._add_section_header(pdf, "Executive Summary")

        key_factors = master.get("key_factors", ["No key findings found."])
        risks = master.get("risks", [])
        confidence_map = {
            "Patent": all_agent_results.get("patent_analysis", {}).get("confidence", 0),
            "Clinical Trials": all_agent_results.get("clinical_trials_analysis", {}).get("confidence", 0),
            "Market": all_agent_results.get("market_analysis", {}).get("confidence", 0),
            "Web Intelligence": all_agent_results.get("web_intelligence_analysis", {}).get("confidence", 0),
            "EXIM": all_agent_results.get("exim_analysis", {}).get("confidence", 0),
            "Internal Knowledge": all_agent_results.get("internal_knowledge_analysis", {}).get("confidence", 0)
        }

        pdf.set_font("Arial", "B", 13)  # Changed from Helvetica
        pdf.cell(0, 10, "Key Findings:", ln=True)
        self._add_bullets(pdf, key_factors)

        pdf.set_font("Arial", "B", 13)  # Changed from Helvetica
        pdf.cell(0, 10, "Risk Factors:", ln=True)
        self._add_bullets(pdf, risks if risks else ["None detected"])

        pdf.set_font("Arial", "B", 13)  # Changed from Helvetica
        pdf.cell(0, 10, "Confidence Breakdown:", ln=True)
        for agent, score in confidence_map.items():
            pdf.cell(0, 8, f"{agent}: {score:.2f}", ln=True)

        # -----------------------------
        # PAGE 3: Patent Analysis
        # -----------------------------
        pdf.add_page()
        self._add_section_header(pdf, "Patent Analysis")
        patent = all_agent_results.get("patent_analysis", {})
        self._add_kv_block(pdf, {
            "Patent Status": patent.get("patent_status", "N/A"),
            "FTO Status": patent.get("fto_status", "N/A"),
            "Expiry Date": patent.get("expiry_date", "N/A"),
            "Confidence": patent.get("confidence", "N/A")
        })
        self._add_bullets(pdf, [patent.get("reasoning", "No reasoning available.")])

        # -----------------------------
        # PAGE 4: Clinical Evidence
        # -----------------------------
        pdf.add_page()
        self._add_section_header(pdf, "Clinical Evidence")
        clinical = all_agent_results.get("clinical_trials_analysis", {})
        self._add_kv_block(pdf, {
            "Active Trials": clinical.get("active_trials", "N/A"),
            "Phases": clinical.get("phases", "N/A"),
            "Confidence": clinical.get("confidence", "N/A")
        })
        sponsors = clinical.get("key_sponsors", [])
        if sponsors:
            self._add_bullets(pdf, [f"Sponsors: {', '.join(sponsors)}"])
        self._add_bullets(pdf, [clinical.get("latest_findings", "No findings available.")])

        # -----------------------------
        # PAGE 5: Market Opportunity
        # -----------------------------
        pdf.add_page()
        self._add_section_header(pdf, "Market Opportunity")
        market = all_agent_results.get("market_analysis", {})
        self._add_kv_block(pdf, {
            "Market Size": market.get("market_size", "N/A"),
            "Growth Rate": market.get("growth_rate", "N/A"),
            "Competition": market.get("competition_level", "N/A"),
            "Confidence": market.get("confidence", "N/A")
        })
        self._add_bullets(pdf, [market.get("key_insights", "No insights available.")])

        # -----------------------------
        # PAGE 6: Additional Intelligence
        # -----------------------------
        pdf.add_page()
        self._add_section_header(pdf, "Additional Intelligence")

        web = all_agent_results.get("web_intelligence_analysis", {})
        exim = all_agent_results.get("exim_analysis", {})
        internal = all_agent_results.get("internal_knowledge_analysis", {})

        pdf.set_font("Arial", "B", 13)  # Changed from Helvetica
        pdf.cell(0, 10, "Scientific Literature Support:", ln=True)
        self._add_kv_block(pdf, {
            "Literature Support": web.get("literature_support", "N/A"),
            "Guidelines Alignment": web.get("guidelines_alignment", "N/A"),
            "Confidence": web.get("confidence", "N/A")
        })
        self._add_bullets(pdf, web.get("key_findings", []) or ["No findings available."])

        pdf.set_font("Arial", "B", 13)  # Changed from Helvetica
        pdf.cell(0, 10, "Sourcing & Trade Analysis:", ln=True)
        self._add_kv_block(pdf, {
            "Import Dependency": exim.get("import_dependency", "N/A"),
            "Sourcing Risk": exim.get("sourcing_risk", "N/A"),
            "Manufacturing Viability": exim.get("manufacturing_viability", "N/A")
        })
        self._add_bullets(pdf, [exim.get("key_insights", "No insights available.")])

        pdf.set_font("Arial", "B", 13)  # Changed from Helvetica
        pdf.cell(0, 10, "Internal Knowledge:", ln=True)
        self._add_kv_block(pdf, {
            "Strategic Alignment": internal.get("strategic_alignment", "N/A"),
            "Manufacturing Capability": internal.get("manufacturing_capability", "N/A"),
            "Confidence": internal.get("confidence", "N/A")
        })
        self._add_bullets(pdf, internal.get("internal_insights", []) or ["No insights available."])

        # -----------------------------
        # PAGE 7: Recommendation & Next Steps
        # -----------------------------
        pdf.add_page()
        self._add_section_header(pdf, "Recommendation & Next Steps", color=color)
        self._add_kv_block(pdf, {
            "Final Recommendation": recommendation,
            "Overall Confidence": f"{overall_confidence:.2f}"
        })
        pdf.set_font("Arial", "", 12)
        next_steps = master.get("next_steps", "No next steps provided.")
        try:
            pdf.write(8, f"Next Steps:\n{str(next_steps)[:1000]}")
            pdf.ln(12)
        except Exception as e:
            logger.warning(f"Could not add next steps: {e}")
        try:
            pdf.write(8, "Suggested Timeline: 6-12 months review cycle.\n"
                         "Risk Mitigation: Secure patent clearance, prioritize phase 2 validation.")
        except Exception as e:
            logger.warning(f"Could not add timeline: {e}")

        # -----------------------------
        # Save PDF
        # -----------------------------
        filename = f"{molecule_name}_{disease_name}_analysis_report.pdf".replace(" ", "_")
        filepath = os.path.join(self.output_dir, filename)
        pdf.output(filepath)
        logger.info(f"Report generated: {filepath}")
        return filepath