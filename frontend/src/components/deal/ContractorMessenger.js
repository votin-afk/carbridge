import { useState, useEffect, useRef } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import {
  CreditCard,
  Search,
  FileCheck,
  Truck,
  Shield,
  Ship,
  FileText,
  CheckCheck,
  MessageSquare,
  Paperclip,
  Send,
  Upload,
  Download,
  Loader2,
  User,
  Building2,
  File,
  Image,
  Video,
  Car,
  Clock,
  CheckCircle2,
  AlertCircle,
  SendHorizontal
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Stage configuration
const STAGES = [
  { key: 'leasing', label: 'Лизинг', icon: CreditCard },
  { key: 'inspection', label: 'Инспекция', icon: Search },
  { key: 'export', label: 'Выкуп', icon: FileCheck },
  { key: 'logistics_china', label: 'Доставка (Китай)', icon: Truck },
  { key: 'insurance', label: 'Страхование', icon: Shield },
  { key: 'delivery_rb', label: 'Доставка (РБ)', icon: Ship },
  { key: 'customs', label: 'Таможня', icon: FileText },
  { key: 'completion', label: 'Завершение', icon: CheckCheck }
];

const ContractorMessenger = ({ deal, token, myStages = [], onRefresh }) => {
  const [selectedStage, setSelectedStage] = useState(null);
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [unreadCounts, setUnreadCounts] = useState({});
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (deal?.id) {
      fetchUnreadCounts();
    }
  }, [deal?.id]);

  useEffect(() => {
    if (selectedStage && deal?.id) {
      fetchStageData();
      const interval = setInterval(fetchStageData, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedStage, deal?.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchUnreadCounts = async () => {
    try {
      const response = await axios.get(`${API}/contractor/deals/${deal.id}/unread-counts`, { headers });
      setUnreadCounts(response.data);
    } catch (error) {
      console.error('Error fetching unread counts:', error);
    }
  };

  const fetchStageData = async () => {
    if (!selectedStage) return;
    setLoading(true);
    try {
      const [messagesRes, filesRes] = await Promise.all([
        axios.get(`${API}/contractor/deals/${deal.id}/stages/${selectedStage}/messages`, { headers }),
        axios.get(`${API}/contractor/deals/${deal.id}/files`, { headers }).then(res => ({
          data: res.data.filter(f => f.stage_key === selectedStage)
        }))
      ]);
      setMessages(messagesRes.data);
      setFiles(filesRes.data);
      fetchUnreadCounts();
    } catch (error) {
      console.error('Error fetching stage data:', error);
      if (error.response?.status === 403) {
        toast.error('Вы не назначены на этот этап');
        setSelectedStage(null);
      }
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedStage) return;
    
    setSending(true);
    try {
      await axios.post(`${API}/contractor/deals/${deal.id}/stages/${selectedStage}/messages`, {
        content: newMessage
      }, { headers });
      
      setNewMessage('');
      fetchStageData();
    } catch (error) {
      toast.error('Ошибка отправки сообщения');
    } finally {
      setSending(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedStage) return;
    
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Файл слишком большой (максимум 50MB)');
      return;
    }
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await axios.post(`${API}/contractor/deals/${deal.id}/stages/${selectedStage}/files`, formData, {
        headers: { ...headers, 'Content-Type': 'multipart/form-data' }
      });
      toast.success('Файл загружен');
      fetchStageData();
    } catch (error) {
      toast.error('Ошибка загрузки файла');
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const downloadFile = async (fileId, filename) => {
    try {
      const response = await fetch(
        `${API}/contractor/deals/${deal.id}/files/${fileId}/download`,
        { headers: { 'Authorization': `Bearer ${token}` } }
      );
      if (!response.ok) throw new Error('Download failed');
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename || 'file';
      document.body.appendChild(a);
      a.click();
      setTimeout(() => {
        URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }, 1000);
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Ошибка скачивания файла');
    }
  };

  const getStageStatus = (stageKey) => {
    const stageData = deal?.stages?.[stageKey];
    if (!stageData) return 'pending';
    return stageData.status || 'pending';
  };

  const isMyStage = (stageKey) => {
    return myStages.some(s => s.stage_key === stageKey);
  };

  const getFileIcon = (category) => {
    switch (category) {
      case 'photo': return <Image size={16} className="text-emerald-400" />;
      case 'video': return <Video size={16} className="text-purple-400" />;
      default: return <File size={16} className="text-blue-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const selectedStageInfo = STAGES.find(s => s.key === selectedStage);

  // Filter to show only stages assigned to this contractor
  const myStageKeys = myStages.map(s => s.stage_key);

  if (myStageKeys.length === 0) {
    return (
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-8 text-center">
        <AlertCircle size={48} className="mx-auto mb-4 text-slate-600" />
        <p className="text-slate-400">Вы не назначены ни на один этап этой сделки</p>
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="contractor-messenger">
      {/* My Stages Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {STAGES.filter(stage => isMyStage(stage.key)).map(stage => {
          const status = getStageStatus(stage.key);
          const unread = unreadCounts[stage.key] || 0;
          const Icon = stage.icon;
          const isSelected = selectedStage === stage.key;
          
          return (
            <button
              key={stage.key}
              onClick={() => setSelectedStage(stage.key)}
              data-testid={`contractor-stage-${stage.key}`}
              className={`relative p-4 rounded-lg border transition-all text-left ${
                isSelected 
                  ? 'bg-emerald-500/10 border-emerald-500' 
                  : 'bg-[#15191E] border-[#27272A] hover:border-emerald-500/50'
              }`}
            >
              <div className="flex items-center gap-3 mb-2">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  isSelected ? 'bg-emerald-500/20' : 'bg-[#27272A]'
                }`}>
                  <Icon size={20} className={isSelected ? 'text-emerald-400' : 'text-slate-400'} />
                </div>
                {/* Unread Badge */}
                {unread > 0 && (
                  <span className="absolute top-2 right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unread}
                  </span>
                )}
              </div>
              <p className={`text-sm font-medium ${isSelected ? 'text-emerald-400' : 'text-white'}`}>
                {stage.label}
              </p>
              <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-xs ${
                status === 'completed' || status === 'paid' ? 'bg-emerald-500/20 text-emerald-400' :
                status === 'approved' ? 'bg-blue-500/20 text-blue-400' :
                status === 'awaiting_approval' ? 'bg-amber-500/20 text-amber-400' :
                'bg-slate-700 text-slate-400'
              }`}>
                {status === 'completed' || status === 'paid' ? 'Завершён' :
                 status === 'approved' ? 'Подтверждён' :
                 status === 'awaiting_approval' ? 'На модерации' :
                 'В работе'}
              </span>
            </button>
          );
        })}
      </div>

      {/* Stage Chat Panel */}
      <Dialog open={!!selectedStage} onOpenChange={() => setSelectedStage(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {selectedStageInfo && (
                <>
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <selectedStageInfo.icon size={20} className="text-emerald-400" />
                  </div>
                  <div>
                    <span>{selectedStageInfo.label}</span>
                    <p className="text-sm text-slate-400 font-normal mt-0.5">
                      Клиент: {deal.client?.name || deal.client?.email || 'Неизвестно'}
                    </p>
                  </div>
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 flex flex-col overflow-hidden">
            {/* Files Section */}
            <div className="border-b border-[#27272A] p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <Paperclip size={16} />
                  Файлы ({files.length})
                </h4>
                <div>
                  <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <Button
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="bg-emerald-500 hover:bg-emerald-600 text-white"
                  >
                    {uploading ? <Loader2 size={14} className="animate-spin mr-1" /> : <Upload size={14} className="mr-1" />}
                    Загрузить
                  </Button>
                </div>
              </div>
              
              {files.length > 0 ? (
                <div className="space-y-2 max-h-[100px] overflow-y-auto">
                  {files.map(file => (
                    <div key={file.id} className="flex items-center gap-2 p-2 bg-[#0B0F14] rounded-lg">
                      {getFileIcon(file.category)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white truncate">{file.original_name}</p>
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                          <span>{formatFileSize(file.size)}</span>
                          <span>•</span>
                          <span className={file.uploader_type === 'client' ? 'text-[#00E5FF]' : 'text-emerald-400'}>
                            {file.uploader_name}
                          </span>
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => downloadFile(file.id, file.original_name)}
                        className="h-8 w-8 p-0"
                      >
                        <Download size={14} />
                      </Button>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-sm">Нет файлов</p>
              )}
            </div>

            {/* Chat Section */}
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="p-3 border-b border-[#27272A]">
                <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                  <MessageSquare size={16} />
                  Чат с клиентом
                </h4>
              </div>
              
              {/* Messages */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[300px]">
                {loading && messages.length === 0 ? (
                  <div className="flex justify-center py-8">
                    <Loader2 className="animate-spin text-emerald-400" size={24} />
                  </div>
                ) : messages.length === 0 ? (
                  <div className="text-center py-8">
                    <MessageSquare size={32} className="mx-auto mb-2 text-slate-600" />
                    <p className="text-slate-400 text-sm">Нет сообщений</p>
                    <p className="text-slate-500 text-xs">Начните общение с клиентом</p>
                  </div>
                ) : (
                  messages.map(msg => (
                    <div
                      key={msg.id}
                      className={`flex ${msg.sender_type === 'contractor' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div className={`max-w-[80%] rounded-lg p-3 ${
                        msg.sender_type === 'contractor'
                          ? 'bg-emerald-500/10 border border-emerald-500/30'
                          : 'bg-[#00E5FF]/10 border border-[#00E5FF]/30'
                      }`}>
                        <div className="flex items-center gap-2 mb-1">
                          {msg.sender_type === 'contractor' ? (
                            <Building2 size={12} className="text-emerald-400" />
                          ) : (
                            <User size={12} className="text-[#00E5FF]" />
                          )}
                          <span className={`text-xs font-medium ${
                            msg.sender_type === 'contractor' ? 'text-emerald-400' : 'text-[#00E5FF]'
                          }`}>
                            {msg.sender_name}
                          </span>
                          {msg.source === 'telegram' && (
                            <span className="text-xs text-blue-400" title="Отправлено из Telegram">
                              <SendHorizontal size={10} className="inline" /> TG
                            </span>
                          )}
                          <span className="text-xs text-slate-500">
                            {new Date(msg.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                        {msg.content && <p className="text-white text-sm whitespace-pre-wrap">{msg.content}</p>}
                        {msg.file_ids && msg.file_ids.length > 0 && (
                          <div className="mt-1 space-y-1">
                            {msg.file_ids.map(fid => (
                              <button
                                key={fid}
                                onClick={() => downloadFile(fid, `file_${fid}`)}
                                className="flex items-center gap-1 text-xs text-[#00E5FF] hover:underline"
                              >
                                <Paperclip size={10} /> Скачать файл
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Message Input */}
              <div className="p-3 border-t border-[#27272A]">
                <div className="flex gap-2">
                  <Input
                    value={newMessage}
                    onChange={(e) => setNewMessage(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                    placeholder="Напишите сообщение..."
                    className="flex-1 bg-[#0B0F14] border-[#27272A]"
                  />
                  <Button
                    onClick={sendMessage}
                    disabled={sending || !newMessage.trim()}
                    className="bg-emerald-500 hover:bg-emerald-600 text-white"
                  >
                    {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ContractorMessenger;
