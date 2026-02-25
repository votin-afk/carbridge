import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { 
  Car, 
  Plus, 
  Trash2, 
  Send,
  ExternalLink,
  Link2,
  Loader2,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  Wallet,
  FileSearch,
  Lock,
  FileText,
  CreditCard,
  ClipboardCheck,
  Package,
  Truck,
  Star,
  Users,
  ChevronDown,
  X
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Contractor stage config
const stageConfig = {
  inspection: {
    label: 'Проверка',
    icon: ClipboardCheck,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30'
  },
  export: {
    label: 'Экспорт',
    icon: Package,
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30'
  },
  logistics: {
    label: 'Логистика',
    icon: Truck,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30'
  }
};

const MyGarage = () => {
  const { token, user } = useAuth();
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [addMode, setAddMode] = useState('url');
  const [urlInput, setUrlInput] = useState('');
  const [parsing, setParsing] = useState(false);
  const [parseResult, setParseResult] = useState(null);
  const [calculatedPrice, setCalculatedPrice] = useState(null);
  const [calculatingPrice, setCalculatingPrice] = useState(false);
  
  // User account state
  const [userBalance, setUserBalance] = useState(0);
  const [isVerified, setIsVerified] = useState(false);
  const [contractSigned, setContractSigned] = useState(false);
  
  // Contractor selection state
  const [contractorDialogOpen, setContractorDialogOpen] = useState(null); // { carId, stage }
  const [contractors, setContractors] = useState([]);
  const [loadingContractors, setLoadingContractors] = useState(false);
  
  const [formData, setFormData] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    price_cny: '',
    engine_type: 'ice',
    engine_volume: '',
    mileage: '',
    image_url: '',
    source_url: '',
    description: ''
  });

  const headers = { Authorization: `Bearer ${token}` };

  const fetchCars = async () => {
    try {
      const response = await axios.get(`${API}/garage`, { headers });
      setCars(response.data);
    } catch (error) {
      console.error('Error fetching garage:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserAccount = async () => {
    try {
      const response = await axios.get(`${API}/user/account`, { headers });
      setUserBalance(response.data.balance || 0);
      setIsVerified(response.data.is_verified || false);
      setContractSigned(response.data.contract_signed || false);
    } catch (error) {
      // If endpoint doesn't exist yet, use defaults
      console.log('Account endpoint not available, using defaults');
    }
  };

  useEffect(() => {
    fetchCars();
    fetchUserAccount();
  }, []);

  // Calculate price when form data changes
  const calculateBelarusPrice = async (priceCny, engineType, engineVolume, year) => {
    if (!priceCny) return;
    
    setCalculatingPrice(true);
    try {
      const currentYear = new Date().getFullYear();
      const carAge = currentYear - year;
      let age = 'under3';
      if (carAge >= 3 && carAge < 5) age = '3to5';
      else if (carAge >= 5) age = 'over5';

      const response = await axios.post(`${API}/calculator`, {
        price_cny: parseFloat(priceCny),
        age: age,
        engine_type: engineType || 'ice',
        engine_volume: engineVolume ? parseInt(engineVolume) : 2000,
        user_type: 'individual',
        use_decree_140: false,
        payment_via_platform: true
      });
      setCalculatedPrice(response.data);
    } catch (error) {
      console.error('Calculation error:', error);
      setCalculatedPrice(null);
    } finally {
      setCalculatingPrice(false);
    }
  };

  useEffect(() => {
    if (formData.price_cny) {
      const timeout = setTimeout(() => {
        calculateBelarusPrice(
          formData.price_cny, 
          formData.engine_type, 
          formData.engine_volume,
          formData.year
        );
      }, 500);
      return () => clearTimeout(timeout);
    } else {
      setCalculatedPrice(null);
    }
  }, [formData.price_cny, formData.engine_type, formData.engine_volume, formData.year]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleParseUrl = async () => {
    if (!urlInput.trim()) {
      toast.error('Вставьте ссылку на объявление');
      return;
    }

    setParsing(true);
    setParseResult(null);
    setCalculatedPrice(null);

    try {
      const response = await axios.post(`${API}/parse-url`, { url: urlInput.trim() });
      
      if (response.data.success) {
        setParseResult({ success: true, data: response.data });
        const newFormData = {
          brand: response.data.brand || '',
          model: response.data.model || '',
          year: response.data.year || new Date().getFullYear(),
          price_cny: response.data.price_cny || '',
          engine_type: response.data.engine_type || 'ice',
          engine_volume: response.data.engine_volume || '',
          mileage: response.data.mileage || '',
          image_url: response.data.image_url || '',
          source_url: response.data.source_url || urlInput.trim(),
          description: response.data.description || ''
        };
        setFormData(newFormData);
        toast.success('Данные извлечены! Проверьте и добавьте в гараж');
      } else {
        setParseResult({ success: false, error: response.data.error });
        toast.error(response.data.error || 'Не удалось извлечь данные');
      }
    } catch (error) {
      setParseResult({ success: false, error: 'Ошибка при обработке ссылки' });
      toast.error('Ошибка при обработке ссылки');
    } finally {
      setParsing(false);
    }
  };

  const handleAddCar = async () => {
    if (!formData.brand || !formData.model || !formData.price_cny) {
      toast.error('Заполните обязательные поля');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/garage`, {
        ...formData,
        year: parseInt(formData.year),
        price_cny: parseFloat(formData.price_cny),
        engine_volume: formData.engine_volume ? parseInt(formData.engine_volume) : null,
        mileage: formData.mileage ? parseInt(formData.mileage) : null,
        calculated_price_usd: calculatedPrice?.total_usd || null,
        calculated_price_byn: calculatedPrice?.total_byn || null
      }, { headers });
      
      toast.success('Авто добавлено в гараж');
      setIsAddDialogOpen(false);
      resetForm();
      fetchCars();
    } catch (error) {
      toast.error('Ошибка при добавлении');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      brand: '', model: '', year: new Date().getFullYear(),
      price_cny: '', engine_type: 'ice', engine_volume: '',
      mileage: '', image_url: '', source_url: '', description: ''
    });
    setUrlInput('');
    setParseResult(null);
    setCalculatedPrice(null);
    setAddMode('url');
  };

  // Delete confirmation state
  const [deleteConfirmId, setDeleteConfirmId] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const handleDeleteCar = async (carId) => {
    setDeleting(true);
    try {
      await axios.delete(`${API}/garage/${carId}`, { headers });
      toast.success('Авто удалено');
      setCars(prevCars => prevCars.filter(c => c.id !== carId));
      setDeleteConfirmId(null);
    } catch (error) {
      console.error('Delete error:', error);
      toast.error('Ошибка при удалении');
    } finally {
      setDeleting(false);
    }
  };

  const confirmDelete = (carId) => {
    setDeleteConfirmId(carId);
  };

  const cancelDelete = () => {
    setDeleteConfirmId(null);
  };

  // Contractor functions
  const openContractorDialog = async (carId, stage) => {
    setContractorDialogOpen({ carId, stage });
    setLoadingContractors(true);
    try {
      const response = await axios.get(`${API}/contractors`, {
        params: { contractor_type: stage }
      });
      setContractors(response.data);
    } catch (error) {
      toast.error('Ошибка загрузки подрядчиков');
    } finally {
      setLoadingContractors(false);
    }
  };

  const assignContractor = async (contractorId) => {
    if (!contractorDialogOpen) return;
    
    try {
      await axios.post(`${API}/garage/${contractorDialogOpen.carId}/assign-contractor`, {
        car_id: contractorDialogOpen.carId,
        contractor_id: contractorId,
        stage: contractorDialogOpen.stage
      }, { headers });
      
      toast.success('Подрядчик выбран');
      setContractorDialogOpen(null);
      fetchCars();
    } catch (error) {
      toast.error('Ошибка при выборе подрядчика');
    }
  };

  const removeContractor = async (carId, stage) => {
    try {
      await axios.delete(`${API}/garage/${carId}/contractor/${stage}`, { headers });
      toast.success('Подрядчик удален');
      fetchCars();
    } catch (error) {
      toast.error('Ошибка при удалении подрядчика');
    }
  };

  const handleStartTender = async (carId) => {
    if (!contractSigned) {
      toast.error('Для запуска тендера необходимо подписать договор');
      return;
    }
    if (userBalance <= 0) {
      toast.error('Для запуска тендера необходимо пополнить баланс');
      return;
    }

    try {
      await axios.post(`${API}/tenders`, { car_id: carId }, { headers });
      toast.success('Тендер запущен! Проверьте раздел "Тендеры"');
      fetchCars();
    } catch (error) {
      toast.error('Ошибка при запуске тендера');
    }
  };

  const handleRequestReport = async (carId) => {
    if (!contractSigned) {
      toast.error('Для запроса отчёта необходимо подписать договор');
      return;
    }
    if (userBalance <= 0) {
      toast.error('Для запроса отчёта необходимо пополнить баланс');
      return;
    }

    toast.success('Запрос на отчёт о состоянии отправлен');
  };

  const canPerformActions = contractSigned && userBalance > 0;

  const getStatusBadge = (status) => {
    const styles = {
      saved: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      tender_active: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      in_progress: 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/20'
    };
    const labels = {
      saved: 'Сохранен',
      tender_active: 'Тендер активен',
      in_progress: 'В работе'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs border ${styles[status] || styles.saved}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getEngineTypeLabel = (type) => {
    const labels = { ice: 'ДВС', hybrid: 'Гибрид', electric: 'Электро' };
    return labels[type] || type;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ru-RU', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    }).format(num);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="my-garage">
      {/* Balance Card */}
      <div className="bg-gradient-to-r from-[#1C2128] to-[#15191E] border border-[#27272A] rounded-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
              <Wallet size={28} className="text-[#00E5FF]" />
            </div>
            <div>
              <p className="text-slate-400 text-sm">Мой баланс</p>
              <p className="text-2xl font-bold text-white">${formatNumber(userBalance)}</p>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Verification Status */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-sm border ${
              isVerified 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-amber-500/10 border-amber-500/30 text-amber-400'
            }`}>
              {isVerified ? <CheckCircle2 size={16} /> : <AlertCircle size={16} />}
              <span className="text-sm">{isVerified ? 'Верифицирован' : 'Не верифицирован'}</span>
            </div>
            
            {/* Contract Status */}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-sm border ${
              contractSigned 
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400' 
                : 'bg-slate-500/10 border-slate-500/30 text-slate-400'
            }`}>
              <FileText size={16} />
              <span className="text-sm">{contractSigned ? 'Договор подписан' : 'Договор не подписан'}</span>
            </div>

            <Button 
              className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              onClick={() => toast.info('Функция пополнения баланса будет доступна после верификации')}
            >
              <CreditCard size={16} className="mr-2" />
              Пополнить
            </Button>
          </div>
        </div>

        {!canPerformActions && (
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-sm">
            <p className="text-amber-400 text-sm flex items-center gap-2">
              <Lock size={14} />
              Для запуска тендера и запроса отчётов необходимо пройти верификацию, подписать договор и пополнить баланс
            </p>
          </div>
        )}
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Мой гараж</h1>
          <p className="text-slate-400 mt-1">
            Сохраненные автомобили для тендера
          </p>
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={(open) => { setIsAddDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button data-testid="add-car-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
              <Plus size={18} className="mr-2" />
              Добавить авто
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Добавить автомобиль</DialogTitle>
            </DialogHeader>

            <Tabs value={addMode} onValueChange={setAddMode} className="mt-4">
              <TabsList className="grid grid-cols-2 bg-[#0B0F14] p-1 rounded-sm">
                <TabsTrigger 
                  value="url"
                  className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black rounded-sm flex items-center gap-2"
                >
                  <Sparkles size={14} />
                  По ссылке
                </TabsTrigger>
                <TabsTrigger 
                  value="manual"
                  className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black rounded-sm"
                >
                  Вручную
                </TabsTrigger>
              </TabsList>

              <TabsContent value="url" className="mt-4 space-y-4">
                {/* URL Input */}
                <div>
                  <Label className="text-slate-300">Ссылка на объявление</Label>
                  <p className="text-slate-500 text-xs mb-2">
                    Вставьте ссылку с che168.com, 58.com, guazi.com или dongchedi.com
                  </p>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Link2 size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                      <Input
                        data-testid="parse-url-input"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        placeholder="https://www.che168.com/dealer/..."
                        className="pl-9 bg-[#0B0F14] border-[#27272A] text-white"
                        disabled={parsing}
                      />
                    </div>
                    <Button
                      data-testid="parse-url-btn"
                      onClick={handleParseUrl}
                      disabled={parsing || !urlInput.trim()}
                      className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black px-4"
                    >
                      {parsing ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
                    </Button>
                  </div>
                </div>

                {/* Parse Result */}
                {parseResult && (
                  <div className={`p-4 rounded-sm border ${
                    parseResult.success 
                      ? 'bg-emerald-500/10 border-emerald-500/30' 
                      : 'bg-red-500/10 border-red-500/30'
                  }`}>
                    <div className="flex items-start gap-3">
                      {parseResult.success ? (
                        <CheckCircle2 size={20} className="text-emerald-400 flex-shrink-0 mt-0.5" />
                      ) : (
                        <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
                      )}
                      <div>
                        {parseResult.success ? (
                          <>
                            <p className="text-emerald-400 font-medium">Данные извлечены!</p>
                            <p className="text-slate-400 text-sm mt-1">
                              {parseResult.data.brand} {parseResult.data.model} ({parseResult.data.year}) — 
                              ¥{parseResult.data.price_cny?.toLocaleString()}
                            </p>
                          </>
                        ) : (
                          <>
                            <p className="text-red-400 font-medium">Ошибка</p>
                            <p className="text-slate-400 text-sm mt-1">{parseResult.error}</p>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Parsed Data Preview with Belarus Price */}
                {parseResult?.success && (
                  <div className="space-y-3 pt-2">
                    <p className="text-slate-400 text-sm">Проверьте данные и нажмите "Добавить в гараж"</p>
                    
                    {formData.image_url && (
                      <div className="h-40 bg-[#1C2128] rounded-sm overflow-hidden">
                        <img 
                          src={formData.image_url} 
                          alt="Preview" 
                          className="w-full h-full object-cover"
                          onError={(e) => e.target.style.display = 'none'}
                        />
                      </div>
                    )}

                    <div className="grid grid-cols-2 gap-3 text-sm">
                      <div className="bg-[#1C2128] p-3 rounded-sm">
                        <span className="text-slate-500">Марка:</span>
                        <p className="text-white">{formData.brand || '—'}</p>
                      </div>
                      <div className="bg-[#1C2128] p-3 rounded-sm">
                        <span className="text-slate-500">Модель:</span>
                        <p className="text-white">{formData.model || '—'}</p>
                      </div>
                      <div className="bg-[#1C2128] p-3 rounded-sm">
                        <span className="text-slate-500">Год:</span>
                        <p className="text-white">{formData.year || '—'}</p>
                      </div>
                      <div className="bg-[#1C2128] p-3 rounded-sm">
                        <span className="text-slate-500">Цена в Китае:</span>
                        <p className="text-white">¥{formData.price_cny?.toLocaleString() || '—'}</p>
                      </div>
                    </div>

                    {/* Belarus Price Calculation */}
                    {calculatedPrice && (
                      <div className="bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded-sm p-4">
                        <p className="text-[#00E5FF] font-medium mb-2 flex items-center gap-2">
                          <CheckCircle2 size={16} />
                          Расчёт под ключ в Беларуси
                        </p>
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div>
                            <span className="text-slate-400">Итого USD:</span>
                            <p className="text-white font-semibold text-lg">${formatNumber(calculatedPrice.total_usd)}</p>
                          </div>
                          <div>
                            <span className="text-slate-400">Итого BYN:</span>
                            <p className="text-white font-semibold text-lg">{formatNumber(calculatedPrice.total_byn)} BYN</p>
                          </div>
                        </div>
                        <p className="text-slate-500 text-xs mt-2">
                          Включает: растаможку, доставку, комиссию платформы 3%, комиссию за оплату 1.5%
                        </p>
                      </div>
                    )}
                    {calculatingPrice && (
                      <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 flex items-center gap-3">
                        <Loader2 size={20} className="text-[#00E5FF] animate-spin" />
                        <span className="text-slate-400">Расчёт стоимости...</span>
                      </div>
                    )}

                    <Button
                      data-testid="add-parsed-car"
                      onClick={handleAddCar}
                      disabled={submitting}
                      className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black mt-2"
                    >
                      {submitting ? 'Добавление...' : 'Добавить в гараж'}
                    </Button>
                  </div>
                )}

                {!parseResult && (
                  <div className="text-center py-6 text-slate-500">
                    <Link2 size={32} className="mx-auto mb-2 opacity-30" />
                    <p className="text-sm">Вставьте ссылку на объявление</p>
                    <p className="text-xs mt-1">AI извлечёт данные автоматически</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="manual" className="mt-4 space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300">Марка *</Label>
                    <Input
                      data-testid="add-car-brand"
                      name="brand"
                      value={formData.brand}
                      onChange={handleChange}
                      placeholder="BYD, Li Auto..."
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">Модель *</Label>
                    <Input
                      data-testid="add-car-model"
                      name="model"
                      value={formData.model}
                      onChange={handleChange}
                      placeholder="Han, L9..."
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300">Год</Label>
                    <Input
                      type="number"
                      name="year"
                      value={formData.year}
                      onChange={handleChange}
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">Цена (CNY) *</Label>
                    <Input
                      data-testid="add-car-price"
                      type="number"
                      name="price_cny"
                      value={formData.price_cny}
                      onChange={handleChange}
                      placeholder="150000"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-slate-300">Тип двигателя</Label>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {['ice', 'hybrid', 'electric'].map(type => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, engine_type: type }))}
                        className={`py-2 px-3 rounded-sm border text-sm ${
                          formData.engine_type === type
                            ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                            : 'bg-[#0B0F14] text-slate-400 border-[#27272A]'
                        }`}
                      >
                        {getEngineTypeLabel(type)}
                      </button>
                    ))}
                  </div>
                </div>

                {formData.engine_type !== 'electric' && (
                  <div>
                    <Label className="text-slate-300">Объем двигателя (см³)</Label>
                    <Input
                      type="number"
                      name="engine_volume"
                      value={formData.engine_volume}
                      onChange={handleChange}
                      placeholder="2000"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                )}

                <div>
                  <Label className="text-slate-300">Пробег (км)</Label>
                  <Input
                    type="number"
                    name="mileage"
                    value={formData.mileage}
                    onChange={handleChange}
                    placeholder="50000"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>

                {/* Belarus Price Calculation for Manual Input */}
                {calculatedPrice && (
                  <div className="bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded-sm p-4">
                    <p className="text-[#00E5FF] font-medium mb-2 flex items-center gap-2">
                      <CheckCircle2 size={16} />
                      Расчёт под ключ в Беларуси
                    </p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-slate-400">Итого USD:</span>
                        <p className="text-white font-semibold text-lg">${formatNumber(calculatedPrice.total_usd)}</p>
                      </div>
                      <div>
                        <span className="text-slate-400">Итого BYN:</span>
                        <p className="text-white font-semibold text-lg">{formatNumber(calculatedPrice.total_byn)} BYN</p>
                      </div>
                    </div>
                  </div>
                )}
                {calculatingPrice && (
                  <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 flex items-center gap-3">
                    <Loader2 size={20} className="text-[#00E5FF] animate-spin" />
                    <span className="text-slate-400">Расчёт стоимости...</span>
                  </div>
                )}

                <div>
                  <Label className="text-slate-300">Ссылка на объявление</Label>
                  <Input
                    name="source_url"
                    value={formData.source_url}
                    onChange={handleChange}
                    placeholder="https://che168.com/..."
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>

                <div>
                  <Label className="text-slate-300">URL изображения</Label>
                  <Input
                    name="image_url"
                    value={formData.image_url}
                    onChange={handleChange}
                    placeholder="https://..."
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>

                <div>
                  <Label className="text-slate-300">Описание</Label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    placeholder="Дополнительная информация..."
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 focus:border-[#00E5FF] min-h-[80px]"
                  />
                </div>

                <Button
                  data-testid="add-car-submit"
                  onClick={handleAddCar}
                  disabled={submitting}
                  className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black mt-4"
                >
                  {submitting ? 'Добавление...' : 'Добавить в гараж'}
                </Button>
              </TabsContent>
            </Tabs>
          </DialogContent>
        </Dialog>
      </div>

      {/* Cars Grid */}
      {cars.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cars.map((car) => (
            <div 
              key={car.id}
              className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden card-hover"
            >
              {/* Image */}
              <div className="h-40 bg-[#1C2128] relative">
                {car.image_url ? (
                  <img 
                    src={car.image_url} 
                    alt={`${car.brand} ${car.model}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Car size={48} className="text-slate-600" />
                  </div>
                )}
                <div className="absolute top-3 right-3">
                  {getStatusBadge(car.status)}
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-white font-semibold text-lg">
                    {car.brand} {car.model}
                  </h3>
                  <span className="text-slate-400 text-sm">
                    ¥{car.price_cny?.toLocaleString()}
                  </span>
                </div>

                {/* Belarus Price */}
                {car.calculated_price_usd && (
                  <div className="mb-3 p-2 bg-[#00E5FF]/10 rounded-sm">
                    <p className="text-[#00E5FF] font-semibold">
                      ${formatNumber(car.calculated_price_usd)} под ключ
                    </p>
                  </div>
                )}

                <div className="flex flex-wrap gap-2 text-sm text-slate-400 mb-4">
                  <span>{car.year}</span>
                  <span>•</span>
                  <span>{getEngineTypeLabel(car.engine_type)}</span>
                  {car.engine_volume && (
                    <>
                      <span>•</span>
                      <span>{car.engine_volume} см³</span>
                    </>
                  )}
                  {car.mileage && (
                    <>
                      <span>•</span>
                      <span>{car.mileage.toLocaleString()} км</span>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="space-y-2">
                  <div className="flex gap-2">
                    {car.status === 'saved' && (
                      <Button
                        data-testid={`start-tender-${car.id}`}
                        onClick={() => handleStartTender(car.id)}
                        disabled={!canPerformActions}
                        className={`flex-1 text-sm ${
                          canPerformActions 
                            ? 'bg-[#00E5FF] hover:bg-[#22D3EE] text-black' 
                            : 'bg-slate-700 text-slate-400 cursor-not-allowed'
                        }`}
                      >
                        {!canPerformActions && <Lock size={12} className="mr-1" />}
                        <Send size={14} className="mr-1" />
                        Запустить тендер
                      </Button>
                    )}
                    {car.source_url && (
                      <a 
                        href={car.source_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="p-2 border border-[#27272A] rounded-sm text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF]"
                      >
                        <ExternalLink size={16} />
                      </a>
                    )}
                    
                    {/* Delete Button with Confirmation */}
                    {deleteConfirmId === car.id ? (
                      <div className="flex gap-1">
                        <button
                          data-testid={`confirm-delete-${car.id}`}
                          onClick={() => handleDeleteCar(car.id)}
                          disabled={deleting}
                          className="p-2 bg-red-500 rounded-sm text-white hover:bg-red-600 disabled:opacity-50"
                        >
                          {deleting ? <Loader2 size={16} className="animate-spin" /> : <CheckCircle2 size={16} />}
                        </button>
                        <button
                          data-testid={`cancel-delete-${car.id}`}
                          onClick={cancelDelete}
                          className="p-2 border border-[#27272A] rounded-sm text-slate-400 hover:text-white"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <button
                        data-testid={`delete-car-${car.id}`}
                        onClick={() => confirmDelete(car.id)}
                        className="p-2 border border-[#27272A] rounded-sm text-slate-400 hover:text-red-400 hover:border-red-400"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                  
                  {/* Request Report Button */}
                  {car.status === 'saved' && (
                    <Button
                      data-testid={`request-report-${car.id}`}
                      onClick={() => handleRequestReport(car.id)}
                      disabled={!canPerformActions}
                      variant="outline"
                      className={`w-full text-sm ${
                        canPerformActions 
                          ? 'border-[#27272A] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF]' 
                          : 'border-slate-700 text-slate-500 cursor-not-allowed'
                      }`}
                    >
                      {!canPerformActions && <Lock size={12} className="mr-1" />}
                      <FileSearch size={14} className="mr-1" />
                      Запросить отчёт о состоянии
                    </Button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <Car size={64} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-xl font-semibold text-white mb-2">Гараж пуст</h3>
          <p className="text-slate-400 mb-6 max-w-md mx-auto">
            Добавьте автомобили по ссылке с китайских площадок или вручную, и запустите тендер для получения предложений
          </p>
          <Button
            onClick={() => setIsAddDialogOpen(true)}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            <Plus size={18} className="mr-2" />
            Добавить первое авто
          </Button>
        </div>
      )}
    </div>
  );
};

export default MyGarage;
