import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from '../hooks/useTranslation';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Switch } from '../components/ui/switch';
import { ArrowLeft, Calculator as CalcIcon, Info, BadgePercent, CreditCard } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Calculator = () => {
  const { t, lang } = useTranslation();
  const [userType, setUserType] = useState('individual');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    price_cny: '',
    age: 'under3',
    engine_type: 'ice',
    engine_volume: '',
    use_decree_140: false,
    payment_via_platform: true
  });

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleCalculate = async () => {
    if (!formData.price_cny) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/calculator`, {
        price_cny: parseFloat(formData.price_cny),
        age: formData.age,
        engine_type: formData.engine_type,
        engine_volume: formData.engine_volume ? parseInt(formData.engine_volume) : null,
        user_type: userType,
        use_decree_140: formData.use_decree_140,
        payment_via_platform: formData.payment_via_platform
      });
      setResult(response.data);
    } catch (error) {
      console.error('Calculation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat(lang === 'ru' ? 'ru-RU' : 'en-US', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    }).format(num);
  };

  const engineTypes = [
    { value: 'ice', labelKey: 'calc.ice' },
    { value: 'hybrid', labelKey: 'calc.hybrid' },
    { value: 'electric', labelKey: 'calc.electric' }
  ];

  const ageOptions = [
    { value: 'under3', labelKey: 'calc.under3' },
    { value: '3to5', labelKey: 'calc.age3to5' },
    { value: 'over5', labelKey: 'calc.over5' }
  ];

  return (
    <div className="min-h-screen bg-[#0B0F14] topo-bg">
      {/* Header */}
      <header className="bg-[#0B0F14]/90 backdrop-blur-md border-b border-[#27272A] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-6">
              <Link to="/" className="text-slate-400 hover:text-white transition-colors">
                <ArrowLeft size={20} />
              </Link>
              <Logo />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#00E5FF]/10 rounded-full mb-4">
            <CalcIcon size={32} className="text-[#00E5FF]" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2" data-testid="calc-page-title">{t('calc.pageTitle')}</h1>
          <p className="text-slate-400">{t('calc.pageSubtitle')}</p>
        </div>

        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 md:p-8">
          {/* User Type Tabs */}
          <Tabs value={userType} onValueChange={(v) => { setUserType(v); setResult(null); }} className="mb-8">
            <TabsList className="grid grid-cols-2 bg-[#0B0F14] p-1 rounded-sm">
              <TabsTrigger 
                data-testid="calc-tab-individual"
                value="individual"
                className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black rounded-sm"
              >
                {t('calc.individual')}
              </TabsTrigger>
              <TabsTrigger 
                data-testid="calc-tab-legal"
                value="legal"
                className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black rounded-sm"
              >
                {t('calc.legalEntity')}
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Input Form */}
            <div className="space-y-6">
              {/* Price */}
              <div>
                <Label className="text-slate-300">{t('calc.priceCny')}</Label>
                <div className="relative mt-2">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">&yen;</span>
                  <Input
                    data-testid="calc-price-input"
                    type="number"
                    name="price_cny"
                    value={formData.price_cny}
                    onChange={handleChange}
                    placeholder="000 000"
                    className="pl-10 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-600"
                  />
                </div>
              </div>

              {/* Engine Type */}
              <div>
                <Label className="text-slate-300">{t('calc.engineType')}</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {engineTypes.map(type => (
                    <button
                      key={type.value}
                      data-testid={`calc-engine-${type.value}`}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, engine_type: type.value }))}
                      className={`py-3 px-4 rounded-sm border text-sm font-medium transition-colors ${
                        formData.engine_type === type.value
                          ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                          : 'bg-[#0B0F14] text-slate-400 border-[#27272A] hover:border-slate-500'
                      }`}
                    >
                      {t(type.labelKey)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Age */}
              <div>
                <Label className="text-slate-300">{t('calc.carAge')}</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {ageOptions.map(age => (
                    <button
                      key={age.value}
                      data-testid={`calc-age-${age.value}`}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, age: age.value }))}
                      className={`py-3 px-4 rounded-sm border text-sm font-medium transition-colors ${
                        formData.age === age.value
                          ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                          : 'bg-[#0B0F14] text-slate-400 border-[#27272A] hover:border-slate-500'
                      }`}
                    >
                      {t(age.labelKey)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Engine Volume (for ICE and Hybrid) */}
              {formData.engine_type !== 'electric' && (
                <div>
                  <Label className="text-slate-300">{t('calc.engineVolumeCm')}</Label>
                  <Input
                    data-testid="calc-volume-input"
                    type="number"
                    name="engine_volume"
                    value={formData.engine_volume}
                    onChange={handleChange}
                    placeholder={t('calc.enterVolume')}
                    className="mt-2 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-600"
                  />
                </div>
              )}

              {/* Decree 140 - Only for individuals */}
              {userType === 'individual' && (
                <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <BadgePercent size={20} className="text-[#00E5FF]" />
                      <div>
                        <p className="text-white font-medium text-sm">{t('calc.decree140Benefit')}</p>
                        <p className="text-slate-500 text-xs">{t('calc.decree140DiscountShort')}</p>
                      </div>
                    </div>
                    <Switch
                      data-testid="calc-decree-140"
                      checked={formData.use_decree_140}
                      onCheckedChange={(checked) => setFormData(prev => ({ ...prev, use_decree_140: checked }))}
                    />
                  </div>
                  {formData.use_decree_140 && (
                    <p className="text-slate-400 text-xs mt-3 pl-8">
                      {t('calc.decree140Eligible')}
                    </p>
                  )}
                </div>
              )}

              {/* Payment method info */}
              <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 space-y-3">
                <div className="flex items-center gap-3">
                  <CreditCard size={20} className="text-[#00E5FF]" />
                  <p className="text-white font-medium text-sm">{t('calc.platformFees')}</p>
                </div>
                <div className="pl-8 space-y-2 text-sm">
                  <div className="flex justify-between text-slate-400">
                    <span>{t('calc.platformCommission')}</span>
                    <span className="text-white">3%</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>{t('calc.paymentCommission')}</span>
                    <span className="text-white">1.5%</span>
                  </div>
                </div>
              </div>

              {/* Calculate Button */}
              <Button
                data-testid="calc-submit-btn"
                onClick={handleCalculate}
                disabled={!formData.price_cny || loading}
                className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-semibold py-6 rounded-sm mt-4"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                    {t('calc.calculating')}
                  </span>
                ) : (
                  t('calc.calculate')
                )}
              </Button>
            </div>

            {/* Results */}
            <div>
              {result ? (
                <div className="space-y-4" data-testid="calc-results">
                  {/* Total */}
                  <div className="bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded-sm p-6">
                    <p className="text-slate-400 text-sm mb-1">{t('calc.totalTurnkey')}</p>
                    <p className="text-[#00E5FF] text-4xl font-bold mb-1">
                      {formatNumber(result.total_usd)} $
                    </p>
                    <p className="text-slate-400">
                      {formatNumber(result.total_byn)} BYN
                    </p>
                  </div>

                  {/* Discount Badge */}
                  {result.decree_140_discount > 0 && (
                    <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-sm p-4 flex items-center gap-3">
                      <BadgePercent size={24} className="text-emerald-400" />
                      <div>
                        <p className="text-emerald-400 font-medium">{t('calc.decree140Applied')}</p>
                        <p className="text-slate-400 text-sm">
                          {t('calc.savings')}: {formatNumber(result.decree_140_discount)} BYN
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Breakdown */}
                  <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 space-y-4">
                    <h3 className="text-white font-semibold mb-4">{t('calc.breakdown')}</h3>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.carPriceLabel')}</span>
                        <span className="text-white">{formatNumber(result.price_usd)} $</span>
                      </div>
                      
                      <div className="border-t border-[#27272A] pt-3 mt-3">
                        <p className="text-slate-500 text-xs uppercase tracking-wider mb-2">{t('calc.customsPayments')}</p>
                      </div>
                      
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.customsDuty')}</span>
                        <span className="text-white">{formatNumber(result.customs_duty)} BYN</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.utilizationFee')}</span>
                        <span className="text-white">{formatNumber(result.utilization_fee)} BYN</span>
                      </div>
                      {result.vat > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">{t('calc.vat')}</span>
                          <span className="text-white">{formatNumber(result.vat)} BYN</span>
                        </div>
                      )}
                      
                      <div className="border-t border-[#27272A] pt-3 mt-3">
                        <p className="text-slate-500 text-xs uppercase tracking-wider mb-2">{t('calc.fixedCosts')}</p>
                      </div>
                      
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.feesInBelarus')}</span>
                        <span className="text-white">{formatNumber(result.fixed_costs_byn)} BYN</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.deliveryAndProcessing')}</span>
                        <span className="text-white">{formatNumber(result.fixed_costs_usd)} $</span>
                      </div>
                      
                      <div className="border-t border-[#27272A] pt-3 mt-3">
                        <p className="text-slate-500 text-xs uppercase tracking-wider mb-2">{t('calc.platformFees')}</p>
                      </div>
                      
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.platformCommission3')}</span>
                        <span className="text-white">{formatNumber(result.platform_commission)} BYN</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">{t('calc.paymentCommission15')}</span>
                        <span className="text-white">{formatNumber(result.payment_commission)} BYN</span>
                      </div>
                      
                      {result.decree_140_discount > 0 && (
                        <>
                          <div className="border-t border-[#27272A] pt-3 mt-3">
                            <p className="text-emerald-400 text-xs uppercase tracking-wider mb-2">{t('calc.benefits')}</p>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-emerald-400">{t('calc.decree140DiscountLabel')}</span>
                            <span className="text-emerald-400">-{formatNumber(result.decree_140_discount)} BYN</span>
                          </div>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex items-start gap-3 p-4 bg-[#1C2128] border border-[#27272A] rounded-sm">
                    <Info size={18} className="text-[#00E5FF] flex-shrink-0 mt-0.5" />
                    <p className="text-slate-400 text-sm">
                      {t('calc.disclaimer')}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center text-slate-500">
                    <CalcIcon size={48} className="mx-auto mb-4 opacity-30" />
                    <p>{t('calc.enterData')}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Fixed Costs Info */}
        <div className="mt-8 bg-[#15191E] border border-[#27272A] rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4">{t('calc.fixedCostsTitle')}</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">{t('calc.customsFee')}</span>
                <span className="text-white">120 BYN</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">{t('calc.warehouseServices')}</span>
                <span className="text-white">350 BYN</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">{t('calc.epts')}</span>
                <span className="text-white">70 BYN</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">{t('calc.deliveryToBelarus')}</span>
                <span className="text-white">2 300 $</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">{t('calc.exporterCommission')}</span>
                <span className="text-white">900 $</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">{t('calc.processingInChina')}</span>
                <span className="text-white">9 000 &yen;</span>
              </div>
            </div>
          </div>
        </div>

        {/* Decree 140 Info */}
        <div className="mt-6 bg-[#15191E] border border-[#27272A] rounded-lg p-6">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 bg-emerald-500/10 rounded-full flex items-center justify-center flex-shrink-0">
              <BadgePercent size={20} className="text-emerald-400" />
            </div>
            <div>
              <h3 className="text-white font-semibold mb-2">{t('calc.decree140InfoTitle')}</h3>
              <p className="text-slate-400 text-sm mb-3">
                {t('calc.decree140InfoDesc')}
              </p>
              <ul className="text-slate-400 text-sm space-y-1 list-disc list-inside">
                <li>{t('calc.decree140Cat1')}</li>
                <li>{t('calc.decree140Cat2')}</li>
                <li>{t('calc.decree140Cat3')}</li>
              </ul>
              <p className="text-slate-500 text-xs mt-3">
                {t('calc.decree140Note')}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Calculator;
