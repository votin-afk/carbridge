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
  Send
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const serviceOptions = [
  { value: 'inspection', label: 'Инспекция авто', description: 'Техническая проверка автомобилей' },
  { value: 'purchase', label: 'Выкуп/Покупка', description: 'Выкуп автомобилей на аукционах' },
  { value: 'export', label: 'Экспорт', description: 'Таможенное оформление в КНР' },
  { value: 'logistics', label: 'Логистика', description: 'Доставка авто в Беларусь' },
  { value: 'leasing', label: 'Лизинг', description: 'Лизинговые услуги' },
  { value: 'customs', label: 'Растаможка в РБ', description: 'Таможенное оформление в Беларуси' }
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
  
  const [formData, setFormData] = useState({
    // Step 1 - Company Info
    company_name: '',
    country: 'CN', // BY or CN
    contractor_type: '',
    registration_number: '',
    legal_address: '',
    
    // Step 2 - Contact Info
    contact_person: '',
    position: '',
    phone: '',
    email: '',
    whatsapp: '',
    wechat: '',
    telegram: '',
    website: '',
    
    // Step 3 - Services (multiple selection)
    services: [],
    description: '',
    experience_years: '',
    
    // Step 4 - Documents
    license_info: '',
    additional_info: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const selectType = (type) => {
    setFormData(prev => ({ ...prev, contractor_type: type }));
  };

  const nextStep = () => {
    if (step === 1 && (!formData.company_name || !formData.country)) {
      toast.error('Заполните название компании и выберите страну');
      return;
    }
    if (step === 2 && (!formData.contact_person || !formData.phone || !formData.email)) {
      toast.error('Заполните контактные данные');
      return;
    }
    if (step === 3 && (formData.services.length === 0 || !formData.description)) {
      toast.error('Выберите услуги и добавьте описание');
      return;
    }
    setStep(step + 1);
  };

  const prevStep = () => {
    setStep(step - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      await axios.post(`${API}/contractors/register`, {
        company_name: formData.company_name,
        country: formData.country,
        registration_number: formData.registration_number,
        legal_address: formData.legal_address,
        contact_person: formData.contact_person,
        position: formData.position,
        phone: formData.phone,
        email: formData.email,
        whatsapp: formData.whatsapp,
        wechat: formData.wechat,
        telegram: formData.telegram,
        website: formData.website,
        services: formData.services,
        description: formData.description,
        experience_years: formData.experience_years ? parseInt(formData.experience_years) : null
      });
      
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
          {[1, 2, 3, 4].map((s) => (
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
              {s < 4 && (
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
                  <Label className="text-slate-300">Перечень услуг *</Label>
                  <textarea
                    name="services"
                    value={formData.services}
                    onChange={handleChange}
                    placeholder="Опишите услуги, которые вы предоставляете..."
                    className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 min-h-[80px]"
                  />
                </div>

                <div>
                  <Label className="text-slate-300">Ценовой диапазон</Label>
                  <Input
                    name="price_range"
                    value={formData.price_range}
                    onChange={handleChange}
                    placeholder="$100 - $500"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
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
                  <div>
                    <Label className="text-slate-300">Завершенных сделок</Label>
                    <Input
                      name="deals_completed"
                      type="number"
                      min="0"
                      value={formData.deals_completed}
                      onChange={handleChange}
                      placeholder="100"
                      className="mt-1 bg-[#0B0F14] border-[#27272A]"
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 4 - Final */}
          {step === 4 && (
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
                      <span className="text-slate-500">Тип:</span>
                      <span className="text-white">{contractorTypes[formData.contractor_type]?.label || '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Контакт:</span>
                      <span className="text-white">{formData.contact_person || '—'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-500">Email:</span>
                      <span className="text-white">{formData.email || '—'}</span>
                    </div>
                  </div>
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
            
            {step < 4 ? (
              <Button
                onClick={nextStep}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                Далее
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={submitting}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                {submitting ? (
                  <>
                    <Loader2 size={18} className="mr-2 animate-spin" />
                    Отправка...
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
