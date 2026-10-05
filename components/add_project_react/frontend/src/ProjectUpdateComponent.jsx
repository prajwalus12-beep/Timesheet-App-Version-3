import React, { useState, useMemo, useEffect, useCallback, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { ExternalLink, Search, Filter, Download, X, Info, Save, Link, ChevronDown, ChevronUp, Send, Trash2 } from "lucide-react";
import "./styles.css";

function ProjectUpdateComponent(props) {
  const { args } = props;
  const serverProjects = args.projects || [];
  const leadEngineers = args.lead_engineers || [];
  const statusOptions = args.status_options || ["In progress", "Complete", "On hold", "Cancelled"];
  const readOnly = args.read_only || false;
  const isCompact = args.is_compact || false;
  const isAddMode = args.is_add_mode || false;
  const employees = args.employees || [];

  const [projects, setProjects] = useState(() => {
    return [...serverProjects].sort((a, b) => {
      const codeA = parseInt((a.project_code || "0").replace(/\D/g, ""), 10) || 0;
      const codeB = parseInt((b.project_code || "0").replace(/\D/g, ""), 10) || 0;
      return codeB - codeA;
    });
  });

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
      setSelectedIds(new Set());
    }
  }, [serverProjects]);

  // ---- Multi-select / delete state ----
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Build set of existing project codes for duplicate detection
  const existingProjectCodes = useMemo(() => {
    const s = new Set();
    serverProjects.forEach(p => { if (p.project_code) s.add(String(p.project_code).trim().toLowerCase()); });
    return s;
  }, [serverProjects]);

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
  // Field-level errors: { [projectCode]: { [fieldName]: errorMessage } }
  const [fieldErrors, setFieldErrors] = useState({});

  const [sortField, setSortField] = useState("project_code");
  const [sortOrder, setSortOrder] = useState("desc");

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder(field === "project_name" ? "asc" : "desc");
    }
  };

  useEffect(() => { Streamlit.setFrameHeight(); });

  const serverProjectsMap = useMemo(() => {
    const map = new Map();
    serverProjects.forEach(p => map.set(p.project_code, p));
    return map;
  }, [serverProjects]);

  const updatedFlagKeys = [
    "project_name_updated", "lead_engineer_updated", "priority_updated",
    "status_updated", "trello_link_updated", "start_date_updated",
    "end_date_updated", "prototype_link_updated", "slack_link_updated",
    "estimated_days_updated", "checkbox_bc_updated", "checkbox_trello_updated",
    "checkbox_wa_updated", "checkbox_ws_updated", "notes_updated"
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
        } else if (filterPriorityMin || filterPriorityMax) return false;
      }
      const server = serverProjectsMap.get(p.project_code);
      const originalStatus = server ? server.status : p.status;
      if (filterStatus.length > 0 && !filterStatus.includes(originalStatus)) return false;
      const isComplete = originalStatus === "Complete";
      const hasUpdate = updatedFlagKeys.some(k => p[k] === true || p[k] === "true" || p[k] === "True");
      if (filterShowCompleted) { if (!isComplete) return false; }
      else { if (isComplete && !hasUpdate) return false; }
      if (filterUpdatedOnly && !hasUpdate) return false;
      return true;
    });
  }, [projects, serverProjectsMap, filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterStatus, filterUpdatedOnly, filterShowCompleted]);

  const sortedProjects = useMemo(() => {
    return [...filteredProjects].sort((a, b) => {
      let valA = a[sortField], valB = b[sortField];
      if (sortField === "project_code") {
        valA = parseInt((valA || "0").replace(/\D/g, ""), 10) || 0;
        valB = parseInt((valB || "0").replace(/\D/g, ""), 10) || 0;
      } else if (sortField === "start_date" || sortField === "end_date") {
        valA = valA ? new Date(valA).getTime() : 0;
        valB = valB ? new Date(valB).getTime() : 0;
      } else {
        valA = (valA || "").toString().toLowerCase();
        valB = (valB || "").toString().toLowerCase();
      }
      if (valA < valB) return sortOrder === "asc" ? -1 : 1;
      if (valA > valB) return sortOrder === "asc" ? 1 : -1;
      return 0;
    });
  }, [filteredProjects, sortField, sortOrder]);

  const resetFilters = () => {
    setFilterName(""); setFilterCodeMin(""); setFilterCodeMax("");
    setFilterLead(""); setFilterPriorityMin(""); setFilterPriorityMax("");
    setFilterStatus([]); setFilterUpdatedOnly(false); setFilterShowCompleted(false);
  };

  const [displayCount, setDisplayCount] = useState(30);
  useEffect(() => { setDisplayCount(30); }, [filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterStatus, filterUpdatedOnly, filterShowCompleted, projects, sortField, sortOrder]);

  const handleScroll = (e) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    if (scrollHeight - scrollTop <= clientHeight + 50 && displayCount < filteredProjects.length) {
      setDisplayCount(prev => prev + 30);
    }
  };

  const handleUpdate = (projectCode, field, value) => {
    setProjects(prev => prev.map(p => p.project_code === projectCode ? { ...p, [field]: value } : p));
    if (value && String(value).trim()) {
      setFieldErrors(prev => {
        const updated = { ...prev };
        if (updated[projectCode]) {
          const copy = { ...updated[projectCode] };
          delete copy[field];
          updated[projectCode] = copy;
        }
        return updated;
      });
    }
  };

  const isDirty = (projectCode, field) => {
    const local = projects.find(p => p.project_code === projectCode);
    if (!local) return false;
    if (local._isNew) return !!local[field];
    const server = serverProjects.find(p => p.project_code === projectCode);
    if (!server) return false;
    return String(server[field] ?? "") !== String(local[field] ?? "");
  };

  const isDbUpdated = (project, field) => {
    const flag = project[field + "_updated"];
    return flag === true || flag === "true" || flag === "True";
  };

  const editedCount = useMemo(() => {
    return projects.filter(p => {
      if (p._isNew) return true;
      const server = serverProjects.find(sp => sp.project_code === p.project_code);
      return server && JSON.stringify(server) !== JSON.stringify(p);
    }).length;
  }, [projects, serverProjects]);

  // ---- Delete helpers ----
  const toggleSelectProject = (recordId) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(recordId)) next.delete(recordId); else next.add(recordId);
      return next;
    });
  };

  const visibleIds = sortedProjects.slice(0, displayCount).map(p => p.id).filter(id => id != null);
  const allVisibleSelected = visibleIds.length > 0 && visibleIds.every(id => selectedIds.has(id));
  const someVisibleSelected = visibleIds.some(id => selectedIds.has(id));

  const toggleSelectAll = () => {
    if (allVisibleSelected) {
      setSelectedIds(prev => { const next = new Set(prev); visibleIds.forEach(id => next.delete(id)); return next; });
    } else {
      setSelectedIds(prev => { const next = new Set(prev); visibleIds.forEach(id => next.add(id)); return next; });
    }
  };

  const handleDeleteSingle = (project) => { setDeleteTarget(project); setShowDeleteConfirm(true); };
  const handleDeleteSelected = () => { if (selectedIds.size === 0) return; setDeleteTarget(null); setShowDeleteConfirm(true); };

  const confirmDelete = () => {
    let recordIds = [];
    if (deleteTarget) {
      if (deleteTarget._isNew) {
        setProjects(prev => prev.filter(p => p.project_code !== deleteTarget.project_code));
        setShowDeleteConfirm(false); setDeleteTarget(null); return;
      }
      recordIds = [deleteTarget.id];
    } else {
      const newRowCodes = [...selectedIds]
        .map(id => projects.find(p => p.id === id))
        .filter(p => p && p._isNew).map(p => p.project_code);
      if (newRowCodes.length > 0)
        setProjects(prev => prev.filter(p => !newRowCodes.includes(p.project_code)));
      recordIds = [...selectedIds].filter(id => {
        const p = projects.find(p2 => p2.id === id);
        return p && !p._isNew;
      });
    }
    setShowDeleteConfirm(false); setDeleteTarget(null); setSelectedIds(new Set());
    if (recordIds.length > 0) Streamlit.setComponentValue({ action: "delete_projects", record_ids: recordIds });
  };

  // ---- Required field validation ----
  const REQUIRED_FIELDS = ["project_code", "project_name", "lead_engineer", "start_date", "end_date", "estimated_days"];
  const REQUIRED_LABELS = {
    project_code: "Project Code", project_name: "Project Name",
    lead_engineer: "Lead Engineer", start_date: "Start Date",
    end_date: "Est. Date", estimated_days: "Est. Days"
  };
  const getFieldError = (projectCode, field) => fieldErrors[projectCode]?.[field] || null;

  // ---- Save ----
  const handleSave = useCallback(() => {
    const edits = {};
    const vErrors = [];
    const newFieldErrors = {};

    projects.forEach(p => {
      let server;
      if (!p._isNew) {
        server = serverProjects.find(sp => sp.project_code === p.project_code);
        if (!server) return;
      }
      const changes = {};
      const editableFields = [
        "project_name", "lead_engineer", "priority", "start_date", "end_date",
        "status", "trello_link", "prototype_link", "slack_link",
        "checkbox_bc", "checkbox_trello", "checkbox_wa", "checkbox_ws", "estimated_days", "notes"
      ];
      if (p._isNew) {
        changes["_isNew"] = true;
        changes["project_code"] = p.project_code;
        editableFields.forEach(f => { if (p[f] !== undefined && p[f] !== "") changes[f] = p[f]; });
      } else {
        editableFields.forEach(f => { if (String(server[f] ?? "") !== String(p[f] ?? "")) changes[f] = p[f]; });
      }

      if (Object.keys(changes).length > 0 && (p._isNew || Object.keys(changes).length > 1 || !changes["_isNew"])) {
        const errs = [];
        const isUnchecked = v => v === 1 || v === "1" || v === 1.0 || v === "1.0";

        // Required field check for new projects
        if (p._isNew) {
          const reqErrs = {};
          REQUIRED_FIELDS.forEach(f => {
            const val = p[f];
            if (!val || String(val).trim() === "") {
              reqErrs[f] = `${REQUIRED_LABELS[f]} is required`;
              errs.push(`${REQUIRED_LABELS[f]} is required`);
            }
          });
          if (Object.keys(reqErrs).length > 0) newFieldErrors[p.project_code] = reqErrs;

          // Frontend duplicate project code check
          const code = String(p.project_code || "").trim();
          if (code && !code.startsWith("new_") && existingProjectCodes.has(code.toLowerCase())) {
            errs.push(`Project Code "${code}" already exists — use a unique code`);
            newFieldErrors[p.project_code] = {
              ...(newFieldErrors[p.project_code] || {}),
              project_code: `Code "${code}" already exists`
            };
          }
        }

        if (p._isNew && (!p.project_code || p.project_code.startsWith("new_"))) errs.push("Job No is required for new projects");
        if (!p.start_date) errs.push("Missing start date");
        if (!p.end_date) errs.push("Missing End Date");
        if (p.start_date && p.end_date && new Date(p.start_date) > new Date(p.end_date)) errs.push("Start Date must be <= End Date");
        const pastStatuses = ["Not started", "Ongoing", "In testing", "Awaiting Info", "At Beta", "In progress"];
        if (pastStatuses.includes(p.status) && p.end_date) {
          const today = new Date(); today.setHours(0,0,0,0);
          if (new Date(p.end_date) < today) errs.push("Past date is not allowed.");
        }
        if (!p.trello_link) errs.push("Missing Trello link");
        if (!p.estimated_days) errs.push("Missing estimates");
        if (parseFloat(p.actual_days || 0) > 1 && p.status === "Not started") errs.push("Actual days > 1 but status is Not started");
        if (isUnchecked(p.checkbox_bc)) errs.push("BRD checkbox not checked");
        if (isUnchecked(p.checkbox_trello)) errs.push("Trello checkbox not checked");
        if (isUnchecked(p.checkbox_wa)) errs.push("WA checkbox not checked");
        if (isUnchecked(p.checkbox_ws)) errs.push("WS checkbox not checked");

        const uniqueErrs = [...new Set(errs)];
        if (uniqueErrs.length > 0) vErrors.push({ projectCode: p.project_code, name: p.project_name, errors: uniqueErrs });
        edits[p.project_code] = changes;
      }
    });

    setFieldErrors(newFieldErrors);
    if (vErrors.length > 0) {
      setValidationErrors(vErrors);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    setValidationErrors([]);
    if (Object.keys(edits).length > 0) Streamlit.setComponentValue({ action: "save", edits });
  }, [projects, serverProjects, existingProjectCodes]);

  const handleExportClick = () => Streamlit.setComponentValue({ action: "open_export_modal" });
  const handleOpenReminderModal = () => {
    const displayedProjectCodes = filteredProjects.map(p => String(p.project_code));
    Streamlit.setComponentValue({ action: "open_reminder_modal", payload: { displayedProjectCodes } });
  };

  // ---- Cell class helpers ----
  const isFieldEmpty = v => !v || v.toString().trim() === "";

  const cellInputClass = (projectCode, field, value, extra = "") => {
    let cls = "pu-cell-input";
    if (extra) cls += " " + extra;
    if (isDirty(projectCode, field)) cls += " dirty";
    const proj = projects.find(p => p.project_code === projectCode);
    if (proj && !proj._isNew && !isDirty(projectCode, field) && isDbUpdated(proj, field)) cls += " db-updated";
    if (isFieldEmpty(value)) cls += " pu-highlight-empty";
    if (getFieldError(projectCode, field)) cls += " pu-field-error";
    return cls;
  };

  const cellSelectClass = (projectCode, field, value, extra = "") => {
    let cls = "pu-cell-select";
    if (extra) cls += " " + extra;
    if (isDirty(projectCode, field)) cls += " dirty";
    const proj = projects.find(p => p.project_code === projectCode);
    if (proj && !proj._isNew && !isDirty(projectCode, field) && isDbUpdated(proj, field)) cls += " db-updated";
    if (isFieldEmpty(value)) cls += " pu-highlight-empty";
    if (getFieldError(projectCode, field)) cls += " pu-field-error";
    return cls;
  };

  // ---- MultiSelect sub-component ----
  const MultiSelect = ({ options, selected, onChange, placeholder }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [tempSelected, setTempSelected] = useState(selected);
    const containerRef = useRef(null);
    useEffect(() => { setTempSelected(selected); }, [selected]);
    useEffect(() => {
      const handler = e => {
        if (containerRef.current && !containerRef.current.contains(e.target)) {
          setIsOpen(false); setTempSelected(selected);
        }
      };
      document.addEventListener("mousedown", handler);
      return () => document.removeEventListener("mousedown", handler);
    }, [selected]);
    const toggleOption = opt => setTempSelected(prev =>
      prev.includes(opt) ? prev.filter(i => i !== opt) : [...prev, opt]
    );
    const handleApply = () => { onChange(tempSelected); setIsOpen(false); };
    const displayValue = () => {
      if (selected.length === 0) return <span className="pu-multiselect-placeholder">{placeholder}</span>;
      if (selected.length <= 2) return selected.join(", ");
      return selected.slice(0, 2).join(", ") + "...";
    };
    return (
      <div className="pu-multiselect" ref={containerRef}>
        <button className={`pu-multiselect-trigger ${isOpen ? "active" : ""}`} onClick={() => setIsOpen(!isOpen)}>
          <div className="pu-multiselect-value">{displayValue()}</div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            {selected.length > 1 && <span className="pu-multiselect-badge">{selected.length}</span>}
            <ExternalLink size={14} className="pu-multiselect-arrow" style={{ transform: isOpen ? "rotate(180deg)" : "none" }} />
          </div>
        </button>
        {isOpen && (
          <div className="pu-multiselect-menu">
            <div className="pu-multiselect-list">
              {options.map(opt => (
                <div key={opt} className={`pu-multiselect-item ${tempSelected.includes(opt) ? "selected" : ""}`} onClick={() => toggleOption(opt)}>
                  <div className="pu-multiselect-checkbox">
                    {tempSelected.includes(opt) && <X size={10} className="pu-multiselect-check-icon" />}
                  </div>
                  <span>{opt}</span>
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

  // ---- Delete Confirmation Dialog ----
  const DeleteConfirmDialog = () => {
    const isMulti = !deleteTarget;
    const count = isMulti ? selectedIds.size : 1;
    const name = deleteTarget ? (deleteTarget.project_name || deleteTarget.project_code) : null;
    return (
      <div className="pu-modal-overlay" onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>
        <div className="pu-modal" onClick={e => e.stopPropagation()} style={{ maxWidth: "24rem" }}>
          <div className="pu-modal-header" style={{ background: "#fef2f2", borderBottom: "1px solid #fecaca" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Trash2 size={18} color="#dc2626" />
              <h3 style={{ color: "#991b1b" }}>Confirm Delete</h3>
            </div>
            <button className="pu-modal-close" onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}>
              <X size={18} />
            </button>
          </div>
          <div className="pu-modal-body">
            <p style={{ fontSize: "0.9rem", color: "#374151", marginBottom: "1.25rem" }}>
              {isMulti
                ? <><strong>{count}</strong> selected project{count !== 1 ? "s" : ""} will be <strong>permanently deleted</strong>. This cannot be undone.</>
                : <>Project <strong>"{name}"</strong> will be <strong>permanently deleted</strong>. This cannot be undone.</>}
            </p>
            <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
              <button onClick={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}
                style={{ padding: "0.5rem 1.25rem", borderRadius: "6px", border: "1px solid #e2e8f0", background: "#f8fafc", cursor: "pointer", fontSize: "0.875rem", fontWeight: 500 }}>
                Cancel
              </button>
              <button onClick={confirmDelete}
                style={{ padding: "0.5rem 1.25rem", borderRadius: "6px", border: "none", background: "#dc2626", color: "#fff", cursor: "pointer", fontSize: "0.875rem", fontWeight: 600, display: "flex", alignItems: "center", gap: "6px" }}>
                <Trash2 size={14} /> Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const colSpanFull = !readOnly && !isCompact && isAddMode ? 9 : (isCompact ? 5 : 7);
  const R = <span style={{ color: "#ef4444", fontWeight: 700 }}> *</span>;

  return (
    <div className="pu-page">
      {showDeleteConfirm && <DeleteConfirmDialog />}
      <div className="pu-container">

        {/* ── Header ── */}
        <div className="pu-header">
          <h1 className="pu-title">Project Attributes</h1>
          <div className="pu-header-actions">
            <span className="pu-count-label">
              Showing {filteredProjects.length} incomplete project status records of {projects.length} projects.
            </span>
            {!readOnly && !isCompact && editedCount > 0 && (
              <button className="pu-save-btn" onClick={handleSave}><Save size={16} /> Save Changes ({editedCount})</button>
            )}
            {!readOnly && !isCompact && isAddMode && (
              <button className="pu-save-btn" onClick={() => {
                const newProj = { project_code: "new_" + Math.random().toString(36).substr(2, 9), project_name: "", status: "Not started", _isNew: true };
                setProjects([newProj, ...projects]);
              }}>&#10133; Add Project</button>
            )}
            {!readOnly && !isCompact && selectedIds.size > 0 && (
              <button onClick={handleDeleteSelected}
                style={{ display: "inline-flex", alignItems: "center", gap: "0.5rem", padding: "0.5rem 1rem", background: "#dc2626", color: "#fff", border: "none", borderRadius: "0.5rem", cursor: "pointer", fontSize: "0.875rem", fontWeight: 500 }}>
                <Trash2 size={16} /> Delete Selected ({selectedIds.size})
              </button>
            )}
            <button className="pu-export-btn" onClick={handleExportClick}><Download size={16} /> Export</button>
            {!readOnly && !isCompact && isAdmin && (
              <button className="pu-export-btn" onClick={handleOpenReminderModal}><Send size={16} /> Send Reminder</button>
            )}
          </div>
        </div>

        {/* ── Validation Errors Banner ── */}
        {validationErrors.length > 0 && (
          <div style={{ backgroundColor: "#fee2e2", border: "1px solid #ef4444", borderRadius: "6px", padding: "12px", marginBottom: "1rem", color: "#b91c1c" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "8px" }}>
              <strong style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <Info size={16} /> Validation Errors — please fix before saving
              </strong>
              <button onClick={() => setValidationErrors([])} style={{ background: "none", border: "none", cursor: "pointer", color: "#b91c1c" }}><X size={16} /></button>
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

        {/* ── Unsaved Changes Banner ── */}
        {!readOnly && !isCompact && editedCount > 0 && (
          <div className="pu-unsaved-banner">
            <span>⚠ You have {editedCount} unsaved change(s).</span>
            <button className="pu-save-btn" onClick={handleSave} style={{ padding: "0.35rem 0.75rem", fontSize: "0.8rem" }}>
              <Save size={14} /> Save
            </button>
          </div>
        )}

        {/* ── Filters ── */}
        <div className="pu-filters">
          <div className="pu-filters-header"
            style={{ cursor: "pointer", display: "flex", justifyContent: "space-between", marginBottom: isFiltersOpen ? "1rem" : "0" }}
            onClick={() => setIsFiltersOpen(!isFiltersOpen)}>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <Filter size={18} /><span>Filters</span>
            </div>
            <div>{isFiltersOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}</div>
          </div>
          {isFiltersOpen && (
            <div className="pu-filters-grid">
              <div className="pu-filter-group">
                <label className="pu-filter-label">Project Name</label>
                <div className="pu-filter-input-wrap">
                  <input type="text" placeholder="Search Project Name..." value={filterName}
                    onChange={e => setFilterName(e.target.value)} className="pu-filter-input has-icon" />
                  <Search size={14} className="pu-filter-search-icon" />
                </div>
              </div>
              <div className="pu-filter-group">
                <label className="pu-filter-label">Project Code Range</label>
                <div className="pu-filter-range">
                  <input type="number" placeholder="Min" value={filterCodeMin} onChange={e => setFilterCodeMin(e.target.value)} className="pu-filter-input" />
                  <span className="pu-range-sep">–</span>
                  <input type="number" placeholder="Max" value={filterCodeMax} onChange={e => setFilterCodeMax(e.target.value)} className="pu-filter-input" />
                </div>
              </div>
              <div className="pu-filter-group">
                <label className="pu-filter-label">Lead Engineer</label>
                <select value={filterLead} onChange={e => setFilterLead(e.target.value)} className="pu-filter-select">
                  <option value="">All Engineers</option>
                  {leadEngineers.map(eng => <option key={eng} value={eng}>{eng}</option>)}
                </select>
              </div>
              <div className="pu-filter-group">
                <label className="pu-filter-label">Priority (Min - Max)</label>
                <div className="pu-filter-range">
                  <input type="number" placeholder="Min" value={filterPriorityMin} onChange={e => setFilterPriorityMin(e.target.value)} className="pu-filter-input" />
                  <span className="pu-range-sep">-</span>
                  <input type="number" placeholder="Max" value={filterPriorityMax} onChange={e => setFilterPriorityMax(e.target.value)} className="pu-filter-input" />
                </div>
              </div>
              <div className="pu-filter-group">
                <label className="pu-filter-label">Status</label>
                <div className="pu-status-row">
                  <MultiSelect options={statusOptions} selected={filterStatus} onChange={setFilterStatus} placeholder="All Statuses" />
                  <button className="pu-clear-btn" onClick={resetFilters} title="Clear all filters">Clear</button>
                </div>
              </div>
              {!isCompact && (
                <div className="pu-filter-group pu-filter-group--full">
                  <label className="pu-filter-label">Quick Filters</label>
                  <div style={{ display: "flex", gap: "10px" }}>
                    <button className={`pu-updated-toggle${filterUpdatedOnly ? " active" : ""}`}
                      onClick={() => setFilterUpdatedOnly(v => !v)} title="Show only rows with highlighted fields">
                      <span className="pu-updated-dot" /> Updated Records Only
                    </button>
                    <button className={`pu-updated-toggle${filterShowCompleted ? " active" : ""}`}
                      onClick={() => setFilterShowCompleted(v => !v)}
                      style={{ borderColor: filterShowCompleted ? "#10b981" : "", color: filterShowCompleted ? "#10b981" : "" }}
                      title="Show only completed projects">
                      <span className="pu-updated-dot" style={{ backgroundColor: filterShowCompleted ? "#10b981" : "" }} /> Completed Records
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* ── Sort Controls ── */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: "10px", marginBottom: "12px", padding: "10px 15px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", marginRight: "5px", letterSpacing: "0.05em" }}>Sort By:</span>
          {[
            { key: "project_code", label: "PROJECT CODE" },
            { key: "project_name", label: "PROJECT NAME" },
            ...(!isCompact ? [{ key: "start_date", label: "START DATE" }, { key: "end_date", label: "END DATE" }] : [])
          ].map(s => (
            <button key={s.key} onClick={() => handleSort(s.key)} style={{
              padding: "6px 14px", borderRadius: "6px", fontSize: "0.75rem", fontWeight: "700",
              border: sortField === s.key ? "1px solid #3b82f6" : "1px solid #cbd5e1",
              background: sortField === s.key ? "#eff6ff" : "#ffffff",
              color: sortField === s.key ? "#1d4ed8" : "#475569",
              cursor: "pointer", display: "flex", alignItems: "center", gap: "6px",
              boxShadow: "0 1px 2px 0 rgba(0,0,0,0.05)", textTransform: "uppercase"
            }}>
              {s.label} {sortField === s.key && (sortOrder === "asc" ? "▲" : "▼")}
            </button>
          ))}
        </div>

        {/* ── Data Table ── */}
        <div className="pu-table-wrapper">
          <div className="pu-table-scroll" onScroll={handleScroll}>
            <table className="pu-table">
              <thead>
                <tr>
                  {!readOnly && !isCompact && isAddMode && (
                    <th style={{ width: "2.5rem", textAlign: "center", padding: "0.5rem" }}>
                      <input type="checkbox" checked={allVisibleSelected}
                        ref={el => { if (el) el.indeterminate = someVisibleSelected && !allVisibleSelected; }}
                        onChange={toggleSelectAll} title="Select / deselect all visible"
                        style={{ cursor: "pointer", width: "15px", height: "15px" }} />
                    </th>
                  )}
                  <th className="th-hash">#</th>
                  <th className="th-code">CODE{R}</th>
                  <th className="th-project">
                    PROJECT NAME{R} / TRELLO URL
                    {!isCompact && (<> /<br />PROTOTYPE URL / SLACK URL</>)}
                  </th>
                  <th className="th-lead">
                    LEAD ENGINEER{R}
                    {!isCompact && (<> /<br />START DATE{R} / END DATE{R}</>)}
                  </th>
                  <th className="th-status">
                    STATUS / PRIORITY{!isCompact && (<> / NOTES</>)}
                  </th>
                  {!isCompact && (<>
                    <th className="th-process"><span className="process-header">PROJECT PROCESS</span></th>
                    <th className="th-estimate"><span className="process-header">TIME ANALYSIS<br />DAYS</span></th>
                  </>)}
                  {!readOnly && !isCompact && isAddMode && (
                    <th style={{ width: "3rem", textAlign: "center", padding: "0.5rem" }}></th>
                  )}
                </tr>
              </thead>
              <tbody>
                {sortedProjects.length > 0 ? (
                  sortedProjects.slice(0, displayCount).map((project, index) => {
                    const isSelected = project.id != null && selectedIds.has(project.id);
                    const projFieldErrs = fieldErrors[project.project_code] || {};
                    const isDupCode = project._isNew && project.project_code
                      && !project.project_code.startsWith("new_")
                      && existingProjectCodes.has(String(project.project_code).trim().toLowerCase());

                    return (
                      <React.Fragment key={project.project_code}>
                        <tr className={`pu-row-primary${isSelected ? " pu-row-selected" : ""}`}>

                          {/* Checkbox */}
                          {!readOnly && !isCompact && isAddMode && (
                            <td style={{ textAlign: "center", padding: "0.375rem 0.25rem", verticalAlign: "middle" }}>
                              <input type="checkbox" checked={isSelected}
                                onChange={() => toggleSelectProject(project.id)}
                                style={{ cursor: "pointer", width: "15px", height: "15px" }} />
                            </td>
                          )}

                          {/* Row number */}
                          <td className="td-hash">{index + 1}</td>

                          {/* Project Code */}
                          <td className="td-code">
                            {project._isNew ? (
                              <div>
                                <input type="text"
                                  value={project.project_code.startsWith("new_") ? "" : project.project_code}
                                  onChange={e => {
                                    const raw = e.target.value;
                                    const newCode = raw || project.project_code;
                                    setProjects(prev => prev.map(p =>
                                      p.project_code === project.project_code ? { ...p, project_code: newCode } : p
                                    ));
                                    if (raw) {
                                      setFieldErrors(prev => {
                                        const u = { ...prev };
                                        if (u[project.project_code]) {
                                          const c = { ...u[project.project_code] }; delete c.project_code; u[project.project_code] = c;
                                        }
                                        return u;
                                      });
                                    }
                                  }}
                                  className={`pu-cell-input${projFieldErrs.project_code || isDupCode ? " pu-field-error" : ""}`}
                                  placeholder="Job No *"
                                  style={{ width: "80px", padding: "4px" }}
                                />
                                {projFieldErrs.project_code && <div className="pu-field-error-msg">{projFieldErrs.project_code}</div>}
                                {isDupCode && !projFieldErrs.project_code && <div className="pu-field-error-msg">⚠ Code already exists</div>}
                              </div>
                            ) : (
                              <b>{project.project_code || ""}</b>
                            )}
                          </td>

                          {/* Project Name / URLs */}
                          <td className="td-project-name">
                            <div>
                              <input type="text" value={project.project_name || ""}
                                onChange={e => handleUpdate(project.project_code, "project_name", e.target.value)}
                                className={cellInputClass(project.project_code, "project_name", project.project_name, "name-field")}
                                disabled={readOnly || isCompact}
                                title={project.project_name || "Project Name — required"}
                                placeholder="Project Name *" />
                              {projFieldErrs.project_name && <div className="pu-field-error-msg">{projFieldErrs.project_name}</div>}
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                              <div className="pu-url-input-wrapper">
                                <input type="text" value={project.trello_link || ""}
                                  onChange={e => handleUpdate(project.project_code, "trello_link", e.target.value)}
                                  className={cellInputClass(project.project_code, "trello_link", project.trello_link, "url-field-small")}
                                  disabled={readOnly || isCompact} placeholder="Trello URL" />
                                {project.trello_link && project.trello_link.startsWith("http") && (
                                  <a href={project.trello_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Trello"><Link size={12} /></a>
                                )}
                              </div>
                              {!isCompact && (
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.15rem" }}>
                                  <div className="pu-url-input-wrapper">
                                    <input type="text" value={project.prototype_link || ""}
                                      onChange={e => handleUpdate(project.project_code, "prototype_link", e.target.value)}
                                      className={cellInputClass(project.project_code, "prototype_link", project.prototype_link, "url-field-small")}
                                      disabled={readOnly} placeholder="Prototype URL" />
                                    {project.prototype_link && project.prototype_link.startsWith("http") && (
                                      <a href={project.prototype_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Prototype"><Link size={12} /></a>
                                    )}
                                  </div>
                                  <div className="pu-url-input-wrapper">
                                    <input type="text" value={project.slack_link || ""}
                                      onChange={e => handleUpdate(project.project_code, "slack_link", e.target.value)}
                                      className={cellInputClass(project.project_code, "slack_link", project.slack_link, "url-field-small")}
                                      disabled={readOnly} placeholder="Slack URL" />
                                    {project.slack_link && project.slack_link.startsWith("http") && (
                                      <a href={project.slack_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Slack"><Link size={12} /></a>
                                    )}
                                  </div>
                                </div>
                              )}
                            </div>
                          </td>

                          {/* Lead Engineer / Dates */}
                          <td className="td-lead">
                            <div>
                              <select value={project.lead_engineer || ""}
                                onChange={e => handleUpdate(project.project_code, "lead_engineer", e.target.value)}
                                className={cellSelectClass(project.project_code, "lead_engineer", project.lead_engineer, "lead-select-main")}
                                disabled={readOnly || isCompact}>
                                <option value="">Lead Engineer *</option>
                                {leadEngineers.map(eng => <option key={eng} value={eng}>{eng}</option>)}
                              </select>
                              {projFieldErrs.lead_engineer && <div className="pu-field-error-msg">{projFieldErrs.lead_engineer}</div>}
                            </div>
                            {!isCompact && (
                              <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                                <div className="pu-date-input-wrap">
                                  <input type="date" value={project.start_date || ""}
                                    onChange={e => handleUpdate(project.project_code, "start_date", e.target.value)}
                                    className={cellInputClass(project.project_code, "start_date", project.start_date, "date-field-small")}
                                    disabled={readOnly} title="Start Date *" />
                                  {projFieldErrs.start_date && <div className="pu-field-error-msg">{projFieldErrs.start_date}</div>}
                                </div>
                                <div className="pu-date-input-wrap">
                                  <input type="date" value={project.end_date || ""}
                                    onChange={e => handleUpdate(project.project_code, "end_date", e.target.value)}
                                    className={cellInputClass(project.project_code, "end_date", project.end_date, "date-field-small")}
                                    disabled={readOnly} title="Est. Date (End Date) *" />
                                  {projFieldErrs.end_date && <div className="pu-field-error-msg">{projFieldErrs.end_date}</div>}
                                </div>
                              </div>
                            )}
                          </td>

                          {/* Status / Priority / Notes */}
                          <td className="td-status-group">
                            <select value={project.status || "In progress"}
                              onChange={e => handleUpdate(project.project_code, "status", e.target.value)}
                              className={cellSelectClass(project.project_code, "status", project.status || "In progress", "status-select-main")}
                              disabled={readOnly || isCompact}>
                              {statusOptions.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                              <input type="text" value={project.priority || ""}
                                onChange={e => handleUpdate(project.project_code, "priority", e.target.value.toUpperCase())}
                                className={cellInputClass(project.project_code, "priority", project.priority, "priority-field-small")}
                                disabled={readOnly || isCompact} placeholder="Priority" />
                              {!isCompact && (
                                <textarea value={project.notes || ""}
                                  onChange={e => handleUpdate(project.project_code, "notes", e.target.value || null)}
                                  className={`pu-notes-textarea${isDirty(project.project_code, "notes") ? " dirty" : ""}${!isDirty(project.project_code, "notes") && isDbUpdated(project, "notes") ? " db-updated" : ""}`}
                                  style={{ marginTop: "0.2rem", minHeight: "44px" }}
                                  disabled={readOnly} placeholder="Add notes…"
                                  title={project.notes || "Add notes..."} rows={2} />
                              )}
                            </div>
                          </td>

                          {/* Checkboxes + Est/Actual */}
                          {!isCompact && (<>
                            <td className="td-process">
                              <div className="pu-checkbox-grid">
                                {[
                                  { label: "BRD", field: "checkbox_bc" },
                                  { label: "Trello", field: "checkbox_trello" },
                                  { label: "WA", field: "checkbox_wa" },
                                  { label: "WS", field: "checkbox_ws" }
                                ].map(item => {
                                  const dirty = isDirty(project.project_code, item.field);
                                  const dbUpd = !dirty && isDbUpdated(project, item.field);
                                  return (
                                    <label key={item.field} className={`pu-checkbox-label${dirty ? " dirty" : ""}${dbUpd ? " db-updated" : ""}`}>
                                      <input type="checkbox"
                                        checked={(() => {
                                          const v = project[item.field];
                                          if (v === null || v === undefined || v === "") return true;
                                          if (v === 1 || v === "1" || v === 1.0 || v === "1.0") return false;
                                          return false;
                                        })()}
                                        onChange={e => handleUpdate(project.project_code, item.field, e.target.checked ? null : 1)}
                                        disabled={readOnly} />
                                      <span>{item.label}</span>
                                    </label>
                                  );
                                })}
                              </div>
                            </td>
                            <td className="td-estimate">
                              <div className="pu-estimate-wrap">
                                <span className="pu-estimate-label">EST <span style={{ color: "#ef4444" }}>*</span></span>
                                <input type="number"
                                  value={(() => {
                                    const v = project.estimated_days;
                                    if (v === null || v === undefined || v === "") return "";
                                    const n = parseFloat(v);
                                    return isNaN(n) ? v : n.toString();
                                  })()}
                                  onChange={e => handleUpdate(project.project_code, "estimated_days", e.target.value ? parseFloat(e.target.value) : null)}
                                  className={cellInputClass(project.project_code, "estimated_days", project.estimated_days, "estimate-input")}
                                  disabled={readOnly} placeholder="0" />
                                {projFieldErrs.estimated_days && (
                                  <div className="pu-field-error-msg" style={{ fontSize: "0.6rem" }}>{projFieldErrs.estimated_days}</div>
                                )}
                                <span className="pu-estimate-label" style={{ marginTop: "0.4rem" }}>ACTUAL</span>
                                <input type="number"
                                  value={(() => {
                                    const v = project.actual_days;
                                    if (v === null || v === undefined || v === "") return "";
                                    const n = parseFloat(v);
                                    if (isNaN(n)) return "";
                                    const f = n - Math.floor(n);
                                    return f >= 0.5 ? Math.ceil(n) : Math.floor(n);
                                  })()}
                                  className="pu-cell-input estimate-input" disabled readOnly
                                  style={{ backgroundColor: "#f8fafc", color: "#64748b", cursor: "not-allowed" }} />
                              </div>
                            </td>
                          </>)}

                          {/* Delete button */}
                          {!readOnly && !isCompact && isAddMode && (
                            <td style={{ textAlign: "center", padding: "0.375rem 0.25rem", verticalAlign: "middle" }}>
                              <button onClick={() => handleDeleteSingle(project)} title="Delete this project"
                                style={{ background: "none", border: "none", cursor: "pointer", color: "#94a3b8", padding: "4px", borderRadius: "4px", display: "inline-flex", alignItems: "center", transition: "color 150ms, background 150ms" }}
                                onMouseEnter={e => { e.currentTarget.style.color = "#dc2626"; e.currentTarget.style.background = "#fef2f2"; }}
                                onMouseLeave={e => { e.currentTarget.style.color = "#94a3b8"; e.currentTarget.style.background = "none"; }}>
                                <Trash2 size={15} />
                              </button>
                            </td>
                          )}
                        </tr>
                        <tr className="pu-spacer-row"><td colSpan={colSpanFull}></td></tr>
                      </React.Fragment>
                    );
                  })
                ) : (
                  <tr>
                    <td colSpan={colSpanFull}>
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
