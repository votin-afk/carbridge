import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { 
  Bot, 
  Send, 
  User, 
  Loader2,
  Sparkles,
  Car,
  Calculator,
  FileText,
  HelpCircle,
  Trash2,
  RotateCcw
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const AIAssistant = () => {
  const { token, user } = useAuth();
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Здравствуйте${user?.name ? `, ${user.name}` : ''}! 👋\n\nЯ ваш персональный ИИ-ассистент по импорту автомобилей из Китая. Я могу помочь вам с:\n\n• Подбором автомобиля по вашим критериям\n• Расчётом стоимости растаможки\n• Объяснением процесса покупки\n• Консультацией по документам\n• Ответами на любые вопросы\n\nЧем могу помочь?`
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const headers = { Authorization: `Bearer ${token}` };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      const response = await axios.post(`${API}/api/chat`, {
        message: userMessage,
        context: 'dashboard_assistant'
      }, { headers });

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: response.data.response || response.data.message || 'Извините, не удалось получить ответ.'
      }]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Извините, произошла ошибка при обработке запроса. Попробуйте ещё раз.'
      }]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: `Чат очищен. Чем могу помочь?`
    }]);
  };

  const quickQuestions = [
    { icon: Car, text: 'Как выбрать авто из Китая?' },
    { icon: Calculator, text: 'Сколько стоит растаможка?' },
    { icon: FileText, text: 'Какие документы нужны?' },
    { icon: HelpCircle, text: 'Как проверить авто?' }
  ];

  const handleQuickQuestion = (question) => {
    setInput(question);
    setTimeout(() => sendMessage(), 100);
  };

  return (
    <div className="h-[calc(100vh-180px)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-[#00E5FF] to-purple-500 rounded-full flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">ИИ-Ассистент</h1>
            <p className="text-slate-400 text-sm">Персональный помощник по импорту авто</p>
          </div>
        </div>
        <Button
          onClick={clearChat}
          variant="outline"
          size="sm"
          className="border-[#27272A] text-slate-400 hover:text-white"
        >
          <RotateCcw size={16} className="mr-2" />
          Очистить чат
        </Button>
      </div>

      {/* Chat Container */}
      <div className="flex-1 bg-[#15191E] border border-[#27272A] rounded-lg flex flex-col overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user' 
                  ? 'bg-[#00E5FF]/20' 
                  : 'bg-gradient-to-br from-[#00E5FF] to-purple-500'
              }`}>
                {message.role === 'user' ? (
                  <User size={16} className="text-[#00E5FF]" />
                ) : (
                  <Sparkles size={16} className="text-white" />
                )}
              </div>
              <div className={`max-w-[80%] rounded-lg p-3 ${
                message.role === 'user'
                  ? 'bg-[#00E5FF]/10 text-white'
                  : 'bg-[#0B0F14] text-slate-300'
              }`}>
                <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#00E5FF] to-purple-500 flex items-center justify-center">
                <Sparkles size={16} className="text-white" />
              </div>
              <div className="bg-[#0B0F14] rounded-lg p-3">
                <div className="flex items-center gap-2 text-slate-400">
                  <Loader2 size={16} className="animate-spin" />
                  <span className="text-sm">Думаю...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Quick Questions */}
        {messages.length === 1 && (
          <div className="px-4 pb-4">
            <p className="text-slate-500 text-xs mb-2">Быстрые вопросы:</p>
            <div className="flex flex-wrap gap-2">
              {quickQuestions.map((q, index) => (
                <button
                  key={index}
                  onClick={() => handleQuickQuestion(q.text)}
                  className="flex items-center gap-2 px-3 py-1.5 bg-[#0B0F14] border border-[#27272A] rounded-full text-slate-400 text-sm hover:border-[#00E5FF]/50 hover:text-[#00E5FF] transition-colors"
                >
                  <q.icon size={14} />
                  {q.text}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-[#27272A]">
          <form onSubmit={(e) => { e.preventDefault(); sendMessage(); }} className="flex gap-3">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Введите ваш вопрос..."
              className="flex-1 bg-[#0B0F14] border-[#27272A] text-white"
              disabled={loading}
            />
            <Button
              type="submit"
              disabled={!input.trim() || loading}
              className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {loading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Send size={18} />
              )}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AIAssistant;
