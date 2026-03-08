import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Checkbox } from "../../components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  Car,
  User,
  Building2,
  DollarSign,
  Calendar,
  Gauge,
  Fuel,
  Palette,
  Settings,
  FileText,
  CheckCircle2,
  Loader2,
  Plus,
  ChevronRight,
  ChevronLeft,
  Zap,
  Eye,
  AlertTriangle,
  Star,
  MapPin,
  Cog,
  Monitor,
  Sofa,
  Sparkles,
  Package,
  Clock,
  Target,
  Send,
  Headphones,
  XCircle,
  Users
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// === КОНСТАНТЫ ФОРМЫ (из PDF) ===

const bodyTypes = [
  { value: 'sedan', label: 'Седан' },
  { value: 'hatchback', label: 'Хэтчбек' },
  { value: 'coupe', label: 'Купе' },
  { value: 'minivan', label: 'Минивэн' },
  { value: 'wagon', label: 'Универсал' },
  { value: 'pickup', label: 'Пикап' },
  { value: 'suv', label: 'SUV/Кроссовер' },
  { value: 'any', label: 'Любой' }
];

const engineTypes = [
  { value: 'petrol', label: 'Бензин' },
  { value: 'diesel', label: 'Дизель' },
  { value: 'electric', label: 'Электро (BEV)' },
  { value: 'hybrid', label: 'Гибрид (HEV)' },
  { value: 'phev', label: 'PHEV' },
  { value: 'gas', label: 'Газ' }
];

const engineVolumes = [
  { value: 'lt1', label: 'до 1.0' },
  { value: '1_15', label: '1.0-1.5' },
  { value: '15_2', label: '1.5-2.0' },
  { value: '2_25', label: '2.0-2.5' },
  { value: '25_3', label: '2.5-3.0' },
  { value: 'gt3', label: '>3.0' },
  { value: 'any', label: 'Не важно' }
];

const transmissions = [
  { value: 'mt', label: 'MT (Механика)' },
  { value: 'at', label: 'AT (Автомат)' },
  { value: 'amt_dsg', label: 'AMT/DSG' },
  { value: 'cvt', label: 'CVT (Вариатор)' },
  { value: 'reducer', label: 'Редуктор' },
  { value: 'any', label: 'Не важно' }
];

const driveTypes = [
  { value: 'fwd', label: 'FWD (Передний)' },
  { value: 'rwd', label: 'RWD (Задний)' },
  { value: 'awd', label: 'AWD/4WD (Полный)' },
  { value: 'any', label: 'Не важно' }
];

const bodyColors = [
  { value: 'white', label: 'Белый' },
  { value: 'black', label: 'Чёрный' },
  { value: 'grey', label: 'Серый' },
  { value: 'silver', label: 'Серебристый' },
  { value: 'blue', label: 'Синий' },
  { value: 'red', label: 'Красный' },
  { value: 'brown', label: 'Коричневый' },
  { value: 'green', label: 'Зелёный' },
  { value: 'other', label: 'Другой' },
  { value: 'any', label: 'Не важно' }
];

const interiorColors = [
  { value: 'black', label: 'Чёрный' },
  { value: 'beige', label: 'Бежевый' },
  { value: 'grey', label: 'Серый' },
  { value: 'brown', label: 'Коричневый' },
  { value: 'combi', label: 'Комби' },
  { value: 'other', label: 'Другой' },
  { value: 'any', label: 'Не важно' }
];

const interiorMaterials = [
  { value: 'leather', label: 'Кожа' },
  { value: 'eco_leather', label: 'Экокожа' },
  { value: 'fabric', label: 'Ткань' },
  { value: 'alcantara', label: 'Алькантара' },
  { value: 'any', label: 'Не важно' }
];

const mileageOptions = [
  { value: 'lt10', label: '<10 тыс. км' },
  { value: 'lt30', label: '<30 тыс. км' },
  { value: 'lt50', label: '<50 тыс. км' },
  { value: 'lt80', label: '<80 тыс. км' },
  { value: 'lt100', label: '<100 тыс. км' },
  { value: 'gt100', label: '>100 тыс. км' },
  { value: 'any', label: 'Не важно' }
];

const carConditions = [
  { value: 'new', label: 'Только новый (0 км)' },
  { value: 'used', label: 'С пробегом' },
  { value: 'any', label: 'Любое' }
];

const damageLevels = [
  { value: 'level1', label: 'Уровень 1 (Минимальные)', desc: 'Мелкие царапины до 2 см, потёртости на бамперах' },
  { value: 'level12', label: 'Уровень 1-2 (Незначительные)', desc: 'Царапины до металла (не более 2 шт.), вмятины до 3 см' },
  { value: 'level123', label: 'Уровень 1-3 (Средние)', desc: 'Локальный перекрас 1-2 элементов, вмятины до 5 см' },
  { value: 'new_only', label: 'Только новый', desc: 'Без каких-либо повреждений' }
];

const purchaseTimelines = [
  { value: 'urgent', label: 'Срочно' },
  { value: '1month', label: '1 месяц' },
  { value: '2_3months', label: '2-3 месяца' },
  { value: 'not_rush', label: 'Не спешу' }
];

const paymentMethods = [
  { value: 'full_prepay', label: '100% предоплата' },
  { value: 'installment', label: 'Рассрочка' },
  { value: 'credit_leasing', label: 'Кредит/Лизинг' }
];

const carPurposes = [
  { value: 'personal', label: 'Личное' },
  { value: 'business', label: 'Бизнес' },
  { value: 'taxi', label: 'Такси' },
  { value: 'resale', label: 'Перепродажа' }
];

const customsClearanceOptions = [
  { value: 'carbridge', label: 'Через CarBridge' },
  { value: 'self', label: 'Самостоятельно' },
  { value: 'unknown', label: 'Не знаю' }
];

