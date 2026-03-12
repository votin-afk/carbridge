import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Slider } from '../../components/ui/slider';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../../components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { Checkbox } from "../../components/ui/checkbox";
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
  BadgeCheck,
  Calculator,
  Shield,
  FileText,
  Building2,
  CheckCheck,
  SkipForward,
  Trash2,
  XCircle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Platform commission rates
const PLATFORM_COMMISSION = 0.03; // 3%
const PLATFORM_PAYMENT_FEE = 0.01; // +1% if paid through platform

// New stages structure
const STAGES = [
  { key: 'leasing', label: 'Лизинг', icon: CreditCard, optional: true, hasCalculator: true },
  { key: 'inspection', label: 'Инспекция авто', icon: Search, optional: true },
  { key: 'export', label: 'Выкуп и экспорт', icon: FileCheck, optional: false, hasInvoice: true },
  { key: 'logistics_china', label: 'Доставка до порта (Китай)', icon: Truck, optional: true },
  { key: 'insurance', label: 'Страхование авто', icon: Shield, optional: true },
  { key: 'delivery_rb', label: 'Доставка в Беларусь', icon: Ship, optional: true },
  { key: 'customs', label: 'Таможенное оформление', icon: FileText, optional: true },
  { key: 'completion', label: 'Завершение сделки', icon: CheckCheck, optional: false }
];

// Leasing terms
const LEASING_TERMS = [12, 24, 36, 48, 60];

