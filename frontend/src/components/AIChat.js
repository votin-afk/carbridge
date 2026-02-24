import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2, Bot, User } from 'lucide-react';
import { Button } from '../components/ui/button';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AIChat = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Привет! Я AI-ассистент CARBRIDGE. Помогу подобрать автомобиль из Китая, расскажу о процессе покупки и растаможки. Чем могу помочь?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

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
      const response = await axios.post(`${API}/chat`, {
        message: userMessage,
        session_id: sessionId
      });
      
      setSessionId(response.data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: response.data.response }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Извините, произошла ошибка. Попробуйте позже или свяжитесь с нами напрямую.' 
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Chat Button */}
      <button
        data-testid="ai-chat-toggle"
        onClick={() => setIsOpen(!isOpen)}
        className={`fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center transition-all duration-300 ${
          isOpen 
            ? 'bg-[#27272A] text-white rotate-90' 
            : 'bg-[#00E5FF] text-black hover:bg-[#22D3EE] pulse-cyan'
        }`}
      >
        {isOpen ? <X size={24} /> : <MessageCircle size={24} />}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div 
          data-testid="ai-chat-window"
          className="fixed bottom-24 right-6 z-50 w-[380px] max-w-[calc(100vw-48px)] h-[500px] max-h-[calc(100vh-140px)] bg-[#0B0F14] border border-[#27272A] rounded-lg shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-[#27272A] bg-[#15191E] flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#00E5FF]/10 flex items-center justify-center">
              <Bot className="w-5 h-5 text-[#00E5FF]" />
            </div>
            <div>
              <h3 className="font-semibold text-white text-sm">AI-Ассистент</h3>
              <p className="text-xs text-slate-400">Подбор авто из Китая</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center ${
                  msg.role === 'user' ? 'bg-[#27272A]' : 'bg-[#00E5FF]/10'
                }`}>
                  {msg.role === 'user' ? (
                    <User className="w-4 h-4 text-slate-400" />
                  ) : (
                    <Bot className="w-4 h-4 text-[#00E5FF]" />
                  )}
                </div>
                <div className={`max-w-[80%] px-4 py-3 text-sm leading-relaxed ${
                  msg.role === 'user' 
                    ? 'chat-bubble-user text-white' 
                    : 'chat-bubble-ai text-slate-200'
                }`}>
                  {msg.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-[#00E5FF]/10 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-[#00E5FF]" />
                </div>
                <div className="chat-bubble-ai px-4 py-3">
                  <Loader2 className="w-4 h-4 text-[#00E5FF] animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="p-4 border-t border-[#27272A] bg-[#15191E]">
            <div className="flex gap-2">
              <input
                data-testid="ai-chat-input"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Напишите сообщение..."
                className="flex-1 bg-[#0B0F14] border border-[#27272A] rounded-lg px-4 py-2 text-sm text-white placeholder:text-slate-500 focus:border-[#00E5FF] focus:ring-1 focus:ring-[#00E5FF]/20"
                disabled={loading}
              />
              <Button
                data-testid="ai-chat-send"
                onClick={sendMessage}
                disabled={!input.trim() || loading}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black px-4 rounded-lg disabled:opacity-50"
              >
                <Send size={18} />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default AIChat;
