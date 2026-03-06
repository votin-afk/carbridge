import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  MapPin,
  Car,
  Loader2,
  Ship,
  Truck,
  Package,
  CheckCircle2,
  Clock,
  Navigation,
  RefreshCw,
  ExternalLink,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Tracking stages with locations
const TRACKING_STAGES = [
  { id: 'china_warehouse', label: 'Склад в Китае', icon: Package, location: { lat: 31.2304, lng: 121.4737, city: 'Шанхай' } },
  { id: 'china_port', label: 'Порт отправки', icon: Ship, location: { lat: 22.5431, lng: 114.0579, city: 'Шэньчжэнь' } },
  { id: 'in_transit', label: 'В пути', icon: Navigation, location: { lat: 35.6762, lng: 139.6503, city: 'В море' } },
  { id: 'eu_port', label: 'Порт прибытия', icon: Ship, location: { lat: 54.6872, lng: 25.2797, city: 'Клайпеда' } },
  { id: 'customs', label: 'Таможня', icon: Package, location: { lat: 53.9006, lng: 27.5590, city: 'Минск' } },
  { id: 'delivery', label: 'Доставка', icon: Truck, location: { lat: 53.9006, lng: 27.5590, city: 'Минск' } },
  { id: 'delivered', label: 'Доставлено', icon: CheckCircle2, location: null }
];

