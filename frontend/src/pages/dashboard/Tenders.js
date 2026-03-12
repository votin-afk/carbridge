import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { 
  FileStack, 
  Car, 
  Star,
  Clock,
  Truck,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ShoppingCart,
  Loader2,
  ExternalLink,
  Image,
  Video,
  Search,
  Package,
  Ship,
  Shield,
  DollarSign,
  User
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Service labels for display
const serviceLabels = {
  inspection: { label: 'Инспекция', icon: Search, color: 'text-blue-400' },
  export: { label: 'Выкуп/экспорт', icon: Package, color: 'text-amber-400' },
  logistics_china: { label: 'До порта', icon: Truck, color: 'text-emerald-400' },
  delivery_rb: { label: 'В Беларусь', icon: Ship, color: 'text-indigo-400' },
  insurance: { label: 'Страхование', icon: Shield, color: 'text-cyan-400' }
};

const Tenders = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedTender, setExpandedTender] = useState(null);
  const [addingToDeal, setAddingToDeal] = useState(null);
  const [selectedOffer, setSelectedOffer] = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchTenders = async () => {
    try {
      const response = await axios.get(`${API}/tenders`, { headers });
      setTenders(response.data);
    } catch (error) {
      console.error('Error fetching tenders:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTenders();
  }, []);

  const handleSelectOffer = async (tenderId, offerId) => {
    try {
      await axios.post(`${API}/tenders/${tenderId}/select/${offerId}`, {}, { headers });
      toast.success('Предложение выбрано!');
      fetchTenders();
    } catch (error) {
      toast.error('Ошибка при выборе предложения');
    }
  };

  const handleAddToDeal = async (tender) => {
    if (!tender.car_id) {
      toast.error('Автомобиль не найден');
      return;
    }
    
    setAddingToDeal(tender.id);
    try {
      await axios.post(`${API}/deals/add-car`, {
        car_id: tender.car_id,
        from_tender: true,
        tender_id: tender.id,
        tender_offer_id: tender.selected_offer_id
      }, { headers });
      
      toast.success('Авто добавлено в сделку!');
      navigate('/dashboard/deals');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при создании сделки');
    } finally {
      setAddingToDeal(null);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      selected: 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/20',
      completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
    };
    const labels = {
      active: 'Активен',
      selected: 'Выбран подрядчик',
      completed: 'Завершен'
    };
    return (
      <span className={`px-3 py-1 rounded-full text-xs border ${styles[status] || styles.active}`}>
        {labels[status] || status}
      </span>
    );
  };

  const renderStars = (rating) => {
    return (
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            size={14}
            className={star <= rating ? 'text-amber-400 fill-amber-400' : 'text-slate-600'}
          />
        ))}
        <span className="text-slate-400 text-sm ml-1">{rating?.toFixed(1)}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="tenders-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <FileStack className="text-[#00E5FF]" />
            Мои тендеры
          </h1>
          <p className="text-slate-400 mt-1">Предложения от подрядчиков на ваши автомобили</p>
        </div>
      </div>

      {/* Tenders */}
      {tenders.length > 0 ? (
        <div className="space-y-6">
          {tenders.map((tender) => (
            <div
              key={tender.id}
              className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden"
              data-testid={`tender-${tender.id}`}
            >
              {/* Tender Header */}
              <div 
                className="p-4 cursor-pointer hover:bg-[#1C2128] transition-colors"
                onClick={() => setExpandedTender(expandedTender === tender.id ? null : tender.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-[#0B0F14] rounded-sm overflow-hidden flex-shrink-0">
                      <img 
                        src={tender.car_info?.image_url || 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=200'} 
                        alt={tender.car_info?.brand || tender.car_request?.brand}
                        className="w-full h-full object-cover"
                        onError={(e) => { e.target.src = 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=200'; }}
                      />
                    </div>
                    <div>
                      <h3 className="text-white font-medium">
                        {(tender.car_info?.brand || tender.car_request?.brand || 'Любая марка').toUpperCase()} {tender.car_info?.model || tender.car_request?.model || ''}
                      </h3>
                      <p className="text-slate-400 text-sm">
                        {tender.car_info?.year 
                          ? `${tender.car_info.year} • ¥${tender.car_info?.price_cny?.toLocaleString() || '—'}`
                          : tender.car_request?.year_from 
                            ? `${tender.car_request.year_from}${tender.car_request.year_to ? '-' + tender.car_request.year_to : ''} год`
                            : 'Заявка на подбор'
                        }
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right hidden sm:block">
                      <p className="text-slate-400 text-xs">Предложений</p>
                      <p className="text-[#00E5FF] text-lg font-bold">{tender.offers?.length || 0}</p>
                    </div>
                    {getStatusBadge(tender.status)}
                    {expandedTender === tender.id ? (
                      <ChevronUp className="text-slate-400" />
                    ) : (
                      <ChevronDown className="text-slate-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Offers */}
              {expandedTender === tender.id && (
                <div className="border-t border-[#27272A]">
                  {tender.offers && tender.offers.length > 0 ? (
                    <div className="p-4 space-y-4">
                      <p className="text-slate-400 text-sm">Предложения от подрядчиков:</p>
                      
                      {/* Offer Cards */}
                      <div className="grid gap-4 md:grid-cols-2">
                        {tender.offers.map((offer, index) => (
                          <OfferCard
                            key={offer.id}
                            offer={offer}
                            isFirst={index === 0}
                            isSelected={tender.selected_offer_id === offer.id}
                            tenderStatus={tender.status}
                            onSelect={() => handleSelectOffer(tender.id, offer.id)}
                            onAddToDeal={() => handleAddToDeal(tender)}
                            addingToDeal={addingToDeal === tender.id}
                            dealCreated={tender.deal_created}
                          />
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="p-8 text-center">
                      <Clock size={32} className="mx-auto mb-2 text-slate-600" />
                      <p className="text-slate-400">Пока нет предложений</p>
                      <p className="text-slate-500 text-sm">Подрядчики скоро откликнутся на ваш тендер</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <FileStack size={48} className="mx-auto mb-4 text-slate-600" />
          <p className="text-white font-medium mb-2">Нет активных тендеров</p>
          <p className="text-slate-400 text-sm mb-4">Создайте тендер, добавив автомобиль из гаража</p>
          <Button 
            onClick={() => navigate('/dashboard/garage')}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            Перейти в гараж
          </Button>
        </div>
      )}
    </div>
  );
};

// Offer Card Component
const OfferCard = ({ offer, isFirst, isSelected, tenderStatus, onSelect, onAddToDeal, addingToDeal, dealCreated }) => {
  const [showDetails, setShowDetails] = useState(false);
  
  return (
    <div className={`bg-[#0B0F14] border rounded-sm overflow-hidden ${
      isFirst ? 'border-[#00E5FF]/50' : 'border-[#27272A]'
    } ${isSelected ? 'ring-2 ring-emerald-500/50' : ''}`}>
      
      {/* Badge */}
      {isFirst && !isSelected && (
        <div className="bg-[#00E5FF]/10 px-3 py-1.5 border-b border-[#00E5FF]/20">
          <span className="text-[#00E5FF] text-xs font-medium flex items-center gap-1">
            <CheckCircle2 size={12} /> Лучшее предложение
          </span>
        </div>
      )}
      {isSelected && (
        <div className="bg-emerald-500/10 px-3 py-1.5 border-b border-emerald-500/20">
          <span className="text-emerald-400 text-xs font-medium flex items-center gap-1">
            <CheckCircle2 size={12} /> Выбранное предложение
          </span>
        </div>
      )}

      <div className="p-4">
        {/* Contractor & Price */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#15191E] rounded-full flex items-center justify-center">
              <User size={14} className="text-slate-400" />
            </div>
            <div>
              <p className="text-white text-sm font-medium">{offer.contractor_name || 'Подрядчик'}</p>
              <div className="flex items-center gap-1">
                {[1,2,3,4,5].map(s => (
                  <Star key={s} size={10} className={s <= (offer.contractor_rating || 5) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'} />
                ))}
              </div>
            </div>
          </div>
          <div className="text-right">
            <p className="text-[#00E5FF] text-xl font-bold">${offer.price_usd?.toLocaleString()}</p>
            {offer.price_cny && (
              <p className="text-slate-500 text-xs">¥{offer.price_cny.toLocaleString()}</p>
            )}
          </div>
        </div>

        {/* Car Info from Offer */}
        {offer.car_details && (
          <div className="bg-[#15191E] rounded p-2 mb-3">
            <p className="text-slate-300 text-sm">{offer.car_details}</p>
          </div>
        )}

        {/* Car Link */}
        {offer.car_link && (
          <a 
            href={offer.car_link} 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-[#00E5FF] text-sm hover:underline mb-3"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink size={14} />
            Ссылка на авто
          </a>
        )}

        {/* Photos/Videos indicators */}
        <div className="flex items-center gap-3 mb-3">
          {offer.car_photos?.length > 0 && (
            <span className="flex items-center gap-1 text-slate-400 text-xs">
              <Image size={12} /> {offer.car_photos.length} фото
            </span>
          )}
          {offer.car_videos?.length > 0 && (
            <span className="flex items-center gap-1 text-slate-400 text-xs">
              <Video size={12} /> {offer.car_videos.length} видео
            </span>
          )}
        </div>

        {/* Included Services */}
        {offer.included_services && Object.values(offer.included_services).some(v => v) && (
          <div className="mb-3">
            <p className="text-slate-500 text-xs mb-2">Этапы в цене:</p>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(offer.included_services).map(([key, included]) => {
                if (!included) return null;
                const service = serviceLabels[key];
                if (!service) return null;
                const ServiceIcon = service.icon;
                const price = offer.service_prices?.[key];
                return (
                  <div 
                    key={key} 
                    className="flex items-center gap-1 px-2 py-1 bg-[#15191E] rounded text-xs"
                    title={price ? `$${price}` : ''}
                  >
                    <ServiceIcon size={10} className={service.color} />
                    <span className="text-slate-300">{service.label}</span>
                    {price && <span className="text-slate-500">${price}</span>}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Delivery Info */}
        <div className="flex items-center gap-4 text-sm mb-3">
          {offer.delivery_days && (
            <div className="flex items-center gap-1 text-slate-400">
              <Clock size={12} />
              <span>{offer.delivery_days} дней</span>
            </div>
          )}
          {offer.delivery_cost !== undefined && (
            <div className="flex items-center gap-1 text-slate-400">
              <Truck size={12} />
              <span>{offer.delivery_cost === 0 ? 'Бесплатно' : `$${offer.delivery_cost}`}</span>
            </div>
          )}
        </div>

        {/* Notes */}
        {offer.notes && (
          <p className="text-slate-500 text-xs mb-3 italic">"{offer.notes}"</p>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          {tenderStatus === 'active' && (
            <Button
              onClick={(e) => { e.stopPropagation(); onSelect(); }}
              className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              size="sm"
            >
              Выбрать
            </Button>
          )}
          {isSelected && !dealCreated && (
            <Button
              onClick={(e) => { e.stopPropagation(); onAddToDeal(); }}
              disabled={addingToDeal}
              className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
              size="sm"
            >
              {addingToDeal ? <Loader2 size={14} className="mr-1 animate-spin" /> : <ShoppingCart size={14} className="mr-1" />}
              В сделку
            </Button>
          )}
          {isSelected && dealCreated && (
            <span className="flex-1 text-center text-emerald-400 text-sm py-2">
              ✓ Сделка создана
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default Tenders;
