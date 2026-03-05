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
  ExternalLink
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
  
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (isModerator) {
      fetchData();
    }
  }, [activeTab, isModerator]);

  const fetchData = async () => {
    setLoading(true);
    try {
      if (activeTab === 'applications') {
        const response = await axios.get(`${API}/moderator/applications`, { headers });
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
        const response = await axios.get(`${API}/moderator/contractor-applications`, { headers });
        setContractorApplications(response.data);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      // Use demo data if API not ready
      if (activeTab === 'applications') {
        setApplications(DEMO_APPLICATIONS);
      } else if (activeTab === 'deals') {
        setDeals(DEMO_DEALS);
      } else if (activeTab === 'tenders') {
        setTenders(DEMO_TENDERS);
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
      toast.success(`Подрядчик одобрен! Временный пароль: ${response.data.temp_password}`);
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

  if (!isModerator) {
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
          <TabsList className="bg-[#15191E] p-1 mb-6">
            <TabsTrigger value="applications" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <Users size={16} className="mr-2" />
              Заявки подрядчиков
            </TabsTrigger>
            <TabsTrigger value="deals" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
              <FileCheck size={16} className="mr-2" />
              Сделки
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

          {/* Applications Tab */}
          <TabsContent value="applications">
            {loading ? (
              <LoadingState />
            ) : applications.length > 0 ? (
              <div className="space-y-4">
                {applications.map(app => (
                  <ApplicationCard 
                    key={app.id} 
                    application={app}
                    onView={() => setSelectedApplication(app)}
                    onApprove={() => handleApproveApplication(app.id)}
                    onReject={() => handleRejectApplication(app.id)}
                  />
                ))}
              </div>
            ) : (
              <EmptyState text="Нет заявок на рассмотрение" />
            )}
          </TabsContent>

          {/* Deals Tab */}
          <TabsContent value="deals">
            {loading ? (
              <LoadingState />
            ) : deals.length > 0 ? (
              <div className="space-y-4">
                {deals.map(deal => (
                  <DealCard 
                    key={deal.id} 
                    deal={deal}
                    onConfirmStage={(stage) => handleConfirmStage(deal.id, stage)}
                    onView={() => setSelectedDeal(deal)}
                  />
                ))}
              </div>
            ) : (
              <EmptyState text="Нет активных сделок" />
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
                  <TenderCard key={tender.id} tender={tender} />
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
