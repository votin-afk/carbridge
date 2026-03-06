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
  SkipForward
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
  { key: 'inspection', label: 'Проверка', icon: Search, optional: true },
  { key: 'export', label: 'Экспорт', icon: FileCheck, optional: false, hasInvoice: true },
  { key: 'logistics_china', label: 'Логистика до порта', icon: Truck, optional: true },
  { key: 'insurance', label: 'Страхование', icon: Shield, optional: true },
  { key: 'delivery_rb', label: 'Доставка в РБ', icon: Ship, optional: true },
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
    return services.includes(serviceType);
  });

  // Get price for this service
  const getContractorPrice = (contractor) => {
    const prices = contractor.service_prices;
    if (!prices) return null;
    
    // Check for specific service price
    if (prices[serviceType]) return prices[serviceType];
    
    // Fallbacks
    if (stage === 'delivery_rb' && prices.logistics) return prices.logistics;
    if (stage === 'logistics_china' && prices.logistics) return prices.logistics;
    
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
                <span className="text-slate-400">Стоимость авто</span>
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

// Customs Calculator Dialog
const CustomsDialog = ({ open, onClose, customsData, contractors, onSelectContractor, processing }) => {
  const [engineVolume, setEngineVolume] = useState(2000);
  const [isElectric, setIsElectric] = useState(false);
  const [useDecree140, setUseDecree140] = useState(false);
  const [selectedBroker, setSelectedBroker] = useState(null);

  if (!customsData) return null;

  const { dealId, carInfo } = customsData;
  const carPrice = carInfo?.price_usd || 0;
  const carYear = carInfo?.year || new Date().getFullYear();
  const carAge = new Date().getFullYear() - carYear;

  // EUR/USD rate (approximate)
  const EUR_USD = 1.08;
  const carPriceEur = carPrice / EUR_USD;

  // Calculate customs payments for Belarus
  const calculateCustomsPayments = () => {
    // 1. Утилизационный сбор (Utilization fee)
    let utilizationFee = 0;
    if (isElectric) {
      utilizationFee = carAge <= 3 ? 3400 : 5200; // BYN base for electric
    } else {
      if (engineVolume <= 1000) {
        utilizationFee = carAge <= 3 ? 544 : 1088;
      } else if (engineVolume <= 2000) {
        utilizationFee = carAge <= 3 ? 870 : 2610;
      } else if (engineVolume <= 3000) {
        utilizationFee = carAge <= 3 ? 1305 : 5655;
      } else if (engineVolume <= 3500) {
        utilizationFee = carAge <= 3 ? 2175 : 9353;
      } else {
        utilizationFee = carAge <= 3 ? 3480 : 14964;
      }
    }
    // Convert BYN to USD (approx rate 3.2)
    const utilizationFeeUsd = Math.round(utilizationFee / 3.2);

    // 2. Таможенная пошлина (Customs duty) - based on engine volume and age
    let customsDuty = 0;
    if (isElectric) {
      customsDuty = carPriceEur * 0.15; // 15% for electric
    } else if (carAge <= 3) {
      // New cars - percentage of price
      if (carPriceEur < 8500) customsDuty = Math.max(carPriceEur * 0.54, engineVolume * 2.5);
      else if (carPriceEur < 16700) customsDuty = Math.max(carPriceEur * 0.48, engineVolume * 3.5);
      else if (carPriceEur < 42300) customsDuty = Math.max(carPriceEur * 0.48, engineVolume * 5.5);
      else if (carPriceEur < 84500) customsDuty = Math.max(carPriceEur * 0.48, engineVolume * 7.5);
      else if (carPriceEur < 169000) customsDuty = Math.max(carPriceEur * 0.48, engineVolume * 15);
      else customsDuty = Math.max(carPriceEur * 0.48, engineVolume * 20);
    } else if (carAge <= 5) {
      // 3-5 years old
      if (engineVolume <= 1000) customsDuty = engineVolume * 1.5;
      else if (engineVolume <= 1500) customsDuty = engineVolume * 1.7;
      else if (engineVolume <= 1800) customsDuty = engineVolume * 2.5;
      else if (engineVolume <= 2300) customsDuty = engineVolume * 2.7;
      else if (engineVolume <= 3000) customsDuty = engineVolume * 3.0;
      else customsDuty = engineVolume * 3.6;
    } else {
      // Over 5 years
      if (engineVolume <= 1000) customsDuty = engineVolume * 3.0;
      else if (engineVolume <= 1500) customsDuty = engineVolume * 3.2;
      else if (engineVolume <= 1800) customsDuty = engineVolume * 3.5;
      else if (engineVolume <= 2300) customsDuty = engineVolume * 4.8;
      else if (engineVolume <= 3000) customsDuty = engineVolume * 5.0;
      else customsDuty = engineVolume * 5.7;
    }
    const customsDutyUsd = Math.round(customsDuty * EUR_USD);

    // 3. Таможенный сбор (Customs fee) - fixed
    const customsFee = 120; // USD

    // 4. ЭПТС (Electronic vehicle passport)
    const eptsСost = 45; // USD

    // 5. Apply Decree 140 discount (50% on customs duty for certain categories)
    let decree140Discount = 0;
    if (useDecree140) {
      decree140Discount = customsDutyUsd * 0.5;
    }

    const totalPayments = utilizationFeeUsd + customsDutyUsd + customsFee + eptsСost - decree140Discount;

    return {
      utilizationFee: utilizationFeeUsd,
      customsDuty: customsDutyUsd,
      customsFee,
      eptsCost: eptsСost,
      decree140Discount,
      total: totalPayments
    };
  };

  const payments = calculateCustomsPayments();

  // Filter customs brokers
  const customsBrokers = contractors.filter(c => {
    const services = c.services?.toLowerCase() || '';
    return services.includes('customs') || services.includes('таможн');
  });

  const getBrokerPrice = (broker) => {
    return broker.service_prices?.customs || 300;
  };

  const handleSelectBroker = () => {
    if (!selectedBroker) {
      toast.error('Выберите таможенного брокера');
      return;
    }
    const broker = customsBrokers.find(b => b.id === selectedBroker);
    const brokerPrice = getBrokerPrice(broker);
    onSelectContractor(dealId, 'customs', selectedBroker, brokerPrice);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Calculator size={20} className="text-[#00E5FF]" />
            Таможенные платежи
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-6 mt-4">
          {/* Car Info */}
          <div className="p-4 bg-[#0B0F14] rounded-sm">
            <p className="text-slate-400 text-sm">Автомобиль</p>
            <p className="text-white font-medium">{carInfo?.brand} {carInfo?.model} {carInfo?.year}</p>
            <p className="text-[#00E5FF]">${carPrice.toLocaleString()}</p>
          </div>

          {/* Engine Parameters */}
          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div
                onClick={() => setIsElectric(false)}
                className={`flex-1 p-3 rounded-sm border cursor-pointer ${
                  !isElectric ? 'border-[#00E5FF] bg-[#00E5FF]/10' : 'border-[#27272A] bg-[#0B0F14]'
                }`}
              >
                <p className="text-white font-medium text-center">ДВС / Гибрид</p>
              </div>
              <div
                onClick={() => setIsElectric(true)}
                className={`flex-1 p-3 rounded-sm border cursor-pointer ${
                  isElectric ? 'border-[#00E5FF] bg-[#00E5FF]/10' : 'border-[#27272A] bg-[#0B0F14]'
                }`}
              >
                <p className="text-white font-medium text-center">Электро</p>
              </div>
            </div>

            {!isElectric && (
              <div>
                <div className="flex justify-between mb-2">
                  <Label className="text-white">Объём двигателя</Label>
                  <span className="text-[#00E5FF] font-bold">{engineVolume} см³</span>
                </div>
                <Slider
                  value={[engineVolume]}
                  onValueChange={(v) => setEngineVolume(v[0])}
                  min={500}
                  max={6000}
                  step={100}
                  className="w-full"
                />
                <div className="flex justify-between text-slate-500 text-xs mt-1">
                  <span>500</span>
                  <span>3000</span>
                  <span>6000 см³</span>
                </div>
              </div>
            )}
          </div>

          {/* Decree 140 Toggle */}
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
                <p className="text-slate-400 text-sm">Скидка 50% на таможенную пошлину для отдельных категорий граждан</p>
              </div>
            </div>
          </div>

          {/* Payments Breakdown */}
          <div className="space-y-2 p-4 bg-[#0B0F14] rounded-sm">
            <h4 className="text-white font-medium mb-3">Расчёт таможенных платежей</h4>
            
            <div className="flex justify-between py-2 border-b border-[#27272A]">
              <span className="text-slate-400">Утилизационный сбор</span>
              <span className="text-white font-medium">${payments.utilizationFee.toLocaleString()}</span>
            </div>
            
            <div className="flex justify-between py-2 border-b border-[#27272A]">
              <span className="text-slate-400">Таможенная пошлина</span>
              <span className="text-white font-medium">${payments.customsDuty.toLocaleString()}</span>
            </div>
            
            <div className="flex justify-between py-2 border-b border-[#27272A]">
              <span className="text-slate-400">Таможенный сбор</span>
              <span className="text-white font-medium">${payments.customsFee}</span>
            </div>
            
            <div className="flex justify-between py-2 border-b border-[#27272A]">
              <span className="text-slate-400">ЭПТС</span>
              <span className="text-white font-medium">${payments.eptsCost}</span>
            </div>

            {useDecree140 && (
              <div className="flex justify-between py-2 border-b border-[#27272A] text-emerald-400">
                <span>Льгота по Указу №140 (-50%)</span>
                <span>-${payments.decree140Discount.toLocaleString()}</span>
              </div>
            )}

            <div className="flex justify-between pt-3">
              <span className="text-white font-bold">Итого платежи</span>
              <span className="text-[#00E5FF] font-bold text-xl">${payments.total.toLocaleString()}</span>
            </div>
          </div>

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

          {/* Total with broker */}
          {selectedBroker && (
            <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-sm">
              <div className="flex justify-between items-center">
                <span className="text-emerald-400">Всего к оплате (платежи + брокер)</span>
                <span className="text-emerald-400 font-bold text-xl">
                  ${(payments.total + getBrokerPrice(customsBrokers.find(b => b.id === selectedBroker))).toLocaleString()}
                </span>
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
              Выбрать брокера
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
  onCompleteDeal
}) => {
  const getStageStatus = (stageKey) => {
    const stage = deal.stages?.[stageKey];
    if (!stage) return 'pending';
    if (stage.completed) return 'completed';
    if (stage.paid) return 'paid';
    if (stage.invoice_created) return 'invoice';
    if (stage.contractor_id) return 'contractor_selected';
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

          return (
            <div
              key={stage.key}
              className={`p-4 rounded-sm border ${
                isCurrent ? 'border-[#00E5FF] bg-[#00E5FF]/5' :
                status === 'completed' || status === 'paid' ? 'border-emerald-500/30 bg-emerald-500/5' :
                status === 'skipped' ? 'border-slate-600/30 bg-slate-800/20' :
                'border-[#27272A] bg-[#0B0F14]'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    status === 'completed' || status === 'paid' ? 'bg-emerald-500/20' :
                    status === 'skipped' ? 'bg-slate-600/20' :
                    isCurrent ? 'bg-[#00E5FF]/20' :
                    'bg-[#27272A]'
                  }`}>
                    {status === 'completed' || status === 'paid' ? (
                      <CheckCircle2 size={20} className="text-emerald-400" />
                    ) : status === 'skipped' ? (
                      <SkipForward size={20} className="text-slate-500" />
                    ) : (
                      <Icon size={20} className={isCurrent ? 'text-[#00E5FF]' : 'text-slate-500'} />
                    )}
                  </div>
                  <div>
                    <p className={`font-medium ${
                      status === 'completed' || status === 'paid' ? 'text-emerald-400' :
                      status === 'skipped' ? 'text-slate-500' :
                      isCurrent ? 'text-white' :
                      'text-slate-400'
                    }`}>
                      {stage.label}
                      {stage.optional && <span className="text-slate-500 text-xs ml-2">(можно пропустить)</span>}
                    </p>
                    
                    {/* Stage status info */}
                    {status === 'contractor_selected' && stageData?.price && (
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
                  </div>
                </div>

                {/* Stage Actions */}
                {isCurrent && status === 'pending' && (
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

                {/* Show invoice button if contractor selected */}
                {status === 'contractor_selected' && stageData?.price && (
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
