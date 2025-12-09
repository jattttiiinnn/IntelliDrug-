"""
conflict_detector.py

Detects conflicting entries in drug repurposing analysis data.
"""

from typing import Dict, Any, List


class ConflictDetector:
    """
    Detect conflicts in results data from multiple sources or entries.
    """

    @staticmethod
    def detect_conflicts(results_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect conflicts for the same molecule across multiple data points.

        Args:
            results_dict (dict): Combined results from MasterAgent.

        Returns:
            dict: Conflict report. If no conflicts, 'conflict_detected' = False.
        """
        conflict_report = {"conflict_detected": False, "conflicts": []}

        # Example: check patent expiry field
        patent_data = results_dict.get("patent_analysis", {})
        if isinstance(patent_data, dict):
            # Check for multiple entries with different expiry dates
            expiry_values = []
            # Support for multiple sources
            if "source_data" in patent_data:
                for entry in patent_data["source_data"]:
                    expiry_values.append(
                        {"source": entry.get("source", "unknown"),
                         "value": entry.get("expiry_date"),
                         "confidence": entry.get("confidence", 0)}
                    )
            else:
                # fallback: single source only
                expiry_values.append({
                    "source": "Generic",
                    "value": patent_data.get("expiry_date"),
                    "confidence": patent_data.get("confidence", 0)
                })

            unique_values = set([v["value"] for v in expiry_values if v["value"]])
            if len(unique_values) > 1:
                conflict_report["conflict_detected"] = True
                conflict_report["conflicts"].append({
                    "field": "patent_expiry",
                    "sources": expiry_values,
                    "resolution": "Use highest confidence source with flag for review"
                })

        return conflict_report
