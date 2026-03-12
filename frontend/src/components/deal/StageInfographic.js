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
  X,
  ChevronLeft,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Trash2,
  ClipboardCheck
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Stage configuration
const STAGES = [
  { key: 'leasing', label: 'Лизинг', icon: CreditCard, color: 'purple' },
  { key: 'inspection', label: 'Инспекция', icon: Search, color: 'blue' },
  { key: 'export', label: 'Выкуп', icon: FileCheck, color: 'emerald' },
  { key: 'logistics_china', label: 'Доставка (Китай)', icon: Truck, color: 'amber' },
  { key: 'insurance', label: 'Страхование', icon: Shield, color: 'cyan' },
  { key: 'delivery_rb', label: 'Доставка (РБ)', icon: Ship, color: 'indigo' },
  { key: 'customs', label: 'Таможня', icon: FileText, color: 'orange' },
  { key: 'completion', label: 'Завершение', icon: CheckCheck, color: 'green' }
];

const StageInfographic = ({ deal, token, onRefresh }) => {
  const [selectedStage, setSelectedStage] = useState(null);
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [completing, setCompleting] = useState(false);
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
      const response = await axios.get(`${API}/deals/${deal.id}/unread-counts`, { headers });
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
        axios.get(`${API}/deals/${deal.id}/stages/${selectedStage}/messages`, { headers }),
        axios.get(`${API}/deals/${deal.id}/stages/${selectedStage}/files`, { headers })
      ]);
      setMessages(messagesRes.data);
      setFiles(filesRes.data);
      
      // Update unread counts after fetching
      fetchUnreadCounts();
    } catch (error) {
      console.error('Error fetching stage data:', error);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedStage) return;
    
    setSending(true);
    try {
      await axios.post(`${API}/deals/${deal.id}/stages/${selectedStage}/messages`, {
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
      await axios.post(`${API}/deals/${deal.id}/stages/${selectedStage}/files`, formData, {
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
      const response = await axios.get(
        `${API}/deals/${deal.id}/files/${fileId}/download`,
        { headers, responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast.error('Ошибка скачивания файла');
    }
  };

  const getStageStatus = (stageKey) => {
    const stageData = deal?.stages?.[stageKey];
    if (!stageData) return 'pending';
    return stageData.status || 'pending';
  };

  const getStageContractor = (stageKey) => {
    const stageData = deal?.stages?.[stageKey];
    return stageData?.contractor_name || null;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'paid':
        return 'bg-emerald-500';
      case 'approved':
        return 'bg-blue-500';
      case 'awaiting_approval':
        return 'bg-amber-500';
      case 'skipped':
        return 'bg-slate-500';
      default:
        return 'bg-slate-600';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed':
      case 'paid':
        return 'Завершён';
      case 'approved':
        return 'Подтверждён';
      case 'awaiting_approval':
        return 'На модерации';
      case 'skipped':
        return 'Пропущен';
      case 'pending':
        return 'Ожидает';
      default:
        return status;
    }
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
  const stageContractor = selectedStage ? getStageContractor(selectedStage) : null;

  return (
    <div className="space-y-4" data-testid="stage-infographic">
      {/* Horizontal Timeline */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4 overflow-x-auto">
        <div className="flex items-center justify-between min-w-[800px] relative">
          {/* Progress Line */}
          <div className="absolute top-1/2 left-0 right-0 h-1 bg-[#27272A] -translate-y-1/2 z-0" />
          
          {STAGES.map((stage, index) => {
            const status = getStageStatus(stage.key);
            const contractor = getStageContractor(stage.key);
            const unread = unreadCounts[stage.key] || 0;
            const Icon = stage.icon;
            const isSelected = selectedStage === stage.key;
            
            return (
              <div key={stage.key} className="relative z-10 flex flex-col items-center">
                {/* Stage Circle */}
                <button
                  onClick={() => setSelectedStage(stage.key)}
                  data-testid={`stage-${stage.key}`}
                  className={`relative w-14 h-14 rounded-full flex items-center justify-center transition-all ${
                    isSelected 
                      ? 'bg-[#00E5FF] text-black scale-110 shadow-lg shadow-[#00E5FF]/30' 
                      : status === 'completed' || status === 'paid'
                        ? 'bg-emerald-500 text-white'
                        : status === 'approved'
                          ? 'bg-blue-500 text-white'
                          : status === 'awaiting_approval'
                            ? 'bg-amber-500 text-black'
                            : status === 'skipped'
                              ? 'bg-slate-600 text-slate-300'
                              : 'bg-[#27272A] text-slate-400 hover:bg-[#3f3f46]'
                  }`}
                >
                  <Icon size={24} />
                  
                  {/* Unread Badge */}
                  {unread > 0 && (
                    <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                      {unread}
                    </span>
                  )}
                </button>
                
                {/* Stage Label */}
                <div className="mt-2 text-center">
                  <p className={`text-xs font-medium ${isSelected ? 'text-[#00E5FF]' : 'text-white'}`}>
                    {stage.label}
                  </p>
                  {contractor && (
                    <p className="text-[10px] text-slate-400 mt-0.5 max-w-[80px] truncate">
                      {contractor}
                    </p>
                  )}
                  <span className={`inline-block mt-1 px-2 py-0.5 rounded-full text-[10px] ${
                    status === 'completed' || status === 'paid' ? 'bg-emerald-500/20 text-emerald-400' :
                    status === 'approved' ? 'bg-blue-500/20 text-blue-400' :
                    status === 'awaiting_approval' ? 'bg-amber-500/20 text-amber-400' :
                    status === 'skipped' ? 'bg-slate-500/20 text-slate-400' :
                    'bg-slate-700 text-slate-400'
                  }`}>
                    {getStatusLabel(status)}
                  </span>
                </div>
                
                {/* Connector Line */}
                {index < STAGES.length - 1 && (
                  <div className={`absolute top-7 left-14 h-1 z-0 ${
                    status === 'completed' || status === 'paid' ? 'bg-emerald-500' : 'bg-[#27272A]'
                  }`} style={{ width: 'calc(100vw / 8 - 56px)', minWidth: '60px', pointerEvents: 'none' }} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Stage Panel */}
      <Dialog open={!!selectedStage} onOpenChange={() => setSelectedStage(null)}>
        <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-3">
              {selectedStageInfo && (
                <>
                  <div className={`w-10 h-10 rounded-lg bg-[#00E5FF]/10 flex items-center justify-center`}>
                    <selectedStageInfo.icon size={20} className="text-[#00E5FF]" />
                  </div>
                  <div>
                    <span>{selectedStageInfo.label}</span>
                    {stageContractor && (
                      <p className="text-sm text-slate-400 font-normal mt-0.5">
                        Подрядчик: {stageContractor}
                      </p>
                    )}
                  </div>
                </>
              )}
            </DialogTitle>
          </DialogHeader>

          {!stageContractor ? (
            <div className="flex-1 flex flex-col items-center justify-center py-12">
              <AlertCircle size={48} className="text-slate-600 mb-4" />
              <p className="text-slate-400 text-center">
                Подрядчик ещё не назначен на этот этап
              </p>
              <p className="text-slate-500 text-sm mt-1">
                Выберите подрядчика в разделе "Авто для сделки"
              </p>
            </div>
          ) : (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Files Section */}
              <div className="border-b border-[#27272A] p-4">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-slate-300 flex items-center gap-2">
                    <Paperclip size={16} />
                    Файлы этапа ({files.length})
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
                      className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                    >
                      {uploading ? <Loader2 size={14} className="animate-spin mr-1" /> : <Upload size={14} className="mr-1" />}
                      Загрузить
                    </Button>
                  </div>
                </div>
                
                {files.length > 0 ? (
                  <div className="space-y-2 max-h-[120px] overflow-y-auto">
                    {files.map(file => (
                      <div key={file.id} className="flex items-center gap-2 p-2 bg-[#0B0F14] rounded-lg">
                        {getFileIcon(file.category)}
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-white truncate">{file.original_name}</p>
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span>{formatFileSize(file.size)}</span>
                            <span>•</span>
                            <span className={file.uploader_type === 'contractor' ? 'text-purple-400' : 'text-[#00E5FF]'}>
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
                    Чат с подрядчиком
                  </h4>
                </div>
                
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-3 min-h-[200px] max-h-[300px]">
                  {loading && messages.length === 0 ? (
                    <div className="flex justify-center py-8">
                      <Loader2 className="animate-spin text-[#00E5FF]" size={24} />
                    </div>
                  ) : messages.length === 0 ? (
                    <div className="text-center py-8">
                      <MessageSquare size={32} className="mx-auto mb-2 text-slate-600" />
                      <p className="text-slate-400 text-sm">Нет сообщений</p>
                      <p className="text-slate-500 text-xs">Начните общение с подрядчиком</p>
                    </div>
                  ) : (
                    messages.map(msg => (
                      <div
                        key={msg.id}
                        className={`flex ${msg.sender_type === 'client' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div className={`max-w-[80%] rounded-lg p-3 ${
                          msg.sender_type === 'client'
                            ? 'bg-[#00E5FF]/10 border border-[#00E5FF]/30'
                            : 'bg-purple-500/10 border border-purple-500/30'
                        }`}>
                          <div className="flex items-center gap-2 mb-1">
                            {msg.sender_type === 'client' ? (
                              <User size={12} className="text-[#00E5FF]" />
                            ) : (
                              <Building2 size={12} className="text-purple-400" />
                            )}
                            <span className={`text-xs font-medium ${
                              msg.sender_type === 'client' ? 'text-[#00E5FF]' : 'text-purple-400'
                            }`}>
                              {msg.sender_name}
                            </span>
                            <span className="text-xs text-slate-500">
                              {new Date(msg.created_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                          <p className="text-white text-sm whitespace-pre-wrap">{msg.content}</p>
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
                      className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                    >
                      {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default StageInfographic;
