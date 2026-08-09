import React, { useState, useRef } from "react";
import logoMaharera from "./assets/logo_maharera.jpg";
import centerImg from "./assets/center.png";

const API_BASE = "http://127.0.0.1:8080/api";

export default function App() {
  const [stage, setStage] = useState("landing"); // landing | upload | results
  const [file, setFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [results, setResults] = useState([]); // [{ index, clause, status, confidence, reason, recommendation, citations, retrieved_context }]
  const [activeResultIndex, setActiveResultIndex] = useState(0);
  const [error, setError] = useState("");
  const fileInputRef = useRef(null);
  const [activeDetailTab, setActiveDetailTab] = useState("original"); // original | reasoning | sources | recommendation
  const clauseStripRef = useRef(null);
  const footerRef = useRef(null);

  const scrollToFooter = () => {
    if (footerRef.current) {
      footerRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  const scrollStripRight = () => {
    if (clauseStripRef.current) {
      clauseStripRef.current.scrollBy({ left: 240, behavior: "smooth" });
    }
  };

  // File drag & drop triggers
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile.type === "application/pdf") {
        uploadAndAnalyze(droppedFile);
      } else {
        setError("Only PDF files are supported.");
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadAndAnalyze(e.target.files[0]);
    }
  };

  // Upload file & run direct RAG compliance analysis
  const uploadAndAnalyze = async (selectedFile) => {
    setFile(selectedFile);
    setError("");
    setIsAnalyzing(true);
    setStage("upload"); // Remain on upload view while showing the main spinner

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(`${API_BASE}/analyze-pdf`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Failed to analyze agreement.");
      }

      const data = await response.json();
      if (!data.results || data.results.length === 0) {
        throw new Error("No clauses could be extracted or analyzed from this PDF.");
      }

      setResults(data.results);
      setActiveResultIndex(0);
      setStage("results");
    } catch (err) {
      console.error(err);
      setError(err.message || "An error occurred during file analysis.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Reset dashboard
  const resetApp = () => {
    setStage("landing");
    setFile(null);
    setResults([]);
    setError("");
  };

  const startNewScan = () => {
    setStage("upload");
    setFile(null);
    setResults([]);
    setError("");
  };

  // Helper for computing results statistics
  const getStats = () => {
    const compliant = results.filter((r) => r.status === "Compliant").length;
    const nonCompliant = results.filter((r) => r.status === "Non-Compliant").length;
    const review = results.filter((r) => r.status === "Needs Review").length;
    return { compliant, nonCompliant, review };
  };

  const stats = getStats();
  const currentResult = results[activeResultIndex];

  return (
    <div className={`app-container ${stage !== "results" ? "theme-bg" : ""}`}>
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-logo-container" onClick={resetApp}>
            <img src={logoMaharera} alt="MahaRERA Logo" className="header-logo-image" />
            <div className="header-brand-text">
              <div className="brand-title-line1">MAHARASHTRA REAL ESTATE</div>
              <div className="brand-title-line2">REGULATORY AUTHORITY</div>
              <div className="brand-subtitle">ISO 9001:2015 CERTIFIED</div>
            </div>
          </div>
          
          <nav className="header-nav">
            <span 
              className={`nav-link ${stage === "landing" ? "active" : ""}`} 
              onClick={resetApp}
            >
              Home
            </span>
            <span 
              className="nav-link" 
              onClick={scrollToFooter}
            >
              About
            </span>
            <span 
              className="nav-link" 
              onClick={scrollToFooter}
            >
              Contact
            </span>
          </nav>
        </div>
      </header>

      {/* Main Content Area */}
      {stage === "landing" ? (
        <div className="landing-hero animate-fade-in">
          <div className="hero-content">
            <div className="hero-graphics">
              <img src={centerImg} alt="MahaRERA Center Graphic" className="hero-center-img" />
            </div>
            <h1 className="hero-title">Ensuring Legal Transparency in Real Estate Transactions</h1>
            <p className="hero-subtitle">Simplifying Regulations for Developers and Buyers</p>
            <button className="btn-get-started" onClick={() => setStage("upload")}>
              Get Started
            </button>
          </div>
        </div>
      ) : (
        <main className="app-main">
          {/* Error Messages */}
          {error && (
            <div className="glass-card" style={{ borderColor: "#ef4444", padding: "1rem" }}>
              <span style={{ color: "#ef4444", fontWeight: 600 }}>⚠️ Error: </span>
              <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>{error}</span>
            </div>
          )}

        {/* STAGE 1: UPLOAD ZONE */}
        {stage === "upload" && !isAnalyzing && (
          <div className="upload-card">
            {/* File Icon Header */}
            <div className="upload-header-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="12" fill="#e0e7ff" />
                <path d="M7 16V8C7 6.89543 7.89543 6 9 6H13L17 10V16C17 17.1046 16.1046 18 15 18H9C7.89543 18 7 17.1046 7 16Z" fill="#5856d6" />
                <path d="M12 11V15M12 11L10 13M12 11L14 13" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>

            <h2 className="upload-title">Upload Builder Buyer Agreement PDF</h2>
            <p className="upload-subtitle">Drag and drop your PDF file here or click to browse</p>
            
            <div
              className="upload-dropzone"
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current.click()}
            >
              {/* Cloud Icon */}
              <div className="cloud-icon-container">
                <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M32 18C25.3726 18 20 23.3726 20 30C16.6863 30 14 32.6863 14 36C14 39.3137 16.6863 42 20 42H44C47.3137 42 50 39.3137 50 36C50 32.6863 47.3137 30 44 30C44 23.3726 38.6274 18 32 18Z" fill="#f5f7ff" stroke="#c7d2fe" strokeWidth="2" strokeLinejoin="round"/>
                  <path d="M32 27V39M32 27L28 31M32 27L36 31" stroke="#5856d6" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <circle cx="21" cy="22" r="1.5" fill="#a5b4fc" />
                  <circle cx="43" cy="40" r="1.5" fill="#a5b4fc" />
                  <path d="M44 24L46 26M46 24L44 26" stroke="#c7d2fe" strokeWidth="1.5" />
                  <path d="M18 36L20 38M20 36L18 38" stroke="#c7d2fe" strokeWidth="1.5" />
                </svg>
              </div>

              <div className="dropzone-text">Drag & drop your file here</div>
              
              <div className="dropzone-divider">
                <span className="divider-line"></span>
                <span className="divider-text">or</span>
                <span className="divider-line"></span>
              </div>

              <button className="btn-primary btn-choose-file" type="button">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '6px', verticalAlign: 'middle', display: 'inline-block'}}>
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                Choose File
              </button>

              <div className="dropzone-limits">Only PDF files are allowed • Max size 25MB</div>

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                accept="application/pdf"
                style={{ display: "none" }}
              />
            </div>
          </div>
        )}

        {/* STAGE 2: LOADING / AUDITING */}
        {isAnalyzing && (
          <div className="glass-card loading-wrapper" style={{ padding: '3.5rem 2rem', maxWidth: '800px', margin: '3.5rem auto' }}>
            <h2 className="loading-title" style={{ fontSize: '1.4rem', fontWeight: 700, color: '#0f172a', marginBottom: '0.75rem', lineHeight: '1.35' }}>
              We're reviewing your document and matching it against applicable MahaRERA regulations.
            </h2>
            <p className="loading-subtitle" style={{ fontSize: '0.95rem', color: '#64748b', marginBottom: '1.5rem' }}>
              Please wait while we analyze the agreement and generate your compliance report. This may take up to a minute.
            </p>
            <div className="progress-bar-container">
              <div className="progress-bar-fill"></div>
            </div>
          </div>
        )}

              {/* STAGE 3: SIDE-BY-SIDE RAG RESULTS */}
        {stage === "results" && currentResult && (
          <div className="glass-card animate-fade-in" style={{ padding: "2rem", border: "none", boxShadow: "0 10px 30px rgba(0, 0, 0, 0.04)" }}>
            
            {/* Results Header Bar */}
            <div className="results-header-bar" style={{ marginBottom: "2rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <h2 style={{ fontSize: "1.75rem", fontWeight: 700, color: "#0f172a", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  Audit Compliance Report
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent-primary)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ verticalAlign: 'middle' }}>
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                  </svg>
                </h2>
                <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem", marginTop: "0.25rem" }}>
                  Review clause-level compliance audit with MahaRERA regulatory references.
                </p>
              </div>
              <div className="results-stats-row" style={{ display: "flex", gap: "1.25rem", alignItems: "center" }}>
                {/* Stats Cards */}
                <div className="results-stats-card compliant" style={{ borderColor: 'rgba(5, 150, 105, 0.15)' }}>
                  <div className="results-stats-text">
                    <span className="results-stats-num" style={{ color: 'var(--color-compliant)' }}>{stats.compliant}</span>
                    <span className="results-stats-label" style={{ color: 'var(--color-compliant)' }}>Compliant</span>
                  </div>
                </div>

                <div className="results-stats-card non-compliant" style={{ borderColor: 'rgba(220, 38, 38, 0.15)' }}>
                  <div className="results-stats-text">
                    <span className="results-stats-num" style={{ color: 'var(--color-non-compliant)' }}>{stats.nonCompliant}</span>
                    <span className="results-stats-label" style={{ color: 'var(--color-non-compliant)' }}>Non-Compliant</span>
                  </div>
                </div>

                <div className="results-stats-card review" style={{ borderColor: 'rgba(217, 119, 6, 0.15)' }}>
                  <div className="results-stats-text">
                    <span className="results-stats-num" style={{ color: 'var(--color-review)' }}>{stats.review}</span>
                    <span className="results-stats-label" style={{ color: 'var(--color-review)' }}>Needs Review</span>
                  </div>
                </div>

                <button className="btn-primary" onClick={startNewScan} style={{ padding: "0.6rem 1.25rem", fontSize: "0.85rem", display: "inline-flex", alignItems: "center", gap: "0.5rem" }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
                  </svg>
                  New Scan
                </button>
              </div>
            </div>

            {/* Horizontal Scrollable Clause Strip */}
            <div className="clause-strip-container" style={{ position: 'relative', marginBottom: '2rem' }}>
              <div className="clause-strip" ref={clauseStripRef}>
                {results.map((res, idx) => {
                  const statusColor = res.status === "Compliant" ? "#22c55e" : res.status === "Non-Compliant" ? "#ef4444" : "#f59e0b";
                  return (
                    <div
                      key={idx}
                      className={`strip-tab-card ${activeResultIndex === idx ? "active" : ""}`}
                      onClick={() => setActiveResultIndex(idx)}
                    >
                      <div className="strip-tab-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                          <span className="strip-tab-index">Clause {res.index}</span>
                        </div>
                        <span className="strip-tab-dot" style={{ backgroundColor: statusColor }}></span>
                      </div>
                      <p className="strip-tab-preview">"{res.clause}"</p>
                    </div>
                  );
                })}
              </div>
              <button className="strip-arrow" onClick={scrollStripRight}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
              </button>
            </div>

            {/* Sub-Layout (Details Sidebar + Detail Pane) */}
            <div className="details-sub-layout">
              <div className="details-sidebar">
                <span className="details-sidebar-label">DETAILS</span>
                
                <button 
                  className={`detail-side-btn ${activeDetailTab === "original" ? "active" : ""}`}
                  onClick={() => setActiveDetailTab("original")}
                >
                  <svg className="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="16" y1="13" x2="8" y2="13"></line>
                    <line x1="16" y1="17" x2="8" y2="17"></line>
                  </svg>
                  <div className="btn-text-block">
                    <span className="btn-title">Original Clause Text</span>
                    <span className="btn-desc">View the extracted clause</span>
                  </div>
                </button>

                <button 
                  className={`detail-side-btn ${activeDetailTab === "reasoning" ? "active" : ""}`}
                  onClick={() => setActiveDetailTab("reasoning")}
                >
                  <svg className="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                  </svg>
                  <div className="btn-text-block">
                    <span className="btn-title">Compliance Reasoning</span>
                    <span className="btn-desc">AI analysis and reasoning</span>
                  </div>
                </button>

                <button 
                  className={`detail-side-btn ${activeDetailTab === "sources" ? "active" : ""}`}
                  onClick={() => setActiveDetailTab("sources")}
                >
                  <svg className="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>
                  </svg>
                  <div className="btn-text-block">
                    <span className="btn-title">Source Regulatory Context</span>
                    <span className="btn-desc">MahaRERA regulatory references</span>
                  </div>
                </button>

                <button 
                  className={`detail-side-btn ${activeDetailTab === "recommendation" ? "active" : ""}`}
                  onClick={() => setActiveDetailTab("recommendation")}
                >
                  <svg className="btn-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"></path>
                    <line x1="9" y1="18" x2="15" y2="18"></line>
                  </svg>
                  <div className="btn-text-block">
                    <span className="btn-title">Recommendations</span>
                    <span className="btn-desc">Actionable suggestions</span>
                  </div>
                </button>
              </div>

              <div className="details-pane">
                {/* PANEL 1: ORIGINAL CLAUSE */}
                {activeDetailTab === "original" && (
                  <div className="pane-content-wrapper animate-fade-in">
                    <div className="pane-header-block">
                      <h3 className="pane-title">Original Clause Text</h3>
                      <p className="pane-subtitle">This is the exact clause extracted from your Builder Buyer Agreement.</p>
                    </div>
                    
                    <div className="pane-quote-box">
                      <span className="quote-mark">“</span>
                      <p className="quote-text">{currentResult.clause}</p>
                    </div>

                    <div className="pane-meta-footer">
                      <div className="pane-status-block">
                        <span className="meta-label">Audit Status</span>
                        <span className={`status-badge-tint ${currentResult.status.toLowerCase().replace(" ", "-")}`}>
                          {currentResult.status}
                        </span>
                      </div>
                      <div className="pane-confidence-block">
                        <span className="meta-label">Confidence Score</span>
                        <div className="confidence-meter-row">
                          <div className="confidence-meter-bar">
                            <div className="confidence-meter-fill" style={{ width: `${currentResult.confidence}%` }}></div>
                          </div>
                          <span className="confidence-text">{currentResult.confidence}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* PANEL 2: COMPLIANCE REASONING */}
                {activeDetailTab === "reasoning" && (
                  <div className="pane-content-wrapper animate-fade-in">
                    <div className="pane-header-block">
                      <h3 className="pane-title">Compliance Reasoning</h3>
                      <p className="pane-subtitle">Detailed AI analysis matching this clause against official MahaRERA provisions.</p>
                    </div>

                    <div className="pane-paragraph-box">
                      <p className="reasoning-paragraph">{currentResult.reason}</p>
                    </div>

                    <div className="pane-meta-footer">
                      <div className="pane-status-block">
                        <span className="meta-label">Audit Status</span>
                        <span className={`status-badge-tint ${currentResult.status.toLowerCase().replace(" ", "-")}`}>
                          {currentResult.status}
                        </span>
                      </div>
                      <div className="pane-confidence-block">
                        <span className="meta-label">Confidence Score</span>
                        <div className="confidence-meter-row">
                          <div className="confidence-meter-bar">
                            <div className="confidence-meter-fill" style={{ width: `${currentResult.confidence}%` }}></div>
                          </div>
                          <span className="confidence-text">{currentResult.confidence}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* PANEL 3: SOURCE REGULATORY CONTEXT */}
                {activeDetailTab === "sources" && (
                  <div className="pane-content-wrapper animate-fade-in">
                    <div className="pane-header-block">
                      <h3 className="pane-title">Source Regulatory Context</h3>
                      <p className="pane-subtitle">Retrieved regulatory sections and rules referenced for this audit.</p>
                    </div>

                    <div className="sources-reading-document">
                      {currentResult.retrieved_context && currentResult.retrieved_context.length > 0 ? (
                        currentResult.retrieved_context.map((doc, idx) => {
                          const docTitle = doc.document.replace(/_/g, " ");
                          return (
                            <React.Fragment key={idx}>
                              <div className="source-document-section">
                                <div className="source-section-header">
                                  <h4 className="source-section-title">{docTitle} — Page {doc.page}</h4>
                                </div>
                                <div className="source-section-content">
                                  {doc.content}
                                </div>
                              </div>
                              {idx < currentResult.retrieved_context.length - 1 && (
                                <hr className="citation-page-line" />
                              )}
                            </React.Fragment>
                          );
                        })
                      ) : (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", marginTop: "2rem" }}>
                          No regulatory sections were retrieved for this clause.
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {/* PANEL 4: RECOMMENDATIONS */}
                {activeDetailTab === "recommendation" && (
                  <div className="pane-content-wrapper animate-fade-in">
                    <div className="pane-header-block">
                      <h3 className="pane-title">Actionable Recommendations</h3>
                      <p className="pane-subtitle">Steps recommended to bring this clause into compliance with MahaRERA guidelines.</p>
                    </div>

                    <div className="pane-paragraph-box">
                      <p className="recommendations-paragraph">
                        {currentResult.recommendation || "No action required. The clause is fully compliant with MahaRERA regulations."}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

          </div>
        )}

      </main>
      )}

      {/* Footer */}
      <footer className="app-footer" ref={footerRef}>
        <div className="footer-content">
          
          {/* Column 1: Brand details & Logo */}
          <div className="footer-col brand-col">
            <div className="footer-logo-row">
              <img src={logoMaharera} alt="MahaRERA Logo" className="footer-logo-img" />
              <div className="footer-brand-text">
                <span className="footer-brand-title">MAHARERA</span>
                <span className="footer-brand-subtitle">COMPLIANCE AUDITOR</span>
              </div>
            </div>
            <p className="footer-brand-desc">
              Ensuring transparency and legal compliance in builder buyer agreements under MahaRERA regulations.
            </p>
          </div>

          {/* Column 2: Navigation Links */}
          <div className="footer-col links-col">
            <h4 className="footer-col-title">Quick Links</h4>
            <ul className="footer-links-list">
              <li><span className="footer-nav-link" onClick={resetApp}>Home Page</span></li>
              <li><span className="footer-nav-link" onClick={scrollToFooter}>About Auditor</span></li>
              <li><span className="footer-nav-link" onClick={scrollToFooter}>Contact Support</span></li>
            </ul>
          </div>

          {/* Column 3: Contact & Credits */}
          <div className="footer-col contact-col">
            <h4 className="footer-col-title">Auditor Credits</h4>
            <p className="footer-credit-text">
              <span className="footer-pulse-dot"></span>
              Made by Soham Dalal
            </p>
            <p className="footer-email-text">
              Email: <a href="mailto:sohamdalal9481@gmail.com" className="footer-link">sohamdalal9481@gmail.com</a>
            </p>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="footer-bottom-bar">
          <p className="footer-copyright">&copy; {new Date().getFullYear()} MahaRERA Compliance Auditor. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
