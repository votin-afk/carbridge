import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import {
  Shield,
  FileText,
  Upload,
  CheckCircle2,
  Clock,
  AlertCircle,
  Download,
  Eye,
  User,
  Building2,
  Loader2,
  BadgeCheck,
  XCircle,
  CreditCard,
  DollarSign,
  BanknoteIcon,
  Copy
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusConfig = {
  not_started: { label: 'Не начата', color: 'text-slate-400', bg: 'bg-slate-500/10', icon: Clock },
  pending: { label: 'Данные отправлены', color: 'text-amber-400', bg: 'bg-amber-500/10', icon: Clock },
  documents_uploaded: { label: 'Документы загружены', color: 'text-blue-400', bg: 'bg-blue-500/10', icon: FileText },
  under_review: { label: 'На проверке', color: 'text-purple-400', bg: 'bg-purple-500/10', icon: Eye },
  approved: { label: 'Подтверждено', color: 'text-emerald-400', bg: 'bg-emerald-500/10', icon: CheckCircle2 },
  rejected: { label: 'Отклонено', color: 'text-red-400', bg: 'bg-red-500/10', icon: XCircle }
};

const Verification = () => {
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [verification, setVerification] = useState(null);
  const [activeTab, setActiveTab] = useState('data');
  const [submitting, setSubmitting] = useState(false);
  const [contractDialog, setContractDialog] = useState(false);
  const [contractData, setContractData] = useState(null);
  
  const [formData, setFormData] = useState({
    full_name: user?.name || '',
    passport_series: '',
    passport_number: '',
    passport_issued_by: '',
    passport_issue_date: '',
    registration_address: '',
    phone: user?.phone || '',
    email: user?.email || '',
    client_type: 'individual',
    company_name: '',
    company_unp: '',
    company_address: ''
  });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchVerificationStatus();
  }, []);

  const fetchVerificationStatus = async () => {
    try {
      const response = await axios.get(`${API}/verification/status`, { headers });
      if (response.data.verification) {
        setVerification(response.data.verification);
        setFormData(prev => ({
          ...prev,
          ...response.data.verification
        }));
      }
    } catch (error) {
      console.error('Error fetching verification:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    
    try {
      const response = await axios.post(`${API}/verification/submit`, formData, { headers });
      toast.success('Данные верификации отправлены');
      setVerification(response.data);
      fetchVerificationStatus();
      setActiveTab('documents');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка отправки данных');
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileUpload = async (docType, file) => {
    // In production, upload to cloud storage and get URL
    // For now, simulate with a placeholder
    const fileUrl = URL.createObjectURL(file);
    
    try {
      await axios.post(`${API}/verification/upload-document`, {
        doc_type: docType,
        file_url: fileUrl,
        file_name: file.name
      }, { headers });
      
      toast.success('Документ загружен');
      fetchVerificationStatus();
    } catch (error) {
      toast.error('Ошибка загрузки документа');
    }
  };

  const fetchContract = async () => {
    try {
      const response = await axios.get(`${API}/verification/contract`, { headers });
      setContractData(response.data);
      setContractDialog(true);
    } catch (error) {
      toast.error('Ошибка загрузки договора');
    }
  };

  const signContract = async () => {
    try {
      await axios.post(`${API}/verification/sign-contract`, {}, { headers });
      toast.success('Договор подписан');
      setContractDialog(false);
      fetchVerificationStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка подписания');
    }
  };

  const status = verification?.status ? statusConfig[verification.status] : statusConfig.not_started;
  const StatusIcon = status.icon;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#00E5FF]" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Status Banner */}
      <div className={`p-6 rounded-sm border ${status.bg} border-${status.color.replace('text-', '')}/30`}>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full ${status.bg} flex items-center justify-center`}>
              <StatusIcon size={24} className={status.color} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Верификация клиента</h2>
              <p className={`${status.color} font-medium`}>{status.label}</p>
            </div>
          </div>
          
          {verification?.contract_number && (
            <div className="text-right">
              <p className="text-slate-400 text-sm">Номер договора</p>
              <p className="text-[#00E5FF] font-mono font-bold">{verification.contract_number}</p>
            </div>
          )}
        </div>
      </div>

      {/* Progress Steps */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { step: 1, label: 'Личные данные', status: verification ? 'done' : 'current' },
          { step: 2, label: 'Документы', status: verification?.documents?.length > 0 ? 'done' : verification ? 'current' : 'pending' },
          { step: 3, label: 'Договор', status: verification?.contract_signed ? 'done' : verification?.documents?.length > 0 ? 'current' : 'pending' },
          { step: 4, label: 'Предоплата $500', status: verification?.prepayment_confirmed ? 'done' : verification?.contract_signed ? 'current' : 'pending' },
          { step: 5, label: 'Подтверждение', status: verification?.status === 'approved' ? 'done' : 'pending' }
        ].map(({ step, label, status }) => (
          <div key={step} className={`p-4 rounded-sm border ${
            status === 'done' ? 'bg-emerald-500/10 border-emerald-500/30' :
            status === 'current' ? 'bg-[#00E5FF]/10 border-[#00E5FF]/30' :
            'bg-[#15191E] border-[#27272A]'
          }`}>
            <div className="flex items-center gap-3">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                status === 'done' ? 'bg-emerald-500 text-black' :
                status === 'current' ? 'bg-[#00E5FF] text-black' :
                'bg-[#27272A] text-slate-500'
              }`}>
                {status === 'done' ? <CheckCircle2 size={16} /> : step}
              </div>
              <span className={`text-sm ${
                status === 'done' ? 'text-emerald-400' :
                status === 'current' ? 'text-[#00E5FF]' :
                'text-slate-500'
              }`}>{label}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-[#15191E] p-1 flex-wrap">
          <TabsTrigger value="data" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <User size={16} className="mr-2" />
            Личные данные
          </TabsTrigger>
          <TabsTrigger value="documents" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <FileText size={16} className="mr-2" />
            Документы
          </TabsTrigger>
          <TabsTrigger value="contract" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <Shield size={16} className="mr-2" />
            Договор
          </TabsTrigger>
          <TabsTrigger value="prepayment" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <CreditCard size={16} className="mr-2" />
            Предоплата
          </TabsTrigger>
        </TabsList>

        {/* Personal Data Tab */}
        <TabsContent value="data">
          <form onSubmit={handleSubmit} className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Client Type */}
              <div className="md:col-span-2">
                <Label className="text-slate-300">Тип клиента</Label>
                <div className="flex gap-4 mt-2">
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, client_type: 'individual' }))}
                    className={`flex-1 p-4 rounded-sm border transition-all ${
                      formData.client_type === 'individual'
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                        : 'border-[#27272A] hover:border-slate-500'
                    }`}
                  >
                    <User size={24} className={formData.client_type === 'individual' ? 'text-[#00E5FF]' : 'text-slate-400'} />
                    <p className={`mt-2 font-medium ${formData.client_type === 'individual' ? 'text-white' : 'text-slate-400'}`}>
                      Физическое лицо
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, client_type: 'legal' }))}
                    className={`flex-1 p-4 rounded-sm border transition-all ${
                      formData.client_type === 'legal'
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                        : 'border-[#27272A] hover:border-slate-500'
                    }`}
                  >
                    <Building2 size={24} className={formData.client_type === 'legal' ? 'text-[#00E5FF]' : 'text-slate-400'} />
                    <p className={`mt-2 font-medium ${formData.client_type === 'legal' ? 'text-white' : 'text-slate-400'}`}>
                      Юридическое лицо
                    </p>
                  </button>
                </div>
              </div>

              {/* Full Name */}
              <div>
                <Label className="text-slate-300">ФИО полностью *</Label>
                <Input
                  value={formData.full_name}
                  onChange={(e) => setFormData(prev => ({ ...prev, full_name: e.target.value }))}
                  placeholder="Иванов Иван Иванович"
                  required
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              {/* Passport Series */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Серия паспорта *</Label>
                  <Input
                    value={formData.passport_series}
                    onChange={(e) => setFormData(prev => ({ ...prev, passport_series: e.target.value }))}
                    placeholder="AB"
                    required
                    maxLength={2}
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Номер паспорта *</Label>
                  <Input
                    value={formData.passport_number}
                    onChange={(e) => setFormData(prev => ({ ...prev, passport_number: e.target.value }))}
                    placeholder="1234567"
                    required
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              </div>

              {/* Passport Issued By */}
              <div>
                <Label className="text-slate-300">Кем выдан паспорт *</Label>
                <Input
                  value={formData.passport_issued_by}
                  onChange={(e) => setFormData(prev => ({ ...prev, passport_issued_by: e.target.value }))}
                  placeholder="Минским ГОВД"
                  required
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              {/* Passport Issue Date */}
              <div>
                <Label className="text-slate-300">Дата выдачи паспорта *</Label>
                <Input
                  type="date"
                  value={formData.passport_issue_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, passport_issue_date: e.target.value }))}
                  required
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              {/* Registration Address */}
              <div className="md:col-span-2">
                <Label className="text-slate-300">Адрес регистрации *</Label>
                <Input
                  value={formData.registration_address}
                  onChange={(e) => setFormData(prev => ({ ...prev, registration_address: e.target.value }))}
                  placeholder="г. Минск, ул. Примерная, д. 1, кв. 1"
                  required
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              {/* Phone */}
              <div>
                <Label className="text-slate-300">Телефон *</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData(prev => ({ ...prev, phone: e.target.value }))}
                  placeholder="+375 29 123 45 67"
                  required
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              {/* Email */}
              <div>
                <Label className="text-slate-300">Email *</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="example@email.com"
                  required
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              {/* Legal Entity Fields */}
              {formData.client_type === 'legal' && (
                <>
                  <div>
                    <Label className="text-slate-300">Название организации *</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData(prev => ({ ...prev, company_name: e.target.value }))}
                      placeholder="ООО «Компания»"
                      required={formData.client_type === 'legal'}
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">УНП *</Label>
                    <Input
                      value={formData.company_unp}
                      onChange={(e) => setFormData(prev => ({ ...prev, company_unp: e.target.value }))}
                      placeholder="123456789"
                      required={formData.client_type === 'legal'}
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <Label className="text-slate-300">Юридический адрес *</Label>
                    <Input
                      value={formData.company_address}
                      onChange={(e) => setFormData(prev => ({ ...prev, company_address: e.target.value }))}
                      placeholder="г. Минск, ул. Офисная, д. 1"
                      required={formData.client_type === 'legal'}
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </>
              )}
            </div>

            <Button
              type="submit"
              disabled={submitting || verification?.status === 'approved'}
              className="mt-6 w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {submitting ? (
                <Loader2 className="animate-spin mr-2" size={16} />
              ) : verification ? (
                'Обновить данные'
              ) : (
                'Отправить на верификацию'
              )}
            </Button>
          </form>
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents">
          <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
            {!verification ? (
              <div className="text-center py-12">
                <AlertCircle size={48} className="mx-auto mb-4 text-amber-400" />
                <p className="text-white font-medium">Сначала заполните личные данные</p>
                <Button onClick={() => setActiveTab('data')} className="mt-4">
                  Заполнить данные
                </Button>
              </div>
            ) : (
              <div className="space-y-6">
                <h3 className="text-white font-semibold text-lg">Загрузите сканы документов</h3>
                
                {/* Document Upload Cards */}
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    { type: 'passport_scan', label: 'Скан паспорта (разворот)', required: true },
                    { type: 'passport_back', label: 'Скан паспорта (прописка)', required: true },
                    { type: 'driver_license', label: 'Водительское удостоверение', required: false },
                    { type: 'other', label: 'Другой документ', required: false }
                  ].map(({ type, label, required }) => {
                    const uploaded = verification?.documents?.find(d => d.type === type);
                    
                    return (
                      <div
                        key={type}
                        className={`p-4 rounded-sm border ${
                          uploaded ? 'border-emerald-500/30 bg-emerald-500/10' : 'border-[#27272A]'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <p className="text-white font-medium">{label}</p>
                            {required && <span className="text-red-400 text-xs">* Обязательно</span>}
                          </div>
                          {uploaded && <CheckCircle2 size={20} className="text-emerald-400" />}
                        </div>
                        
                        {uploaded ? (
                          <div className="flex items-center gap-2 text-sm">
                            <FileText size={14} className="text-emerald-400" />
                            <span className="text-slate-300 truncate">{uploaded.name}</span>
                          </div>
                        ) : (
                          <label className="block">
                            <input
                              type="file"
                              accept="image/*,.pdf"
                              onChange={(e) => e.target.files?.[0] && handleFileUpload(type, e.target.files[0])}
                              className="hidden"
                            />
                            <div className="flex items-center justify-center gap-2 py-3 border border-dashed border-[#27272A] rounded-sm cursor-pointer hover:border-[#00E5FF] transition-colors">
                              <Upload size={16} className="text-slate-400" />
                              <span className="text-slate-400 text-sm">Выбрать файл</span>
                            </div>
                          </label>
                        )}
                      </div>
                    );
                  })}
                </div>

                {verification?.documents?.length >= 2 && (
                  <Button onClick={() => setActiveTab('contract')} className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
                    Перейти к договору
                  </Button>
                )}
              </div>
            )}
          </div>
        </TabsContent>

        {/* Contract Tab */}
        <TabsContent value="contract">
          <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
            {!verification?.documents?.length ? (
              <div className="text-center py-12">
                <AlertCircle size={48} className="mx-auto mb-4 text-amber-400" />
                <p className="text-white font-medium">Сначала загрузите документы</p>
                <Button onClick={() => setActiveTab('documents')} className="mt-4">
                  Загрузить документы
                </Button>
              </div>
            ) : (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-white font-semibold text-lg">Договор на оказание услуг</h3>
                    <p className="text-slate-400 text-sm">Договор № {verification?.contract_number}</p>
                  </div>
                  {verification?.contract_signed && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 rounded-full">
                      <BadgeCheck size={16} className="text-emerald-400" />
                      <span className="text-emerald-400 text-sm">Подписан</span>
                    </div>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <Button
                    onClick={fetchContract}
                    variant="outline"
                    className="border-[#00E5FF]/50 text-[#00E5FF] hover:bg-[#00E5FF]/10"
                  >
                    <Eye size={16} className="mr-2" />
                    Просмотреть договор
                  </Button>
                  <Button
                    onClick={() => {
                      // Download PDF directly
                      window.open(`${API}/verification/contract/download`, '_blank');
                    }}
                    variant="outline"
                    className="border-[#00E5FF]/50 text-[#00E5FF] hover:bg-[#00E5FF]/10"
                  >
                    <Download size={16} className="mr-2" />
                    Скачать PDF
                  </Button>
                </div>

                {!verification?.contract_signed && (
                  <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-sm">
                    <p className="text-amber-400 text-sm">
                      Для продолжения работы необходимо подписать договор. Ознакомьтесь с условиями и нажмите "Подписать".
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        </TabsContent>
      </Tabs>

      {/* Contract Dialog */}
      <Dialog open={contractDialog} onOpenChange={setContractDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText size={20} className="text-[#00E5FF]" />
              Договор № {contractData?.contract_number}
            </DialogTitle>
          </DialogHeader>
          
          {contractData && (
            <div className="mt-4 space-y-6">
              {/* Contract Preview */}
              <div className="p-6 bg-white text-black rounded-sm font-serif text-sm leading-relaxed max-h-[60vh] overflow-y-auto">
                <div className="text-center mb-6">
                  <h2 className="text-lg font-bold">ДОГОВОР № {contractData.contract_number}</h2>
                  <p>на оказание услуг по организации приобретения и доставки автомобиля</p>
                  <p className="mt-2">г. {contractData.city} &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; «{contractData.date}»</p>
                </div>

                <p className="mb-4">
                  <strong>{contractData.executor.name}</strong>, именуемое в дальнейшем «Исполнитель», в лице директора {contractData.executor.director}, 
                  действующего на основании Устава, с одной стороны, и
                </p>

                <p className="mb-4">
                  Гражданин(ка) <strong>{contractData.client.full_name}</strong>, паспорт: серия № <strong>{contractData.client.passport_series} {contractData.client.passport_number}</strong>, 
                  выдан <strong>{contractData.client.passport_issued_by}</strong> <strong>{contractData.client.passport_issue_date}</strong>, 
                  проживающий(ая) по адресу: <strong>{contractData.client.registration_address}</strong>, 
                  именуемый(ая) в дальнейшем «Заказчик», с другой стороны,
                </p>

                <p className="mb-4">вместе именуемые «Стороны», заключили настоящий Договор о нижеследующем:</p>

                <h3 className="font-bold mt-6 mb-2">1. ПРЕДМЕТ ДОГОВОРА</h3>
                <p className="mb-2">1.1. Исполнитель обязуется оказать Заказчику услуги по организации приобретения и доставки транспортного средства (далее – «Автомобиль») из Китайской Народной Республики через цифровую платформу CarBridge, а Заказчик обязуется принять и оплатить оказанные услуги.</p>
                <p className="mb-2">1.2. В комплекс услуг Исполнителя входит:</p>
                <p className="ml-4">1.2.1. Предоставление доступа к функционалу платформы CarBridge, включая AI-агента для подбора автомобиля;</p>
                <p className="ml-4">1.2.2. Доступ к тендерной системе для получения предложений от китайских поставщиков;</p>
                <p className="ml-4">1.2.3. Координация процесса проверки технического состояния автомобиля;</p>
                <p className="ml-4">1.2.4. Взаимодействие с проверенными подрядчиками (продавцами) в КНР;</p>
                <p className="ml-4">1.2.5. Организация логистики (выбор перевозчика через тендерную систему);</p>
                <p className="ml-4">1.2.6. Предоставление доступа к системе GPS-мониторинга для отслеживания груза;</p>
                <p className="ml-4">1.2.7. Консультационная поддержка по вопросам таможенного оформления.</p>

                <h3 className="font-bold mt-6 mb-2">2. ПОРЯДОК ОКАЗАНИЯ УСЛУГ</h3>
                <p className="mb-2">2.1. Оказание услуг осуществляется поэтапно через личный кабинет Заказчика на платформе CarBridge:</p>
                <p className="ml-4">2.1.1. Регистрация Заказчика на платформе и получение доступа к личному кабинету.</p>
                <p className="ml-4">2.1.2. Подбор автомобиля с использованием AI-агента или самостоятельный выбор из каталога.</p>
                <p className="ml-4">2.1.3. Формирование и утверждение Заказчиком типовой формы запроса на автомобиль.</p>
                <p className="ml-4">2.1.4. Внесение Заказчиком предоплаты для активации тендерной системы.</p>
                <p className="ml-4">2.1.5. Автоматическая рассылка запроса подрядчикам в Китае.</p>
                <p className="ml-4">2.1.6. Сбор и предоставление Заказчику коммерческих предложений.</p>
                <p className="ml-4">2.1.7. Выбор Заказчиком конкретного предложения (автомобиля и поставщика).</p>
                <p className="ml-4">2.1.8. Организация детальной проверки автомобиля (видеообзор, фото, отчет).</p>
                <p className="ml-4">2.1.9. Заключение договора купли-продажи между Заказчиком и Продавцом.</p>
                <p className="ml-4">2.1.10. Контроль процесса выкупа и перевода денежных средств.</p>
                <p className="ml-4">2.1.11. Организация логистики: тендер среди перевозчиков.</p>
                <p className="ml-4">2.1.12. GPS-мониторинг на всем пути следования автомобиля.</p>
                <p className="ml-4">2.1.13. Организация таможенного оформления: тендер среди брокеров.</p>
                <p className="ml-4">2.1.14. Передача автомобиля Заказчику.</p>
                <p className="mt-2 mb-2">2.2. <strong>Важное условие:</strong> Исполнитель предоставляет информационно-техническую платформу для организации сделки, но не выступает Продавцом автомобиля. Договор купли-продажи заключается напрямую между Заказчиком и китайским поставщиком.</p>

                <h3 className="font-bold mt-6 mb-2">4. СТОИМОСТЬ УСЛУГ И ПОРЯДОК РАСЧЕТОВ</h3>
                <p className="mb-2">4.1. Для начала работы Заказчик вносит Предоплату в размере <strong>1500 (Тысяча пятьсот) белорусских рублей</strong>. Данная сумма не подлежит возврату после запуска тендерной процедуры.</p>
                <p className="mb-2">4.2. Вознаграждение (комиссия) Исполнителя составляет <strong>3% (три процента)</strong> от стоимости автомобиля.</p>
                <p className="mb-2">4.3. Оплата комиссии производится после выбора автомобиля, но до момента перечисления средств за выкуп.</p>
                <p className="mb-2">4.5.2. За организацию платежей через платформу взимается комиссия <strong>1,5%</strong> от суммы каждого платежа.</p>

                <h3 className="font-bold mt-6 mb-2">5. ОТВЕТСТВЕННОСТЬ СТОРОН</h3>
                <p className="mb-2">5.1.1. Исполнитель не несет ответственности за скрытые дефекты и техническое состояние автомобиля.</p>
                <p className="mb-2">5.1.2. Исполнитель не несет ответственности за нарушение сроков поставки перевозчиками.</p>
                <p className="mb-2">5.1.3. Исполнитель не несет ответственности за действия таможенных органов.</p>

                <h3 className="font-bold mt-6 mb-2">7. СРОК ДЕЙСТВИЯ</h3>
                <p className="mb-2">7.1. Договор вступает в силу с момента регистрации на платформе и внесения предоплаты.</p>
                <p className="mb-2">7.2. Договор действует до полного исполнения Сторонами обязательств.</p>

                <h3 className="font-bold mt-6 mb-2">9. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ</h3>
                <p className="mb-2">9.2. Регистрация на платформе и внесение предоплаты означает полное согласие со всеми условиями настоящего Договора (договор присоединения, ст. 398 ГК РБ).</p>

                <div className="mt-8 grid grid-cols-2 gap-8 border-t pt-6">
                  <div>
                    <h4 className="font-bold mb-2">ИСПОЛНИТЕЛЬ:</h4>
                    <p>{contractData.executor.name}</p>
                    <p>Юр. адрес: {contractData.executor.address}</p>
                    <p>УНП: {contractData.executor.unp}</p>
                    <p className="mt-4">Директор _____________ / К.М. Вотинцев /</p>
                    <p className="mt-2">М.П.</p>
                  </div>
                  <div>
                    <h4 className="font-bold mb-2">ЗАКАЗЧИК:</h4>
                    <p>Ф.И.О.: {contractData.client.full_name}</p>
                    <p>Паспорт: {contractData.client.passport_series} {contractData.client.passport_number}</p>
                    <p>Адрес: {contractData.client.registration_address}</p>
                    <p>Телефон: {contractData.client.phone}</p>
                    <p>Email: {contractData.client.email}</p>
                    <p className="mt-4">Заказчик _____________ / _____________ /</p>
                  </div>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                <Button
                  onClick={() => {
                    // Download PDF with auth
                    const link = document.createElement('a');
                    link.href = `${API}/verification/contract/download`;
                    link.target = '_blank';
                    // Add auth header via fetch
                    fetch(`${API}/verification/contract/download`, {
                      headers: { Authorization: `Bearer ${token}` }
                    })
                    .then(res => res.blob())
                    .then(blob => {
                      const url = window.URL.createObjectURL(blob);
                      const a = document.createElement('a');
                      a.href = url;
                      a.download = `Dogovor_CarBridge_${contractData.contract_number}.pdf`;
                      a.click();
                      window.URL.revokeObjectURL(url);
                      toast.success('PDF договора сохранён');
                    })
                    .catch(() => toast.error('Ошибка скачивания'));
                  }}
                  variant="outline"
                  className="flex-1 border-[#00E5FF]/50 text-[#00E5FF]"
                >
                  <Download size={16} className="mr-2" />
                  Скачать PDF
                </Button>
                
                {!contractData.signed && (
                  <Button
                    onClick={signContract}
                    className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
                  >
                    <BadgeCheck size={16} className="mr-2" />
                    Подписать договор
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Verification;
