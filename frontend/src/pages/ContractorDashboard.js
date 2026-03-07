import { useState, useEffect } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import {
  Building2,
  LayoutDashboard,
  Gavel,
  FileText,
  Star,
  TrendingUp,
  Clock,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Loader2,
  LogOut,
  Car,
  DollarSign,
  Calendar,
  Send,
  Eye,
  BadgeCheck,
  Users,
  Package
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ContractorDashboard = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [contractor, setContractor] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedTender, setSelectedTender] = useState(null);
  const [offerDialog, setOfferDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [token, setToken] = useState(() => localStorage.getItem('contractor_token'));
  
  const [offerData, setOfferData] = useState({
    price_usd: '',
    price_cny: '',
    delivery_days: '',
    delivery_cost: '',
    car_details: '',
    car_link: '',
    car_photos: [],
    car_videos: [],
    notes: '',
    valid_until: '',
    // Services included in offer
    included_services: {
      inspection: false,
      export: false,
      logistics_china: false,
      delivery_rb: false,
      insurance: false
    },
    // Service prices breakdown
    service_prices: {
      inspection: '',
      export: '',
      logistics_china: '',
      delivery_rb: '',
      insurance: ''
    }
  });

  useEffect(() => {
    if (token) {
      fetchDashboard(token);
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchDashboard = async (currentToken) => {
    try {
      const response = await axios.get(`${API}/contractor-dashboard`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setDashboardData(response.data);
      
      // Handle services that might be string or array
      const contractorData = response.data.contractor;
      if (contractorData && typeof contractorData.services === 'string') {
        contractorData.services = contractorData.services.split(',').map(s => s.trim()).filter(s => s);
      }
      setContractor(contractorData);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      if (error.response?.status === 401) {
        localStorage.removeItem('contractor_token');
        setToken(null);
        setContractor(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('contractor_token');
    setToken(null);
    setContractor(null);
    navigate('/contractor-register');
  };

  const submitOffer = async () => {
    if (!selectedTender) return;
    
    // Validate at least one service is selected
    const hasServices = Object.values(offerData.included_services).some(v => v);
    if (!hasServices) {
      toast.error('Выберите хотя бы одну услугу');
      return;
    }
    
    setSubmitting(true);
    try {
      // Calculate total from individual service prices
      let calculatedTotal = 0;
      Object.entries(offerData.included_services).forEach(([service, included]) => {
        if (included && offerData.service_prices[service]) {
          calculatedTotal += parseFloat(offerData.service_prices[service]) || 0;
        }
      });
      
      await axios.post(`${API}/contractor-offers`, {
        tender_id: selectedTender.id,
        price_usd: parseFloat(offerData.price_usd) || calculatedTotal,
        price_cny: parseFloat(offerData.price_cny) || null,
        delivery_days: parseInt(offerData.delivery_days) || null,
        delivery_cost: parseFloat(offerData.delivery_cost) || null,
        car_details: offerData.car_details,
        car_link: offerData.car_link,
        car_photos: offerData.car_photos,
        car_videos: offerData.car_videos,
        notes: offerData.notes,
        included_services: offerData.included_services,
        service_prices: offerData.service_prices
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success('Предложение отправлено');
      setOfferDialog(false);
      setSelectedTender(null);
      resetOfferData();
      fetchDashboard();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка отправки');
    } finally {
      setSubmitting(false);
    }
  };

  const resetOfferData = () => {
    setOfferData({
      price_usd: '',
      price_cny: '',
      delivery_days: '',
      delivery_cost: '',
      car_details: '',
      car_link: '',
      car_photos: [],
      car_videos: [],
      notes: '',
      valid_until: '',
      included_services: {
        inspection: false,
        export: false,
        logistics_china: false,
        delivery_rb: false,
        insurance: false
      },
      service_prices: {
        inspection: '',
        export: '',
        logistics_china: '',
        delivery_rb: '',
        insurance: ''
      }
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center">
        <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
      </div>
    );
  }

  // Login form if not authenticated
  if (!contractor) {
    return <ContractorLogin onSuccess={(newToken) => {
      setToken(newToken);
      setLoading(true);
    }} />;
  }

  return (
    <div className="min-h-screen bg-[#0B0F14] pb-24 sm:pb-20 overflow-y-auto">
      <div className="max-w-7xl mx-auto px-4 py-6 sm:py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
              <Building2 size={24} className="text-[#00E5FF]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-bold text-white">{contractor.company_name}</h1>
                {contractor.verified && (
                  <BadgeCheck size={20} className="text-emerald-400" />
                )}
              </div>
              <p className="text-slate-400 text-sm">Личный кабинет подрядчика</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="flex items-center gap-1">
                <Star size={16} className="text-amber-400" />
                <span className="text-white font-medium">{contractor.rating?.toFixed(1)}</span>
              </div>
              <p className="text-slate-400 text-xs">{contractor.deals_count} сделок</p>
            </div>
            <Button variant="ghost" onClick={handleLogout} className="text-slate-400">
              <LogOut size={18} />
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon={Gavel} label="Активные тендеры" value={dashboardData?.active_tenders || 0} color="cyan" />
          <StatCard icon={Send} label="Мои предложения" value={dashboardData?.my_offers || 0} color="blue" />
          <StatCard icon={CheckCircle2} label="Завершённые сделки" value={dashboardData?.completed_deals || 0} color="emerald" />
          <StatCard icon={Users} label="Новые заявки" value={dashboardData?.new_applications || 0} color="amber" />
        </div>

        {/* Main Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-[#15191E] p-1 mb-6 flex-wrap h-auto gap-1">
            <TabsTrigger value="overview" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black text-xs sm:text-sm">
              <LayoutDashboard size={16} className="mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Обзор</span>
              <span className="sm:hidden">Обзор</span>
            </TabsTrigger>
            <TabsTrigger value="tenders" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black text-xs sm:text-sm">
              <Gavel size={16} className="mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Тендеры</span>
              <span className="sm:hidden">Тендеры</span>
            </TabsTrigger>
            <TabsTrigger value="applications" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black text-xs sm:text-sm">
              <FileText size={16} className="mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Заявки клиентов</span>
              <span className="sm:hidden">Заявки</span>
            </TabsTrigger>
            <TabsTrigger value="offers" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black text-xs sm:text-sm">
              <Package size={16} className="mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Мои предложения</span>
              <span className="sm:hidden">Мои</span>
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Services */}
              <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
                <h3 className="text-white font-semibold mb-4">Ваши услуги</h3>
                <div className="flex flex-wrap gap-2">
                  {contractor.services && contractor.services.length > 0 ? contractor.services.map(service => (
                    <span key={service} className="px-3 py-1 bg-[#00E5FF]/10 text-[#00E5FF] rounded-full text-sm">
                      {serviceLabels[service] || service}
                    </span>
                  )) : (
                    <span className="text-slate-500 text-sm">Услуги не указаны</span>
                  )}
                </div>
              </div>

              {/* Recent Activity */}
              <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
                <h3 className="text-white font-semibold mb-4">Последняя активность</h3>
                {dashboardData?.recent_offers?.length > 0 ? (
                  <div className="space-y-3">
                    {dashboardData.recent_offers.slice(0, 5).map(offer => (
                      <div key={offer.id} className="flex items-center justify-between text-sm">
                        <span className="text-slate-300">Предложение #{offer.id.slice(0, 6)}</span>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          offer.status === 'accepted' ? 'bg-emerald-500/10 text-emerald-400' :
                          offer.status === 'pending' ? 'bg-amber-500/10 text-amber-400' :
                          'bg-slate-500/10 text-slate-400'
                        }`}>
                          {offer.status === 'accepted' ? 'Принято' : 
                           offer.status === 'pending' ? 'На рассмотрении' : offer.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-slate-500 text-sm">Пока нет активности</p>
                )}
              </div>
            </div>
          </TabsContent>

          {/* Tenders Tab */}
          <TabsContent value="tenders">
            {dashboardData?.tenders?.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.tenders.map(tender => (
                  <div key={tender.id} className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="text-white font-medium">
                          {tender.car_info?.brand} {tender.car_info?.model || 'Автомобиль'}
                        </h4>
                        <p className="text-slate-400 text-sm">
                          Тендер #{tender.id.slice(0, 8)} • {new Date(tender.created_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                      <span className={`px-3 py-1 rounded-full text-xs ${
                        tender.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'
                      }`}>
                        {tender.status === 'active' ? 'Активен' : tender.status}
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                      <div>
                        <p className="text-slate-500">Бюджет</p>
                        <p className="text-[#00E5FF] font-medium">${tender.budget?.toLocaleString() || '—'}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Предложений</p>
                        <p className="text-white">{tender.offers?.length || 0}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Срок</p>
                        <p className="text-white">{tender.delivery_days || '—'} дней</p>
                      </div>
                    </div>

                    <Button
                      onClick={() => {
                        setSelectedTender(tender);
                        setOfferDialog(true);
                      }}
                      className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                    >
                      <Send size={16} className="mr-2" />
                      Сделать предложение
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет активных тендеров" icon={Gavel} />
            )}
          </TabsContent>

          {/* Applications Tab */}
          <TabsContent value="applications">
            {dashboardData?.applications?.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.applications.map(app => (
                  <div key={app.id} className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h4 className="text-white font-medium">
                          {app.brand ? `${app.brand} ${app.model || ''}` : 'Любой автомобиль'}
                        </h4>
                        <p className="text-slate-400 text-sm">
                          Заявка {app.application_number} • {new Date(app.created_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {app.urgent && (
                          <span className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded">Срочно</span>
                        )}
                        <span className={`px-3 py-1 rounded-full text-xs ${
                          app.status === 'new' ? 'bg-blue-500/10 text-blue-400' : 'bg-amber-500/10 text-amber-400'
                        }`}>
                          {app.status === 'new' ? 'Новая' : 'В работе'}
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4 mb-4 text-sm">
                      <div>
                        <p className="text-slate-500">Бюджет</p>
                        <p className="text-[#00E5FF] font-medium">
                          {app.budget_max ? `${app.budget_max.toLocaleString()} ${app.budget_currency}` : '—'}
                        </p>
                      </div>
                      <div>
                        <p className="text-slate-500">Тип двигателя</p>
                        <p className="text-white">{engineLabels[app.engine_type] || 'Любой'}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Год</p>
                        <p className="text-white">{app.year_from || '—'} - {app.year_to || '—'}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Оплата</p>
                        <p className="text-white">{paymentLabels[app.payment_method] || app.payment_method}</p>
                      </div>
                    </div>

                    <Button
                      onClick={() => {
                        setSelectedTender({ id: app.id, type: 'application', ...app });
                        setOfferDialog(true);
                      }}
                      className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                    >
                      <Send size={16} className="mr-2" />
                      Откликнуться
                    </Button>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет активных заявок" icon={FileText} />
            )}
          </TabsContent>

          {/* My Offers Tab */}
          <TabsContent value="offers">
            {dashboardData?.recent_offers?.length > 0 ? (
              <div className="space-y-4">
                {dashboardData.recent_offers.map(offer => (
                  <div key={offer.id} className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">Предложение #{offer.id.slice(0, 8)}</p>
                        <p className="text-slate-400 text-sm">
                          {new Date(offer.created_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-[#00E5FF] font-medium">
                          ${offer.price_usd?.toLocaleString() || '—'}
                        </p>
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          offer.status === 'accepted' ? 'bg-emerald-500/10 text-emerald-400' :
                          offer.status === 'rejected' ? 'bg-red-500/10 text-red-400' :
                          'bg-amber-500/10 text-amber-400'
                        }`}>
                          {offer.status === 'accepted' ? 'Принято' : 
                           offer.status === 'rejected' ? 'Отклонено' : 'На рассмотрении'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Вы ещё не отправляли предложений" icon={Package} />
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Offer Dialog */}
      <Dialog open={offerDialog} onOpenChange={setOfferDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Send size={20} className="text-[#00E5FF]" />
              Сделать предложение
            </DialogTitle>
          </DialogHeader>

          {selectedTender && (
            <div className="space-y-4 mt-4">
              {/* Tender Info */}
              <div className="p-3 bg-[#0B0F14] rounded-sm">
                <p className="text-white font-medium">
                  {selectedTender.car_info?.brand || selectedTender.brand || 'Автомобиль'} {selectedTender.car_info?.model || selectedTender.model || ''}
                </p>
                <p className="text-slate-400 text-sm">
                  {selectedTender.type === 'application' ? `Заявка ${selectedTender.application_number}` : `Тендер #${selectedTender.id.slice(0, 8)}`}
                </p>
              </div>

              {/* Car Link */}
              <div>
                <Label className="text-slate-300">🔗 Ссылка на автомобиль</Label>
                <Input
                  type="url"
                  value={offerData.car_link}
                  onChange={(e) => setOfferData(p => ({ ...p, car_link: e.target.value }))}
                  placeholder="https://che168.com/car/123..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
                <p className="text-slate-500 text-xs mt-1">Ссылка на объявление, если авто в общем доступе</p>
              </div>

              {/* Car Details */}
              <div>
                <Label className="text-slate-300">📋 Детали автомобиля</Label>
                <textarea
                  value={offerData.car_details}
                  onChange={(e) => setOfferData(p => ({ ...p, car_details: e.target.value }))}
                  placeholder="VIN, год, комплектация, пробег, цвет, состояние..."
                  rows={3}
                  className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500"
                />
              </div>

              {/* Photo/Video Links */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">📷 Фото (ссылки)</Label>
                  <textarea
                    value={offerData.car_photos.join('\n')}
                    onChange={(e) => setOfferData(p => ({ ...p, car_photos: e.target.value.split('\n').filter(l => l.trim()) }))}
                    placeholder="Ссылки на фото (по одной на строку)"
                    rows={2}
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 text-xs"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">🎥 Видео (ссылки)</Label>
                  <textarea
                    value={offerData.car_videos.join('\n')}
                    onChange={(e) => setOfferData(p => ({ ...p, car_videos: e.target.value.split('\n').filter(l => l.trim()) }))}
                    placeholder="Ссылки на видео (по одной на строку)"
                    rows={2}
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 text-xs"
                  />
                </div>
              </div>

              {/* Services Selection */}
              <div>
                <Label className="text-slate-300 mb-2 block">🛠️ Этапы сделки в предложении</Label>
                <div className="space-y-3 p-3 bg-[#0B0F14] rounded-sm">
                  {[
                    { key: 'inspection', label: 'Инспекция авто', desc: 'Проверка технического состояния' },
                    { key: 'export', label: 'Выкуп и экспорт', desc: 'Покупка и оформление экспорта из Китая' },
                    { key: 'logistics_china', label: 'Доставка до порта (Китай)', desc: 'Логистика до порта отправления' },
                    { key: 'delivery_rb', label: 'Доставка в Беларусь', desc: 'Морская/ж/д доставка' },
                    { key: 'insurance', label: 'Страхование авто', desc: 'Страхование на время транспортировки' }
                  ].map(service => (
                    <div key={service.key} className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3 flex-1">
                        <input
                          type="checkbox"
                          checked={offerData.included_services[service.key]}
                          onChange={(e) => setOfferData(p => ({
                            ...p,
                            included_services: { ...p.included_services, [service.key]: e.target.checked }
                          }))}
                          className="w-4 h-4 rounded border-[#27272A] bg-[#15191E] text-[#00E5FF]"
                        />
                        <div>
                          <p className="text-white text-sm">{service.label}</p>
                          <p className="text-slate-500 text-xs">{service.desc}</p>
                        </div>
                      </div>
                      {offerData.included_services[service.key] && (
                        <div className="flex items-center gap-1">
                          <span className="text-slate-400 text-sm">$</span>
                          <Input
                            type="number"
                            value={offerData.service_prices[service.key]}
                            onChange={(e) => setOfferData(p => ({
                              ...p,
                              service_prices: { ...p.service_prices, [service.key]: e.target.value }
                            }))}
                            placeholder="0"
                            className="w-24 bg-[#15191E] border-[#27272A] text-right h-8"
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Total from services */}
                {Object.values(offerData.included_services).some(v => v) && (
                  <div className="flex justify-between items-center mt-2 p-2 bg-[#00E5FF]/10 rounded">
                    <span className="text-slate-300 text-sm">Итого за выбранные услуги:</span>
                    <span className="text-[#00E5FF] font-bold">
                      ${Object.entries(offerData.service_prices)
                        .filter(([k]) => offerData.included_services[k])
                        .reduce((sum, [, v]) => sum + (parseFloat(v) || 0), 0)
                        .toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {/* Pricing */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">💵 Общая цена (USD) *</Label>
                  <Input
                    type="number"
                    value={offerData.price_usd}
                    onChange={(e) => setOfferData(p => ({ ...p, price_usd: e.target.value }))}
                    placeholder="Авто + услуги"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                  <p className="text-slate-500 text-xs mt-1">Полная стоимость с доставкой</p>
                </div>
                <div>
                  <Label className="text-slate-300">💴 Цена авто (CNY)</Label>
                  <Input
                    type="number"
                    value={offerData.price_cny}
                    onChange={(e) => setOfferData(p => ({ ...p, price_cny: e.target.value }))}
                    placeholder="В юанях"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">📅 Срок доставки (дней)</Label>
                  <Input
                    type="number"
                    value={offerData.delivery_days}
                    onChange={(e) => setOfferData(p => ({ ...p, delivery_days: e.target.value }))}
                    placeholder="30"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">🚚 Отдельно доставка ($)</Label>
                  <Input
                    type="number"
                    value={offerData.delivery_cost}
                    onChange={(e) => setOfferData(p => ({ ...p, delivery_cost: e.target.value }))}
                    placeholder="0 если включена"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              </div>

              <div>
                <Label className="text-slate-300">📝 Примечания</Label>
                <textarea
                  value={offerData.notes}
                  onChange={(e) => setOfferData(p => ({ ...p, notes: e.target.value }))}
                  placeholder="Дополнительная информация, условия..."
                  rows={2}
                  className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500"
                />
              </div>

              <Button
                onClick={submitOffer}
                disabled={submitting || !offerData.price_usd}
                className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                {submitting ? <Loader2 className="animate-spin mr-2" size={16} /> : <Send size={16} className="mr-2" />}
                Отправить предложение
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Contractor Login Component
const ContractorLogin = ({ onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/contractors/login`, { email, password });
      const newToken = response.data.access_token;
      localStorage.setItem('contractor_token', newToken);
      toast.success('Вход выполнен');
      onSuccess(newToken);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка входа');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
            <Building2 size={32} className="text-[#00E5FF]" />
          </div>
          <h1 className="text-2xl font-bold text-white">Кабинет подрядчика</h1>
          <p className="text-slate-400 mt-2">Войдите в личный кабинет</p>
        </div>

        <form onSubmit={handleLogin} className="bg-[#15191E] border border-[#27272A] rounded-sm p-6 space-y-4">
          <div>
            <Label className="text-slate-300">Email</Label>
            <Input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="contractor@company.com"
              required
              className="mt-1 bg-[#0B0F14] border-[#27272A]"
            />
          </div>
          <div>
            <Label className="text-slate-300">Пароль</Label>
            <Input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="mt-1 bg-[#0B0F14] border-[#27272A]"
            />
          </div>
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            {loading ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
            Войти
          </Button>
        </form>

        <div className="text-center mt-6">
          <p className="text-slate-400 text-sm">
            Ещё не зарегистрированы?{' '}
            <Link to="/contractor-register" className="text-[#00E5FF] hover:underline">
              Подать заявку
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

// Helper Components
const StatCard = ({ icon: Icon, label, value, color }) => (
  <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
    <div className="flex items-center gap-3">
      <div className={`w-10 h-10 bg-${color}-500/10 rounded-full flex items-center justify-center`}>
        <Icon size={20} className={`text-${color}-400`} />
      </div>
      <div>
        <p className="text-slate-400 text-sm">{label}</p>
        <p className="text-2xl font-bold text-white">{value}</p>
      </div>
    </div>
  </div>
);

const EmptyState = ({ text, icon: Icon }) => (
  <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
    <Icon size={48} className="mx-auto mb-4 text-slate-600" />
    <p className="text-slate-400">{text}</p>
  </div>
);

// Labels
const serviceLabels = {
  inspection: 'Инспекция',
  purchase: 'Выкуп авто',
  export: 'Экспорт',
  logistics: 'Логистика',
  leasing: 'Лизинг',
  customs: 'Растаможка'
};

const engineLabels = {
  ice: 'ДВС',
  hybrid: 'Гибрид',
  electric: 'Электро',
  any: 'Любой'
};

const paymentLabels = {
  full: 'Полная оплата',
  leasing: 'Лизинг',
  credit: 'Кредит'
};

export default ContractorDashboard;
