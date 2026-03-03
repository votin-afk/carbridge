import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../components/ui/dialog";
import { 
  Flame,
  Clock,
  Car,
  Plus,
  ArrowLeft,
  Loader2,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Gauge,
  Fuel,
  DollarSign,
  User,
  ShoppingCart
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Countdown Timer Component
const CountdownTimer = ({ expiresAt, onExpire }) => {
  const [timeLeft, setTimeLeft] = useState({ days: 0, hours: 0, minutes: 0, seconds: 0 });
  const [isExpired, setIsExpired] = useState(false);

  useEffect(() => {
    const calculateTimeLeft = () => {
      const now = new Date();
      const expiry = new Date(expiresAt);
      const diff = expiry - now;

      if (diff <= 0) {
        setIsExpired(true);
        if (onExpire) onExpire();
        return { days: 0, hours: 0, minutes: 0, seconds: 0 };
      }

      return {
        days: Math.floor(diff / (1000 * 60 * 60 * 24)),
        hours: Math.floor((diff / (1000 * 60 * 60)) % 24),
        minutes: Math.floor((diff / 1000 / 60) % 60),
        seconds: Math.floor((diff / 1000) % 60)
      };
    };

    setTimeLeft(calculateTimeLeft());
    const timer = setInterval(() => {
      setTimeLeft(calculateTimeLeft());
    }, 1000);

    return () => clearInterval(timer);
  }, [expiresAt, onExpire]);

  if (isExpired) {
    return (
      <div className="flex items-center gap-1 text-red-400 text-sm">
        <AlertTriangle size={14} />
        <span>Истекло</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Clock size={14} className="text-amber-400" />
      <div className="flex gap-1 text-sm">
        {timeLeft.days > 0 && (
          <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
            {timeLeft.days}д
          </span>
        )}
        <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
          {String(timeLeft.hours).padStart(2, '0')}ч
        </span>
        <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
          {String(timeLeft.minutes).padStart(2, '0')}м
        </span>
        <span className="bg-amber-500/20 text-amber-400 px-1.5 py-0.5 rounded">
          {String(timeLeft.seconds).padStart(2, '0')}с
        </span>
      </div>
    </div>
  );
};

// Hot Deal Card Component
const HotDealCard = ({ deal, onAddToGarage, onExpire, isAdding }) => {
  const [showDetails, setShowDetails] = useState(false);

  const getEngineTypeLabel = (type) => {
    const labels = { ice: 'ДВС', hybrid: 'Гибрид', electric: 'Электро' };
    return labels[type] || type;
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ru-RU').format(num);
  };

  const hasDiscount = deal.special_price_cny && deal.special_price_cny < deal.price_cny;
  const discountPercent = hasDiscount 
    ? Math.round((1 - deal.special_price_cny / deal.price_cny) * 100)
    : 0;

  return (
    <>
      <div 
        onClick={() => setShowDetails(true)}
        className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden cursor-pointer hover:border-amber-500/50 transition-colors group"
      >
        {/* Image */}
        <div className="h-44 bg-[#1C2128] relative overflow-hidden">
          {deal.image_url ? (
            <img 
              src={deal.image_url} 
              alt={`${deal.brand} ${deal.model}`}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Car size={48} className="text-slate-600" />
            </div>
          )}
          
          {/* Hot badge */}
          <div className="absolute top-3 left-3 bg-gradient-to-r from-orange-500 to-red-500 text-white px-2 py-1 rounded-sm text-xs font-bold flex items-center gap-1">
            <Flame size={12} />
            ГОРЯЩЕЕ
          </div>

          {/* Discount badge */}
          {hasDiscount && (
            <div className="absolute top-3 right-3 bg-green-500 text-white px-2 py-1 rounded-sm text-xs font-bold">
              -{discountPercent}%
            </div>
          )}

          {/* Verified seller */}
          {deal.is_verified_seller && (
            <div className="absolute bottom-3 left-3 bg-[#00E5FF]/90 text-black px-2 py-1 rounded-sm text-xs font-medium flex items-center gap-1">
              <CheckCircle2 size={12} />
              {deal.seller_name}
            </div>
          )}
        </div>

        {/* Content */}
        <div className="p-4">
          <h3 className="text-white font-semibold text-lg mb-1">
            {deal.brand} {deal.model}
          </h3>
          
          <div className="flex flex-wrap gap-2 text-sm text-slate-400 mb-3">
            <span>{deal.year}</span>
            <span>•</span>
            <span>{getEngineTypeLabel(deal.engine_type)}</span>
            {deal.mileage && (
              <>
                <span>•</span>
                <span>{formatNumber(deal.mileage)} км</span>
              </>
            )}
          </div>

          {/* Price */}
          <div className="mb-3">
            {hasDiscount ? (
              <div className="flex items-baseline gap-2">
                <span className="text-slate-500 line-through text-sm">¥{formatNumber(deal.price_cny)}</span>
                <span className="text-amber-400 font-bold text-xl">¥{formatNumber(deal.special_price_cny)}</span>
              </div>
            ) : (
              <span className="text-amber-400 font-bold text-xl">¥{formatNumber(deal.price_cny)}</span>
            )}
            {deal.calculated_price_usd && (
              <p className="text-[#00E5FF] text-sm mt-1">
                ≈ ${formatNumber(Math.round(deal.calculated_price_usd))} под ключ
              </p>
            )}
          </div>

          {/* Timer */}
          <div className="pt-3 border-t border-[#27272A]">
            <CountdownTimer expiresAt={deal.expires_at} onExpire={() => onExpire(deal.id)} />
          </div>
        </div>
      </div>

      {/* Details Modal */}
      <Dialog open={showDetails} onOpenChange={setShowDetails}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Flame size={20} className="text-orange-500" />
              Горящее предложение
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            {/* Image */}
            {deal.image_url && (
              <div className="h-48 rounded-sm overflow-hidden">
                <img 
                  src={deal.image_url} 
                  alt={`${deal.brand} ${deal.model}`}
                  className="w-full h-full object-cover"
                />
              </div>
            )}

            {/* Car Info */}
            <div>
              <h3 className="text-white font-bold text-xl mb-2">
                {deal.brand} {deal.model}
              </h3>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="flex items-center gap-2 text-slate-400">
                  <Calendar size={14} />
                  <span>{deal.year} год</span>
                </div>
                <div className="flex items-center gap-2 text-slate-400">
                  <Fuel size={14} />
                  <span>{getEngineTypeLabel(deal.engine_type)}</span>
                </div>
                {deal.mileage && (
                  <div className="flex items-center gap-2 text-slate-400">
                    <Gauge size={14} />
                    <span>{formatNumber(deal.mileage)} км</span>
                  </div>
                )}
                {deal.engine_volume && (
                  <div className="flex items-center gap-2 text-slate-400">
                    <Car size={14} />
                    <span>{deal.engine_volume} см³</span>
                  </div>
                )}
              </div>
            </div>

            {/* Description */}
            {deal.description && (
              <div className="p-3 bg-[#0B0F14] rounded-sm">
                <p className="text-slate-300 text-sm">{deal.description}</p>
              </div>
            )}

            {/* Price */}
            <div className="p-4 bg-gradient-to-r from-amber-500/10 to-orange-500/10 rounded-sm border border-amber-500/30">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-400">Цена:</span>
                {hasDiscount ? (
                  <div className="text-right">
                    <span className="text-slate-500 line-through text-sm mr-2">¥{formatNumber(deal.price_cny)}</span>
                    <span className="text-amber-400 font-bold text-xl">¥{formatNumber(deal.special_price_cny)}</span>
                    <span className="ml-2 bg-green-500 text-white text-xs px-1.5 py-0.5 rounded">-{discountPercent}%</span>
                  </div>
                ) : (
                  <span className="text-amber-400 font-bold text-xl">¥{formatNumber(deal.price_cny)}</span>
                )}
              </div>
              {deal.calculated_price_usd && (
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Под ключ в РБ:</span>
                  <span className="text-[#00E5FF] font-bold">${formatNumber(Math.round(deal.calculated_price_usd))}</span>
                </div>
              )}
            </div>

            {/* Seller */}
            <div className="flex items-center justify-between p-3 bg-[#0B0F14] rounded-sm">
              <div className="flex items-center gap-2">
                <User size={16} className="text-slate-400" />
                <span className="text-slate-300">{deal.seller_name}</span>
                {deal.is_verified_seller && (
                  <CheckCircle2 size={14} className="text-[#00E5FF]" />
                )}
              </div>
              <span className="text-slate-500 text-xs">
                {deal.seller_type === 'contractor' ? 'Подрядчик' : 'Модератор'}
              </span>
            </div>

            {/* Timer */}
            <div className="flex items-center justify-between p-3 bg-red-500/10 border border-red-500/30 rounded-sm">
              <span className="text-slate-300 text-sm">Осталось времени:</span>
              <CountdownTimer expiresAt={deal.expires_at} onExpire={() => onExpire(deal.id)} />
            </div>

            {/* Add to Garage Button */}
            <Button
              data-testid={`add-hot-deal-${deal.id}`}
              onClick={() => {
                onAddToGarage(deal.id);
                setShowDetails(false);
              }}
              disabled={isAdding}
              className="w-full bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white"
            >
              {isAdding ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <ShoppingCart size={16} className="mr-2" />
              )}
              Добавить в гараж
            </Button>

            <p className="text-slate-500 text-xs text-center">
              При добавлении продавец будет автоматически выбран как подрядчик
            </p>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

const HotDealsPage = () => {
  const { token, user } = useAuth();
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addingToGarage, setAddingToGarage] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const [formData, setFormData] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    price_cny: '',
    special_price_cny: '',
    mileage: '',
    engine_type: 'ice',
    engine_volume: '',
    image_url: '',
    description: '',
    expires_hours: 24
  });

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  // Check if user can create deals (moderator/admin or verified contractor)
  const canCreateDeals = user && (
    user.role === 'moderator' || 
    user.role === 'admin' ||
    user.is_verified_contractor
  );

  const fetchDeals = async () => {
    try {
      const response = await axios.get(`${API}/hot-deals`);
      setDeals(response.data);
    } catch (error) {
      console.error('Error fetching hot deals:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDeals();
    // Refresh every 30 seconds to remove expired deals
    const interval = setInterval(fetchDeals, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleExpire = useCallback((dealId) => {
    setDeals(prev => prev.filter(d => d.id !== dealId));
  }, []);

  const handleAddToGarage = async (dealId) => {
    if (!token) {
      toast.error('Войдите в аккаунт, чтобы добавить авто в гараж');
      return;
    }

    setAddingToGarage(dealId);
    try {
      const response = await axios.post(`${API}/hot-deals/${dealId}/add-to-garage`, {}, { headers });
      toast.success(`${response.data.message}. Продавец: ${response.data.seller_name || 'назначен'}`);
    } catch (error) {
      const message = error.response?.data?.detail || 'Ошибка при добавлении в гараж';
      toast.error(message);
    } finally {
      setAddingToGarage(null);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCreateDeal = async () => {
    if (!formData.brand || !formData.model || !formData.price_cny) {
      toast.error('Заполните обязательные поля');
      return;
    }

    setSubmitting(true);
    try {
      const expiresAt = new Date(Date.now() + formData.expires_hours * 60 * 60 * 1000).toISOString();
      
      await axios.post(`${API}/hot-deals`, {
        brand: formData.brand,
        model: formData.model,
        year: parseInt(formData.year),
        price_cny: parseFloat(formData.price_cny),
        special_price_cny: formData.special_price_cny ? parseFloat(formData.special_price_cny) : null,
        mileage: formData.mileage ? parseInt(formData.mileage) : null,
        engine_type: formData.engine_type,
        engine_volume: formData.engine_volume ? parseInt(formData.engine_volume) : null,
        image_url: formData.image_url || null,
        description: formData.description || null,
        expires_at: expiresAt
      }, { headers });

      toast.success('Горящее предложение создано');
      setShowAddDialog(false);
      setFormData({
        brand: '', model: '', year: new Date().getFullYear(),
        price_cny: '', special_price_cny: '', mileage: '',
        engine_type: 'ice', engine_volume: '', image_url: '',
        description: '', expires_hours: 24
      });
      fetchDeals();
    } catch (error) {
      const message = error.response?.data?.detail || 'Ошибка при создании предложения';
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  const getEngineTypeLabel = (type) => {
    const labels = { ice: 'ДВС', hybrid: 'Гибрид', electric: 'Электро' };
    return labels[type] || type;
  };

  return (
    <div className="min-h-screen bg-[#0B0F14] py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <div className="mb-6">
          <Link to="/">
            <Button variant="ghost" className="text-slate-400 hover:text-white">
              <ArrowLeft size={18} className="mr-2" />
              На главную
            </Button>
          </Link>
        </div>

        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-500/20 to-red-500/20 border border-orange-500/30 rounded-full px-4 py-2 mb-4">
            <Flame size={18} className="text-orange-500" />
            <span className="text-orange-400 font-medium">Ограниченное время</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Горящие предложения
          </h1>
          <p className="text-slate-400 max-w-2xl mx-auto mb-6">
            Специальные цены от проверенных продавцов. Успейте забрать выгодное предложение до истечения таймера!
          </p>

          {/* Add Deal Button - only for authorized sellers */}
          {canCreateDeals && (
            <Button
              onClick={() => setShowAddDialog(true)}
              className="bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white"
            >
              <Plus size={18} className="mr-2" />
              Добавить предложение
            </Button>
          )}
        </div>

        {/* Deals Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 size={32} className="text-orange-500 animate-spin" />
          </div>
        ) : deals.length > 0 ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {deals.map((deal) => (
              <HotDealCard
                key={deal.id}
                deal={deal}
                onAddToGarage={handleAddToGarage}
                onExpire={handleExpire}
                isAdding={addingToGarage === deal.id}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
            <Flame size={64} className="mx-auto mb-4 text-slate-600" />
            <h3 className="text-xl font-semibold text-white mb-2">Нет активных предложений</h3>
            <p className="text-slate-400 mb-6">
              Горящие предложения появляются регулярно. Следите за обновлениями!
            </p>
            <Link to="/catalog">
              <Button className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
                Перейти в каталог
              </Button>
            </Link>
          </div>
        )}
      </div>

      {/* Add Deal Dialog */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Flame size={20} className="text-orange-500" />
              Создать горящее предложение
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Марка *</Label>
                <Input
                  name="brand"
                  value={formData.brand}
                  onChange={handleChange}
                  placeholder="BYD"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Модель *</Label>
                <Input
                  name="model"
                  value={formData.model}
                  onChange={handleChange}
                  placeholder="Seal"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Год выпуска</Label>
                <Input
                  type="number"
                  name="year"
                  value={formData.year}
                  onChange={handleChange}
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
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
                        ? 'bg-orange-500 text-white border-orange-500'
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

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-300">Цена (¥) *</Label>
                <Input
                  type="number"
                  name="price_cny"
                  value={formData.price_cny}
                  onChange={handleChange}
                  placeholder="200000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
              <div>
                <Label className="text-slate-300">Спец. цена (¥)</Label>
                <Input
                  type="number"
                  name="special_price_cny"
                  value={formData.special_price_cny}
                  onChange={handleChange}
                  placeholder="180000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
                <p className="text-slate-500 text-xs mt-1">Если есть скидка</p>
              </div>
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
                placeholder="Особенности автомобиля..."
                className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 min-h-[80px]"
              />
            </div>

            <div>
              <Label className="text-slate-300">Срок действия предложения</Label>
              <select
                name="expires_hours"
                value={formData.expires_hours}
                onChange={handleChange}
                className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white"
              >
                <option value={6}>6 часов</option>
                <option value={12}>12 часов</option>
                <option value={24}>24 часа</option>
                <option value={48}>2 дня</option>
                <option value={72}>3 дня</option>
                <option value={168}>7 дней</option>
              </select>
            </div>

            <Button
              onClick={handleCreateDeal}
              disabled={submitting}
              className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600 text-white"
            >
              {submitting ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <Flame size={16} className="mr-2" />
              )}
              Создать предложение
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HotDealsPage;
