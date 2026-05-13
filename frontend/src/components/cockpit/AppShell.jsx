import React, { useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import {
  LayoutGrid, FilePlus, Cpu, MessagesSquare, Network, ListTree, FileCode2,
  Hammer, ClipboardCheck, Package, ChevronLeft, ChevronRight, Activity,
  Wand2, Shield, Sparkles,
} from 'lucide-react';
import { motion } from 'framer-motion';
import { Sheet, SheetTrigger, SheetContent, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import SystemHealthPill from '@/components/cockpit/SystemHealthPill';
import StatePill from '@/components/cockpit/StatePill';
import EventLedgerDrawer from '@/components/cockpit/EventLedgerDrawer';

const GLOBAL_NAV = [
  { to: '/', icon: LayoutGrid, label: 'Dashboard' },
  { to: '/projects/new', icon: FilePlus, label: 'New Project' },
];

function ProjectNav({ id, current }) {
  const items = [
    { to: `/projects/${id}`, icon: Cpu, label: 'Cockpit' },
    { to: `/projects/${id}/brd`, icon: MessagesSquare, label: 'BRD' },
    { to: `/projects/${id}/architecture`, icon: Network, label: 'Architecture' },
    { to: `/projects/${id}/plan`, icon: ListTree, label: 'Plan' },
    { to: `/projects/${id}/files`, icon: FileCode2, label: 'Files' },
    { to: `/projects/${id}/build`, icon: Hammer, label: 'Build & Repair' },
    { to: `/projects/${id}/acceptance`, icon: ClipboardCheck, label: 'Acceptance' },
    { to: `/projects/${id}/improve`, icon: Wand2, label: 'Improve' },
    { to: `/projects/${id}/constraints`, icon: Shield, label: 'Constraints' },
    { to: `/projects/${id}/sandbox`, icon: Sparkles, label: 'Sandbox' },
    { to: `/projects/${id}/export`, icon: Package, label: 'Export' },
  ];
  return (
    <div className="mt-2">
      <div className="px-3 py-2 text-[10px] uppercase tracking-wider text-muted-foreground font-mono">Project</div>
      <nav className="flex flex-col gap-0.5 px-2">
        {items.map(it => (
          <NavItem key={it.to} {...it} active={current === it.to} testid={`sidebar-${it.label.toLowerCase().replace(/\s|&/g, '-')}`} />
        ))}
      </nav>
    </div>
  );
}

function NavItem({ to, icon: Icon, label, active, testid }) {
  return (
    <Link
      to={to}
      data-testid={testid || `sidebar-nav-${label.toLowerCase().replace(/\s/g, '-')}`}
      className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors duration-150 ${
        active
          ? 'bg-[hsl(var(--primary)/0.14)] text-foreground border border-[hsl(var(--primary)/0.30)]'
          : 'text-muted-foreground hover:text-foreground hover:bg-accent border border-transparent'
      }`}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{label}</span>
    </Link>
  );
}

export function AppShell({ children, project }) {
  const location = useLocation();
  const { id } = useParams();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const projectId = id || project?.id;

  return (
    <div className="dark min-h-screen bg-background text-foreground bg-noise">
      <div className="relative z-10 flex min-h-screen">
        {/* Sidebar */}
        <aside className="hidden md:flex md:w-[260px] shrink-0 flex-col border-r border-border bg-card">
          <div className="flex items-center gap-2 px-4 py-4 border-b border-border">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[hsl(var(--primary)/0.18)] border border-[hsl(var(--primary)/0.35)]">
              <Activity className="h-4 w-4 text-[hsl(var(--primary))]" />
            </div>
            <div>
              <div className="text-sm font-semibold leading-tight">Local App Creator</div>
              <div className="text-[10px] font-mono text-muted-foreground">software factory</div>
            </div>
          </div>
          <nav className="flex flex-col gap-0.5 px-2 py-3">
            {GLOBAL_NAV.map(it => (
              <NavItem key={it.to} {...it} active={location.pathname === it.to} />
            ))}
          </nav>
          {projectId && <ProjectNav id={projectId} current={location.pathname} />}
          <div className="mt-auto px-4 py-3 border-t border-border text-[10px] text-muted-foreground font-mono">
            v0.2.0 · local-first
          </div>
        </aside>

        {/* Main */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Top bar */}
          <header className="flex items-center gap-3 border-b border-border bg-card px-4 sm:px-6 py-3">
            <div className="flex items-center gap-3 min-w-0">
              {project && (
                <>
                  <span className="text-sm text-muted-foreground">Project</span>
                  <span className="text-sm font-semibold truncate max-w-[280px]">{project.name}</span>
                  <span className="text-[11px] font-mono text-muted-foreground">#{project.id}</span>
                  <StatePill state={project.state} />
                </>
              )}
              {!project && (
                <span className="text-sm font-semibold">Dashboard</span>
              )}
            </div>
            <div className="ml-auto flex items-center gap-2">
              <SystemHealthPill />
              <Sheet open={drawerOpen} onOpenChange={setDrawerOpen}>
                <SheetTrigger asChild>
                  <button
                    data-testid="open-event-ledger-button"
                    className="inline-flex items-center gap-2 rounded-md border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground hover:bg-accent transition-colors duration-150"
                  >
                    <Activity className="h-3.5 w-3.5" />
                    Event Ledger
                  </button>
                </SheetTrigger>
                <SheetContent side="right" className="w-full sm:max-w-[520px] p-0">
                  <SheetTitle className="sr-only">Event Ledger</SheetTitle>
                  <SheetDescription className="sr-only">Real-time event stream of orchestrator pipeline activity.</SheetDescription>
                  <EventLedgerDrawer projectId={projectId} />
                </SheetContent>
              </Sheet>
            </div>
          </header>

          <motion.main
            key={location.pathname}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, ease: [0.2, 0.8, 0.2, 1] }}
            className="flex-1 px-4 sm:px-6 lg:px-8 py-6"
          >
            {children}
          </motion.main>
        </div>
      </div>
    </div>
  );
}

export default AppShell;
