import React from "react";
import { Info, AlertTriangle, AlertCircle, Shield, Sparkles, Check, ChevronRight } from "lucide-react";

/**
 * Lightweight, robust Markdown to React Parser
 * Supports:
 * - H1, H2, H3, H4 with auto ID for scrolling
 * - Tables with proper headers & cells
 * - GitHub Alert blockquotes (> [!NOTE], > [!TIP], > [!IMPORTANT], > [!WARNING], > [!CAUTION])
 * - Lists (bulleted, numbered)
 * - Code blocks and inline code
 * - Links and bold/italic formatting
 * - Horizontal rules
 */

export function parseMarkdown(markdownText, onLinkClick) {
  if (!markdownText) return null;

  const lines = markdownText.split("\n");
  const elements = [];
  let i = 0;

  // Inline formatting helper
  const renderInline = (text) => {
    if (!text) return "";
    
    // We split by tokens for bold, italic, code, links
    // First escape links to avoid collision
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = linkRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: "text", val: text.substring(lastIndex, match.index) });
      }
      parts.push({ type: "link", label: match[1], url: match[2] });
      lastIndex = match.index + match[0].length;
    }
    if (lastIndex < text.length) {
      parts.push({ type: "text", val: text.substring(lastIndex) });
    }

    // Now format inner parts (code, bold, italic)
    return parts.map((part, pIdx) => {
      if (part.type === "link") {
        return (
          <a
            key={pIdx}
            href={part.url}
            className="md-link"
            onClick={(e) => {
              if (onLinkClick && (part.url.endsWith(".md") || part.url.includes(".md#"))) {
                e.preventDefault();
                onLinkClick(part.url);
              }
            }}
            target={part.url.startsWith("http") ? "_blank" : "_self"}
            rel="noopener noreferrer"
          >
            {part.label}
          </a>
        );
      }

      // Format text part: code `...`, bold **...**, italic *...*
      const segments = [];
      const codeRegex = /`([^`]+)`/g;
      let cLast = 0;
      let cMatch;

      while ((cMatch = codeRegex.exec(part.val)) !== null) {
        if (cMatch.index > cLast) {
          segments.push(formatBoldItalic(part.val.substring(cLast, cMatch.index), `txt-${pIdx}-${cLast}`));
        }
        segments.push(
          <code key={`code-${pIdx}-${cMatch.index}`} className="md-inline-code">
            {cMatch[1]}
          </code>
        );
        cLast = cMatch.index + cMatch[0].length;
      }
      if (cLast < part.val.length) {
        segments.push(formatBoldItalic(part.val.substring(cLast), `txt-${pIdx}-${cLast}`));
      }

      return <span key={pIdx}>{segments}</span>;
    });
  };

  const formatBoldItalic = (text, keyPrefix) => {
    // Process bold **text**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((seg, idx) => {
      if (seg.startsWith("**") && seg.endsWith("**")) {
        const inner = seg.slice(2, -2);
        return <strong key={`${keyPrefix}-b-${idx}`} className="md-strong">{inner}</strong>;
      }
      // Process italic *text*
      const subParts = seg.split(/(\*[^*]+\*)/g);
      return subParts.map((sub, sIdx) => {
        if (sub.startsWith("*") && sub.endsWith("*")) {
          return <em key={`${keyPrefix}-i-${idx}-${sIdx}`} className="md-em">{sub.slice(1, -1)}</em>;
        }
        return sub;
      });
    });
  };

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // Empty line
    if (!trimmed) {
      i++;
      continue;
    }

    // Code block
    if (trimmed.startsWith("```")) {
      const lang = trimmed.slice(3).trim();
      const codeLines = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(
        <div key={`code-block-${i}`} className="md-code-block-wrapper">
          {lang && <div className="md-code-header">{lang}</div>}
          <pre className="md-code-block">
            <code>{codeLines.join("\n")}</code>
          </pre>
        </div>
      );
      continue;
    }

    // GitHub Alert or Blockquote (> [!NOTE], etc.)
    if (trimmed.startsWith(">")) {
      const quoteLines = [];
      let alertType = null;

      while (i < lines.length && lines[i].trim().startsWith(">")) {
        let qLine = lines[i].trim().replace(/^>\s?/, "");
        const alertMatch = qLine.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i);
        if (alertMatch) {
          alertType = alertMatch[1].toUpperCase();
          qLine = qLine.replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]/i, "").trim();
        }
        if (qLine) {
          quoteLines.push(qLine);
        }
        i++;
      }

      const alertConfig = {
        NOTE: { icon: Info, title: "Note", className: "md-alert-note" },
        TIP: { icon: Sparkles, title: "Tip", className: "md-alert-tip" },
        IMPORTANT: { icon: AlertCircle, title: "Important", className: "md-alert-important" },
        WARNING: { icon: AlertTriangle, title: "Warning", className: "md-alert-warning" },
        CAUTION: { icon: Shield, title: "Caution", className: "md-alert-caution" },
      };

      if (alertType && alertConfig[alertType]) {
        const conf = alertConfig[alertType];
        const IconComponent = conf.icon;
        elements.push(
          <div key={`alert-${i}`} className={`md-alert ${conf.className}`}>
            <div className="md-alert-title">
              <IconComponent size={18} className="md-alert-icon" />
              <span>{conf.title}</span>
            </div>
            <div className="md-alert-body">
              {quoteLines.map((ql, qIdx) => (
                <p key={qIdx}>{renderInline(ql)}</p>
              ))}
            </div>
          </div>
        );
      } else {
        // Standard blockquote
        elements.push(
          <blockquote key={`quote-${i}`} className="md-blockquote">
            {quoteLines.map((ql, qIdx) => (
              <p key={qIdx}>{renderInline(ql)}</p>
            ))}
          </blockquote>
        );
      }
      continue;
    }

    // Horizontal Rule
    if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
      elements.push(<hr key={`hr-${i}`} className="md-hr" />);
      i++;
      continue;
    }

    // Headings
    if (trimmed.startsWith("#")) {
      const levelMatch = trimmed.match(/^(#{1,6})\s+(.*)$/);
      if (levelMatch) {
        const level = levelMatch[1].length;
        const headingText = levelMatch[2].trim();
        const anchorId = headingText
          .toLowerCase()
          .replace(/[^\w\s-]/g, "")
          .replace(/\s+/g, "-");

        const HeadingTag = `h${level}`;
        elements.push(
          <HeadingTag key={`h-${i}`} id={anchorId} className={`md-heading md-h${level}`}>
            {renderInline(headingText)}
          </HeadingTag>
        );
        i++;
        continue;
      }
    }

    // Markdown Table
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }

      if (tableLines.length >= 2) {
        const parseRow = (rowStr) =>
          rowStr
            .split("|")
            .slice(1, -1)
            .map((c) => c.trim());

        const headers = parseRow(tableLines[0]);
        // line 1 is separator |---|---|
        const dataRows = tableLines.slice(2).map(parseRow);

        elements.push(
          <div key={`table-${i}`} className="md-table-container">
            <table className="md-table">
              <thead>
                <tr>
                  {headers.map((h, hIdx) => (
                    <th key={hIdx}>{renderInline(h)}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dataRows.map((row, rIdx) => (
                  <tr key={rIdx}>
                    {row.map((cell, cIdx) => (
                      <td key={cIdx}>{renderInline(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        );
        continue;
      }
    }

    // Bullet List (- or *)
    if (/^[-*]\s+/.test(trimmed)) {
      const listItems = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i].trim())) {
        const itemText = lines[i].trim().replace(/^[-*]\s+/, "");
        // Check for checklist [ ] or [x]
        const checkMatch = itemText.match(/^\[([ xX])\]\s+(.*)$/);
        if (checkMatch) {
          const isChecked = checkMatch[1].toLowerCase() === "x";
          listItems.push(
            <li key={`li-${i}`} className="md-checklist-item">
              <input type="checkbox" checked={isChecked} readOnly className="md-checkbox" />
              <span>{renderInline(checkMatch[2])}</span>
            </li>
          );
        } else {
          listItems.push(<li key={`li-${i}`}>{renderInline(itemText)}</li>);
        }
        i++;
      }
      elements.push(
        <ul key={`ul-${i}`} className="md-ul">
          {listItems}
        </ul>
      );
      continue;
    }

    // Numbered List (1. ...)
    if (/^\d+\.\s+/.test(trimmed)) {
      const listItems = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i].trim())) {
        const itemText = lines[i].trim().replace(/^\d+\.\s+/, "");
        listItems.push(<li key={`oli-${i}`}>{renderInline(itemText)}</li>);
        i++;
      }
      elements.push(
        <ol key={`ol-${i}`} className="md-ol">
          {listItems}
        </ol>
      );
      continue;
    }

    // Standard paragraph
    elements.push(
      <p key={`p-${i}`} className="md-p">
        {renderInline(trimmed)}
      </p>
    );
    i++;
  }

  return elements;
}
