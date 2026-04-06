def build_model_b_interpretation(b1_findings: dict, b2_findings: dict) -> dict:
    nuclei_count = b1_findings.get("nuclei_count", 0)
    avg_nuclei_area = b1_findings.get("avg_nuclei_area", 0)
    irregularity_score = b1_findings.get("irregularity_score", 0)
    nuclei_density = str(b1_findings.get("nuclei_density", "unknown")).lower()

    predicted_mitosis_count = b2_findings.get("predicted_mitosis_count", 0)

    # support both names
    mitotic_activity = str(
        b2_findings.get("mitotic_activity")
        or b2_findings.get("mitotic_activity_level")
        or "unknown"
    ).lower()

    grade_support = "Grade support unavailable"
    summary_parts = []

    if nuclei_density == "high":
        summary_parts.append("High nuclei density detected")
    elif nuclei_density == "moderate":
        summary_parts.append("Moderate nuclei density detected")
    elif nuclei_density == "low":
        summary_parts.append("Low nuclei density detected")

    if irregularity_score not in [None, ""]:
        try:
            if float(irregularity_score) > 0.5:
                summary_parts.append("Nuclei show increased shape irregularity")
        except Exception:
            pass

    if mitotic_activity == "high":
        summary_parts.append("High mitotic activity detected")
    elif mitotic_activity == "moderate":
        summary_parts.append("Moderate mitotic activity detected")
    elif mitotic_activity == "low":
        summary_parts.append("Low mitotic activity detected")

    if nuclei_density == "high" and mitotic_activity == "high":
        grade_support = "Grade 3 likely pattern"
    elif nuclei_density in ["moderate", "high"] and mitotic_activity in ["moderate", "high"]:
        grade_support = "Grade 2 likely pattern"
    elif nuclei_density == "low" and mitotic_activity == "low":
        grade_support = "Grade 1 likely pattern"
    else:
        grade_support = "Intermediate grade pattern"

    if not summary_parts:
        summary = (
            "Model B combined analysis completed using nuclei morphology and "
            "mitotic activity. Educational support only."
        )
    else:
        summary = ". ".join(summary_parts) + ". Educational support only."

    return {
        "grade_support": grade_support,
        "summary": summary,
        "feature_summary": {
            "nuclei_count": nuclei_count,
            "avg_nuclei_area": avg_nuclei_area,
            "irregularity_score": irregularity_score,
            "nuclei_density": nuclei_density,
            "predicted_mitosis_count": predicted_mitosis_count,
            "mitotic_activity": mitotic_activity,
        }
    }