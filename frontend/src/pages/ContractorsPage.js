import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from '../hooks/useTranslation';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Search as SearchIcon,
  CheckCircle2,
  Star,
  Phone,
  Mail,
  Globe,
  Trash2,
  Loader2,
  Building2,
  Truck,
  ClipboardCheck,
  Package,
  ExternalLink,
  ArrowLeft,
  UserPlus,
  CreditCard
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Service stages matching deal flow
const stageConfig = [
  { key: 'leasing', icon: CreditCard, color: 'text-purple-400', bgColor: 'bg-purple-500/10', borderColor: 'border-purple-500/30' },
  { key: 'inspection', icon: ClipboardCheck, color: 'text-blue-400', bgColor: 'bg-blue-500/10', borderColor: 'border-blue-500/30' },
  { key: 'export', icon: Package, color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/30' },
  { key: 'logistics_china', icon: Truck, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', borderColor: 'border-emerald-500/30' },
  { key: 'insurance', icon: ClipboardCheck, color: 'text-cyan-400', bgColor: 'bg-cyan-500/10', borderColor: 'border-cyan-500/30' },
  { key: 'delivery_rb', icon: Truck, color: 'text-indigo-400', bgColor: 'bg-indigo-500/10', borderColor: 'border-indigo-500/30' },
  { key: 'customs', icon: Building2, color: 'text-rose-400', bgColor: 'bg-rose-500/10', borderColor: 'border-rose-500/30' },
  { key: 'legal_belarus', icon: Building2, color: 'text-amber-400', bgColor: 'bg-amber-500/10', borderColor: 'border-amber-500/30' },
  { key: 'legal_china', icon: Building2, color: 'text-red-400', bgColor: 'bg-red-500/10', borderColor: 'border-red-500/30' },
];

const stageLabels = {
  ru: {
    leasing: { label: 'Лизинг', description: 'Лизинговые компании' },
    inspection: { label: 'Инспекция авто', description: 'Проверка технического состояния' },
    export: { label: 'Выкуп и экспорт', description: 'Выкуп и экспорт из Китая' },
    logistics_china: { label: 'Доставка до порта (Китай)', description: 'Логистика до порта отправления' },
    insurance: { label: 'Страхование авто', description: 'Страхование груза' },
    delivery_rb: { label: 'Доставка в Беларусь', description: 'Морская/ж/д доставка' },
    customs: { label: 'Таможенное оформление', description: 'Растаможка в Беларуси' },
    legal_belarus: { label: 'Юристы (Беларусь)', description: 'Юридическая помощь в Беларуси' },
    legal_china: { label: 'Юристы (Китай)', description: 'Юридическая помощь в Китае' },
  },
  en: {
    leasing: { label: 'Leasing', description: 'Leasing companies' },
    inspection: { label: 'Car Inspection', description: 'Technical condition check' },
    export: { label: 'Purchase & Export', description: 'Purchase and export from China' },
    logistics_china: { label: 'Port Delivery (China)', description: 'Logistics to departure port' },
    insurance: { label: 'Car Insurance', description: 'Cargo insurance' },
    delivery_rb: { label: 'Delivery to Belarus', description: 'Sea/rail delivery' },
    customs: { label: 'Customs Clearance', description: 'Customs in Belarus' },
    legal_belarus: { label: 'Lawyers (Belarus)', description: 'Legal help in Belarus' },
    legal_china: { label: 'Lawyers (China)', description: 'Legal help in China' },
  },
};

const getServiceStages = (lang) => stageConfig.map(s => ({
  ...s,
  label: stageLabels[lang]?.[s.key]?.label || stageLabels.ru[s.key]?.label,
  description: stageLabels[lang]?.[s.key]?.description || stageLabels.ru[s.key]?.description,
}));

const getContractorTypes = (lang) => {
  const stages = getServiceStages(lang);
  return {
    inspection: stages.find(s => s.key === 'inspection'),
    export: stages.find(s => s.key === 'export'),
    logistics: stages.find(s => s.key === 'delivery_rb'),
    leasing: stages.find(s => s.key === 'leasing')
  };
};

// Messenger icons
const WhatsAppIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

const WeChatIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.007-.27-.018-.406-.032z"/>
  </svg>
);

const TelegramIcon = ({ className }) => (
  <svg viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
  </svg>
);

const ContractorsPage = () => {
  const { token } = useAuth();
  const { t, lang } = useTranslation();
  const serviceStages = getServiceStages(lang);
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('inspection');
  const [searchQuery, setSearchQuery] = useState('');

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  const fetchContractors = async (type) => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/contractors`, {
        params: { contractor_type: type }
      });
      setContractors(response.data);
    } catch (error) {
      console.error('Error fetching contractors:', error);
      toast.error(t('messages.loadError'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContractors(activeTab);
  }, [activeTab]);

  const handleDeleteContractor = async (contractorId) => {
    if (!window.confirm(t('messages.confirmDelete'))) return;
    
    try {
      await axios.delete(`${API}/contractors/${contractorId}`, { headers });
      toast.success(t('messages.contractorDeleted'));
      fetchContractors(activeTab);
    } catch (error) {
      if (error.response?.data?.detail?.includes('demo')) {
        toast.error(t('messages.demoCannotDelete'));
      } else {
        toast.error(t('messages.deleteError'));
      }
    }
  };

  const filteredContractors = contractors.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const TypeIcon = stageConfig.find(s => s.key === activeTab)?.icon || Building2;

  return (
    <div className="min-h-screen bg-[#0B0F14] py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <div className="mb-6">
          <Link to="/">
            <Button variant="ghost" className="text-slate-400 hover:text-white">
              <ArrowLeft size={18} className="mr-2" />
              {t('nav.backToMain')}
            </Button>
          </Link>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <p className="text-[#00E5FF] text-sm font-medium uppercase tracking-wider mb-3">{t('contractors.partnersLabel')}</p>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">{t('contractors.title')}</h1>
          <p className="text-slate-400 max-w-2xl mx-auto mb-6">
            {t('contractors.subtitle')}
          </p>
          <div className="flex flex-col sm:flex-row justify-center gap-3">
            <Link to="/contractor-register">
              <Button className="bg-gradient-to-r from-[#00E5FF] to-[#22D3EE] text-black">
                <UserPlus size={18} className="mr-2" />
                {t('contractors.becomeContractor')}
              </Button>
            </Link>
            <Link to="/contractor-dashboard">
              <Button variant="outline" className="border-[#00E5FF] text-[#00E5FF] hover:bg-[#00E5FF]/10">
                <Building2 size={18} className="mr-2" />
                {t('contractors.contractorLogin')}
              </Button>
            </Link>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
          <div className="flex flex-col gap-4">
            <TabsList className="bg-[#15191E] p-1 rounded-sm flex flex-wrap gap-1 h-auto">
              {serviceStages.map(stage => (
                <TabsTrigger 
                  key={stage.key}
                  value={stage.key}
                  className={`data-[state=active]:${stage.bgColor} data-[state=active]:text-white rounded-sm flex items-center gap-2 px-3 py-2 text-sm`}
                >
                  <stage.icon size={14} />
                  <span className="hidden sm:inline">{stage.label}</span>
                  <span className="sm:hidden">{stage.label.split(' ')[0]}</span>
                </TabsTrigger>
              ))}
            </TabsList>

            <div className="flex gap-3">
              <div className="relative flex-1 max-w-md">
                <SearchIcon size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <Input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('contractors.searchPlaceholder')}
                  className="pl-9 bg-[#15191E] border-[#27272A] text-white"
                  data-testid="contractors-search-input"
                />
              </div>
            </div>

            {/* Current stage description */}
            <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
              <p className="text-slate-400 text-sm">
                {serviceStages.find(s => s.key === activeTab)?.description || t('contractors.stageDefaultDesc')}
              </p>
            </div>
          </div>

          {/* Content */}
          {serviceStages.map(stage => (
            <TabsContent key={stage.key} value={stage.key} className="mt-0">
              {loading ? (
                <div className="flex items-center justify-center h-64">
                  <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
                </div>
              ) : filteredContractors.length > 0 ? (
                <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {filteredContractors.map((contractor) => (
                    <ContractorCard 
                      key={contractor.id} 
                      contractor={contractor}
                      onDelete={handleDeleteContractor}
                      isAuthenticated={!!token}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
                  <TypeIcon size={64} className="mx-auto mb-4 text-slate-600" />
                  <h3 className="text-xl font-semibold text-white mb-2">{t('contractors.noContractorsFound')}</h3>
                  <p className="text-slate-400">
                    {searchQuery ? t('contractors.tryChangingSearch') : t('contractors.noCategoryContractors')}
                  </p>
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>
      </div>
    </div>
  );
};

const ContractorCard = ({ contractor, onDelete, isAuthenticated }) => {
  const { t, lang } = useTranslation();
  const contractorTypes = getContractorTypes(lang);
  const typeConfig = contractorTypes[contractor.contractor_type] || contractorTypes.inspection;
  const TypeIcon = typeConfig?.icon || Building2;

  return (
    <div className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden card-hover">
      {/* Header */}
      <div className={`p-4 ${typeConfig.bgColor} border-b ${typeConfig.borderColor}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${typeConfig.bgColor} flex items-center justify-center`}>
              <TypeIcon size={20} className={typeConfig.color} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-white font-semibold">{contractor.name}</h3>
                {contractor.is_verified && (
                  <CheckCircle2 size={16} className="text-[#00E5FF]" />
                )}
              </div>
              <span className={`text-xs ${typeConfig.color}`}>{typeConfig.label}</span>
            </div>
          </div>
          {isAuthenticated && !contractor.id.startsWith('insp-') && !contractor.id.startsWith('exp-') && !contractor.id.startsWith('log-') && !contractor.id.startsWith('leas-') && (
            <button
              onClick={() => onDelete(contractor.id)}
              className="text-slate-500 hover:text-red-400 p-1"
              data-testid={`delete-contractor-${contractor.id}`}
            >
              <Trash2 size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {/* Rating & Deals */}
        <div className="flex items-center gap-4 mb-3">
          <div className="flex items-center gap-1">
            <Star size={14} className="text-amber-400 fill-amber-400" />
            <span className="text-white font-medium">{contractor.rating.toFixed(1)}</span>
          </div>
          <span className="text-slate-500">&bull;</span>
          <span className="text-slate-400 text-sm">{contractor.deals_count} {t('contractors.deals')}</span>
        </div>

        {/* Description */}
        <p className="text-slate-400 text-sm mb-3 line-clamp-2">{contractor.description}</p>

        {/* Services */}
        <div className="mb-3">
          <p className="text-slate-500 text-xs mb-1">{t('contractors.services')}:</p>
          <p className="text-slate-300 text-sm line-clamp-2">
            {(() => {
              const sLabels = stageLabels[lang] || stageLabels.ru;
              const servicesArray = typeof contractor.services === 'string' 
                ? contractor.services.split(',').map(s => s.trim())
                : (contractor.services || []);
              return servicesArray.map(s => sLabels[s]?.label || s).join(', ');
            })()}
          </p>
        </div>

        {/* Service Prices */}
        {contractor.service_prices && Object.keys(contractor.service_prices).length > 0 && (
          <div className="mb-3 p-2 bg-[#0B0F14] rounded-sm">
            <p className="text-slate-500 text-xs mb-2">{t('contractors.servicePrices')}:</p>
            <div className="space-y-1">
              {Object.entries(contractor.service_prices).map(([service, price]) => {
                const serviceName = t(`contractors.serviceLabels.${service}`);
                const displayName = serviceName !== `contractors.serviceLabels.${service}` ? serviceName : service;
                
                let priceDisplay;
                if (service === 'leasing' && typeof price === 'object' && price !== null) {
                  priceDisplay = `${price.rate}% (${price.currency || 'USD'})`;
                } else if (typeof price === 'number') {
                  priceDisplay = `$${price}`;
                } else {
                  priceDisplay = String(price);
                }
                
                return (
                  <div key={service} className="flex justify-between items-center text-sm">
                    <span className="text-slate-400">{displayName}</span>
                    <span className="text-[#00E5FF] font-medium">{priceDisplay}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Price Range (fallback) */}
        {!contractor.service_prices && contractor.price_range && (
          <div className="mb-4 p-2 bg-[#0B0F14] rounded-sm">
            <span className="text-slate-500 text-xs">{t('contractors.cost')}: </span>
            <span className="text-[#00E5FF] font-medium">{contractor.price_range}</span>
          </div>
        )}

        {/* Contacts */}
        <div className="space-y-2 pt-3 border-t border-[#27272A]">
          {contractor.phone && (
            <a href={`tel:${contractor.phone}`} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm">
              <Phone size={14} />
              {contractor.phone}
            </a>
          )}
          {contractor.email && (
            <a href={`mailto:${contractor.email}`} className="flex items-center gap-2 text-slate-400 hover:text-white text-sm">
              <Mail size={14} />
              {contractor.email}
            </a>
          )}
          {contractor.website && (
            <a href={contractor.website} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-slate-400 hover:text-[#00E5FF] text-sm">
              <Globe size={14} />
              {t('contractors.websiteLink')}
              <ExternalLink size={12} />
            </a>
          )}
        </div>

        {/* Messengers */}
        <div className="flex gap-2 mt-3 pt-3 border-t border-[#27272A]">
          {contractor.whatsapp && (
            <a
              href={`https://wa.me/${contractor.whatsapp.replace(/\D/g, '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-8 h-8 bg-[#25D366]/10 rounded-full flex items-center justify-center text-[#25D366] hover:bg-[#25D366] hover:text-white transition-colors"
            >
              <WhatsAppIcon className="w-4 h-4" />
            </a>
          )}
          {contractor.wechat && (
            <div
              onClick={() => {
                navigator.clipboard.writeText(contractor.wechat);
                toast.success(`${t('messages.wechatCopied')}: ${contractor.wechat}`);
              }}
              className="w-8 h-8 bg-[#07C160]/10 rounded-full flex items-center justify-center text-[#07C160] hover:bg-[#07C160] hover:text-white transition-colors cursor-pointer"
            >
              <WeChatIcon className="w-4 h-4" />
            </div>
          )}
          {contractor.telegram && (
            <a
              href={`https://t.me/${contractor.telegram.replace('@', '')}`}
              target="_blank"
              rel="noopener noreferrer"
              className="w-8 h-8 bg-[#0088CC]/10 rounded-full flex items-center justify-center text-[#0088CC] hover:bg-[#0088CC] hover:text-white transition-colors"
            >
              <TelegramIcon className="w-4 h-4" />
            </a>
          )}
          <Link 
            to={`/contractor/${contractor.id}`}
            className="ml-auto flex items-center gap-1.5 px-3 py-1.5 bg-[#00E5FF]/10 text-[#00E5FF] text-sm rounded hover:bg-[#00E5FF]/20 transition-colors"
            data-testid={`contractor-profile-link-${contractor.id}`}
          >
            {t('nav.more')} <ExternalLink size={12} />
          </Link>
        </div>
      </div>
    </div>
  );
};

export default ContractorsPage;
