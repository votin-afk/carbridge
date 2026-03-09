import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { 
  Scale, 
  MapPin, 
  Phone, 
  Mail, 
  Clock, 
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileText,
  Globe,
  Building2,
  Users
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const LegalHelp = () => {
  const { token, user } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      const response = await axios.get(`${API}/api/legal-help/requests`, { headers });
      setRequests(response.data);
    } catch (error) {
      console.error('Error fetching legal requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const requestHelp = async (country) => {
    setSubmitting(country);
    try {
      await axios.post(`${API}/api/legal-help/request`, { country }, { headers });
      toast.success(`Запрос на юридическую помощь в ${country === 'belarus' ? 'Беларуси' : 'Китае'} отправлен`);
      fetchRequests();
    } catch (error) {
      toast.error('Ошибка при отправке запроса');
    } finally {
      setSubmitting(null);
    }
  };

  const services = [
    {
      country: 'belarus',
      title: 'Юридическая помощь в Беларуси',
      flag: '🇧🇾',
      description: 'Сопровождение сделки, растаможка, регистрация авто',
      services: [
        'Консультация по таможенному законодательству',
        'Помощь в оформлении документов',
        'Сопровождение растаможки',
        'Регистрация авто в ГАИ',
        'Разрешение споров с продавцами',
        'Проверка юридической чистоты авто'
      ],
      contacts: {
        phone: '+375 17 336-00-00',
        email: 'legal@carbridge.by',
        address: 'г. Минск, ул. Немига, 3, оф. 501'
      }
    },
    {
      country: 'china',
      title: 'Юридическая помощь в Китае',
      flag: '🇨🇳',
      description: 'Проверка продавца, контракты, экспортные документы',
      services: [
        'Проверка китайских продавцов',
        'Составление и проверка контрактов',
        'Сопровождение сделки в Китае',
        'Оформление экспортных документов',
        'Разрешение споров с китайскими компаниями',
        'Услуги переводчика'
      ],
      contacts: {
        phone: '+86 21 5888-8888',
        email: 'china-legal@carbridge.com',
        address: 'Shanghai, Pudong District'
      }
    }
  ];

  const statusLabels = {
    pending: { label: 'Ожидает обработки', color: 'text-amber-400', icon: Clock },
    in_progress: { label: 'В работе', color: 'text-blue-400', icon: Users },
    completed: { label: 'Завершено', color: 'text-emerald-400', icon: CheckCircle2 }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Scale className="text-[#00E5FF]" />
          Юридическая помощь
        </h1>
        <p className="text-slate-400 mt-1">Профессиональное юридическое сопровождение в Беларуси и Китае</p>
      </div>

      {/* Services Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {services.map(service => (
          <div key={service.country} className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-[#27272A] bg-gradient-to-r from-[#0B0F14] to-transparent">
              <div className="flex items-center gap-4">
                <span className="text-4xl">{service.flag}</span>
                <div>
                  <h2 className="text-xl font-bold text-white">{service.title}</h2>
                  <p className="text-slate-400 text-sm">{service.description}</p>
                </div>
              </div>
            </div>

            {/* Services List */}
            <div className="p-6">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                <FileText size={16} className="text-[#00E5FF]" />
                Услуги
              </h3>
              <ul className="space-y-2">
                {service.services.map((item, index) => (
                  <li key={index} className="flex items-start gap-2 text-slate-300 text-sm">
                    <CheckCircle2 size={14} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                    {item}
                  </li>
                ))}
              </ul>

              {/* Contacts */}
              <div className="mt-6 pt-4 border-t border-[#27272A]">
                <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                  <Building2 size={16} className="text-[#00E5FF]" />
                  Контакты
                </h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-slate-400">
                    <Phone size={14} />
                    <span>{service.contacts.phone}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400">
                    <Mail size={14} />
                    <span>{service.contacts.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400">
                    <MapPin size={14} />
                    <span>{service.contacts.address}</span>
                  </div>
                </div>
              </div>

              {/* Request Button */}
              <Button
                onClick={() => requestHelp(service.country)}
                disabled={submitting === service.country}
                className="w-full mt-6 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                {submitting === service.country ? (
                  <>
                    <Loader2 size={16} className="mr-2 animate-spin" />
                    Отправка...
                  </>
                ) : (
                  <>
                    <Scale size={16} className="mr-2" />
                    Запросить помощь
                  </>
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* My Requests */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
        <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Clock className="text-[#00E5FF]" />
          Мои запросы
        </h2>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={24} className="text-[#00E5FF] animate-spin" />
          </div>
        ) : requests.length > 0 ? (
          <div className="space-y-3">
            {requests.map(request => {
              const status = statusLabels[request.status] || statusLabels.pending;
              const StatusIcon = status.icon;
              
              return (
                <div key={request.id} className="flex items-center justify-between p-4 bg-[#0B0F14] rounded-lg border border-[#27272A]">
                  <div className="flex items-center gap-4">
                    <span className="text-2xl">{request.country === 'belarus' ? '🇧🇾' : '🇨🇳'}</span>
                    <div>
                      <p className="text-white font-medium">
                        Юридическая помощь в {request.country_name}
                      </p>
                      <p className="text-slate-400 text-sm">
                        {new Date(request.created_at).toLocaleDateString('ru-RU', {
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric'
                        })}
                      </p>
                    </div>
                  </div>
                  <div className={`flex items-center gap-2 ${status.color}`}>
                    <StatusIcon size={16} />
                    <span className="text-sm">{status.label}</span>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="text-center py-8">
            <Scale size={48} className="mx-auto mb-4 text-slate-600" />
            <p className="text-slate-400">У вас пока нет запросов на юридическую помощь</p>
          </div>
        )}
      </div>

      {/* Info Block */}
      <div className="bg-[#15191E] border border-amber-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertCircle size={20} className="text-amber-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="text-amber-400 font-medium">Важная информация</h4>
            <p className="text-slate-400 text-sm mt-1">
              После отправки запроса наш специалист свяжется с вами в течение 24 часов для уточнения деталей. 
              Стоимость услуг зависит от сложности вопроса и обсуждается индивидуально.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LegalHelp;
