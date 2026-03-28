import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import axios from 'axios';
import { toast } from 'sonner';
import {
  Car,
  CheckCircle2,
  Loader2,
  Calendar,
  DollarSign,
  MapPin,
  FileText,
  Download,
  Trophy
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const getProxiedImageUrl = (url) => {
  if (!url) return null;
  if (url.includes('autoimg.cn') || url.includes('che168.com') || url.includes('autohome.com')) {
    return `${API}/api/proxy/image?url=${encodeURIComponent(url)}`;
  }
  return url;
};

const PurchasedCars = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [completedDeals, setCompletedDeals] = useState([]);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchCompletedDeals();
  }, []);

  const fetchCompletedDeals = async () => {
    try {
      const response = await axios.get(`${API}/api/deals/completed`, { headers });
      setCompletedDeals(response.data);
    } catch (error) {
      console.error('Error fetching completed deals:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Trophy className="text-amber-400" />
            Приобретённые авто
          </h1>
          <p className="text-slate-400 mt-1">
            Автомобили с завершёнными сделками
          </p>
        </div>
        <div className="text-right">
          <p className="text-slate-400 text-sm">Всего приобретено</p>
          <p className="text-2xl font-bold text-[#00E5FF]">{completedDeals.length}</p>
        </div>
      </div>

      {/* Empty State */}
      {completedDeals.length === 0 ? (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <Car size={64} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-xl font-medium text-white mb-2">Пока нет приобретённых авто</h3>
          <p className="text-slate-400 max-w-md mx-auto">
            Здесь будут отображаться автомобили после завершения всех этапов сделки
          </p>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {completedDeals.map((deal) => {
            const car = deal.car_details || deal.car_info || {};
            return (
              <div
                key={deal.id}
                className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden"
                data-testid={`purchased-car-${deal.id}`}
              >
                {/* Car Image */}
                <div className="h-48 bg-[#1C2128] relative">
                  <img
                    src={getProxiedImageUrl(car.image_url) || 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%230B0F14" width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="%23555" font-size="14">AUTO</text></svg>'}
                    alt={`${car.brand || ''} ${car.model || ''}`}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect fill="%230B0F14" width="100" height="100"/><text x="50" y="55" text-anchor="middle" fill="%23555" font-size="14">AUTO</text></svg>';
                    }}
                  />
                  <div className="absolute top-3 right-3 px-3 py-1.5 bg-emerald-500/90 backdrop-blur-sm rounded-full flex items-center gap-2">
                    <CheckCircle2 size={14} />
                    <span className="text-sm font-medium text-white">Завершена</span>
                  </div>
                </div>

                {/* Car Info */}
                <div className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <p className="text-slate-500 text-sm">{car.brand || 'Марка'}</p>
                      <h3 className="text-xl font-bold text-white">
                        {car.model || 'Модель'}
                      </h3>
                      <p className="text-slate-400 text-sm">
                        {car.year || '—'} • {car.mileage ? `${car.mileage.toLocaleString()} км` : '—'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-slate-500 text-xs">Итого оплачено</p>
                      <p className="text-2xl font-bold text-emerald-400">
                        ${(deal.total_paid || 0).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* Details Grid */}
                  <div className="grid grid-cols-2 gap-3 mb-4">
                    <div className="bg-[#0B0F14] rounded p-3">
                      <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                        <Calendar size={12} />
                        Дата завершения
                      </div>
                      <p className="text-white text-sm font-medium">
                        {formatDate(deal.completed_at)}
                      </p>
                    </div>
                    <div className="bg-[#0B0F14] rounded p-3">
                      <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                        <DollarSign size={12} />
                        Цена авто
                      </div>
                      <p className="text-white text-sm font-medium">
                        ${(car.price_usd || deal.car_price || 0).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  {/* VIN if available */}
                  {car.vin && (
                    <div className="bg-[#0B0F14] rounded p-3 mb-4">
                      <div className="flex items-center gap-2 text-slate-500 text-xs mb-1">
                        <FileText size={12} />
                        VIN номер
                      </div>
                      <p className="text-white text-sm font-mono">{car.vin}</p>
                    </div>
                  )}

                  {/* Stages Summary */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {deal.stages && Object.entries(deal.stages).map(([key, stage]) => {
                      if (!stage.completed && !stage.paid) return null;
                      const stageNames = {
                        car_payment: 'Оплата авто',
                        inspection: 'Проверка',
                        purchase: 'Выкуп',
                        logistics: 'Логистика',
                        customs: 'Растаможка',
                        export: 'Экспорт',
                        sbkts: 'СБКТС',
                        registration: 'Регистрация'
                      };
                      return (
                        <span
                          key={key}
                          className="px-2 py-1 text-xs bg-emerald-500/10 text-emerald-400 rounded"
                        >
                          ✓ {stageNames[key] || key}
                        </span>
                      );
                    })}
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 border-[#27272A] text-slate-300 hover:bg-[#27272A]"
                    >
                      <FileText size={14} className="mr-2" />
                      Документы
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="flex-1 border-[#27272A] text-slate-300 hover:bg-[#27272A]"
                    >
                      <Download size={14} className="mr-2" />
                      Акт приёмки
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Total Stats */}
      {completedDeals.length > 0 && (
        <div className="bg-gradient-to-r from-emerald-500/10 to-[#00E5FF]/10 border border-emerald-500/20 rounded-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-400 text-sm">Общая сумма покупок</p>
              <p className="text-3xl font-bold text-white">
                ${completedDeals.reduce((sum, d) => sum + (d.total_paid || 0), 0).toLocaleString()}
              </p>
            </div>
            <div className="text-right">
              <p className="text-slate-400 text-sm">Средняя стоимость</p>
              <p className="text-xl font-bold text-[#00E5FF]">
                ${Math.round(completedDeals.reduce((sum, d) => sum + (d.total_paid || 0), 0) / completedDeals.length).toLocaleString()}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PurchasedCars;
