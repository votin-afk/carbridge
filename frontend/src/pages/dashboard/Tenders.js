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
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Tenders = () => {
  const { token } = useAuth();
  const [tenders, setTenders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedTender, setExpandedTender] = useState(null);

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
        {[...Array(5)].map((_, i) => (
          <Star 
            key={i} 
            size={14} 
            className={i < Math.floor(rating) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'}
          />
        ))}
        <span className="text-slate-400 text-sm ml-1">{rating}</span>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="tenders-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Тендеры</h1>
        <p className="text-slate-400 mt-1">
          Предложения от подрядчиков по вашим запросам
        </p>
      </div>

      {/* Tenders List */}
      {tenders.length > 0 ? (
        <div className="space-y-4">
          {tenders.map((tender) => (
            <div 
              key={tender.id}
              className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden"
            >
              {/* Tender Header */}
              <div 
                className="p-4 cursor-pointer hover:bg-[#1C2128] transition-colors"
                onClick={() => setExpandedTender(expandedTender === tender.id ? null : tender.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-[#1C2128] rounded-sm flex items-center justify-center">
                      <Car size={24} className="text-slate-500" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold">
                        {tender.car_info?.brand} {tender.car_info?.model}
                      </h3>
                      <p className="text-slate-400 text-sm">
                        {tender.car_info?.year} • ¥{tender.car_info?.price_cny?.toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-white font-semibold">
                        {tender.offers?.length || 0} предложений
                      </p>
                      {getStatusBadge(tender.status)}
                    </div>
                    {expandedTender === tender.id ? (
                      <ChevronUp className="text-slate-400" />
                    ) : (
                      <ChevronDown className="text-slate-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Offers */}
              {expandedTender === tender.id && tender.offers && (
                <div className="border-t border-[#27272A]">
                  {/* Best Offer */}
                  {tender.offers.length > 0 && (
                    <div className="p-4 bg-[#00E5FF]/5 border-b border-[#27272A]">
                      <div className="inline-flex items-center gap-2 px-2 py-1 bg-[#00E5FF]/20 rounded text-[#00E5FF] text-xs font-medium mb-3">
                        <CheckCircle2 size={12} />
                        Лучшее предложение
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 items-center">
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Цена (USD)</p>
                          <p className="text-white text-xl font-bold">
                            ${tender.offers[0].price_usd?.toLocaleString()}
                          </p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Рейтинг</p>
                          {renderStars(tender.offers[0].contractor_rating)}
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Срок</p>
                          <p className="text-white">{tender.offers[0].delivery_days} дней</p>
                        </div>
                        <div>
                          <p className="text-slate-400 text-xs mb-1">Доставка</p>
                          <p className="text-white">
                            {tender.offers[0].delivery_cost === 0 
                              ? 'Бесплатно' 
                              : `$${tender.offers[0].delivery_cost}`}
                          </p>
                        </div>
                        <div>
                          {tender.status === 'active' ? (
                            <Button
                              data-testid={`select-offer-${tender.offers[0].id}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSelectOffer(tender.id, tender.offers[0].id);
                              }}
                              className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black w-full"
                            >
                              Выбрать
                            </Button>
                          ) : tender.selected_offer_id === tender.offers[0].id ? (
                            <span className="text-emerald-400 text-sm flex items-center gap-1">
                              <CheckCircle2 size={16} /> Выбрано
                            </span>
                          ) : null}
                        </div>
                      </div>
                      <p className="text-slate-500 text-sm mt-2">
                        {tender.offers[0].contractor_name}
                      </p>
                    </div>
                  )}

                  {/* Other Offers */}
                  {tender.offers.slice(1).map((offer) => (
                    <div 
                      key={offer.id}
                      className="p-4 border-b border-[#27272A] last:border-b-0 hover:bg-[#1C2128]/50"
                    >
                      <div className="grid grid-cols-2 md:grid-cols-6 gap-4 items-center">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-8 bg-[#27272A] rounded flex items-center justify-center">
                            <Car size={16} className="text-slate-500" />
                          </div>
                          <p className="text-white font-semibold">
                            ${offer.price_usd?.toLocaleString()}
                          </p>
                        </div>
                        <div>{renderStars(offer.contractor_rating)}</div>
                        <div className="text-white text-sm">{offer.delivery_days} дней</div>
                        <div className="text-white text-sm">
                          {offer.delivery_cost === 0 ? 'Бесплатно' : `$${offer.delivery_cost}`}
                        </div>
                        <div className="text-slate-400 text-sm">{offer.payment_method}</div>
                        <div>
                          {tender.status === 'active' ? (
                            <Button
                              data-testid={`select-offer-${offer.id}`}
                              onClick={(e) => {
                                e.stopPropagation();
                                handleSelectOffer(tender.id, offer.id);
                              }}
                              variant="outline"
                              size="sm"
                              className="border-[#27272A] text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF]"
                            >
                              Выбрать
                            </Button>
                          ) : tender.selected_offer_id === offer.id ? (
                            <span className="text-emerald-400 text-sm flex items-center gap-1">
                              <CheckCircle2 size={14} /> Выбрано
                            </span>
                          ) : null}
                        </div>
                      </div>
                      <p className="text-slate-500 text-sm mt-2">
                        {offer.contractor_name}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <FileStack size={64} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-xl font-semibold text-white mb-2">Нет активных тендеров</h3>
          <p className="text-slate-400 mb-6 max-w-md mx-auto">
            Добавьте автомобиль в гараж и запустите тендер, чтобы получить предложения от подрядчиков
          </p>
        </div>
      )}
    </div>
  );
};

export default Tenders;