const colorImportance = [
  { value: 'required', label: 'Обязательно' },
  { value: 'preferred', label: 'Желательно' },
  { value: 'not_important', label: 'Не важно' }
];

// Опции
const electronicOptions = [
  { value: 'system_360', label: 'Система 360°' },
  { value: 'acc', label: 'ACC (Адаптив. круиз)' },
  { value: 'lka', label: 'LKA (Контроль полосы)' },
  { value: 'autopark', label: 'Автопарковка' },
  { value: 'parking_sensors', label: 'Датчики парковки' },
  { value: 'rear_camera', label: 'Камера заднего вида' },
  { value: 'wireless_charge', label: 'Беспроводная зарядка' },
  { value: 'hud', label: 'HUD (Проекция)' },
  { value: 'carplay', label: 'CarPlay / Android Auto' }
];

const comfortOptions = [
  { value: 'panoramic_roof', label: 'Панорамная крыша' },
  { value: 'heated_front', label: 'Подогрев перед. сидений' },
  { value: 'heated_rear', label: 'Подогрев зад. сидений' },
  { value: 'ventilated_seats', label: 'Вентиляция сидений' },
  { value: 'massage_seats', label: 'Массаж сидений' },
  { value: 'seat_memory', label: 'Память сидений' },
  { value: 'climate_control', label: 'Климат-контроль (2-3 зоны)' },
  { value: 'heated_wheel', label: 'Подогрев руля' },
  { value: 'electric_trunk', label: 'Электропривод багажника' },
  { value: 'keyless', label: 'Бесключевой доступ' }
];

const exteriorOptions = [
  { value: 'sport_package', label: 'Спортивный пакет' },
  { value: 'wheels_r18', label: 'Диски R18+' },
  { value: 'led_matrix', label: 'LED/Matrix фары' },
  { value: 'factory_tint', label: 'Тонировка штатная' }
];

const otherOptions = [
  { value: 'towbar', label: 'Фаркоп' },
  { value: 'spare_wheel', label: 'Запасное колесо' },
  { value: 'third_row', label: 'Третий ряд сидений' },
  { value: 'premium_audio', label: 'Premium аудио' }
];

