import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
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
  Plus
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DashboardOverview = () => {
  const { user, token } = useAuth();
  const [stats, setStats] = useState({
    garage: 0,
    activeTenders: 0,
    completedTenders: 0,
    documents: 0
  });
  const [recentCars, setRecentCars] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` };
        
        const [garageRes, tendersRes, docsRes] = await Promise.all([
          axios.get(`${API}/garage`, { headers }),
          axios.get(`${API}/tenders`, { headers }),
          axios.get(`${API}/documents`, { headers })
        ]);

        setStats({
          garage: garageRes.data.length,
          activeTenders: tendersRes.data.filter(t => t.status === 'active').length,
          completedTenders: tendersRes.data.filter(t => t.status === 'selected').length,
          documents: docsRes.data.length
        });

        setRecentCars(garageRes.data.slice(0, 3));
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [token]);

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
      title: 'Активные тендеры', 
      value: stats.activeTenders, 
      icon: Clock, 
      color: 'text-amber-400',
      bgColor: 'bg-amber-400/10',
      link: '/dashboard/tenders'
    },
    { 
      title: 'Завершено', 
      value: stats.completedTenders, 
      icon: CheckCircle2, 
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-400/10',
      link: '/dashboard/tenders'
    },
    { 
      title: 'Документов', 
      value: stats.documents, 
      icon: FileText, 
      color: 'text-purple-400',
      bgColor: 'bg-purple-400/10',
      link: '/dashboard/documents'
    },
  ];

  const getStatusBadge = (status) => {
    const styles = {
      saved: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      tender_active: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      in_progress: 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/20',
      completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    };
    const labels = {
      saved: 'Сохранен',
      tender_active: 'Тендер',
      in_progress: 'В работе',
      completed: 'Завершен'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs border ${styles[status] || styles.saved}`}>
        {labels[status] || status}
      </span>
    );
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

      {/* Quick Actions & Recent */}
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
            <Link to="/calculator">
              <Button 
                variant="outline" 
                className="w-full border-[#27272A] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF] justify-start gap-3"
              >
                <TrendingUp size={18} />
                Рассчитать стоимость
              </Button>
            </Link>
          </div>
        </div>

        {/* Recent Cars */}
        <div className="lg:col-span-2 bg-[#15191E] border border-[#27272A] rounded-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-white">Последние авто</h2>
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
                  <div className="w-16 h-12 bg-[#27272A] rounded-sm flex items-center justify-center">
                    {car.image_url ? (
                      <img src={car.image_url} alt={car.model} className="w-full h-full object-cover rounded-sm" />
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
        <h2 className="text-lg font-semibold text-white mb-6">Как это работает</h2>
        <div className="grid md:grid-cols-6 gap-4">
          {[
            { step: 1, title: "Подбор", active: true },
            { step: 2, title: "Тендер", active: false },
            { step: 3, title: "Инспекция", active: false },
            { step: 4, title: "Оплата", active: false },
            { step: 5, title: "Логистика", active: false },
            { step: 6, title: "Выдача", active: false },
          ].map((item, idx) => (
            <div key={idx} className="text-center">
              <div className={`w-10 h-10 mx-auto rounded-full flex items-center justify-center border-2 ${
                item.active 
                  ? 'bg-[#00E5FF] border-[#00E5FF] text-black' 
                  : 'border-[#27272A] text-slate-500'
              }`}>
                {item.step}
              </div>
              <p className={`mt-2 text-sm ${item.active ? 'text-white' : 'text-slate-500'}`}>
                {item.title}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
