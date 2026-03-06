import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Car,
  CheckCircle2,
  Clock,
  Loader2,
  DollarSign,
  Wallet,
  Search,
  Truck,
  Ship,
  FileCheck,
  CreditCard,
  Package,
  ChevronRight,
  AlertCircle,
  BadgeCheck
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STAGES = [
  { key: 'leasing_request', label: 'Лизинг', icon: CreditCard, optional: true },
  { key: 'inspection', label: 'Проверка', icon: Search },
  { key: 'export', label: 'Экспорт', icon: FileCheck },
  { key: 'logistics', label: 'Логистика', icon: Truck },
  { key: 'payment', label: 'Оплата', icon: DollarSign },
  { key: 'delivery', label: 'Доставка', icon: Package }
];

const DealCars = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [deals, setDeals] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [contractorDialog, setContractorDialog] = useState(null);
  const [paymentDialog, setPaymentDialog] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [balance, setBalance] = useState(0);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [dealsRes, contractorsRes, accountRes] = await Promise.all([
        axios.get(`${API}/deals`, { headers }),
        axios.get(`${API}/contractors`, { headers }),
        axios.get(`${API}/account/summary`, { headers })
      ]);
      setDeals(dealsRes.data.filter(d => d.status === 'active'));
      setContractors(contractorsRes.data);
      setBalance(accountRes.data.balance || 0);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const skipLeasing = async (dealId) => {
    try {
      await axios.post(`${API}/deals/${dealId}/skip-leasing`, {}, { headers });
      toast.success('Этап лизинга пропущен');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    }
  };

  const requestLeasing = async (dealId, companyId) => {
    try {
      await axios.post(`${API}/deals/${dealId}/request-leasing`, {
        leasing_company_id: companyId
      }, { headers });
      toast.success('Запрос на лизинг отправлен');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    }
  };

  const selectContractor = async (dealId, stage, contractorId, price) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/select-contractor`, {
        stage,
        contractor_id: contractorId,
        price
      }, { headers });
      toast.success('Подрядчик выбран');
      setContractorDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  const payStage = async (dealId, stage, amount) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/pay-stage`, {
        stage,
        amount
      }, { headers });
      toast.success('Оплата прошла успешно');
      setPaymentDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  const getStageStatus = (deal, stageKey) => {
    const stage = deal.stages?.[stageKey];
    if (!stage) return 'pending';
    if (stage.completed || stage.moderator_approved) return 'completed';
    if (stage.paid) return 'paid';
    if (stage.contractor_id) return 'contractor_selected';
    if (stage.skipped) return 'skipped';
    if (stage.requested) return 'requested';
    return 'pending';
  };

  const getCurrentStageIndex = (deal) => {
    return STAGES.findIndex(s => s.key === deal.current_stage);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-[#00E5FF]" size={32} />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="deal-cars">
      {/* Header with Balance */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Авто для сделки</h1>
          <p className="text-slate-400">Управление активными сделками</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="px-4 py-2 bg-[#15191E] border border-[#27272A] rounded-sm">
            <div className="flex items-center gap-2">
              <Wallet size={18} className="text-emerald-400" />
              <span className="text-emerald-400 font-bold">${balance.toLocaleString()}</span>
            </div>
          </div>
        </div>
      </div>

      {deals.length === 0 ? (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <p className="text-white font-medium mb-2">Нет активных сделок</p>
          <p className="text-slate-400 text-sm">Добавьте автомобиль из гаража или выберите предложение из тендера</p>
        </div>
      ) : (
        <div className="space-y-6">
          {deals.map(deal => (
            <DealCard
              key={deal.id}
              deal={deal}
              balance={balance}
              contractors={contractors}
              onSkipLeasing={() => skipLeasing(deal.id)}
              onRequestLeasing={(companyId) => requestLeasing(deal.id, companyId)}
              onSelectContractor={(stage) => setContractorDialog({ dealId: deal.id, stage })}
              onPayStage={(stage, amount) => setPaymentDialog({ dealId: deal.id, stage, amount })}
            />
          ))}
        </div>
      )}

      {/* Contractor Selection Dialog */}
      <Dialog open={!!contractorDialog} onOpenChange={() => setContractorDialog(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle>Выбор подрядчика</DialogTitle>
          </DialogHeader>
          {contractorDialog && (
            <div className="space-y-4 mt-4">
              <p className="text-slate-400 text-sm">
                Этап: {STAGES.find(s => s.key === contractorDialog.stage)?.label}
              </p>
              {contractors
                .filter(c => {
                  if (contractorDialog.stage === 'inspection') return c.services?.includes('inspection');
                  if (contractorDialog.stage === 'export') return c.services?.includes('export') || c.services?.includes('customs');
                  if (contractorDialog.stage === 'logistics') return c.services?.includes('logistics');
                  return true;
                })
                .map(contractor => {
                  // Get price from service_prices based on current stage
                  const getContractorPrice = () => {
                    const stage = contractorDialog.stage;
                    const prices = contractor.service_prices;
                    if (prices && prices[stage]) {
                      return prices[stage];
                    }
                    // Fallback for export stage - check customs price too
                    if (stage === 'export' && prices?.customs) {
                      return prices.customs;
                    }
                    return null;
                  };
                  const price = getContractorPrice();
                  
                  // Only show contractors that have a price for this service
                  if (!price) return null;
                  
                  return (
                    <div
                      key={contractor.id}
                      className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A] hover:border-[#00E5FF]/50 cursor-pointer"
                      onClick={() => selectContractor(contractorDialog.dealId, contractorDialog.stage, contractor.id, price)}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{contractor.name}</p>
                          <p className="text-slate-400 text-sm">{contractor.description}</p>
                          {contractor.rating && (
                            <p className="text-amber-400 text-xs mt-1">★ {contractor.rating.toFixed(1)} • {contractor.deals_count || 0} сделок</p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-[#00E5FF] font-bold text-lg">${price}</p>
                          <p className="text-slate-500 text-xs">за услугу</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              {contractors.filter(c => {
                const stage = contractorDialog.stage;
                const hasService = stage === 'inspection' ? c.services?.includes('inspection') :
                                   stage === 'export' ? (c.services?.includes('export') || c.services?.includes('customs')) :
                                   stage === 'logistics' ? c.services?.includes('logistics') : true;
                const hasPrice = c.service_prices && (c.service_prices[stage] || (stage === 'export' && c.service_prices.customs));
                return hasService && !hasPrice;
              }).length > 0 && (
                <p className="text-slate-500 text-xs text-center pt-2 border-t border-[#27272A]">
                  Некоторые подрядчики не указали цены на этот этап
                </p>
              )}
              {processing && <Loader2 className="animate-spin mx-auto" />}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Payment Dialog */}
      <Dialog open={!!paymentDialog} onOpenChange={() => setPaymentDialog(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle>Оплата этапа</DialogTitle>
          </DialogHeader>
          {paymentDialog && (
            <div className="space-y-4 mt-4">
              <div className="p-4 bg-[#0B0F14] rounded-sm">
                <p className="text-slate-400 text-sm">Этап</p>
                <p className="text-white font-medium">{STAGES.find(s => s.key === paymentDialog.stage)?.label}</p>
              </div>
              <div className="p-4 bg-[#0B0F14] rounded-sm">
                <p className="text-slate-400 text-sm">Сумма к оплате</p>
                <p className="text-[#00E5FF] text-2xl font-bold">${paymentDialog.amount}</p>
              </div>
              <div className="p-4 bg-[#0B0F14] rounded-sm">
                <p className="text-slate-400 text-sm">Ваш баланс</p>
                <p className={`text-xl font-bold ${balance >= paymentDialog.amount ? 'text-emerald-400' : 'text-red-400'}`}>
                  ${balance}
                </p>
              </div>
              {balance < paymentDialog.amount ? (
                <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-sm">
                  <p className="text-red-400 text-sm">Недостаточно средств. Пополните баланс.</p>
                </div>
              ) : (
                <Button
                  onClick={() => payStage(paymentDialog.dealId, paymentDialog.stage, paymentDialog.amount)}
                  disabled={processing}
                  className="w-full bg-emerald-500 hover:bg-emerald-600 text-white"
                >
                  {processing ? <Loader2 className="animate-spin mr-2" size={16} /> : <DollarSign size={16} className="mr-2" />}
                  Оплатить ${paymentDialog.amount}
                </Button>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Deal Card Component
const DealCard = ({ deal, balance, contractors, onSkipLeasing, onRequestLeasing, onSelectContractor, onPayStage }) => {
  const [expanded, setExpanded] = useState(true);
  const leasingCompanies = contractors.filter(c => c.services?.includes('leasing'));

  const getStageStatus = (stageKey) => {
    const stage = deal.stages?.[stageKey];
    if (!stage) return 'pending';
    if (stage.completed || stage.moderator_approved) return 'completed';
    if (stage.paid) return 'paid';
    if (stage.contractor_id) return 'contractor_selected';
    if (stage.skipped) return 'skipped';
    if (stage.requested) return 'requested';
    return 'pending';
  };

  const isCurrentStage = (stageKey) => deal.current_stage === stageKey;

  return (
    <div className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden">
      {/* Car Header */}
      <div className="p-4 border-b border-[#27272A] flex items-center justify-between">
        <div className="flex items-center gap-4">
          {deal.car_info?.image_url ? (
            <img src={deal.car_info.image_url} alt="" className="w-16 h-12 object-cover rounded" />
          ) : (
            <div className="w-16 h-12 bg-[#0B0F14] rounded flex items-center justify-center">
              <Car size={24} className="text-slate-600" />
            </div>
          )}
          <div>
            <h3 className="text-white font-semibold">
              {deal.car_info?.brand} {deal.car_info?.model}
            </h3>
            <p className="text-slate-400 text-sm">{deal.car_info?.year} • ${deal.car_info?.price_usd?.toLocaleString()}</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {deal.from_tender && (
            <span className="px-2 py-1 bg-emerald-500/10 text-emerald-400 text-xs rounded">Из тендера</span>
          )}
          <span className="px-3 py-1 bg-[#00E5FF]/10 text-[#00E5FF] rounded-full text-sm">
            Активна
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="p-4 bg-[#0B0F14]">
        <div className="flex items-center justify-between mb-2">
          <p className="text-slate-400 text-xs">Прогресс сделки</p>
          <p className="text-white text-xs font-medium">
            {STAGES.filter(s => getStageStatus(s.key) === 'completed').length} / {STAGES.length} этапов
          </p>
        </div>
        <div className="flex gap-1">
          {STAGES.map((stage, idx) => {
            const status = getStageStatus(stage.key);
            return (
              <div
                key={stage.key}
                className={`flex-1 h-2 rounded-full ${
                  status === 'completed' ? 'bg-emerald-500' :
                  status === 'paid' ? 'bg-blue-500' :
                  status === 'contractor_selected' ? 'bg-amber-500' :
                  status === 'skipped' ? 'bg-slate-600' :
                  isCurrentStage(stage.key) ? 'bg-[#00E5FF]' :
                  'bg-[#27272A]'
                }`}
              />
            );
          })}
        </div>
      </div>

      {/* Stages */}
      {expanded && (
        <div className="p-4 space-y-3">
          {STAGES.map((stage, idx) => {
            const status = getStageStatus(stage.key);
            const stageData = deal.stages?.[stage.key];
            const Icon = stage.icon;
            const isCurrent = isCurrentStage(stage.key);

            return (
              <div
                key={stage.key}
                className={`p-4 rounded-sm border ${
                  isCurrent ? 'border-[#00E5FF] bg-[#00E5FF]/5' :
                  status === 'completed' ? 'border-emerald-500/30 bg-emerald-500/5' :
                  'border-[#27272A] bg-[#0B0F14]'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      status === 'completed' ? 'bg-emerald-500/20' :
                      isCurrent ? 'bg-[#00E5FF]/20' :
                      'bg-[#27272A]'
                    }`}>
                      {status === 'completed' ? (
                        <CheckCircle2 size={20} className="text-emerald-400" />
                      ) : (
                        <Icon size={20} className={isCurrent ? 'text-[#00E5FF]' : 'text-slate-500'} />
                      )}
                    </div>
                    <div>
                      <p className={`font-medium ${
                        status === 'completed' ? 'text-emerald-400' :
                        isCurrent ? 'text-white' :
                        'text-slate-400'
                      }`}>
                        {stage.label}
                        {stage.optional && <span className="text-slate-500 text-xs ml-2">(опционально)</span>}
                      </p>
                      {status === 'contractor_selected' && stageData?.price && (
                        <p className="text-[#00E5FF] text-sm">${stageData.price}</p>
                      )}
                      {status === 'paid' && (
                        <p className="text-emerald-400 text-sm">Оплачено</p>
                      )}
                      {status === 'requested' && (
                        <p className="text-amber-400 text-sm">Запрос отправлен</p>
                      )}
                      {status === 'skipped' && (
                        <p className="text-slate-500 text-sm">Пропущен</p>
                      )}
                    </div>
                  </div>

                  {/* Stage Actions */}
                  {isCurrent && status === 'pending' && (
                    <div className="flex gap-2">
                      {stage.key === 'leasing_request' && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={onSkipLeasing}
                            className="border-slate-500 text-slate-400"
                          >
                            Пропустить
                          </Button>
                          <Select onValueChange={(v) => onRequestLeasing(v)}>
                            <SelectTrigger className="w-40 bg-[#0B0F14] border-[#27272A]">
                              <SelectValue placeholder="Выбрать компанию" />
                            </SelectTrigger>
                            <SelectContent className="bg-[#15191E] border-[#27272A]">
                              {leasingCompanies.map(c => (
                                <SelectItem key={c.id} value={c.id} className="text-white">{c.name}</SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </>
                      )}
                      {['inspection', 'export', 'logistics'].includes(stage.key) && (
                        <Button
                          size="sm"
                          onClick={() => onSelectContractor(stage.key)}
                          className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                        >
                          Выбрать подрядчика
                        </Button>
                      )}
                    </div>
                  )}

                  {status === 'contractor_selected' && !stageData?.paid && (
                    <Button
                      size="sm"
                      onClick={() => onPayStage(stage.key, stageData?.price || 500)}
                      className="bg-emerald-500 hover:bg-emerald-600 text-white"
                    >
                      <DollarSign size={14} className="mr-1" />
                      Оплатить
                    </Button>
                  )}

                  {status === 'paid' && !stageData?.moderator_approved && (
                    <span className="text-amber-400 text-xs flex items-center gap-1">
                      <Clock size={14} />
                      Ожидает подтверждения
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Total */}
      <div className="p-4 border-t border-[#27272A] bg-[#0B0F14] flex items-center justify-between">
        <div>
          <p className="text-slate-400 text-sm">Всего оплачено</p>
          <p className="text-white font-bold">${deal.total_paid?.toLocaleString() || 0}</p>
        </div>
        <Button
          variant="ghost"
          onClick={() => setExpanded(!expanded)}
          className="text-slate-400"
        >
          {expanded ? 'Свернуть' : 'Развернуть'}
        </Button>
      </div>
    </div>
  );
};

export default DealCars;
