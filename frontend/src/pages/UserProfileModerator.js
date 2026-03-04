import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui/tabs";
import { 
  ArrowLeft,
  User,
  Car,
  FileText,
  Gavel,
  Wallet,
  Shield,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Loader2,
  BadgeCheck,
  FileCheck,
  DollarSign,
  Calendar,
  Mail,
  Phone,
  MessageSquare,
  ChevronRight,
  Play,
  Lock,
  Unlock,
  Eye,
  Edit3
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Stage configuration
const stageConfig = {
  verification: { label: 'Верификация', icon: Shield, color: 'text-blue-400' },
  contract: { label: 'Договор', icon: FileText, color: 'text-purple-400' },
  inspection: { label: 'Инспекция', icon: Eye, color: 'text-amber-400' },
  payment: { label: 'Оплата', icon: DollarSign, color: 'text-emerald-400' },
  export: { label: 'Экспорт', icon: Car, color: 'text-cyan-400' },
  logistics: { label: 'Логистика', icon: Car, color: 'text-orange-400' },
  delivery: { label: 'Выдача', icon: CheckCircle2, color: 'text-green-400' }
};

const UserProfileModerator = () => {
  const { userId } = useParams();
  const { token, user: currentUser } = useAuth();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  // Dialog states
  const [documentDialog, setDocumentDialog] = useState(null);
  const [dealDialog, setDealDialog] = useState(null);
  const [actionComment, setActionComment] = useState('');
  const [processing, setProcessing] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchUserData = async () => {
    try {
      const response = await axios.get(`${API}/moderator/users/${userId}/full-profile`, { headers });
      setUserData(response.data);
    } catch (error) {
      console.error('Error fetching user data:', error);
      toast.error('Ошибка загрузки данных пользователя');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, [userId]);

  // Sign contract
  const handleSignContract = async (action) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/moderator/users/${userId}/sign-contract`, { action }, { headers });
      toast.success(action === 'approve' ? 'Договор подписан' : 'Договор отклонён');
      fetchUserData();
    } catch (error) {
      toast.error('Ошибка при работе с договором');
    } finally {
      setProcessing(false);
    }
  };

  // Verify document
  const handleVerifyDocument = async (docId, action) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/moderator/documents/${docId}/verify`, {
        action,
        comment: actionComment
      }, { headers });
      
      toast.success(action === 'approve' ? 'Документ проверен' : 'Документ отклонён');
      setDocumentDialog(null);
      setActionComment('');
      fetchUserData();
    } catch (error) {
      toast.error('Ошибка при проверке документа');
    } finally {
      setProcessing(false);
    }
  };

  // Approve deal stage
  const handleApproveDealStage = async (dealId, action) => {
    setProcessing(true);
    try {
      const response = await axios.post(`${API}/moderator/deals/${dealId}/approve-stage`, {
        action,
        comment: actionComment
      }, { headers });
      
      toast.success(response.data.message);
      setDealDialog(null);
      setActionComment('');
      fetchUserData();
    } catch (error) {
      toast.error('Ошибка при одобрении этапа');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center">
        <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
      </div>
    );
  }

  if (!userData) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle size={48} className="mx-auto mb-4 text-amber-400" />
          <p className="text-white text-lg">Пользователь не найден</p>
          <Link to="/moderator">
            <Button className="mt-4">Вернуться</Button>
          </Link>
        </div>
      </div>
    );
  }

  const { user, account, cars, tenders, documents, deals, affiliate } = userData;

  return (
    <div className="min-h-screen bg-[#0B0F14] py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link to="/moderator">
              <Button variant="ghost" className="text-slate-400 hover:text-white">
                <ArrowLeft size={20} className="mr-2" />
                Назад
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                {user.name}
                {account?.is_verified && (
                  <BadgeCheck size={24} className="text-[#00E5FF]" />
                )}
              </h1>
              <p className="text-slate-400">{user.email}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-slate-400 text-sm">Баланс</p>
              <p className="text-[#00E5FF] text-xl font-bold">${account?.balance?.toFixed(2) || '0.00'}</p>
            </div>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {/* Verification Status */}
          <div className={`p-4 rounded-sm border ${
            account?.is_verified 
              ? 'bg-emerald-500/10 border-emerald-500/30' 
              : 'bg-amber-500/10 border-amber-500/30'
          }`}>
            <Shield size={20} className={`mb-2 ${account?.is_verified ? 'text-emerald-400' : 'text-amber-400'}`} />
            <p className="text-slate-400 text-xs">Верификация</p>
            <p className={`font-semibold ${account?.is_verified ? 'text-emerald-400' : 'text-amber-400'}`}>
              {account?.is_verified ? 'Подтверждён' : 'Ожидает'}
            </p>
          </div>

          {/* Contract Status */}
          <div className={`p-4 rounded-sm border ${
            account?.contract_signed 
              ? 'bg-purple-500/10 border-purple-500/30' 
              : 'bg-slate-500/10 border-slate-500/30'
          }`}>
            <div className="flex items-center justify-between mb-2">
              <FileText size={20} className={account?.contract_signed ? 'text-purple-400' : 'text-slate-400'} />
              {account?.is_verified && !account?.contract_signed && (
                <Button
                  size="sm"
                  onClick={() => handleSignContract('approve')}
                  disabled={processing}
                  className="bg-purple-500 hover:bg-purple-600 text-white text-xs"
                >
                  Подписать
                </Button>
              )}
            </div>
            <p className="text-slate-400 text-xs">Договор</p>
            <p className={`font-semibold ${account?.contract_signed ? 'text-purple-400' : 'text-slate-400'}`}>
              {account?.contract_signed ? 'Подписан' : 'Не подписан'}
            </p>
          </div>

          {/* Cars Count */}
          <div className="p-4 rounded-sm border bg-[#00E5FF]/10 border-[#00E5FF]/30">
            <Car size={20} className="text-[#00E5FF] mb-2" />
            <p className="text-slate-400 text-xs">Авто в гараже</p>
            <p className="text-[#00E5FF] font-semibold text-xl">{cars?.length || 0}</p>
          </div>

          {/* Active Deals */}
          <div className="p-4 rounded-sm border bg-orange-500/10 border-orange-500/30">
            <Gavel size={20} className="text-orange-400 mb-2" />
            <p className="text-slate-400 text-xs">Активных сделок</p>
            <p className="text-orange-400 font-semibold text-xl">
              {deals?.filter(d => d.status === 'active').length || 0}
            </p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-[#15191E] p-1 mb-6">
            <TabsTrigger value="overview" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              Обзор
            </TabsTrigger>
            <TabsTrigger value="documents" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              Документы ({documents?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="deals" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              Сделки ({deals?.length || 0})
            </TabsTrigger>
            <TabsTrigger value="cars" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              Гараж ({cars?.length || 0})
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview">
            <div className="grid md:grid-cols-2 gap-6">
              {/* User Info */}
              <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <User size={18} />
                  Информация о пользователе
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <Mail size={16} className="text-slate-400" />
                    <span className="text-white">{user.email}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Calendar size={16} className="text-slate-400" />
                    <span className="text-slate-300">
                      Регистрация: {new Date(user.created_at).toLocaleDateString('ru-RU')}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <Shield size={16} className="text-slate-400" />
                    <span className={`${
                      user.role === 'admin' ? 'text-amber-400' :
                      user.role === 'moderator' ? 'text-purple-400' : 'text-slate-300'
                    }`}>
                      Роль: {user.role === 'admin' ? 'Администратор' : 
                             user.role === 'moderator' ? 'Модератор' : 'Пользователь'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Account Status */}
              <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                  <Wallet size={18} />
                  Состояние аккаунта
                </h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Баланс:</span>
                    <span className="text-[#00E5FF] font-bold">${account?.balance?.toFixed(2) || '0.00'}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Верификация:</span>
                    {account?.is_verified ? (
                      <span className="flex items-center gap-1 text-emerald-400">
                        <CheckCircle2 size={14} /> Подтверждён
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-400">
                        <Clock size={14} /> Ожидает
                      </span>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Договор:</span>
                    {account?.contract_signed ? (
                      <span className="flex items-center gap-1 text-purple-400">
                        <FileCheck size={14} /> Подписан
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-slate-500">
                        <XCircle size={14} /> Не подписан
                      </span>
                    )}
                  </div>
                  {account?.verification_date && (
                    <div className="pt-3 border-t border-[#27272A]">
                      <p className="text-slate-500 text-xs">
                        Верифицирован: {new Date(account.verification_date).toLocaleString('ru-RU')}
                      </p>
                      {account.verified_by_name && (
                        <p className="text-slate-500 text-xs">
                          Модератор: {account.verified_by_name}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </div>

              {/* Affiliate Info */}
              {affiliate && (
                <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6 md:col-span-2">
                  <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <BadgeCheck size={18} className="text-emerald-400" />
                    Партнёрская программа
                    {affiliate.is_partner && (
                      <span className="px-2 py-0.5 bg-amber-500/20 text-amber-400 text-xs rounded-full">
                        Партнёр
                      </span>
                    )}
                  </h3>
                  <div className="grid grid-cols-4 gap-4">
                    <div>
                      <p className="text-slate-400 text-xs">Рефералов</p>
                      <p className="text-white font-semibold">{affiliate.total_referrals}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Сделок</p>
                      <p className="text-white font-semibold">{affiliate.completed_deals}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Заработано</p>
                      <p className="text-emerald-400 font-semibold">${affiliate.total_earnings?.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-slate-400 text-xs">Реф. код</p>
                      <p className="text-[#00E5FF] font-mono">{affiliate.referral_code}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </TabsContent>

          {/* Documents Tab */}
          <TabsContent value="documents">
            {documents?.length > 0 ? (
              <div className="space-y-4">
                {documents.map((doc) => (
                  <div 
                    key={doc.id}
                    className={`bg-[#15191E] border rounded-sm p-4 ${
                      doc.is_verified 
                        ? 'border-emerald-500/30' 
                        : 'border-[#27272A]'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <FileText size={20} className={doc.is_verified ? 'text-emerald-400' : 'text-slate-400'} />
                        <div>
                          <p className="text-white font-medium">{doc.name || doc.type}</p>
                          <p className="text-slate-500 text-sm">
                            Загружен: {new Date(doc.created_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        {doc.is_verified ? (
                          <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 rounded-full">
                            <CheckCircle2 size={14} className="text-emerald-400" />
                            <span className="text-emerald-400 text-sm">Проверено</span>
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            onClick={() => setDocumentDialog(doc)}
                            className="bg-emerald-500 hover:bg-emerald-600 text-white"
                          >
                            <FileCheck size={14} className="mr-1" />
                            Проверить
                          </Button>
                        )}
                      </div>
                    </div>
                    
                    {doc.is_verified && doc.verified_by_name && (
                      <div className="mt-3 pt-3 border-t border-[#27272A] flex items-center gap-2">
                        <CheckCircle2 size={12} className="text-emerald-400" />
                        <span className="text-slate-500 text-xs">
                          Проверил: {doc.verified_by_name} • {new Date(doc.verified_at).toLocaleString('ru-RU')}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-[#15191E] border border-[#27272A] rounded-sm">
                <FileText size={48} className="mx-auto mb-4 text-slate-600" />
                <p className="text-slate-400">Документы не загружены</p>
              </div>
            )}
          </TabsContent>

          {/* Deals Tab */}
          <TabsContent value="deals">
            {deals?.length > 0 ? (
              <div className="space-y-4">
                {deals.map((deal) => {
                  const currentStage = stageConfig[deal.current_stage] || stageConfig.verification;
                  const StageIcon = currentStage.icon;
                  
                  return (
                    <div 
                      key={deal.id}
                      className="bg-[#15191E] border border-[#27272A] rounded-sm p-4"
                    >
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h4 className="text-white font-semibold">
                            {deal.car_info?.brand} {deal.car_info?.model}
                          </h4>
                          <p className="text-slate-400 text-sm">
                            Сделка #{deal.id.slice(0, 8)} • Создана: {new Date(deal.created_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-full text-xs ${
                            deal.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                            deal.status === 'active' ? 'bg-blue-500/10 text-blue-400' :
                            'bg-slate-500/10 text-slate-400'
                          }`}>
                            {deal.status === 'completed' ? 'Завершена' :
                             deal.status === 'active' ? 'Активна' : deal.status}
                          </span>
                        </div>
                      </div>

                      {/* Stages Progress */}
                      <div className="mb-4">
                        <p className="text-slate-400 text-xs mb-2">Текущий этап:</p>
                        <div className="flex items-center gap-2">
                          <StageIcon size={16} className={currentStage.color} />
                          <span className={`font-medium ${currentStage.color}`}>
                            {currentStage.label}
                          </span>
                          {!deal.can_proceed && deal.status === 'active' && (
                            <span className="flex items-center gap-1 px-2 py-0.5 bg-amber-500/10 text-amber-400 text-xs rounded">
                              <Lock size={10} />
                              Ожидает одобрения
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Stage Indicators */}
                      <div className="flex items-center gap-1 mb-4">
                        {Object.entries(stageConfig).map(([key, config], idx) => {
                          const stageData = deal.stages?.[key] || {};
                          const isCompleted = stageData.moderator_approved;
                          const isCurrent = deal.current_stage === key;
                          
                          return (
                            <div
                              key={key}
                              className={`flex-1 h-2 rounded-full ${
                                isCompleted ? 'bg-emerald-500' :
                                isCurrent ? 'bg-amber-500' :
                                'bg-[#27272A]'
                              }`}
                              title={config.label}
                            />
                          );
                        })}
                      </div>

                      {/* Action Button */}
                      {deal.status === 'active' && !deal.can_proceed && (
                        <Button
                          onClick={() => setDealDialog(deal)}
                          className="w-full bg-emerald-500 hover:bg-emerald-600 text-white"
                        >
                          <Play size={14} className="mr-2" />
                          Одобрить этап "{currentStage.label}"
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-12 bg-[#15191E] border border-[#27272A] rounded-sm">
                <Gavel size={48} className="mx-auto mb-4 text-slate-600" />
                <p className="text-slate-400">Сделок нет</p>
              </div>
            )}
          </TabsContent>

          {/* Cars Tab */}
          <TabsContent value="cars">
            {cars?.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {cars.map((car) => (
                  <div 
                    key={car.id}
                    className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden"
                  >
                    <div className="h-32 bg-[#1C2128] flex items-center justify-center">
                      {car.image_url ? (
                        <img src={car.image_url} alt={`${car.brand} ${car.model}`} className="w-full h-full object-cover" />
                      ) : (
                        <Car size={32} className="text-slate-600" />
                      )}
                    </div>
                    <div className="p-4">
                      <h4 className="text-white font-semibold">{car.brand} {car.model}</h4>
                      <p className="text-slate-400 text-sm">{car.year} • ¥{car.price_cny?.toLocaleString()}</p>
                      {car.calculated_price_usd && (
                        <p className="text-[#00E5FF] font-medium mt-1">
                          ${car.calculated_price_usd.toLocaleString()} под ключ
                        </p>
                      )}
                      <div className="mt-2">
                        <span className={`px-2 py-0.5 rounded text-xs ${
                          car.status === 'in_deal' ? 'bg-orange-500/10 text-orange-400' :
                          car.status === 'saved' ? 'bg-blue-500/10 text-blue-400' :
                          'bg-slate-500/10 text-slate-400'
                        }`}>
                          {car.status === 'in_deal' ? 'В сделке' :
                           car.status === 'saved' ? 'Сохранён' : car.status}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 bg-[#15191E] border border-[#27272A] rounded-sm">
                <Car size={48} className="mx-auto mb-4 text-slate-600" />
                <p className="text-slate-400">Гараж пуст</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>

      {/* Document Verification Dialog */}
      <Dialog open={!!documentDialog} onOpenChange={() => setDocumentDialog(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileCheck size={20} className="text-emerald-400" />
              Проверка документа
            </DialogTitle>
          </DialogHeader>
          
          {documentDialog && (
            <div className="space-y-4 mt-4">
              <div className="p-3 bg-[#0B0F14] rounded-sm">
                <p className="text-white font-medium">{documentDialog.name || documentDialog.type}</p>
                <p className="text-slate-400 text-sm">
                  Загружен: {new Date(documentDialog.created_at).toLocaleDateString('ru-RU')}
                </p>
              </div>

              <div>
                <label className="text-slate-300 text-sm">Комментарий</label>
                <Input
                  value={actionComment}
                  onChange={(e) => setActionComment(e.target.value)}
                  placeholder="Комментарий к проверке..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={() => handleVerifyDocument(documentDialog.id, 'approve')}
                  disabled={processing}
                  className="bg-emerald-500 hover:bg-emerald-600 text-white"
                >
                  {processing ? <Loader2 size={16} className="mr-2 animate-spin" /> : <CheckCircle2 size={16} className="mr-2" />}
                  Проверено ✓
                </Button>
                <Button
                  onClick={() => handleVerifyDocument(documentDialog.id, 'reject')}
                  disabled={processing}
                  variant="outline"
                  className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                >
                  <XCircle size={16} className="mr-2" />
                  Отклонить
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Deal Stage Approval Dialog */}
      <Dialog open={!!dealDialog} onOpenChange={() => setDealDialog(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Play size={20} className="text-emerald-400" />
              Одобрение этапа сделки
            </DialogTitle>
          </DialogHeader>
          
          {dealDialog && (
            <div className="space-y-4 mt-4">
              <div className="p-3 bg-[#0B0F14] rounded-sm">
                <p className="text-white font-medium">
                  {dealDialog.car_info?.brand} {dealDialog.car_info?.model}
                </p>
                <p className="text-slate-400 text-sm">Сделка #{dealDialog.id.slice(0, 8)}</p>
              </div>

              <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-sm">
                <p className="text-amber-400 text-sm font-medium">Текущий этап:</p>
                <p className="text-white text-lg">
                  {stageConfig[dealDialog.current_stage]?.label || dealDialog.current_stage}
                </p>
              </div>

              <div>
                <label className="text-slate-300 text-sm">Комментарий</label>
                <Input
                  value={actionComment}
                  onChange={(e) => setActionComment(e.target.value)}
                  placeholder="Комментарий к решению..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <Button
                  onClick={() => handleApproveDealStage(dealDialog.id, 'approve')}
                  disabled={processing}
                  className="bg-emerald-500 hover:bg-emerald-600 text-white"
                >
                  {processing ? <Loader2 size={16} className="mr-2 animate-spin" /> : <Unlock size={16} className="mr-2" />}
                  Одобрить
                </Button>
                <Button
                  onClick={() => handleApproveDealStage(dealDialog.id, 'reject')}
                  disabled={processing}
                  variant="outline"
                  className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                >
                  <Lock size={16} className="mr-2" />
                  Отклонить
                </Button>
              </div>

              <p className="text-slate-500 text-xs text-center">
                После одобрения пользователь сможет перейти к следующему этапу
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UserProfileModerator;
