import { Home, LayoutDashboard, Settings, Shield, Sparkles, PanelLeftClose, PanelLeftOpen } from 'lucide-react';
import { useState } from 'react';
import { Link, useLocation } from 'react-router';

const menuItems = [
  { icon: Home, label: 'Home', path: '/' },
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: Sparkles, label: 'Copiloto Técnico', path: '/technical' },
  { icon: Shield, label: 'Governança IA', path: '/governance' },
  { icon: Settings, label: 'Configurações', path: '/settings' },
];

export function Sidebar() {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div
      className={`hidden h-full flex-col border-r border-sidebar-border bg-sidebar lg:flex transition-all duration-300 ${
        collapsed ? 'w-16' : 'w-64'
      }`}
    >
      <div className="border-b border-sidebar-border p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary">
            <Shield className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-semibold text-sidebar-foreground">NeoIA</h1>
              <p className="text-xs text-muted-foreground">Security Portal</p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 p-2">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <li key={item.label}>
                <Link
                  to={item.path}
                  title={collapsed ? item.label : undefined}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-3 transition-colors ${
                    collapsed ? 'justify-center' : ''
                  } ${
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent/50'
                  }`}
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {!collapsed && <span className="text-sm font-medium">{item.label}</span>}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="border-t border-sidebar-border p-2">
        {!collapsed && (
          <div className="flex items-center gap-3 px-3 py-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
              <span className="text-xs font-medium">AD</span>
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-sidebar-foreground truncate">Admin User</p>
              <p className="text-xs text-muted-foreground truncate">admin@neoia.com</p>
            </div>
          </div>
        )}

        <div className={`flex ${collapsed ? 'justify-center' : ''} px-1`}>
          <button
            type="button"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? 'Expandir sidebar' : 'Recolher sidebar'}
            className="flex h-9 w-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground"
          >
            {collapsed ? (
              <PanelLeftOpen className="h-5 w-5" />
            ) : (
              <PanelLeftClose className="h-5 w-5" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
