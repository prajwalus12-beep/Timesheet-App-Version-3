import React, { useState, useMemo, useEffect, useCallback, useRef } from "react";
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib";
import { ExternalLink, Search, Filter, Download, X, Info, Save, Link, ChevronDown, ChevronUp, Send, Trash2, CheckCircle, RotateCcw } from "lucide-react";
import "./styles.css";

// ---- Required and Editable Fields Constants ----
const REQUIRED_FIELDS = ["project_code", "project_name", "lead_engineer", "start_date", "end_date", "estimated_days"];
const REQUIRED_LABELS = {
  project_code: "Project Code", project_name: "Project Name",
  lead_engineer: "Lead Engineer", start_date: "Start Date",
  end_date: "Est. Date", estimated_days: "Est. Days"
};
const EDITABLE_FIELDS = [
  "project_code", "project_name", "lead_engineer", "priority", "start_date", "end_date",
  "status", "trello_link", "prototype_link", "slack_link",
  "checkbox_bc", "checkbox_trello", "checkbox_wa", "checkbox_ws", "estimated_days", "notes"
];

function ProjectUpdateComponent(props) {
  const { args } = props;
  const serverProjects = args.projects || [];
  const leadEngineers = args.lead_engineers || [];
  const statusOptions = args.status_options || ["In progress", "Complete", "On hold", "Cancelled"];
  const readOnly = args.read_only || false;
  const isCompact = args.is_compact || false;
  const isAddMode = args.is_add_mode || false;
  const employees = args.employees || [];

  // Helper to normalize and add immutable _uid to each project
  const normalizeProject = useCallback((p, idx = 0) => {
    const isExported = p.is_exported === true || p.is_exported === "true" || p.fmp_added === true || p.fmp_added === "true";
    return {
      ...p,
      _uid: p.id != null ? `proj_id_${p.id}` : (p._uid || `new_uid_${Date.now()}_${idx}_${Math.random().toString(36).substr(2, 7)}`),
      is_exported: isExported,
      project_code: p.project_code != null ? String(p.project_code) : ""
    };
  }, []);

  const [projects, setProjects] = useState(() => {
    return serverProjects.map((p, i) => normalizeProject(p, i)).sort((a, b) => {
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
      const sorted = serverProjects.map((p, i) => normalizeProject(p, i)).sort((a, b) => {
        const codeA = parseInt((a.project_code || "0").replace(/\D/g, ""), 10) || 0;
        const codeB = parseInt((b.project_code || "0").replace(/\D/g, ""), 10) || 0;
        return codeB - codeA;
      });
      // Retain any new, unsaved project rows that were being filled out
      setProjects(prev => {
        const unsaved = prev.filter(p => p._isNew);
        return [...unsaved, ...sorted];
      });
      setSelectedIds(new Set());
    }
  }, [serverProjects, normalizeProject]);

  // ---- Multi-select / delete / export state ----
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Duplicate project code detector
  const isDuplicateCode = useCallback((project) => {
    const code = String(project.project_code || "").trim().toLowerCase();
    if (!code) return false;
    // Check against server-persisted projects
    const inServer = serverProjects.some(sp => {
      if (project.id != null && sp.id === project.id) return false;
      return String(sp.project_code || "").trim().toLowerCase() === code;
    });
    if (inServer) return true;
    // Check against other projects currently in state
    return projects.some(other => {
      if (other._uid === project._uid) return false;
      return String(other.project_code || "").trim().toLowerCase() === code;
    });
  }, [serverProjects, projects]);

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
  const [filterExportStatus, setFilterExportStatus] = useState("non-exported"); // "all" | "exported" | "non-exported"
  const [isFiltersOpen, setIsFiltersOpen] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);
  
  // Field-level errors: { [projectUid]: { [fieldName]: errorMessage } }
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
    serverProjects.forEach(p => {
      if (p.id != null) map.set(p.id, p);
      if (p.project_code) map.set(String(p.project_code), p);
    });
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
      // Export Status Radio Filter
      if (filterExportStatus === "exported" && !p.is_exported) return false;
      if (filterExportStatus === "non-exported" && p.is_exported) return false;

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
      const server = (p.id != null ? serverProjectsMap.get(p.id) : null) || serverProjectsMap.get(String(p.project_code));
      const originalStatus = server ? server.status : p.status;
      if (filterStatus.length > 0 && !filterStatus.includes(originalStatus)) return false;
      const isComplete = originalStatus === "Complete";
      const hasUpdate = updatedFlagKeys.some(k => p[k] === true || p[k] === "true" || p[k] === "True");
      if (filterShowCompleted) { if (!isComplete) return false; }
      else { if (isComplete && !hasUpdate) return false; }
      if (filterUpdatedOnly && !hasUpdate) return false;
      return true;
    });
  }, [projects, serverProjectsMap, filterExportStatus, filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterStatus, filterUpdatedOnly, filterShowCompleted]);

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
    setFilterExportStatus("non-exported");
  };

  const [displayCount, setDisplayCount] = useState(30);
  useEffect(() => {
    setDisplayCount(30);
  }, [filterName, filterCodeMin, filterCodeMax, filterLead, filterPriorityMin, filterPriorityMax, filterStatus, filterUpdatedOnly, filterShowCompleted, filterExportStatus, projects, sortField, sortOrder]);

  const handleScroll = (e) => {
    const { scrollHeight, scrollTop, clientHeight } = e.target;
    if (scrollHeight - scrollTop <= clientHeight + 50 && displayCount < filteredProjects.length) {
      setDisplayCount(prev => prev + 30);
    }
  };

  // Date helper to parse UTC days
  const parseDateToUtcDays = (dateVal) => {
    if (!dateVal) return null;
    if (dateVal instanceof Date) {
      if (isNaN(dateVal.getTime())) return null;
      return Date.UTC(dateVal.getFullYear(), dateVal.getMonth(), dateVal.getDate()) / 86400000;
    }
    const s = String(dateVal).split("T")[0].trim();
    if (!s) return null;

    // Check YYYY-MM-DD
    const isoMatch = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (isoMatch) {
      const y = parseInt(isoMatch[1], 10);
      const m = parseInt(isoMatch[2], 10) - 1;
      const d = parseInt(isoMatch[3], 10);
      return Date.UTC(y, m, d) / 86400000;
    }

    // Check DD-MM-YYYY or DD/MM/YYYY
    const dmyMatch = s.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$/);
    if (dmyMatch) {
      const d = parseInt(dmyMatch[1], 10);
      const m = parseInt(dmyMatch[2], 10) - 1;
      const y = parseInt(dmyMatch[3], 10);
      return Date.UTC(y, m, d) / 86400000;
    }

    const dt = new Date(s);
    if (!isNaN(dt.getTime())) {
      return Date.UTC(dt.getFullYear(), dt.getMonth(), dt.getDate()) / 86400000;
    }
    return null;
  };

  // EST = End Date − Start Date (excluding start date itself)
  const calculateEstDays = (startDate, endDate) => {
    const d1 = parseDateToUtcDays(startDate);
    const d2 = parseDateToUtcDays(endDate);
    if (d1 === null || d2 === null) return null;
    const diff = Math.round(d2 - d1);
    return diff >= 0 ? diff : 0;
  };

  // Safe row-specific update identified by unique immutable _uid
  const handleUpdate = (projectUid, field, value) => {
    setProjects(prev => prev.map(p => {
      if (p._uid !== projectUid) return p;
      const updated = { ...p, [field]: value };
      if (field === "start_date" || field === "end_date") {
        const sDate = field === "start_date" ? value : p.start_date;
        const eDate = field === "end_date" ? value : p.end_date;
        if (sDate && eDate) {
          const est = calculateEstDays(sDate, eDate);
          if (est !== null) {
            updated.estimated_days = est;
          }
        }
      }
      return updated;
    }));

    if (value && String(value).trim()) {
      setFieldErrors(prev => {
        const updated = { ...prev };
        if (updated[projectUid]) {
          const copy = { ...updated[projectUid] };
          delete copy[field];
          if (field === "start_date" || field === "end_date") {
            delete copy.estimated_days;
          }
          updated[projectUid] = copy;
        }
        return updated;
      });
    }
  };


  const isDirty = (project, field) => {
    if (!project) return false;
    if (project._isNew) return !!project[field];
    const server = (project.id != null ? serverProjectsMap.get(project.id) : null) || serverProjectsMap.get(String(project.project_code));
    if (!server) return false;
    const sVal = server[field] === null || server[field] === undefined ? "" : String(server[field]).trim();
    const pVal = project[field] === null || project[field] === undefined ? "" : String(project[field]).trim();
    return sVal !== pVal;
  };

  const isDbUpdated = (project, field) => {
    const flag = project[field + "_updated"];
    return flag === true || flag === "true" || flag === "True";
  };

  const isProjectDirty = useCallback((p) => {
    if (!p) return false;
    if (p._isNew) {
      return EDITABLE_FIELDS.some(f => p[f] !== undefined && p[f] !== null && String(p[f]).trim() !== "");
    }
    const server = (p.id != null ? serverProjectsMap.get(p.id) : null) || serverProjectsMap.get(String(p.project_code));
    if (!server) return false;
    return EDITABLE_FIELDS.some(f => {
      const sVal = server[f] === null || server[f] === undefined ? "" : String(server[f]).trim();
      const pVal = p[f] === null || p[f] === undefined ? "" : String(p[f]).trim();
      return sVal !== pVal;
    });
  }, [serverProjectsMap]);

  const editedCount = useMemo(() => {
    return projects.filter(p => isProjectDirty(p)).length;
  }, [projects, isProjectDirty]);

  const hasUnfilledRequired = useMemo(() => {
    const dirtyProjects = projects.filter(p => isProjectDirty(p));
    if (dirtyProjects.length === 0) return false;
    return dirtyProjects.some(p => {
      return REQUIRED_FIELDS.some(f => {
        const val = p[f];
        return val === undefined || val === null || String(val).trim() === "";
      });
    });
  }, [projects, isProjectDirty]);

  // ---- Selection helpers ----
  const toggleSelectProject = (projectIdOrUid) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(projectIdOrUid)) next.delete(projectIdOrUid); else next.add(projectIdOrUid);
      return next;
    });
  };

  const visibleSelectableIds = sortedProjects.slice(0, displayCount).map(p => p.id != null ? p.id : p._uid);
  const allVisibleSelected = visibleSelectableIds.length > 0 && visibleSelectableIds.every(id => selectedIds.has(id));
  const someVisibleSelected = visibleSelectableIds.some(id => selectedIds.has(id));

  const toggleSelectAll = () => {
    if (allVisibleSelected) {
      setSelectedIds(prev => { const next = new Set(prev); visibleSelectableIds.forEach(id => next.delete(id)); return next; });
    } else {
      setSelectedIds(prev => { const next = new Set(prev); visibleSelectableIds.forEach(id => next.add(id)); return next; });
    }
  };

  // ---- Mark as Exported handler ----
  const handleMarkAsExported = () => {
    if (selectedIds.size === 0) {
      alert("Please select one or more project records from the list to mark as exported.");
      return;
    }
    // Only persistable records with DB ids can be updated on server
    const savedRecordIds = [...selectedIds]
      .map(id => projects.find(p => p.id === id || p._uid === id))
      .filter(p => p && !p._isNew && p.id != null)
      .map(p => p.id);

    if (savedRecordIds.length === 0) {
      alert("Selected new project(s) must be saved first before marking them as exported.");
      return;
    }

    Streamlit.setComponentValue({
      action: "mark_as_exported",
      record_ids: savedRecordIds
    });
  };

  // ---- Mark as Non-Exported handler ----
  const handleMarkAsNonExported = () => {
    if (selectedIds.size === 0) {
      alert("Please select one or more project records from the list to mark as non-exported.");
      return;
    }
    const savedRecordIds = [...selectedIds]
      .map(id => projects.find(p => p.id === id || p._uid === id))
      .filter(p => p && !p._isNew && p.id != null)
      .map(p => p.id);

    if (savedRecordIds.length === 0) {
      alert("Selected new project(s) must be saved first before marking them as non-exported.");
      return;
    }

    Streamlit.setComponentValue({
      action: "mark_as_non_exported",
      record_ids: savedRecordIds
    });
  };

  // ---- Delete helpers ----
  const handleDeleteSingle = (project) => { setDeleteTarget(project); setShowDeleteConfirm(true); };
  const handleDeleteSelected = () => { if (selectedIds.size === 0) return; setDeleteTarget(null); setShowDeleteConfirm(true); };

  const confirmDelete = () => {
    let recordIds = [];
    if (deleteTarget) {
      if (deleteTarget._isNew) {
        setProjects(prev => prev.filter(p => p._uid !== deleteTarget._uid));
        setShowDeleteConfirm(false); setDeleteTarget(null); return;
      }
      recordIds = [deleteTarget.id];
    } else {
      const newRowUids = [...selectedIds]
        .map(id => projects.find(p => p.id === id || p._uid === id))
        .filter(p => p && p._isNew).map(p => p._uid);
      if (newRowUids.length > 0)
        setProjects(prev => prev.filter(p => !newRowUids.includes(p._uid)));
      recordIds = [...selectedIds]
        .map(id => projects.find(p => p.id === id || p._uid === id))
        .filter(p => p && !p._isNew && p.id != null)
        .map(p => p.id);
    }
    setShowDeleteConfirm(false); setDeleteTarget(null); setSelectedIds(new Set());
    if (recordIds.length > 0) Streamlit.setComponentValue({ action: "delete_projects", record_ids: recordIds });
  };

  // ---- Required field validation ----
  const getFieldError = (projectUid, field) => fieldErrors[projectUid]?.[field] || null;

  // ---- Save ----
  const handleSave = useCallback(() => {
    const edits = {};
    const vErrors = [];
    const newFieldErrors = {};

    projects.forEach(p => {
      let server;
      if (!p._isNew) {
        server = (p.id != null ? serverProjectsMap.get(p.id) : null) || serverProjectsMap.get(String(p.project_code));
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
        changes["id"] = p.id;
        changes["project_code"] = p.project_code;
        editableFields.forEach(f => { if (String(server[f] ?? "") !== String(p[f] ?? "")) changes[f] = p[f]; });
      }

      const hasFieldChanges = p._isNew ? Object.keys(changes).length > 1 : Object.keys(changes).some(k => k !== "id" && k !== "project_code");

      if (hasFieldChanges || p._isNew) {
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

          // Duplicate project code check
          const code = String(p.project_code || "").trim();
          if (code && isDuplicateCode(p)) {
            errs.push(`Project Code "${code}" already exists — please use a unique code`);
            reqErrs["project_code"] = `Code "${code}" already exists`;
          }
          if (Object.keys(reqErrs).length > 0) newFieldErrors[p._uid] = reqErrs;
        }

        if (p._isNew && (!p.project_code || !String(p.project_code).trim())) errs.push("Project Code is required for new projects");
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
        if (uniqueErrs.length > 0) vErrors.push({ projectCode: p.project_code || "New Project", name: p.project_name, errors: uniqueErrs });
        edits[p.project_code || p._uid] = changes;
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
  }, [projects, serverProjectsMap, isDuplicateCode]);

  const handleExportClick = () => {
    const displayedProjectCodes = filteredProjects.map(p => String(p.project_code));
    const displayedIds = filteredProjects.filter(p => p.id != null).map(p => p.id);
    Streamlit.setComponentValue({
      action: "open_export_modal",
      payload: {
        displayedProjectCodes,
        displayedIds
      }
    });
  };
  const handleOpenReminderModal = () => {
    const displayedProjectCodes = filteredProjects.map(p => String(p.project_code));
    Streamlit.setComponentValue({ action: "open_reminder_modal", payload: { displayedProjectCodes } });
  };

  // ---- Cell class helpers ----
  const isFieldEmpty = v => !v || v.toString().trim() === "";

  const cellInputClass = (project, field, value, extra = "") => {
    let cls = "pu-cell-input";
    if (extra) cls += " " + extra;
    if (isDirty(project, field)) cls += " dirty";
    if (!project._isNew && !isDirty(project, field) && isDbUpdated(project, field)) cls += " db-updated";
    if (isFieldEmpty(value)) cls += " pu-highlight-empty";
    if (getFieldError(project._uid, field)) cls += " pu-field-error";
    return cls;
  };

  const cellSelectClass = (project, field, value, extra = "") => {
    let cls = "pu-cell-select";
    if (extra) cls += " " + extra;
    if (isDirty(project, field)) cls += " dirty";
    if (!project._isNew && !isDirty(project, field) && isDbUpdated(project, field)) cls += " db-updated";
    if (isFieldEmpty(value)) cls += " pu-highlight-empty";
    if (getFieldError(project._uid, field)) cls += " pu-field-error";
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
    const name = deleteTarget ? (deleteTarget.project_name || deleteTarget.project_code || "Unnamed Project") : null;
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
              Showing {filteredProjects.length} records of {projects.length} total.
            </span>
            {!readOnly && !isCompact && editedCount > 0 && (
              <button className="pu-save-btn" onClick={handleSave}><Save size={16} /> Save Changes ({editedCount})</button>
            )}
            {!readOnly && !isCompact && isAddMode && (
              <button className="pu-save-btn" onClick={() => {
                const newProj = {
                  _uid: `new_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`,
                  project_code: "",
                  project_name: "",
                  status: "Not started",
                  priority: "2",
                  is_exported: false,
                  _isNew: true
                };
                setProjects(prev => [newProj, ...prev]);
              }}>&#10133; Add Project</button>
            )}
            {/* Mark as Exported Button - Admin only */}
            {!readOnly && !isCompact && isAdmin && (
              <button
                className={`pu-mark-exported-btn ${selectedIds.size === 0 ? "disabled" : ""}`}
                onClick={handleMarkAsExported}
                title="Mark selected project records as Exported"
              >
                <CheckCircle size={16} /> Mark as Exported {selectedIds.size > 0 ? `(${selectedIds.size})` : ""}
              </button>
            )}
            {/* Mark as Non-Exported Button - Admin only */}
            {!readOnly && !isCompact && isAdmin && (
              <button
                className={`pu-mark-non-exported-btn ${selectedIds.size === 0 ? "disabled" : ""}`}
                onClick={handleMarkAsNonExported}
                title="Mark selected project records as Non-Exported"
              >
                <RotateCcw size={16} /> Mark as Non - Exported {selectedIds.size > 0 ? `(${selectedIds.size})` : ""}
              </button>
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

        {/* ── Unsaved Changes Warning Banner (only appears if required fields are not filled) ── */}
        {!readOnly && !isCompact && editedCount > 0 && hasUnfilledRequired && (
          <div className="pu-unsaved-banner">
            <span>⚠ Please fill all required fields before saving ({editedCount} unsaved project(s)).</span>
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

        {/* ── Prominent Radio Buttons Filter & Sort Bar ── */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: "12px", marginBottom: "12px", padding: "10px 15px", background: "#f8fafc", borderRadius: "8px", border: "1px solid #e2e8f0" }}>
          
          {/* Quick Radio Filter for Export Status */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Export Status:
            </span>
            <div className="pu-radio-group" style={{ padding: 0 }}>
              <label className={`pu-radio-item ${filterExportStatus === "all" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="quickExportFilter"
                  value="all"
                  checked={filterExportStatus === "all"}
                  onChange={() => setFilterExportStatus("all")}
                />
                <span>All Records</span>
              </label>
              <label className={`pu-radio-item ${filterExportStatus === "exported" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="quickExportFilter"
                  value="exported"
                  checked={filterExportStatus === "exported"}
                  onChange={() => setFilterExportStatus("exported")}
                />
                <span>Exported Records</span>
              </label>
              <label className={`pu-radio-item ${filterExportStatus === "non-exported" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="quickExportFilter"
                  value="non-exported"
                  checked={filterExportStatus === "non-exported"}
                  onChange={() => setFilterExportStatus("non-exported")}
                />
                <span>Non-Exported Records</span>
              </label>
            </div>
          </div>

          {/* Sort Controls */}
          <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
            <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.05em" }}>Sort By:</span>
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
                    const selectKey = project.id != null ? project.id : project._uid;
                    const isSelected = selectedIds.has(selectKey);
                    const projFieldErrs = fieldErrors[project._uid] || {};
                    const isDupCode = project._isNew && isDuplicateCode(project);

                    return (
                      <React.Fragment key={project._uid}>
                        <tr className={`pu-row-primary${isSelected ? " pu-row-selected" : ""}`}>

                          {/* Checkbox */}
                          {!readOnly && !isCompact && isAddMode && (
                            <td style={{ textAlign: "center", padding: "0.375rem 0.25rem", verticalAlign: "middle" }}>
                              <input type="checkbox" checked={isSelected}
                                onChange={() => toggleSelectProject(selectKey)}
                                style={{ cursor: "pointer", width: "15px", height: "15px" }} />
                            </td>
                          )}

                          {/* Row number */}
                          <td className="td-hash">{index + 1}</td>

                          {/* Project Code */}
                          <td className="td-code">
                            {project._isNew ? (
                              <div>
                                <input
                                  type="text"
                                  value={project.project_code || ""}
                                  onChange={e => handleUpdate(project._uid, "project_code", e.target.value)}
                                  className={`pu-cell-input${projFieldErrs.project_code || isDupCode ? " pu-field-error" : ""}`}
                                  placeholder="Job No *"
                                  style={{ width: "85px", padding: "4px" }}
                                />
                                {isDupCode && (
                                  <div className="pu-field-error-msg" style={{ color: "#dc2626", fontSize: "0.72rem", marginTop: "3px", fontWeight: 600 }}>
                                    ⚠ Project Code "{project.project_code}" already exists
                                  </div>
                                )}
                                {projFieldErrs.project_code && !isDupCode && (
                                  <div className="pu-field-error-msg">{projFieldErrs.project_code}</div>
                                )}
                              </div>
                            ) : (
                              <div>
                                <b>{project.project_code || ""}</b>
                              </div>
                            )}
                            {/* Visual Export Status Badge */}
                            <div style={{ marginTop: "4px" }}>
                              {project.is_exported ? (
                                <span className="pu-badge-exported" title="Exported record">✓ Exported</span>
                              ) : (
                                <span className="pu-badge-not-exported" title="Not yet exported">Non-Exported</span>
                              )}
                            </div>
                          </td>

                          {/* Project Name / URLs */}
                          <td className="td-project-name">
                            <div>
                              <input type="text" value={project.project_name || ""}
                                onChange={e => handleUpdate(project._uid, "project_name", e.target.value)}
                                className={cellInputClass(project, "project_name", project.project_name, "name-field")}
                                disabled={readOnly || isCompact}
                                title={project.project_name || "Project Name — required"}
                                placeholder="Project Name *" />
                              {projFieldErrs.project_name && <div className="pu-field-error-msg">{projFieldErrs.project_name}</div>}
                            </div>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                              <div className="pu-url-input-wrapper">
                                <input type="text" value={project.trello_link || ""}
                                  onChange={e => handleUpdate(project._uid, "trello_link", e.target.value)}
                                  className={cellInputClass(project, "trello_link", project.trello_link, "url-field-small")}
                                  disabled={readOnly || isCompact} placeholder="Trello URL" />
                                {project.trello_link && project.trello_link.startsWith("http") && (
                                  <a href={project.trello_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Trello"><Link size={12} /></a>
                                )}
                              </div>
                              {!isCompact && (
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.15rem" }}>
                                  <div className="pu-url-input-wrapper">
                                    <input type="text" value={project.prototype_link || ""}
                                      onChange={e => handleUpdate(project._uid, "prototype_link", e.target.value)}
                                      className={cellInputClass(project, "prototype_link", project.prototype_link, "url-field-small")}
                                      disabled={readOnly} placeholder="Prototype URL" />
                                    {project.prototype_link && project.prototype_link.startsWith("http") && (
                                      <a href={project.prototype_link} target="_blank" rel="noopener noreferrer" className="pu-input-url-btn" title="Open Prototype"><Link size={12} /></a>
                                    )}
                                  </div>
                                  <div className="pu-url-input-wrapper">
                                    <input type="text" value={project.slack_link || ""}
                                      onChange={e => handleUpdate(project._uid, "slack_link", e.target.value)}
                                      className={cellInputClass(project, "slack_link", project.slack_link, "url-field-small")}
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
                                onChange={e => handleUpdate(project._uid, "lead_engineer", e.target.value)}
                                className={cellSelectClass(project, "lead_engineer", project.lead_engineer, "lead-select-main")}
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
                                    onChange={e => handleUpdate(project._uid, "start_date", e.target.value)}
                                    className={cellInputClass(project, "start_date", project.start_date, "date-field-small")}
                                    disabled={readOnly} title="Start Date *" />
                                  {projFieldErrs.start_date && <div className="pu-field-error-msg">{projFieldErrs.start_date}</div>}
                                </div>
                                <div className="pu-date-input-wrap">
                                  <input type="date" value={project.end_date || ""}
                                    onChange={e => handleUpdate(project._uid, "end_date", e.target.value)}
                                    className={cellInputClass(project, "end_date", project.end_date, "date-field-small")}
                                    disabled={readOnly} title="Est. Date (End Date) *" />
                                  {projFieldErrs.end_date && <div className="pu-field-error-msg">{projFieldErrs.end_date}</div>}
                                </div>
                              </div>
                            )}
                          </td>

                          {/* Status / Priority / Notes */}
                          <td className="td-status-group">
                            <select value={project.status || "Not started"}
                              onChange={e => handleUpdate(project._uid, "status", e.target.value)}
                              className={cellSelectClass(project, "status", project.status || "Not started", "status-select-main")}
                              disabled={readOnly || isCompact}>
                              {statusOptions.map(s => <option key={s} value={s}>{s}</option>)}
                            </select>
                            <div style={{ display: "flex", flexDirection: "column", gap: "0.15rem", marginTop: "0.15rem" }}>
                              <input type="text" value={project.priority || ""}
                                onChange={e => handleUpdate(project._uid, "priority", e.target.value.toUpperCase())}
                                className={cellInputClass(project, "priority", project.priority, "priority-field-small")}
                                disabled={readOnly || isCompact} placeholder="Priority" />
                              {!isCompact && (
                                <textarea value={project.notes || ""}
                                  onChange={e => handleUpdate(project._uid, "notes", e.target.value || null)}
                                  className={`pu-notes-textarea${isDirty(project, "notes") ? " dirty" : ""}${!isDirty(project, "notes") && isDbUpdated(project, "notes") ? " db-updated" : ""}`}
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
                                  const dirty = isDirty(project, item.field);
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
                                        onChange={e => handleUpdate(project._uid, item.field, e.target.checked ? null : 1)}
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
                                  onChange={e => handleUpdate(project._uid, "estimated_days", e.target.value ? parseFloat(e.target.value) : null)}
                                  className={cellInputClass(project, "estimated_days", project.estimated_days, "estimate-input")}
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
