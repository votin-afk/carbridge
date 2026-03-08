import { useState, useEffect } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { 
  Shield,
  Users,
  FileCheck,
  Gavel,
  CheckCircle2,
  XCircle,
  Clock,
  Eye,
  Phone,
  Mail,
  Building2,
  Loader2,
  AlertCircle,
  ArrowLeft,
  Plus,
  Search,
  Car,
  Play,
  Pause,
  MessageSquare,
  UserCog,
  Crown,
  User,
  Wallet,
  DollarSign,
  PlusCircle,
  MinusCircle,
  FileText,
  Image,
  Download,
  ExternalLink,
  Trash2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusConfig = {
  pending: { label: 'Ожидает', color: 'text-amber-400', bg: 'bg-amber-500/10' },
  reviewing: { label: 'На проверке', color: 'text-blue-400', bg: 'bg-blue-500/10' },
  approved: { label: 'Одобрено', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  rejected: { label: 'Отклонено', color: 'text-red-400', bg: 'bg-red-500/10' }
};

const roleConfig = {
  admin: { label: 'Администратор', color: 'text-amber-400', bg: 'bg-amber-500/10', icon: Crown },
  moderator: { label: 'Модератор', color: 'text-blue-400', bg: 'bg-blue-500/10', icon: Shield },
  user: { label: 'Пользователь', color: 'text-slate-400', bg: 'bg-slate-500/10', icon: User }
};

const dealStages = {
  inspection: { label: 'Проверка', icon: FileCheck },
  export: { label: 'Экспорт', icon: Building2 },
  logistics: { label: 'Логистика', icon: Car },
  customs: { label: 'Растаможка', icon: FileCheck },
  delivery: { label: 'Доставка', icon: Car }
};

const ModeratorPage = () => {
  const { token, user, isModerator, isAdmin } = useAuth();
  const [activeTab, setActiveTab] = useState('applications');
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [applications, setApplications] = useState([]);
  const [deals, setDeals] = useState([]);
  const [tenders, setTenders] = useState([]);
  const [users, setUsers] = useState([]);
  const [verifications, setVerifications] = useState([]);
  const [contractorApplications, setContractorApplications] = useState([]);
  const [pendingStages, setPendingStages] = useState([]);
  
  // Dialog states
  const [selectedApplication, setSelectedApplication] = useState(null);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [selectedVerification, setSelectedVerification] = useState(null);
  const [selectedContractor, setSelectedContractor] = useState(null);
  const [newTenderDialog, setNewTenderDialog] = useState(false);
  const [newTenderData, setNewTenderData] = useState({ brand: '', model: '', budget: '' });
  
  // Balance management states
  const [balanceDialogUser, setBalanceDialogUser] = useState(null);
  const [balanceAmount, setBalanceAmount] = useState('');
  const [balanceReason, setBalanceReason] = useState('');
  const [updatingBalance, setUpdatingBalance] = useState(false);
  const [userAccounts, setUserAccounts] = useState({}); // user_id -> account data
  
  // Delete confirmation dialog state
  const [deleteDialog, setDeleteDialog] = useState(null); // { type: 'user'|'tender'|..., id: string, title: string }
  
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (isModerator) {
      fetchData();
      // Always fetch pending stages count for badge
      fetchPendingStagesCount();
    }
  }, [activeTab, isModerator]);

  const fetchPendingStagesCount = async () => {
    try {
      const response = await axios.get(`${API}/moderator/deals/pending-stages`, { headers });
      setPendingStages(response.data);
    } catch (error) {
      console.error('Error fetching pending stages:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'applications') {
        // Fetch CAR applications (user requests for car selection)
        const response = await axios.get(`${API}/moderator/car-applications`, { headers });
        setApplications(response.data);
      } else if (activeTab === 'deals') {
        const response = await axios.get(`${API}/moderator/deals`, { headers });
        setDeals(response.data);
      } else if (activeTab === 'tenders') {
        const response = await axios.get(`${API}/moderator/tenders`, { headers });
        setTenders(response.data);
      } else if (activeTab === 'users' && isAdmin) {
        const response = await axios.get(`${API}/admin/users`, { headers });
        setUsers(response.data);
      } else if (activeTab === 'documents') {
        const response = await axios.get(`${API}/moderator/verifications/pending`, { headers });
        setVerifications(response.data);
      } else if (activeTab === 'contractors') {
        // Fetch CONTRACTOR applications (not approved contractors)
        const response = await axios.get(`${API}/moderator/contractor-applications`, { headers });
        setContractorApplications(response.data);
      } else if (activeTab === 'stage-moderation') {
        // Fetch pending stage confirmations
        const response = await axios.get(`${API}/moderator/deals/pending-stages`, { headers });
        setPendingStages(response.data);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      // Use demo data if API not ready
      if (activeTab === 'applications') {
        setApplications([]);
      } else if (activeTab === 'deals') {
        setDeals([]);
      } else if (activeTab === 'tenders') {
        setTenders([]);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      await axios.put(`${API}/admin/users/${userId}/role`, { role: newRole }, { headers });
      toast.success('Роль пользователя обновлена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка при обновлении роли');
    }
  };

  const handleConfirmStage = async (dealId, stageKey) => {
    try {
      await axios.post(`${API}/moderator/deals/${dealId}/confirm-stage`, { stage: stageKey }, { headers });
      toast.success('Этап подтверждён');
      // Refresh pending stages
      const response = await axios.get(`${API}/moderator/deals/pending-stages`, { headers });
      setPendingStages(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка подтверждения этапа');
    }
  };

  const openBalanceDialog = async (user) => {
    setBalanceDialogUser(user);
    setBalanceAmount('');
    setBalanceReason('');
    
    // Fetch user account data
    try {
      const response = await axios.get(`${API}/admin/users/${user.id}/account`, { headers });
      setUserAccounts(prev => ({
        ...prev,
        [user.id]: response.data.account
      }));
    } catch (error) {
      console.error('Error fetching user account:', error);
    }
  };

  const handleUpdateBalance = async (isAdd = true) => {
    if (!balanceAmount || parseFloat(balanceAmount) <= 0) {
      toast.error('Введите сумму');
      return;
    }

    setUpdatingBalance(true);
    try {
      const amount = isAdd ? parseFloat(balanceAmount) : -parseFloat(balanceAmount);
      const response = await axios.post(`${API}/admin/users/${balanceDialogUser.id}/balance`, {
        amount,
        reason: balanceReason || null
      }, { headers });
      
      toast.success(`Баланс ${isAdd ? 'начислен' : 'списан'}: $${balanceAmount}`);
      
      // Update local cache
      setUserAccounts(prev => ({
        ...prev,
        [balanceDialogUser.id]: {
          ...prev[balanceDialogUser.id],
          balance: response.data.new_balance
        }
      }));
      
      setBalanceDialogUser(null);
    } catch (error) {
      const message = error.response?.data?.detail || 'Ошибка при изменении баланса';
      toast.error(message);
    } finally {
      setUpdatingBalance(false);
    }
  };

  const handleApproveApplication = async (appId) => {
    try {
      await axios.post(`${API}/moderator/applications/${appId}/approve`, {}, { headers });
      toast.success('Заявка одобрена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка при одобрении');
    }
    setSelectedApplication(null);
  };

  const handleRejectApplication = async (appId) => {
    try {
      await axios.post(`${API}/moderator/applications/${appId}/reject`, {}, { headers });
      toast.success('Заявка отклонена');
      fetchData();
    } catch (error) {
      toast.error('Ошибка при отклонении');
    }
    setSelectedApplication(null);
  };

  const handleApproveContractor = async (contractorId) => {
    try {
      const response = await axios.post(`${API}/moderator/contractors/${contractorId}/approve`, { verified: true }, { headers });
      if (response.data.temp_password) {
        toast.success(`Подрядчик одобрен! Временный пароль: ${response.data.temp_password}`);
      } else {
        toast.success('Подрядчик одобрен! Он может войти с паролем, указанным при регистрации');
      }
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при одобрении подрядчика');
    }
    setSelectedContractor(null);
  };

  const handleRejectContractor = async (contractorId) => {
    try {
      await axios.post(`${API}/moderator/contractors/${contractorId}/reject`, {}, { headers });
      toast.success('Подрядчик отклонён');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при отклонении подрядчика');
    }
    setSelectedContractor(null);
  };

  // ==================== DELETE HANDLERS ====================
  
  // Show delete confirmation dialog
  const showDeleteDialog = (type, id, title) => {
    setDeleteDialog({ type, id, title });
  };

  // Execute delete after confirmation
  const executeDelete = async () => {
    if (!deleteDialog) return;
    
    const { type, id } = deleteDialog;
    
    try {
      switch (type) {
        case 'user':
          await axios.delete(`${API}/moderator/users/${id}`, { headers });
          toast.success('Пользователь удалён');
          setUsers(prev => prev.filter(u => u.id !== id));
          break;
        case 'tender':
          await axios.delete(`${API}/moderator/tenders/${id}`, { headers });
          toast.success('Тендер удалён');
          setTenders(prev => prev.filter(t => t.id !== id));
          break;
        case 'garage':
          await axios.delete(`${API}/moderator/garage/${id}`, { headers });
          toast.success('Авто удалено из гаража');
          fetchData();
          break;
        case 'contractor':
          await axios.delete(`${API}/moderator/contractors/${id}`, { headers });
          toast.success('Подрядчик удалён');
          setContractorApplications(prev => prev.filter(c => c.id !== id));
          break;
        case 'deal':
          await axios.delete(`${API}/moderator/deals/${id}`, { headers });
          toast.success('Сделка отменена');
          setDeals(prev => prev.filter(d => d.id !== id));
          break;
        case 'application':
          await axios.delete(`${API}/moderator/car-applications/${id}`, { headers });
          toast.success('Заявка удалена');
          setApplications(prev => prev.filter(app => app.id !== id));
          break;
        default:
          console.error('Unknown delete type:', type);
      }
    } catch (error) {
      console.error('Delete error:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при удалении');
    } finally {
      setDeleteDialog(null);
    }
  };

  // Wrapper functions for UI
  const handleDeleteUser = (userId) => showDeleteDialog('user', userId, 'Удалить пользователя и все его данные?');
  const handleDeleteTender = (tenderId) => showDeleteDialog('tender', tenderId, 'Удалить тендер?');
  const handleDeleteGarageItem = (garageId) => showDeleteDialog('garage', garageId, 'Удалить авто из гаража?');
  const handleDeleteContractor = (contractorId) => showDeleteDialog('contractor', contractorId, 'Удалить подрядчика?');
  const handleDeleteDeal = (dealId) => showDeleteDialog('deal', dealId, 'Отменить сделку?');
  const handleDeleteCarApplication = (appId) => showDeleteDialog('application', appId, 'Удалить заявку на подбор авто?');

  const handleConfirmStage = async (dealId, stage) => {
    try {
      await axios.post(`${API}/moderator/deals/${dealId}/confirm-stage`, { stage }, { headers });
      toast.success(`Этап "${dealStages[stage]?.label}" подтвержден`);
      fetchData();
    } catch (error) {
      toast.error('Ошибка при подтверждении');
    }
  };

  const handleApproveVerification = async (verificationId) => {
    try {
      await axios.post(`${API}/moderator/verifications/${verificationId}/review`, {
        action: 'approve',
        comment: ''
      }, { headers });
      toast.success('Верификация подтверждена');
      fetchData();
      setSelectedVerification(null);
    } catch (error) {
      toast.error('Ошибка при подтверждении');
    }
  };

  const handleRejectVerification = async (verificationId) => {
    try {
      await axios.post(`${API}/moderator/verifications/${verificationId}/review`, {
        action: 'reject',
        comment: ''
      }, { headers });
      toast.success('Верификация отклонена');
      fetchData();
      setSelectedVerification(null);
    } catch (error) {
      toast.error('Ошибка при отклонении');
    }
  };

  const handleVerifyDocument = async (verificationId, docId, action) => {
    try {
      await axios.post(`${API}/moderator/verifications/${verificationId}/documents/${docId}/verify`, {
        action,
        comment: ''
      }, { headers });
      toast.success(`Документ ${action === 'approve' ? 'подтверждён' : 'отклонён'}`);
      // Refresh verification data
      const response = await axios.get(`${API}/moderator/verifications/${verificationId}`, { headers });
      setSelectedVerification(response.data);
      fetchData();
    } catch (error) {
      toast.error('Ошибка при проверке документа');
    }
  };

  const handleCreateTender = async () => {
    if (!newTenderData.brand || !newTenderData.model) {
      toast.error('Заполните марку и модель');
      return;
    }
    
    try {
      await axios.post(`${API}/moderator/tenders`, newTenderData, { headers });
      toast.success('Тендер создан');
      setNewTenderDialog(false);
      setNewTenderData({ brand: '', model: '', budget: '' });
      fetchData();
    } catch (error) {
      toast.error('Ошибка при создании тендера');
    }
  };

  if (!token) {
    return <Navigate to="/auth" replace />;
  }

  if (!isModerator && !isAdmin) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center">
        <div className="text-center">
          <Shield size={64} className="mx-auto mb-4 text-slate-600" />
          <h1 className="text-2xl font-bold text-white mb-2">Доступ запрещен</h1>
          <p className="text-slate-400 mb-6">У вас нет прав для просмотра этой страницы</p>
          <Link to="/">
            <Button className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
              На главную
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F14] py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link to="/">
              <Button variant="ghost" className="text-slate-400 hover:text-white">
                <ArrowLeft size={18} className="mr-2" />
                На главную
              </Button>
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-2">
                <Shield size={24} className="text-[#00E5FF]" />
                Панель модератора
              </h1>
              <p className="text-slate-400 text-sm">Управление платформой CARBRIDGE</p>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard 
            icon={Users} 
            label="Заявки подрядчиков" 
            value={applications.filter(a => a.status === 'pending').length}
            color="amber"
          />
          <StatCard 
            icon={FileCheck} 
            label="Активные сделки" 
            value={deals.filter(d => d.status === 'in_progress').length}
            color="blue"
          />
          <StatCard 
            icon={Gavel} 
            label="Активные тендеры" 
            value={tenders.filter(t => t.status === 'active').length}
            color="emerald"
          />
          <StatCard 
            icon={CheckCircle2} 
            label="Завершено сегодня" 
            value={deals.filter(d => d.status === 'completed').length}
            color="cyan"
          />
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-[#15191E] p-1 mb-6 flex-wrap">
            <TabsTrigger value="applications" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <Car size={16} className="mr-2" />
              Заявки на авто
            </TabsTrigger>
            <TabsTrigger value="contractors" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <Building2 size={16} className="mr-2" />
              Подрядчики
              {contractorApplications.filter(c => c.status === 'pending').length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-amber-500 text-black text-xs rounded-full">
                  {contractorApplications.filter(c => c.status === 'pending').length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="deals" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <FileCheck size={16} className="mr-2" />
              Сделки
            </TabsTrigger>
            <TabsTrigger value="stage-moderation" className="data-[state=active]:bg-purple-500 data-[state=active]:text-white">
              <Shield size={16} className="mr-2" />
              Модерация этапов
              {pendingStages.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-purple-600 text-white text-xs rounded-full">
                  {pendingStages.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="tenders" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <Gavel size={16} className="mr-2" />
              Тендеры
            </TabsTrigger>
            <TabsTrigger value="documents" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <FileText size={16} className="mr-2" />
              Документы
              {verifications.length > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-red-500 text-white text-xs rounded-full">
                  {verifications.length}
                </span>
              )}
            </TabsTrigger>
            {isAdmin && (
              <TabsTrigger value="users" className="data-[state=active]:bg-amber-500 data-[state=active]:text-black">
                <UserCog size={16} className="mr-2" />
                Пользователи
              </TabsTrigger>
            )}
          </TabsList>

          {/* Applications Tab - User Car Applications */}
          <TabsContent value="applications">
            {loading ? (
              <LoadingState />
            ) : applications.length > 0 ? (
              <div className="space-y-4">
                {applications.map(app => (
                  <div 
                    key={app.id} 
                    className="bg-[#15191E] border border-[#27272A] rounded-sm p-4"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                          <Car size={24} className="text-[#00E5FF]" />
                        </div>
                        <div>
                          <h3 className="text-white font-medium">
                            {app.car_params?.brand || 'Любая марка'} {app.car_params?.model || ''}
                          </h3>
                          <p className="text-slate-400 text-sm">
                            Клиент: {app.user_name || app.client_data?.full_name || 'Не указан'}
                          </p>
                          <p className="text-slate-500 text-xs">
                            {app.user_email || app.client_data?.email || ''}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          app.status === 'pending' ? 'bg-amber-500/10 text-amber-400' :
                          app.status === 'approved' ? 'bg-emerald-500/10 text-emerald-400' :
                          app.status === 'rejected' ? 'bg-red-500/10 text-red-400' :
                          'bg-slate-500/10 text-slate-400'
                        }`}>
                          {app.status === 'pending' ? 'Ожидает' : 
                           app.status === 'approved' ? 'Одобрена' :
                           app.status === 'rejected' ? 'Отклонена' : app.status}
                        </span>
                      </div>
                    </div>
                    
                    <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-slate-500">Бюджет:</span>
                        <p className="text-white">
                          {app.budget_terms?.budget_from && app.budget_terms?.budget_to 
                            ? `${app.budget_terms.budget_from} - ${app.budget_terms.budget_to} ${app.budget_terms.currency || 'USD'}`
                            : 'Не указан'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-500">Год:</span>
                        <p className="text-white">
                          {app.car_params?.year_from ? `от ${app.car_params.year_from}` : 'Любой'}
                        </p>
                      </div>
                      <div>
                        <span className="text-slate-500">Кузов:</span>
                        <p className="text-white">{app.car_params?.body_type || 'Любой'}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Создана:</span>
                        <p className="text-white">
                          {app.created_at ? new Date(app.created_at).toLocaleDateString('ru') : '—'}
                        </p>
                      </div>
                    </div>
                    
                    <div className="mt-4 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedApplication(app)}
                        className="border-[#27272A] text-slate-300"
                      >
                        <Eye size={14} className="mr-1" />
                        Подробнее
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteCarApplication(app.id);
                        }}
                        className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                      >
                        <Trash2 size={14} className="mr-1" />
                        Удалить
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет заявок на подбор авто" />
            )}
          </TabsContent>

          {/* Contractors Tab */}
          <TabsContent value="contractors">
            {loading ? (
              <LoadingState />
            ) : contractorApplications.length > 0 ? (
              <div className="space-y-4">
                {contractorApplications.map(contractor => (
                  <div
                    key={contractor.id}
                    className="bg-[#15191E] border border-[#27272A] rounded-sm p-4"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                          <Building2 size={24} className="text-[#00E5FF]" />
                        </div>
                        <div>
                          <h3 className="text-white font-medium">{contractor.company_name}</h3>
                          <div className="flex items-center gap-2 text-slate-400 text-sm">
                            <span>{contractor.country === 'CN' ? '🇨🇳 Китай' : '🇧🇾 Беларусь'}</span>
                            <span>•</span>
                            <span>{contractor.contact_person}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-3 py-1 rounded-full text-sm ${
                          contractor.status === 'pending' 
                            ? 'bg-amber-500/10 text-amber-400' 
                            : contractor.status === 'approved'
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-red-500/10 text-red-400'
                        }`}>
                          {contractor.status === 'pending' ? 'Ожидает' : contractor.status === 'approved' ? 'Одобрен' : 'Отклонён'}
                        </span>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => setSelectedContractor(contractor)}
                          className="border-[#27272A] text-slate-300"
                        >
                          <Eye size={14} className="mr-1" />
                          Детали
                        </Button>
                        {contractor.status === 'pending' && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleApproveContractor(contractor.id)}
                              className="bg-emerald-500 hover:bg-emerald-600 text-white"
                            >
                              <CheckCircle2 size={14} className="mr-1" />
                              Одобрить
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleRejectContractor(contractor.id)}
                              className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                            >
                              <XCircle size={14} className="mr-1" />
                              Отклонить
                            </Button>
                          </>
                        )}
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            handleDeleteContractor(contractor.id);
                          }}
                          className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                        >
                          <Trash2 size={14} />
                        </Button>
                      </div>
                    </div>
                    
                    {/* Services */}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {(Array.isArray(contractor.services) ? contractor.services : (contractor.services || '').split(',').filter(Boolean)).map(service => {
                        const serviceLabels = {
                          inspection: 'Инспекция',
                          export: 'Экспорт',
                          logistics: 'Логистика',
                          purchase: 'Выкуп авто',
                          leasing: 'Лизинг',
                          customs: 'Растаможка'
                        };
                        return (
                          <span
                            key={service}
                            className="px-2 py-1 bg-[#00E5FF]/10 text-[#00E5FF] text-xs rounded-sm"
                          >
                            {serviceLabels[service] || service}
                          </span>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет заявок от подрядчиков" />
            )}
          </TabsContent>

          {/* Deals Tab */}
          <TabsContent value="deals">
            {loading ? (
              <LoadingState />
            ) : deals.length > 0 ? (
              <div className="space-y-4">
                {deals.map(deal => (
                  <div key={deal.id} className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                          <Car size={24} className="text-[#00E5FF]" />
                        </div>
                        <div>
                          <h3 className="text-white font-medium">{deal.car_brand} {deal.car_model}</h3>
                          <p className="text-slate-400 text-sm">Клиент: {deal.client_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[#00E5FF] font-bold">${deal.amount?.toLocaleString() || 0}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          deal.status === 'in_progress' ? 'bg-blue-500/10 text-blue-400' :
                          deal.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                          'bg-amber-500/10 text-amber-400'
                        }`}>
                          {deal.status === 'in_progress' ? 'В работе' : 
                           deal.status === 'completed' ? 'Завершена' : 'Тендер'}
                        </span>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center gap-2">
                      <span className="text-slate-500 text-sm">Текущий этап:</span>
                      <span className="text-white text-sm">{dealStages[deal.current_stage]?.label || deal.current_stage}</span>
                    </div>
                    <div className="mt-3 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setSelectedDeal(deal)}
                        className="border-[#27272A] text-slate-300"
                      >
                        <Eye size={14} className="mr-1" />
                        Детали
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteDeal(deal.id);
                        }}
                        className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                      >
                        <Trash2 size={14} className="mr-1" />
                        Отменить сделку
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет активных сделок" />
            )}
          </TabsContent>

          {/* Stage Moderation Tab */}
          <TabsContent value="stage-moderation">
            {loading ? (
              <LoadingState />
            ) : pendingStages.length > 0 ? (
              <div className="space-y-4">
                <div className="p-4 bg-purple-500/10 border border-purple-500/30 rounded-lg mb-4">
                  <h3 className="text-purple-300 font-medium flex items-center gap-2">
                    <Shield size={18} />
                    Этапы сделок, требующие подтверждения
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">
                    После подтверждения этапа клиент сможет оплатить его
                  </p>
                </div>

                {pendingStages.map((item, idx) => {
                  const stageLabels = {
                    leasing: 'Лизинг',
                    inspection: 'Инспекция авто',
                    export: 'Выкуп и экспорт',
                    logistics_china: 'Доставка до порта (Китай)',
                    insurance: 'Страхование авто',
                    delivery_rb: 'Доставка в Беларусь',
                    customs: 'Таможенное оформление',
                    completion: 'Завершение сделки'
                  };
                  
                  return (
                    <div key={`${item.deal_id}-${item.stage_key}-${idx}`} className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className="w-12 h-12 bg-purple-500/20 rounded-full flex items-center justify-center">
                            <FileCheck size={24} className="text-purple-400" />
                          </div>
                          <div>
                            <h4 className="text-white font-medium">
                              {item.car_info?.brand} {item.car_info?.model}
                            </h4>
                            <p className="text-slate-400 text-sm">
                              Сделка #{item.deal_id?.slice(0, 8)}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <span className="px-3 py-1 bg-purple-500/10 text-purple-400 rounded-full text-sm">
                            {stageLabels[item.stage_key] || item.stage_key}
                          </span>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4 text-sm">
                        <div className="bg-[#0B0F14] p-3 rounded">
                          <p className="text-slate-500 text-xs">Клиент</p>
                          <p className="text-white">{item.user?.name || item.user?.email || '—'}</p>
                        </div>
                        <div className="bg-[#0B0F14] p-3 rounded">
                          <p className="text-slate-500 text-xs">Подрядчик</p>
                          <p className="text-purple-300">{item.contractor_name || '—'}</p>
                        </div>
                        <div className="bg-[#0B0F14] p-3 rounded">
                          <p className="text-slate-500 text-xs">Цена этапа</p>
                          <p className="text-[#00E5FF] font-medium">${item.price?.toLocaleString() || '0'}</p>
                        </div>
                        <div className="bg-[#0B0F14] p-3 rounded">
                          <p className="text-slate-500 text-xs">Дата создания</p>
                          <p className="text-slate-300">{item.created_at ? new Date(item.created_at).toLocaleDateString('ru-RU') : '—'}</p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <Button
                          onClick={() => handleConfirmStage(item.deal_id, item.stage_key)}
                          className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
                        >
                          <CheckCircle2 size={16} className="mr-2" />
                          Подтвердить этап
                        </Button>
                        <Button
                          variant="outline"
                          className="border-slate-500 text-slate-400"
                        >
                          <Eye size={16} className="mr-2" />
                          Подробнее
                        </Button>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <EmptyState text="Нет этапов для подтверждения" />
            )}
          </TabsContent>

          {/* Tenders Tab */}
          <TabsContent value="tenders">
            <div className="flex justify-end mb-4">
              <Button 
                onClick={() => setNewTenderDialog(true)}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                <Plus size={18} className="mr-2" />
                Создать тендер
              </Button>
            </div>
            
            {loading ? (
              <LoadingState />
            ) : tenders.length > 0 ? (
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {tenders.map(tender => (
                  <div key={tender.id} className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-[#00E5FF] text-xs">#{tender.id?.slice(0, 8)}</span>
                      <span className={`px-2 py-1 rounded text-xs ${
                        tender.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' :
                        tender.status === 'closed' ? 'bg-slate-500/10 text-slate-400' :
                        'bg-amber-500/10 text-amber-400'
                      }`}>
                        {tender.status === 'active' ? 'Активен' : 
                         tender.status === 'closed' ? 'Закрыт' : tender.status}
                      </span>
                    </div>
                    <h3 className="text-white font-medium mb-1">{tender.car_brand} {tender.car_model}</h3>
                    <p className="text-slate-400 text-sm mb-3">
                      Бюджет: до ${tender.budget?.toLocaleString() || '—'}
                    </p>
                    <p className="text-slate-500 text-xs mb-3">
                      Предложений: {tender.offers_count || 0}
                    </p>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 border-[#27272A] text-slate-300"
                      >
                        <Eye size={14} className="mr-1" />
                        Детали
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant="outline"
                        onClick={(e) => {
                          e.preventDefault();
                          e.stopPropagation();
                          handleDeleteTender(tender.id);
                        }}
                        className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                      >
                        <Trash2 size={14} />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState text="Нет активных тендеров" />
            )}
          </TabsContent>

          {/* Documents/Verifications Tab */}
          <TabsContent value="documents">
            {loading ? (
              <LoadingState />
            ) : verifications.length > 0 ? (
              <div className="space-y-4">
                {verifications.map(verification => (
                  <VerificationCard
                    key={verification.id}
                    verification={verification}
                    onView={() => setSelectedVerification(verification)}
                    onApprove={() => handleApproveVerification(verification.id)}
                    onReject={() => handleRejectVerification(verification.id)}
                  />
                ))}
              </div>
            ) : (
              <EmptyState text="Нет документов на проверку" />
            )}
          </TabsContent>

          {/* Users Tab (Admin Only) */}
          {isAdmin && (
            <TabsContent value="users">
              {loading ? (
                <LoadingState />
              ) : users.length > 0 ? (
                <div className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden overflow-x-auto">
                  <table className="w-full min-w-[900px]">
                    <thead className="bg-[#0B0F14]">
                      <tr>
                        <th className="text-left text-slate-400 text-sm font-medium p-4">Пользователь</th>
                        <th className="text-left text-slate-400 text-sm font-medium p-4">Email</th>
                        <th className="text-left text-slate-400 text-sm font-medium p-4">Роль</th>
                        <th className="text-left text-slate-400 text-sm font-medium p-4">Баланс</th>
                        <th className="text-left text-slate-400 text-sm font-medium p-4">Дата регистрации</th>
                        <th className="text-left text-slate-400 text-sm font-medium p-4">Действия</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map(u => {
                        const role = roleConfig[u.role] || roleConfig.user;
                        const RoleIcon = role.icon;
                        const userAccount = userAccounts[u.id];
                        return (
                          <tr key={u.id} className="border-t border-[#27272A] hover:bg-[#1C2128]">
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className={`w-8 h-8 rounded-full ${role.bg} flex items-center justify-center`}>
                                  <RoleIcon size={16} className={role.color} />
                                </div>
                                <span className="text-white font-medium">{u.name}</span>
                              </div>
                            </td>
                            <td className="p-4 text-slate-400">{u.email}</td>
                            <td className="p-4">
                              <span className={`px-2 py-1 rounded-full text-xs ${role.bg} ${role.color}`}>
                                {role.label}
                              </span>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-2">
                                <span className="text-[#00E5FF] font-medium">
                                  ${userAccount?.balance?.toFixed(2) || '0.00'}
                                </span>
                                <button
                                  onClick={() => openBalanceDialog(u)}
                                  className="p-1 rounded hover:bg-[#00E5FF]/10 text-slate-400 hover:text-[#00E5FF]"
                                  title="Управление балансом"
                                >
                                  <Wallet size={14} />
                                </button>
                              </div>
                            </td>
                            <td className="p-4 text-slate-400 text-sm">
                              {new Date(u.created_at).toLocaleDateString('ru')}
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-2">
                                <Link to={`/moderator/user/${u.id}`}>
                                  <Button
                                    size="sm"
                                    className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                                  >
                                    <Eye size={14} className="mr-1" />
                                    Профиль
                                  </Button>
                                </Link>
                                <Select
                                  value={u.role || 'user'}
                                  onValueChange={(value) => handleUpdateUserRole(u.id, value)}
                                >
                                  <SelectTrigger className="w-36 bg-[#0B0F14] border-[#27272A]">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent className="bg-[#15191E] border-[#27272A]">
                                    <SelectItem value="user" className="text-white">Пользователь</SelectItem>
                                    <SelectItem value="moderator" className="text-white">Модератор</SelectItem>
                                    <SelectItem value="admin" className="text-white">Администратор</SelectItem>
                                  </SelectContent>
                                </Select>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => openBalanceDialog(u)}
                                  className="border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
                                >
                                  <DollarSign size={14} className="mr-1" />
                                  Баланс
                                </Button>
                                {u.role !== 'admin' && (
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="outline"
                                    onClick={(e) => {
                                      e.preventDefault();
                                      e.stopPropagation();
                                      handleDeleteUser(u.id);
                                    }}
                                    className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                                  >
                                    <Trash2 size={14} />
                                  </Button>
                                )}
                              </div>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState text="Нет пользователей" />
              )}
            </TabsContent>
          )}
        </Tabs>

        {/* Application Detail Dialog */}
        <Dialog open={!!selectedApplication} onOpenChange={() => setSelectedApplication(null)}>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Заявка подрядчика</DialogTitle>
            </DialogHeader>
            {selectedApplication && (
              <div className="space-y-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <InfoField label="Компания" value={selectedApplication.company_name} />
                  <InfoField label="Тип" value={selectedApplication.contractor_type} />
                  <InfoField label="Контакт" value={selectedApplication.contact_person} />
                  <InfoField label="Email" value={selectedApplication.email} />
                  <InfoField label="Телефон" value={selectedApplication.phone} />
                  <InfoField label="Город" value={selectedApplication.city} />
                </div>
                <div>
                  <Label className="text-slate-500">Описание</Label>
                  <p className="text-white mt-1">{selectedApplication.description || '—'}</p>
                </div>
                <div>
                  <Label className="text-slate-500">Услуги</Label>
                  <p className="text-white mt-1">{selectedApplication.services || '—'}</p>
                </div>
                <div className="flex gap-3 pt-4">
                  <Button
                    onClick={() => handleApproveApplication(selectedApplication.id)}
                    className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
                  >
                    <CheckCircle2 size={18} className="mr-2" />
                    Одобрить
                  </Button>
                  <Button
                    onClick={() => handleRejectApplication(selectedApplication.id)}
                    variant="outline"
                    className="flex-1 border-red-500 text-red-400 hover:bg-red-500/10"
                  >
                    <XCircle size={18} className="mr-2" />
                    Отклонить
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* New Tender Dialog */}
        <Dialog open={newTenderDialog} onOpenChange={setNewTenderDialog}>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
            <DialogHeader>
              <DialogTitle>Создать новый тендер</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div>
                <Label className="text-slate-300">Марка автомобиля</Label>
                <Input
                  value={newTenderData.brand}
                  onChange={(e) => setNewTenderData(prev => ({ ...prev, brand: e.target.value }))}
                  placeholder="BYD, Li Auto..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Модель</Label>
                <Input
                  value={newTenderData.model}
                  onChange={(e) => setNewTenderData(prev => ({ ...prev, model: e.target.value }))}
                  placeholder="Han, L9..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Бюджет (USD)</Label>
                <Input
                  type="number"
                  value={newTenderData.budget}
                  onChange={(e) => setNewTenderData(prev => ({ ...prev, budget: e.target.value }))}
                  placeholder="30000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <Button
                onClick={handleCreateTender}
                className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                Создать тендер
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* Balance Management Dialog */}
        <Dialog open={!!balanceDialogUser} onOpenChange={() => setBalanceDialogUser(null)}>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Wallet size={20} className="text-[#00E5FF]" />
                Управление балансом
              </DialogTitle>
            </DialogHeader>
            
            {balanceDialogUser && (
              <div className="space-y-4 mt-4">
                {/* User Info */}
                <div className="p-3 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <p className="text-slate-400 text-xs">Пользователь</p>
                  <p className="text-white font-medium">{balanceDialogUser.name}</p>
                  <p className="text-slate-500 text-sm">{balanceDialogUser.email}</p>
                </div>

                {/* Current Balance */}
                <div className="p-4 bg-[#00E5FF]/10 border border-[#00E5FF]/20 rounded-sm text-center">
                  <p className="text-slate-400 text-sm mb-1">Текущий баланс</p>
                  <p className="text-[#00E5FF] text-3xl font-bold">
                    ${userAccounts[balanceDialogUser.id]?.balance?.toFixed(2) || '0.00'}
                  </p>
                </div>

                {/* Amount Input */}
                <div>
                  <Label className="text-slate-300">Сумма ($)</Label>
                  <Input
                    type="number"
                    value={balanceAmount}
                    onChange={(e) => setBalanceAmount(e.target.value)}
                    placeholder="100.00"
                    min="0"
                    step="0.01"
                    className="mt-1 bg-[#0B0F14] border-[#27272A] text-lg"
                  />
                </div>

                {/* Reason */}
                <div>
                  <Label className="text-slate-300">Причина (опционально)</Label>
                  <Input
                    value={balanceReason}
                    onChange={(e) => setBalanceReason(e.target.value)}
                    placeholder="Бонус за регистрацию, возврат..."
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-3">
                  <Button
                    onClick={() => handleUpdateBalance(true)}
                    disabled={updatingBalance || !balanceAmount}
                    className="bg-emerald-500 hover:bg-emerald-600 text-white"
                  >
                    {updatingBalance ? (
                      <Loader2 size={16} className="mr-2 animate-spin" />
                    ) : (
                      <PlusCircle size={16} className="mr-2" />
                    )}
                    Начислить
                  </Button>
                  <Button
                    onClick={() => handleUpdateBalance(false)}
                    disabled={updatingBalance || !balanceAmount}
                    variant="outline"
                    className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                  >
                    {updatingBalance ? (
                      <Loader2 size={16} className="mr-2 animate-spin" />
                    ) : (
                      <MinusCircle size={16} className="mr-2" />
                    )}
                    Списать
                  </Button>
                </div>

                <p className="text-slate-500 text-xs text-center">
                  Все операции записываются в историю транзакций
                </p>
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Verification Details Dialog */}
        <Dialog open={!!selectedVerification} onOpenChange={() => setSelectedVerification(null)}>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <FileText size={20} className="text-[#00E5FF]" />
                Верификация клиента
              </DialogTitle>
            </DialogHeader>
            
            {selectedVerification && (
              <div className="space-y-6 mt-4">
                {/* Client Info */}
                <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-[#00E5FF] font-medium mb-3">Данные клиента</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">ФИО</p>
                      <p className="text-white">{selectedVerification.full_name}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Тип</p>
                      <p className="text-white">{selectedVerification.client_type === 'legal' ? 'Юр. лицо' : 'Физ. лицо'}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Паспорт</p>
                      <p className="text-white">{selectedVerification.passport_series} {selectedVerification.passport_number}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Выдан</p>
                      <p className="text-white">{selectedVerification.passport_issued_by}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Телефон</p>
                      <p className="text-white">{selectedVerification.phone}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Email</p>
                      <p className="text-white">{selectedVerification.email}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-slate-500">Адрес регистрации</p>
                      <p className="text-white">{selectedVerification.registration_address}</p>
                    </div>
                  </div>
                </div>

                {/* Contract Info */}
                <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-[#00E5FF] font-medium mb-3">Договор</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Номер договора</p>
                      <p className="text-white font-mono">{selectedVerification.contract_number}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Подписан клиентом</p>
                      <p className={selectedVerification.contract_signed ? 'text-emerald-400' : 'text-amber-400'}>
                        {selectedVerification.contract_signed ? 'Да' : 'Нет'}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Documents */}
                <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-[#00E5FF] font-medium mb-3">Загруженные документы</h4>
                  {selectedVerification.documents?.length > 0 ? (
                    <div className="space-y-3">
                      {selectedVerification.documents.map((doc, idx) => (
                        <div key={doc.id || idx} className="flex items-center justify-between p-3 bg-[#15191E] rounded-sm border border-[#27272A]">
                          <div className="flex items-center gap-3">
                            <Image size={20} className="text-slate-400" />
                            <div>
                              <p className="text-white text-sm">
                                {doc.type === 'passport_scan' ? 'Скан паспорта (разворот)' :
                                 doc.type === 'passport_back' ? 'Скан паспорта (прописка)' :
                                 doc.type === 'driver_license' ? 'Водительское удостоверение' :
                                 doc.name || doc.type}
                              </p>
                              <p className="text-slate-500 text-xs">
                                Загружен: {new Date(doc.uploaded_at).toLocaleDateString('ru-RU')}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {doc.url && (
                              <Button size="sm" variant="ghost" asChild className="text-slate-400 hover:text-[#00E5FF]">
                                <a href={doc.url} target="_blank" rel="noopener noreferrer">
                                  <ExternalLink size={16} />
                                </a>
                              </Button>
                            )}
                            {doc.verified === true ? (
                              <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded flex items-center gap-1">
                                <CheckCircle2 size={12} />
                                Подтверждён
                              </span>
                            ) : doc.verified === false ? (
                              <span className="px-2 py-1 bg-red-500/10 text-red-400 text-xs rounded flex items-center gap-1">
                                <XCircle size={12} />
                                Отклонён
                              </span>
                            ) : (
                              <div className="flex gap-1">
                                <Button
                                  size="sm"
                                  className="bg-emerald-500 hover:bg-emerald-600 text-white h-7 px-2"
                                  onClick={() => handleVerifyDocument(selectedVerification.id, doc.id, 'approve')}
                                >
                                  <CheckCircle2 size={14} />
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="border-red-500/50 text-red-400 h-7 px-2"
                                  onClick={() => handleVerifyDocument(selectedVerification.id, doc.id, 'reject')}
                                >
                                  <XCircle size={14} />
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm">Документы не загружены</p>
                  )}
                </div>

                {/* Actions */}
                {selectedVerification.status !== 'approved' && selectedVerification.status !== 'rejected' && (
                  <div className="flex gap-3">
                    <Button
                      className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
                      onClick={() => handleApproveVerification(selectedVerification.id)}
                    >
                      <CheckCircle2 size={16} className="mr-2" />
                      Подтвердить верификацию
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1 border-red-500/50 text-red-400 hover:bg-red-500/10"
                      onClick={() => handleRejectVerification(selectedVerification.id)}
                    >
                      <XCircle size={16} className="mr-2" />
                      Отклонить
                    </Button>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Contractor Details Dialog */}
        <Dialog open={!!selectedContractor} onOpenChange={() => setSelectedContractor(null)}>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Building2 size={20} className="text-[#00E5FF]" />
                Заявка подрядчика
              </DialogTitle>
            </DialogHeader>
            
            {selectedContractor && (
              <div className="space-y-6 mt-4">
                {/* Company Info */}
                <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-[#00E5FF] font-medium mb-3">Информация о компании</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Название</p>
                      <p className="text-white">{selectedContractor.company_name}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Страна</p>
                      <p className="text-white">{selectedContractor.country === 'CN' ? '🇨🇳 Китай' : '🇧🇾 Беларусь'}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Рег. номер</p>
                      <p className="text-white font-mono">{selectedContractor.registration_number}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Опыт работы</p>
                      <p className="text-white">{selectedContractor.experience_years || 0} лет</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-slate-500">Юридический адрес</p>
                      <p className="text-white">{selectedContractor.legal_address}</p>
                    </div>
                  </div>
                </div>

                {/* Contact Info */}
                <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-[#00E5FF] font-medium mb-3">Контактные данные</h4>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <p className="text-slate-500">Контактное лицо</p>
                      <p className="text-white">{selectedContractor.contact_person}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Должность</p>
                      <p className="text-white">{selectedContractor.position}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Телефон</p>
                      <p className="text-white">{selectedContractor.phone}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Email</p>
                      <p className="text-white">{selectedContractor.email}</p>
                    </div>
                  </div>
                </div>

                {/* Services */}
                <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-[#00E5FF] font-medium mb-3">Услуги</h4>
                  <div className="flex flex-wrap gap-2">
                    {(Array.isArray(selectedContractor.services) ? selectedContractor.services : (selectedContractor.services || '').split(',').filter(Boolean)).map(service => {
                      const serviceLabels = {
                        inspection: '🔍 Инспекция',
                        export: '📦 Экспорт',
                        logistics: '🚚 Логистика',
                        purchase: '💰 Выкуп авто',
                        leasing: '📋 Лизинг',
                        customs: '🏛️ Растаможка'
                      };
                      return (
                        <span
                          key={service}
                          className="px-3 py-1.5 bg-[#00E5FF]/10 text-[#00E5FF] text-sm rounded-sm"
                        >
                          {serviceLabels[service] || service}
                        </span>
                      );
                    })}
                  </div>
                </div>

                {/* Description */}
                {selectedContractor.description && (
                  <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                    <h4 className="text-[#00E5FF] font-medium mb-3">Описание</h4>
                    <p className="text-slate-300 text-sm">{selectedContractor.description}</p>
                  </div>
                )}

                {/* Service Prices */}
                {selectedContractor.service_prices && Object.keys(selectedContractor.service_prices).length > 0 && (
                  <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                    <h4 className="text-[#00E5FF] font-medium mb-3">Стоимость услуг</h4>
                    <div className="space-y-2">
                      {Object.entries(selectedContractor.service_prices).map(([service, price]) => {
                        const serviceNames = {
                          inspection: 'Инспекция',
                          purchase: 'Выкуп авто',
                          export: 'Экспорт',
                          logistics: 'Логистика',
                          leasing: 'Лизинг',
                          customs: 'Растаможка'
                        };
                        return (
                          <div key={service} className="flex justify-between text-sm">
                            <span className="text-slate-400">{serviceNames[service] || service}</span>
                            <span className="text-white font-medium">${price} USD</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Actions */}
                {selectedContractor.status === 'pending' && (
                  <div className="flex gap-3">
                    <Button
                      className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
                      onClick={() => handleApproveContractor(selectedContractor.id)}
                    >
                      <CheckCircle2 size={16} className="mr-2" />
                      Одобрить подрядчика
                    </Button>
                    <Button
                      variant="outline"
                      className="flex-1 border-red-500/50 text-red-400 hover:bg-red-500/10"
                      onClick={() => handleRejectContractor(selectedContractor.id)}
                    >
                      <XCircle size={16} className="mr-2" />
                      Отклонить
                    </Button>
                  </div>
                )}

                {selectedContractor.status === 'approved' && (
                  <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-sm flex items-center gap-3">
                    <CheckCircle2 size={20} className="text-emerald-400" />
                    <span className="text-emerald-400">Подрядчик одобрен и может работать на платформе</span>
                  </div>
                )}

                {selectedContractor.status === 'rejected' && (
                  <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-sm flex items-center gap-3">
                    <XCircle size={20} className="text-red-400" />
                    <span className="text-red-400">Заявка отклонена</span>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={!!deleteDialog} onOpenChange={() => setDeleteDialog(null)}>
          <AlertDialogContent className="bg-[#15191E] border-[#27272A]">
            <AlertDialogHeader>
              <AlertDialogTitle className="text-white">Подтвердите действие</AlertDialogTitle>
              <AlertDialogDescription className="text-slate-400">
                {deleteDialog?.title || 'Вы уверены?'} Это действие необратимо.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel className="bg-[#27272A] text-white border-[#27272A] hover:bg-[#3f3f46]">
                Отмена
              </AlertDialogCancel>
              <AlertDialogAction 
                onClick={executeDelete}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Удалить
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
};

// Sub-components
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

const ApplicationCard = ({ application, onView, onApprove, onReject }) => {
  const status = statusConfig[application.status] || statusConfig.pending;
  
  return (
    <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-2">
            <h3 className="text-white font-semibold">{application.company_name}</h3>
            <span className={`px-2 py-0.5 rounded-full text-xs ${status.bg} ${status.color}`}>
              {status.label}
            </span>
          </div>
          <div className="flex flex-wrap gap-4 text-sm text-slate-400">
            <span>{application.contractor_type}</span>
            <span>•</span>
            <span>{application.contact_person}</span>
            <span>•</span>
            <span>{application.email}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="ghost" onClick={onView} className="text-slate-400">
            <Eye size={16} />
          </Button>
          {application.status === 'pending' && (
            <>
              <Button size="sm" onClick={onApprove} className="bg-emerald-500 hover:bg-emerald-600 text-white">
                <CheckCircle2 size={16} />
              </Button>
              <Button size="sm" variant="ghost" onClick={onReject} className="text-red-400 hover:bg-red-500/10">
                <XCircle size={16} />
              </Button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const DealCard = ({ deal, onConfirmStage, onView }) => {
  return (
    <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-white font-semibold">{deal.car_brand} {deal.car_model}</h3>
          <p className="text-slate-400 text-sm">Клиент: {deal.client_name}</p>
        </div>
        <span className="text-[#00E5FF] font-medium">${deal.amount?.toLocaleString()}</span>
      </div>
      
      {/* Stage Progress */}
      <div className="space-y-2">
        <p className="text-slate-500 text-xs uppercase tracking-wider">Этапы сделки</p>
        <div className="grid grid-cols-5 gap-2">
          {Object.entries(dealStages).map(([key, { label, icon: Icon }]) => {
            const isCompleted = deal.completed_stages?.includes(key);
            const isCurrent = deal.current_stage === key;
            
            return (
              <button
                key={key}
                onClick={() => !isCompleted && onConfirmStage(key)}
                disabled={isCompleted}
                className={`p-2 rounded-sm text-center transition-all ${
                  isCompleted 
                    ? 'bg-emerald-500/10 border border-emerald-500/30' 
                    : isCurrent 
                      ? 'bg-[#00E5FF]/10 border border-[#00E5FF]/30 hover:bg-[#00E5FF]/20' 
                      : 'bg-[#0B0F14] border border-[#27272A] hover:border-slate-500'
                }`}
              >
                <Icon size={16} className={`mx-auto ${isCompleted ? 'text-emerald-400' : isCurrent ? 'text-[#00E5FF]' : 'text-slate-500'}`} />
                <p className={`text-xs mt-1 ${isCompleted ? 'text-emerald-400' : isCurrent ? 'text-[#00E5FF]' : 'text-slate-500'}`}>
                  {label}
                </p>
                {isCompleted && <CheckCircle2 size={12} className="text-emerald-400 mx-auto mt-1" />}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const TenderCard = ({ tender }) => {
  return (
    <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
      <div className="flex items-center justify-between mb-3">
        <span className={`px-2 py-0.5 rounded-full text-xs ${
          tender.status === 'active' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-500/10 text-slate-400'
        }`}>
          {tender.status === 'active' ? 'Активен' : 'Завершен'}
        </span>
        <span className="text-slate-500 text-xs">{tender.offers_count} предложений</span>
      </div>
      <h3 className="text-white font-semibold">{tender.brand} {tender.model}</h3>
      <p className="text-[#00E5FF] font-medium mt-1">Бюджет: ${tender.budget?.toLocaleString()}</p>
      <p className="text-slate-400 text-sm mt-2">Создан: {new Date(tender.created_at).toLocaleDateString('ru')}</p>
    </div>
  );
};

const VerificationCard = ({ verification, onView, onApprove, onReject }) => {
  const statusMap = {
    pending: { label: 'Ожидает', color: 'text-amber-400', bg: 'bg-amber-500/10' },
    documents_uploaded: { label: 'Документы загружены', color: 'text-blue-400', bg: 'bg-blue-500/10' },
    under_review: { label: 'На проверке', color: 'text-purple-400', bg: 'bg-purple-500/10' },
    approved: { label: 'Подтверждено', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    rejected: { label: 'Отклонено', color: 'text-red-400', bg: 'bg-red-500/10' }
  };
  
  const status = statusMap[verification.status] || statusMap.pending;
  const documents = verification.documents || [];
  const approvedDocs = documents.filter(d => d.verified === true).length;
  
  return (
    <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
            <FileText size={24} className="text-[#00E5FF]" />
          </div>
          <div>
            <h3 className="text-white font-semibold">{verification.full_name || verification.user_name}</h3>
            <p className="text-slate-400 text-sm">{verification.email || verification.user_email}</p>
            <p className="text-slate-500 text-xs mt-1">
              Договор: <span className="text-[#00E5FF]">{verification.contract_number}</span>
            </p>
          </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs ${status.bg} ${status.color}`}>
          {status.label}
        </span>
      </div>
      
      <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-slate-500">Тип клиента</p>
          <p className="text-white">{verification.client_type === 'legal' ? 'Юр. лицо' : 'Физ. лицо'}</p>
        </div>
        <div>
          <p className="text-slate-500">Документов</p>
          <p className="text-white">{documents.length} загружено</p>
        </div>
        <div>
          <p className="text-slate-500">Проверено</p>
          <p className={approvedDocs === documents.length && documents.length > 0 ? 'text-emerald-400' : 'text-amber-400'}>
            {approvedDocs} / {documents.length}
          </p>
        </div>
      </div>
      
      {/* Documents Preview */}
      {documents.length > 0 && (
        <div className="mt-4 p-3 bg-[#0B0F14] rounded-sm">
          <p className="text-slate-400 text-xs mb-2">Загруженные документы:</p>
          <div className="flex flex-wrap gap-2">
            {documents.map((doc, idx) => (
              <div
                key={doc.id || idx}
                className={`px-2 py-1 rounded text-xs flex items-center gap-1 ${
                  doc.verified === true ? 'bg-emerald-500/10 text-emerald-400' :
                  doc.verified === false ? 'bg-red-500/10 text-red-400' :
                  'bg-slate-500/10 text-slate-400'
                }`}
              >
                <Image size={12} />
                {doc.type === 'passport_scan' ? 'Паспорт (разворот)' :
                 doc.type === 'passport_back' ? 'Паспорт (прописка)' :
                 doc.type === 'driver_license' ? 'Вод. удостоверение' :
                 doc.name || doc.type}
                {doc.verified === true && <CheckCircle2 size={12} />}
                {doc.verified === false && <XCircle size={12} />}
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="mt-4 flex gap-2">
        <Button 
          variant="outline" 
          className="flex-1 border-[#00E5FF]/50 text-[#00E5FF] hover:bg-[#00E5FF]/10"
          onClick={onView}
        >
          <Eye size={16} className="mr-2" />
          Подробнее
        </Button>
        {verification.status !== 'approved' && verification.status !== 'rejected' && (
          <>
            <Button 
              className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
              onClick={onApprove}
            >
              <CheckCircle2 size={16} className="mr-2" />
              Подтвердить
            </Button>
            <Button 
              variant="outline"
              className="border-red-500/50 text-red-400 hover:bg-red-500/10"
              onClick={onReject}
            >
              <XCircle size={16} />
            </Button>
          </>
        )}
      </div>
    </div>
  );
};

const InfoField = ({ label, value }) => (
  <div>
    <Label className="text-slate-500">{label}</Label>
    <p className="text-white">{value || '—'}</p>
  </div>
);

const LoadingState = () => (
  <div className="flex items-center justify-center h-64">
    <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
  </div>
);

const EmptyState = ({ text }) => (
  <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
    <AlertCircle size={48} className="mx-auto mb-4 text-slate-600" />
    <p className="text-slate-400">{text}</p>
  </div>
);

// Demo data
const DEMO_APPLICATIONS = [
  {
    id: 'app-1',
    company_name: 'AutoCheck Shanghai',
    contractor_type: 'inspection',
    contact_person: 'Li Wei',
    email: 'li@autocheck.cn',
    phone: '+86 138 1234 5678',
    city: 'Shanghai',
    description: 'Professional car inspection service',
    services: 'Full inspection, VIN check, history report',
    status: 'pending',
    created_at: '2024-02-20'
  },
  {
    id: 'app-2',
    company_name: 'FastExport Co.',
    contractor_type: 'export',
    contact_person: 'Zhang Min',
    email: 'zhang@fastexport.cn',
    phone: '+86 139 8765 4321',
    city: 'Guangzhou',
    description: 'Quick and reliable export services',
    services: 'Purchase, documentation, customs',
    status: 'reviewing',
    created_at: '2024-02-18'
  }
];

const DEMO_DEALS = [
  {
    id: 'deal-1',
    car_brand: 'BYD',
    car_model: 'Han',
    client_name: 'Иванов И.И.',
    amount: 35000,
    current_stage: 'export',
    completed_stages: ['inspection'],
    status: 'in_progress'
  },
  {
    id: 'deal-2',
    car_brand: 'Li Auto',
    car_model: 'L9',
    client_name: 'Петров П.П.',
    amount: 55000,
    current_stage: 'logistics',
    completed_stages: ['inspection', 'export'],
    status: 'in_progress'
  }
];

const DEMO_TENDERS = [
  {
    id: 'tender-1',
    brand: 'Zeekr',
    model: '001',
    budget: 45000,
    offers_count: 3,
    status: 'active',
    created_at: '2024-02-22'
  },
  {
    id: 'tender-2',
    brand: 'NIO',
    model: 'ES6',
    budget: 50000,
    offers_count: 5,
    status: 'active',
    created_at: '2024-02-20'
  }
];

export default ModeratorPage;
