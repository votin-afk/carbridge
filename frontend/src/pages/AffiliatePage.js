import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
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
  Users,
  DollarSign,
  Gift,
  TrendingUp,
  Copy,
  CheckCircle2,
  ArrowLeft,
  Loader2,
  Wallet,
  ArrowRight,
  Star,
  Award,
  Percent,
  HandCoins,
  Send,
  Shield,
  Clock,
  ExternalLink,
  CreditCard,
  Banknote,
  BadgeCheck
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Stats Card Component
const StatCard = ({ icon: Icon, label, value, subValue, color = "cyan" }) => {
  const colors = {
    cyan: "text-[#00E5FF] bg-[#00E5FF]/10 border-[#00E5FF]/20",
    green: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/20"
  };

  return (
    <div className={`p-4 rounded-sm border ${colors[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon size={18} className={colors[color].split(' ')[0]} />
        <span className="text-slate-400 text-sm">{label}</span>
      </div>
      <p className="text-white text-2xl font-bold">{value}</p>
      {subValue && <p className="text-slate-500 text-xs mt-1">{subValue}</p>}
    </div>
  );
};

const AffiliatePage = () => {
  const { token, user } = useAuth();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [affiliateData, setAffiliateData] = useState(null);
  const [referrals, setReferrals] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [showRegisterDialog, setShowRegisterDialog] = useState(false);
  const [showWithdrawDialog, setShowWithdrawDialog] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [withdrawing, setWithdrawing] = useState(false);
  const [copied, setCopied] = useState(false);

  const [registerForm, setRegisterForm] = useState({
    phone: '',
    telegram: '',
    payment_method: 'platform_balance',
    bank_details: ''
  });

  const [withdrawForm, setWithdrawForm] = useState({
    amount: '',
    method: 'platform_balance',
    details: ''
  });

  const headers = token ? { Authorization: `Bearer ${token}` } : {};

  // Check for referral code in URL
  useEffect(() => {
    const refCode = searchParams.get('ref');
    if (refCode && token) {
      applyReferralCode(refCode);
    }
  }, [searchParams, token]);

  const applyReferralCode = async (code) => {
    try {
      await axios.post(`${API}/affiliate/register-referral?referral_code=${code}`, {}, { headers });
      toast.success('Реферальный код применён!');
    } catch (error) {
      // Ignore if already applied or invalid
    }
  };

  const fetchAffiliateData = async () => {
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/affiliate/status`, { headers });
      setAffiliateData(response.data);
      
      // Fetch referrals and transactions
      const [refResponse, txResponse] = await Promise.all([
        axios.get(`${API}/affiliate/referrals`, { headers }),
        axios.get(`${API}/affiliate/transactions`, { headers })
      ]);
      setReferrals(refResponse.data);
      setTransactions(txResponse.data);
    } catch (error) {
      if (error.response?.status !== 404) {
        console.error('Error fetching affiliate data:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAffiliateData();
  }, [token]);

  const handleRegister = async () => {
    setRegistering(true);
    try {
      const response = await axios.post(`${API}/affiliate/register`, registerForm, { headers });
      setAffiliateData(response.data);
      setShowRegisterDialog(false);
      toast.success('Вы успешно зарегистрированы в партнёрской программе!');
    } catch (error) {
      const message = error.response?.data?.detail || 'Ошибка регистрации';
      toast.error(message);
    } finally {
      setRegistering(false);
    }
  };

  const handleWithdraw = async () => {
    if (!withdrawForm.amount || parseFloat(withdrawForm.amount) <= 0) {
      toast.error('Введите сумму');
      return;
    }

    setWithdrawing(true);
    try {
      await axios.post(`${API}/affiliate/withdraw`, {
        amount: parseFloat(withdrawForm.amount),
        method: withdrawForm.method,
        details: withdrawForm.details || null
      }, { headers });
      
      toast.success(
        withdrawForm.method === 'platform_balance' 
          ? 'Средства переведены на баланс платформы'
          : 'Заявка на вывод создана'
      );
      setShowWithdrawDialog(false);
      setWithdrawForm({ amount: '', method: 'platform_balance', details: '' });
      fetchAffiliateData();
    } catch (error) {
      const message = error.response?.data?.detail || 'Ошибка вывода';
      toast.error(message);
    } finally {
      setWithdrawing(false);
    }
  };

  const copyReferralLink = () => {
    if (affiliateData?.referral_link) {
      navigator.clipboard.writeText(affiliateData.referral_link);
      setCopied(true);
      toast.success('Ссылка скопирована!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatNumber = (num) => new Intl.NumberFormat('ru-RU').format(num);

  // Benefits data
  const benefits = [
    {
      icon: Percent,
      title: '20% от комиссии',
      description: 'Получайте 20% от комиссии CarBridge с каждой завершённой сделки вашего реферала'
    },
    {
      icon: Award,
      title: 'Статус партнёра',
      description: 'После 3 завершённых сделок рефералов вы получаете статус официального партнёра'
    },
    {
      icon: Wallet,
      title: 'Гибкий вывод',
      description: 'Выводите заработок на банковский счёт, криптокошелёк или используйте на платформе'
    },
    {
      icon: Shield,
      title: 'Прозрачность',
      description: 'Отслеживайте всех рефералов, сделки и начисления в личном кабинете'
    }
  ];

  // How it works steps
  const steps = [
    { num: '01', title: 'Регистрация', desc: 'Зарегистрируйтесь в партнёрской программе' },
    { num: '02', title: 'Приглашение', desc: 'Делитесь реферальной ссылкой с друзьями' },
    { num: '03', title: 'Сделки', desc: 'Рефералы совершают покупки авто' },
    { num: '04', title: 'Заработок', desc: 'Получайте 20% от комиссии платформы' }
  ];

  return (
    <div className="min-h-screen bg-[#0B0F14]">
      {/* Header */}
      <header className="border-b border-[#27272A] bg-[#15191E]/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2">
              <ArrowLeft size={20} className="text-slate-400" />
              <span className="text-white font-bold text-xl">CarBridge</span>
            </Link>
            
            {!token ? (
              <Link to="/auth">
                <Button className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
                  Войти
                </Button>
              </Link>
            ) : (
              <Link to="/dashboard">
                <Button variant="outline" className="border-[#27272A] text-slate-300">
                  Личный кабинет
                </Button>
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-16 border-b border-[#27272A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full mb-6">
              <HandCoins size={18} className="text-emerald-400" />
              <span className="text-emerald-400 font-medium">Партнёрская программа</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl font-bold text-white mb-6">
              Зарабатывайте с{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#00E5FF] to-emerald-400">
                CarBridge
              </span>
            </h1>
            
            <p className="text-slate-400 text-lg mb-8">
              Приглашайте друзей и получайте <span className="text-emerald-400 font-semibold">20%</span> от комиссии платформы 
              с каждой завершённой сделки. Без ограничений по заработку!
            </p>

            {!token ? (
              <Link to="/auth">
                <Button size="lg" className="bg-gradient-to-r from-[#00E5FF] to-emerald-500 hover:opacity-90 text-black px-8">
                  <Users size={20} className="mr-2" />
                  Стать партнёром
                </Button>
              </Link>
            ) : !affiliateData ? (
              <Button 
                size="lg" 
                onClick={() => setShowRegisterDialog(true)}
                className="bg-gradient-to-r from-[#00E5FF] to-emerald-500 hover:opacity-90 text-black px-8"
              >
                <Users size={20} className="mr-2" />
                Присоединиться к программе
              </Button>
            ) : (
              <div className="flex items-center justify-center gap-4">
                {affiliateData.is_partner && (
                  <div className="flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/20 rounded-full">
                    <BadgeCheck size={18} className="text-amber-400" />
                    <span className="text-amber-400 font-medium">Официальный партнёр</span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Affiliate Dashboard (if registered) */}
      {affiliateData && (
        <section className="py-12 border-b border-[#27272A]">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <TrendingUp size={24} className="text-[#00E5FF]" />
              Ваша статистика
            </h2>

            {/* Stats Grid */}
            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatCard 
                icon={Users} 
                label="Рефералов" 
                value={affiliateData.total_referrals}
                subValue={`${affiliateData.active_referrals} активных`}
                color="cyan"
              />
              <StatCard 
                icon={CheckCircle2} 
                label="Сделок" 
                value={affiliateData.completed_deals}
                subValue={affiliateData.is_partner ? "Партнёр ✓" : `До партнёра: ${3 - affiliateData.completed_deals}`}
                color="green"
              />
              <StatCard 
                icon={DollarSign} 
                label="Всего заработано" 
                value={`$${formatNumber(affiliateData.total_earnings)}`}
                color="amber"
              />
              <StatCard 
                icon={Wallet} 
                label="Доступно к выводу" 
                value={`$${formatNumber(affiliateData.available_balance)}`}
                subValue={`Выведено: $${formatNumber(affiliateData.withdrawn_earnings)}`}
                color="purple"
              />
            </div>

            {/* Referral Link */}
            <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6 mb-8">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <Gift size={18} className="text-emerald-400" />
                Ваша реферальная ссылка
              </h3>
              
              <div className="flex gap-3">
                <div className="flex-1 bg-[#0B0F14] border border-[#27272A] rounded-sm px-4 py-3">
                  <code className="text-[#00E5FF] text-sm break-all">{affiliateData.referral_link}</code>
                </div>
                <Button
                  onClick={copyReferralLink}
                  className={`px-6 ${copied ? 'bg-emerald-500' : 'bg-[#00E5FF]'} hover:opacity-90 text-black`}
                >
                  {copied ? <CheckCircle2 size={18} /> : <Copy size={18} />}
                </Button>
              </div>
              
              <p className="text-slate-500 text-sm mt-3">
                Код: <span className="text-white font-mono">{affiliateData.referral_code}</span>
              </p>
            </div>

            {/* Withdraw Button */}
            {affiliateData.available_balance > 0 && (
              <div className="flex justify-center">
                <Button
                  onClick={() => setShowWithdrawDialog(true)}
                  className="bg-emerald-500 hover:bg-emerald-600 text-white px-8"
                >
                  <Banknote size={18} className="mr-2" />
                  Вывести ${formatNumber(affiliateData.available_balance)}
                </Button>
              </div>
            )}

            {/* Referrals List */}
            {referrals.length > 0 && (
              <div className="mt-8">
                <h3 className="text-white font-semibold mb-4">Ваши рефералы</h3>
                <div className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-[#0B0F14]">
                      <tr>
                        <th className="text-left text-slate-400 text-xs font-medium px-4 py-3">Пользователь</th>
                        <th className="text-left text-slate-400 text-xs font-medium px-4 py-3">Дата регистрации</th>
                        <th className="text-center text-slate-400 text-xs font-medium px-4 py-3">Сделок</th>
                        <th className="text-right text-slate-400 text-xs font-medium px-4 py-3">Комиссия</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-[#27272A]">
                      {referrals.map((ref) => (
                        <tr key={ref.id} className="hover:bg-[#1C2128]">
                          <td className="px-4 py-3">
                            <p className="text-white text-sm">{ref.referral_name || 'Пользователь'}</p>
                            <p className="text-slate-500 text-xs">{ref.referral_email}</p>
                          </td>
                          <td className="px-4 py-3 text-slate-400 text-sm">
                            {new Date(ref.registered_at).toLocaleDateString('ru-RU')}
                          </td>
                          <td className="px-4 py-3 text-center">
                            <span className={`px-2 py-1 rounded text-xs ${
                              ref.completed_deals > 0 
                                ? 'bg-emerald-500/10 text-emerald-400' 
                                : 'bg-slate-500/10 text-slate-400'
                            }`}>
                              {ref.completed_deals}
                            </span>
                          </td>
                          <td className="px-4 py-3 text-right text-emerald-400 font-medium">
                            ${formatNumber(ref.total_commission)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Transactions */}
            {transactions.length > 0 && (
              <div className="mt-8">
                <h3 className="text-white font-semibold mb-4">История операций</h3>
                <div className="space-y-2">
                  {transactions.slice(0, 5).map((tx) => (
                    <div 
                      key={tx.id}
                      className="flex items-center justify-between p-4 bg-[#15191E] border border-[#27272A] rounded-sm"
                    >
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-full ${
                          tx.type === 'commission' 
                            ? 'bg-emerald-500/10 text-emerald-400'
                            : 'bg-red-500/10 text-red-400'
                        }`}>
                          {tx.type === 'commission' ? <TrendingUp size={16} /> : <Send size={16} />}
                        </div>
                        <div>
                          <p className="text-white text-sm">{tx.description}</p>
                          <p className="text-slate-500 text-xs">
                            {new Date(tx.created_at).toLocaleDateString('ru-RU')}
                          </p>
                        </div>
                      </div>
                      <span className={`font-semibold ${
                        tx.amount > 0 ? 'text-emerald-400' : 'text-red-400'
                      }`}>
                        {tx.amount > 0 ? '+' : ''}${formatNumber(Math.abs(tx.amount))}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* Benefits Section */}
      <section className="py-16 border-b border-[#27272A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-white text-center mb-12">
            Преимущества партнёрской программы
          </h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {benefits.map((benefit, idx) => (
              <div 
                key={idx}
                className="p-6 bg-[#15191E] border border-[#27272A] rounded-sm hover:border-[#00E5FF]/30 transition-colors"
              >
                <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center mb-4">
                  <benefit.icon size={24} className="text-[#00E5FF]" />
                </div>
                <h3 className="text-white font-semibold mb-2">{benefit.title}</h3>
                <p className="text-slate-400 text-sm">{benefit.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-16 border-b border-[#27272A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl font-bold text-white text-center mb-12">
            Как это работает
          </h2>
          
          <div className="grid md:grid-cols-4 gap-6">
            {steps.map((step, idx) => (
              <div key={idx} className="text-center relative">
                {idx < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-1/2 w-full h-0.5 bg-gradient-to-r from-[#00E5FF] to-transparent" />
                )}
                <div className="w-16 h-16 mx-auto bg-gradient-to-br from-[#00E5FF] to-emerald-500 rounded-full flex items-center justify-center mb-4 relative z-10">
                  <span className="text-black font-bold text-lg">{step.num}</span>
                </div>
                <h3 className="text-white font-semibold mb-2">{step.title}</h3>
                <p className="text-slate-400 text-sm">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Commission Calculator */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            Пример расчёта
          </h2>
          <p className="text-slate-400 mb-8">
            При покупке автомобиля за <span className="text-white">$30,000</span>
          </p>
          
          <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-8">
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 bg-[#0B0F14] rounded-sm">
                <p className="text-slate-400 text-xs mb-1">Стоимость авто</p>
                <p className="text-white text-xl font-bold">$30,000</p>
              </div>
              <div className="p-4 bg-[#0B0F14] rounded-sm">
                <p className="text-slate-400 text-xs mb-1">Комиссия CarBridge (3%)</p>
                <p className="text-white text-xl font-bold">$900</p>
              </div>
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-sm">
                <p className="text-emerald-400 text-xs mb-1">Ваш заработок (20%)</p>
                <p className="text-emerald-400 text-xl font-bold">$180</p>
              </div>
            </div>
            
            <p className="text-slate-400 text-sm">
              5 рефералов × 2 сделки в год = <span className="text-emerald-400 font-semibold">$1,800/год</span> пассивного дохода
            </p>
          </div>

          {!affiliateData && token && (
            <Button 
              onClick={() => setShowRegisterDialog(true)}
              size="lg"
              className="mt-8 bg-gradient-to-r from-[#00E5FF] to-emerald-500 hover:opacity-90 text-black px-8"
            >
              Начать зарабатывать
              <ArrowRight size={18} className="ml-2" />
            </Button>
          )}
        </div>
      </section>

      {/* Register Dialog */}
      <Dialog open={showRegisterDialog} onOpenChange={setShowRegisterDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users size={20} className="text-[#00E5FF]" />
              Регистрация в партнёрской программе
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div>
              <Label className="text-slate-300">Телефон (опционально)</Label>
              <Input
                type="tel"
                value={registerForm.phone}
                onChange={(e) => setRegisterForm(prev => ({ ...prev, phone: e.target.value }))}
                placeholder="+375 29 123 45 67"
                className="mt-1 bg-[#0B0F14] border-[#27272A]"
              />
            </div>

            <div>
              <Label className="text-slate-300">Telegram (опционально)</Label>
              <Input
                value={registerForm.telegram}
                onChange={(e) => setRegisterForm(prev => ({ ...prev, telegram: e.target.value }))}
                placeholder="@username"
                className="mt-1 bg-[#0B0F14] border-[#27272A]"
              />
            </div>

            <div>
              <Label className="text-slate-300">Способ получения выплат</Label>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {[
                  { value: 'platform_balance', label: 'Баланс', icon: Wallet },
                  { value: 'bank_transfer', label: 'Банк', icon: CreditCard },
                  { value: 'crypto', label: 'Крипто', icon: Banknote }
                ].map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setRegisterForm(prev => ({ ...prev, payment_method: option.value }))}
                    className={`py-3 px-2 rounded-sm border text-sm flex flex-col items-center gap-1 ${
                      registerForm.payment_method === option.value
                        ? 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]'
                        : 'bg-[#0B0F14] text-slate-400 border-[#27272A]'
                    }`}
                  >
                    <option.icon size={18} />
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {registerForm.payment_method === 'bank_transfer' && (
              <div>
                <Label className="text-slate-300">Банковские реквизиты</Label>
                <textarea
                  value={registerForm.bank_details}
                  onChange={(e) => setRegisterForm(prev => ({ ...prev, bank_details: e.target.value }))}
                  placeholder="IBAN, название банка..."
                  className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 min-h-[80px]"
                />
              </div>
            )}

            <Button
              onClick={handleRegister}
              disabled={registering}
              className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {registering ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <CheckCircle2 size={16} className="mr-2" />
              )}
              Зарегистрироваться
            </Button>

            <p className="text-slate-500 text-xs text-center">
              Регистрируясь, вы соглашаетесь с условиями партнёрской программы
            </p>
          </div>
        </DialogContent>
      </Dialog>

      {/* Withdraw Dialog */}
      <Dialog open={showWithdrawDialog} onOpenChange={setShowWithdrawDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Banknote size={20} className="text-emerald-400" />
              Вывод средств
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-sm">
              <p className="text-slate-400 text-sm">Доступно к выводу</p>
              <p className="text-emerald-400 text-2xl font-bold">
                ${formatNumber(affiliateData?.available_balance || 0)}
              </p>
            </div>

            <div>
              <Label className="text-slate-300">Сумма вывода ($)</Label>
              <Input
                type="number"
                value={withdrawForm.amount}
                onChange={(e) => setWithdrawForm(prev => ({ ...prev, amount: e.target.value }))}
                placeholder="0.00"
                max={affiliateData?.available_balance || 0}
                className="mt-1 bg-[#0B0F14] border-[#27272A]"
              />
            </div>

            <div>
              <Label className="text-slate-300">Способ вывода</Label>
              <div className="grid grid-cols-3 gap-2 mt-2">
                {[
                  { value: 'platform_balance', label: 'На баланс', icon: Wallet, desc: 'Мгновенно' },
                  { value: 'bank_transfer', label: 'На карту', icon: CreditCard, desc: '1-3 дня' },
                  { value: 'crypto', label: 'Крипто', icon: Banknote, desc: '1 час' }
                ].map(option => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => setWithdrawForm(prev => ({ ...prev, method: option.value }))}
                    className={`py-3 px-2 rounded-sm border text-sm flex flex-col items-center gap-1 ${
                      withdrawForm.method === option.value
                        ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500'
                        : 'bg-[#0B0F14] text-slate-400 border-[#27272A]'
                    }`}
                  >
                    <option.icon size={18} />
                    <span>{option.label}</span>
                    <span className="text-xs opacity-60">{option.desc}</span>
                  </button>
                ))}
              </div>
            </div>

            {withdrawForm.method !== 'platform_balance' && (
              <div>
                <Label className="text-slate-300">
                  {withdrawForm.method === 'bank_transfer' ? 'Реквизиты карты' : 'Адрес кошелька'}
                </Label>
                <Input
                  value={withdrawForm.details}
                  onChange={(e) => setWithdrawForm(prev => ({ ...prev, details: e.target.value }))}
                  placeholder={withdrawForm.method === 'bank_transfer' ? 'IBAN или номер карты' : 'USDT TRC20 адрес'}
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>
            )}

            <Button
              onClick={handleWithdraw}
              disabled={withdrawing || !withdrawForm.amount}
              className="w-full bg-emerald-500 hover:bg-emerald-600 text-white"
            >
              {withdrawing ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <Send size={16} className="mr-2" />
              )}
              {withdrawForm.method === 'platform_balance' ? 'Перевести на баланс' : 'Создать заявку'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AffiliatePage;
