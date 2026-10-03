import React, { useState } from "react";
import { analyzeReport } from "../services/api";
import { SparkleIcon } from "./Icons.jsx";

/**
 * AI Request Analyzer. The person pastes the text of a prescription,
 * lab report, or referral note; this sends it to /ai/analyze-report
 * and shows what it found (blood type, units, hospital, urgency).
 * Nothing is submitted automatically -- "Use these details" just
 * fills in the normal request form below, so the person always
 * reviews it before anything is actually sent.
 */
export default function AIReportAnalyzer({ onUseResult }) {
  const [open, setOpen] = useState(false);
  const [reportText, setReportText] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  async function handleAnalyze() {
    if (!reportText.trim()) return;
    setLoading(true);
    setErrorMessage("");
    setResult(null);
    try {
      const response = await analyzeReport(reportText);
      setResult(response.data);
    } catch (error) {
      setErrorMessage("Could not analyze that text. Please try again or fill in the form manually.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card ai-card">
      <button type="button" className="ai-card-toggle" onClick={() => setOpen(!open)}>
        <SparkleIcon size={18} color="#B01E28" />
        <span>AI Request Analyzer — paste a prescription or report and let AI fill the form</span>
        <span className="ai-card-toggle-caret">{open ? "−" : "+"}</span>
      </button>

      {open && (
        <div className="ai-card-body">
          <p className="subtitle">Paste the text of the prescription, lab report, or referral note below.</p>
          <textarea
            className="ai-textarea"
            rows={4}
            placeholder="e.g. Patient requires 3 units of B+ blood urgently. Please arrange at City General Hospital."
            value={reportText}
            onChange={(e) => setReportText(e.target.value)}
          />
          <button type="button" className="inline-btn" onClick={handleAnalyze} disabled={loading || !reportText.trim()}>
            {loading ? "Analyzing…" : "Analyze with AI"}
          </button>

          {errorMessage && <p className="error-text">{errorMessage}</p>}

          {result && (
            <div className="ai-result">
              <div className="ai-result-grid">
                <div><span className="ai-result-label">Blood group</span>{result.blood_type || "—"}</div>
                <div><span className="ai-result-label">Units</span>{result.units ?? "—"}</div>
                <div><span className="ai-result-label">Hospital</span>{result.hospital_name || "—"}</div>
                <div><span className="ai-result-label">Urgency</span>{result.urgency_type || "—"}</div>
              </div>
              <p className="empty-state">{result.notes} (confidence: {Math.round(result.confidence * 100)}%)</p>
              <button type="button" className="inline-btn btn-outline" onClick={() => onUseResult(result)}>
                Use these details in the form below
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
