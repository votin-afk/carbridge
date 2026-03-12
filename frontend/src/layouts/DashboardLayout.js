import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import axios from 'axios';
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
  MapPin,
  Bell,
  ChevronRight,
  Shield,
  ClipboardList,
  ShoppingCart,
  Trophy,
  Search,
  Bot,
  Scale,
  CheckCircle2,
  DollarSign,
  Clock
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const { user, token, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (token) {
      fetchNotifications();
    }
  }, [token]);

  const fetchNotifications = async () => {
    try {
      const response = await axios.get(`${API}/api/user/notifications`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await axios.post(`${API}/api/user/notifications/${notificationId}/read`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setNotifications(prev => prev.map(n => 
        n.id === notificationId ? { ...n, is_read: true } : n
      ));
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Error marking notification read:', error);
    }
  };

  const handleNotificationClick = (notification) => {
    if (!notification.is_read) {
      markAsRead(notification.id);
    }
    if (notification.deal_id) {
      navigate('/dashboard/deals');
      setShowNotifications(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const navItems = [
    { to: '/dashboard', icon: LayoutDashboard, label: 'Обзор', end: true },
    { to: '/dashboard/catalog', icon: Search, label: 'Каталог' },
    { to: '/dashboard/garage', icon: Car, label: 'Мой гараж' },
    { to: '/dashboard/applications', icon: ClipboardList, label: 'Заявки' },
    { to: '/dashboard/tenders', icon: FileStack, label: 'Тендеры' },
    { to: '/dashboard/deals', icon: ShoppingCart, label: 'Авто для сделки' },
    { to: '/dashboard/purchased', icon: Trophy, label: 'Приобретённые авто' },
    { to: '/dashboard/verification', icon: Shield, label: 'Верификация' },
    { to: '/dashboard/documents', icon: FileText, label: 'Документы' },
    { to: '/dashboard/tracking', icon: MapPin, label: 'Отследить авто' },
    { to: '/dashboard/ai-assistant', icon: Bot, label: 'ИИ-Ассистент' },
    { to: '/dashboard/legal-help', icon: Scale, label: 'Юридическая помощь' },
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
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" x2="16" y1="6" y2="6"/><line x1="16" x2="16" y1="14" y2="18"/><path d="M16 10h.01"/><path d="M12 10h.01"/><path d="M8 10h.01"/><path d="M12 14h.01"/><path d="M8 14h.01"/><path d="M12 18h.01"/><path d="M8 18h.01"/></svg>
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
            {/* Notifications */}
            <div className="relative">
              <button 
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 text-slate-400 hover:text-white transition-colors"
              >
                <Bell size={20} />
                {unreadCount > 0 && (
                  <span className="absolute top-0.5 right-0.5 w-5 h-5 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">
                    {unreadCount > 9 ? '9+' : unreadCount}
                  </span>
                )}
              </button>
              
              {/* Notifications Dropdown */}
              {showNotifications && (
                <div className="absolute right-0 top-12 w-80 bg-[#1C2128] border border-[#27272A] rounded-lg shadow-xl z-50 max-h-96 overflow-y-auto">
                  <div className="p-3 border-b border-[#27272A] flex justify-between items-center">
                    <h4 className="text-white font-semibold">Уведомления</h4>
                    {unreadCount > 0 && (
                      <span className="text-xs text-[#00E5FF]">{unreadCount} новых</span>
                    )}
                  </div>
                  {notifications.length === 0 ? (
                    <div className="p-4 text-center text-slate-400">
                      Нет уведомлений
                    </div>
                  ) : (
                    notifications.slice(0, 10).map(notification => (
                      <div 
                        key={notification.id}
                        className={`p-3 border-b border-[#27272A] hover:bg-[#27272A] cursor-pointer ${!notification.is_read ? 'bg-[#27272A]/50' : ''}`}
                        onClick={() => handleNotificationClick(notification)}
                      >
                        <div className="flex items-start gap-2">
                          {notification.type === 'stage_approved' && (
                            <CheckCircle2 size={16} className="text-emerald-400 mt-0.5" />
                          )}
                          {notification.type === 'payment_received' && (
                            <DollarSign size={16} className="text-[#00E5FF] mt-0.5" />
                          )}
                          {!['stage_approved', 'payment_received'].includes(notification.type) && (
                            <Bell size={16} className="text-amber-400 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <p className="text-white text-sm font-medium">{notification.title}</p>
                            <p className="text-slate-400 text-xs">{notification.message}</p>
                            <p className="text-slate-500 text-xs mt-1 flex items-center gap-1">
                              <Clock size={10} />
                              {new Date(notification.created_at).toLocaleString('ru-RU')}
                            </p>
                          </div>
                          {!notification.is_read && (
                            <div className="w-2 h-2 bg-[#00E5FF] rounded-full"></div>
                          )}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
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