const DealCars = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [deals, setDeals] = useState([]);
  const [contractors, setContractors] = useState([]);
  const [leasingCompanies, setLeasingCompanies] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [balance, setBalance] = useState(0);

  // Dialog states
  const [leasingDialog, setLeasingDialog] = useState(null);
  const [contractorDialog, setContractorDialog] = useState(null);
  const [invoiceDialog, setInvoiceDialog] = useState(null);
  const [skipDialog, setSkipDialog] = useState(null);
  const [customsDialog, setCustomsDialog] = useState(null);
  const [cancelDealDialog, setCancelDealDialog] = useState(null); // { dealId: string }
  const [completeStageDialog, setCompleteStageDialog] = useState(null); // { dealId, stage }
  const [updatePriceDialog, setUpdatePriceDialog] = useState(null); // { dealId, stage, currentPrice }

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [dealsRes, contractorsRes, accountRes] = await Promise.all([
        axios.get(`${API}/deals`, { headers }),
        axios.get(`${API}/contractors`),
        axios.get(`${API}/account/summary`, { headers })
      ]);
      
      const activeDeals = Array.isArray(dealsRes.data) 
        ? dealsRes.data.filter(d => d.status === 'active')
        : [];
      setDeals(activeDeals);
      
      const allContractors = Array.isArray(contractorsRes.data) ? contractorsRes.data : [];
      setContractors(allContractors);
      
      // Filter leasing companies
      const leasing = allContractors.filter(c => 
        c.services?.toLowerCase().includes('leasing') || 
        c.services?.toLowerCase().includes('лизинг')
      );
      setLeasingCompanies(leasing);
      
      setBalance(accountRes.data?.balance || 0);
    } catch (error) {
      console.error('Error:', error);
      toast.error('Ошибка загрузки данных');
    } finally {
      setLoading(false);
    }
  };

  // Skip stage
  const skipStage = async (dealId, stage) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/skip-stage`, { stage }, { headers });
      toast.success('Этап пропущен');
      setSkipDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  // Complete stage - send for moderator approval
  const completeStage = async (dealId, stage) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/complete-stage`, { stage }, { headers });
      toast.success('Этап отмечен как завершённый. Ожидайте подтверждения модератора.');
      setCompleteStageDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  // Update stage price
  const updateStagePrice = async (dealId, stage, newPrice, reason) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/update-stage-price`, { 
        stage, 
        price: newPrice,
        reason 
      }, { headers });
      toast.success('Стоимость этапа обновлена');
      setUpdatePriceDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  // Cancel deal - show confirmation dialog
  const showCancelDealDialog = (dealId) => {
    setCancelDealDialog({ dealId });
  };

  // Execute cancel deal after confirmation
  const executeCancelDeal = async () => {
    if (!cancelDealDialog) return;
    setProcessing(true);
    try {
      await axios.delete(`${API}/deals/${cancelDealDialog.dealId}`, { headers });
      toast.success('Сделка отменена');
      setDeals(prev => prev.filter(d => d.id !== cancelDealDialog.dealId));
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при отмене сделки');
    } finally {
      setProcessing(false);
      setCancelDealDialog(null);
    }
  };

  // Submit leasing request
  const submitLeasingRequest = async (dealId, leasingData) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/leasing-request`, leasingData, { headers });
      toast.success('Заявка на лизинг отправлена');
      setLeasingDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  // Select contractor and create invoice
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

  // Pay invoice
  const payInvoice = async (dealId, stage, amount, throughPlatform) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/pay-invoice`, {
        stage,
        amount,
        through_platform: throughPlatform
      }, { headers });
      toast.success(throughPlatform ? 'Оплата прошла успешно' : 'Счёт отмечен как оплаченный');
      setInvoiceDialog(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
  };

  // Complete deal
  const completeDeal = async (dealId) => {
    setProcessing(true);
    try {
      await axios.post(`${API}/deals/${dealId}/complete`, {}, { headers });
      toast.success('Сделка завершена!');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка');
    } finally {
      setProcessing(false);
    }
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
              leasingCompanies={leasingCompanies}
              onOpenLeasing={(dealId) => setLeasingDialog({ dealId, carPrice: deal.car_info?.price_usd || 0 })}
              onOpenContractor={(dealId, stage) => setContractorDialog({ dealId, stage })}
              onOpenInvoice={(dealId, stage, invoice) => setInvoiceDialog({ dealId, stage, invoice })}
              onSkipStage={(dealId, stage) => setSkipDialog({ dealId, stage })}
              onOpenCustoms={(dealId, carInfo) => setCustomsDialog({ dealId, carInfo })}
              onCompleteDeal={completeDeal}
              onCancelDeal={showCancelDealDialog}
            />
          ))}
        </div>
      )}

      {/* Leasing Calculator Dialog */}
      <LeasingDialog
        open={!!leasingDialog}
        onClose={() => setLeasingDialog(null)}
        leasingData={leasingDialog}
        leasingCompanies={leasingCompanies}
        onSubmit={submitLeasingRequest}
        processing={processing}
      />

      {/* Contractor Selection Dialog */}
      <ContractorDialog
        open={!!contractorDialog}
        onClose={() => setContractorDialog(null)}
        dialogData={contractorDialog}
        contractors={contractors}
        onSelect={selectContractor}
        processing={processing}
      />

      {/* Invoice Dialog */}
      <InvoiceDialog
        open={!!invoiceDialog}
        onClose={() => setInvoiceDialog(null)}
        invoiceData={invoiceDialog}
        balance={balance}
        onPay={payInvoice}
        processing={processing}
      />

      {/* Skip Stage Dialog */}
      <Dialog open={!!skipDialog} onOpenChange={() => setSkipDialog(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle>Пропустить этап?</DialogTitle>
          </DialogHeader>
          {skipDialog && (
            <div className="space-y-4 mt-4">
              <p className="text-slate-400">
                Вы уверены, что хотите пропустить этап "{STAGES.find(s => s.key === skipDialog.stage)?.label}"?
              </p>
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={() => setSkipDialog(null)}
                  className="flex-1 border-slate-500"
                >
                  Отмена
                </Button>
                <Button
                  onClick={() => skipStage(skipDialog.dealId, skipDialog.stage)}
                  disabled={processing}
                  className="flex-1 bg-amber-500 hover:bg-amber-600 text-black"
                >
                  {processing ? <Loader2 className="animate-spin mr-2" size={16} /> : <SkipForward size={16} className="mr-2" />}
                  Пропустить
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Customs Calculator Dialog */}
      <CustomsDialog
        open={!!customsDialog}
        onClose={() => setCustomsDialog(null)}
        customsData={customsDialog}
        contractors={contractors}
        onSelectContractor={selectContractor}
        processing={processing}
      />

      {/* Cancel Deal Confirmation Dialog */}
      <AlertDialog open={!!cancelDealDialog} onOpenChange={() => setCancelDealDialog(null)}>
        <AlertDialogContent className="bg-[#15191E] border-[#27272A]">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-white">Отменить сделку?</AlertDialogTitle>
            <AlertDialogDescription className="text-slate-400">
              Авто вернётся в гараж. Это действие необратимо.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="bg-[#27272A] text-white border-[#27272A] hover:bg-[#3f3f46]">
              Нет, оставить
            </AlertDialogCancel>
            <AlertDialogAction 
              onClick={executeCancelDeal}
              disabled={processing}
              className="bg-red-600 hover:bg-red-700 text-white"
            >
              {processing ? 'Отмена...' : 'Да, отменить'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

// Leasing Calculator Dialog Component
const LeasingDialog = ({ open, onClose, leasingData, leasingCompanies, onSubmit, processing }) => {
  const [term, setTerm] = useState(36);
  const [downPayment, setDownPayment] = useState(20);
  const [selectedCompanies, setSelectedCompanies] = useState([]);

  const carPrice = leasingData?.carPrice || 0;
  const loanAmount = carPrice * (1 - downPayment / 100);

  // Calculate monthly payment (simplified formula)
  const calculateMonthlyPayment = (company) => {
    const rate = company?.service_prices?.leasing_rate || 12; // Annual rate %
    const monthlyRate = rate / 100 / 12;
    const payment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, term)) / (Math.pow(1 + monthlyRate, term) - 1);
    return Math.round(payment);
  };

  const toggleCompany = (companyId) => {
    setSelectedCompanies(prev =>
      prev.includes(companyId)
        ? prev.filter(id => id !== companyId)
        : [...prev, companyId]
    );
  };

  const handleSubmit = () => {
    if (selectedCompanies.length === 0) {
      toast.error('Выберите хотя бы одну лизинговую компанию');
      return;
    }
    onSubmit(leasingData.dealId, {
      term,
      down_payment_percent: downPayment,
      loan_amount: loanAmount,
      selected_companies: selectedCompanies
    });
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator size={20} className="text-[#00E5FF]" />
            Калькулятор лизинга
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Car Price */}
          <div className="p-4 bg-[#0B0F14] rounded-sm">
            <p className="text-slate-400 text-sm">Стоимость автомобиля</p>
            <p className="text-[#00E5FF] text-2xl font-bold">${carPrice.toLocaleString()}</p>
          </div>

          {/* Term Selection */}
          <div>
            <Label className="text-white mb-2 block">Срок лизинга (месяцев)</Label>
            <div className="flex gap-2">
              {LEASING_TERMS.map(t => (
                <Button
                  key={t}
                  variant={term === t ? "default" : "outline"}
                  onClick={() => setTerm(t)}
                  className={term === t 
                    ? "bg-[#00E5FF] text-black hover:bg-[#22D3EE]" 
                    : "border-[#27272A] text-slate-400 hover:text-white"}
                >
                  {t}
                </Button>
              ))}
            </div>
          </div>

          {/* Down Payment */}
          <div>
            <div className="flex justify-between mb-2">
              <Label className="text-white">Первоначальный взнос</Label>
              <span className="text-[#00E5FF] font-bold">{downPayment}%</span>
            </div>
            <Slider
              value={[downPayment]}
              onValueChange={(v) => setDownPayment(v[0])}
              min={10}
              max={50}
              step={5}
              className="w-full"
            />
            <div className="flex justify-between text-slate-500 text-xs mt-1">
              <span>10%</span>
              <span>${Math.round(carPrice * downPayment / 100).toLocaleString()}</span>
              <span>50%</span>
            </div>
          </div>

          {/* Loan Amount */}
          <div className="p-4 bg-[#0B0F14] rounded-sm">
            <p className="text-slate-400 text-sm">Сумма кредита</p>
            <p className="text-white text-xl font-bold">${Math.round(loanAmount).toLocaleString()}</p>
          </div>

          {/* Leasing Companies */}
          <div>
            <Label className="text-white mb-3 block">Выберите лизинговые компании</Label>
            {leasingCompanies.length === 0 ? (
              <p className="text-slate-500 text-sm">Нет доступных лизинговых компаний</p>
            ) : (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {leasingCompanies.map(company => {
                  const monthlyPayment = calculateMonthlyPayment(company);
                  const isSelected = selectedCompanies.includes(company.id);
                  const rate = company?.service_prices?.leasing_rate || 12;

                  return (
                    <div
                      key={company.id}
                      onClick={() => toggleCompany(company.id)}
                      className={`p-4 rounded-sm border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                          : 'border-[#27272A] bg-[#0B0F14] hover:border-[#00E5FF]/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <Checkbox checked={isSelected} />
                          <div>
                            <p className="text-white font-medium">{company.name}</p>
                            <p className="text-slate-400 text-sm">Ставка: {rate}% годовых</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-[#00E5FF] font-bold">${monthlyPayment}/мес</p>
                          <p className="text-slate-500 text-xs">~${monthlyPayment * term} всего</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 border-slate-500"
            >
              Отмена
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={processing || selectedCompanies.length === 0}
              className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {processing ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              Отправить заявки ({selectedCompanies.length})
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Contractor Selection Dialog
const ContractorDialog = ({ open, onClose, dialogData, contractors, onSelect, processing }) => {
  if (!dialogData) return null;

  const stage = dialogData.stage;
  const stageInfo = STAGES.find(s => s.key === stage);

  // Map stage key to service type
  const getServiceType = (stageKey) => {
    const mapping = {
      'inspection': 'inspection',
      'export': 'export',
      'logistics_china': 'logistics',
      'insurance': 'insurance',
      'delivery_rb': 'logistics',
      'customs': 'customs'
    };
    return mapping[stageKey] || stageKey;
  };

  const serviceType = getServiceType(stage);

  // Filter contractors by service
  const filteredContractors = contractors.filter(c => {
    const services = c.services?.toLowerCase() || '';
    if (stage === 'insurance') {
      return services.includes('insurance') || services.includes('страхов');
    }
    if (stage === 'logistics_china') {
      return services.includes('logistics_china') || services.includes('логистик') || services.includes('доставка');
    }
    if (stage === 'delivery_rb') {
      return services.includes('delivery_rb') || services.includes('доставка') || services.includes('logistics');
    }
    if (stage === 'customs') {
      return services.includes('customs') || services.includes('таможен') || services.includes('растамож');
    }
    if (stage === 'inspection') {
      return services.includes('inspection') || services.includes('осмотр') || services.includes('проверк');
    }
    if (stage === 'export') {
      return services.includes('export') || services.includes('экспорт') || services.includes('вывоз');
    }
    return services.includes(serviceType);
  });

  // Get price for this service
  const getContractorPrice = (contractor) => {
    const prices = contractor.service_prices;
    if (!prices) return null;
    
    // Check for specific stage price first
    if (prices[stage]) return prices[stage];
    
    // Check for service type price
    if (prices[serviceType]) return prices[serviceType];
    
    // Fallbacks for logistics stages
    if (stage === 'delivery_rb') {
      return prices.delivery_rb || prices.logistics || null;
    }
    if (stage === 'logistics_china') {
      return prices.logistics_china || prices.logistics || null;
    }
    
    return null;
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Выбор подрядчика</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          <p className="text-slate-400 text-sm">
            Этап: {stageInfo?.label}
          </p>
          
          {filteredContractors.length === 0 ? (
            <p className="text-slate-500 text-center py-8">
              Нет доступных подрядчиков для этого этапа
            </p>
          ) : (
            filteredContractors.map(contractor => {
              const price = getContractorPrice(contractor);
              if (!price) return null;

              return (
                <div
                  key={contractor.id}
                  className="p-4 bg-[#0B0F14] rounded-sm border border-[#27272A] hover:border-[#00E5FF]/50 cursor-pointer"
                  onClick={() => onSelect(dialogData.dealId, stage, contractor.id, price)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-white font-medium">{contractor.name}</p>
                      <p className="text-slate-400 text-sm line-clamp-1">{contractor.description}</p>
                      {contractor.rating && (
                        <p className="text-amber-400 text-xs mt-1">
                          ★ {contractor.rating.toFixed(1)} • {contractor.deals_count || 0} сделок
                        </p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-[#00E5FF] font-bold text-lg">${price}</p>
                      <p className="text-slate-500 text-xs">за услугу</p>
                    </div>
                  </div>
                </div>
              );
            })
          )}
          
          {processing && <Loader2 className="animate-spin mx-auto" />}
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Invoice Dialog
const InvoiceDialog = ({ open, onClose, invoiceData, balance, onPay, processing }) => {
  const [paymentMethod, setPaymentMethod] = useState('platform');

  if (!invoiceData) return null;

  const { dealId, stage, invoice } = invoiceData;
  const stageInfo = STAGES.find(s => s.key === stage);

  const servicePrice = invoice?.service_price || 0;
  const carPrice = invoice?.car_price || 0;
  const platformCommission = (servicePrice + carPrice) * PLATFORM_COMMISSION;
  const platformFee = paymentMethod === 'platform' ? (servicePrice + carPrice) * PLATFORM_PAYMENT_FEE : 0;
  const totalAmount = servicePrice + carPrice + platformCommission + platformFee;

  const canPayThroughPlatform = balance >= totalAmount;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <FileText size={20} className="text-[#00E5FF]" />
            Счёт на оплату
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          <div className="p-3 bg-[#0B0F14] rounded-sm">
            <p className="text-slate-400 text-sm">Этап</p>
            <p className="text-white font-medium">{stageInfo?.label}</p>
          </div>

          {/* Invoice breakdown */}
          <div className="space-y-2 p-4 bg-[#0B0F14] rounded-sm">
            {carPrice > 0 && (
              <div className="flex justify-between">
                <span className="text-slate-400">Базовая стоимость авто в Китае</span>
                <span className="text-white">${carPrice.toLocaleString()}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-slate-400">Стоимость услуги</span>
              <span className="text-white">${servicePrice.toLocaleString()}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Комиссия платформы (3%)</span>
              <span className="text-white">${platformCommission.toFixed(2)}</span>
            </div>
            {paymentMethod === 'platform' && (
              <div className="flex justify-between text-amber-400">
                <span>Комиссия за оплату (+1%)</span>
                <span>${platformFee.toFixed(2)}</span>
              </div>
            )}
            <div className="border-t border-[#27272A] pt-2 mt-2">
              <div className="flex justify-between">
                <span className="text-white font-bold">Итого</span>
                <span className="text-[#00E5FF] font-bold text-xl">${totalAmount.toFixed(2)}</span>
              </div>
            </div>
          </div>

          {/* Payment Method Selection */}
          <div className="space-y-3">
            <Label className="text-white">Способ оплаты</Label>
            
            <div
              onClick={() => setPaymentMethod('self')}
              className={`p-4 rounded-sm border cursor-pointer ${
                paymentMethod === 'self'
                  ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                  : 'border-[#27272A] bg-[#0B0F14]'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-4 h-4 rounded-full border-2 ${
                  paymentMethod === 'self' ? 'border-[#00E5FF] bg-[#00E5FF]' : 'border-slate-500'
                }`} />
                <div>
                  <p className="text-white font-medium">Самостоятельно</p>
                  <p className="text-slate-400 text-sm">Без дополнительной комиссии</p>
                </div>
              </div>
            </div>

            <div
              onClick={() => setPaymentMethod('platform')}
              className={`p-4 rounded-sm border cursor-pointer ${
                paymentMethod === 'platform'
                  ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                  : 'border-[#27272A] bg-[#0B0F14]'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className={`w-4 h-4 rounded-full border-2 ${
                  paymentMethod === 'platform' ? 'border-[#00E5FF] bg-[#00E5FF]' : 'border-slate-500'
                }`} />
                <div className="flex-1">
                  <p className="text-white font-medium">Через платформу</p>
                  <p className="text-slate-400 text-sm">+1% комиссия, списание с баланса</p>
                </div>
                <div className="text-right">
                  <p className={`text-sm ${canPayThroughPlatform ? 'text-emerald-400' : 'text-red-400'}`}>
                    Баланс: ${balance.toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Warning if not enough balance */}
          {paymentMethod === 'platform' && !canPayThroughPlatform && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-sm">
              <p className="text-red-400 text-sm">
                Недостаточно средств. Необходимо: ${totalAmount.toFixed(2)}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 border-slate-500"
            >
              Отмена
            </Button>
            <Button
              onClick={() => onPay(dealId, stage, totalAmount, paymentMethod === 'platform')}
              disabled={processing || (paymentMethod === 'platform' && !canPayThroughPlatform)}
              className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
            >
              {processing ? <Loader2 className="animate-spin mr-2" size={16} /> : <DollarSign size={16} className="mr-2" />}
              {paymentMethod === 'platform' ? 'Оплатить' : 'Отметить оплаченным'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Customs Calculator Dialog - Uses same API as main calculator
const CustomsDialog = ({ open, onClose, customsData, contractors, onSelectContractor, processing }) => {
  const [userType, setUserType] = useState('individual');
  const [engineType, setEngineType] = useState('ice');
  const [engineVolume, setEngineVolume] = useState('2000');
  const [age, setAge] = useState('under3');
  const [useDecree140, setUseDecree140] = useState(false);
  const [selectedBroker, setSelectedBroker] = useState(null);
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);

  const dealId = customsData?.dealId;
  const carInfo = customsData?.carInfo;
  const priceCny = carInfo?.price_cny || 180000;

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ru-RU', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    }).format(num);
  };

  // Call calculator API
  const handleCalculate = async () => {
    if (!priceCny) return;
    setCalcLoading(true);
    try {
      const response = await axios.post(`${API}/calculator`, {
        price_cny: priceCny,
        age: age,
        engine_type: engineType,
        engine_volume: engineType !== 'electric' ? parseInt(engineVolume) : null,
        user_type: userType,
        use_decree_140: useDecree140,
        payment_via_platform: true
      });
      setCalcResult(response.data);
    } catch (error) {
      console.error('Calculation error:', error);
      toast.error('Ошибка расчёта');
    } finally {
      setCalcLoading(false);
    }
  };

  // Auto-calculate on mount and param changes
  useEffect(() => {
    if (open && priceCny) {
      handleCalculate();
    }
  }, [open, priceCny, age, engineType, engineVolume, userType, useDecree140]);

  // Filter customs brokers
  const customsBrokers = contractors.filter(c => {
    const services = c.services?.toLowerCase() || '';
    return services.includes('customs') || services.includes('таможн');
  });

  const getBrokerPrice = (broker) => {
    return broker.service_prices?.customs || 300;
  };

  // Calculate total customs payments in USD
  const getCustomsPaymentsUsd = () => {
    if (!calcResult) return 0;
    const totalByn = calcResult.customs_duty + 
                     calcResult.utilization_fee + 
                     (calcResult.vat || 0) + 
                     120 + 70;
    return Math.round(totalByn / 3.2); // Convert BYN to USD
  };

  const handleSelectBroker = () => {
    if (!selectedBroker) {
      toast.error('Выберите таможенного брокера');
      return;
    }
    const broker = customsBrokers.find(b => b.id === selectedBroker);
    const brokerPrice = getBrokerPrice(broker);
    const customsPaymentsUsd = getCustomsPaymentsUsd();
    const totalPrice = customsPaymentsUsd + brokerPrice; // Total: customs payments + broker fee
    
    onSelectContractor(dealId, 'customs', selectedBroker, totalPrice);
    onClose();
  };

  if (!customsData) return null;

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator size={20} className="text-[#00E5FF]" />
            Калькулятор растаможки
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-5 mt-4">
          {/* Car Info */}
          <div className="p-4 bg-[#0B0F14] rounded-sm">
            <p className="text-slate-400 text-sm">Автомобиль</p>
            <p className="text-white font-medium">{carInfo?.brand} {carInfo?.model} {carInfo?.year}</p>
            <p className="text-[#00E5FF]">¥{priceCny.toLocaleString()} CNY</p>
          </div>

          {/* User Type */}
          <div>
            <Label className="text-slate-300 mb-2 block">Тип лица</Label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { value: 'individual', label: 'Физ. лицо' },
                { value: 'legal', label: 'Юр. лицо' }
              ].map(type => (
                <button
                  key={type.value}
                  onClick={() => setUserType(type.value)}
                  className={`py-3 px-4 rounded-sm border text-sm font-medium transition-colors ${
                    userType === type.value
                      ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                      : 'bg-[#0B0F14] text-slate-400 border-[#27272A] hover:border-slate-500'
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Engine Type */}
          <div>
            <Label className="text-slate-300 mb-2 block">Тип двигателя</Label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'ice', label: 'ДВС' },
                { value: 'hybrid', label: 'Гибрид' },
                { value: 'electric', label: 'Электро' }
              ].map(type => (
                <button
                  key={type.value}
                  onClick={() => setEngineType(type.value)}
                  className={`py-3 px-4 rounded-sm border text-sm font-medium transition-colors ${
                    engineType === type.value
                      ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                      : 'bg-[#0B0F14] text-slate-400 border-[#27272A] hover:border-slate-500'
                  }`}
                >
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Age */}
          <div>
            <Label className="text-slate-300 mb-2 block">Возраст авто</Label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: 'under3', label: 'До 3 лет' },
                { value: '3to5', label: '3-5 лет' },
                { value: 'over5', label: '5+ лет' }
              ].map(a => (
                <button
                  key={a.value}
                  onClick={() => setAge(a.value)}
                  className={`py-3 px-4 rounded-sm border text-sm font-medium transition-colors ${
                    age === a.value
                      ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                      : 'bg-[#0B0F14] text-slate-400 border-[#27272A] hover:border-slate-500'
                  }`}
                >
                  {a.label}
                </button>
              ))}
            </div>
          </div>

          {/* Engine Volume (for ICE and Hybrid) */}
          {engineType !== 'electric' && (
            <div>
              <Label className="text-slate-300 mb-2 block">Объём двигателя (см³)</Label>
              <Input
                type="number"
                value={engineVolume}
                onChange={(e) => setEngineVolume(e.target.value)}
                placeholder="Введите объем"
                className="bg-[#0B0F14] border-[#27272A] text-white"
              />
            </div>
          )}

          {/* Decree 140 - Only for individuals */}
          {userType === 'individual' && (
            <div
              onClick={() => setUseDecree140(!useDecree140)}
              className={`p-4 rounded-sm border cursor-pointer ${
                useDecree140 ? 'border-emerald-500 bg-emerald-500/10' : 'border-[#27272A] bg-[#0B0F14]'
              }`}
            >
              <div className="flex items-center gap-3">
                <Checkbox checked={useDecree140} />
                <div>
                  <p className="text-white font-medium">Льгота по Указу №140</p>
                  <p className="text-slate-400 text-sm">50% скидка на пошлины для многодетных семей, инвалидов I-II гр.</p>
                </div>
              </div>
            </div>
          )}

          {/* Results */}
          {calcLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-[#00E5FF]" size={32} />
            </div>
          ) : calcResult && (
            <div className="space-y-4">
              {/* Customs Payments Only */}
              <div className="bg-[#0B0F14] border border-[#27272A] rounded-sm p-4 space-y-3">
                <h4 className="text-white font-semibold mb-3">Таможенные платежи</h4>
                
                <div className="flex justify-between text-sm py-2 border-b border-[#27272A]">
                  <span className="text-slate-400">Таможенная пошлина</span>
                  <span className="text-white">{formatNumber(calcResult.customs_duty)} BYN</span>
                </div>
                
                <div className="flex justify-between text-sm py-2 border-b border-[#27272A]">
                  <span className="text-slate-400">Утилизационный сбор</span>
                  <span className="text-white">{formatNumber(calcResult.utilization_fee)} BYN</span>
                </div>
                
                {calcResult.vat > 0 && (
                  <div className="flex justify-between text-sm py-2 border-b border-[#27272A]">
                    <span className="text-slate-400">НДС (20%)</span>
                    <span className="text-white">{formatNumber(calcResult.vat)} BYN</span>
                  </div>
                )}
                
                <div className="flex justify-between text-sm py-2 border-b border-[#27272A]">
                  <span className="text-slate-400">Таможенный сбор</span>
                  <span className="text-white">120,00 BYN</span>
                </div>
                
                <div className="flex justify-between text-sm py-2 border-b border-[#27272A]">
                  <span className="text-slate-400">ЭПТС</span>
                  <span className="text-white">70,00 BYN</span>
                </div>

                {/* Show discount info if applied - discount is already included in customs_duty */}
                {calcResult.decree_140_discount > 0 && (
                  <div className="flex justify-between text-sm py-2 border-b border-[#27272A] text-emerald-400">
                    <span>Льгота по Указу №140 (применена)</span>
                    <span>-{formatNumber(calcResult.decree_140_discount)} BYN</span>
                  </div>
                )}

                {/* Subtotal customs payments - customs_duty already includes discount */}
                <div className="flex justify-between pt-2">
                  <span className="text-white font-semibold">Итого таможенные платежи</span>
                  <span className="text-[#00E5FF] font-bold text-lg">
                    {formatNumber(
                      calcResult.customs_duty + 
                      calcResult.utilization_fee + 
                      (calcResult.vat || 0) + 
                      120 + 70
                    )} BYN
                  </span>
                </div>
              </div>

              {/* Discount Badge */}
              {calcResult.decree_140_discount > 0 && (
                <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-sm p-3 flex items-center gap-3">
                  <BadgeCheck size={20} className="text-emerald-400" />
                  <div>
                    <p className="text-emerald-400 font-medium text-sm">Льгота по Указу 140 применена</p>
                    <p className="text-slate-400 text-xs">
                      Экономия: {formatNumber(calcResult.decree_140_discount)} BYN (50% от пошлины)
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Select Broker */}
          <div>
            <Label className="text-white mb-3 block">Выберите таможенного брокера</Label>
            {customsBrokers.length === 0 ? (
              <p className="text-slate-500 text-sm">Нет доступных таможенных брокеров</p>
            ) : (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {customsBrokers.map(broker => {
                  const price = getBrokerPrice(broker);
                  const isSelected = selectedBroker === broker.id;

                  return (
                    <div
                      key={broker.id}
                      onClick={() => setSelectedBroker(broker.id)}
                      className={`p-4 rounded-sm border cursor-pointer ${
                        isSelected
                          ? 'border-[#00E5FF] bg-[#00E5FF]/10'
                          : 'border-[#27272A] bg-[#0B0F14] hover:border-[#00E5FF]/50'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-white font-medium">{broker.name}</p>
                          {broker.rating && (
                            <p className="text-amber-400 text-xs">★ {broker.rating.toFixed(1)}</p>
                          )}
                        </div>
                        <div className="text-right">
                          <p className="text-[#00E5FF] font-bold">${price}</p>
                          <p className="text-slate-500 text-xs">услуга брокера</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Total to pay with broker selected */}
          {selectedBroker && calcResult && (
            <div className="bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded-sm p-4">
              <p className="text-slate-400 text-sm mb-2">К оплате (таможенные платежи + услуга брокера)</p>
              <div className="flex justify-between items-center">
                <div>
                  <p className="text-[#00E5FF] text-2xl font-bold">
                    {formatNumber(
                      calcResult.customs_duty + 
                      calcResult.utilization_fee + 
                      (calcResult.vat || 0) + 
                      120 + 70 +
                      getBrokerPrice(customsBrokers.find(b => b.id === selectedBroker)) * 3.2
                    )} BYN
                  </p>
                  <p className="text-slate-400 text-sm">
                    ≈ ${formatNumber(
                      (calcResult.customs_duty + 
                       calcResult.utilization_fee + 
                       (calcResult.vat || 0) + 
                       120 + 70) / 3.2 +
                      getBrokerPrice(customsBrokers.find(b => b.id === selectedBroker))
                    )} USD
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 border-slate-500"
            >
              Отмена
            </Button>
            <Button
              onClick={handleSelectBroker}
              disabled={processing || !selectedBroker}
              className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {processing ? <Loader2 className="animate-spin mr-2" size={16} /> : null}
              Выбрать брокера и оплатить
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

// Deal Card Component
const DealCard = ({ 
  deal, 
  balance, 
  contractors, 
  leasingCompanies,
  onOpenLeasing, 
  onOpenContractor, 
  onOpenInvoice,
  onSkipStage,
  onOpenCustoms,
  onCompleteDeal,
  onCancelDeal
}) => {
  const getStageStatus = (stageKey) => {
    const stage = deal.stages?.[stageKey];
    if (!stage) return 'pending';
    if (stage.completed) return 'completed';
    if (stage.paid) return 'paid';
    if (stage.invoice_created) return 'invoice';
    // Locked stage with contractor from tender offer
    if (stage.locked && stage.contractor_id) return 'contractor_assigned';
    // Only mark as contractor_selected if both contractor_id AND price are set
    if (stage.contractor_id && stage.price > 0) return 'contractor_selected';
    if (stage.skipped) return 'skipped';
    if (stage.requested) return 'requested';
    return 'pending';
  };

  const isCurrentStage = (stageKey) => deal.current_stage === stageKey;

  const canComplete = () => {
    // Check if export is done (minimum required)
    const exportStatus = getStageStatus('export');
    return exportStatus === 'completed' || exportStatus === 'paid';
  };

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
            <p className="text-slate-400 text-sm">
              {deal.car_info?.year} • ${deal.car_info?.price_usd?.toLocaleString()}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {/* Total Paid Badge */}
          <div className="text-right">
            <p className="text-slate-500 text-xs">Оплачено</p>
            <p className="text-emerald-400 font-bold">${(deal.total_paid || 0).toLocaleString()}</p>
          </div>
          <span className="px-3 py-1 bg-[#00E5FF]/10 text-[#00E5FF] rounded-full text-sm">
            Активна
          </span>
          {/* Cancel Deal Button - only if no payments made */}
          {(deal.total_paid || 0) === 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => onCancelDeal(deal.id)}
              className="border-red-500/30 text-red-400 hover:bg-red-500/10"
              title="Отменить сделку"
            >
              <Trash2 size={16} />
            </Button>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="p-4 bg-[#0B0F14]">
        <div className="flex items-center justify-between mb-2">
          <p className="text-slate-400 text-xs">Прогресс сделки</p>
          <p className="text-white text-xs font-medium">
            {STAGES.filter(s => ['completed', 'skipped', 'paid'].includes(getStageStatus(s.key))).length} / {STAGES.length} этапов
          </p>
        </div>
        <div className="flex gap-1">
          {STAGES.map((stage) => {
            const status = getStageStatus(stage.key);
            return (
              <div
                key={stage.key}
                className={`flex-1 h-2 rounded-full ${
                  status === 'completed' || status === 'paid' ? 'bg-emerald-500' :
                  status === 'invoice' ? 'bg-blue-500' :
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
      <div className="p-4 space-y-3">
        {STAGES.map((stage) => {
          const status = getStageStatus(stage.key);
          const stageData = deal.stages?.[stage.key];
          const Icon = stage.icon;
          const isCurrent = isCurrentStage(stage.key);
          const isLocked = stageData?.locked;
          const moderatorConfirmed = stageData?.moderator_confirmed;

          return (
            <div
              key={stage.key}
              className={`p-4 rounded-sm border ${
                isCurrent ? 'border-[#00E5FF] bg-[#00E5FF]/5' :
                status === 'completed' || status === 'paid' ? 'border-emerald-500/30 bg-emerald-500/5' :
                status === 'skipped' ? 'border-slate-600/30 bg-slate-800/20' :
                isLocked ? 'border-purple-500/30 bg-purple-500/5' :
                'border-[#27272A] bg-[#0B0F14]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    status === 'completed' || status === 'paid' ? 'bg-emerald-500/20' :
                    status === 'skipped' ? 'bg-slate-600/20' :
                    isCurrent ? 'bg-[#00E5FF]/20' :
                    isLocked ? 'bg-purple-500/20' :
                    'bg-[#27272A]'
                  }`}>
                    {status === 'completed' || status === 'paid' ? (
                      <CheckCircle2 size={20} className="text-emerald-400" />
                    ) : status === 'skipped' ? (
                      <SkipForward size={20} className="text-slate-500" />
                    ) : (
                      <Icon size={20} className={isCurrent ? 'text-[#00E5FF]' : isLocked ? 'text-purple-400' : 'text-slate-500'} />
                    )}
                  </div>
                  <div>
                    <p className={`font-medium ${
                      status === 'completed' || status === 'paid' ? 'text-emerald-400' :
                      status === 'skipped' ? 'text-slate-500' :
                      isCurrent ? 'text-white' :
                      isLocked ? 'text-purple-300' :
                      'text-slate-400'
                    }`}>
                      {stage.label}
                      {stage.optional && !isLocked && <span className="text-slate-500 text-xs ml-2">(можно пропустить)</span>}
                      {isLocked && <span className="text-purple-400 text-xs ml-2">(из предложения)</span>}
                    </p>
                    
                    {/* Stage status info */}
                    {isLocked && stageData?.contractor_name && (
                      <div className="flex items-center gap-2 text-sm">
                        <Building2 size={14} className="text-purple-400" />
                        <span className="text-purple-300">{stageData.contractor_name}</span>
                        {stageData.price && (
                          <span className="text-slate-400">• ${stageData.price}</span>
                        )}
                      </div>
                    )}
                    {status === 'contractor_assigned' && stageData?.contractor_name && (
                      <p className="text-purple-400 text-sm">
                        {stageData.contractor_name} • ${stageData.price || 'цена не указана'}
                        <span className="text-purple-300 text-xs ml-2">— готово к оплате</span>
                      </p>
                    )}
                    {status === 'contractor_selected' && stageData?.price && !isLocked && (
                      <p className="text-amber-400 text-sm">Подрядчик выбран • ${stageData.price}</p>
                    )}
                    {status === 'invoice' && (
                      <p className="text-blue-400 text-sm">Счёт сформирован</p>
                    )}
                    {status === 'paid' && (
                      <p className="text-emerald-400 text-sm">Оплачено</p>
                    )}
                    {status === 'requested' && (
                      <p className="text-amber-400 text-sm">Заявка отправлена</p>
                    )}
                    {status === 'skipped' && (
                      <p className="text-slate-500 text-sm">Пропущен</p>
                    )}
                    
                    {/* Moderator confirmation status */}
                    {isLocked && status !== 'paid' && status !== 'completed' && (
                      <div className="flex items-center gap-1 mt-1">
                        {moderatorConfirmed ? (
                          <span className="flex items-center gap-1 text-emerald-400 text-xs">
                            <BadgeCheck size={12} />
                            Подтверждён модератором
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-amber-400 text-xs">
                            <Clock size={12} />
                            Ожидает проверки модератора
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Stage Actions */}
                {/* Allow selecting contractor for pending stages (not just current) */}
                {status === 'pending' && !isLocked && (
                  <div className="flex gap-2">
                    {/* Leasing stage */}
                    {stage.key === 'leasing' && (
                      <>
                        {stage.optional && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onSkipStage(deal.id, stage.key)}
                            className="border-slate-500 text-slate-400"
                          >
                            Пропустить
                          </Button>
                        )}
                        <Button
                          size="sm"
                          onClick={() => onOpenLeasing(deal.id)}
                          className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                        >
                          <Calculator size={16} className="mr-1" />
                          Калькулятор
                        </Button>
                      </>
                    )}

                    {/* Contractor selection stages (except customs) */}
                    {['inspection', 'export', 'logistics_china', 'insurance', 'delivery_rb'].includes(stage.key) && (
                      <>
                        {stage.optional && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => onSkipStage(deal.id, stage.key)}
                            className="border-slate-500 text-slate-400"
                          >
                            Пропустить
                          </Button>
                        )}
                        <Button
                          size="sm"
                          onClick={() => onOpenContractor(deal.id, stage.key)}
                          className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                        >
                          Выбрать подрядчика
                        </Button>
                      </>
                    )}

                    {/* Customs stage with calculator */}
                    {stage.key === 'customs' && (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => onSkipStage(deal.id, stage.key)}
                          className="border-slate-500 text-slate-400"
                        >
                          Пропустить
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => onOpenCustoms(deal.id, deal.car_info)}
                          className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                        >
                          <Calculator size={16} className="mr-1" />
                          Рассчитать платежи
                        </Button>
                      </>
                    )}

                    {/* Completion stage */}
                    {stage.key === 'completion' && (
                      <Button
                        size="sm"
                        onClick={() => onCompleteDeal(deal.id)}
                        disabled={!canComplete()}
                        className="bg-emerald-500 hover:bg-emerald-600 text-white"
                      >
                        <CheckCheck size={16} className="mr-1" />
                        Завершить сделку
                      </Button>
                    )}
                  </div>
                )}

                {/* Actions for LOCKED stages from tender offer */}
                {isLocked && status !== 'paid' && status !== 'completed' && status !== 'skipped' && (
                  <div className="flex gap-2 items-center">
                    {moderatorConfirmed ? (
                      <Button
                        size="sm"
                        onClick={() => onOpenInvoice(deal.id, stage.key, {
                          service_price: stageData?.price || 0,
                          car_price: stage.key === 'export' ? Math.round((deal.car_info?.price_cny || 0) / 7.2) : 0
                        })}
                        className="bg-emerald-500 hover:bg-emerald-600 text-white"
                      >
                        <DollarSign size={16} className="mr-1" />
                        Оплатить этап
                      </Button>
                    ) : (
                      <span className="text-amber-400 text-sm flex items-center gap-1">
                        <AlertCircle size={14} />
                        Ожидает модерации
                      </span>
                    )}
                  </div>
                )}

                {/* Show invoice button if contractor selected (not locked) */}
                {!isLocked && status === 'contractor_selected' && stageData?.price && (
                  <Button
                    size="sm"
                    onClick={() => onOpenInvoice(deal.id, stage.key, {
                      service_price: stageData.price,
                      // For export stage: use base price in China (CNY converted to USD)
                      car_price: stage.key === 'export' ? Math.round((deal.car_info?.price_cny || 0) / 7.2) : 0
                    })}
                    className="bg-blue-500 hover:bg-blue-600 text-white"
                  >
                    <FileText size={16} className="mr-1" />
                    Оплатить
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default DealCars;
