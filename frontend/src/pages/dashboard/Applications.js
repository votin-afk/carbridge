import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
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
  Phone,
  Mail,
  DollarSign,
  Calendar,
  Gauge,
  Fuel,
  Palette,
  Settings,
  FileText,
  CheckCircle2,
  Clock,
  AlertCircle,
  Loader2,
  Plus,
  ChevronRight,
  ChevronLeft,
  Zap,
  Users,
  Accessibility
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const bodyTypes = [
  { value: 'sedan', label: 'Седан' },
  { value: 'suv', label: 'Внедорожник (SUV)' },
  { value: 'crossover', label: 'Кроссовер' },
  { value: 'hatchback', label: 'Хэтчбек' },
  { value: 'minivan', label: 'Минивэн' },
  { value: 'coupe', label: 'Купе' },
  { value: 'wagon', label: 'Универсал' },
  { value: 'pickup', label: 'Пикап' }
];

const engineTypes = [
  { value: 'ice', label: 'Бензин/Дизель', icon: Fuel },
  { value: 'hybrid', label: 'Гибрид', icon: Zap },
  { value: 'electric', label: 'Электро', icon: Zap },
  { value: 'any', label: 'Любой', icon: Settings }
];

const transmissions = [
  { value: 'auto', label: 'Автомат' },
  { value: 'manual', label: 'Механика' },
  { value: 'any', label: 'Любая' }
];

const driveTypes = [
  { value: 'fwd', label: 'Передний' },
  { value: 'rwd', label: 'Задний' },
  { value: 'awd', label: 'Полный' },
  { value: 'any', label: 'Любой' }
];

const contactMethods = [
  { value: 'phone', label: 'Телефон' },
  { value: 'whatsapp', label: 'WhatsApp' },
  { value: 'telegram', label: 'Telegram' },
  { value: 'viber', label: 'Viber' },
  { value: 'email', label: 'Email' }
];

const paymentMethods = [
  { value: 'full', label: 'Полная оплата', desc: 'Оплата 100% стоимости' },
  { value: 'leasing', label: 'Лизинг', desc: 'Рассрочка через лизинговую компанию' },
  { value: 'credit', label: 'Кредит', desc: 'Банковский кредит' }
];

