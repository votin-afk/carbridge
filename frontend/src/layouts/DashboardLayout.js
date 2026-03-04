import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import { 
  LayoutDashboard, 
  Car, 
  FileStack, 
  FileText, 
  LogOut, 
  Menu, 
  X,
  Calculator,
  Bell,
  ChevronRight,
  Shield,
  ClipboardList
} from 'lucide-react';

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Обзор', end: true },
    { to: '/dashboard/garage', icon: Car, label: 'Мой гараж' },
    { to: '/dashboard/applications', icon: ClipboardList, label: 'Заявки' },
    { to: '/dashboard/tenders', icon: FileStack, label: 'Тендеры' },
    { to: '/dashboard/verification', icon: Shield, label: 'Верификация' },
    { to: '/dashboard/documents', icon: FileText, label: 'Документы' },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F14] flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-[#15191E] border-r border-[#27272A] transform transition-transform duration-300 ${
        sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
      }`}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="p-6 border-b border-[#27272A] flex items-center justify-between">
            <Logo />
            <button 
              className="lg:hidden text-slate-400 hover:text-white"
              onClick={() => setSidebarOpen(false)}
            >
              <X size={20} />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) => `
                  flex items-center gap-3 px-4 py-3 rounded-sm transition-colors
                  ${isActive 
                    ? 'bg-[#00E5FF]/10 text-[#00E5FF] border-l-2 border-[#00E5FF]' 
                    : 'text-slate-400 hover:text-white hover:bg-white/5'
                  }
                `}
              >
                <item.icon size={20} />
                <span className="font-medium">{item.label}</span>
              </NavLink>
            ))}

            <div className="pt-4 mt-4 border-t border-[#27272A]">
              <NavLink
                to="/calculator"
                onClick={() => setSidebarOpen(false)}
                className="flex items-center gap-3 px-4 py-3 rounded-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
              >
                <Calculator size={20} />
                <span className="font-medium">Калькулятор</span>
                <ChevronRight size={16} className="ml-auto" />
              </NavLink>
            </div>
          </nav>

          {/* User section */}
          <div className="p-4 border-t border-[#27272A]">
            <div className="flex items-center gap-3 mb-4 px-2">
              <div className="w-10 h-10 rounded-full bg-[#00E5FF]/10 flex items-center justify-center text-[#00E5FF] font-semibold">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{user?.name}</p>
                <p className="text-slate-500 text-xs truncate">{user?.email}</p>
              </div>
            </div>
            <Button
              data-testid="logout-btn"
              onClick={handleLogout}
              variant="ghost"
              className="w-full justify-start gap-3 text-slate-400 hover:text-red-400 hover:bg-red-500/10"
            >
              <LogOut size={18} />
              Выйти
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="h-16 bg-[#15191E]/80 backdrop-blur-sm border-b border-[#27272A] flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
          <button
            data-testid="mobile-menu-btn"
            className="lg:hidden text-slate-400 hover:text-white p-2"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu size={24} />
          </button>

          <div className="flex-1 lg:flex-none" />

          <div className="flex items-center gap-4">
            <button className="relative p-2 text-slate-400 hover:text-white transition-colors">
              <Bell size={20} />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-[#00E5FF] rounded-full" />
            </button>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
