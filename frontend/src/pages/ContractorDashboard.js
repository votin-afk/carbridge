import { useState, useEffect, useRef } from 'react';
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
  Package,
  Phone,
  Mail,
  MapPin,
  Fuel,
  Settings,
  Palette,
  User,
  Info,
  Folder,
  MessageSquare,
  Paperclip,
  Upload,
  Download,
  Image,
  Video,
  File,
  Trash2,
  Bell
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import ContractorMessenger from '../components/deal/ContractorMessenger';

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
  const [detailsDialog, setDetailsDialog] = useState(false);
  const [selectedApplication, setSelectedApplication] = useState(null);
  
  // Deal chat states
  const [myDeals, setMyDeals] = useState([]);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [myStages, setMyStages] = useState([]); // Stages assigned to contractor for selected deal
  const [dealMessages, setDealMessages] = useState([]);
  const [dealFiles, setDealFiles] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [sendingMessage, setSendingMessage] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [dealActiveTab, setDealActiveTab] = useState('chat');
  
  // Notifications state
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  
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
      fetchNotifications(token);
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchNotifications = async (currentToken) => {
    try {
      const response = await axios.get(`${API}/contractor-notifications`, {
        headers: { Authorization: `Bearer ${currentToken}` }
      });
      setNotifications(response.data.notifications || []);
      setUnreadCount(response.data.unread_count || 0);
    } catch (error) {
      console.error('Error fetching notifications:', error);
    }
  };

  const markNotificationRead = async (notificationId) => {
    try {
      await axios.post(`${API}/contractor-notifications/${notificationId}/read`, {}, {
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

  // Fetch my deals when switching to deals tab
  useEffect(() => {
    if (activeTab === 'deals' && token) {
      fetchMyDeals();
    }
  }, [activeTab, token]);

  // Polling for deal messages
  useEffect(() => {
    if (selectedDeal && token) {
      fetchDealData();
      fetchMyStages();
      const interval = setInterval(fetchDealData, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedDeal]);

  const fetchMyDeals = async () => {
    try {
      const response = await axios.get(`${API}/contractor/deals`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyDeals(response.data);
    } catch (error) {
      console.error('Error fetching deals:', error);
    }
  };

  const fetchMyStages = async () => {
    if (!selectedDeal) return;
    try {
      const response = await axios.get(`${API}/contractor/deals/${selectedDeal.id}/my-stages`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMyStages(response.data);
    } catch (error) {
      console.error('Error fetching my stages:', error);
      setMyStages([]);
    }
  };

  const fetchDealData = async () => {
    if (!selectedDeal) return;
    
    try {
      const [messagesRes, filesRes] = await Promise.all([
        axios.get(`${API}/contractor/deals/${selectedDeal.id}/messages`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/contractor/deals/${selectedDeal.id}/files`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setDealMessages(messagesRes.data);
      setDealFiles(filesRes.data);
    } catch (error) {
      console.error('Error fetching deal data:', error);
    }
  };

  const sendDealMessage = async () => {
    if (!newMessage.trim() || !selectedDeal) return;
    
    setSendingMessage(true);
    try {
      await axios.post(`${API}/contractor/deals/${selectedDeal.id}/messages`, {
        content: newMessage
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setNewMessage('');
      fetchDealData();
    } catch (error) {
      toast.error('Ошибка отправки сообщения');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleDealFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedDeal) return;
    
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Файл слишком большой (максимум 50MB)');
      return;
    }
    
    setUploadingFile(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', 'document');
    formData.append('description', '');
    
    try {
      await axios.post(`${API}/contractor/deals/${selectedDeal.id}/files`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.success('Файл загружен');
      fetchDealData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка загрузки файла');
    } finally {
      setUploadingFile(false);
      e.target.value = '';
    }
  };

  const downloadDealFile = async (fileId, filename) => {
    try {
      const response = await axios.get(
        `${API}/contractor/deals/${selectedDeal.id}/files/${fileId}/download`,
        { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' }
      );
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (error) {
      toast.error('Ошибка скачивания файла');
    }
  };

  const getFileIcon = (category) => {
    switch (category) {
      case 'photo': return <Image size={16} className="text-emerald-400" />;
      case 'video': return <Video size={16} className="text-purple-400" />;
      case 'document': return <FileText size={16} className="text-blue-400" />;
      default: return <File size={16} className="text-slate-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
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
      fetchDashboard(token);
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
            
            {/* Notifications */}
            <div className="relative">
              <Button 
                variant="ghost" 
                onClick={() => setShowNotifications(!showNotifications)}
                className="text-slate-400 relative"
              >
                <Bell size={18} />
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </Button>
              
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
                    notifications.map(notification => (
                      <div 
                        key={notification.id}
                        className={`p-3 border-b border-[#27272A] hover:bg-[#27272A] cursor-pointer ${!notification.is_read ? 'bg-[#27272A]/50' : ''}`}
                        onClick={() => {
                          if (!notification.is_read) {
                            markNotificationRead(notification.id);
                          }
                          if (notification.type === 'new_tender') {
                            setActiveTab('tenders');
                            setShowNotifications(false);
                          }
                        }}
                      >
                        <div className="flex items-start gap-2">
                          {notification.type === 'new_tender' && (
                            <Gavel size={16} className="text-[#00E5FF] mt-0.5" />
                          )}
                          {notification.type === 'deal_assigned' && (
                            <CheckCircle2 size={16} className="text-emerald-400 mt-0.5" />
                          )}
                          <div className="flex-1">
                            <p className="text-white text-sm font-medium">{notification.title}</p>
                            <p className="text-slate-400 text-xs">{notification.message}</p>
                            <p className="text-slate-500 text-xs mt-1">
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
            <TabsTrigger value="deals" className="data-[state=active]:bg-emerald-500 data-[state=active]:text-white text-xs sm:text-sm">
              <Folder size={16} className="mr-1 sm:mr-2" />
              <span className="hidden sm:inline">Мои сделки</span>
              <span className="sm:hidden">Сделки</span>
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
                          {(tender.car_info?.brand || tender.car_request?.brand || 'Любая марка').toUpperCase()} {tender.car_info?.model || tender.car_request?.model || ''}
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
                        <p className="text-[#00E5FF] font-medium">
                          ${tender.budget?.toLocaleString() || tender.car_request?.budget_max?.toLocaleString() || '—'}
                        </p>
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
                        <h4 className="text-white font-medium text-lg">
                          {app.brand ? `${app.brand.toUpperCase()} ${app.model || ''}` : 'Любой автомобиль'}
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

                    {/* Basic Info Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 text-sm">
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Бюджет в Китае</p>
                        <p className="text-[#00E5FF] font-medium">
                          ${app.budget_china_from?.toLocaleString() || '—'} - ${app.budget_china_to?.toLocaleString() || '—'}
                        </p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Общий бюджет</p>
                        <p className="text-emerald-400 font-medium">
                          ${app.budget_total?.toLocaleString() || app.budget_max?.toLocaleString() || '—'}
                        </p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Год выпуска</p>
                        <p className="text-white">{app.year_from || '—'} - {app.year_to || '—'}</p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Тип двигателя</p>
                        <p className="text-white">{engineLabels[app.engine_type] || app.engine_type || 'Любой'}</p>
                      </div>
                    </div>

                    {/* Extended Info Grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3 text-sm">
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Кузов</p>
                        <p className="text-white">{bodyLabels[app.body_type] || app.body_type || 'Любой'}</p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Привод</p>
                        <p className="text-white">{driveLabels[app.drive_type] || app.drive_type || 'Любой'}</p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Пробег</p>
                        <p className="text-white">{mileageLabels[app.mileage_max] || app.mileage_max || 'Любой'}</p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Оплата</p>
                        <p className="text-white">{paymentLabels[app.payment_method] || app.payment_method || '—'}</p>
                      </div>
                    </div>

                    {/* Color and timeline */}
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3 text-sm">
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Цвет кузова</p>
                        <p className="text-white">{colorLabels[app.body_color] || app.body_color || 'Любой'}</p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Сроки покупки</p>
                        <p className="text-white">{timelineLabels[app.purchase_timeline] || app.purchase_timeline || '—'}</p>
                      </div>
                      <div className="bg-[#0B0F14] p-2 rounded">
                        <p className="text-slate-500 text-xs">Клиент</p>
                        <p className="text-white">{app.full_name || '—'}</p>
                      </div>
                    </div>

                    {/* Additional requirements */}
                    {app.additional_requirements && (
                      <div className="mb-3 p-2 bg-[#0B0F14] rounded">
                        <p className="text-slate-500 text-xs mb-1">Дополнительные требования</p>
                        <p className="text-slate-300 text-sm">{app.additional_requirements}</p>
                      </div>
                    )}

                    {/* Options if any */}
                    {(app.options_comfort?.length > 0 || app.options_electronic?.length > 0 || app.options_exterior?.length > 0) && (
                      <div className="mb-3 p-2 bg-[#0B0F14] rounded">
                        <p className="text-slate-500 text-xs mb-2">Желаемые опции</p>
                        <div className="flex flex-wrap gap-1">
                          {app.options_comfort?.map(opt => (
                            <span key={opt} className="px-2 py-0.5 bg-emerald-500/10 text-emerald-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                          {app.options_electronic?.map(opt => (
                            <span key={opt} className="px-2 py-0.5 bg-blue-500/10 text-blue-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                          {app.options_exterior?.map(opt => (
                            <span key={opt} className="px-2 py-0.5 bg-purple-500/10 text-purple-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Buttons */}
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSelectedApplication(app);
                          setDetailsDialog(true);
                        }}
                        className="flex-1 border-[#27272A] hover:bg-[#27272A]"
                      >
                        <Eye size={16} className="mr-2" />
                        Все детали
                      </Button>
                      <Button
                        onClick={() => {
                          setSelectedTender({ id: app.id, type: 'application', ...app });
                          setOfferDialog(true);
                        }}
                        className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                      >
                        <Send size={16} className="mr-2" />
                        Откликнуться
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет активных заявок" icon={FileText} />
            )}
          </TabsContent>

          {/* My Deals Tab */}
          <TabsContent value="deals">
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Deals List */}
              <div className="lg:col-span-1 space-y-3">
                <h3 className="text-white font-medium">Мои сделки</h3>
                
                {myDeals.length === 0 ? (
                  <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 text-center">
                    <Car size={48} className="mx-auto mb-3 text-slate-600" />
                    <p className="text-slate-400">Нет активных сделок</p>
                  </div>
                ) : (
                  myDeals.map(deal => (
                    <div
                      key={deal.id}
                      onClick={() => setSelectedDeal(deal)}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedDeal?.id === deal.id
                          ? 'bg-emerald-500/10 border-emerald-500'
                          : 'bg-[#15191E] border-[#27272A] hover:border-emerald-500/50'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        {deal.car_info?.image_url ? (
                          <img src={deal.car_info.image_url} alt="" className="w-12 h-9 object-cover rounded" />
                        ) : (
                          <div className="w-12 h-9 bg-[#0B0F14] rounded flex items-center justify-center">
                            <Car size={18} className="text-slate-600" />
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-white font-medium truncate">
                            {deal.car_info?.brand} {deal.car_info?.model}
                          </p>
                          <p className="text-slate-500 text-xs">
                            Клиент: {deal.client?.name || deal.client?.email || '—'}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>

              {/* Deal Content */}
              <div className="lg:col-span-2">
                {!selectedDeal ? (
                  <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
                    <MessageSquare size={64} className="mx-auto mb-4 text-slate-600" />
                    <p className="text-slate-400">Выберите сделку для просмотра чата и документов</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {/* Deal Header */}
                    <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
                      <div className="flex items-center gap-4">
                        {selectedDeal.car_info?.image_url ? (
                          <img src={selectedDeal.car_info.image_url} alt="" className="w-16 h-12 object-cover rounded" />
                        ) : (
                          <div className="w-16 h-12 bg-[#0B0F14] rounded flex items-center justify-center">
                            <Car size={24} className="text-slate-600" />
                          </div>
                        )}
                        <div>
                          <h3 className="text-white font-semibold text-lg">
                            {selectedDeal.car_info?.brand} {selectedDeal.car_info?.model}
                          </h3>
                          <p className="text-slate-400 text-sm">
                            Клиент: {selectedDeal.client?.name || selectedDeal.client?.email}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Stage-based Messenger */}
                    <ContractorMessenger
                      deal={selectedDeal}
                      token={token}
                      myStages={myStages}
                      onRefresh={fetchMyDeals}
                    />
                  </div>
                )}
              </div>
            </div>
          </TabsContent>
                    {dealActiveTab === 'chat' ? (
                      <div className="flex flex-col h-[400px]">
                        {/* Messages */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-3">
                          {dealMessages.length === 0 ? (
                            <div className="text-center py-8">
                              <MessageSquare size={48} className="mx-auto mb-3 text-slate-600" />
                              <p className="text-slate-400">Нет сообщений</p>
                            </div>
                          ) : (
                            dealMessages.map(msg => (
                              <div
                                key={msg.id}
                                className={`flex ${msg.sender_type === 'contractor' ? 'justify-end' : 'justify-start'}`}
                              >
                                <div className={`max-w-[70%] ${
                                  msg.sender_type === 'contractor'
                                    ? 'bg-emerald-500/10 border border-emerald-500/30'
                                    : 'bg-[#27272A]'
                                } rounded-lg p-3`}>
                                  <div className="flex items-center gap-2 mb-1">
                                    {msg.sender_type === 'contractor' ? (
                                      <Building2 size={12} className="text-emerald-400" />
                                    ) : (
                                      <User size={12} className="text-[#00E5FF]" />
                                    )}
                                    <span className={`text-xs font-medium ${
                                      msg.sender_type === 'contractor' ? 'text-emerald-400' : 'text-[#00E5FF]'
                                    }`}>
                                      {msg.sender_name}
                                    </span>
                                    <span className="text-xs text-slate-500">
                                      {new Date(msg.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                  </div>
                                  <p className="text-white text-sm whitespace-pre-wrap">{msg.content}</p>
                                </div>
                              </div>
                            ))
                          )}
                        </div>

                        {/* Message Input */}
                        <div className="p-4 border-t border-[#27272A]">
                          <div className="flex gap-2">
                            <Input
                              value={newMessage}
                              onChange={(e) => setNewMessage(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendDealMessage()}
                              placeholder="Напишите сообщение..."
                              className="flex-1 bg-[#0B0F14] border-[#27272A]"
                            />
                            <input
                              type="file"
                              id="contractor-file-upload"
                              onChange={handleDealFileUpload}
                              className="hidden"
                            />
                            <Button
                              onClick={() => document.getElementById('contractor-file-upload')?.click()}
                              variant="outline"
                              className="border-[#27272A]"
                              disabled={uploadingFile}
                            >
                              {uploadingFile ? <Loader2 size={16} className="animate-spin" /> : <Paperclip size={16} />}
                            </Button>
                            <Button
                              onClick={sendDealMessage}
                              disabled={sendingMessage || !newMessage.trim()}
                              className="bg-emerald-500 hover:bg-emerald-600 text-white"
                            >
                              {sendingMessage ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                            </Button>
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="p-4">
                        {/* Upload Button */}
                        <div className="mb-4">
                          <input
                            type="file"
                            id="contractor-file-upload-2"
                            onChange={handleDealFileUpload}
                            className="hidden"
                          />
                          <Button
                            onClick={() => document.getElementById('contractor-file-upload-2')?.click()}
                            disabled={uploadingFile}
                            className="bg-emerald-500 hover:bg-emerald-600 text-white"
                          >
                            {uploadingFile ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Upload size={16} className="mr-2" />}
                            Загрузить файл
                          </Button>
                        </div>

                        {/* Files List */}
                        {dealFiles.length === 0 ? (
                          <div className="text-center py-8">
                            <Folder size={48} className="mx-auto mb-3 text-slate-600" />
                            <p className="text-slate-400">Нет файлов</p>
                          </div>
                        ) : (
                          <div className="space-y-2">
                            {dealFiles.map(file => (
                              <div
                                key={file.id}
                                className="flex items-center gap-3 p-3 bg-[#0B0F14] rounded-lg"
                              >
                                <div className="w-10 h-10 bg-[#27272A] rounded-lg flex items-center justify-center">
                                  {getFileIcon(file.category)}
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-white text-sm truncate">{file.original_name}</p>
                                  <div className="flex items-center gap-2 text-xs text-slate-500">
                                    <span>{formatFileSize(file.size)}</span>
                                    <span>•</span>
                                    <span className={file.uploader_type === 'contractor' ? 'text-emerald-400' : 'text-[#00E5FF]'}>
                                      {file.uploader_name}
                                    </span>
                                  </div>
                                </div>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => downloadDealFile(file.id, file.original_name)}
                                  className="h-8 w-8 p-0 text-slate-400 hover:text-white"
                                >
                                  <Download size={16} />
                                </Button>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
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
                  {(selectedTender.car_info?.brand || selectedTender.car_request?.brand || selectedTender.brand || 'Любая марка').toUpperCase()} {selectedTender.car_info?.model || selectedTender.car_request?.model || selectedTender.model || ''}
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

      {/* Application Details Dialog */}
      <Dialog open={detailsDialog} onOpenChange={setDetailsDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText size={20} className="text-[#00E5FF]" />
              Полная информация о заявке
            </DialogTitle>
          </DialogHeader>

          {selectedApplication && (
            <div className="space-y-4 mt-4">
              {/* Header */}
              <div className="p-4 bg-[#0B0F14] rounded-lg">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-xl font-bold text-white">
                      {selectedApplication.brand?.toUpperCase() || 'Любой'} {selectedApplication.model || ''}
                    </h3>
                    <p className="text-slate-400">
                      Заявка {selectedApplication.application_number}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-[#00E5FF]">
                      ${selectedApplication.budget_total?.toLocaleString() || selectedApplication.budget_max?.toLocaleString() || '—'}
                    </p>
                    <p className="text-slate-500 text-sm">общий бюджет</p>
                  </div>
                </div>
              </div>

              {/* Client Info */}
              <div className="p-4 bg-[#0B0F14] rounded-lg">
                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <User size={16} className="text-[#00E5FF]" />
                  Информация о клиенте
                </h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Имя</p>
                    <p className="text-white">{selectedApplication.full_name || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Тип клиента</p>
                    <p className="text-white">{clientTypeLabels[selectedApplication.client_type] || selectedApplication.client_type || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Телефон</p>
                    <p className="text-white flex items-center gap-1">
                      <Phone size={14} className="text-slate-500" />
                      {selectedApplication.phone || '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Email</p>
                    <p className="text-white flex items-center gap-1">
                      <Mail size={14} className="text-slate-500" />
                      {selectedApplication.email || '—'}
                    </p>
                  </div>
                  {selectedApplication.delivery_city && (
                    <div className="col-span-2">
                      <p className="text-slate-500">Город доставки</p>
                      <p className="text-white flex items-center gap-1">
                        <MapPin size={14} className="text-slate-500" />
                        {selectedApplication.delivery_city}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* Car Requirements */}
              <div className="p-4 bg-[#0B0F14] rounded-lg">
                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <Car size={16} className="text-[#00E5FF]" />
                  Требования к автомобилю
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Марка</p>
                    <p className="text-white font-medium">{selectedApplication.brand?.toUpperCase() || 'Любая'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Модель</p>
                    <p className="text-white">{selectedApplication.model || 'Любая'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Год выпуска</p>
                    <p className="text-white">{selectedApplication.year_from || '—'} - {selectedApplication.year_to || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Тип кузова</p>
                    <p className="text-white">{bodyLabels[selectedApplication.body_type] || selectedApplication.body_type || 'Любой'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Тип двигателя</p>
                    <p className="text-white">{engineLabels[selectedApplication.engine_type] || selectedApplication.engine_type || 'Любой'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Объём двигателя</p>
                    <p className="text-white">{selectedApplication.engine_volume || 'Любой'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Мощность</p>
                    <p className="text-white">
                      {selectedApplication.power_from || selectedApplication.power_to 
                        ? `${selectedApplication.power_from || '—'} - ${selectedApplication.power_to || '—'} л.с.`
                        : 'Любая'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">КПП</p>
                    <p className="text-white">{selectedApplication.transmission === 'any' ? 'Любая' : selectedApplication.transmission || 'Любая'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Привод</p>
                    <p className="text-white">{driveLabels[selectedApplication.drive_type] || selectedApplication.drive_type || 'Любой'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Пробег</p>
                    <p className="text-white">{mileageLabels[selectedApplication.mileage_max] || selectedApplication.mileage_max || 'Любой'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Состояние</p>
                    <p className="text-white">{conditionLabels[selectedApplication.car_condition] || selectedApplication.car_condition || 'Любое'}</p>
                  </div>
                  {selectedApplication.allow_damage && (
                    <div>
                      <p className="text-slate-500">Допустимы повреждения</p>
                      <p className="text-amber-400">Да, уровень: {selectedApplication.damage_level || '—'}</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Color Preferences */}
              <div className="p-4 bg-[#0B0F14] rounded-lg">
                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <Palette size={16} className="text-[#00E5FF]" />
                  Цвет
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Цвет кузова</p>
                    <p className="text-white">{colorLabels[selectedApplication.body_color] || selectedApplication.body_color || 'Любой'}</p>
                  </div>
                  {selectedApplication.exact_color && (
                    <div>
                      <p className="text-slate-500">Точный цвет</p>
                      <p className="text-white">{selectedApplication.exact_color}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-slate-500">Важность цвета</p>
                    <p className="text-white">
                      {selectedApplication.color_importance === 'important' ? 'Важно' : 
                       selectedApplication.color_importance === 'not_important' ? 'Не важно' : '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Цвет салона</p>
                    <p className="text-white">{colorLabels[selectedApplication.interior_color] || selectedApplication.interior_color || 'Любой'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Материал салона</p>
                    <p className="text-white">{selectedApplication.interior_material === 'any' ? 'Любой' : selectedApplication.interior_material || 'Любой'}</p>
                  </div>
                </div>
              </div>

              {/* Budget */}
              <div className="p-4 bg-[#0B0F14] rounded-lg">
                <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                  <DollarSign size={16} className="text-[#00E5FF]" />
                  Бюджет и оплата
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Бюджет в Китае</p>
                    <p className="text-[#00E5FF] font-medium">
                      ${selectedApplication.budget_china_from?.toLocaleString() || '—'} - ${selectedApplication.budget_china_to?.toLocaleString() || '—'}
                    </p>
                  </div>
                  <div>
                    <p className="text-slate-500">Общий бюджет</p>
                    <p className="text-emerald-400 font-medium">${selectedApplication.budget_total?.toLocaleString() || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Способ оплаты</p>
                    <p className="text-white">{paymentLabels[selectedApplication.payment_method] || selectedApplication.payment_method || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Сроки покупки</p>
                    <p className="text-white">{timelineLabels[selectedApplication.purchase_timeline] || selectedApplication.purchase_timeline || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Назначение авто</p>
                    <p className="text-white">{selectedApplication.car_purpose === 'personal' ? 'Личное использование' : selectedApplication.car_purpose || '—'}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Растаможка</p>
                    <p className="text-white">{selectedApplication.customs_clearance === 'carbridge' ? 'Через CarBridge' : selectedApplication.customs_clearance || '—'}</p>
                  </div>
                </div>
              </div>

              {/* Priorities */}
              {(selectedApplication.priority_price || selectedApplication.priority_reliability) && (
                <div className="p-4 bg-[#0B0F14] rounded-lg">
                  <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <TrendingUp size={16} className="text-[#00E5FF]" />
                    Приоритеты клиента (1-5)
                  </h4>
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div className="text-center">
                      <p className="text-slate-500 text-xs">Цена</p>
                      <div className="text-xl font-bold text-[#00E5FF]">{selectedApplication.priority_price || '—'}</div>
                    </div>
                    <div className="text-center">
                      <p className="text-slate-500 text-xs">Надёжность</p>
                      <div className="text-xl font-bold text-emerald-400">{selectedApplication.priority_reliability || '—'}</div>
                    </div>
                    <div className="text-center">
                      <p className="text-slate-500 text-xs">Технологии</p>
                      <div className="text-xl font-bold text-blue-400">{selectedApplication.priority_technology || '—'}</div>
                    </div>
                    <div className="text-center">
                      <p className="text-slate-500 text-xs">Престиж</p>
                      <div className="text-xl font-bold text-purple-400">{selectedApplication.priority_prestige || '—'}</div>
                    </div>
                    <div className="text-center">
                      <p className="text-slate-500 text-xs">Экономия топлива</p>
                      <div className="text-xl font-bold text-amber-400">{selectedApplication.priority_fuel || '—'}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Options */}
              {(selectedApplication.options_comfort?.length > 0 || 
                selectedApplication.options_electronic?.length > 0 || 
                selectedApplication.options_exterior?.length > 0 ||
                selectedApplication.options_other?.length > 0) && (
                <div className="p-4 bg-[#0B0F14] rounded-lg">
                  <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <Settings size={16} className="text-[#00E5FF]" />
                    Желаемые опции
                  </h4>
                  <div className="space-y-3">
                    {selectedApplication.options_comfort?.length > 0 && (
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Комфорт</p>
                        <div className="flex flex-wrap gap-1">
                          {selectedApplication.options_comfort.map(opt => (
                            <span key={opt} className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedApplication.options_electronic?.length > 0 && (
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Электроника</p>
                        <div className="flex flex-wrap gap-1">
                          {selectedApplication.options_electronic.map(opt => (
                            <span key={opt} className="px-2 py-1 bg-blue-500/10 text-blue-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedApplication.options_exterior?.length > 0 && (
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Экстерьер</p>
                        <div className="flex flex-wrap gap-1">
                          {selectedApplication.options_exterior.map(opt => (
                            <span key={opt} className="px-2 py-1 bg-purple-500/10 text-purple-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                    {selectedApplication.options_other?.length > 0 && (
                      <div>
                        <p className="text-slate-500 text-xs mb-1">Прочее</p>
                        <div className="flex flex-wrap gap-1">
                          {selectedApplication.options_other.map(opt => (
                            <span key={opt} className="px-2 py-1 bg-slate-500/10 text-slate-400 text-xs rounded">
                              {optionLabels[opt] || opt}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Additional Info */}
              {(selectedApplication.additional_requirements || selectedApplication.required_options || selectedApplication.preferred_options) && (
                <div className="p-4 bg-[#0B0F14] rounded-lg">
                  <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
                    <Info size={16} className="text-[#00E5FF]" />
                    Дополнительная информация
                  </h4>
                  {selectedApplication.required_options && (
                    <div className="mb-3">
                      <p className="text-slate-500 text-xs mb-1">Обязательные опции</p>
                      <p className="text-white text-sm">{selectedApplication.required_options}</p>
                    </div>
                  )}
                  {selectedApplication.preferred_options && (
                    <div className="mb-3">
                      <p className="text-slate-500 text-xs mb-1">Желательные опции</p>
                      <p className="text-white text-sm">{selectedApplication.preferred_options}</p>
                    </div>
                  )}
                  {selectedApplication.additional_requirements && (
                    <div>
                      <p className="text-slate-500 text-xs mb-1">Дополнительные требования</p>
                      <p className="text-white text-sm">{selectedApplication.additional_requirements}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-2">
                <Button
                  variant="outline"
                  onClick={() => setDetailsDialog(false)}
                  className="flex-1 border-[#27272A] hover:bg-[#27272A]"
                >
                  Закрыть
                </Button>
                <Button
                  onClick={() => {
                    setDetailsDialog(false);
                    setSelectedTender({ id: selectedApplication.id, type: 'application', ...selectedApplication });
                    setOfferDialog(true);
                  }}
                  className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                >
                  <Send size={16} className="mr-2" />
                  Откликнуться
                </Button>
              </div>
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
  full_prepay: 'Полная предоплата',
  leasing: 'Лизинг',
  credit: 'Кредит',
  partial: 'Частичная оплата'
};

const bodyLabels = {
  sedan: 'Седан',
  suv: 'Кроссовер/SUV',
  hatchback: 'Хэтчбек',
  wagon: 'Универсал',
  coupe: 'Купе',
  minivan: 'Минивэн',
  pickup: 'Пикап',
  any: 'Любой'
};

const driveLabels = {
  fwd: 'Передний',
  rwd: 'Задний',
  awd: '4WD/AWD',
  any: 'Любой'
};

const mileageLabels = {
  lt20: 'до 20 000 км',
  lt50: 'до 50 000 км',
  lt80: 'до 80 000 км',
  lt100: 'до 100 000 км',
  lt150: 'до 150 000 км',
  any: 'Любой'
};

const colorLabels = {
  white: 'Белый',
  black: 'Чёрный',
  silver: 'Серебристый',
  gray: 'Серый',
  blue: 'Синий',
  red: 'Красный',
  brown: 'Коричневый',
  green: 'Зелёный',
  beige: 'Бежевый',
  any: 'Любой'
};

const timelineLabels = {
  asap: 'Как можно скорее',
  '1month': 'В течение месяца',
  '2_3months': '2-3 месяца',
  '3_6months': '3-6 месяцев',
  'no_rush': 'Не тороплюсь'
};

const conditionLabels = {
  new: 'Новый',
  used: 'С пробегом',
  any: 'Любой'
};

const optionLabels = {
  // Comfort
  heated_seats: 'Подогрев сидений',
  ventilated_seats: 'Вентиляция сидений',
  heated_wheel: 'Подогрев руля',
  panoramic_roof: 'Панорамная крыша',
  sunroof: 'Люк',
  climate_control: 'Климат-контроль',
  rear_climate: 'Задний климат',
  seat_memory: 'Память сидений',
  massage_seats: 'Массаж сидений',
  // Electronic
  cruise_control: 'Круиз-контроль',
  adaptive_cruise: 'Адаптивный круиз',
  lane_assist: 'Ассистент полосы',
  parking_sensors: 'Парктроники',
  camera_360: 'Камера 360°',
  rear_camera: 'Задняя камера',
  blind_spot: 'Мониторинг слепых зон',
  head_up: 'Проекция на лобовое',
  keyless: 'Бесключевой доступ',
  remote_start: 'Дистанционный запуск',
  // Exterior
  led_lights: 'LED фары',
  matrix_lights: 'Матричные фары',
  wheels_r18: 'Диски R18+',
  wheels_r19: 'Диски R19+',
  wheels_r20: 'Диски R20+',
  tinted_windows: 'Тонировка',
  // Other
  spare_wheel: 'Запасное колесо',
  first_aid: 'Аптечка',
  fire_extinguisher: 'Огнетушитель'
};

const clientTypeLabels = {
  individual: 'Физ. лицо',
  company: 'Юр. лицо',
  ip: 'ИП'
};

const priorityLabels = {
  1: 'Не важно',
  2: 'Мало важно',
  3: 'Средне',
  4: 'Важно',
  5: 'Очень важно'
};

export default ContractorDashboard;
