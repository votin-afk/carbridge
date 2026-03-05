import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { 
  Car, 
  FileStack, 
  FileText, 
  TrendingUp, 
  Clock, 
  CheckCircle2,
  ArrowRight,
  Plus,
  Users,
  Wallet,
  BadgeCheck,
  Gift,
  Copy,
  DollarSign,
  Shield,
  AlertCircle,
  CreditCard,
  Headphones,
  Loader2,
  ShoppingCart,
  ClipboardList,
  Search,
  Truck,
  Package
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEAL_STAGES = [
  { key: 'leasing_request', label: 'Лизинг', optional: true },
  { key: 'inspection', label: 'Проверка' },
  { key: 'export', label: 'Экспорт' },
  { key: 'logistics', label: 'Логистика' },
  { key: 'payment', label: 'Оплата' },
  { key: 'delivery', label: 'Доставка' }
];

const DashboardOverview = () => {
  const { user, token } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    garage: 0,
    activeTenders: 0,
    completedTenders: 0,
    applications: 0,
    activeDeals: 0
  });
  const [recentCars, setRecentCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [affiliateData, setAffiliateData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [accountSummary, setAccountSummary] = useState(null);
  const [requestingHelp, setRequestingHelp] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [garageRes, tendersRes, docsRes, accountRes, applicationsRes, dealsRes] = await Promise.all([
          axios.get(`${API}/garage`, { headers }),
          axios.get(`${API}/tenders`, { headers }),
          axios.get(`${API}/documents`, { headers }),
          axios.get(`${API}/account/summary`, { headers }).catch(() => ({ data: null })),
          axios.get(`${API}/applications/my`, { headers }).catch(() => ({ data: [] })),
          axios.get(`${API}/deals`, { headers }).catch(() => ({ data: [] }))
        ]);

        setStats({
          garage: garageRes.data.length,
          activeTenders: tendersRes.data.filter(t => t.status === 'active').length,
          completedTenders: tendersRes.data.filter(t => t.status === 'selected').length,
          documents: docsRes.data.length,
          applications: applicationsRes.data?.length || 0,
          activeDeals: dealsRes.data?.filter(d => d.status === 'active').length || 0
        });

        setRecentCars(garageRes.data.slice(0, 3));
        setAccountSummary(accountRes.data);
        
        // Fetch affiliate data
        try {
          const affRes = await axios.get(`${API}/affiliate/status`, { headers });
          setAffiliateData(affRes.data);
        } catch (e) {
          // Not registered in affiliate program
        }
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

  const copyReferralLink = () => {
    if (affiliateData?.referral_link) {
      navigator.clipboard.writeText(affiliateData.referral_link);
      setCopied(true);
      toast.success('Ссылка скопирована!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRequestConsultantHelp = async () => {
    if ((accountSummary?.balance || 0) < 200) {
      toast.error('Недостаточно средств. Требуется $200');
      return;
    }
    
    setRequestingHelp(true);
    try {
      await axios.post(`${API}/deals/request-assistance`, {}, { headers });
      toast.success('Запрос на помощь консультанта отправлен! С баланса списано $200');
      // Refresh account summary
      const res = await axios.get(`${API}/account/summary`, { headers });
      setAccountSummary(res.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при запросе помощи');
    } finally {
      setRequestingHelp(false);
    }
  };

  const statCards = [
    { 
      title: 'В гараже', 
      value: stats.garage, 
      icon: Car, 
      color: 'text-[#00E5FF]',
      bgColor: 'bg-[#00E5FF]/10',
      link: '/dashboard/garage'
    },
    { 
      title: 'Активные заявки', 
      value: stats.applications, 
      icon: ClipboardList, 
      color: 'text-blue-400',
      bgColor: 'bg-blue-400/10',
      link: '/dashboard/applications'
    },
    { 
      title: 'Активные сделки', 
      value: stats.activeDeals, 
      icon: ShoppingCart, 
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/10',
      link: '/dashboard/deals'
    },
    { 
      title: 'Тендеры', 
      value: stats.activeTenders, 
      icon: FileStack, 
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10',
      link: '/dashboard/tenders'
    },
  ];

  const getStatusBadge = (status) => {
    const styles = {
      saved: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      tender_active: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      in_progress: 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/20',
      in_deal: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
      completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    };
    const labels = {
      saved: 'Сохранен',
      tender_active: 'Тендер',
      in_progress: 'В работе',
      in_deal: 'В сделке',
      completed: 'Завершен'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs border ${styles[status] || styles.saved}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getCurrentStageIndex = () => {
    if (!accountSummary?.active_deal) return -1;
    const currentStage = accountSummary.active_deal.current_stage;
    return DEAL_STAGES.findIndex(s => s.key === currentStage);
  };

  const getStageStatus = (stageKey) => {
    if (!accountSummary?.active_deal?.stages) return 'pending';
    const stage = accountSummary.active_deal.stages[stageKey];
    if (!stage) return 'pending';
    if (stage.completed || stage.moderator_approved) return 'completed';
    if (stage.paid) return 'paid';
    if (stage.skipped) return 'skipped';
    return 'pending';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard-overview">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Добро пожаловать, {user?.name}!
        </h1>
        <p className="text-slate-400 mt-1">
          Здесь вы можете управлять подбором и покупкой автомобилей из Китая
        </p>
      </div>

      {/* Account Status Card */}
      <div className="bg-gradient-to-r from-[#1C2128] to-[#15191E] border border-[#27272A] rounded-lg p-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          {/* Balance */}
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
              <Wallet size={28} className="text-[#00E5FF]" />
            </div>
            <div>
              <p className="text-slate-400 text-sm">Мой баланс</p>
              <p className="text-2xl font-bold text-white">
                ${(accountSummary?.balance || 0).toLocaleString('ru-RU', { minimumFractionDigits: 2 })}
              </p>
            </div>
          </div>
          
          <div className="flex flex-wrap gap-3">
            {/* Verification Status */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-sm border ${
              accountSummary?.is_verified 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}>
              {accountSummary?.is_verified ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
              <span className="text-sm">{accountSummary?.is_verified ? 'Верифицирован' : 'Не верифицирован'}</span>
            </div>
            
            {/* Contract Status */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-sm border ${
              accountSummary?.contract_signed 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-slate-500/10 border-slate-500/30 text-slate-400'
            }`}>
              <FileText size={16} />
              <span className="text-sm">
                {accountSummary?.contract_signed 
                  ? `Договор ${accountSummary.contract_number || ''}` 
                  : 'Договор не подписан'}
              </span>
            </div>

            <Button 
              className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              onClick={() => toast.info('Функция пополнения баланса скоро будет доступна')}
            >
              <CreditCard size={16} className="mr-2" />
              Пополнить
            </Button>
          </div>
        </div>

        {/* Verification Warning */}
        {(!accountSummary?.is_verified || !accountSummary?.contract_signed) && (
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-sm">
            <p className="text-amber-400 text-sm flex items-center gap-2">
              <Shield size={14} />
              {!accountSummary?.is_verified 
                ? 'Пройдите верификацию для запуска сделок'
                : 'Подпишите договор для запуска сделок'}
              <Link to="/dashboard/verification" className="underline hover:text-amber-300">
                Начать →
              </Link>
            </p>
          </div>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, idx) => (
          <Link 
            key={idx} 
            to={stat.link}
            className="bg-[#15191E] border border-[#27272A] rounded-sm p-5 card-hover"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-slate-400 text-sm">{stat.title}</p>
                <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
              </div>
              <div className={`w-10 h-10 ${stat.bgColor} rounded-sm flex items-center justify-center`}>
                <stat.icon size={20} className={stat.color} />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Active Deal Tracker */}
      {accountSummary?.active_deal && (
        <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <ShoppingCart size={20} className="text-[#00E5FF]" />
                Активная сделка
              </h2>
              <p className="text-slate-400 text-sm mt-1">
                {accountSummary.active_deal.car_info?.brand} {accountSummary.active_deal.car_info?.model} ({accountSummary.active_deal.car_info?.year})
              </p>
            </div>
            <Link to="/dashboard/deals">
              <Button size="sm" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
                Подробнее
                <ArrowRight size={14} className="ml-1" />
              </Button>
            </Link>
          </div>

          {/* Progress Timeline */}
          <div className="flex items-center gap-2">
            {DEAL_STAGES.map((stage, idx) => {
              const status = getStageStatus(stage.key);
              const isCurrent = getCurrentStageIndex() === idx;
              const isPast = getCurrentStageIndex() > idx;
              
              return (
                <div key={stage.key} className="flex-1 flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all ${
                    status === 'completed' ? 'bg-emerald-500 border-emerald-500 text-white' :
                    status === 'skipped' ? 'bg-slate-600 border-slate-600 text-slate-400' :
                    isCurrent ? 'bg-[#00E5FF] border-[#00E5FF] text-black' :
                    'border-[#27272A] text-slate-500'
                  }`}>
                    {status === 'completed' ? (
                      <CheckCircle2 size={16} />
                    ) : (
                      <span className="text-xs font-bold">{idx + 1}</span>
                    )}
                  </div>
                  <p className={`mt-2 text-xs text-center ${
                    status === 'completed' ? 'text-emerald-400' :
                    isCurrent ? 'text-white' :
                    'text-slate-500'
                  }`}>
                    {stage.label}
                  </p>
                  {idx < DEAL_STAGES.length - 1 && (
                    <div className={`absolute w-full h-0.5 top-4 left-1/2 ${
                      isPast || status === 'completed' ? 'bg-emerald-500' : 'bg-[#27272A]'
                    }`} style={{ width: 'calc(100% - 2rem)', marginLeft: '1rem' }} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Quick Actions & Recent Cars */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Quick Actions */}
        <div className="lg:col-span-1 bg-[#15191E] border border-[#27272A] rounded-sm p-6">
          <h2 className="text-lg font-semibold text-white mb-4">Быстрые действия</h2>
          <div className="space-y-3">
            <Link to="/dashboard/garage">
              <Button 
                data-testid="quick-add-car"
                className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black justify-start gap-3"
              >
                <Plus size={18} />
                Добавить авто в гараж
              </Button>
            </Link>
            <Link to="/dashboard/applications">
              <Button 
                variant="outline" 
                className="w-full border-[#27272A] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF] justify-start gap-3"
              >
                <ClipboardList size={18} />
                Создать заявку на подбор
              </Button>
            </Link>
            <Link to="/calculator">
              <Button 
                variant="outline" 
                className="w-full border-[#27272A] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF] justify-start gap-3"
              >
                <TrendingUp size={18} />
                Рассчитать стоимость
              </Button>
            </Link>
            
            {/* Consultant Help Button */}
            <Button 
              variant="outline"
              onClick={handleRequestConsultantHelp}
              disabled={requestingHelp || (accountSummary?.balance || 0) < 200}
              className={`w-full justify-start gap-3 ${
                (accountSummary?.balance || 0) >= 200
                  ? 'border-purple-500/50 text-purple-400 hover:border-purple-400 hover:bg-purple-500/10'
                  : 'border-slate-700 text-slate-500 cursor-not-allowed'
              }`}
            >
              {requestingHelp ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Headphones size={18} />
              )}
              Помощь консультанта — $200
            </Button>
          </div>
        </div>

        {/* Recent Cars */}
        <div className="lg:col-span-2 bg-[#15191E] border border-[#27272A] rounded-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Последние авто в гараже</h2>
            <Link to="/dashboard/garage" className="text-[#00E5FF] text-sm hover:underline flex items-center gap-1">
              Все авто <ArrowRight size={14} />
            </Link>
          </div>

          {recentCars.length > 0 ? (
            <div className="space-y-3">
              {recentCars.map((car) => (
                <div 
                  key={car.id}
                  className="flex items-center gap-4 p-4 bg-[#1C2128] border border-[#27272A] rounded-sm"
                >
                  <div className="w-16 h-12 bg-[#27272A] rounded-sm flex items-center justify-center overflow-hidden">
                    {car.image_url ? (
                      <img src={car.image_url} alt={car.model} className="w-full h-full object-cover" />
                    ) : (
                      <Car size={20} className="text-slate-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {car.brand} {car.model}
                    </p>
                    <p className="text-slate-400 text-sm">
                      {car.year} • ¥{car.price_cny?.toLocaleString()}
                    </p>
                  </div>
                  {getStatusBadge(car.status)}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Car size={40} className="mx-auto mb-2 opacity-30" />
              <p>Нет авто в гараже</p>
              <Link to="/dashboard/garage">
                <Button variant="link" className="text-[#00E5FF] mt-2">
                  Добавить первое авто
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Process Steps */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
        <h2 className="text-lg font-semibold text-white mb-6">Процесс сделки</h2>
        <div className="grid md:grid-cols-6 gap-4">
          {[
            { step: 1, title: "Подбор", desc: "Найдите авто в каталоге или гараже", icon: Search },
            { step: 2, title: "Тендер/Сделка", desc: "Запустите тендер или добавьте в сделку ($300)", icon: FileStack },
            { step: 3, title: "Инспекция", desc: "Выберите подрядчика для проверки", icon: ClipboardList },
            { step: 4, title: "Оплата", desc: "Оплатите этапы через платформу", icon: DollarSign },
            { step: 5, title: "Логистика", desc: "Доставка авто в Беларусь", icon: Truck },
            { step: 6, title: "Выдача", desc: "Получите ваш автомобиль", icon: Package },
          ].map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="text-center">
                <div className="w-12 h-12 mx-auto rounded-full flex items-center justify-center bg-[#00E5FF]/10 border-2 border-[#00E5FF]/30 text-[#00E5FF]">
                  <Icon size={20} />
                </div>
                <p className="mt-2 text-sm text-white font-medium">{item.title}</p>
                <p className="mt-1 text-xs text-slate-500">{item.desc}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Affiliate Section */}
      {affiliateData ? (
        <div className="bg-gradient-to-r from-emerald-500/10 to-[#00E5FF]/10 border border-emerald-500/20 rounded-sm p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              {affiliateData.is_partner ? (
                <div className="w-12 h-12 bg-amber-500/10 rounded-full flex items-center justify-center">
                  <BadgeCheck size={24} className="text-amber-400" />
                </div>
              ) : (
                <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center">
                  <Users size={24} className="text-emerald-400" />
                </div>
              )}
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-semibold text-white">Партнёрская программа</h2>
                  {affiliateData.is_partner && (
                    <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                      Партнёр ✓
                    </span>
                  )}
                </div>
                <p className="text-slate-400 text-sm">
                  {affiliateData.is_partner 
                    ? 'Вы официальный партнёр CarBridge' 
                    : `До статуса партнёра: ${3 - affiliateData.completed_deals} сделок`
                  }
                </p>
              </div>
            </div>
            <Link to="/partners">
              <Button variant="outline" size="sm" className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10">
                Подробнее
                <ArrowRight size={14} className="ml-1" />
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-[#15191E]/50 rounded-sm p-3">
              <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                <Users size={12} />
                Рефералов
              </div>
              <p className="text-white font-semibold">{affiliateData.total_referrals}</p>
            </div>
            <div className="bg-[#15191E]/50 rounded-sm p-3">
              <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                <CheckCircle2 size={12} />
                Сделок
              </div>
              <p className="text-white font-semibold">{affiliateData.completed_deals}</p>
            </div>
            <div className="bg-[#15191E]/50 rounded-sm p-3">
              <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                <DollarSign size={12} />
                Заработано
              </div>
              <p className="text-emerald-400 font-semibold">${affiliateData.total_earnings?.toFixed(2)}</p>
            </div>
            <div className="bg-[#15191E]/50 rounded-sm p-3">
              <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
                <Wallet size={12} />
                К выводу
              </div>
              <p className="text-[#00E5FF] font-semibold">${affiliateData.available_balance?.toFixed(2)}</p>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-[#15191E]/50 rounded-sm p-3">
            <Gift size={16} className="text-emerald-400 flex-shrink-0" />
            <code className="text-emerald-400 text-sm flex-1 truncate">{affiliateData.referral_link}</code>
            <Button
              size="sm"
              onClick={copyReferralLink}
              className={`${copied ? 'bg-emerald-500' : 'bg-emerald-500/20'} hover:bg-emerald-500/30 text-emerald-400`}
            >
              {copied ? <CheckCircle2 size={14} /> : <Copy size={14} />}
            </Button>
          </div>
        </div>
      ) : (
        <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 bg-emerald-500/10 rounded-full flex items-center justify-center">
                <Gift size={24} className="text-emerald-400" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-white">Партнёрская программа</h2>
                <p className="text-slate-400 text-sm">
                  Приглашайте друзей и получайте 20% от комиссии CarBridge
                </p>
              </div>
            </div>
            <Link to="/partners">
              <Button className="bg-emerald-500 hover:bg-emerald-600 text-white">
                <Users size={16} className="mr-2" />
                Стать партнёром
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardOverview;
