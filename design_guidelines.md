{
  "product": {
    "name": "Local App Creator",
    "positioning": "Local-first AI software engineer + project architect (premium software factory cockpit).",
    "design_personality": {
      "keywords": [
        "mission-control",
        "factory-cockpit",
        "technical",
        "premium",
        "honesty-first",
        "dense-but-legible",
        "keyboard-friendly",
        "no-fluff"
      ],
      "anti_keywords": [
        "playful",
        "no-code-template",
        "marketing-landing-page",
        "glass-everywhere",
        "neon-everywhere"
      ]
    }
  },

  "inspiration_fusion": {
    "layout_principles": [
      "DevTools-like shell: left nav + top breadcrumb + main workspace + right event drawer",
      "Mission control density: compact tables, logs, and status chips with strict hierarchy",
      "Linear/Vercel clarity: restrained accent usage, crisp borders, strong typography"
    ],
    "references": {
      "search_terms_used": [
        "mission control dashboard UI devtool cockpit",
        "developer tool design system dark mode graphite electric accent status badges"
      ],
      "notes": [
        "Use graphite neutrals for 80–90% of UI; reserve electric accent for focus/active/links.",
        "Status badges must be unmistakable and consistent across all pages.",
        "Event ledger should feel like a console: monospaced, timestamped, filterable." 
      ]
    }
  },

  "typography": {
    "font_pairing": {
      "sans_ui": {
        "name": "IBM Plex Sans",
        "fallback": "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial",
        "usage": "Body copy, headings, navigation, tables"
      },
      "mono_accent": {
        "name": "IBM Plex Mono",
        "fallback": "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace",
        "usage": "IDs, file paths, event payload previews, code-ish strings, status reasons"
      }
    },
    "google_fonts_import": {
      "instructions": "Add to /app/frontend/src/index.css (top) or in index.html <link>. Prefer CSS import for simplicity.",
      "css": "@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');"
    },
    "scale_tailwind": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg font-medium text-muted-foreground",
      "section_title": "text-lg font-semibold",
      "body": "text-sm md:text-base leading-6",
      "small": "text-xs text-muted-foreground",
      "mono_small": "font-mono text-xs tracking-tight"
    },
    "weights": {
      "regular": 400,
      "medium": 500,
      "semibold": 600
    }
  },

  "design_tokens": {
    "notes": [
      "Dark-first. No transparent backgrounds. Surfaces are solid with subtle elevation.",
      "Avoid saturated gradients; use solid graphite surfaces + tiny accent glows.",
      "Tokens should be implemented by overriding shadcn CSS variables in index.css under .dark."
    ],
    "css_custom_properties": {
      "recommended": {
        "radius": {
          "--radius": "0.75rem",
          "--radius-sm": "0.5rem",
          "--radius-lg": "1rem"
        },
        "shadows": {
          "--shadow-1": "0 1px 0 rgba(255,255,255,0.04), 0 10px 30px rgba(0,0,0,0.35)",
          "--shadow-2": "0 1px 0 rgba(255,255,255,0.06), 0 18px 50px rgba(0,0,0,0.45)"
        },
        "focus": {
          "--focus-ring": "0 0 0 3px rgba(34,211,238,0.25)",
          "--focus-ring-strong": "0 0 0 3px rgba(96,165,250,0.28)"
        }
      },
      "shadcn_dark_override_hsl": {
        "implementation_target": "/app/frontend/src/index.css",
        "vars": {
          "--background": "222 18% 7%",
          "--foreground": "210 20% 96%",
          "--card": "222 18% 9%",
          "--card-foreground": "210 20% 96%",
          "--popover": "222 18% 9%",
          "--popover-foreground": "210 20% 96%",
          "--primary": "196 100% 50%",
          "--primary-foreground": "222 18% 7%",
          "--secondary": "222 14% 14%",
          "--secondary-foreground": "210 20% 96%",
          "--muted": "222 14% 14%",
          "--muted-foreground": "215 14% 70%",
          "--accent": "222 14% 14%",
          "--accent-foreground": "210 20% 96%",
          "--destructive": "0 84% 60%",
          "--destructive-foreground": "210 20% 96%",
          "--border": "222 12% 18%",
          "--input": "222 12% 18%",
          "--ring": "196 100% 50%",
          "--chart-1": "196 100% 50%",
          "--chart-2": "160 84% 45%",
          "--chart-3": "38 92% 55%",
          "--chart-4": "262 83% 65%",
          "--chart-5": "0 84% 60%"
        },
        "semantic_extensions_add": {
          "--surface-2": "222 14% 12%",
          "--surface-3": "222 12% 16%",
          "--code-bg": "222 18% 6%",
          "--code-border": "222 12% 18%",
          "--link": "210 100% 70%",
          "--info": "210 100% 65%",
          "--success": "160 84% 45%",
          "--warning": "38 92% 55%",
          "--blocked": "270 90% 62%",
          "--placeholder": "215 10% 55%"
        }
      },
      "palette_hex_reference": {
        "graphite_bg": "#0B0F14",
        "graphite_panel": "#111823",
        "graphite_panel_2": "#151F2D",
        "border": "#223044",
        "text": "#E7EEF8",
        "muted_text": "#A9B6C8",
        "electric_cyan": "#22D3EE",
        "electric_blue": "#60A5FA",
        "success_green": "#34D399",
        "warning_amber": "#FBBF24",
        "danger_red": "#FB7185",
        "blocked_purple": "#A78BFA",
        "placeholder_gray": "#64748B"
      }
    }
  },

  "layout_and_grid": {
    "app_shell": {
      "structure": "Left collapsible sidebar + top bar (breadcrumb + state pill + health) + main content + right event ledger drawer.",
      "container": "Use full-width; constrain inner reading areas to max-w-[1200px] only where appropriate (BRD text), but keep cockpit pages fluid.",
      "grid": {
        "desktop": "12-col grid, gap-6; primary panels span 7–9 cols, secondary panels 3–5 cols.",
        "tablet": "6-col grid, gap-5",
        "mobile": "single column, gap-4; sidebar becomes Sheet/Drawer"
      },
      "spacing": {
        "page_padding": "px-4 sm:px-6 lg:px-8 py-6",
        "panel_padding": "p-4 sm:p-5",
        "dense_rows": "py-2.5"
      }
    },
    "top_bar": {
      "left": "Breadcrumb + project name (truncate) + subtle mono project id",
      "center_optional": "Phase stepper (compact) on cockpit page only",
      "right": "System health pill + Event Ledger button + theme toggle (future)"
    }
  },

  "components": {
    "component_path": {
      "shadcn_primary": "/app/frontend/src/components/ui",
      "use_components": [
        "button.jsx",
        "badge.jsx",
        "card.jsx",
        "tabs.jsx",
        "table.jsx",
        "scroll-area.jsx",
        "separator.jsx",
        "sheet.jsx",
        "drawer.jsx",
        "resizable.jsx",
        "command.jsx",
        "breadcrumb.jsx",
        "tooltip.jsx",
        "progress.jsx",
        "skeleton.jsx",
        "collapsible.jsx",
        "accordion.jsx",
        "sonner.jsx"
      ]
    },

    "buttons": {
      "style": "Professional / Corporate with slight premium elevation",
      "variants": {
        "primary": {
          "use": "Primary actions: New Project, Generate, Run Build, Export ZIP",
          "tailwind": "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-0",
          "micro_interaction": "hover: subtle glow shadow; press: scale-[0.98]"
        },
        "secondary": {
          "use": "Safe secondary actions: View reasoning, Open drawer",
          "tailwind": "bg-secondary text-secondary-foreground hover:bg-secondary/80 border border-border",
          "micro_interaction": "hover: border brightens; press: scale-[0.99]"
        },
        "ghost": {
          "use": "Toolbar icon buttons, table row actions",
          "tailwind": "hover:bg-accent hover:text-accent-foreground",
          "micro_interaction": "hover: background only (no transform)"
        },
        "destructive": {
          "use": "Reset project, delete run",
          "tailwind": "bg-destructive text-destructive-foreground hover:bg-destructive/90"
        }
      },
      "sizes": {
        "sm": "h-8 px-3 text-xs",
        "md": "h-9 px-4 text-sm",
        "lg": "h-10 px-5 text-sm"
      },
      "data_testid_examples": [
        "data-testid=\"new-project-cta-button\"",
        "data-testid=\"export-zip-button\"",
        "data-testid=\"run-build-button\""
      ]
    },

    "status_badges": {
      "principles": [
        "Always show a badge for any claim: Real / Partial / Unsupported / Blocked / Placeholder.",
        "Badges must be readable at 12–13px and distinguishable by both color and icon/shape.",
        "Use subtle tinted backgrounds (not full neon) + 1px border; no gradients."
      ],
      "mapping": {
        "real": {
          "label": "Real",
          "color": "success",
          "tailwind": "bg-[hsl(var(--success)/0.14)] text-[hsl(var(--success))] border border-[hsl(var(--success)/0.35)]",
          "icon": "CheckCircle"
        },
        "partial": {
          "label": "Partial",
          "color": "warning",
          "tailwind": "bg-[hsl(var(--warning)/0.14)] text-[hsl(var(--warning))] border border-[hsl(var(--warning)/0.35)]",
          "icon": "AlertTriangle"
        },
        "unsupported": {
          "label": "Unsupported",
          "color": "destructive",
          "tailwind": "bg-[hsl(var(--destructive)/0.14)] text-[hsl(var(--destructive))] border border-[hsl(var(--destructive)/0.35)]",
          "icon": "XCircle"
        },
        "blocked": {
          "label": "Blocked",
          "color": "blocked",
          "tailwind": "bg-[hsl(var(--blocked)/0.14)] text-[hsl(var(--blocked))] border border-[hsl(var(--blocked)/0.35)]",
          "icon": "Ban"
        },
        "placeholder": {
          "label": "Placeholder",
          "color": "muted",
          "tailwind": "bg-transparent text-muted-foreground border border-dashed border-border",
          "icon": "CircleDashed"
        }
      },
      "badge_shape": "rounded-full px-2.5 py-1 text-xs font-medium inline-flex items-center gap-1",
      "data_testid": "data-testid=\"status-badge\" (add suffix per row: status-badge-real, etc.)"
    },

    "project_state_pill": {
      "states": [
        "Idea",
        "BRD",
        "Architecture",
        "Plan",
        "Generating",
        "Building",
        "Repair",
        "Acceptance",
        "Export"
      ],
      "visual": {
        "base": "inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs border",
        "dot": "h-2 w-2 rounded-full",
        "typography": "font-medium",
        "mapping": {
          "Idea": "bg-muted text-foreground border-border",
          "BRD": "bg-[hsl(var(--info)/0.12)] text-[hsl(var(--info))] border-[hsl(var(--info)/0.35)]",
          "Architecture": "bg-[hsl(var(--primary)/0.12)] text-[hsl(var(--primary))] border-[hsl(var(--primary)/0.35)]",
          "Plan": "bg-[hsl(var(--primary)/0.10)] text-foreground border-border",
          "Generating": "bg-[hsl(var(--primary)/0.14)] text-[hsl(var(--primary))] border-[hsl(var(--primary)/0.35)]",
          "Building": "bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.35)]",
          "Repair": "bg-[hsl(var(--blocked)/0.12)] text-[hsl(var(--blocked))] border-[hsl(var(--blocked)/0.35)]",
          "Acceptance": "bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]",
          "Export": "bg-secondary text-secondary-foreground border-border"
        }
      },
      "data_testid": "data-testid=\"project-state-pill\""
    },

    "sidebar": {
      "behavior": {
        "desktop": "Fixed left column w/ Collapsible groups; width 280px expanded, 72px collapsed.",
        "mobile": "Use Sheet (left) triggered by icon button in top bar."
      },
      "nav_item": {
        "base": "flex items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent",
        "active": "bg-[hsl(var(--primary)/0.12)] text-foreground border border-[hsl(var(--primary)/0.25)]",
        "icon": "lucide-react icons only",
        "data_testid": "data-testid=\"sidebar-nav-item\" with route suffix"
      },
      "sections": [
        "Project",
        "BRD",
        "Architecture",
        "Plan",
        "Files",
        "Build",
        "Acceptance",
        "Export"
      ]
    },

    "breadcrumb": {
      "use": "shadcn breadcrumb.jsx",
      "pattern": "Dashboard / ProjectName / Section",
      "data_testid": "data-testid=\"top-breadcrumb\""
    },

    "event_ledger_drawer": {
      "container": "Use Sheet (right side) or Drawer depending on existing patterns; prefer Sheet for right slide-out.",
      "layout": {
        "header": "Title 'Event Ledger' + connection status dot + Pause/Resume + Clear",
        "filters": "Tabs or segmented controls: All / Build / BRD / Export / Errors",
        "list": "ScrollArea with virtual-ish feel (cap height), each row is compact",
        "row": {
          "left": "timestamp (mono), actor badge",
          "middle": "event type (strong), short message",
          "right": "status badge + chevron to expand payload preview"
        },
        "expanded": "Accordion reveals JSON payload preview in mono on code-bg surface"
      },
      "row_styles": {
        "base": "rounded-md border border-border bg-card px-3 py-2",
        "hover": "hover:bg-[hsl(var(--accent))] (subtle)"
      },
      "data_testid": {
        "open_button": "data-testid=\"open-event-ledger-button\"",
        "drawer": "data-testid=\"event-ledger-drawer\"",
        "row": "data-testid=\"event-ledger-row\"",
        "connection": "data-testid=\"event-ledger-connection-status\""
      }
    },

    "file_tree_and_code_viewer": {
      "layout": "IDE-like split: left file tree (ScrollArea) + right code panel. Use Resizable for desktop.",
      "components": {
        "split": "resizable.jsx",
        "tree_container": "scroll-area.jsx",
        "code_container": "tabs.jsx (Code / Raw / Diff future) + scroll-area.jsx"
      },
      "file_tree": {
        "row": "flex items-center gap-2 px-2 py-1.5 rounded-md text-sm",
        "hover": "hover:bg-accent",
        "active": "bg-[hsl(var(--primary)/0.12)] border border-[hsl(var(--primary)/0.25)]",
        "meta": "right-aligned badges for generated/modified",
        "typography": "file name in sans; path in mono xs"
      },
      "code_panel": {
        "surface": "bg-[hsl(var(--code-bg))] border border-[hsl(var(--code-border))] rounded-lg",
        "header": "filename + copy button + language badge",
        "body": "Monaco-style highlighting (if Monaco not installed, use pre>code with prism-like styling later)",
        "mono": "font-mono text-xs sm:text-sm leading-6",
        "data_testid": {
          "tree": "data-testid=\"file-tree\"",
          "tree_item": "data-testid=\"file-tree-item\"",
          "code_viewer": "data-testid=\"code-viewer\"",
          "copy": "data-testid=\"copy-code-button\""
        }
      }
    },

    "brd_chat": {
      "layout": "Two-column on desktop: left conversation + right BRD maturity + requirement list. Single column on mobile.",
      "question_card": {
        "visual": "Card with category badge + question text + 'Why we ask' collapsible",
        "tailwind": "bg-card border border-border rounded-lg p-4",
        "category_badge": "use Badge with muted background + mono label",
        "data_testid": "data-testid=\"brd-question-card\""
      },
      "answer_card": {
        "visual": "Textarea + helper text + Save/Next buttons; show validation errors inline",
        "tailwind": "bg-[hsl(var(--surface-2))] border border-border rounded-lg p-4",
        "data_testid": {
          "textarea": "data-testid=\"brd-answer-textarea\"",
          "submit": "data-testid=\"brd-answer-submit-button\""
        }
      },
      "maturity_gauge": {
        "component": "progress.jsx",
        "spec": "0–100 with labeled ticks at 0/25/50/75/100; show delta after each answer",
        "visual": "Progress bar with primary accent; numeric score in mono",
        "data_testid": "data-testid=\"brd-maturity-gauge\""
      },
      "requirements_list": {
        "row": "Requirement title + status badge + coverage indicator",
        "interaction": "Click opens side panel with details + acceptance mapping",
        "data_testid": "data-testid=\"brd-requirement-row\""
      }
    },

    "acceptance_matrix": {
      "component": "table.jsx",
      "grid": "Sticky first column (requirement) + horizontally scrollable checks",
      "cell": {
        "content": "Status badge PASS/PARTIAL/FAIL + tooltip with evidence",
        "empty": "Placeholder badge if not run"
      },
      "data_testid": {
        "table": "data-testid=\"acceptance-matrix-table\"",
        "cell": "data-testid=\"acceptance-matrix-cell\""
      }
    },

    "build_runner_timeline": {
      "layout": "Runs list (left) + selected run details (right). On mobile: tabs.",
      "timeline": "Vertical timeline with attempt nodes; each node has status badge + duration + log link",
      "logs": "ScrollArea with mono text; highlight errors in destructive tint",
      "data_testid": {
        "run_row": "data-testid=\"build-run-row\"",
        "repair_node": "data-testid=\"repair-attempt-node\"",
        "logs": "data-testid=\"build-logs-panel\""
      }
    },

    "system_health_pill": {
      "spec": "Always visible on Dashboard + Project top bar. Shows LLM provider: Primary OK / Quota Exhausted (fallback active) / Offline.",
      "visual": "Pill with icon + provider name + small mono detail",
      "states": {
        "primary_ok": "bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))] border-[hsl(var(--success)/0.35)]",
        "fallback_active": "bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))] border-[hsl(var(--warning)/0.35)]",
        "offline": "bg-[hsl(var(--destructive)/0.12)] text-[hsl(var(--destructive))] border-[hsl(var(--destructive)/0.35)]"
      },
      "data_testid": "data-testid=\"system-health-pill\""
    }
  },

  "pages": {
    "dashboard": {
      "cards": "Project cards show: name, last event time, current phase pill, last acceptance summary.",
      "cta": "New Project primary button top-right; secondary 'Import ZIP' future.",
      "health": "System health panel with provider status + SSE connected indicator.",
      "data_testid": {
        "project_card": "data-testid=\"project-card\"",
        "new_project": "data-testid=\"dashboard-new-project-button\""
      }
    },
    "new_project": {
      "layout": "Centered-ish form but left-aligned text; max-w-xl; show examples in muted mono.",
      "fields": "Project name (Input) + idea description (Textarea) + Create button.",
      "data_testid": {
        "name": "data-testid=\"new-project-name-input\"",
        "idea": "data-testid=\"new-project-idea-textarea\"",
        "submit": "data-testid=\"create-project-submit-button\""
      }
    },
    "cockpit": {
      "hero_panel": "State machine viz (stepper) + current phase actions + mini event feed.",
      "stepper": "Horizontal stepper with compact nodes; current node glows subtly.",
      "data_testid": {
        "stepper": "data-testid=\"project-phase-stepper\"",
        "mini_feed": "data-testid=\"cockpit-mini-event-feed\""
      }
    }
  },

  "empty_loading_error_states": {
    "loading": {
      "use": "skeleton.jsx for cards/tables; show 'Connecting to SSE…' in mono",
      "avoid": "spinners-only; always pair with text"
    },
    "empty": {
      "pattern": "Card with title + 1 sentence + primary CTA + secondary docs link",
      "example": "No build runs yet → Run Build"
    },
    "error": {
      "pattern": "Alert component with error code in mono + retry button + 'Open Event Ledger'",
      "data_testid": "data-testid=\"error-alert\""
    }
  },

  "motion": {
    "library": {
      "name": "framer-motion",
      "usage": "Micro-interactions only: drawer open, list item enter, badge updates. No flashy parallax.",
      "install": "npm i framer-motion"
    },
    "durations_ms": {
      "fast": 120,
      "base": 180,
      "slow": 240
    },
    "easing": {
      "standard": "cubic-bezier(0.2, 0.8, 0.2, 1)",
      "emphasized": "cubic-bezier(0.2, 0.9, 0.2, 1)"
    },
    "interaction_rules": [
      "No transition: all. Only transition colors, opacity, shadow.",
      "Buttons: hover shadow + slight brightness; press scale 0.98.",
      "Badges: on status change, crossfade + subtle pulse (opacity only).",
      "Event rows: animate-in from y=4, opacity 0→1 (fast)."
    ],
    "tailwind_examples": {
      "button": "transition-colors duration-150",
      "card_hover": "transition-colors duration-150 hover:bg-[hsl(var(--surface-2))]",
      "focus": "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    }
  },

  "accessibility": {
    "targets": {
      "contrast": "WCAG AA (4.5:1 for body text).",
      "hit_area": "Minimum 40px touch targets on mobile.",
      "focus": "Visible focus ring on all interactive elements."
    },
    "keyboard": {
      "requirements": [
        "Sidebar nav items reachable via Tab; active route indicated.",
        "Event ledger drawer: Esc closes; focus trapped inside Sheet.",
        "Tables: row actions accessible; tooltips not required for core info.",
        "Cmd+K reserved for Command component (future), but keep a placeholder trigger button disabled with Placeholder badge."
      ]
    },
    "aria": {
      "rules": [
        "Badges should include aria-label describing meaning (e.g., 'Acceptance check: PASS').",
        "Icon-only buttons must have aria-label.",
        "SSE connection status should be announced via aria-live polite region (optional)."
      ]
    }
  },

  "libraries_optional": {
    "code_highlighting": {
      "preferred": "Monaco Editor (if later added)",
      "fallback": "pre/code with mono + ScrollArea",
      "note": "Keep initial implementation lightweight; do not block MVP on Monaco."
    },
    "charts": {
      "available": "recharts (already installed)",
      "usage": "BRD maturity trend, build duration sparkline, acceptance pass rate"
    }
  },

  "images": {
    "image_urls": [
      {
        "category": "background_texture",
        "description": "Optional subtle noise texture (CSS-based preferred). Avoid large images; keep local-first.",
        "url": "(use CSS noise; no external image required)"
      }
    ],
    "css_noise_snippet": "/* Add to a top-level container: */\n.bg-noise::before {\n  content: '';\n  position: fixed;\n  inset: 0;\n  pointer-events: none;\n  background-image: url('data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"160\" height=\"160\"><filter id=\"n\"><feTurbulence type=\"fractalNoise\" baseFrequency=\"0.8\" numOctaves=\"3\" stitchTiles=\"stitch\"/></filter><rect width=\"160\" height=\"160\" filter=\"url(%23n)\" opacity=\"0.06\"/></svg>');\n  mix-blend-mode: overlay;\n  opacity: 0.35;\n}"
  },

  "instructions_to_main_agent": {
    "critical": [
      "Remove CRA default App.css centering patterns; do NOT use .App { text-align:center }.",
      "Implement dark theme by setting <html class=\"dark\"> and overriding shadcn tokens in /app/frontend/src/index.css.",
      "No transparent backgrounds: cards/panels must be solid (bg-card / bg-secondary / custom surface vars).",
      "Every interactive + key informational element must include data-testid in kebab-case.",
      "Status badges must be used everywhere a claim is made (Real/Partial/Unsupported/Blocked/Placeholder).",
      "Event Ledger must be real-time SSE; show connection state explicitly (connected/reconnecting/offline)."
    ],
    "implementation_shortlist": [
      "Use Sheet for right Event Ledger drawer.",
      "Use Resizable for Files IDE split view.",
      "Use ScrollArea for logs, file tree, event list.",
      "Use Table for acceptance matrix and build runs.",
      "Use Progress for BRD maturity gauge.",
      "Use Sonner for toasts."
    ],
    "data_testid_convention": {
      "rule": "kebab-case, role-based",
      "examples": [
        "data-testid=\"project-card\"",
        "data-testid=\"project-state-pill\"",
        "data-testid=\"acceptance-matrix-cell\"",
        "data-testid=\"event-ledger-row\"",
        "data-testid=\"brd-answer-submit-button\""
      ]
    }
  },

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>  \n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
