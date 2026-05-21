import React, { useState, useMemo, useEffect, useCallback, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { ExternalLink, Search, Filter, Download, X, Info, Save, Link, ChevronDown, ChevronUp, Send, Mail } from "lucide-react";
import "./styles.css";

function ProjectUpdateComponent(props) {
  const { args } = props;

  // Data from Python
  const serverProjects = args.projects || [];
  const leadEngineers = args.lead_engineers || [];
  const statusOptions = args.status_options || ["In progress", "Complete", "On hold", "Cancelled"];
  const readOnly = args.read_only || false;
  const isCompact = args.is_compact || false; // New prop for compact/report mode
  const employees = args.employees || [];

  // Local working copy of projects
  const [projects, setProjects] = useState(() => {
    // Sort initially based on the numeric value of project_code descending
    return [...serverProjects].sort((a, b) => {
      const codeA = parseInt((a.project_code || "0").replace(/\D/g, ""), 10) || 0;
      const codeB = parseInt((b.project_code || "0").replace(/\D/g, ""), 10) || 0;
      return codeB - codeA;
    });
  });

  // Sync when Python sends new data (e.g., after a save)
  const prevServerRef = useRef(null);
  useEffect(() => {
    const newKey = JSON.stringify(serverProjects);
    if (prevServerRef.current !== newKey) {
      prevServerRef.current = newKey;
      const sorted = [...serverProjects].sort((a, b) => {
        const codeA = parseInt((a.project_code || "0").replace(/\D/g, ""), 10) || 0;
        const codeB = parseInt((b.project_code || "0").replace(/\D/g, ""), 10) || 0;
        return codeB - codeA;
      });
      setProjects(sorted);
    }
  }, [serverProjects]);

  // Filter States
  const isAdmin = String(args.user_role || "").toLowerCase() === "admin";
  const [filterName, setFilterName] = useState("");
  const [filterCodeMin, setFilterCodeMin] = useState("");
  const [filterCodeMax, setFilterCodeMax] = useState("");
  const [filterLead, setFilterLead] = useState(isAdmin ? "" : (args.current_user || ""));
  const [filterPriorityMin, setFilterPriorityMin] = useState("");
  const [filterPriorityMax, setFilterPriorityMax] = useState("");
  const [filterStatus, setFilterStatus] = useState(isAdmin ? [] : ["In progress", "In testing", "To be deployed"]);
  const [filterUpdatedOnly, setFilterUpdatedOnly] = useState(false);
  const [filterShowCompleted, setFilterShowCompleted] = useState(false);
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);



  // Sort States
  const [sortField, setSortField] = useState('project_code');
  const [sortOrder, setSortOrder] = useState('desc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder(field === 'project_name' ? 'asc' : 'desc');
    }
  };

  // Adjust iframe height after each render
  useEffect(() => { Streamlit.setFrameHeight(); });

  // ---- Filtering ----
  const updatedFlagKeys = [
    "project_name_updated", "lead_engineer_updated", "priority_updated",
    "status_updated", "trello_link_updated", "start_date_updated",
    "end_date_updated", "prototype_link_updated", "slack_link_updated",
    "estimated_days_updated", "checkbox_bc_updated", "checkbox_trello_updated",
    "checkbox_wa_updated", "checkbox_ws_updated"
  ];

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      if (filterName) {
        const nameMatch = (p.project_name || "").toLowerCase().includes(filterName.toLowerCase());
        const codeMatch = (p.project_code || "").toLowerCase().includes(filterName.toLowerCase());
        if (!nameMatch && !codeMatch) return false;
      }
      const code = parseInt(p.project_code, 10);
      if (filterCodeMin && code < parseInt(filterCodeMin, 10)) return false;
      if (filterCodeMax && code > parseInt(filterCodeMax, 10)) return false;
      if (filterLead && p.lead_engineer !== filterLead) return false;
      if (filterPriorityMin || filterPriorityMax) {
        const pVal = parseFloat(p.priority);
        if (!isNaN(pVal)) {
          if (filterPriorityMin && pVal < parseFloat(filterPriorityMin)) return false;
          if (filterPriorityMax && pVal > parseFloat(filterPriorityMax)) return false;
        } else if (filterPriorityMin || filterPriorityMax) {
          // If it's not a number but we have range filters, it's a mismatch
          return false;
        }
      }
      if (filterStatus.length > 0 && !filterStatus.includes(p.status)) return false;

      const isComplete = p.status === "Complete";
      const hasUpdate = updatedFlagKeys.some(
        (k) => p[k] === true || p[k] === "true" || p[k] === "True"
      );

      // Status filters handle "Complete" visibility logic
      if (filterShowCompleted) {
        // If "Show Completed Only" is active, hide everything else
        if (!isComplete) return false;
      } else {
        // By default, hide completed records UNLESS they have been highlighted/updated
        if (isComplete && !hasUpdate) return false;
      }

      if (filterUpdatedOnly && !hasUpdate) return false;

      return true;
    });
  }, [projects, filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterStatus, filterUpdatedOnly, filterShowCompleted]);

  const sortedProjects = useMemo(() => {
    return [...filteredProjects].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];
      
      if (sortField === 'project_code') {
        valA = parseInt((valA || "0").replace(/\D/g, ""), 10) || 0;
        valB = parseInt((valB || "0").replace(/\D/g, ""), 10) || 0;
      } else if (sortField === 'start_date' || sortField === 'end_date') {
        valA = valA ? new Date(valA).getTime() : 0;
        valB = valB ? new Date(valB).getTime() : 0;
      } else {
        valA = (valA || "").toString().toLowerCase();
        valB = (valB || "").toString().toLowerCase();
      }

      if (valA < valB) return sortOrder === 'asc' ? -1 : 1;
      if (valA > valB) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredProjects, sortField, sortOrder]);

  const resetFilters = () => {
    setFilterName(""); setFilterCodeMin(""); setFilterCodeMax("");
    setFilterLead("");
    setFilterPriorityMin("");
    setFilterPriorityMax("");
    setFilterStatus([]);
    setFilterUpdatedOnly(false);
    setFilterShowCompleted(false);
  };

  // ---- Infinite Scroll ----
  const [displayCount, setDisplayCount] = useState(30);

  // Reset display count when filters or data change
  useEffect(() => {
    setDisplayCount(30);
  }, [filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterStatus, filterUpdatedOnly, filterShowCompleted, projects, sortField, sortOrder]);

  const handleScroll = (e) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    // If scrolled within 50px of the bottom, load more
    if (scrollHeight - scrollTop <= clientHeight + 50) {
      if (displayCount < filteredProjects.length) {
        setDisplayCount(prev => prev + 30);
      }
    }
  };

  // ---- Editing ----
  const handleUpdate = (projectCode, field, value) => {
    setProjects((prev) =>
      prev.map((p) => (p.project_code === projectCode ? { ...p, [field]: value } : p))
    );
  };

  // Check if a field has been edited locally (differs from server data)
  const isDirty = (projectCode, field) => {
    const server = serverProjects.find((p) => p.project_code === projectCode);
    const local = projects.find((p) => p.project_code === projectCode);
    if (!server || !local) return false;
    return String(server[field] ?? "") !== String(local[field] ?? "");
  };

  // Check if a field has the DB _updated flag
  const isDbUpdated = (project, field) => {
    const flag = project[field + "_updated"];
    if (flag === true || flag === "true" || flag === "True") return true;
    return false;
  };

  // Count of locally edited projects
  const editedCount = useMemo(() => {
    return projects.filter((p) => {
      const server = serverProjects.find((sp) => sp.project_code === p.project_code);
      return server && JSON.stringify(server) !== JSON.stringify(p);
    }).length;
  }, [projects, serverProjects]);



  // ---- Save ----
  const handleSave = useCallback(() => {
    const edits = {};
    const vErrors = [];

    projects.forEach((p, idx) => {
      const server = serverProjects.find((sp) => sp.project_code === p.project_code);
      if (!server) return;
      const changes = {};
      const editableFields = [
        "project_name", "lead_engineer", "priority", "start_date", "end_date",
        "status", "trello_link", "prototype_link", "slack_link",
        "checkbox_bc", "checkbox_trello", "checkbox_wa", "checkbox_ws", "estimated_days"
      ];
      editableFields.forEach((f) => {
        if (String(server[f] ?? "") !== String(p[f] ?? "")) {
          changes[f] = p[f];
        }
      });
      if (Object.keys(changes).length > 0) {
        const errs = [];
        const isUnchecked = (val) => (val === 1 || val === "1" || val === 1.0 || val === "1.0");

        if (!p.start_date) errs.push("Missing start date");
        if (!p.end_date) errs.push("Missing End Date");
        if (p.start_date && p.end_date && new Date(p.start_date) > new Date(p.end_date)) {
          errs.push("Start Date to be <= End Date");
        }
        const validatePastDateStatuses = ["Not started", "Ongoing", "In testing", "Awaiting Info", "At Beta", "In progress"];
        if (validatePastDateStatuses.includes(p.status) && p.end_date) {
          const today = new Date();
          today.setHours(0,0,0,0);
          if (new Date(p.end_date) < today) {
            errs.push("Past date is not allowed.");
          }
        }
        if (!p.trello_link) errs.push("Missing Trello link");
        if (!p.estimated_days) errs.push("Missing estimates");
        if (parseFloat(p.actual_days || 0) > 1 && p.status === "Not started") {
          errs.push("Actual says more than one but the status is not started");
        }
        if (isUnchecked(p.checkbox_bc)) errs.push("Please check the BRD check box is not checked");
        if (isUnchecked(p.checkbox_trello)) errs.push("Please check the Trello checkbox is not checked");
        if (isUnchecked(p.checkbox_wa)) errs.push("Please check the WA check box is not checked");
        if (isUnchecked(p.checkbox_ws)) errs.push("Please check that the WS checkbox is not checked");

        if (errs.length > 0) {
          vErrors.push({ projectCode: p.project_code, name: p.project_name, errors: errs });
        }

        edits[p.project_code] = changes;
      }
    });

    if (vErrors.length > 0) {
      setValidationErrors(vErrors);
      // Automatically scroll to the top so the user sees the errors
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    setValidationErrors([]);

    if (Object.keys(edits).length > 0) {
      Streamlit.setComponentValue({ action: "save", edits: edits });
    }
  }, [projects, serverProjects]);

  // ---- Export ----
  const handleExportClick = () => {
    Streamlit.setComponentValue({ action: "open_export_modal" });
  };

  const handleOpenReminderModal = () => {
    const displayedProjectCodes = filteredProjects.map(p => String(p.project_code));
    Streamlit.setComponentValue({
      action: "open_reminder_modal",
      payload: {
        displayedProjectCodes: displayedProjectCodes
      }
    });
  };

  // ---- Cell class helpers ----
  const isFieldEmpty = (value) => {
    return !value || value.toString().trim() === "";
  };

  const cellInputClass = (projectCode, field, value, extra = "") => {
    let cls = "pu-cell-input";
    if (extra) cls += " " + extra;
    if (isDirty(projectCode, field)) cls += " dirty";
    const proj = projects.find(p => p.project_code === projectCode);
    if (proj && !isDirty(projectCode, field) && isDbUpdated(proj, field)) cls += " db-updated";
    if (isFieldEmpty(value)) cls += " pu-highlight-empty";
    return cls;
  };

  const cellSelectClass = (projectCode, field, value, extra = "") => {
    let cls = "pu-cell-select";
    if (extra) cls += " " + extra;
    if (isDirty(projectCode, field)) cls += " dirty";
    const proj = projects.find(p => p.project_code === projectCode);
    if (proj && !isDirty(projectCode, field) && isDbUpdated(proj, field)) cls += " db-updated";
    if (isFieldEmpty(value)) cls += " pu-highlight-empty";
    return cls;
  };

  const statusClass = (status) => {
    if (status === "Complete") return "status-complete";
    if (status === "In progress") return "status-progress";
    if (status === "In testing") return "status-testing";
    if (status === "Not started") return "status-not-started";
    if (status === "Awaiting Info") return "status-awaiting";
    if (status === "At Beta") return "status-beta";
    if (status === "To be deployed") return "status-deploy";
    if (status === "Duplicate - Closed") return "status-duplicate";
    if (status === "Ongoing") return "status-ongoing";
    return "";
  };

  // ---- MultiSelect Sub-component ----
  const MultiSelect = ({ options, selected, onChange, placeholder }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [tempSelected, setTempSelected] = useState(selected);
    const containerRef = useRef(null);

    // Sync temp state when external selected changes (e.g. on Reset)
    useEffect(() => {
      setTempSelected(selected);
    }, [selected]);

    useEffect(() => {
      const handleClickOutside = (event) => {
        if (containerRef.current && !containerRef.current.contains(event.target)) {
          setIsOpen(false);
          setTempSelected(selected); // Reset temp state on close without apply
        }
      };
      document.addEventListener("mousedown", handleClickOutside);
      return () => document.removeEventListener("mousedown", handleClickOutside);
    }, [selected]);

    const toggleOption = (option) => {
      setTempSelected(prev => 
        prev.includes(option)
          ? prev.filter(item => item !== option)
          : [...prev, option]
      );
    };

    const handleApply = () => {
      onChange(tempSelected);
      setIsOpen(false);
    };

    const displayValue = () => {
      if (selected.length === 0) return <span className="pu-multiselect-placeholder">{placeholder}</span>;
      if (selected.length <= 2) return selected.join(", ");
      return selected.slice(0, 2).join(", ") + "...";
    };

    return (
      <div className="pu-multiselect" ref={containerRef}>
        <button 
          className={`pu-multiselect-trigger ${isOpen ? "active" : ""}`} 
          onClick={() => setIsOpen(!isOpen)}
        >
          <div className="pu-multiselect-value">
            {displayValue()}
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {selected.length > 1 && <span className="pu-multiselect-badge">{selected.length}</span>}
            <ExternalLink size={14} className="pu-multiselect-arrow" style={{ transform: isOpen ? "rotate(180deg)" : "none" }} />
          </div>
        </button>
        {isOpen && (
          <div className="pu-multiselect-menu">
            <div className="pu-multiselect-list">
              {options.map(option => (
                <div 
                  key={option} 
                  className={`pu-multiselect-item ${tempSelected.includes(option) ? "selected" : ""}`}
                  onClick={() => toggleOption(option)}
                >
                  <div className="pu-multiselect-checkbox">
                    {tempSelected.includes(option) && <X size={10} className="pu-multiselect-check-icon" />}
                  </div>
                  <span>{option}</span>
                </div>
              ))}
            </div>
            <div className="pu-multiselect-footer">
              <button className="pu-multiselect-apply" onClick={handleApply}>Apply</button>
            </div>
          </div>
        )}
      </div>
    );
  };

  // ---- Render ----
  return (
    <div className="pu-page">
      <div className="pu-container">

        {/* Header */}
        <div className="pu-header">
          <h1 className="pu-title">Project Attributes</h1>
          <div className="pu-header-actions">
            <span className="pu-count-label">
              Showing {filteredProjects.length} incomplete project status records of {projects.length} projects.
            </span>
            {!readOnly && !isCompact && editedCount > 0 && (
              <button className="pu-save-btn" onClick={handleSave}>
                <Save size={16} /> Save Changes ({editedCount})
              </button>
            )}
            <button className="pu-export-btn" onClick={handleExportClick}>
              <Download size={16} /> Export
            </button>
            {!readOnly && !isCompact && isAdmin && (
              <button 
                className="pu-export-btn" 
                onClick={handleOpenReminderModal}
              >
                <Send size={16} /> Send Reminder
              </button>
            )}
          </div>
        </div>

        {/* Validation Errors Banner */}
        {validationErrors.length > 0 && (
          <div className="pu-validation-banner" style={{ backgroundColor: "#fee2e2", border: "1px solid #ef4444", borderRadius: "6px", padding: "12px", marginBottom: "1rem", color: "#b91c1c" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
              <strong style={{ display: "flex", alignItems: "center", gap: "6px" }}><Info size={16} /> Validation Errors</strong>
              <button onClick={() => setValidationErrors([])} style={{ background: "none", border: "none", cursor: "pointer", color: "#b91c1c" }}><X size={16}/></button>
            </div>
            <ul style={{ margin: 0, paddingLeft: "1.5rem", fontSize: "0.85rem", display: "flex", flexDirection: "column", gap: "6px" }}>
              {validationErrors.map(ve => (
                <li key={ve.projectCode} style={{ lineHeight: "1.4" }}>
                  <strong>{ve.projectCode} {ve.name ? `(${ve.name})` : ""}:</strong> {ve.errors.join(" • ")}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Unsaved Changes Banner */}
        {!readOnly && !isCompact && editedCount > 0 && (
          <div className="pu-unsaved-banner">
            <span>⚠ You have {editedCount} unsaved change(s).</span>
            <button className="pu-save-btn" onClick={handleSave} style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}>
              <Save size={14} /> Save
            </button>
          </div>
        )}

        {/* Filters */}
        <div className="pu-filters">
          <div 
            className="pu-filters-header" 
            style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", marginBottom: isFiltersOpen ? "1rem" : "0" }}
            onClick={() => setIsFiltersOpen(!isFiltersOpen)}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Filter size={18} />
              <span>Filters</span>
            </div>
            <div>
              {isFiltersOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
            </div>
          </div>
          {isFiltersOpen && (
            <div className="pu-filters-grid">

              {/* Project Name */}
              <div className="pu-filter-group">
                <label className="pu-filter-label">Project Name</label>
                <div className="pu-filter-input-wrap">
                  <input
                    type="text"
                    placeholder="Search Project Name..."
                    value={filterName}
                    onChange={(e) => setFilterName(e.target.value)}
                    className="pu-filter-input has-icon"
                  />
                  <Search size={14} className="pu-filter-search-icon" />
                </div>
              </div>

              {/* Code Range */}
              <div className="pu-filter-group">
                <label className="pu-filter-label">Project Code Range</label>
                <div className="pu-filter-range">
                  <input type="number" placeholder="Min" value={filterCodeMin}
                    onChange={(e) => setFilterCodeMin(e.target.value)} className="pu-filter-input" />
                  <span className="pu-range-sep">–</span>
                  <input type="number" placeholder="Max" value={filterCodeMax}
                    onChange={(e) => setFilterCodeMax(e.target.value)} className="pu-filter-input" />
                </div>
              </div>

              {/* Lead Engineer */}
              <div className="pu-filter-group">
                <label className="pu-filter-label">Lead Engineer</label>
                <select value={filterLead} onChange={(e) => setFilterLead(e.target.value)} className="pu-filter-select">
                  <option value="">All Engineers</option>
                  {leadEngineers.map((eng) => <option key={eng} value={eng}>{eng}</option>)}
                </select>
              </div>

              {/* Priority Range */}
              <div className="pu-filter-group">
                <label className="pu-filter-label">Priority (Min - Max)</label>
                <div className="pu-filter-range">
                  <input type="number" placeholder="Min" value={filterPriorityMin} onChange={(e) => setFilterPriorityMin(e.target.value)} className="pu-filter-input" />
                  <span className="pu-range-sep">-</span>
                  <input type="number" placeholder="Max" value={filterPriorityMax} onChange={(e) => setFilterPriorityMax(e.target.value)} className="pu-filter-input" />
                </div>
              </div>


              {/* Status + Clear */}
              <div className="pu-filter-group">
                <label className="pu-filter-label">Status</label>
                <div className="pu-status-row">
                  <MultiSelect 
                    options={statusOptions}
                    selected={filterStatus}
                    onChange={setFilterStatus}
                    placeholder="All Statuses"
                  />
                  <button className="pu-clear-btn" onClick={resetFilters} title="Clear all filters">Clear</button>
                </div>
              </div>

              {/* Quick Filters - Hide in compact mode */}
              {!isCompact && (
                <div className="pu-filter-group pu-filter-group--full">
                  <label className="pu-filter-label">Quick Filters</label>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      className={`pu-updated-toggle${filterUpdatedOnly ? " active" : ""}`}
                      onClick={() => setFilterUpdatedOnly((v) => !v)}
                      title="Show only rows with highlighted (updated) fields"
                    >
                      <span className="pu-updated-dot" />
                      Updated Records Only
                    </button>
                    <button
                      className={`pu-updated-toggle${filterShowCompleted ? " active" : ""}`}
                      onClick={() => setFilterShowCompleted((v) => !v)}
                      style={{ borderColor: filterShowCompleted ? "#10b981" : "", color: filterShowCompleted ? "#10b981" : "" }}
                      title="Show only completed projects"
                    >
                      <span className="pu-updated-dot" style={{ backgroundColor: filterShowCompleted ? "#10b981" : "" }} />
                      Completed Records
                    </button>
                  </div>
                </div>
              )}

            </div>
          )}
        </div>

        {/* Sort Controls */}
        <div className="pu-sort-controls" style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px", marginBottom: "12px", padding: "10px 15px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginRight: "5px", letterSpacing: "0.05em" }}>Sort By:</span>
          

          <button 
            onClick={() => handleSort('project_code')}
            style={{ 
              padding: "6px 14px", borderRadius: "6px", fontSize: "0.75rem", fontWeight: "700", 
              border: sortField === 'project_code' ? "1px solid #3b82f6" : "1px solid #cbd5e1", 
              background: sortField === 'project_code' ? "#eff6ff" : "#ffffff",
              color: sortField === 'project_code' ? "#1d4ed8" : "#475569",
              cursor: "pointer", display: "flex", alignItems: "center", gap: "6px",
              boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)", textTransform: "uppercase"
            }}
          >
            PROJECT CODE {sortField === 'project_code' && (sortOrder === 'asc' ? '▲' : '▼')}
          </button>

          <button 
            onClick={() => handleSort('project_name')}
            style={{ 
              padding: "6px 14px", borderRadius: "6px", fontSize: "0.75rem", fontWeight: "700", 
              border: sortField === 'project_name' ? "1px solid #3b82f6" : "1px solid #cbd5e1", 
              background: sortField === 'project_name' ? "#eff6ff" : "#ffffff",
              color: sortField === 'project_name' ? "#1d4ed8" : "#475569",
              cursor: "pointer", display: "flex", alignItems: "center", gap: "6px",
              boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)", textTransform: "uppercase"
            }}
          >
            PROJECT NAME {sortField === 'project_name' && (sortOrder === 'asc' ? '▲' : '▼')}
          </button>

          {!isCompact && (
            <>
              <button 
                onClick={() => handleSort('start_date')}
                style={{ 
                  padding: "6px 14px", borderRadius: "6px", fontSize: "0.75rem", fontWeight: "700", 
                  border: sortField === 'start_date' ? "1px solid #3b82f6" : "1px solid #cbd5e1", 
                  background: sortField === 'start_date' ? "#eff6ff" : "#ffffff",
                  color: sortField === 'start_date' ? "#1d4ed8" : "#475569",
                  cursor: "pointer", display: "flex", alignItems: "center", gap: "6px",
                  boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)", textTransform: "uppercase"
                }}
              >
                START DATE {sortField === 'start_date' && (sortOrder === 'asc' ? '▲' : '▼')}
              </button>

              <button 
                onClick={() => handleSort('end_date')}
                style={{ 
                  padding: "6px 14px", borderRadius: "6px", fontSize: "0.75rem", fontWeight: "700", 
                  border: sortField === 'end_date' ? "1px solid #3b82f6" : "1px solid #cbd5e1", 
                  background: sortField === 'end_date' ? "#eff6ff" : "#ffffff",
                  color: sortField === 'end_date' ? "#1d4ed8" : "#475569",
                  cursor: "pointer", display: "flex", alignItems: "center", gap: "6px",
                  boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)", textTransform: "uppercase"
                }}
              >
                END DATE {sortField === 'end_date' && (sortOrder === 'asc' ? '▲' : '▼')}
              </button>
            </>
          )}
        </div>

        {/* Data Table — Two-line row layout matching screenshot */}
        <div className="pu-table-wrapper">
          <div className="pu-table-scroll" onScroll={handleScroll}>
            <table className="pu-table">
              <thead>
                <tr>
                  <th className="th-hash">#</th>
                  <th className="th-code">CODE</th>
                  <th className="th-project">
                    PROJECT NAME / TRELLO URL
                    {!isCompact && (
                      <> /<br />PROTOTYPE URL / SLACK URL</>
                    )}
                  </th>
                  <th className="th-lead">
                    LEAD ENGINEER
                    {!isCompact && (
                      <> /<br />START DATE / END DATE</>
                    )}
                  </th>
                  <th className="th-status">
                    STATUS / PRIORITY
                  </th>
                  {!isCompact && (
                    <>
                      <th className="th-process">
                        <span className="process-header">PROJECT PROCESS</span>
                      </th>
                      <th className="th-estimate">
                        <span className="process-header">TIME ANALYSIS<br/>DAYS</span>
                      </th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {sortedProjects.length > 0 ? (
                  sortedProjects.slice(0, displayCount).map((project, index) => (

                    <React.Fragment key={project.project_code}>
                      {/* Primary row */}
                      <tr className="pu-row-primary">
                        <td className="td-hash">{index + 1}</td>
                        <td className="td-code">
                          <b>{project.project_code || ""}</b>
                        </td>

                        {/* Project Name Column Group */}
                        <td className="td-project-name">
                          <input type="text"
                            value={project.project_name || ""}
                            onChange={(e) => handleUpdate(project.project_code, "project_name", e.target.value)}
                            className={cellInputClass(project.project_code, "project_name", project.project_name, "name-field")}
                            disabled={readOnly || isCompact}
                            title={project.project_name || "Project Name is required"}
                          />
                          <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                            <div className="pu-url-input-wrapper">
                              <input type="text" value={project.trello_link || ""}
                                onChange={(e) => handleUpdate(project.project_code, "trello_link", e.target.value)}
                                className={cellInputClass(project.project_code, "trello_link", project.trello_link, "url-field-small")}
                                disabled={readOnly || isCompact}
                                placeholder="Trello URL" />
                              {project.trello_link && project.trello_link.startsWith("http") && (
                                <a href={project.trello_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Trello">
                                  <Link size={12} />
                                </a>
                              )}
                            </div>
                            {!isCompact && (
                              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.15rem" }}>
                                <div className="pu-url-input-wrapper">
                                  <input type="text" value={project.prototype_link || ""}
                                    onChange={(e) => handleUpdate(project.project_code, "prototype_link", e.target.value)}
                                    className={cellInputClass(project.project_code, "prototype_link", project.prototype_link, "url-field-small")}
                                    disabled={readOnly}
                                    placeholder="Prototype URL" />
                                  {project.prototype_link && project.prototype_link.startsWith("http") && (
                                    <a href={project.prototype_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Prototype">
                                      <Link size={12} />
                                    </a>
                                  )}
                                </div>
                                <div className="pu-url-input-wrapper">
                                  <input type="text" value={project.slack_link || ""}
                                    onChange={(e) => handleUpdate(project.project_code, "slack_link", e.target.value)}
                                    className={cellInputClass(project.project_code, "slack_link", project.slack_link, "url-field-small")}
                                    disabled={readOnly}
                                    placeholder="Slack URL" />
                                  {project.slack_link && project.slack_link.startsWith("http") && (
                                    <a href={project.slack_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Slack">
                                      <Link size={12} />
                                    </a>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </td>

                        {/* Lead Engineer Column Group */}
                        <td className="td-lead">
                          <select value={project.lead_engineer || ""}
                            onChange={(e) => handleUpdate(project.project_code, "lead_engineer", e.target.value)}
                            className={cellSelectClass(project.project_code, "lead_engineer", project.lead_engineer, "lead-select-main")}
                            disabled={readOnly || isCompact}>
                            <option value="">Unassigned</option>
                            {leadEngineers.map((eng) => <option key={eng} value={eng}>{eng}</option>)}
                          </select>
                          {!isCompact && (
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                              <div className="pu-date-input-wrap">
                                <input type="date" value={project.start_date || ""}
                                  onChange={(e) => handleUpdate(project.project_code, "start_date", e.target.value)}
                                  className={cellInputClass(project.project_code, "start_date", project.start_date, "date-field-small")}
                                  disabled={readOnly} />
                              </div>
                              <div className="pu-date-input-wrap">
                                <input type="date" value={project.end_date || ""}
                                  onChange={(e) => handleUpdate(project.project_code, "end_date", e.target.value)}
                                  className={cellInputClass(project.project_code, "end_date", project.end_date, "date-field-small")}
                                  disabled={readOnly} />
                              </div>
                            </div>
                          )}
                        </td>

                        {/* Status Column Group */}
                        <td className="td-status-group">
                          <select value={project.status || "In progress"}
                            onChange={(e) => handleUpdate(project.project_code, "status", e.target.value)}
                            className={cellSelectClass(project.project_code, "status", project.status || "In progress", "status-select-main")}
                            disabled={readOnly || isCompact}>
                            {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                          </select>
                          <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                            <input type="text" value={project.priority || ""}
                              onChange={(e) => handleUpdate(project.project_code, "priority", e.target.value.toUpperCase())}
                              className={cellInputClass(project.project_code, "priority", project.priority, "priority-field-small")}
                              disabled={readOnly || isCompact}
                              placeholder="Priority" />
                          </div>
                        </td>

                        {/* Project Process (Checkboxes) */}
                        {!isCompact && (
                          <>
                            <td className="td-process">
                              <div className="pu-checkbox-grid">
                                {[
                                  { label: "BRD", field: "checkbox_bc" },
                                  { label: "Trello", field: "checkbox_trello" },
                                  { label: "WA", field: "checkbox_wa" },
                                  { label: "WS", field: "checkbox_ws" }
                                ].map((item) => {
                                  const dirty = isDirty(project.project_code, item.field);
                                  const dbUpdated = !dirty && isDbUpdated(project, item.field);
                                  const labelCls = `pu-checkbox-label${dirty ? " dirty" : ""}${dbUpdated ? " db-updated" : ""}`;
                                  
                                  return (
                                    <label key={item.field} className={labelCls}>
                                      <input
                                        type="checkbox"
                                        checked={(() => {
                                          const val = project[item.field];
                                          // null/undefined/empty means CHECKED
                                          if (val === null || val === undefined || val === "") return true;
                                          // 1 (or "1") means UNCHECKED
                                          if (val === 1 || val === "1" || val === 1.0 || val === "1.0") return false;
                                          return false; // default to unchecked for other values
                                        })()}
                                        onChange={(e) => {
                                          const newVal = e.target.checked ? null : 1;
                                          handleUpdate(project.project_code, item.field, newVal);
                                        }}
                                        disabled={readOnly}
                                      />
                                      <span>{item.label}</span>
                                    </label>
                                  );
                                })}
                              </div>
                            </td>

                            <td className="td-estimate">
                              <div className="pu-estimate-wrap">
                                <span className="pu-estimate-label">EST</span>
                                <input
                                  type="number"
                                  value={(() => {
                                    const val = project.estimated_days;
                                    if (val === null || val === undefined || val === "") return "";
                                    const num = parseFloat(val);
                                    if (isNaN(num)) return val;
                                    return num % 1 === 0 ? num.toString() : num.toString();
                                  })()}
                                  onChange={(e) => handleUpdate(project.project_code, "estimated_days", e.target.value ? parseFloat(e.target.value) : null)}
                                  className={cellInputClass(project.project_code, "estimated_days", project.estimated_days, "estimate-input")}
                                  disabled={readOnly}
                                />
                                <span className="pu-estimate-label" style={{ marginTop: "0.4rem" }}>ACTUAL</span>
                                <input
                                  type="number"
                                  value={(() => {
                                    const val = project.actual_days;
                                    if (val === null || val === undefined || val === "") return "";
                                    const num = parseFloat(val);
                                    if (isNaN(num)) return "";
                                    // Rounding: >=0.5 fraction → ceil, <0.5 → floor
                                    const frac = num - Math.floor(num);
                                    return frac >= 0.5 ? Math.ceil(num) : Math.floor(num);
                                  })()}
                                  className="pu-cell-input estimate-input"
                                  disabled={true}
                                  readOnly
                                  style={{ backgroundColor: "#f8fafc", color: "#64748b", cursor: "not-allowed" }}
                                />
                              </div>
                            </td>
                          </>
                        )}
                      </tr>



                      {/* Spacer row for record separation */}
                      <tr className="pu-spacer-row">
                        <td colSpan="7"></td>
                      </tr>
                    </React.Fragment>
                  ))
                ) : (
                  <tr>
                    <td colSpan={isCompact ? 5 : 7}>
                      <div className="pu-empty-state">
                        <Search size={24} />
                        <p>No projects match your current filters.</p>
                        <button className="pu-empty-link" onClick={resetFilters}>Clear filters</button>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>



      </div>
    </div>
  );
}

export default withStreamlitConnection(ProjectUpdateComponent);
