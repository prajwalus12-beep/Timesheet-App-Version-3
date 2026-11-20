import React, { useState, useMemo, useEffect, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import {
  BookOpen,
  Search,
  FileText,
  CheckCircle,
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  Shield,
  User,
  Clock,
  Folder,
  Settings,
  Upload,
  BarChart2,
  ChevronRight,
  Copy,
  Check,
  ExternalLink,
  Lock,
  ArrowRight,
  ArrowLeft,
  X,
  Sparkles,
  Layers,
  Calendar,
  Eye,
  RefreshCw
} from "lucide-react";
import { parseMarkdown } from "./markdownParser";
import "./styles.css";

// Fallback icon selector based on filename / topic
function getDocIcon(filename) {
  const f = filename.toLowerCase();
  if (f.includes("getting-started")) return BookOpen;
  if (f.includes("employee-management")) return User;
  if (f.includes("project-management") || f.includes("project-updates")) return Folder;
  if (f.includes("add-project")) return Layers;
  if (f.includes("timesheet")) return Clock;
  if (f.includes("leave")) return Calendar;
  if (f.includes("report")) return BarChart2;
  if (f.includes("import")) return Upload;
  if (f.includes("setting")) return Settings;
  if (f.includes("validation")) return AlertCircle;
  if (f.includes("troubleshoot") || f.includes("faq")) return HelpCircle;
  if (f.includes("security") || f.includes("profile")) return Lock;
  return FileText;
}

function HelpComponent(props) {
  const { args } = props;
  const userRole = args.user_role || "employee";
  const userName = args.user_name || "User";
  const allDocs = args.docs || { admin: [], employee: [] };

  // Current view role: Admins can toggle between 'admin' and 'employee' docs
  const [activeRole, setActiveRole] = useState(userRole === "admin" ? "admin" : "employee");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDocId, setSelectedDocId] = useState(args.initial_doc_id || "");
  const [copied, setCopied] = useState(false);
  const [errorSearchQuery, setErrorSearchQuery] = useState("");

  const contentRef = useRef(null);

  // Available docs for current activeRole
  const currentDocs = useMemo(() => {
    return allDocs[activeRole] || [];
  }, [allDocs, activeRole]);

  // Sync initial_doc_id when passed
  useEffect(() => {
    if (args.initial_doc_id) {
      setSelectedDocId(args.initial_doc_id);
    }
  }, [args.initial_doc_id]);

  // Default selection when role changes or initial load
  useEffect(() => {
    if (currentDocs.length > 0) {
      // Keep selection if exists in new list, else pick initial or first
      const exists = currentDocs.some((d) => d.id === selectedDocId);
      if (!exists) {
        if (args.initial_doc_id && currentDocs.some((d) => d.id === args.initial_doc_id)) {
          setSelectedDocId(args.initial_doc_id);
        } else {
          setSelectedDocId(currentDocs[0].id);
        }
      }
    }
  }, [currentDocs, activeRole, args.initial_doc_id]);

  // Adjust Streamlit frame height automatically
  useEffect(() => {
    const updateHeight = () => {
      const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
      Streamlit.setFrameHeight(Math.max(scrollHeight + 40, 850));
    };

    updateHeight();
    const timer = setTimeout(updateHeight, 250);
    window.addEventListener("resize", updateHeight);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", updateHeight);
    };
  }, [selectedDocId, searchQuery, activeRole]);

  // Filtered docs based on search
  const filteredDocs = useMemo(() => {
    if (!searchQuery.trim()) return currentDocs;
    const q = searchQuery.toLowerCase();
    return currentDocs.filter(
      (doc) =>
        (doc.title && doc.title.toLowerCase().includes(q)) ||
        (doc.category && doc.category.toLowerCase().includes(q)) ||
        (doc.content && doc.content.toLowerCase().includes(q))
    );
  }, [currentDocs, searchQuery]);

  // Current active doc
  const activeDoc = useMemo(() => {
    return currentDocs.find((d) => d.id === selectedDocId) || currentDocs[0] || null;
  }, [currentDocs, selectedDocId]);

  // Current doc index for Prev / Next navigation
  const currentIndex = useMemo(() => {
    return currentDocs.findIndex((d) => d.id === (activeDoc && activeDoc.id));
  }, [currentDocs, activeDoc]);

  const prevDoc = currentIndex > 0 ? currentDocs[currentIndex - 1] : null;
  const nextDoc = currentIndex < currentDocs.length - 1 ? currentDocs[currentIndex + 1] : null;

  // Handle in-document link clicks (e.g. [Link](./02-employee-management.md))
  const handleLinkClick = (url) => {
    // Extract target file name
    const cleanUrl = url.replace("./", "").replace("../", "").split("#")[0];
    const targetDoc = currentDocs.find((d) => d.filename.endsWith(cleanUrl) || cleanUrl.endsWith(d.filename));
    if (targetDoc) {
      setSelectedDocId(targetDoc.id);
      if (contentRef.current) {
        contentRef.current.scrollTop = 0;
      }
    }
  };

  const handleCopyDoc = () => {
    if (activeDoc && activeDoc.content) {
      navigator.clipboard.writeText(activeDoc.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="help-container">
      {/* --- TOP NAVBAR --- */}
      <header className="help-header">
        <div className="help-header-left">
          <div className="help-logo-badge">
            <BookOpen size={20} className="help-logo-icon" />
          </div>
          <div>
            <h1 className="help-title">Help & Documentation Center</h1>
            <p className="help-subtitle">
              Interactive user guides, module workflows, and validation reference
            </p>
          </div>
        </div>

        <div className="help-header-right">
          {/* Admin Role Switcher */}
          {userRole === "admin" ? (
            <div className="role-switch-container">
              <span className="role-switch-label">Documentation View:</span>
              <div className="role-switch-toggle">
                <button
                  type="button"
                  className={`role-toggle-btn ${activeRole === "admin" ? "active" : ""}`}
                  onClick={() => setActiveRole("admin")}
                >
                  <Shield size={14} />
                  <span>Admin Manual</span>
                </button>
                <button
                  type="button"
                  className={`role-toggle-btn ${activeRole === "employee" ? "active" : ""}`}
                  onClick={() => setActiveRole("employee")}
                >
                  <Eye size={14} />
                  <span>Employee Manual</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="employee-badge">
              <User size={15} />
              <span>Employee Portal</span>
            </div>
          )}
        </div>
      </header>

      {/* --- MAIN LAYOUT (SIDEBAR + CONTENT) --- */}
      <div className="help-main-body">
        {/* --- LEFT SIDEBAR --- */}
        <aside className="help-sidebar">
          {/* Search Box */}
          <div className="search-box-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder={`Search ${activeRole === "admin" ? "admin" : "employee"} guides...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={() => setSearchQuery("")}
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Document Navigation Tree */}
          <div className="doc-nav-list">
            <div className="doc-nav-section-header">
              <span>{activeRole === "admin" ? "ADMINISTRATION GUIDES" : "EMPLOYEE GUIDES"}</span>
              <span className="doc-count-badge">{filteredDocs.length}</span>
            </div>

            {filteredDocs.length === 0 ? (
              <div className="no-search-results">
                <AlertCircle size={24} className="no-results-icon" />
                <p>No matching guides found</p>
                <button
                  type="button"
                  className="clear-search-link"
                  onClick={() => setSearchQuery("")}
                >
                  Clear search query
                </button>
              </div>
            ) : (
              filteredDocs.map((doc, idx) => {
                const IconComponent = getDocIcon(doc.filename);
                const isSelected = activeDoc && activeDoc.id === doc.id;

                return (
                  <button
                    key={doc.id || idx}
                    type="button"
                    className={`doc-nav-item ${isSelected ? "selected" : ""}`}
                    onClick={() => {
                      setSelectedDocId(doc.id);
                      if (contentRef.current) {
                        contentRef.current.scrollTop = 0;
                      }
                    }}
                  >
                    <div className="doc-nav-icon-wrapper">
                      <IconComponent size={16} className="doc-icon" />
                    </div>
                    <div className="doc-nav-item-body">
                      <span className="doc-nav-title">{doc.title || doc.filename}</span>
                      <span className="doc-nav-meta">Guide #{idx + 1}</span>
                    </div>
                    <ChevronRight size={14} className="doc-nav-chevron" />
                  </button>
                );
              })
            )}
          </div>

          {/* Quick Helper Box */}
          <div className="quick-help-card">
            <div className="quick-help-title">
              <Sparkles size={14} className="sparkles-icon" />
              <span>Need Quick Answers?</span>
            </div>
            <p className="quick-help-desc">
              Check the <strong>Validations & Errors</strong> guide for direct fixes to any error message.
            </p>
            <button
              type="button"
              className="quick-help-btn"
              onClick={() => {
                const vDoc = currentDocs.find((d) => d.filename.includes("validation") || d.filename.includes("troubleshoot"));
                if (vDoc) {
                  setSelectedDocId(vDoc.id);
                }
              }}
            >
              Open Error Reference →
            </button>
          </div>
        </aside>

        {/* --- MAIN CONTENT AREA --- */}
        <main className="help-content-pane" ref={contentRef}>
          {activeDoc ? (
            <article className="doc-article">
              {/* Document Header */}
              <div className="article-header">
                <div className="article-breadcrumb">
                  <span>Help Center</span>
                  <ChevronRight size={12} />
                  <span>{activeRole === "admin" ? "Admin Manual" : "Employee Manual"}</span>
                  <ChevronRight size={12} />
                  <span className="breadcrumb-active">{activeDoc.title}</span>
                </div>

                <div className="article-actions">
                  <button
                    type="button"
                    className="action-btn"
                    onClick={handleCopyDoc}
                    title="Copy Guide Markdown"
                  >
                    {copied ? <Check size={14} color="#10B981" /> : <Copy size={14} />}
                    <span>{copied ? "Copied!" : "Copy"}</span>
                  </button>
                </div>
              </div>

              {/* Special interactive widget for Validations Guide */}
              {(activeDoc.filename.includes("validation") || activeDoc.filename.includes("troubleshoot")) && (
                <div className="validation-lookup-widget">
                  <div className="lookup-header">
                    <Search size={18} className="lookup-icon" />
                    <div>
                      <h4 className="lookup-title">Interactive Error Lookup</h4>
                      <p className="lookup-desc">
                        Type any error message you see on your screen to jump straight to its cause and solution:
                      </p>
                    </div>
                  </div>
                  <input
                    type="text"
                    className="lookup-input"
                    placeholder="e.g. Hours must be between 0.5 and 24, Account locked, 0 new entries..."
                    value={errorSearchQuery}
                    onChange={(e) => setErrorSearchQuery(e.target.value)}
                  />
                  {errorSearchQuery && (
                    <div className="lookup-tip">
                      Looking for <strong>"{errorSearchQuery}"</strong> — see highlighted table rows below.
                    </div>
                  )}
                </div>
              )}

              {/* Rendered Document Body */}
              <div className="article-body">
                {parseMarkdown(activeDoc.content, handleLinkClick)}
              </div>

              {/* Navigation Footer (Prev / Next) */}
              <div className="article-footer-nav">
                {prevDoc ? (
                  <button
                    type="button"
                    className="nav-step-btn prev"
                    onClick={() => {
                      setSelectedDocId(prevDoc.id);
                      if (contentRef.current) contentRef.current.scrollTop = 0;
                    }}
                  >
                    <ArrowLeft size={16} />
                    <div className="nav-step-text">
                      <span className="nav-step-direction">Previous Guide</span>
                      <span className="nav-step-title">{prevDoc.title}</span>
                    </div>
                  </button>
                ) : (
                  <div />
                )}

                {nextDoc ? (
                  <button
                    type="button"
                    className="nav-step-btn next"
                    onClick={() => {
                      setSelectedDocId(nextDoc.id);
                      if (contentRef.current) contentRef.current.scrollTop = 0;
                    }}
                  >
                    <div className="nav-step-text">
                      <span className="nav-step-direction">Next Guide</span>
                      <span className="nav-step-title">{nextDoc.title}</span>
                    </div>
                    <ArrowRight size={16} />
                  </button>
                ) : (
                  <div />
                )}
              </div>
            </article>
          ) : (
            <div className="doc-empty-state">
              <BookOpen size={48} className="empty-state-icon" />
              <h3>Select a guide from the sidebar</h3>
              <p>Explore detailed instructions, step-by-step walkthroughs, and troubleshooting tips.</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

export default withStreamlitConnection(HelpComponent);
