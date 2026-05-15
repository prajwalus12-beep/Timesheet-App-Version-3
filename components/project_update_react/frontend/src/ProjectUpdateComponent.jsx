import React, { useState, useMemo, useEffect, useCallback, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { ExternalLink, Search, Filter, Download, X, Info, Save, Link } from "lucide-react";
import "./styles.css";

function ProjectUpdateComponent(props) {
  const { args } = props;

  // Data from Python
  const serverProjects = args.projects || [];
  const leadEngineers = args.lead_engineers || [];
  const phaseOptions = args.phase_options || ["Analysis", "Design", "Development", "Testing", "Deployment", "Support"];
  const statusOptions = args.status_options || ["In progress", "Complete", "On hold", "Cancelled"];
  const readOnly = args.read_only || false;
  const isCompact = args.is_compact || false; // New prop for compact/report mode

  // Local working copy of projects
  const [projects, setProjects] = useState(() => {
    // Sort initially based on the numeric value of project_code descending
    return [...serverProjects].sort((a, b) => {
      const codeA = parseInt((a.project_code || "0").replace(/\\D/g, ""), 10) || 0;
      const codeB = parseInt((b.project_code || "0").replace(/\\D/g, ""), 10) || 0;
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
  const isAdmin = args.user_role === "admin";
  const [filterName, setFilterName] = useState("");
  const [filterCodeMin, setFilterCodeMin] = useState("");
  const [filterCodeMax, setFilterCodeMax] = useState("");
  const [filterLead, setFilterLead] = useState(isAdmin ? "" : (args.current_user || ""));
  const [filterPriorityMin, setFilterPriorityMin] = useState(isAdmin ? "" : "1");
  const [filterPriorityMax, setFilterPriorityMax] = useState(isAdmin ? "" : "1");
  const [filterPhase, setFilterPhase] = useState([]);
  const [filterStatus, setFilterStatus] = useState(isAdmin ? [] : ["In progress", "In testing", "To be deployed"]);
  const [filterUpdatedOnly, setFilterUpdatedOnly] = useState(false);
  const [filterShowCompleted, setFilterShowCompleted] = useState(false);

  // Adjust iframe height after each render
  useEffect(() => { Streamlit.setFrameHeight(); });

  // ---- Filtering ----
  const updatedFlagKeys = [
    "project_name_updated", "lead_engineer_updated", "priority_updated",
    "status_updated", "trello_link_updated", "start_date_updated",
    "end_date_updated", "phase_updated", "prototype_link_updated", "slack_link_updated",
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
      if (filterPhase.length > 0 && !filterPhase.includes(p.phase)) return false;
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
  }, [projects, filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterPhase, filterStatus, filterUpdatedOnly, filterShowCompleted]);

  const resetFilters = () => {
    setFilterName(""); setFilterCodeMin(""); setFilterCodeMax("");
    setFilterLead(isAdmin ? "" : (args.current_user || ""));
    setFilterPriorityMin(isAdmin ? "" : "1");
    setFilterPriorityMax(isAdmin ? "" : "1");
    setFilterPhase([]);
    setFilterStatus(isAdmin ? [] : ["In progress", "In testing", "To be deployed"]);
    setFilterUpdatedOnly(false);
    setFilterShowCompleted(false);
  };

  // ---- Infinite Scroll ----
  const [displayCount, setDisplayCount] = useState(30);

  // Reset display count when filters or data change
  useEffect(() => {
    setDisplayCount(30);
  }, [filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterPhase, filterStatus, projects]);

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
    projects.forEach((p, idx) => {
      const server = serverProjects.find((sp) => sp.project_code === p.project_code);
      if (!server) return;
      const changes = {};
      const editableFields = [
        "project_name", "lead_engineer", "priority", "start_date", "end_date",
        "status", "phase", "trello_link", "prototype_link", "slack_link",
        "checkbox_bc", "checkbox_trello", "checkbox_wa", "checkbox_ws", "estimated_days"
      ];
      editableFields.forEach((f) => {
        if (String(server[f] ?? "") !== String(p[f] ?? "")) {
          changes[f] = p[f];
        }
      });
      if (Object.keys(changes).length > 0) {
        edits[p.project_code] = changes;
      }
    });
    if (Object.keys(edits).length > 0) {
      setIsSaving(true);
      Streamlit.setComponentValue({ action: "save", edits: edits });
    }
  }, [projects, serverProjects]);

  // ---- Export ----
  const handleExportClick = () => {
    Streamlit.setComponentValue({ action: "open_export_modal" });
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
          </div>
        </div>

        {/* Unsaved Changes Banner */}
        {!readOnly && !isCompact && editedCount > 0 && (
          <div className="pu-unsaved-banner">
            <span>⚠ You have {editedCount} unsaved change(s).</span>
            <button className="pu-save-btn" onClick={handleSave} style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}>
              <Save size={14} /> Save
            </button>
          </div>
        )}

        {/* Quick Filters - Hide in compact mode */}
        {!isCompact && (
          <div className="pu-quick-filters">
            <span className="pu-quick-label">QUICK FILTER:</span>
            <label className={`pu-toggle ${filterUpdatedOnly ? "active" : ""}`}>
              <input type="checkbox" checked={filterUpdatedOnly} onChange={(e) => setFilterUpdatedOnly(e.target.checked)} />
              <span>Show only updated</span>
            </label>
            <label className={`pu-toggle ${filterShowCompleted ? "active" : ""}`}>
              <input type="checkbox" checked={filterShowCompleted} onChange={(e) => setFilterShowCompleted(e.target.checked)} />
              <span>Show completed records</span>
            </label>
          </div>
        )}

        {/* Filters */}
        <div className="pu-filters">
          <div className="pu-filters-header">
            <Filter size={18} />
            <span>Filters</span>
          </div>
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


            {/* Phase - Hide in compact mode */}
            {!isCompact && (
              <div className="pu-filter-group">
                <label className="pu-filter-label">Phase</label>
                <MultiSelect 
                  options={phaseOptions}
                  selected={filterPhase}
                  onChange={setFilterPhase}
                  placeholder="All Phases"
                />
              </div>
            )}

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
                    PROJECT NAME / TRELLO URL /<br />
                    PROTOTYPE URL / SLACK URL
                  </th>
                  <th className="th-lead">
                    LEAD ENGINEER /<br />
                    START DATE / END DATE
                  </th>
                  <th className="th-status">
                    STATUS / PRIORITY { !isCompact && "/ PHASE" }
                  </th>
                  {!isCompact && (
                    <>
                      <th className="th-process">
                        <span className="process-header">PROJECT PROCESS</span>
                      </th>
                      <th className="th-estimate">
                        <span className="process-header">ESTIMATE DAYS</span>
                      </th>
                    </>
                  )}
                </tr>
              </thead>
              <tbody>
                {filteredProjects.length > 0 ? (
                  filteredProjects.slice(0, displayCount).map((project, index) => (

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
                          <div className="pu-url-row" style={{ gridTemplateColumns: isCompact ? "1fr" : "repeat(3, 1fr)" }}>
                            <input type="text" value={project.trello_link || ""}
                              onChange={(e) => handleUpdate(project.project_code, "trello_link", e.target.value)}
                              className={cellInputClass(project.project_code, "trello_link", project.trello_link, "url-field-small")}
                              disabled={readOnly || isCompact}
                              placeholder="Trello URL" />
                            {!isCompact && (
                              <>
                                <input type="text" value={project.prototype_link || ""}
                                  onChange={(e) => handleUpdate(project.project_code, "prototype_link", e.target.value)}
                                  className={cellInputClass(project.project_code, "prototype_link", project.prototype_link, "url-field-small")}
                                  disabled={readOnly}
                                  placeholder="Prototype URL" />
                                <input type="text" value={project.slack_link || ""}
                                  onChange={(e) => handleUpdate(project.project_code, "slack_link", e.target.value)}
                                  className={cellInputClass(project.project_code, "slack_link", project.slack_link, "url-field-small")}
                                  disabled={readOnly}
                                  placeholder="Slack URL" />
                              </>
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
                            <div className="pu-date-row">
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
                          <div className="pu-phase-row" style={{ gridTemplateColumns: isCompact ? "1fr" : "2fr 1fr" }}>
                            {!isCompact && (
                              <select value={project.phase || "Analysis"}
                                onChange={(e) => handleUpdate(project.project_code, "phase", e.target.value)}
                                className={cellSelectClass(project.project_code, "phase", project.phase || "Analysis", "phase-select-small")}
                                disabled={readOnly}>
                                {phaseOptions.map((ph) => <option key={ph} value={ph}>{ph}</option>)}
                              </select>
                            )}
                            <input type="text" value={project.priority || ""}
                              onChange={(e) => handleUpdate(project.project_code, "priority", e.target.value.toUpperCase())}
                              className={cellInputClass(project.project_code, "priority", project.priority, "priority-field-small")}
                              disabled={readOnly || isCompact} />
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
                                <span className="pu-estimate-label">DAYS</span>
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
