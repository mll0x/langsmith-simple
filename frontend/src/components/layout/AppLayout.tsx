import { NavLink } from 'react-router-dom'
import { Activity, Terminal, Rocket, Workflow } from 'lucide-react'

interface AppLayoutProps {
  children: React.ReactNode
}

function NavItem({ to, icon: Icon, label }: { to: string; icon: React.ElementType; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? 'bg-accent/10 text-accent'
            : 'text-text-secondary hover:text-text hover:bg-surface-hover'
        }`
      }
    >
      <Icon size={16} />
      {label}
    </NavLink>
  )
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen bg-bg">
      <aside className="w-56 border-r border-border bg-bg flex flex-col">
        <div className="px-4 py-4 flex items-center gap-2 border-b border-border">
          <Workflow className="text-accent" size={22} />
          <span className="font-semibold text-text">LangSmith Simple</span>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavItem to="/traces" icon={Activity} label="Traces" />
          <NavItem to="/playground" icon={Terminal} label="Playground" />
          <NavItem to="/deployments" icon={Rocket} label="Deployments" />
        </nav>
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  )
}
