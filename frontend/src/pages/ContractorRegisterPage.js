import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { 
  ArrowLeft,
  Building2,
  ClipboardCheck,
  Package,
  Truck,
  CheckCircle2,
  Loader2,
  Phone,
  Mail,
  Globe,
  Send,
  Upload,
  X,
  FileText
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Services matching deal stages
const serviceOptions = [
  { value: 'leasing', label: 'Лизинг', description: 'Лизинговые услуги для покупки авто', isLeasing: true },
  { value: 'inspection', label: 'Инспекция авто', description: 'Техническая проверка автомобилей' },
  { value: 'export', label: 'Выкуп и экспорт', description: 'Выкуп автомобиля и таможенное оформление в КНР' },
  { value: 'logistics_china', label: 'Доставка до порта (Китай)', description: 'Логистика до порта отправления' },
  { value: 'insurance', label: 'Страхование авто', description: 'Страхование на время транспортировки' },
  { value: 'delivery_rb', label: 'Доставка в Беларусь', description: 'Морская/ж/д доставка из Китая в РБ' },
  { value: 'customs', label: 'Таможенное оформление', description: 'Растаможка и оформление в Беларуси' },
  { value: 'legal_belarus', label: 'Юридические услуги (Беларусь)', description: 'Юридическая помощь в Беларуси' },
  { value: 'legal_china', label: 'Юридические услуги (Китай)', description: 'Юридическая помощь в Китае' }
];

// Leasing currency options
const leasingCurrencies = [
  { value: 'USD', label: 'USD ($)' },
  { value: 'EUR', label: 'EUR (€)' },
  { value: 'CNY', label: 'CNY (¥)' },
  { value: 'BYN', label: 'BYN (Br)' }
];

const contractorTypes = {
  inspection: {
    label: 'Проверка авто',
    icon: ClipboardCheck,
    description: 'Техническая проверка автомобилей перед покупкой'
  },
  export: {
    label: 'Экспорт',
    icon: Package,
    description: 'Оформление и выкуп автомобилей в Китае'
  },
  logistics: {
    label: 'Логистика',
    icon: Truck,
    description: 'Доставка автомобилей из Китая в Беларусь'
  }
};

const ContractorRegisterPage = () => {
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [applicationFiles, setApplicationFiles] = useState([]);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  
  const [formData, setFormData] = useState({
    // Step 1 - Company Info
    company_name: '',
    country: 'CN', // BY or CN
    contractor_type: '',
    registration_number: '',
    legal_address: '',
    
    // Step 2 - Contact Info & Login
    contact_person: '',
    position: '',
    phone: '',
    email: '',
    password: '',       // Password for contractor login
    password_confirm: '', // Password confirmation
    whatsapp: '',
    wechat: '',
    telegram: '',
    website: '',
    
    // Step 3 - Services (multiple selection)
    services: [],
    description: '',
    experience_years: '',
    
    // Step 4 - Service Prices
    service_prices: {
      inspection: '',
      export: '',
      logistics_china: '',
      insurance: '',
      delivery_rb: '',
      customs: ''
    },
    // Leasing specific fields
    leasing_rate: '', // Percentage
    leasing_currency: 'USD',
    
    // Step 5 - Documents
    license_info: '',
    additional_info: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handlePriceChange = (service, value) => {
    setFormData(prev => ({
      ...prev,
      service_prices: {
        ...prev.service_prices,
        [service]: value
      }
    }));
  };

  const selectType = (type) => {
    setFormData(prev => ({ ...prev, contractor_type: type }));
  };

  const nextStep = () => {
    if (step === 1 && (!formData.company_name || !formData.country)) {
      toast.error('Заполните название компании и выберите страну');
      return;
    }
    if (step === 2 && (!formData.contact_person || !formData.phone || !formData.email || !formData.password)) {
      toast.error('Заполните контактные данные и пароль');
      return;
    }
    if (step === 2 && formData.password !== formData.password_confirm) {
      toast.error('Пароли не совпадают');
      return;
    }
    if (step === 2 && formData.password.length < 6) {
      toast.error('Пароль должен быть не менее 6 символов');
      return;
    }
    if (step === 3 && (formData.services.length === 0 || !formData.description)) {
      toast.error('Выберите услуги и добавьте описание');
      return;
    }
    if (step === 4) {
      // Validate prices for selected services (excluding leasing which has special fields)
      const nonLeasingServices = formData.services.filter(s => s !== 'leasing');
      const missingPrices = nonLeasingServices.filter(s => !formData.service_prices[s] || parseFloat(formData.service_prices[s]) <= 0);
      if (missingPrices.length > 0) {
        toast.error('Укажите стоимость для всех выбранных услуг');
        return;
      }
      // Validate leasing if selected
      if (formData.services.includes('leasing') && (!formData.leasing_rate || parseFloat(formData.leasing_rate) <= 0)) {
        toast.error('Укажите процентную ставку по лизингу');
        return;
      }
    }
    setStep(step + 1);
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // Prepare service prices - only for selected services
      const prices = {};
      formData.services.forEach(service => {
        if (service === 'leasing') {
          // For leasing, store rate and currency
          prices.leasing = {
            rate: parseFloat(formData.leasing_rate),
            currency: formData.leasing_currency
          };
        } else if (formData.service_prices[service]) {
          prices[service] = parseFloat(formData.service_prices[service]);
        }
      });

      const response = await axios.post(`${API}/contractors/register`, {
        company_name: formData.company_name,
        country: formData.country,
        registration_number: formData.registration_number,
        legal_address: formData.legal_address,
        contact_person: formData.contact_person,
        position: formData.position,
        phone: formData.phone,
        email: formData.email,
        password: formData.password,
        whatsapp: formData.whatsapp,
        wechat: formData.wechat,
        telegram: formData.telegram,
        website: formData.website,
        services: formData.services,
        service_prices: prices,
        description: formData.description,
        experience_years: formData.experience_years ? parseInt(formData.experience_years) : null
      });
      
      // Upload files if any
      const appId = response.data?.application_id;
      if (appId && applicationFiles.length > 0) {
        setUploadingFiles(true);
        for (const f of applicationFiles) {
          const fd = new FormData();
          fd.append('file', f.file);
          fd.append('category', f.category);
          fd.append('title', f.title || f.file.name);
          try {
            await axios.post(`${API}/contractor-applications/${appId}/files`, fd, {
              headers: { 'Content-Type': 'multipart/form-data' }
            });
          } catch (err) {
            console.error('File upload error:', err);
          }
        }
        setUploadingFiles(false);
      }
      
      setSubmitted(true);
      toast.success('Заявка отправлена!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при отправке заявки');
    } finally {
      setSubmitting(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center p-4">
        <div className="max-w-md w-full text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-emerald-500/10 rounded-full flex items-center justify-center">
            <CheckCircle2 size={40} className="text-emerald-400" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-4">Заявка отправлена!</h1>
          <p className="text-slate-400 mb-8">
            Спасибо за регистрацию! Наш модератор рассмотрит вашу заявку и свяжется с вами 
            для уточнения деталей и верификации компании.
          </p>
          <p className="text-slate-500 text-sm mb-6">
            Обычно проверка занимает 1-3 рабочих дня
          </p>
          <Link to="/contractors">
            <Button className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
              Вернуться к списку подрядчиков
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0F14] py-12">
      <div className="max-w-2xl mx-auto px-4">
        {/* Back Button */}
        <Link to="/contractors">
          <Button variant="ghost" className="text-slate-400 hover:text-white mb-6">
            <ArrowLeft size={18} className="mr-2" />
            К списку подрядчиков
          </Button>
        </Link>

        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
            <Building2 size={32} className="text-[#00E5FF]" />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">Регистрация подрядчика</h1>
          <p className="text-slate-400">
            Заполните форму для регистрации на платформе CARBRIDGE
          </p>
        </div>

        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-2 mb-8">
          {[1, 2, 3, 4, 5].map((s) => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                s === step 
                  ? 'bg-[#00E5FF] text-black' 
                  : s < step 
                    ? 'bg-emerald-500 text-white' 
                    : 'bg-[#27272A] text-slate-500'
              }`}>
                {s < step ? <CheckCircle2 size={16} /> : s}
              </div>
              {s < 5 && (
                <div className={`w-12 h-0.5 ${s < step ? 'bg-emerald-500' : 'bg-[#27272A]'}`} />
              )}
            </div>
          ))}
        </div>

        {/* Form Card */}
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
          {/* Step 1 - Company Info */}
          {step === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-white mb-4">Информация о компании</h2>
                
                <div className="space-y-4">
                  <div>
                    <Label className="text-slate-300">Название компании *</Label>
                    <Input
                      name="company_name"
                      value={formData.company_name}
                      onChange={handleChange}
                      placeholder="ООО Компания / 公司名称"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>

                  <div>
                    <Label className="text-slate-300">Страна регистрации *</Label>
                    <div className="grid grid-cols-2 gap-3 mt-2">
                      <button
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, country: 'BY' }))}
                        className={`p-4 rounded-sm border text-left transition-all ${
                          formData.country === 'BY'
                            ? 'bg-[#00E5FF]/10 border-[#00E5FF] text-white'
                            : 'bg-[#0B0F14] border-[#27272A] text-slate-400 hover:border-slate-500'
                        }`}
                      >
                        <span className="text-2xl">🇧🇾</span>
                        <p className="font-medium mt-2">Беларусь</p>
                        <p className="text-xs text-slate-500 mt-1">УНП регистрация</p>
                      </button>
                      <button
                        type="button"
                        onClick={() => setFormData(prev => ({ ...prev, country: 'CN' }))}
                        className={`p-4 rounded-sm border text-left transition-all ${
                          formData.country === 'CN'
                            ? 'bg-[#00E5FF]/10 border-[#00E5FF] text-white'
                            : 'bg-[#0B0F14] border-[#27272A] text-slate-400 hover:border-slate-500'
                        }`}
                      >
                        <span className="text-2xl">🇨🇳</span>
                        <p className="font-medium mt-2">Китай</p>
                        <p className="text-xs text-slate-500 mt-1">USCI регистрация</p>
                      </button>
                    </div>
                  </div>

                  <div>
                    <Label className="text-slate-300">
                      {formData.country === 'BY' ? 'УНП' : 'Регистрационный номер (USCI)'}
                    </Label>
                    <Input
                      name="registration_number"
                      value={formData.registration_number}
                      onChange={handleChange}
                      placeholder={formData.country === 'BY' ? '123456789' : '91310000MA1FL5XX0L'}
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>

                  <div>
                    <Label className="text-slate-300">Юридический адрес</Label>
                    <Input
                      name="legal_address"
                      value={formData.legal_address}
                      onChange={handleChange}
                      placeholder={formData.country === 'BY' ? 'г. Минск, ул. Примерная, д. 1' : '上海市浦东新区XX路XX号'}
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 2 - Contacts */}
          {step === 2 && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-white mb-4">Контактная информация</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300">Контактное лицо *</Label>
                    <Input
                      name="contact_person"
                      value={formData.contact_person}
                      onChange={handleChange}
                      placeholder="Иван Иванов"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">Должность</Label>
                    <Input
                      name="position"
                      value={formData.position}
                      onChange={handleChange}
                      placeholder="Директор"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300">Телефон *</Label>
                    <div className="relative mt-1">
                      <Phone size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                      <Input
                        name="phone"
                        value={formData.phone}
                        onChange={handleChange}
                        placeholder="+86..."
                        className="pl-9 bg-[#0B0F14] border-[#27272A]"
                      />
                    </div>
                  </div>
                  <div>
                    <Label className="text-slate-300">Email *</Label>
                    <div className="relative mt-1">
                      <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                      <Input
                        name="email"
                        type="email"
                        value={formData.email}
                        onChange={handleChange}
                        placeholder="info@company.com"
                        className="pl-9 bg-[#0B0F14] border-[#27272A]"
                      />
                    </div>
                  </div>
                </div>

                {/* Password fields */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-300">Пароль для входа *</Label>
                    <Input
                      name="password"
                      type="password"
                      value={formData.password}
                      onChange={handleChange}
                      placeholder="Минимум 6 символов"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                    <p className="text-slate-500 text-xs mt-1">Используйте этот пароль для входа после одобрения</p>
                  </div>
                  <div>
                    <Label className="text-slate-300">Подтверждение пароля *</Label>
                    <Input
                      name="password_confirm"
                      type="password"
                      value={formData.password_confirm}
                      onChange={handleChange}
                      placeholder="Повторите пароль"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label className="text-slate-300">WhatsApp</Label>
                    <Input
                      name="whatsapp"
                      value={formData.whatsapp}
                      onChange={handleChange}
                      placeholder="+86..."
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">WeChat</Label>
                    <Input
                      name="wechat"
                      value={formData.wechat}
                      onChange={handleChange}
                      placeholder="wechat_id"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                  <div>
                    <Label className="text-slate-300">Telegram</Label>
                    <Input
                      name="telegram"
                      value={formData.telegram}
                      onChange={handleChange}
                      placeholder="@username"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>

                <div>
                  <Label className="text-slate-300">Сайт компании</Label>
                  <div className="relative mt-1">
                    <Globe size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <Input
                      name="website"
                      value={formData.website}
                      onChange={handleChange}
                      placeholder="https://company.com"
                      className="pl-9 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 3 - Services */}
          {step === 3 && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-white mb-4">Услуги и опыт</h2>
              
              <div className="space-y-4">
                <div>
                  <Label className="text-slate-300">Предоставляемые услуги * (выберите все применимые)</Label>
                  <div className="grid grid-cols-2 gap-3 mt-2">
                    {serviceOptions.map(({ value, label, description }) => {
                      const isSelected = formData.services.includes(value);
                      return (
                        <button
                          key={value}
                          type="button"
                          onClick={() => {
                            setFormData(prev => ({
                              ...prev,
                              services: isSelected
                                ? prev.services.filter(s => s !== value)
                                : [...prev.services, value]
                            }));
                          }}
                          className={`p-4 rounded-sm border text-left transition-all ${
                            isSelected
                              ? 'bg-[#00E5FF]/10 border-[#00E5FF] text-white'
                              : 'bg-[#0B0F14] border-[#27272A] text-slate-400 hover:border-slate-500'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <p className="font-medium">{label}</p>
                            {isSelected && <CheckCircle2 size={18} className="text-[#00E5FF]" />}
                          </div>
                          <p className="text-xs text-slate-500 mt-1">{description}</p>
                        </button>
                      );
                    })}
                  </div>
                  {formData.services.length > 0 && (
                    <p className="mt-2 text-sm text-[#00E5FF]">
                      Выбрано: {formData.services.length} услуг(и)
                    </p>
                  )}
                </div>

                <div>
                  <Label className="text-slate-300">Описание компании *</Label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    placeholder="Расскажите о вашей компании, специализации, преимуществах..."
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 min-h-[100px]"
                  />
                </div>

                <div>
                  <Label className="text-slate-300">Лет на рынке</Label>
                  <Input
                    name="experience_years"
                    type="number"
                    min="0"
                    value={formData.experience_years}
                    onChange={handleChange}
                    placeholder="5"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Step 4 - Service Prices */}
          {step === 4 && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-white mb-4">Стоимость услуг</h2>
              <p className="text-slate-400 text-sm mb-4">
                Укажите стоимость ваших услуг. Эта сумма будет отображаться клиентам при выборе подрядчика.
              </p>
              
              <div className="space-y-4">
                {formData.services.map(service => {
                  const serviceLabels = {
                    leasing: { name: '📋 Лизинг', desc: 'Укажите процентную ставку и валюту', isLeasing: true },
                    inspection: { name: '🔍 Инспекция авто', desc: 'Проверка технического состояния автомобиля' },
                    export: { name: '📦 Выкуп и экспорт', desc: 'Выкуп автомобиля и оформление экспорта из Китая' },
                    logistics_china: { name: '🚛 Доставка до порта (Китай)', desc: 'Логистика до порта отправления' },
                    insurance: { name: '🛡️ Страхование авто', desc: 'Страхование на время транспортировки' },
                    delivery_rb: { name: '🚢 Доставка в Беларусь', desc: 'Морская/ж/д доставка из Китая' },
                    customs: { name: '🏛️ Таможенное оформление', desc: 'Растаможка и оформление в Беларуси' }
                  };
                  const label = serviceLabels[service] || { name: service, desc: '' };
                  
                  // Special handling for leasing
                  if (service === 'leasing') {
                    return (
                      <div key={service} className="bg-[#0B0F14] border border-[#27272A] rounded-sm p-4">
                        <div className="mb-3">
                          <p className="text-white font-medium">{label.name}</p>
                          <p className="text-slate-500 text-sm">{label.desc}</p>
                        </div>
                        <div className="flex flex-wrap items-center gap-4">
                          <div className="flex items-center gap-2">
                            <Label className="text-slate-400">Ставка:</Label>
                            <Input
                              type="number"
                              min="0"
                              step="0.1"
                              value={formData.leasing_rate}
                              onChange={(e) => setFormData(prev => ({ ...prev, leasing_rate: e.target.value }))}
                              placeholder="12.5"
                              className="w-24 bg-[#15191E] border-[#27272A] text-right"
                            />
                            <span className="text-slate-400">% годовых</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Label className="text-slate-400">Валюта:</Label>
                            <select
                              value={formData.leasing_currency}
                              onChange={(e) => setFormData(prev => ({ ...prev, leasing_currency: e.target.value }))}
                              className="bg-[#15191E] border border-[#27272A] rounded-sm px-3 py-2 text-white"
                            >
                              {leasingCurrencies.map(curr => (
                                <option key={curr.value} value={curr.value}>{curr.label}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      </div>
                    );
                  }
                  
                  return (
                    <div key={service} className="bg-[#0B0F14] border border-[#27272A] rounded-sm p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{label.name}</p>
                          <p className="text-slate-500 text-sm">{label.desc}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-slate-400">$</span>
                          <Input
                            type="number"
                            min="0"
                            step="10"
                            value={formData.service_prices[service] || ''}
                            onChange={(e) => handlePriceChange(service, e.target.value)}
                            placeholder="0"
                            className="w-32 bg-[#15191E] border-[#27272A] text-right"
                          />
                          <span className="text-slate-400">USD</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {formData.services.length === 0 && (
                <div className="text-center py-8 text-slate-500">
                  <p>Вернитесь на предыдущий шаг и выберите услуги</p>
                </div>
              )}
            </div>
          )}

          {/* Step 5 - Final */}
          {step === 5 && (
            <div className="space-y-6">
              <h2 className="text-lg font-semibold text-white mb-4">Дополнительная информация</h2>
              
              <div className="space-y-4">
                <div>
                  <Label className="text-slate-300">Лицензии и сертификаты</Label>
                  <textarea
                    name="license_info"
                    value={formData.license_info}
                    onChange={handleChange}
                    placeholder="Укажите номера лицензий, сертификатов или другие документы..."
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 min-h-[80px]"
                  />
                </div>

                <div>
                  <Label className="text-slate-300">Дополнительная информация</Label>
                  <textarea
                    name="additional_info"
                    value={formData.additional_info}
                    onChange={handleChange}
                    placeholder="Любая дополнительная информация, которую вы хотите сообщить..."
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 min-h-[80px]"
                  />
                </div>

                {/* Summary */}
                <div className="bg-[#0B0F14] border border-[#27272A] rounded-sm p-4 mt-4">
                  <h3 className="text-white font-medium mb-3">Сводка заявки</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-500">Компания:</span>
                      <span className="text-white">{formData.company_name || '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Страна:</span>
                      <span className="text-white">{formData.country === 'BY' ? '🇧🇾 Беларусь' : '🇨🇳 Китай'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Услуги:</span>
                      <span className="text-white">{formData.services.length} выбрано</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Контакт:</span>
                      <span className="text-white">{formData.contact_person || '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Email (логин):</span>
                      <span className="text-white">{formData.email || '—'}</span>
                    </div>
                  </div>
                  
                  {/* Prices Summary */}
                  {formData.services.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-[#27272A]">
                      <h4 className="text-slate-400 text-xs uppercase mb-2">Стоимость услуг</h4>
                      {formData.services.map(service => {
                        const names = {
                          inspection: 'Инспекция',
                          purchase: 'Выкуп',
                          export: 'Экспорт',
                          logistics: 'Логистика',
                          leasing: 'Лизинг',
                          customs: 'Растаможка'
                        };
                        return (
                          <div key={service} className="flex justify-between text-sm">
                            <span className="text-slate-500">{names[service] || service}:</span>
                            <span className="text-[#00E5FF]">${formData.service_prices[service] || 0} USD</span>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                {/* Documents Upload */}
                <div className="mt-6 p-4 bg-[#0B0F14] rounded-sm border border-[#27272A]">
                  <h4 className="text-white font-medium mb-3 flex items-center gap-2">
                    <FileText size={16} className="text-[#00E5FF]" />
                    Документы (сертификаты, лицензии, портфолио)
                  </h4>
                  <p className="text-slate-500 text-xs mb-3">Загрузите документы подтверждающие квалификацию: лицензии, сертификаты, фото площадок, примеры работ</p>
                  <input
                    type="file"
                    multiple
                    accept="image/*,.pdf,.doc,.docx"
                    onChange={(e) => {
                      const newFiles = Array.from(e.target.files).map(f => ({
                        file: f,
                        category: f.type.startsWith('image') ? 'photo' : 'document',
                        title: f.name
                      }));
                      setApplicationFiles(prev => [...prev, ...newFiles]);
                      e.target.value = '';
                    }}
                    className="hidden"
                    id="app-file-input"
                  />
                  <label
                    htmlFor="app-file-input"
                    className="flex items-center justify-center gap-2 p-4 border-2 border-dashed border-[#27272A] rounded cursor-pointer hover:border-[#00E5FF]/50 transition-colors"
                  >
                    <Upload size={20} className="text-slate-400" />
                    <span className="text-slate-400 text-sm">Нажмите для выбора файлов</span>
                  </label>
                  {applicationFiles.length > 0 && (
                    <div className="mt-3 space-y-2">
                      {applicationFiles.map((f, i) => (
                        <div key={i} className="flex items-center justify-between bg-[#15191E] p-2 rounded">
                          <div className="flex items-center gap-2">
                            {f.file.type.startsWith('image') ? (
                              <img src={URL.createObjectURL(f.file)} alt="" className="w-10 h-10 object-cover rounded" />
                            ) : (
                              <FileText size={16} className="text-slate-400" />
                            )}
                            <div>
                              <p className="text-slate-300 text-sm">{f.file.name}</p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <select
                                  value={f.category}
                                  onChange={(e) => {
                                    const updated = [...applicationFiles];
                                    updated[i] = {...updated[i], category: e.target.value};
                                    setApplicationFiles(updated);
                                  }}
                                  className="bg-[#0B0F14] border border-[#27272A] rounded text-[10px] text-slate-400 px-1 py-0.5"
                                >
                                  <option value="document">Документ</option>
                                  <option value="certificate">Сертификат</option>
                                  <option value="license">Лицензия</option>
                                  <option value="photo">Фото</option>
                                  <option value="portfolio">Портфолио</option>
                                </select>
                                <span className="text-slate-600 text-[10px]">{(f.file.size / 1024).toFixed(0)} KB</span>
                              </div>
                            </div>
                          </div>
                          <button onClick={() => setApplicationFiles(prev => prev.filter((_,idx) => idx !== i))} className="text-red-400 hover:text-red-300 p-1">
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <p className="text-slate-500 text-sm">
                  Нажимая "Отправить заявку", вы соглашаетесь с условиями платформы. 
                  После проверки модератор свяжется с вами для уточнения деталей.
                </p>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t border-[#27272A]">
            {step > 1 ? (
              <Button
                variant="outline"
                onClick={prevStep}
                className="border-[#27272A] text-slate-300"
              >
                Назад
              </Button>
            ) : (
              <div />
            )}
            
            {step < 5 ? (
              <Button
                onClick={nextStep}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                Далее
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitting || uploadingFiles}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                {submitting || uploadingFiles ? (
                  <>
                    <Loader2 size={18} className="mr-2 animate-spin" />
                    {uploadingFiles ? 'Загрузка файлов...' : 'Отправка...'}
                  </>
                ) : (
                  <>
                    <Send size={18} className="mr-2" />
                    Отправить заявку
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ContractorRegisterPage;
