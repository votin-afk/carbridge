import { useState, useRef, useEffect, useCallback } from 'react';
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
  Sparkles,
  Car,
  ChevronLeft,
  MessageCircle,
  Flame,
  Clock,
  ShoppingCart
} from 'lucide-react';

// Messenger icons as SVG components
const WhatsAppIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
  </svg>
);

const ViberIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <path d="M11.398.002C9.473.028 5.331.344 3.014 2.467 1.294 4.182.518 6.793.377 10.079c-.141 3.287-.086 9.462 5.656 11.085v2.542s-.039.975.605 1.174c.793.244 1.228-.479 1.987-1.295.414-.449.984-1.109 1.413-1.612 3.89.325 6.882-.418 7.226-.527.793-.252 5.276-.831 6.006-6.786.753-6.14-.357-10.023-2.343-11.771l-.001-.001c-.602-.583-3.003-2.236-8.472-2.416 0 0-.402-.023-.962-.023-.063 0-.126 0-.188.001l.001-.001-.907.053zm.048 1.931c.428-.007.773.013.773.013 4.537.153 6.584 1.406 7.096 1.885 1.618 1.447 2.506 4.867 1.879 9.81-.599 4.873-4.063 5.163-4.741 5.378-.281.089-2.839.715-5.923.512 0 0-2.347 2.83-3.081 3.569-.115.116-.249.161-.338.139-.124-.031-.158-.178-.157-.393l.019-3.86c-4.766-1.349-4.489-6.36-4.379-9.065.116-2.71.732-4.885 2.146-6.292 1.846-1.705 5.205-1.926 6.706-1.696zm-.072 2.444c-.086.003-.171.008-.257.014a.56.56 0 00-.503.426.528.528 0 00.326.621c.059.022.12.036.179.055.227.073.461.121.683.209.55.218.881.665.884 1.263.003.425-.072.848-.148 1.266-.089.491-.172.984-.276 1.472-.045.212-.053.396.1.566.156.174.35.285.575.294.303.012.55-.124.684-.395.087-.176.137-.374.175-.566.116-.578.209-1.16.329-1.737.106-.509.132-1.028.061-1.542-.16-1.159-.821-1.889-1.892-2.283-.457-.168-.934-.258-1.42-.295-.171-.013-.344-.017-.5-.068zm.127 1.558a.473.473 0 00-.465.333.463.463 0 00.229.543c.122.067.266.094.404.122.338.069.582.264.685.598.056.181.073.374.087.563.008.11.027.221.102.302a.446.446 0 00.43.149.47.47 0 00.373-.471c-.012-.337-.017-.68-.095-1.009-.173-.727-.717-1.135-1.464-1.135-.095 0-.191.003-.286.005zm.125 1.59a.438.438 0 00-.423.312c-.038.142.02.277.138.334a.554.554 0 00.476-.001c.106-.049.169-.175.138-.338-.036-.189-.169-.307-.329-.307zm4.796 1.07c-.011.115-.016.201-.028.286-.057.402-.095.81-.177 1.205-.194.937-.713 1.689-1.448 2.303-.472.394-.997.703-1.547.969-.217.105-.432.214-.651.317a.48.48 0 00-.256.361c-.025.17-.02.345-.034.517-.04.5-.076 1-.12 1.5-.009.105-.029.21-.049.314-.041.21-.204.303-.394.225a.696.696 0 01-.179-.12c-.637-.591-1.283-1.174-1.905-1.779-.162-.158-.352-.224-.566-.237-.628-.038-1.248-.127-1.85-.315-.857-.267-1.587-.71-2.171-1.371-.608-.688-.878-1.496-.903-2.395-.011-.403.026-.808.068-1.211.056-.547.226-1.059.477-1.54.381-.728.921-1.309 1.582-1.781.485-.347 1.015-.61 1.585-.802.327-.11.667-.17 1.004-.249.13-.03.263-.04.394-.061.106-.017.211-.038.318-.05.219-.025.439-.051.659-.065.324-.02.649-.03.973-.034.222-.003.444.006.665.019.311.018.621.041.929.078.399.048.789.139 1.172.261.68.217 1.292.548 1.811 1.024.482.443.838.966 1.044 1.585.107.32.171.65.188.985.005.099.006.198.008.299v.041c0 .01-.004.022-.002.033zm-6.161.982c.083.169.183.293.373.299.158.005.295-.042.395-.173.096-.125.139-.269.145-.427.011-.293.018-.585.025-.877.003-.113.002-.227.006-.34a.439.439 0 01.454-.437c.167.001.316.052.42.19.099.131.141.281.147.441.013.345.022.69.036 1.035.007.156.061.296.171.406.214.214.567.227.79.017a.667.667 0 00.198-.433c.025-.346.027-.694.049-1.041.017-.27.182-.457.432-.502a.493.493 0 01.557.303c.046.118.067.248.073.375.016.331.023.663.034.995.008.241.119.413.343.492.227.08.421.017.567-.168.107-.136.152-.296.159-.466.015-.363.025-.726.042-1.089.009-.192.082-.36.238-.477.243-.182.593-.135.78.101.102.129.159.277.17.439.024.379.037.759.06 1.138.021.349.283.605.619.617.345.012.621-.237.652-.582.018-.198.018-.398.028-.597.019-.377.033-.754.06-1.13.024-.338.269-.569.595-.584.342-.016.591.217.63.56.029.259.031.52.045.781.02.374.033.749.059 1.123.023.324.272.569.582.589.333.022.603-.223.633-.569.019-.223.021-.447.035-.67.028-.434.051-.868.089-1.301.026-.298.262-.517.541-.534.308-.019.55.175.596.487.033.223.035.45.049.676.027.432.047.864.081 1.295.025.321.26.561.561.589.319.03.576-.184.623-.51.021-.145.025-.293.034-.439.029-.467.054-.934.086-1.401.016-.242.117-.448.332-.563.309-.165.692-.024.816.313.05.135.075.283.086.428.035.433.057.868.091 1.301.031.4.357.665.729.599.316-.056.519-.32.503-.667-.016-.344-.027-.689-.055-1.032-.043-.527-.147-1.039-.356-1.523-.466-1.082-1.276-1.778-2.415-2.067-.507-.129-1.023-.15-1.541-.107-.631.052-1.224.228-1.765.546-.619.365-1.088.867-1.383 1.52-.209.462-.315.949-.345 1.453-.033.548-.031 1.097-.046 1.645-.003.107 0 .214 0 .363z"/>
  </svg>
);

const TelegramIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.9-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.893-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/>
  </svg>
);

const WeChatIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 0 1 .213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 0 0 .167-.054l1.903-1.114a.864.864 0 0 1 .717-.098 10.16 10.16 0 0 0 2.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178A1.17 1.17 0 0 1 4.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 0 1-1.162 1.178 1.17 1.17 0 0 1-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.34 2.867c-1.797-.052-3.746.512-5.28 1.786-1.72 1.428-2.687 3.72-1.78 6.22.942 2.453 3.666 4.229 6.884 4.229.826 0 1.622-.12 2.361-.336a.722.722 0 0 1 .598.082l1.584.926a.272.272 0 0 0 .14.047c.134 0 .24-.111.24-.247 0-.06-.023-.12-.038-.177l-.327-1.233a.582.582 0 0 1-.023-.156.49.49 0 0 1 .201-.398C23.024 18.48 24 16.82 24 14.98c0-3.21-2.931-5.837-6.656-6.088V8.89c-.135-.007-.27-.018-.406-.032zM13.087 12.2c.535 0 .969.44.969.982a.976.976 0 0 1-.969.983.976.976 0 0 1-.969-.983c0-.542.434-.982.97-.982zm4.827 0c.535 0 .969.44.969.982a.976.976 0 0 1-.97.983.976.976 0 0 1-.968-.983c0-.542.434-.982.969-.982z"/>
  </svg>
);
import axios from 'axios';