const Applications = () => {
  const { token, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [applications, setApplications] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [selectedApp, setSelectedApp] = useState(null);

  const [formData, setFormData] = useState({
    // Personal
    client_type: 'individual',
    full_name: user?.name || '',
    phone: user?.phone || '',
    email: user?.email || '',
    preferred_contact: 'phone',
    // Car preferences
    brand: '',
    model: '',
    body_type: '',
    engine_type: 'any',
    year_from: '',
    year_to: '',
    mileage_max: '',
    // Budget
    budget_min: '',
    budget_max: '',
    budget_currency: 'BYN',
    // Additional
    color_preferences: '',
    transmission: 'any',
    drive_type: 'any',
    // Special
    has_decree_140: false,
    decree_140_category: '',
    // Financing
    payment_method: 'full',
    needs_manager_help: false,
    // Notes
    additional_requirements: '',
    urgent: false
  });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchApplications();
  }, []);

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

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const payload = {
        ...formData,
        year_from: formData.year_from ? parseInt(formData.year_from) : null,
        year_to: formData.year_to ? parseInt(formData.year_to) : null,
        mileage_max: formData.mileage_max ? parseInt(formData.mileage_max) : null,
        budget_min: formData.budget_min ? parseFloat(formData.budget_min) : null,
        budget_max: formData.budget_max ? parseFloat(formData.budget_max) : null
      };
      
      await axios.post(`${API}/applications/create`, payload, { headers });
      toast.success('Заявка успешно создана!');
      setShowForm(false);
      setCurrentStep(1);
      fetchApplications();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка создания заявки');
    } finally {
      setSubmitting(false);
    }
  };

  const cancelApplication = async (appId) => {
    try {
      await axios.delete(`${API}/applications/${appId}`, { headers });
      toast.success('Заявка отменена');
      fetchApplications();
    } catch (error) {
      toast.error('Не удалось отменить заявку');
    }
  };

  const totalSteps = 5;

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <User size={20} className="text-[#00E5FF]" />
              Шаг 1: Контактные данные
            </h3>
            
            {/* Client Type */}
            <div>
              <Label className="text-slate-300 mb-2 block">Тип клиента</Label>
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
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
                <Label className="text-slate-300">ФИО *</Label>
                <Input
                  value={formData.full_name}
                  onChange={(e) => setFormData(p => ({ ...p, full_name: e.target.value }))}
                  placeholder="Иванов Иван Иванович"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Телефон *</Label>
                <Input
                  value={formData.phone}
                  onChange={(e) => setFormData(p => ({ ...p, phone: e.target.value }))}
                  placeholder="+375 29 123 45 67"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Email *</Label>
                <Input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(p => ({ ...p, email: e.target.value }))}
                  placeholder="email@example.com"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Предпочтительный способ связи</Label>
                <Select
                  value={formData.preferred_contact}
                  onValueChange={(v) => setFormData(p => ({ ...p, preferred_contact: v }))}
                >
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#15191E] border-[#27272A]">
                    {contactMethods.map(m => (
                      <SelectItem key={m.value} value={m.value} className="text-white">{m.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Car size={20} className="text-[#00E5FF]" />
              Шаг 2: Параметры автомобиля
            </h3>

            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Марка</Label>
                <Input
                  value={formData.brand}
                  onChange={(e) => setFormData(p => ({ ...p, brand: e.target.value }))}
                  placeholder="BYD, Zeekr, Li Auto..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Модель</Label>
                <Input
                  value={formData.model}
                  onChange={(e) => setFormData(p => ({ ...p, model: e.target.value }))}
                  placeholder="Han, 001, L9..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
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
                    onClick={() => setFormData(p => ({ ...p, body_type: bt.value }))}
                    className={`p-3 rounded-sm border text-sm transition-all ${
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

            <div>
              <Label className="text-slate-300 mb-2 block">Тип двигателя</Label>
              <div className="grid grid-cols-4 gap-2">
                {engineTypes.map(et => {
                  const Icon = et.icon;
                  return (
                    <button
                      key={et.value}
                      type="button"
                      onClick={() => setFormData(p => ({ ...p, engine_type: et.value }))}
                      className={`p-3 rounded-sm border transition-all ${
                        formData.engine_type === et.value
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                          : 'border-[#27272A] hover:border-slate-500'
                      }`}
                    >
                      <Icon size={20} className={formData.engine_type === et.value ? 'text-[#00E5FF]' : 'text-slate-400'} />
                      <p className={`mt-1 text-sm ${formData.engine_type === et.value ? 'text-white' : 'text-slate-400'}`}>
                        {et.label}
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <Label className="text-slate-300">Год от</Label>
                <Input
                  type="number"
                  value={formData.year_from}
                  onChange={(e) => setFormData(p => ({ ...p, year_from: e.target.value }))}
                  placeholder="2020"
                  min="2015"
                  max="2026"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Год до</Label>
                <Input
                  type="number"
                  value={formData.year_to}
                  onChange={(e) => setFormData(p => ({ ...p, year_to: e.target.value }))}
                  placeholder="2026"
                  min="2015"
                  max="2026"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Пробег до (км)</Label>
                <Input
                  type="number"
                  value={formData.mileage_max}
                  onChange={(e) => setFormData(p => ({ ...p, mileage_max: e.target.value }))}
                  placeholder="50000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <DollarSign size={20} className="text-[#00E5FF]" />
              Шаг 3: Бюджет
            </h3>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <Label className="text-slate-300">Бюджет от</Label>
                <Input
                  type="number"
                  value={formData.budget_min}
                  onChange={(e) => setFormData(p => ({ ...p, budget_min: e.target.value }))}
                  placeholder="50000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Бюджет до</Label>
                <Input
                  type="number"
                  value={formData.budget_max}
                  onChange={(e) => setFormData(p => ({ ...p, budget_max: e.target.value }))}
                  placeholder="100000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Валюта</Label>
                <Select
                  value={formData.budget_currency}
                  onValueChange={(v) => setFormData(p => ({ ...p, budget_currency: v }))}
                >
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#15191E] border-[#27272A]">
                    <SelectItem value="BYN" className="text-white">BYN (бел. руб.)</SelectItem>
                    <SelectItem value="USD" className="text-white">USD ($)</SelectItem>
                    <SelectItem value="EUR" className="text-white">EUR (€)</SelectItem>
                    <SelectItem value="CNY" className="text-white">CNY (¥)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label className="text-slate-300 mb-2 block">Способ оплаты</Label>
              <div className="space-y-2">
                {paymentMethods.map(pm => (
                  <button
                    key={pm.value}
                    type="button"
                    onClick={() => setFormData(p => ({ ...p, payment_method: pm.value }))}
                    className={`w-full p-4 rounded-sm border text-left transition-all ${
                      formData.payment_method === pm.value
                        ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                        : 'border-[#27272A] hover:border-slate-500'
                    }`}
                  >
                    <p className={`font-medium ${formData.payment_method === pm.value ? 'text-white' : 'text-slate-300'}`}>
                      {pm.label}
                    </p>
                    <p className="text-slate-500 text-sm">{pm.desc}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Settings size={20} className="text-[#00E5FF]" />
              Шаг 4: Дополнительные параметры
            </h3>

            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <Label className="text-slate-300">Коробка передач</Label>
                <Select
                  value={formData.transmission}
                  onValueChange={(v) => setFormData(p => ({ ...p, transmission: v }))}
                >
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#15191E] border-[#27272A]">
                    {transmissions.map(t => (
                      <SelectItem key={t.value} value={t.value} className="text-white">{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">Привод</Label>
                <Select
                  value={formData.drive_type}
                  onValueChange={(v) => setFormData(p => ({ ...p, drive_type: v }))}
                >
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-[#15191E] border-[#27272A]">
                    {driveTypes.map(d => (
                      <SelectItem key={d.value} value={d.value} className="text-white">{d.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-slate-300">Предпочтения по цвету</Label>
                <Input
                  value={formData.color_preferences}
                  onChange={(e) => setFormData(p => ({ ...p, color_preferences: e.target.value }))}
                  placeholder="Белый, чёрный..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
            </div>

            {/* Decree 140 */}
            <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-sm">
              <div className="flex items-start gap-3">
                <Checkbox
                  id="decree140"
                  checked={formData.has_decree_140}
                  onCheckedChange={(checked) => setFormData(p => ({ ...p, has_decree_140: checked }))}
                />
                <div>
                  <label htmlFor="decree140" className="text-white font-medium cursor-pointer">
                    Указ №140 (льготы на растаможку)
                  </label>
                  <p className="text-slate-400 text-sm mt-1">
                    Скидка 50% на таможенные пошлины для льготных категорий граждан
                  </p>
                </div>
              </div>

              {formData.has_decree_140 && (
                <div className="mt-4 ml-7">
                  <Label className="text-slate-300">Категория льготы</Label>
                  <Select
                    value={formData.decree_140_category}
                    onValueChange={(v) => setFormData(p => ({ ...p, decree_140_category: v }))}
                  >
                    <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A]">
                      <SelectValue placeholder="Выберите категорию" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#15191E] border-[#27272A]">
                      <SelectItem value="many_children" className="text-white">
                        <div className="flex items-center gap-2">
                          <Users size={14} />
                          Многодетная семья
                        </div>
                      </SelectItem>
                      <SelectItem value="disabled_1_2" className="text-white">
                        <div className="flex items-center gap-2">
                          <Accessibility size={14} />
                          Инвалид I-II группы
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              )}
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <FileText size={20} className="text-[#00E5FF]" />
              Шаг 5: Дополнительная информация
            </h3>

            <div>
              <Label className="text-slate-300">Дополнительные пожелания</Label>
              <Textarea
                value={formData.additional_requirements}
                onChange={(e) => setFormData(p => ({ ...p, additional_requirements: e.target.value }))}
                placeholder="Опишите любые дополнительные требования к автомобилю..."
                rows={4}
                className="mt-1 bg-[#0B0F14] border-[#27272A]"
              />
            </div>

            <div className="flex items-start gap-3">
              <Checkbox
                id="manager_help"
                checked={formData.needs_manager_help}
                onCheckedChange={(checked) => setFormData(p => ({ ...p, needs_manager_help: checked }))}
              />
              <div>
                <label htmlFor="manager_help" className="text-white font-medium cursor-pointer">
                  Нужна помощь менеджера
                </label>
                <p className="text-slate-400 text-sm">Персональный менеджер поможет с подбором и ответит на вопросы</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Checkbox
                id="urgent"
                checked={formData.urgent}
                onCheckedChange={(checked) => setFormData(p => ({ ...p, urgent: checked }))}
              />
              <div>
                <label htmlFor="urgent" className="text-amber-400 font-medium cursor-pointer">
                  Срочная заявка
                </label>
                <p className="text-slate-400 text-sm">Пометить заявку как срочную для приоритетной обработки</p>
              </div>
            </div>

            {/* Summary */}
            <div className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
              <h4 className="text-white font-medium mb-3">Сводка заявки:</h4>
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div className="text-slate-400">Клиент:</div>
                <div className="text-white">{formData.full_name}</div>
                
                {formData.brand && (
                  <>
                    <div className="text-slate-400">Авто:</div>
                    <div className="text-white">{formData.brand} {formData.model}</div>
                  </>
                )}
                
                {formData.budget_max && (
                  <>
                    <div className="text-slate-400">Бюджет:</div>
                    <div className="text-[#00E5FF]">
                      {formData.budget_min ? `${formData.budget_min} - ` : 'до '}{formData.budget_max} {formData.budget_currency}
                    </div>
                  </>
                )}
                
                <div className="text-slate-400">Оплата:</div>
                <div className="text-white">{paymentMethods.find(p => p.value === formData.payment_method)?.label}</div>
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
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#00E5FF]" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Заявки на подбор</h1>
          <p className="text-slate-400">Оформите заявку и получите предложения от подрядчиков</p>
        </div>
        <Button
          onClick={() => setShowForm(true)}
          className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
        >
          <Plus size={18} className="mr-2" />
          Оформить заявку
        </Button>
      </div>

      {/* Applications List */}
      {applications.length > 0 ? (
        <div className="space-y-4">
          {applications.map(app => {
            const status = statusLabels[app.status] || statusLabels.new;
            return (
              <div
                key={app.id}
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
                  </div>
                  <div className="flex items-center gap-4">
                    {app.budget_max && (
                      <div className="text-right">
                        <p className="text-[#00E5FF] font-medium">
                          {app.budget_min ? `${app.budget_min.toLocaleString()} - ` : 'до '}
                          {app.budget_max.toLocaleString()} {app.budget_currency}
                        </p>
                      </div>
                    )}
                    <span className={`px-3 py-1 rounded-full text-xs ${status.bg} ${status.color}`}>
                      {status.label}
                    </span>
                    {app.offers_count > 0 && (
                      <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded">
                        {app.offers_count} предложений
                      </span>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <p className="text-white font-medium mb-2">У вас пока нет заявок</p>
          <p className="text-slate-400 text-sm mb-6">Оформите заявку на подбор автомобиля и получите предложения от проверенных подрядчиков</p>
          <Button onClick={() => setShowForm(true)} className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
            <Plus size={18} className="mr-2" />
            Оформить заявку
          </Button>
        </div>
      )}

      {/* Application Form Dialog */}
      <Dialog open={showForm} onOpenChange={setShowForm}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Car size={20} className="text-[#00E5FF]" />
              Заявка на подбор автомобиля
            </DialogTitle>
          </DialogHeader>

          {/* Progress */}
          <div className="flex items-center gap-2 my-4">
            {[1, 2, 3, 4, 5].map(step => (
              <div
                key={step}
                className={`flex-1 h-1 rounded-full ${
                  step <= currentStep ? 'bg-[#00E5FF]' : 'bg-[#27272A]'
                }`}
              />
            ))}
          </div>

          {renderStep()}

          {/* Navigation */}
          <div className="flex justify-between mt-6 pt-4 border-t border-[#27272A]">
            <Button
              variant="ghost"
              onClick={() => setCurrentStep(s => s - 1)}
              disabled={currentStep === 1}
              className="text-slate-400"
            >
              <ChevronLeft size={18} className="mr-1" />
              Назад
            </Button>

            {currentStep < totalSteps ? (
              <Button
                onClick={() => setCurrentStep(s => s + 1)}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                Далее
                <ChevronRight size={18} className="ml-1" />
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitting || !formData.full_name || !formData.phone || !formData.email}
                className="bg-emerald-500 hover:bg-emerald-600 text-white"
              >
                {submitting ? <Loader2 className="animate-spin mr-2" size={16} /> : <CheckCircle2 size={16} className="mr-2" />}
                Отправить заявку
              </Button>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Application Details Dialog */}
      <Dialog open={!!selectedApp} onOpenChange={() => setSelectedApp(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-lg">
          <DialogHeader>
            <DialogTitle>Заявка {selectedApp?.application_number}</DialogTitle>
          </DialogHeader>
          
          {selectedApp && (
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="text-slate-400">Статус:</div>
                <div className={statusLabels[selectedApp.status]?.color}>
                  {statusLabels[selectedApp.status]?.label}
                </div>
                
                <div className="text-slate-400">Авто:</div>
                <div className="text-white">
                  {selectedApp.brand ? `${selectedApp.brand} ${selectedApp.model || ''}` : 'Любой'}
                </div>
                
                <div className="text-slate-400">Бюджет:</div>
                <div className="text-[#00E5FF]">
                  {selectedApp.budget_max 
                    ? `${selectedApp.budget_min || 0} - ${selectedApp.budget_max} ${selectedApp.budget_currency}`
                    : 'Не указан'
                  }
                </div>
                
                <div className="text-slate-400">Предложений:</div>
                <div className="text-white">{selectedApp.offers_count || 0}</div>
              </div>

              {selectedApp.status === 'new' && (
                <Button
                  variant="outline"
                  onClick={() => {
                    cancelApplication(selectedApp.id);
                    setSelectedApp(null);
                  }}
                  className="w-full border-red-500/50 text-red-400 hover:bg-red-500/10"
                >
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