const Tracking = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [deals, setDeals] = useState([]);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [trackingData, setTrackingData] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchDeals();
  }, []);

  const fetchDeals = async () => {
    try {
      const response = await axios.get(`${API}/deals`, { headers });
      const allDeals = Array.isArray(response.data) ? response.data : [];
      // Filter deals that have passed export stage (in delivery process)
      const trackableDeals = allDeals.filter(d => 
        d.status === 'active' && 
        (d.stages?.export?.completed || d.stages?.export?.paid)
      );
      setDeals(trackableDeals);
      
      if (trackableDeals.length > 0 && !selectedDeal) {
        setSelectedDeal(trackableDeals[0].id);
        fetchTrackingData(trackableDeals[0].id);
      }
    } catch (error) {
      console.error('Error fetching deals:', error);
      toast.error('Ошибка загрузки сделок');
    } finally {
      setLoading(false);
    }
  };

  const fetchTrackingData = async (dealId) => {
    setRefreshing(true);
    try {
      const response = await axios.get(`${API}/deals/${dealId}/tracking`, { headers });
      setTrackingData(response.data);
    } catch (error) {
      // If no tracking data, generate mock based on deal stages
      const deal = deals.find(d => d.id === dealId);
      if (deal) {
        const mockTracking = generateMockTracking(deal);
        setTrackingData(mockTracking);
      }
    } finally {
      setRefreshing(false);
    }
  };

  // Generate mock tracking data based on deal progress
  const generateMockTracking = (deal) => {
    const stages = deal.stages || {};
    let currentStageIndex = 0;
    
    // Determine current stage based on deal progress
    if (stages.customs?.completed || stages.customs?.paid) {
      currentStageIndex = 5; // delivery
    } else if (stages.delivery_rb?.completed || stages.delivery_rb?.paid) {
      currentStageIndex = 4; // customs
    } else if (stages.insurance?.completed || stages.insurance?.skipped) {
      currentStageIndex = 3; // eu_port
    } else if (stages.logistics_china?.completed || stages.logistics_china?.skipped) {
      currentStageIndex = 2; // in_transit
    } else if (stages.export?.completed || stages.export?.paid) {
      currentStageIndex = 1; // china_port
    }
    
    const currentStage = TRACKING_STAGES[currentStageIndex];
    const progress = Math.round((currentStageIndex / (TRACKING_STAGES.length - 1)) * 100);
    
    // Generate history
    const history = TRACKING_STAGES.slice(0, currentStageIndex + 1).map((stage, idx) => ({
      stage: stage.id,
      label: stage.label,
      location: stage.location?.city || '',
      timestamp: new Date(Date.now() - (currentStageIndex - idx) * 24 * 60 * 60 * 1000).toISOString(),
      completed: idx < currentStageIndex
    }));
    
    // Estimate arrival
    const daysRemaining = (TRACKING_STAGES.length - 1 - currentStageIndex) * 3;
    const estimatedArrival = new Date(Date.now() + daysRemaining * 24 * 60 * 60 * 1000);
    
    return {
      deal_id: deal.id,
      car_info: deal.car_info,
      current_stage: currentStage.id,
      current_location: currentStage.location,
      progress,
      estimated_arrival: estimatedArrival.toISOString(),
      history,
      last_updated: new Date().toISOString()
    };
  };

  const handleDealChange = (dealId) => {
    setSelectedDeal(dealId);
    fetchTrackingData(dealId);
  };

  const handleRefresh = () => {
    if (selectedDeal) {
      fetchTrackingData(selectedDeal);
    }
  };

  const getCurrentStageInfo = () => {
    if (!trackingData) return null;
    return TRACKING_STAGES.find(s => s.id === trackingData.current_stage);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('ru-RU', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateStr) => {
    return new Date(dateStr).toLocaleString('ru-RU', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#00E5FF]" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="tracking-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Отследить авто</h1>
          <p className="text-slate-400">GPS отслеживание доставки вашего автомобиля</p>
        </div>
        <Button
          onClick={handleRefresh}
          disabled={refreshing || !selectedDeal}
          variant="outline"
          className="border-[#27272A] text-slate-400 hover:text-white"
        >
          <RefreshCw size={16} className={`mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          Обновить
        </Button>
      </div>

      {deals.length === 0 ? (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <MapPin size={48} className="mx-auto mb-4 text-slate-600" />
          <p className="text-white font-medium mb-2">Нет авто для отслеживания</p>
          <p className="text-slate-400 text-sm">
            Отслеживание станет доступно после оформления экспорта
          </p>
        </div>
      ) : (
        <>
          {/* Car Selection */}
          <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
            <label className="text-slate-400 text-sm mb-2 block">Выберите автомобиль</label>
            <Select value={selectedDeal} onValueChange={handleDealChange}>
              <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                <SelectValue placeholder="Выберите авто" />
              </SelectTrigger>
              <SelectContent className="bg-[#15191E] border-[#27272A]">
                {deals.map(deal => (
                  <SelectItem key={deal.id} value={deal.id} className="text-white">
                    {deal.car_info?.brand} {deal.car_info?.model} {deal.car_info?.year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {trackingData && (
            <>
              {/* Map View */}
              <div className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden">
                <div className="relative h-80 bg-[#0B0F14]">
                  {/* Map placeholder with route visualization */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="relative w-full h-full p-8">
                      {/* Route line */}
                      <svg className="absolute inset-0 w-full h-full" viewBox="0 0 100 50">
                        <defs>
                          <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stopColor="#00E5FF" />
                            <stop offset={`${trackingData.progress}%`} stopColor="#00E5FF" />
                            <stop offset={`${trackingData.progress}%`} stopColor="#27272A" />
                            <stop offset="100%" stopColor="#27272A" />
                          </linearGradient>
                        </defs>
                        <path
                          d="M 10,40 Q 30,10 50,25 T 90,40"
                          fill="none"
                          stroke="url(#routeGradient)"
                          strokeWidth="0.5"
                          strokeDasharray="2,1"
                        />
                      </svg>
                      
                      {/* Location markers */}
                      <div className="absolute left-[10%] top-[70%] flex flex-col items-center">
                        <div className="w-4 h-4 bg-emerald-500 rounded-full border-2 border-white animate-pulse" />
                        <span className="text-xs text-slate-400 mt-1">Китай</span>
                      </div>
                      
                      <div className="absolute left-[50%] top-[40%] flex flex-col items-center transform -translate-x-1/2">
                        {trackingData.current_stage === 'in_transit' ? (
                          <>
                            <div className="w-6 h-6 bg-[#00E5FF] rounded-full border-2 border-white flex items-center justify-center animate-pulse">
                              <Ship size={14} className="text-black" />
                            </div>
                            <span className="text-xs text-[#00E5FF] mt-1 font-medium">В пути</span>
                          </>
                        ) : (
                          <div className="w-3 h-3 bg-slate-600 rounded-full" />
                        )}
                      </div>
                      
                      <div className="absolute right-[10%] top-[70%] flex flex-col items-center">
                        <div className={`w-4 h-4 rounded-full border-2 border-white ${
                          trackingData.progress >= 80 ? 'bg-emerald-500' : 'bg-slate-600'
                        }`} />
                        <span className="text-xs text-slate-400 mt-1">Беларусь</span>
                      </div>
                      
                      {/* Current location marker */}
                      {trackingData.current_location && (
                        <div 
                          className="absolute transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center"
                          style={{ 
                            left: `${10 + trackingData.progress * 0.8}%`, 
                            top: `${40 + Math.sin(trackingData.progress * 0.03) * 20}%` 
                          }}
                        >
                          <div className="relative">
                            <div className="absolute -inset-3 bg-[#00E5FF]/20 rounded-full animate-ping" />
                            <div className="w-8 h-8 bg-[#00E5FF] rounded-full border-2 border-white flex items-center justify-center z-10 relative">
                              <Car size={16} className="text-black" />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Current location badge */}
                  <div className="absolute top-4 left-4 bg-[#15191E]/90 backdrop-blur-sm border border-[#27272A] rounded-sm px-4 py-2">
                    <div className="flex items-center gap-2">
                      <MapPin size={16} className="text-[#00E5FF]" />
                      <span className="text-white font-medium">
                        {trackingData.current_location?.city || 'Определяется...'}
                      </span>
                    </div>
                  </div>
                  
                  {/* Progress badge */}
                  <div className="absolute top-4 right-4 bg-[#15191E]/90 backdrop-blur-sm border border-[#27272A] rounded-sm px-4 py-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[#00E5FF] font-bold text-lg">{trackingData.progress}%</span>
                      <span className="text-slate-400 text-sm">выполнено</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Status Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Current Stage */}
                <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                  <p className="text-slate-400 text-sm mb-2">Текущий этап</p>
                  <div className="flex items-center gap-3">
                    {getCurrentStageInfo() && (
                      <>
                        <div className="w-10 h-10 bg-[#00E5FF]/20 rounded-full flex items-center justify-center">
                          {(() => {
                            const StageIcon = getCurrentStageInfo().icon;
                            return <StageIcon size={20} className="text-[#00E5FF]" />;
                          })()}
                        </div>
                        <span className="text-white font-medium">{getCurrentStageInfo().label}</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Estimated Arrival */}
                <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                  <p className="text-slate-400 text-sm mb-2">Ожидаемая доставка</p>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-emerald-500/20 rounded-full flex items-center justify-center">
                      <Clock size={20} className="text-emerald-400" />
                    </div>
                    <span className="text-white font-medium">
                      {formatDate(trackingData.estimated_arrival)}
                    </span>
                  </div>
                </div>

                {/* Car Info */}
                <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                  <p className="text-slate-400 text-sm mb-2">Автомобиль</p>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-amber-500/20 rounded-full flex items-center justify-center">
                      <Car size={20} className="text-amber-400" />
                    </div>
                    <div>
                      <p className="text-white font-medium">
                        {trackingData.car_info?.brand} {trackingData.car_info?.model}
                      </p>
                      <p className="text-slate-400 text-xs">{trackingData.car_info?.year}</p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
                <h3 className="text-white font-semibold mb-6">История перемещений</h3>
                <div className="space-y-4">
                  {TRACKING_STAGES.map((stage, index) => {
                    const historyItem = trackingData.history?.find(h => h.stage === stage.id);
                    const isCurrent = stage.id === trackingData.current_stage;
                    const isPast = index < TRACKING_STAGES.findIndex(s => s.id === trackingData.current_stage);
                    const StageIcon = stage.icon;

                    return (
                      <div key={stage.id} className="flex items-start gap-4">
                        {/* Timeline line */}
                        <div className="flex flex-col items-center">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            isCurrent ? 'bg-[#00E5FF] text-black' :
                            isPast ? 'bg-emerald-500/20 text-emerald-400' :
                            'bg-[#27272A] text-slate-500'
                          }`}>
                            <StageIcon size={18} />
                          </div>
                          {index < TRACKING_STAGES.length - 1 && (
                            <div className={`w-0.5 h-12 ${
                              isPast ? 'bg-emerald-500' : 'bg-[#27272A]'
                            }`} />
                          )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 pb-4">
                          <div className="flex items-center justify-between">
                            <p className={`font-medium ${
                              isCurrent ? 'text-[#00E5FF]' :
                              isPast ? 'text-white' :
                              'text-slate-500'
                            }`}>
                              {stage.label}
                            </p>
                            {historyItem?.timestamp && (
                              <span className="text-slate-500 text-sm">
                                {formatDateTime(historyItem.timestamp)}
                              </span>
                            )}
                          </div>
                          {stage.location?.city && (
                            <p className="text-slate-400 text-sm mt-1">
                              <MapPin size={12} className="inline mr-1" />
                              {stage.location.city}
                            </p>
                          )}
                          {isCurrent && (
                            <span className="inline-block mt-2 px-2 py-1 bg-[#00E5FF]/10 text-[#00E5FF] text-xs rounded">
                              Текущее местоположение
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Last Updated */}
              <div className="text-center text-slate-500 text-sm">
                Последнее обновление: {formatDateTime(trackingData.last_updated)}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default Tracking;