// Popular cars data with prices for Belarus
const popularCars = [
  {
    id: 1,
    name: "GEELY MANJARO",
    priceUSD: 19961.47,
    image: "https://customer-assets.emergentagent.com/job_china-motors-by/artifacts/os4c665q_GEELY%20MANJARO.jpg"
  },
  {
    id: 2,
    name: "BMW iX1",
    priceUSD: 24819.83,
    image: "https://customer-assets.emergentagent.com/job_china-motors-by/artifacts/m2yr3tp2_BMW%20IX1.jpg"
  },
  {
    id: 3,
    name: "AVATR 11",
    priceUSD: 30229.94,
    image: "https://customer-assets.emergentagent.com/job_china-motors-by/artifacts/y3bvr5ut_AVATR%2011.jpg"
  },
  {
    id: 4,
    name: "Mazda EZ6",
    priceUSD: 21817.60,
    image: "https://customer-assets.emergentagent.com/job_china-motors-by/artifacts/pidxk08i_Mazda%20EZ6.jpg"
  }
];

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LandingPage = () => {
  const { isAuthenticated, isModerator, isAdmin, user } = useAuth();
  
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
  
  // Popular cars carousel state
  const [currentCarIndex, setCurrentCarIndex] = useState(0);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [hasUserInteracted, setHasUserInteracted] = useState(false);
  
  // Hot deals state
  const [hotDeals, setHotDeals] = useState([]);
  const [hotDealsLoading, setHotDealsLoading] = useState(true);

  // Fetch hot deals
  useEffect(() => {
    const fetchHotDeals = async () => {
      try {
        const response = await axios.get(`${API}/hot-deals?limit=4`);
        setHotDeals(response.data);
      } catch (error) {
        console.error('Error fetching hot deals:', error);
      } finally {
        setHotDealsLoading(false);
      }
    };
    fetchHotDeals();
  }, []);

  // Scroll to bottom of chat only after user sends a message
  useEffect(() => {
    if (hasUserInteracted && chatMessages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, hasUserInteracted]);

  // Auto-rotate carousel
  useEffect(() => {
    const interval = setInterval(() => {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentCarIndex((prev) => (prev + 1) % popularCars.length);
        setIsTransitioning(false);
      }, 300);
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  const goToSlide = useCallback((index) => {
    if (index === currentCarIndex) return;
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentCarIndex(index);
      setIsTransitioning(false);
    }, 300);
  }, [currentCarIndex]);

  const nextSlide = useCallback(() => {
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentCarIndex((prev) => (prev + 1) % popularCars.length);
      setIsTransitioning(false);
    }, 300);
  }, []);

  const prevSlide = useCallback(() => {
    setIsTransitioning(true);
    setTimeout(() => {
      setCurrentCarIndex((prev) => (prev - 1 + popularCars.length) % popularCars.length);
      setIsTransitioning(false);
    }, 300);
  }, []);

  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    setHasUserInteracted(true);
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
              <Link to="/hot-deals" className="text-orange-400 hover:text-orange-300 transition-colors font-medium flex items-center gap-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-orange-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-orange-500"></span>
                </span>
                Горящие
              </Link>
              <Link to="/contractors" className="text-slate-400 hover:text-[#00E5FF] transition-colors font-medium">Подрядчики</Link>
              <a href="#ai-agent" className="text-slate-400 hover:text-white transition-colors">AI Подбор</a>
              <a href="#process" className="text-slate-400 hover:text-white transition-colors">Процесс</a>
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
              {isModerator && (
                <Link to="/moderator">
                  <Button variant="ghost" className="hidden sm:flex text-amber-400 hover:text-amber-300">
                    <Shield size={18} className="mr-2" />
                    Панель модератора
                  </Button>
                </Link>
              )}
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
                <Link to="/catalog">
                  <Button data-testid="hero-catalog-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-semibold px-8 py-6 rounded-sm btn-glow">
                    <Car className="mr-2" size={20} />
                    Каталог авто
                  </Button>
                </Link>
                <a href="#ai-agent">
                  <Button data-testid="hero-cta-btn" variant="outline" className="border-[#27272A] text-white hover:border-[#00E5FF] hover:text-[#00E5FF] px-8 py-6 rounded-sm">
                    <Sparkles className="mr-2" size={20} />
                    AI Подбор
                  </Button>
                </a>
                <Link to="/calculator">
                  <Button data-testid="hero-calc-btn" variant="outline" className="border-[#27272A] text-white hover:border-[#00E5FF] hover:text-[#00E5FF] px-8 py-6 rounded-sm">
                    Калькулятор
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
                {/* Carousel Navigation Arrows */}
                <button
                  onClick={prevSlide}
                  className="absolute left-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 bg-black/50 hover:bg-[#00E5FF]/30 rounded-full flex items-center justify-center transition-all"
                  data-testid="carousel-prev"
                >
                  <ChevronLeft className="text-white" size={24} />
                </button>
                <button
                  onClick={nextSlide}
                  className="absolute right-2 top-1/2 -translate-y-1/2 z-20 w-10 h-10 bg-black/50 hover:bg-[#00E5FF]/30 rounded-full flex items-center justify-center transition-all"
                  data-testid="carousel-next"
                >
                  <ChevronRight className="text-white" size={24} />
                </button>

                {/* Car Image with Fade Animation */}
                <div className={`transition-opacity duration-300 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
                  <img 
                    src={popularCars[currentCarIndex].image}
                    alt={popularCars[currentCarIndex].name}
                    className="w-full h-[400px] object-cover"
                  />
                </div>
                
                <div className="absolute inset-0 bg-gradient-to-t from-[#0B0F14] via-transparent to-transparent" />
                
                {/* Car Info Overlay */}
                <div className={`absolute bottom-0 left-0 right-0 p-6 transition-opacity duration-300 ${isTransitioning ? 'opacity-0' : 'opacity-100'}`}>
                  <p className="text-slate-400 text-sm mb-1">Популярный выбор</p>
                  <p className="text-white text-xl font-semibold mb-2">{popularCars[currentCarIndex].name}</p>
                  <div className="flex items-center gap-2">
                    <span className="text-[#00E5FF] text-2xl font-bold">
                      ${popularCars[currentCarIndex].priceUSD.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </span>
                    <span className="text-slate-500 text-sm">под ключ в Беларуси</span>
                  </div>
                </div>

                {/* Dots Navigation */}
                <div className="absolute bottom-24 left-0 right-0 flex justify-center gap-2 z-20">
                  {popularCars.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => goToSlide(index)}
                      data-testid={`carousel-dot-${index}`}
                      className={`w-2 h-2 rounded-full transition-all duration-300 ${
                        index === currentCarIndex 
                          ? 'bg-[#00E5FF] w-6' 
                          : 'bg-white/30 hover:bg-white/50'
                      }`}
                    />
                  ))}
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

          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mb-12">
            <div className="bg-[#1C2128] border border-[#27272A] rounded-sm p-6 text-center card-hover">
              <div className="w-12 h-12 mx-auto mb-4 bg-[#00E5FF]/10 rounded-full flex items-center justify-center">
                <Phone size={24} className="text-[#00E5FF]" />
              </div>
              <h3 className="text-white font-medium mb-2">Телефон</h3>
              <a href="tel:+37296699557" className="text-slate-400 hover:text-[#00E5FF] transition-colors">
                +375 (29) 669-95-57
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
              <p className="text-slate-400">г. Минск, ул. Червякова, д. 52, пом. 1</p>
            </div>
          </div>

          {/* Messengers Section */}
          <div className="max-w-2xl mx-auto">
            <h3 className="text-white font-semibold text-xl text-center mb-6">Мессенджеры для связи</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <a
                href="https://wa.me/37296699557"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 flex flex-col items-center gap-2 card-hover group"
                data-testid="contact-whatsapp"
              >
                <div className="w-10 h-10 bg-[#25D366]/10 rounded-full flex items-center justify-center text-[#25D366] group-hover:bg-[#25D366] group-hover:text-white transition-colors">
                  <WhatsAppIcon />
                </div>
                <span className="text-slate-400 text-sm group-hover:text-white transition-colors">WhatsApp</span>
              </a>

              <a
                href="viber://chat?number=+37296699557"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 flex flex-col items-center gap-2 card-hover group"
                data-testid="contact-viber"
              >
                <div className="w-10 h-10 bg-[#7360F2]/10 rounded-full flex items-center justify-center text-[#7360F2] group-hover:bg-[#7360F2] group-hover:text-white transition-colors">
                  <ViberIcon />
                </div>
                <span className="text-slate-400 text-sm group-hover:text-white transition-colors">Viber</span>
              </a>

              <a
                href="https://t.me/kiryl_votsintsau"
                target="_blank"
                rel="noopener noreferrer"
                className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 flex flex-col items-center gap-2 card-hover group"
                data-testid="contact-telegram"
              >
                <div className="w-10 h-10 bg-[#0088CC]/10 rounded-full flex items-center justify-center text-[#0088CC] group-hover:bg-[#0088CC] group-hover:text-white transition-colors">
                  <TelegramIcon />
                </div>
                <span className="text-slate-400 text-sm group-hover:text-white transition-colors">Telegram</span>
              </a>

              <div
                className="bg-[#1C2128] border border-[#27272A] rounded-sm p-4 flex flex-col items-center gap-2 card-hover group cursor-pointer"
                onClick={() => {
                  navigator.clipboard.writeText('wxid_fuzh2yfspean12');
                  alert('WeChat ID скопирован: wxid_fuzh2yfspean12');
                }}
                data-testid="contact-wechat"
              >
                <div className="w-10 h-10 bg-[#07C160]/10 rounded-full flex items-center justify-center text-[#07C160] group-hover:bg-[#07C160] group-hover:text-white transition-colors">
                  <WeChatIcon />
                </div>
                <span className="text-slate-400 text-sm group-hover:text-white transition-colors">WeChat</span>
              </div>
            </div>
            <p className="text-slate-500 text-xs text-center mt-3">WeChat ID: wxid_fuzh2yfspean12 (нажмите чтобы скопировать)</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-[#27272A]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <Logo />
            
            {/* Social Media Icons */}
            <div className="flex items-center gap-4">
              <a
                href="https://wa.me/37296699557"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 bg-[#27272A] rounded-full flex items-center justify-center text-slate-400 hover:bg-[#25D366] hover:text-white transition-colors"
                aria-label="WhatsApp"
                data-testid="footer-whatsapp"
              >
                <WhatsAppIcon />
              </a>
              <a
                href="viber://chat?number=+37296699557"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 bg-[#27272A] rounded-full flex items-center justify-center text-slate-400 hover:bg-[#7360F2] hover:text-white transition-colors"
                aria-label="Viber"
                data-testid="footer-viber"
              >
                <ViberIcon />
              </a>
              <a
                href="https://t.me/kiryl_votsintsau"
                target="_blank"
                rel="noopener noreferrer"
                className="w-9 h-9 bg-[#27272A] rounded-full flex items-center justify-center text-slate-400 hover:bg-[#0088CC] hover:text-white transition-colors"
                aria-label="Telegram"
                data-testid="footer-telegram"
              >
                <TelegramIcon />
              </a>
              <div
                onClick={() => {
                  navigator.clipboard.writeText('wxid_fuzh2yfspean12');
                  alert('WeChat ID скопирован: wxid_fuzh2yfspean12');
                }}
                className="w-9 h-9 bg-[#27272A] rounded-full flex items-center justify-center text-slate-400 hover:bg-[#07C160] hover:text-white transition-colors cursor-pointer"
                aria-label="WeChat"
                data-testid="footer-wechat"
              >
                <WeChatIcon />
              </div>
            </div>

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
