import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ArrowLeft, Calculator as CalcIcon, Info } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Calculator = () => {
  const [userType, setUserType] = useState('individual');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [formData, setFormData] = useState({
    price_cny: '',
    age: 'under3',
    engine_type: 'ice',
    engine_volume: '',
    use_decree_140: false
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
        use_decree_140: formData.use_decree_140
      });
      setResult(response.data);
    } catch (error) {
      console.error('Calculation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('ru-RU', { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    }).format(num);
  };

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

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-[#00E5FF]/10 rounded-full mb-4">
            <CalcIcon size={32} className="text-[#00E5FF]" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Калькулятор растаможки</h1>
          <p className="text-slate-400">Рассчитайте полную стоимость авто «под ключ» в Беларуси</p>
        </div>

        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 md:p-8">
          {/* User Type Tabs */}
          <Tabs value={userType} onValueChange={setUserType} className="mb-8">
            <TabsList className="grid grid-cols-2 bg-[#0B0F14] p-1 rounded-sm">
              <TabsTrigger 
                data-testid="calc-tab-individual"
                value="individual"
                className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black rounded-sm"
              >
                Физ. лицо
              </TabsTrigger>
              <TabsTrigger 
                data-testid="calc-tab-legal"
                value="legal"
                className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black rounded-sm"
              >
                Юр. лицо
              </TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Input Form */}
            <div className="space-y-6">
              {/* Price */}
              <div>
                <Label className="text-slate-300">Цена в CNY (юанях)</Label>
                <div className="relative mt-2">
                  <span className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500">¥</span>
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
                <Label className="text-slate-300">Тип двигателя</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {[
                    { value: 'ice', label: 'ДВС' },
                    { value: 'hybrid', label: 'Гибрид' },
                    { value: 'electric', label: 'Электро' }
                  ].map(type => (
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
                      {type.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Age */}
              <div>
                <Label className="text-slate-300">Возраст авто</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {[
                    { value: 'under3', label: 'До 3 лет' },
                    { value: '3to5', label: '3-5 лет' },
                    { value: 'over5', label: '5+ лет' }
                  ].map(age => (
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
                      {age.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Engine Volume (for ICE and Hybrid) */}
              {formData.engine_type !== 'electric' && (
                <div>
                  <Label className="text-slate-300">Объем двигателя (см³)</Label>
                  <Input
                    data-testid="calc-volume-input"
                    type="number"
                    name="engine_volume"
                    value={formData.engine_volume}
                    onChange={handleChange}
                    placeholder="Введите объем"
                    className="mt-2 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-600"
                  />
                </div>
              )}

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
                    Расчет...
                  </span>
                ) : (
                  'Рассчитать'
                )}
              </Button>
            </div>

            {/* Results */}
            <div>
              {result ? (
                <div className="space-y-4">
                  {/* Total */}
                  <div className="bg-[#00E5FF]/10 border border-[#00E5FF]/30 rounded-sm p-6">
                    <p className="text-slate-400 text-sm mb-1">Итого «под ключ»</p>
                    <p className="text-[#00E5FF] text-4xl font-bold mb-1">
                      {formatNumber(result.total_usd)} $
                    </p>
                    <p className="text-slate-400">
                      {formatNumber(result.total_byn)} BYN
                    </p>
                  </div>

                  {/* Breakdown */}
                  <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 space-y-4">
                    <h3 className="text-white font-semibold mb-4">Детализация</h3>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Цена авто</span>
                        <span className="text-white">{formatNumber(result.price_usd)} $</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Таможенная пошлина</span>
                        <span className="text-white">{formatNumber(result.customs_duty)} BYN</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Утилизационный сбор</span>
                        <span className="text-white">{formatNumber(result.utilization_fee)} BYN</span>
                      </div>
                      {result.vat > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-400">НДС</span>
                          <span className="text-white">{formatNumber(result.vat)} BYN</span>
                        </div>
                      )}
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Фикс. расходы (BYN)</span>
                        <span className="text-white">{formatNumber(result.fixed_costs_byn)} BYN</span>
                      </div>
                      <div className="flex justify-between text-sm">
                        <span className="text-slate-400">Фикс. расходы (USD)</span>
                        <span className="text-white">{formatNumber(result.fixed_costs_usd)} $</span>
                      </div>
                    </div>
                  </div>

                  {/* Info */}
                  <div className="flex items-start gap-3 p-4 bg-[#1C2128] border border-[#27272A] rounded-sm">
                    <Info size={18} className="text-[#00E5FF] flex-shrink-0 mt-0.5" />
                    <p className="text-slate-400 text-sm">
                      Расчет является ориентировочным. Точная стоимость может отличаться в зависимости от актуальных курсов валют и индивидуальных условий.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center">
                  <div className="text-center text-slate-500">
                    <CalcIcon size={48} className="mx-auto mb-4 opacity-30" />
                    <p>Введите данные для расчета</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Fixed Costs Info */}
        <div className="mt-8 bg-[#15191E] border border-[#27272A] rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4">Фиксированные расходы</h3>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Таможенный сбор</span>
                <span className="text-white">120 BYN</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Услуги склада и декларантов</span>
                <span className="text-white">350 BYN</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">ЭПТС</span>
                <span className="text-white">70 BYN</span>
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Доставка до Беларуси</span>
                <span className="text-white">2 300 $</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Комиссия экспортера</span>
                <span className="text-white">900 $</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Оформление в Китае</span>
                <span className="text-white">9 000 ¥</span>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Calculator;
