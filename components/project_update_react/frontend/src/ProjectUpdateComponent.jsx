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
        const codeA = parseInt((a.project_code || "0").replace(/\\D/g, ""), 10) || 0;
        const codeB = parseInt((b.project_code || "0").replace(/\\D/g, ""), 10) || 0;
        return codeB - codeA;
      });
      setProjects(sorted);
    }
  }, [serverProjects]);

  // Filter States
  const [filterName, setFilterName] = useState("");
  const [filterCodeMin, setFilterCodeMin] = useState("");
  const [filterCodeMax, setFilterCodeMax] = useState("");
  const [filterLead, setFilterLead] = useState("");
  const [filterPriority, setFilterPriority] = useState("");
  const [filterPhase, setFilterPhase] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterUpdatedOnly, setFilterUpdatedOnly] = useState(false);
  const [filterShowCompleted, setFilterShowCompleted] = useState(false);

  // Adjust iframe height after each render
  useEffect(() => { Streamlit.setFrameHeight(); });

  // ---- Filtering ----
  const updatedFlagKeys = [
    "project_name_updated", "lead_engineer_updated", "priority_updated",
    "status_updated", "trello_link_updated", "start_date_updated",
    "end_date_updated", "phase_updated", "prototype_link_updated"
  ];

  const filteredProjects = useMemo(() => {
    return projects.filter((p) => {
      if (filterName && !(p.project_name || "").toLowerCase().includes(filterName.toLowerCase())) return false;
      const code = parseInt(p.project_code, 10);
      if (filterCodeMin && code < parseInt(filterCodeMin, 10)) return false;
      if (filterCodeMax && code > parseInt(filterCodeMax, 10)) return false;
      if (filterLead && p.lead_engineer !== filterLead) return false;
      if (filterPriority && (p.priority || "").toUpperCase() !== filterPriority.toUpperCase()) return false;
      if (filterPhase && p.phase !== filterPhase) return false;
      if (filterStatus && p.status !== filterStatus) return false;

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
  }, [projects, filterName, filterCodeMin, filterCodeMax, filterLead, filterPriority, filterPhase, filterStatus, filterUpdatedOnly, filterShowCompleted]);

  const resetFilters = () => {
    setFilterName(""); setFilterCodeMin(""); setFilterCodeMax("");
    setFilterLead(""); setFilterPriority(""); setFilterPhase(""); setFilterStatus("");
    setFilterUpdatedOnly(false);
    setFilterShowCompleted(false);
  };

  // ---- Infinite Scroll ----
  const [displayCount, setDisplayCount] = useState(30);

  // Reset display count when filters or data change
  useEffect(() => {
    setDisplayCount(30);
  }, [filterName, filterCodeMin, filterCodeMax, filterLead, filterPriority, filterPhase, filterStatus, projects]);

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
      const editableFields = ["project_name", "lead_engineer", "priority", "start_date", "end_date", "status", "phase", "trello_link", "prototype_link"];
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

  // Truncate text helper
  const truncate = (text, maxLen = 30) => {
    if (!text) return "";
    return text.length > maxLen ? text.substring(0, maxLen) + "…" : text;
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
              Showing {filteredProjects.length} of {projects.length} projects
            </span>
            {!readOnly && editedCount > 0 && (
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
        {!readOnly && editedCount > 0 && (
          <div className="pu-unsaved-banner">
            <span>⚠ You have {editedCount} unsaved change(s).</span>
            <button className="pu-save-btn" onClick={handleSave} style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}>
              <Save size={14} /> Save
            </button>
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
              <div className="pu-filter-code-range">
                <input type="number" placeholder="Min" value={filterCodeMin}
                  onChange={(e) => setFilterCodeMin(e.target.value)} className="pu-filter-input" />
                <span className="pu-code-separator">–</span>
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

            {/* Priority */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Priority</label>
              <input type="text" placeholder="e.g. 1 ,2" value={filterPriority}
                onChange={(e) => setFilterPriority(e.target.value)}
                className="pu-filter-input" style={{ textTransform: "uppercase" }} />
            </div>

            {/* Phase */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Phase</label>
              <select value={filterPhase} onChange={(e) => setFilterPhase(e.target.value)} className="pu-filter-select">
                <option value="">All Phases</option>
                {phaseOptions.map((ph) => <option key={ph} value={ph}>{ph}</option>)}
              </select>
            </div>

            {/* Status + Clear */}
            <div className="pu-filter-group">
              <label className="pu-filter-label">Status</label>
              <div className="pu-status-row">
                <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="pu-filter-select">
                  <option value="">All Statuses</option>
                  {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <button className="pu-clear-btn" onClick={resetFilters} title="Clear all filters">Clear</button>
              </div>
            </div>

            {/* Quick Filters */}
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

          </div>
        </div>

        {/* Data Table — Two-line row layout matching screenshot */}
        <div className="pu-table-wrapper">
          <div className="pu-table-scroll" onScroll={handleScroll}>
            <table className="pu-table">
              <thead>
                <tr>
                  <th className="th-hash" rowSpan="3">#</th>
                  <th className="th-code" rowSpan="3">CODE</th>
                  <th className="th-project">PROJECT NAME</th>
                  <th className="th-lead">LEAD ENGINEER</th>
                  <th className="th-status">STATUS</th>
                  <th className="th-phase">PHASE</th>
                </tr>
                <tr>
                  <th className="th-sub"><Link size={12} className="th-sub-icon" /> TRELLO URL</th>
                  <th className="th-sub">START DATE</th>
                  <th className="th-sub">END DATE</th>
                  <th className="th-sub"><span className="th-sub-icon-circle">⊙</span> PRIORITY</th>
                </tr>
                <tr>
                  <th className="th-sub"><Link size={12} className="th-sub-icon" /> PROTOTYPE URL</th>
                  <th className="th-sub"><Link size={12} className="th-sub-icon" /> SLACK URL</th>
                  <th className="th-sub" colSpan="2"></th>
                </tr>
              </thead>
              <tbody>
                {filteredProjects.length > 0 ? (
                  filteredProjects.slice(0, displayCount).map((project, index) => (
                    <React.Fragment key={project.project_code}>
                      {/* Primary row */}
                      <tr className="pu-row-primary">
                        <td className="td-hash" rowSpan="3">{index + 1}</td>
                        <td className="td-code" rowSpan="3">
                          <b>{parseInt(project.project_code || "0", 10) + 1}</b>
                        </td>

                        {/* Project Name */}
                        <td className="td-project-name">
                          <textarea
                            rows={2}
                            value={project.project_name || ""}
                            onChange={(e) => handleUpdate(project.project_code, "project_name", e.target.value)}
                            className={cellInputClass(project.project_code, "project_name", project.project_name, "name-field")}
                            disabled={readOnly}
                            title={project.project_name || "Project Name is required"}
                            style={{ resize: "none", overflow: "hidden", fontFamily: "inherit", minHeight: "3rem", lineHeight: "1.25" }}
                          />
                        </td>

                        {/* Lead Engineer */}
                        <td className="td-lead">
                          <select value={project.lead_engineer || ""}
                            onChange={(e) => handleUpdate(project.project_code, "lead_engineer", e.target.value)}
                            className={cellSelectClass(project.project_code, "lead_engineer", project.lead_engineer)}
                            disabled={readOnly}
                            title={!project.lead_engineer ? "Lead Engineer is not yet assigned" : ""}>
                            <option value="">Unassigned</option>
                            {leadEngineers.map((eng) => <option key={eng} value={eng}>{eng}</option>)}
                          </select>
                        </td>

                        {/* Status */}
                        <td className="td-status">
                          <select value={project.status || "In progress"}
                            onChange={(e) => handleUpdate(project.project_code, "status", e.target.value)}
                            className={cellSelectClass(project.project_code, "status", project.status || "In progress")}
                            disabled={readOnly}>
                            {statusOptions.map((s) => <option key={s} value={s}>{s}</option>)}
                          </select>
                        </td>

                        {/* Phase */}
                        <td className="td-phase">
                          <select value={project.phase || "Analysis"}
                            onChange={(e) => handleUpdate(project.project_code, "phase", e.target.value)}
                            className={cellSelectClass(project.project_code, "phase", project.phase || "Analysis")}
                            disabled={readOnly}>
                            {phaseOptions.map((ph) => <option key={ph} value={ph}>{ph}</option>)}
                          </select>
                        </td>
                      </tr>

                      {/* Secondary row */}
                      <tr className="pu-row-secondary">
                        {/* Trello URL */}
                        <td className="td-trello">
                          <div className="pu-url-input-wrapper">
                            <input type="text" value={project.trello_link || ""}
                              onChange={(e) => handleUpdate(project.project_code, "trello_link", e.target.value)}
                              className={cellInputClass(project.project_code, "trello_link", project.trello_link, "url-field")}
                              disabled={readOnly}
                              placeholder="Trello URL"
                              title={!project.trello_link ? "Trello URL is not yet filled" : ""} />
                            {project.trello_link && (
                              <a href={project.trello_link.startsWith('http') ? project.trello_link : `https://${project.trello_link}`}
                                target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Link">
                                <ExternalLink size={14} />
                              </a>
                            )}
                          </div>
                        </td>

                        {/* Start Date */}
                        <td className="td-date">
                          <input type="date" value={project.start_date || ""}
                            onChange={(e) => handleUpdate(project.project_code, "start_date", e.target.value)}
                            className={cellInputClass(project.project_code, "start_date", project.start_date, "date-field")}
                            disabled={readOnly}
                            placeholder="dd - mm - yyyy"
                            title={!project.start_date ? "Start Date is not yet filled" : ""} />
                        </td>

                        {/* End Date */}
                        <td className="td-date">
                          <input type="date" value={project.end_date || ""}
                            onChange={(e) => handleUpdate(project.project_code, "end_date", e.target.value)}
                            className={cellInputClass(project.project_code, "end_date", project.end_date, "date-field")}
                            disabled={readOnly}
                            placeholder="dd - mm - yyyy"
                            title={!project.end_date ? "End Date is not yet filled" : ""} />
                        </td>

                        {/* Priority */}
                        <td className="td-priority">
                          <input type="text" value={project.priority || ""}
                            onChange={(e) => handleUpdate(project.project_code, "priority", e.target.value.toUpperCase())}
                            maxLength={4}
                            className={cellInputClass(project.project_code, "priority", project.priority, "priority-field")}
                            disabled={readOnly}
                            title={!project.priority ? "Priority is not yet filled" : "Priority (e.g. 10)"} />
                        </td>
                      </tr>

                      {/* Tertiary row */}
                      <tr className="pu-row-tertiary">
                        {/* Prototype URL */}
                        <td className="td-prototype">
                          <div className="pu-url-input-wrapper">
                            <input type="text" value={project.prototype_link || ""}
                              onChange={(e) => handleUpdate(project.project_code, "prototype_link", e.target.value)}
                              className={cellInputClass(project.project_code, "prototype_link", project.prototype_link, "url-field")}
                              disabled={readOnly}
                              placeholder="Prototype URL"
                              title={!project.prototype_link ? "Prototype URL is not yet filled" : ""} />
                            {project.prototype_link && (
                              <a href={project.prototype_link.startsWith('http') ? project.prototype_link : `https://${project.prototype_link}`}
                                target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Link">
                                <ExternalLink size={14} />
                              </a>
                            )}
                          </div>
                        </td>

                        {/* Slack URL — read-only display */}
                        <td className="td-slack">
                          <div className="pu-url-input-wrapper">
                            <input
                              type="text"
                              value={project.slack_link || ""}
                              readOnly
                              className="pu-cell-input url-field pu-readonly-field"
                              placeholder="Slack URL"
                              title={project.slack_link ? project.slack_link : "Slack URL is not yet filled"}
                            />
                            {project.slack_link && (
                              <a
                                href={project.slack_link.startsWith('http') ? project.slack_link : `https://${project.slack_link}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="pu-input-url-btn"
                                title="Open Slack Link"
                              >
                                <ExternalLink size={14} />
                              </a>
                            )}
                          </div>
                        </td>

                        <td colSpan="2"></td>
                      </tr>

                      {/* Spacer row for record separation */}
                      <tr className="pu-spacer-row">
                        <td colSpan="6"></td>
                      </tr>
                    </React.Fragment>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6">
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
