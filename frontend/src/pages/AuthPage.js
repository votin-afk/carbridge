import { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { Eye, EyeOff, ArrowLeft, Gift } from 'lucide-react';

const AuthPage = () => {
  const [searchParams] = useSearchParams();
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    name: '',
    phone: '',
    user_type: 'individual',
    referral_code: ''
  });

  const { login, register } = useAuth();
  const navigate = useNavigate();

  // Check for referral code in URL
  useEffect(() => {
    const refCode = searchParams.get('ref');
    if (refCode) {
      setFormData(prev => ({ ...prev, referral_code: refCode }));
      setIsLogin(false); // Switch to registration if coming with referral
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        toast.success('Добро пожаловать!');
      } else {
        await register(formData);
        toast.success('Регистрация успешна!');
      }
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Произошла ошибка');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  return (
    <div className="min-h-screen bg-[#0B0F14] topo-bg flex items-center justify-center p-4">
      <div className="w-full max-w-md relative z-10">
        {/* Back to home */}
        <Link 
          to="/" 
          className="inline-flex items-center gap-2 text-slate-400 hover:text-[#00E5FF] mb-8 transition-colors"
        >
          <ArrowLeft size={18} />
          <span>На главную</span>
        </Link>

        {/* Card */}
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-8">
          <div className="text-center mb-8">
            <Logo size="large" className="justify-center mb-4" />
            <h1 className="text-2xl font-bold text-white mt-4">
              {isLogin ? 'Вход в аккаунт' : 'Регистрация'}
            </h1>
            <p className="text-slate-400 mt-2">
              {isLogin ? 'Войдите в личный кабинет' : 'Создайте аккаунт для начала работы'}
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div>
                  <Label htmlFor="name" className="text-slate-300">Имя</Label>
                  <Input
                    data-testid="auth-name-input"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    placeholder="Ваше имя"
                    className="mt-1 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="phone" className="text-slate-300">Телефон</Label>
                  <Input
                    data-testid="auth-phone-input"
                    id="phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    placeholder="+375 XX XXX XX XX"
                    className="mt-1 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
                  />
                </div>

                <div>
                  <Label className="text-slate-300">Тип аккаунта</Label>
                  <div className="flex gap-4 mt-2">
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="user_type"
                        value="individual"
                        checked={formData.user_type === 'individual'}
                        onChange={handleChange}
                        className="w-4 h-4 text-[#00E5FF] bg-[#0B0F14] border-[#27272A]"
                      />
                      <span className="text-slate-300">Физ. лицо</span>
                    </label>
                    <label className="flex items-center gap-2 cursor-pointer">
                      <input
                        type="radio"
                        name="user_type"
                        value="legal"
                        checked={formData.user_type === 'legal'}
                        onChange={handleChange}
                        className="w-4 h-4 text-[#00E5FF] bg-[#0B0F14] border-[#27272A]"
                      />
                      <span className="text-slate-300">Юр. лицо</span>
                    </label>
                  </div>
                </div>

                {/* Referral Code Field */}
                <div>
                  <Label htmlFor="referral_code" className="text-slate-300 flex items-center gap-2">
                    <Gift size={14} className="text-[#00E5FF]" />
                    Реферальный код (опционально)
                  </Label>
                  <Input
                    data-testid="auth-referral-input"
                    id="referral_code"
                    name="referral_code"
                    value={formData.referral_code}
                    onChange={handleChange}
                    placeholder="Введите код, если вас пригласили"
                    className="mt-1 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
                  />
                  {formData.referral_code && (
                    <p className="text-xs text-emerald-400 mt-1">
                      ✓ Код будет применён при регистрации
                    </p>
                  )}
                </div>
              </>
            )}

            <div>
              <Label htmlFor="email" className="text-slate-300">Email</Label>
              <Input
                data-testid="auth-email-input"
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="email@example.com"
                className="mt-1 bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
                required
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-slate-300">Пароль</Label>
              <div className="relative mt-1">
                <Input
                  data-testid="auth-password-input"
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={handleChange}
                  placeholder="••••••••"
                  className="bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500 pr-10"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <Button
              data-testid="auth-submit-btn"
              type="submit"
              disabled={loading}
              className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-semibold py-3 mt-6 rounded-sm"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  Загрузка...
                </span>
              ) : (
                isLogin ? 'Войти' : 'Зарегистрироваться'
              )}
            </Button>
          </form>

          <div className="mt-6 text-center">
            <button
              data-testid="auth-toggle-mode"
              onClick={() => setIsLogin(!isLogin)}
              className="text-slate-400 hover:text-[#00E5FF] transition-colors"
            >
              {isLogin ? 'Нет аккаунта? Зарегистрируйтесь' : 'Уже есть аккаунт? Войти'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