const Applications = () => {
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);
  const [requestingManagerHelp, setRequestingManagerHelp] = useState(false);
  const [startingTender, setStartingTender] = useState(false);
  const [accountSummary, setAccountSummary] = useState(null);
  const [cancellingApp, setCancellingApp] = useState(false);

  const [formData, setFormData] = useState({
    // Раздел 1: Данные клиента
    client_type: 'individual',
    full_name: user?.name || '',
    delivery_city: '',
    
    // Раздел 2.1: Основные характеристики
    brand: '',
    model: '',
    year_from: '',
    year_to: '',
    body_type: '',
    
    // Раздел 2.2: Двигатель и трансмиссия
    engine_type: '',
    engine_volume: 'any',
    power_from: '',
    power_to: '',
    transmission: 'any',
    drive_type: 'any',
    
    // Раздел 2.3: Внешний вид
    body_color: 'any',
    body_color_other: '',
    exact_color: '',
    color_importance: 'not_important',
    interior_color: 'any',
    interior_color_other: '',
    interior_material: 'any',
    
    // Раздел 3: Пробег и состояние
    mileage_max: 'any',
    car_condition: 'any',
    allow_damage: false,
    damage_level: '',
    damage_comment: '',
    
    // Раздел 4: Опции
    options_electronic: [],
    options_comfort: [],
    options_exterior: [],
    options_other: [],
    required_options: '',
    preferred_options: '',
    
    // Раздел 5: Бюджет и условия
    budget_china_from: '',
    budget_china_to: '',
    budget_total: '',
    purchase_timeline: '1month',
    payment_method: 'full_prepay',
    car_purpose: 'personal',
    customs_clearance: 'carbridge',
    
    // Раздел 6: Приоритеты
    priority_price: 1,
    priority_reliability: 2,
    priority_technology: 3,
    priority_prestige: 4,
    priority_fuel: 5,
    additional_requirements: ''
  });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchApplications();
    fetchAccountSummary();
  }, []);

  const fetchAccountSummary = async () => {
    try {
      const response = await axios.get(`${API}/account/summary`, { headers });
      setAccountSummary(response.data);
    } catch (error) {
      console.log('Account endpoint not available');
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await axios.get(`${API}/applications/my`, { headers });
      setApplications(response.data);
    } catch (error) {
      console.error('Error fetching applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const cancelApplication = async (appId) => {
    setCancellingApp(true);
    try {
      await axios.delete(`${API}/applications/${appId}`, { headers });
      toast.success('Заявка отменена');
      setSelectedApp(null);
      fetchApplications();
    } catch (error) {
      toast.error('Не удалось отменить заявку');
    } finally {
      setCancellingApp(false);
    }
  };

  const requestManagerHelp = async (appId) => {
    if ((accountSummary?.balance || 0) < 200) {
      toast.error('Недостаточно средств. Требуется $200 для помощи менеджера');
      return;
    }
    
    setRequestingManagerHelp(true);
    try {
      await axios.post(`${API}/applications/${appId}/request-manager-help`, {}, { headers });
      toast.success('Менеджер назначен! С баланса списано $200');
      fetchApplications();
      fetchAccountSummary();
      // Обновляем выбранную заявку
      const updated = await axios.get(`${API}/applications/${appId}`, { headers });
      setSelectedApp(updated.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при запросе помощи');
    } finally {
      setRequestingManagerHelp(false);
    }
  };

  const startTenderFromApplication = async (appId) => {
    if (!accountSummary?.contract_signed) {
      toast.error('Для запуска тендера необходимо подписать договор в разделе "Верификация"');
      return;
    }
    
    setStartingTender(true);
    try {
      await axios.post(`${API}/applications/${appId}/start-tender`, {}, { headers });
      toast.success('Тендер запущен! Проверьте раздел "Тендеры"');
      fetchApplications();
      // Обновляем выбранную заявку
      const updated = await axios.get(`${API}/applications/${appId}`, { headers });
      setSelectedApp(updated.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при запуске тендера');
    } finally {
      setStartingTender(false);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        year_from: formData.year_from ? parseInt(formData.year_from) : null,
        year_to: formData.year_to ? parseInt(formData.year_to) : null,
        power_from: formData.power_from ? parseInt(formData.power_from) : null,
        power_to: formData.power_to ? parseInt(formData.power_to) : null,
        budget_china_from: formData.budget_china_from ? parseFloat(formData.budget_china_from) : null,
        budget_china_to: formData.budget_china_to ? parseFloat(formData.budget_china_to) : null,
        budget_total: formData.budget_total ? parseFloat(formData.budget_total) : null
      };
      
      await axios.post(`${API}/applications/create`, payload, { headers });
      toast.success('Заявка успешно создана!');
      setShowForm(false);
      setCurrentStep(1);
      resetForm();
      fetchApplications();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка создания заявки');
    } finally {
      setSubmitting(false);
    }
  };

  const resetForm = () => {
    setFormData({
      client_type: 'individual',
      full_name: user?.name || '',
      delivery_city: '',
      brand: '',
      model: '',
      year_from: '',
      year_to: '',
      body_type: '',
      engine_type: '',
      engine_volume: 'any',
      power_from: '',
      power_to: '',
      transmission: 'any',
      drive_type: 'any',
      body_color: 'any',
      body_color_other: '',
      exact_color: '',
      color_importance: 'not_important',
      interior_color: 'any',
      interior_color_other: '',
      interior_material: 'any',
      mileage_max: 'any',
      car_condition: 'any',
      allow_damage: false,
      damage_level: '',
      damage_comment: '',
      options_electronic: [],
      options_comfort: [],
      options_exterior: [],
      options_other: [],
      required_options: '',
      preferred_options: '',
      budget_china_from: '',
      budget_china_to: '',
      budget_total: '',
      purchase_timeline: '1month',
      payment_method: 'full_prepay',
      car_purpose: 'personal',
      customs_clearance: 'carbridge',
      priority_price: 1,
      priority_reliability: 2,
      priority_technology: 3,
      priority_prestige: 4,
      priority_fuel: 5,
      additional_requirements: ''
    });
  };

  const toggleOption = (category, value) => {
    setFormData(prev => {
      const current = prev[category] || [];
      if (current.includes(value)) {
        return { ...prev, [category]: current.filter(v => v !== value) };
      } else {
        return { ...prev, [category]: [...current, value] };
      }
    });
  };

  const totalSteps = 6;

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6" data-testid="step-1-client-data">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <User size={20} className="text-[#00E5FF]" />
              Раздел 1: Данные клиента
            </h3>
            
            {/* Тип клиента */}
            <div>
              <Label className="text-slate-300 mb-2 block">Тип клиента</Label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  data-testid="client-type-individual"
                  onClick={() => setFormData(p => ({ ...p, client_type: 'individual' }))}
                  className={`p-4 rounded-sm border transition-all ${
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
                  data-testid="client-type-legal"
                  onClick={() => setFormData(p => ({ ...p, client_type: 'legal' }))}
                  className={`p-4 rounded-sm border transition-all ${
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

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">ФИО / Наименование компании *</Label>
                <Input
                  data-testid="full-name-input"
                  value={formData.full_name}
                  onChange={(e) => setFormData(p => ({ ...p, full_name: e.target.value }))}
                  placeholder={formData.client_type === 'individual' ? 'Иванов Иван Иванович' : 'ООО "Компания"'}
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Город доставки</Label>
                <Input
                  data-testid="delivery-city-input"
                  value={formData.delivery_city}
                  onChange={(e) => setFormData(p => ({ ...p, delivery_city: e.target.value }))}
                  placeholder="Минск"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6" data-testid="step-2-car-params">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Car size={20} className="text-[#00E5FF]" />
              Раздел 2: Параметры автомобиля
            </h3>

            {/* 2.1 Основные характеристики */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                <span className="text-[#00E5FF]">2.1</span> Основные характеристики
              </h4>
              
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <Label className="text-slate-300">Марка автомобиля</Label>
                  <Input
                    data-testid="brand-input"
                    value={formData.brand}
                    onChange={(e) => setFormData(p => ({ ...p, brand: e.target.value }))}
                    placeholder="BYD, Zeekr, Li Auto..."
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Модель</Label>
                  <Input
                    data-testid="model-input"
                    value={formData.model}
                    onChange={(e) => setFormData(p => ({ ...p, model: e.target.value }))}
                    placeholder="Han, 001, L9..."
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <Label className="text-slate-300">Год выпуска от</Label>
                  <Input
                    type="number"
                    data-testid="year-from-input"
                    value={formData.year_from}
                    onChange={(e) => setFormData(p => ({ ...p, year_from: e.target.value }))}
                    placeholder="2020"
                    min="2015"
                    max="2026"
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Год выпуска до</Label>
                  <Input
                    type="number"
                    data-testid="year-to-input"
                    value={formData.year_to}
                    onChange={(e) => setFormData(p => ({ ...p, year_to: e.target.value }))}
                    placeholder="2026"
                    min="2015"
                    max="2026"
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
              </div>

              <div>
                <Label className="text-slate-300 mb-2 block">Тип кузова</Label>
                <div className="grid grid-cols-4 gap-2">
                  {bodyTypes.map(bt => (
                    <button
                      key={bt.value}
                      type="button"
                      data-testid={`body-type-${bt.value}`}
                      onClick={() => setFormData(p => ({ ...p, body_type: bt.value }))}
                      className={`p-2 rounded-sm border text-xs transition-all ${
                        formData.body_type === bt.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                          : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {bt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* 2.2 Двигатель и трансмиссия */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                <span className="text-[#00E5FF]">2.2</span> Двигатель и трансмиссия
              </h4>
              
              <div className="mb-4">
                <Label className="text-slate-300 mb-2 block">Тип двигателя</Label>
                <div className="grid grid-cols-3 gap-2">
                  {engineTypes.map(et => (
                    <button
                      key={et.value}
                      type="button"
                      data-testid={`engine-type-${et.value}`}
                      onClick={() => setFormData(p => ({ ...p, engine_type: et.value }))}
                      className={`p-2 rounded-sm border text-xs transition-all ${
                        formData.engine_type === et.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                          : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {et.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <Label className="text-slate-300">Объём двигателя (л)</Label>
                  <Select
                    value={formData.engine_volume}
                    onValueChange={(v) => setFormData(p => ({ ...p, engine_volume: v }))}
                  >
                    <SelectTrigger data-testid="engine-volume-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {engineVolumes.map(ev => (
                        <SelectItem key={ev.value} value={ev.value} className="text-white">{ev.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-slate-300">Тип КПП</Label>
                  <Select
                    value={formData.transmission}
                    onValueChange={(v) => setFormData(p => ({ ...p, transmission: v }))}
                  >
                    <SelectTrigger data-testid="transmission-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {transmissions.map(t => (
                        <SelectItem key={t.value} value={t.value} className="text-white">{t.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <Label className="text-slate-300">Мощность от (л.с.)</Label>
                  <Input
                    type="number"
                    data-testid="power-from-input"
                    value={formData.power_from}
                    onChange={(e) => setFormData(p => ({ ...p, power_from: e.target.value }))}
                    placeholder="150"
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Мощность до (л.с.)</Label>
                  <Input
                    type="number"
                    data-testid="power-to-input"
                    value={formData.power_to}
                    onChange={(e) => setFormData(p => ({ ...p, power_to: e.target.value }))}
                    placeholder="400"
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Тип привода</Label>
                  <Select
                    value={formData.drive_type}
                    onValueChange={(v) => setFormData(p => ({ ...p, drive_type: v }))}
                  >
                    <SelectTrigger data-testid="drive-type-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {driveTypes.map(d => (
                        <SelectItem key={d.value} value={d.value} className="text-white">{d.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* 2.3 Внешний вид */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                <span className="text-[#00E5FF]">2.3</span> Внешний вид
              </h4>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <Label className="text-slate-300">Цвет кузова</Label>
                  <Select
                    value={formData.body_color}
                    onValueChange={(v) => setFormData(p => ({ ...p, body_color: v }))}
                  >
                    <SelectTrigger data-testid="body-color-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {bodyColors.map(c => (
                        <SelectItem key={c.value} value={c.value} className="text-white">{c.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {formData.body_color === 'other' && (
                  <div>
                    <Label className="text-slate-300">Другой цвет</Label>
                    <Input
                      data-testid="body-color-other-input"
                      value={formData.body_color_other}
                      onChange={(e) => setFormData(p => ({ ...p, body_color_other: e.target.value }))}
                      placeholder="Укажите цвет"
                      className="mt-1 bg-[#15191E] border-[#27272A]"
                    />
                  </div>
                )}
              </div>

              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div>
                  <Label className="text-slate-300">Точный цвет (опционально)</Label>
                  <Input
                    data-testid="exact-color-input"
                    value={formData.exact_color}
                    onChange={(e) => setFormData(p => ({ ...p, exact_color: e.target.value }))}
                    placeholder="Например: Midnight Blue Pearl"
                    className="mt-1 bg-[#15191E] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Важность цвета</Label>
                  <Select
                    value={formData.color_importance}
                    onValueChange={(v) => setFormData(p => ({ ...p, color_importance: v }))}
                  >
                    <SelectTrigger data-testid="color-importance-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {colorImportance.map(ci => (
                        <SelectItem key={ci.value} value={ci.value} className="text-white">{ci.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <Label className="text-slate-300">Цвет салона</Label>
                  <Select
                    value={formData.interior_color}
                    onValueChange={(v) => setFormData(p => ({ ...p, interior_color: v }))}
                  >
                    <SelectTrigger data-testid="interior-color-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {interiorColors.map(ic => (
                        <SelectItem key={ic.value} value={ic.value} className="text-white">{ic.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                {formData.interior_color === 'other' && (
                  <div>
                    <Label className="text-slate-300">Другой цвет салона</Label>
                    <Input
                      data-testid="interior-color-other-input"
                      value={formData.interior_color_other}
                      onChange={(e) => setFormData(p => ({ ...p, interior_color_other: e.target.value }))}
                      placeholder="Укажите цвет"
                      className="mt-1 bg-[#15191E] border-[#27272A]"
                    />
                  </div>
                )}
                <div>
                  <Label className="text-slate-300">Материал салона</Label>
                  <Select
                    value={formData.interior_material}
                    onValueChange={(v) => setFormData(p => ({ ...p, interior_material: v }))}
                  >
                    <SelectTrigger data-testid="interior-material-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {interiorMaterials.map(im => (
                        <SelectItem key={im.value} value={im.value} className="text-white">{im.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6" data-testid="step-3-mileage">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Gauge size={20} className="text-[#00E5FF]" />
              Раздел 3: Пробег и состояние
            </h3>

            {/* 3.1 Пробег */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                <span className="text-[#00E5FF]">3.1</span> Пробег
              </h4>

              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Максимальный пробег</Label>
                  <Select
                    value={formData.mileage_max}
                    onValueChange={(v) => setFormData(p => ({ ...p, mileage_max: v }))}
                  >
                    <SelectTrigger data-testid="mileage-max-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {mileageOptions.map(mo => (
                        <SelectItem key={mo.value} value={mo.value} className="text-white">{mo.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label className="text-slate-300">Состояние авто</Label>
                  <Select
                    value={formData.car_condition}
                    onValueChange={(v) => setFormData(p => ({ ...p, car_condition: v }))}
                  >
                    <SelectTrigger data-testid="car-condition-select" className="mt-1 bg-[#15191E] border-[#27272A]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      {carConditions.map(cc => (
                        <SelectItem key={cc.value} value={cc.value} className="text-white">{cc.label}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>

            {/* 3.2 Допустимые повреждения */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4 flex items-center gap-2">
                <span className="text-[#00E5FF]">3.2</span> Допустимые повреждения
              </h4>

              <div className="flex items-start gap-3 mb-4">
                <Checkbox
                  id="allow_damage"
                  data-testid="allow-damage-checkbox"
                  checked={formData.allow_damage}
                  onCheckedChange={(checked) => setFormData(p => ({ ...p, allow_damage: checked }))}
                />
                <div>
                  <label htmlFor="allow_damage" className="text-white font-medium cursor-pointer">
                    Допускаются ли повреждения?
                  </label>
                  <p className="text-slate-400 text-sm">По умолчанию — нет, только идеальное состояние</p>
                </div>
              </div>

              {formData.allow_damage && (
                <div className="space-y-4 mt-4">
                  <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-sm">
                    <p className="text-amber-400 text-sm font-medium mb-2">Градация повреждений:</p>
                    <ul className="text-slate-400 text-xs space-y-1">
                      <li><span className="text-white">Уровень 1:</span> Мелкие царапины до 2 см, потёртости</li>
                      <li><span className="text-white">Уровень 2:</span> Царапины до металла (до 2 шт.), вмятины до 3 см</li>
                      <li><span className="text-white">Уровень 3:</span> Локальный перекрас, вмятины до 5 см</li>
                      <li><span className="text-red-400">Уровень 4 (НЕ ДОПУСКАЕТСЯ):</span> Нарушение геометрии, ДТП</li>
                    </ul>
                  </div>

                  <div>
                    <Label className="text-slate-300 mb-2 block">Допустимый уровень</Label>
                    <div className="space-y-2">
                      {damageLevels.map(dl => (
                        <button
                          key={dl.value}
                          type="button"
                          data-testid={`damage-level-${dl.value}`}
                          onClick={() => setFormData(p => ({ ...p, damage_level: dl.value }))}
                          className={`w-full p-3 rounded-sm border text-left transition-all ${
                            formData.damage_level === dl.value
                              ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                              : 'border-[#27272A] hover:border-slate-500'
                          }`}
                        >
                          <p className={`font-medium ${formData.damage_level === dl.value ? 'text-white' : 'text-slate-300'}`}>
                            {dl.label}
                          </p>
                          <p className="text-slate-500 text-xs">{dl.desc}</p>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label className="text-slate-300">Комментарий по повреждениям</Label>
                    <Textarea
                      data-testid="damage-comment-input"
                      value={formData.damage_comment}
                      onChange={(e) => setFormData(p => ({ ...p, damage_comment: e.target.value }))}
                      placeholder="Опишите дополнительные требования к состоянию..."
                      rows={2}
                      className="mt-1 bg-[#15191E] border-[#27272A]"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6" data-testid="step-4-options">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Settings size={20} className="text-[#00E5FF]" />
              Раздел 4: Дополнительные опции
            </h3>

            {/* Электронные системы */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <Monitor size={16} className="text-[#00E5FF]" />
                Электронные системы
              </h4>
              <div className="grid grid-cols-3 gap-2">
                {electronicOptions.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    data-testid={`option-electronic-${opt.value}`}
                    onClick={() => toggleOption('options_electronic', opt.value)}
                    className={`p-2 rounded-sm border text-xs transition-all ${
                      formData.options_electronic.includes(opt.value)
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                        : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Комфорт */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <Sofa size={16} className="text-[#00E5FF]" />
                Комфорт
              </h4>
              <div className="grid grid-cols-3 gap-2">
                {comfortOptions.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    data-testid={`option-comfort-${opt.value}`}
                    onClick={() => toggleOption('options_comfort', opt.value)}
                    className={`p-2 rounded-sm border text-xs transition-all ${
                      formData.options_comfort.includes(opt.value)
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                        : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Внешний вид */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <Sparkles size={16} className="text-[#00E5FF]" />
                Внешний вид
              </h4>
              <div className="grid grid-cols-4 gap-2">
                {exteriorOptions.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    data-testid={`option-exterior-${opt.value}`}
                    onClick={() => toggleOption('options_exterior', opt.value)}
                    className={`p-2 rounded-sm border text-xs transition-all ${
                      formData.options_exterior.includes(opt.value)
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                        : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Прочее */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                <Package size={16} className="text-[#00E5FF]" />
                Прочее
              </h4>
              <div className="grid grid-cols-4 gap-2">
                {otherOptions.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    data-testid={`option-other-${opt.value}`}
                    onClick={() => toggleOption('options_other', opt.value)}
                    className={`p-2 rounded-sm border text-xs transition-all ${
                      formData.options_other.includes(opt.value)
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                        : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Обязательные/Желательные опции */}
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Обязательные опции</Label>
                <Input
                  data-testid="required-options-input"
                  value={formData.required_options}
                  onChange={(e) => setFormData(p => ({ ...p, required_options: e.target.value }))}
                  placeholder="Например: панорама, кожа"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Желательные опции</Label>
                <Input
                  data-testid="preferred-options-input"
                  value={formData.preferred_options}
                  onChange={(e) => setFormData(p => ({ ...p, preferred_options: e.target.value }))}
                  placeholder="Например: массаж, HUD"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6" data-testid="step-5-budget">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <DollarSign size={20} className="text-[#00E5FF]" />
              Раздел 5: Бюджет и условия
            </h3>

            {/* Бюджет */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4">Бюджет</h4>
              
              <div className="grid md:grid-cols-3 gap-4 mb-4">
                <div>
                  <Label className="text-slate-300">Бюджет в Китае от (USD)</Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                    <Input
                      type="number"
                      data-testid="budget-china-from-input"
                      value={formData.budget_china_from}
                      onChange={(e) => setFormData(p => ({ ...p, budget_china_from: e.target.value }))}
                      placeholder="20000"
                      className="pl-7 bg-[#15191E] border-[#27272A]"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-slate-300">Бюджет в Китае до (USD)</Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                    <Input
                      type="number"
                      data-testid="budget-china-to-input"
                      value={formData.budget_china_to}
                      onChange={(e) => setFormData(p => ({ ...p, budget_china_to: e.target.value }))}
                      placeholder="40000"
                      className="pl-7 bg-[#15191E] border-[#27272A]"
                    />
                  </div>
                </div>
                <div>
                  <Label className="text-slate-300">Общий бюджет до (USD)</Label>
                  <div className="relative mt-1">
                    <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">$</span>
                    <Input
                      type="number"
                      data-testid="budget-total-input"
                      value={formData.budget_total}
                      onChange={(e) => setFormData(p => ({ ...p, budget_total: e.target.value }))}
                      placeholder="55000"
                      className="pl-7 bg-[#15191E] border-[#27272A]"
                    />
                  </div>
                  <p className="text-slate-500 text-xs mt-1">С доставкой и таможней</p>
                </div>
              </div>
            </div>

            {/* Условия */}
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300 mb-2 block">Срок покупки</Label>
                <div className="grid grid-cols-2 gap-2">
                  {purchaseTimelines.map(pt => (
                    <button
                      key={pt.value}
                      type="button"
                      data-testid={`timeline-${pt.value}`}
                      onClick={() => setFormData(p => ({ ...p, purchase_timeline: pt.value }))}
                      className={`p-3 rounded-sm border text-sm transition-all ${
                        formData.purchase_timeline === pt.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                          : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {pt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-slate-300 mb-2 block">Способ оплаты</Label>
                <div className="space-y-2">
                  {paymentMethods.map(pm => (
                    <button
                      key={pm.value}
                      type="button"
                      data-testid={`payment-${pm.value}`}
                      onClick={() => setFormData(p => ({ ...p, payment_method: pm.value }))}
                      className={`w-full p-3 rounded-sm border text-left text-sm transition-all ${
                        formData.payment_method === pm.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                          : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {pm.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300 mb-2 block">Назначение</Label>
                <div className="grid grid-cols-2 gap-2">
                  {carPurposes.map(cp => (
                    <button
                      key={cp.value}
                      type="button"
                      data-testid={`purpose-${cp.value}`}
                      onClick={() => setFormData(p => ({ ...p, car_purpose: cp.value }))}
                      className={`p-3 rounded-sm border text-sm transition-all ${
                        formData.car_purpose === cp.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                          : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {cp.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-slate-300 mb-2 block">Таможенная очистка</Label>
                <div className="space-y-2">
                  {customsClearanceOptions.map(cc => (
                    <button
                      key={cc.value}
                      type="button"
                      data-testid={`customs-${cc.value}`}
                      onClick={() => setFormData(p => ({ ...p, customs_clearance: cc.value }))}
                      className={`w-full p-3 rounded-sm border text-left text-sm transition-all ${
                        formData.customs_clearance === cc.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10 text-white'
                          : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                      }`}
                    >
                      {cc.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-6" data-testid="step-6-priorities">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Star size={20} className="text-[#00E5FF]" />
              Раздел 6: Приоритеты и комментарии
            </h3>

            {/* Приоритеты */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-4">
                Расставьте приоритеты (1-5, где 1 — самое важное)
              </h4>
              
              <div className="space-y-3">
                {[
                  { key: 'priority_price', label: 'Цена', icon: DollarSign },
                  { key: 'priority_reliability', label: 'Надёжность', icon: CheckCircle2 },
                  { key: 'priority_technology', label: 'Технологии', icon: Zap },
                  { key: 'priority_prestige', label: 'Престиж', icon: Star },
                  { key: 'priority_fuel', label: 'Экономия топлива', icon: Fuel }
                ].map(({ key, label, icon: Icon }) => (
                  <div key={key} className="flex items-center justify-between p-3 bg-[#15191E] rounded-sm border border-[#27272A]">
                    <div className="flex items-center gap-3">
                      <Icon size={18} className="text-[#00E5FF]" />
                      <span className="text-white">{label}</span>
                    </div>
                    <div className="flex gap-1">
                      {[1, 2, 3, 4, 5].map(num => (
                        <button
                          key={num}
                          type="button"
                          data-testid={`${key}-${num}`}
                          onClick={() => setFormData(p => ({ ...p, [key]: num }))}
                          className={`w-8 h-8 rounded-sm border text-sm transition-all ${
                            formData[key] === num
                              ? 'border-[#00E5FF] bg-[#00E5FF] text-black font-bold'
                              : 'border-[#27272A] text-slate-400 hover:border-slate-500'
                          }`}
                        >
                          {num}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Дополнительные пожелания */}
            <div>
              <Label className="text-slate-300">Дополнительные пожелания</Label>
              <Textarea
                data-testid="additional-requirements-input"
                value={formData.additional_requirements}
                onChange={(e) => setFormData(p => ({ ...p, additional_requirements: e.target.value }))}
                placeholder="Опишите любые дополнительные требования или пожелания к автомобилю..."
                rows={4}
                className="mt-1 bg-[#0B0F14] border-[#27272A]"
              />
            </div>

            {/* Сводка */}
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-sm">
              <h4 className="text-emerald-400 font-medium mb-3 flex items-center gap-2">
                <CheckCircle2 size={18} />
                Сводка заявки
              </h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-slate-400">Клиент:</div>
                <div className="text-white">{formData.full_name || '—'}</div>
                
                <div className="text-slate-400">Город доставки:</div>
                <div className="text-white">{formData.delivery_city || '—'}</div>
                
                {formData.brand && (
                  <>
                    <div className="text-slate-400">Авто:</div>
                    <div className="text-white">{formData.brand} {formData.model}</div>
                  </>
                )}
                
                {(formData.budget_china_from || formData.budget_china_to) && (
                  <>
                    <div className="text-slate-400">Бюджет в Китае:</div>
                    <div className="text-[#00E5FF]">
                      ${formData.budget_china_from || '—'} — ${formData.budget_china_to || '—'}
                    </div>
                  </>
                )}
                
                {formData.budget_total && (
                  <>
                    <div className="text-slate-400">Общий бюджет:</div>
                    <div className="text-[#00E5FF]">до ${formData.budget_total}</div>
                  </>
                )}
                
                <div className="text-slate-400">Срок:</div>
                <div className="text-white">
                  {purchaseTimelines.find(p => p.value === formData.purchase_timeline)?.label}
                </div>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const statusLabels = {
    new: { label: 'Новая', color: 'text-blue-400', bg: 'bg-blue-500/10' },
    in_progress: { label: 'В работе', color: 'text-amber-400', bg: 'bg-amber-500/10' },
    offers_received: { label: 'Есть предложения', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    completed: { label: 'Завершена', color: 'text-slate-400', bg: 'bg-slate-500/10' },
    cancelled: { label: 'Отменена', color: 'text-red-400', bg: 'bg-red-500/10' }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="loading-spinner">
        <Loader2 className="animate-spin text-[#00E5FF]" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="applications-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Заявки на подбор</h1>
          <p className="text-slate-400">Оформите заявку на подбор автомобиля из Китая</p>
        </div>
        <Button
          data-testid="create-application-btn"
          onClick={() => setShowForm(true)}
          className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
        >
          <Plus size={18} className="mr-2" />
          Оформить заявку
        </Button>
      </div>

      {/* Applications List */}
      {applications.length > 0 ? (
        <div className="space-y-4" data-testid="applications-list">
          {applications.map(app => {
            const status = statusLabels[app.status] || statusLabels.new;
            return (
              <div
                key={app.id}
                data-testid={`application-card-${app.id}`}
                className="bg-[#15191E] border border-[#27272A] rounded-sm p-4 hover:border-[#00E5FF]/30 transition-colors cursor-pointer"
                onClick={() => setSelectedApp(app)}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3 mb-1">
                      <p className="text-white font-medium">
                        {app.brand ? `${app.brand} ${app.model || ''}` : 'Любой автомобиль'}
                      </p>
                      {app.urgent && (
                        <span className="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded">Срочно</span>
                      )}
                    </div>
                    <p className="text-slate-400 text-sm">
                      Заявка {app.application_number} • {new Date(app.created_at).toLocaleDateString('ru-RU')}
                    </p>
                    {app.delivery_city && (
                      <p className="text-slate-500 text-xs flex items-center gap-1 mt-1">
                        <MapPin size={12} />
                        {app.delivery_city}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    {(app.budget_china_to || app.budget_total) && (
                      <div className="text-right">
                        <p className="text-[#00E5FF] font-medium">
                          {app.budget_total 
                            ? `до $${app.budget_total.toLocaleString()}`
                            : app.budget_china_to 
                              ? `$${app.budget_china_from?.toLocaleString() || '—'} - $${app.budget_china_to.toLocaleString()}`
                              : ''
                          }
                        </p>
                      </div>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs ${status.bg} ${status.color}`}>
                      {status.label}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm" data-testid="empty-state">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <p className="text-white font-medium mb-2">У вас пока нет заявок</p>
          <p className="text-slate-400 text-sm mb-6">
            Оформите заявку на подбор автомобиля и получите предложения от проверенных подрядчиков
          </p>
          <Button 
            onClick={() => setShowForm(true)} 
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            <Plus size={18} className="mr-2" />
            Оформить заявку
          </Button>
        </div>
      )}

      {/* Application Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-3xl max-h-[90vh] overflow-y-auto" data-testid="application-form-dialog">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Car size={20} className="text-[#00E5FF]" />
              Заявка на подбор автомобиля
            </DialogTitle>
          </DialogHeader>

          {/* Progress */}
          <div className="flex items-center gap-2 my-4">
            {[1, 2, 3, 4, 5, 6].map(step => (
              <div
                key={step}
                data-testid={`progress-step-${step}`}
                className={`flex-1 h-1 rounded-full transition-all ${
                  step <= currentStep ? 'bg-[#00E5FF]' : 'bg-[#27272A]'
                }`}
              />
            ))}
          </div>
          <div className="text-center text-slate-400 text-sm mb-4">
            Шаг {currentStep} из {totalSteps}
          </div>

          {renderStep()}

          {/* Navigation */}
          <div className="flex justify-between mt-6 pt-4 border-t border-[#27272A]">
            <Button
              variant="ghost"
              data-testid="prev-step-btn"
              onClick={() => setCurrentStep(s => s - 1)}
              disabled={currentStep === 1}
              className="text-slate-400"
            >
              <ChevronLeft size={18} className="mr-1" />
              Назад
            </Button>

            {currentStep < totalSteps ? (
              <Button
                data-testid="next-step-btn"
                onClick={() => setCurrentStep(s => s + 1)}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                Далее
                <ChevronRight size={18} className="ml-1" />
              </Button>
            ) : (
              <Button
                data-testid="submit-application-btn"
                onClick={handleSubmit}
                disabled={submitting || !formData.full_name}
                className="bg-emerald-500 hover:bg-emerald-600 text-white"
              >
                {submitting ? (
                  <Loader2 className="animate-spin mr-2" size={16} />
                ) : (
                  <CheckCircle2 size={16} className="mr-2" />
                )}
                Отправить заявку
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Application Details Dialog */}
      <Dialog open={!!selectedApp} onOpenChange={() => setSelectedApp(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-lg max-h-[80vh] overflow-y-auto" data-testid="application-details-dialog">
          <DialogHeader>
            <DialogTitle>Заявка {selectedApp?.application_number}</DialogTitle>
          </DialogHeader>
          
          {selectedApp && (
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="text-slate-400">Статус:</div>
                <div className={statusLabels[selectedApp.status]?.color}>
                  {statusLabels[selectedApp.status]?.label}
                </div>
                
                <div className="text-slate-400">Клиент:</div>
                <div className="text-white">{selectedApp.full_name}</div>
                
                {selectedApp.delivery_city && (
                  <>
                    <div className="text-slate-400">Город:</div>
                    <div className="text-white">{selectedApp.delivery_city}</div>
                  </>
                )}
                
                <div className="text-slate-400">Авто:</div>
                <div className="text-white">
                  {selectedApp.brand ? `${selectedApp.brand} ${selectedApp.model || ''}` : 'Любой'}
                </div>
                
                {selectedApp.body_type && (
                  <>
                    <div className="text-slate-400">Кузов:</div>
                    <div className="text-white">
                      {bodyTypes.find(b => b.value === selectedApp.body_type)?.label || selectedApp.body_type}
                    </div>
                  </>
                )}
                
                {selectedApp.engine_type && (
                  <>
                    <div className="text-slate-400">Двигатель:</div>
                    <div className="text-white">
                      {engineTypes.find(e => e.value === selectedApp.engine_type)?.label || selectedApp.engine_type}
                    </div>
                  </>
                )}
                
                {(selectedApp.budget_china_from || selectedApp.budget_china_to || selectedApp.budget_total) && (
                  <>
                    <div className="text-slate-400">Бюджет:</div>
                    <div className="text-[#00E5FF]">
                      {selectedApp.budget_total 
                        ? `до $${selectedApp.budget_total.toLocaleString()}`
                        : `$${selectedApp.budget_china_from?.toLocaleString() || '—'} - $${selectedApp.budget_china_to?.toLocaleString() || '—'}`
                      }
                    </div>
                  </>
                )}
                
                {selectedApp.purchase_timeline && (
                  <>
                    <div className="text-slate-400">Срок:</div>
                    <div className="text-white">
                      {purchaseTimelines.find(p => p.value === selectedApp.purchase_timeline)?.label || selectedApp.purchase_timeline}
                    </div>
                  </>
                )}
              </div>

              {selectedApp.additional_requirements && (
                <div className="p-3 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <p className="text-slate-400 text-xs mb-1">Пожелания:</p>
                  <p className="text-white text-sm">{selectedApp.additional_requirements}</p>
                </div>
              )}

              {/* Action Buttons for Active Applications */}
              {(selectedApp.status === 'new' || selectedApp.status === 'in_progress') && (
                <div className="space-y-3 pt-4 border-t border-[#27272A]">
                  {/* Manager Help */}
                  {!selectedApp.manager_assigned && (
                    <Button
                      data-testid="request-manager-help-btn"
                      onClick={() => requestManagerHelp(selectedApp.id)}
                      disabled={requestingManagerHelp || (accountSummary?.balance || 0) < 200}
                      className={`w-full ${
                        (accountSummary?.balance || 0) >= 200
                          ? 'bg-purple-500/20 text-purple-400 hover:bg-purple-500/30 border border-purple-500/30'
                          : 'bg-slate-700 text-slate-500 cursor-not-allowed'
                      }`}
                    >
                      {requestingManagerHelp ? (
                        <Loader2 size={16} className="mr-2 animate-spin" />
                      ) : (
                        <Headphones size={16} className="mr-2" />
                      )}
                      Помощь менеджера в подборе — $200
                    </Button>
                  )}
                  {selectedApp.manager_assigned && (
                    <div className="p-3 bg-purple-500/10 border border-purple-500/30 rounded-sm flex items-center gap-2">
                      <CheckCircle2 size={16} className="text-purple-400" />
                      <span className="text-purple-400 text-sm">Менеджер назначен для помощи в подборе</span>
                    </div>
                  )}

                  {/* Start Tender */}
                  {!selectedApp.tender_started && (
                    <Button
                      data-testid="start-tender-btn"
                      onClick={() => startTenderFromApplication(selectedApp.id)}
                      disabled={startingTender || !accountSummary?.contract_signed}
                      className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                    >
                      {startingTender ? (
                        <Loader2 size={16} className="mr-2 animate-spin" />
                      ) : (
                        <Send size={16} className="mr-2" />
                      )}
                      Запустить тендер
                    </Button>
                  )}
                  {!accountSummary?.contract_signed && !selectedApp.tender_started && (
                    <p className="text-amber-400 text-xs text-center">
                      Для запуска тендера необходимо подписать договор в разделе "Верификация"
                    </p>
                  )}
                  {selectedApp.tender_started && (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-sm flex items-center gap-2">
                      <CheckCircle2 size={16} className="text-emerald-400" />
                      <span className="text-emerald-400 text-sm">Тендер запущен</span>
                    </div>
                  )}

                  {/* View Tender Offers */}
                  {selectedApp.tender_started && (selectedApp.offers_count || 0) > 0 && (
                    <Button
                      onClick={() => {
                        setSelectedApp(null);
                        window.location.href = '/dashboard/tenders';
                      }}
                      variant="outline"
                      className="w-full border-[#27272A] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF]"
                    >
                      <Eye size={16} className="mr-2" />
                      Смотреть предложения ({selectedApp.offers_count})
                    </Button>
                  )}
                </div>
              )}

              {/* Cancel Button */}
              {selectedApp.status === 'new' && (
                <Button
                  data-testid="cancel-application-btn"
                  variant="outline"
                  onClick={() => cancelApplication(selectedApp.id)}
                  disabled={cancellingApp}
                  className="w-full mt-3 border-red-500/50 text-red-400 hover:bg-red-500/10"
                >
                  {cancellingApp ? (
                    <Loader2 size={16} className="mr-2 animate-spin" />
                  ) : (
                    <XCircle size={16} className="mr-2" />
                  )}
                  Отменить заявку
                </Button>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Applications;
