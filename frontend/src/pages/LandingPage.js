import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "../components/ui/accordion";
import { 
  ArrowRight, 
  Shield, 
  Search, 
  Truck, 
  FileCheck,
  Calculator,
  Users,
  CheckCircle2,
  ChevronRight,
  ExternalLink,
  Phone,
  Mail,
  MapPin,
  Bot,
  Send,
  Loader2,
  Sparkles
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LandingPage = () => {
  const { isAuthenticated } = useAuth();
  
  // AI Chat state
  const [chatMessages, setChatMessages] = useState([
    {
      role: 'assistant',
      content: 'Привет! Я AI-ассистент CARBRIDGE. Помогу подобрать автомобиль из Китая под ваши требования. Расскажите, какой автомобиль вы ищете?'
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const response = await axios.post(`${API}/chat`, {
        message: userMessage,
        session_id: sessionId
      });
      setSessionId(response.data.session_id);
      setChatMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Извините, произошла ошибка. Попробуйте позже или свяжитесь с нами напрямую.' 
      }]);
    } finally {
      setChatLoading(false);
    }
  };

  const processSteps = [
    { num: "01", title: "Подбор", desc: "AI-ассистент помогает определить потребности и подобрать авто", icon: Search },
    { num: "02", title: "Тендер", desc: "Запрос рассылается верифицированным подрядчикам в Китае", icon: Users },
    { num: "03", title: "Инспекция", desc: "Видеообзор, фото и профессиональный отчет о состоянии", icon: FileCheck },
    { num: "04", title: "Оплата", desc: "Безопасная сделка с гарантией возврата средств", icon: Shield },
    { num: "05", title: "Логистика", desc: "GPS-трекинг и фото/видео отчеты на каждом этапе", icon: Truck },
    { num: "06", title: "Выдача", desc: "Таможенное оформление и передача авто с документами", icon: CheckCircle2 },
  ];

  const advantages = [
    { title: "Честные 3%", desc: "Прозрачная комиссия без скрытых наценок", icon: "%" },
    { title: "Тендер дилеров", desc: "Конкуренция подрядчиков - лучшая цена для вас", icon: "↔" },
    { title: "GPS-трекинг", desc: "Отслеживайте авто в реальном времени", icon: "◎" },
    { title: "Видео-отчеты", desc: "Фото и видео на каждом этапе сделки", icon: "▶" },
  ];

  const platforms = [
    { name: "58.com", url: "https://m.58.com/", desc: "Крупнейший классифайд Китая" },
    { name: "Che168", url: "https://www.che168.com/", desc: "Ведущая автоплощадка" },
    { name: "Guazi", url: "https://www.guazi.com", desc: "Авто с пробегом" },
    { name: "Dongchedi", url: "https://www.dongchedi.com", desc: "Автопортал от ByteDance" },
  ];

  const faqItems = [
    {
      q: "Сколько стоят ваши услуги?",
      a: "Комиссия платформы составляет 3% от стоимости автомобиля (FOB Китай). За проведение платежа через платформу взимается дополнительно 1.5%, которые включают банковские издержки и гарантию безопасности сделки."
    },
    {
      q: "Как долго занимает доставка?",
      a: "Средний срок доставки составляет 30-45 дней с момента выкупа автомобиля. Срок зависит от выбранного способа перевозки (ЖД или автовоз) и загруженности маршрута."
    },
    {
      q: "Какие гарантии вы предоставляете?",
      a: "Мы используем модель безопасной сделки - деньги переводятся подрядчику только после подтверждения выполнения каждого этапа. Все подрядчики проходят многоуровневую верификацию, включая физический аудит офиса."
    },
    {
      q: "Можно ли привезти электромобиль?",
      a: "Да, электромобили растамаживаются по льготной ставке 0%. Это делает их особенно выгодными для импорта. Мы поможем подобрать подходящую модель с учетом особенностей эксплуатации в Беларуси."
    },
    {
      q: "Что такое Указ 140?",
      a: "Указ № 140 позволяет многодетным семьям, инвалидам I-II групп и родителям детей-инвалидов получить 50% скидку на таможенные пошлины при ввозе автомобиля для личного пользования."
    },
  ];

  return (
    <div className="min-h-screen bg-[#0B0F14]">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0B0F14]/90 backdrop-blur-md border-b border-[#27272A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Logo />
            
            <nav className="hidden md:flex items-center gap-8">
              <Link to="/catalog" className="text-slate-400 hover:text-[#00E5FF] transition-colors font-medium">Каталог</Link>
              <a href="#ai-agent" className="text-slate-400 hover:text-white transition-colors">AI Подбор</a>
              <a href="#process" className="text-slate-400 hover:text-white transition-colors">Процесс</a>
              <a href="#advantages" className="text-slate-400 hover:text-white transition-colors">Преимущества</a>
              <a href="#faq" className="text-slate-400 hover:text-white transition-colors">FAQ</a>
              <a href="#contacts" className="text-slate-400 hover:text-white transition-colors">Контакты</a>
            </nav>

            <div className="flex items-center gap-3">
              <Link to="/calculator">
                <Button variant="ghost" className="hidden sm:flex text-slate-400 hover:text-[#00E5FF]">
                  <Calculator size={18} className="mr-2" />
                  Калькулятор
                </Button>
              </Link>
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button data-testid="header-dashboard-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-medium rounded-sm">
                    Личный кабинет
                  </Button>
                </Link>
              ) : (
                <Link to="/auth">
                  <Button data-testid="header-login-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-medium rounded-sm">
                    Войти
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative pt-32 pb-16 topo-bg overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="fade-in">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#00E5FF]/10 border border-[#00E5FF]/20 rounded-full mb-6">
                <span className="w-2 h-2 bg-[#00E5FF] rounded-full animate-pulse" />
                <span className="text-[#00E5FF] text-sm font-medium">Импорт авто из Китая</span>
              </div>
              
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
                Ваш прямой мост к автомобилям из{' '}
                <span className="text-[#00E5FF]">Китая</span>
              </h1>
              
              <p className="text-lg text-slate-400 mb-8 max-w-lg">
                Прозрачная платформа с тендером среди дилеров. Без скрытых наценок, под контролем AI и модераторов.
              </p>

              <div className="flex flex-wrap gap-4">
                <a href="#ai-agent">
                  <Button data-testid="hero-cta-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-semibold px-8 py-6 rounded-sm btn-glow">
                    <Sparkles className="mr-2" size={20} />
                    AI Подбор авто
                  </Button>
                </a>
                <Link to="/calculator">
                  <Button data-testid="hero-calc-btn" variant="outline" className="border-[#27272A] text-white hover:border-[#00E5FF] hover:text-[#00E5FF] px-8 py-6 rounded-sm">
                    Рассчитать стоимость
                  </Button>
                </Link>
              </div>

              <div className="flex items-center gap-8 mt-10 pt-8 border-t border-[#27272A]">
                <div>
                  <p className="text-3xl font-bold text-white">500+</p>
                  <p className="text-slate-500 text-sm">Доставленных авто</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-white">4.9</p>
                  <p className="text-slate-500 text-sm">Рейтинг клиентов</p>
                </div>
                <div>
                  <p className="text-3xl font-bold text-white">3%</p>
                  <p className="text-slate-500 text-sm">Комиссия</p>
                </div>
              </div>
            </div>

            <div className="relative fade-in fade-in-delay-2">
              <div className="relative rounded-lg overflow-hidden border border-[#27272A] glow-cyan">
                <img 
                  src="https://images.pexels.com/photos/32912506/pexels-photo-32912506.jpeg"
                  alt="Premium Chinese EV"
                  className="w-full h-[400px] object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F14] via-transparent to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-6">
                  <p className="text-slate-400 text-sm mb-1">Популярный выбор</p>
                  <p className="text-white text-xl font-semibold">Li Auto L9 Max</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI Agent Section */}
      <section id="ai-agent" className="py-16 bg-[#15191E]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#00E5FF]/10 border border-[#00E5FF]/20 rounded-full mb-4">
              <Sparkles size={16} className="text-[#00E5FF]" />
              <span className="text-[#00E5FF] text-sm font-medium">AI-агент подбора</span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Подберите авто с помощью AI</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">
              Расскажите о ваших требованиях, бюджете и предпочтениях — AI поможет найти идеальный автомобиль из Китая
            </p>
          </div>

          <div className="max-w-3xl mx-auto">
            <div className="bg-[#1C2128] border border-[#27272A] rounded-lg overflow-hidden glow-cyan">
              {/* Chat Header */}
              <div className="px-6 py-4 border-b border-[#27272A] flex items-center gap-3">
                <div className="w-10 h-10 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                  <Bot className="text-[#00E5FF]" size={20} />
                </div>
                <div>
                  <h3 className="text-white font-semibold">AI-Ассистент CARBRIDGE</h3>
                  <p className="text-slate-500 text-sm">Онлайн • Отвечу на любые вопросы</p>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="h-[350px] overflow-y-auto p-6 space-y-4" data-testid="ai-agent-chat">
                {chatMessages.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                      msg.role === 'user' ? 'bg-[#27272A]' : 'bg-[#00E5FF]/10'
                    }`}>
                      {msg.role === 'user' ? (
                        <span className="text-slate-400 text-sm font-medium">Вы</span>
                      ) : (
                        <Bot className="w-4 h-4 text-[#00E5FF]" />
                      )}
                    </div>
                    <div className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed ${
                      msg.role === 'user' 
                        ? 'bg-[#27272A] text-white rounded-2xl rounded-tr-sm' 
                        : 'bg-[#00E5FF]/10 border border-[#00E5FF]/20 text-slate-200 rounded-2xl rounded-tl-sm'
                    }`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div className="flex gap-3">
                    <div className="w-8 h-8 rounded-full bg-[#00E5FF]/10 flex items-center justify-center">
                      <Bot className="w-4 h-4 text-[#00E5FF]" />
                    </div>
                    <div className="bg-[#00E5FF]/10 border border-[#00E5FF]/20 rounded-2xl rounded-tl-sm px-4 py-3">
                      <Loader2 className="w-5 h-5 text-[#00E5FF] animate-spin" />
                    </div>
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Chat Input */}
              <div className="p-4 border-t border-[#27272A] bg-[#15191E]">
                <div className="flex gap-3">
                  <input
                    data-testid="ai-agent-input"
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                    placeholder="Опишите, какой автомобиль вы ищете..."
                    className="flex-1 bg-[#0B0F14] border border-[#27272A] rounded-lg px-4 py-3 text-white placeholder:text-slate-500 focus:border-[#00E5FF] focus:ring-1 focus:ring-[#00E5FF]/20"
                    disabled={chatLoading}
                  />
                  <Button
                    data-testid="ai-agent-send"
                    onClick={sendChatMessage}
                    disabled={!chatInput.trim() || chatLoading}
                    className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black px-6 rounded-lg disabled:opacity-50"
                  >
                    <Send size={20} />
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2 mt-3">
                  {['Электромобиль до $30000', 'Семейный кроссовер', 'BYD или Li Auto'].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => setChatInput(suggestion)}
                      className="px-3 py-1.5 text-xs bg-[#27272A] text-slate-400 rounded-full hover:bg-[#00E5FF]/10 hover:text-[#00E5FF] transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Process Section */}
      <section id="process" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-[#00E5FF] text-sm font-medium uppercase tracking-wider mb-3">Как это работает</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">Процесс покупки</h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {processSteps.map((step, idx) => (
              <div 
                key={idx}
                className="bg-[#15191E] border border-[#27272A] rounded-sm p-6 card-hover group"
              >
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center text-[#00E5FF] group-hover:bg-[#00E5FF] group-hover:text-black transition-colors">
                    <step.icon size={24} />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[#00E5FF] font-mono text-sm">{step.num}</span>
                      <h3 className="text-white font-semibold">{step.title}</h3>
                    </div>
                    <p className="text-slate-400 text-sm">{step.desc}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Advantages Section */}
      <section id="advantages" className="py-24 bg-[#15191E]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-[#00E5FF] text-sm font-medium uppercase tracking-wider mb-3">Почему мы</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">Наши преимущества</h2>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {advantages.map((item, idx) => (
              <div 
                key={idx}
                className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 text-center card-hover"
              >
                <div className="w-16 h-16 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center text-[#00E5FF] text-2xl font-bold">
                  {item.icon}
                </div>
                <h3 className="text-white font-semibold text-lg mb-2">{item.title}</h3>
                <p className="text-slate-400 text-sm">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platforms Section */}
      <section id="platforms" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-[#00E5FF] text-sm font-medium uppercase tracking-wider mb-3">Где искать</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">Площадки в Китае</h2>
            <p className="text-slate-400 mt-4 max-w-2xl mx-auto">
              Основные платформы для поиска автомобилей. Найдите авто и добавьте его в гараж для запуска тендера.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {platforms.map((platform, idx) => (
              <a
                key={idx}
                href={platform.url}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-[#15191E] border border-[#27272A] rounded-sm p-6 card-hover group flex flex-col"
              >
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-white font-semibold text-lg group-hover:text-[#00E5FF] transition-colors">
                    {platform.name}
                  </h3>
                  <ExternalLink size={18} className="text-slate-500 group-hover:text-[#00E5FF] transition-colors" />
                </div>
                <p className="text-slate-400 text-sm flex-1">{platform.desc}</p>
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* Calculator CTA */}
      <section className="py-24 bg-[#15191E]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-[#1C2128] to-[#15191E] border border-[#27272A] rounded-lg p-8 md:p-12 glow-cyan">
            <div className="grid md:grid-cols-2 gap-8 items-center">
              <div>
                <h2 className="text-3xl font-bold text-white mb-4">
                  Рассчитайте стоимость автомобиля
                </h2>
                <p className="text-slate-400 mb-6">
                  Бесплатный калькулятор для расчета полной стоимости авто «под ключ» в Беларуси. Учитывает все расходы: растаможку, доставку, комиссии. Поддерживает льготу по Указу 140.
                </p>
                <Link to="/calculator">
                  <Button data-testid="calc-cta-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-semibold px-8 py-6 rounded-sm">
                    Открыть калькулятор
                    <ChevronRight className="ml-2" size={20} />
                  </Button>
                </Link>
              </div>
              <div className="hidden md:flex justify-center">
                <div className="w-48 h-48 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                  <Calculator size={80} className="text-[#00E5FF]" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="py-24">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-[#00E5FF] text-sm font-medium uppercase tracking-wider mb-3">FAQ</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">Частые вопросы</h2>
          </div>

          <Accordion type="single" collapsible className="space-y-4">
            {faqItems.map((item, idx) => (
              <AccordionItem 
                key={idx} 
                value={`item-${idx}`}
                className="bg-[#15191E] border border-[#27272A] rounded-sm px-6 data-[state=open]:border-[#00E5FF]/50"
              >
                <AccordionTrigger className="text-white hover:text-[#00E5FF] text-left py-4">
                  {item.q}
                </AccordionTrigger>
                <AccordionContent className="text-slate-400 pb-4">
                  {item.a}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* Contacts Section */}
      <section id="contacts" className="py-24 bg-[#15191E]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <p className="text-[#00E5FF] text-sm font-medium uppercase tracking-wider mb-3">Связаться</p>
            <h2 className="text-3xl sm:text-4xl font-bold text-white">Контакты</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
            <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 text-center card-hover">
              <div className="w-12 h-12 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                <Phone size={24} className="text-[#00E5FF]" />
              </div>
              <h3 className="text-white font-medium mb-2">Телефон</h3>
              <a href="tel:+375291234567" className="text-slate-400 hover:text-[#00E5FF] transition-colors">
                +375 (29) 123-45-67
              </a>
            </div>

            <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 text-center card-hover">
              <div className="w-12 h-12 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                <Mail size={24} className="text-[#00E5FF]" />
              </div>
              <h3 className="text-white font-medium mb-2">Email</h3>
              <a href="mailto:info@carbridge.by" className="text-slate-400 hover:text-[#00E5FF] transition-colors">
                info@carbridge.by
              </a>
            </div>

            <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 text-center card-hover">
              <div className="w-12 h-12 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                <MapPin size={24} className="text-[#00E5FF]" />
              </div>
              <h3 className="text-white font-medium mb-2">Адрес</h3>
              <p className="text-slate-400">г. Минск, ул. Примерная, 123</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-[#27272A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <Logo />
            <p className="text-slate-500 text-sm">
              © 2024 CARBRIDGE. Все права защищены.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
