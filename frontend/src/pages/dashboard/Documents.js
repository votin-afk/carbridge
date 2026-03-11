import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useLocation } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui/tabs";
import { 
  FileText, 
  Download,
  Eye,
  Folder,
  File,
  FileImage,
  FilePlus,
  MessageSquare,
  Send,
  Upload,
  Paperclip,
  Car,
  Image,
  Video,
  X,
  Loader2,
  Clock,
  CheckCircle2,
  User,
  Building2,
  Trash2,
  Headphones,
  Scale,
  Phone,
  Mail,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Stage labels
const stageLabels = {
  leasing: 'Лизинг',
  inspection: 'Инспекция авто',
  export: 'Выкуп и экспорт',
  logistics_china: 'Доставка до порта (Китай)',
  insurance: 'Страхование авто',
  delivery_rb: 'Доставка в Беларусь',
  customs: 'Таможенное оформление',
  completion: 'Завершение сделки'
};

const Documents = () => {
  const { token, user } = useAuth();
  const location = useLocation();
  const [deals, setDeals] = useState([]);
  const [selectedDeal, setSelectedDeal] = useState(null);
  const [messages, setMessages] = useState([]);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [newMessage, setNewMessage] = useState('');
  const [uploadDialog, setUploadDialog] = useState(false);
  const [selectedStage, setSelectedStage] = useState('all');
  const [activeTab, setActiveTab] = useState('files'); // 'files' or 'chat'
  
  // Help requests state
  const [mainTab, setMainTab] = useState('deals'); // 'deals', 'manager_help', 'legal_help'
  const [helpRequests, setHelpRequests] = useState([]);
  const [selectedHelpRequest, setSelectedHelpRequest] = useState(null);
  const [helpMessages, setHelpMessages] = useState([]);
  const [newHelpMessage, setNewHelpMessage] = useState('');
  const [sendingHelp, setSendingHelp] = useState(false);
  
  // Legal help state
  const [legalRequests, setLegalRequests] = useState([]);
  const [selectedLegalRequest, setSelectedLegalRequest] = useState(null);
  
  const messagesEndRef = useRef(null);
  const helpMessagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchDeals();
    fetchHelpRequests();
    fetchLegalRequests();
    
    // Check if we need to open help section
    if (location.state?.openHelpSection) {
      setMainTab('manager_help');
    }
  }, [location.state]);

  useEffect(() => {
    if (selectedDeal) {
      fetchDealData();
      // Polling for new messages every 5 seconds
      const interval = setInterval(fetchDealData, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedDeal]);

  useEffect(() => {
    if (selectedHelpRequest) {
      fetchHelpRequestMessages();
      const interval = setInterval(fetchHelpRequestMessages, 5000);
      return () => clearInterval(interval);
    }
  }, [selectedHelpRequest]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    helpMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [helpMessages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchDeals = async () => {
    try {
      const response = await axios.get(`${API}/deals`, { headers });
      setDeals(response.data.filter(d => d.status === 'active'));
    } catch (error) {
      console.error('Error fetching deals:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchHelpRequests = async () => {
    try {
      const response = await axios.get(`${API}/help-requests`, { headers });
      setHelpRequests(response.data.filter(r => r.request_type === 'car_selection' || r.request_type === 'general'));
    } catch (error) {
      console.error('Error fetching help requests:', error);
    }
  };

  const fetchLegalRequests = async () => {
    try {
      const response = await axios.get(`${API}/help-requests`, { headers });
      setLegalRequests(response.data.filter(r => r.request_type === 'legal'));
    } catch (error) {
      console.error('Error fetching legal requests:', error);
    }
  };

  const fetchHelpRequestMessages = async () => {
    if (!selectedHelpRequest) return;
    try {
      const response = await axios.get(`${API}/help-requests/${selectedHelpRequest.id}`, { headers });
      setHelpMessages(response.data.messages || []);
    } catch (error) {
      console.error('Error fetching help messages:', error);
    }
  };

  const sendHelpMessage = async () => {
    if (!newHelpMessage.trim() || !selectedHelpRequest) return;
    
    setSendingHelp(true);
    try {
      await axios.post(`${API}/help-requests/${selectedHelpRequest.id}/messages`, {
        content: newHelpMessage
      }, { headers });
      
      setNewHelpMessage('');
      fetchHelpRequestMessages();
    } catch (error) {
      toast.error('Ошибка отправки сообщения');
    } finally {
      setSendingHelp(false);
    }
  };

  const requestCallback = async () => {
    try {
      await axios.post(`${API}/callback-request`, {
        request_type: 'manager_callback',
        help_request_id: selectedHelpRequest?.id,
        phone: user?.phone
      }, { headers });
      toast.success('Запрос на звонок отправлен! Менеджер свяжется с вами в ближайшее время.');
    } catch (error) {
      toast.error('Ошибка при отправке запроса');
    }
  };

  const fetchDealData = async () => {
    if (!selectedDeal) return;
    
    try {
      const [messagesRes, filesRes] = await Promise.all([
        axios.get(`${API}/deals/${selectedDeal.id}/messages`, { headers }),
        axios.get(`${API}/deals/${selectedDeal.id}/files`, { headers })
      ]);
      setMessages(messagesRes.data);
      setFiles(filesRes.data);
    } catch (error) {
      console.error('Error fetching deal data:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedDeal) return;
    
    setSending(true);
    try {
      await axios.post(`${API}/deals/${selectedDeal.id}/messages`, {
        content: newMessage,
        stage_key: selectedStage !== 'all' ? selectedStage : null
      }, { headers });
      
      setNewMessage('');
      fetchDealData();
    } catch (error) {
      toast.error('Ошибка отправки сообщения');
    } finally {
      setSending(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !selectedDeal) return;
    
    // Check file size (50MB limit)
    if (file.size > 50 * 1024 * 1024) {
      toast.error('Файл слишком большой (максимум 50MB)');
      return;
    }
    
    setUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('stage_key', selectedStage !== 'all' ? selectedStage : '');
    formData.append('file_type', 'document');
    formData.append('description', '');
    
    try {
      await axios.post(`${API}/deals/${selectedDeal.id}/files`, formData, {
        headers: {
          ...headers,
          'Content-Type': 'multipart/form-data'
        }
      });
      
      toast.success('Файл загружен');
      fetchDealData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка загрузки файла');
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const downloadFile = async (fileId, filename) => {
    try {
      const response = await axios.get(
        `${API}/deals/${selectedDeal.id}/files/${fileId}/download`,
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

  const deleteFile = async (fileId) => {
    if (!window.confirm('Удалить файл?')) return;
    
    try {
      await axios.delete(`${API}/deals/${selectedDeal.id}/files/${fileId}`, { headers });
      toast.success('Файл удалён');
      fetchDealData();
    } catch (error) {
      toast.error('Ошибка удаления файла');
    }
  };

  const getFileIcon = (category) => {
    switch (category) {
      case 'photo': return <Image size={20} className="text-emerald-400" />;
      case 'video': return <Video size={20} className="text-purple-400" />;
      case 'document': return <FileText size={20} className="text-blue-400" />;
      default: return <File size={20} className="text-slate-400" />;
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const filteredFiles = selectedStage === 'all' 
    ? files 
    : files.filter(f => f.stage_key === selectedStage);

  const filteredMessages = selectedStage === 'all'
    ? messages
    : messages.filter(m => m.stage_key === selectedStage || !m.stage_key);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="documents-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Документы и чат</h1>
        <p className="text-slate-400 mt-1">Обмен документами и сообщениями по сделкам</p>
      </div>

      <div className="grid lg:grid-cols-3 gap-6">
        {/* Deals List */}
        <div className="lg:col-span-1 space-y-3">
          <h3 className="text-white font-medium">Мои сделки</h3>
          
          {deals.length === 0 ? (
            <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 text-center">
              <Car size={48} className="mx-auto mb-3 text-slate-600" />
              <p className="text-slate-400">Нет активных сделок</p>
            </div>
          ) : (
            deals.map(deal => (
              <div
                key={deal.id}
                onClick={() => setSelectedDeal(deal)}
                className={`p-4 rounded-lg border cursor-pointer transition-all ${
                  selectedDeal?.id === deal.id
                    ? 'bg-[#00E5FF]/10 border-[#00E5FF]'
                    : 'bg-[#15191E] border-[#27272A] hover:border-[#00E5FF]/50'
                }`}
              >
                <div className="flex items-center gap-3">
                  {deal.car_info?.image_url ? (
                    <img src={deal.car_info.image_url} alt="" className="w-12 h-9 object-cover rounded" />
                  ) : (
                    <div className="w-12 h-9 bg-[#0B0F14] rounded flex items-center justify-center">
                      <Car size={18} className="text-slate-600" />
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">
                      {deal.car_info?.brand} {deal.car_info?.model}
                    </p>
                    <p className="text-slate-500 text-xs">
                      {deal.contractor?.name || 'Нет подрядчика'}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Deal Content */}
        <div className="lg:col-span-2">
          {!selectedDeal ? (
            <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
              <MessageSquare size={64} className="mx-auto mb-4 text-slate-600" />
              <p className="text-slate-400">Выберите сделку для просмотра документов и чата</p>
            </div>
          ) : (
            <div className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden">
              {/* Deal Header */}
              <div className="p-4 border-b border-[#27272A] flex items-center justify-between">
                <div>
                  <h3 className="text-white font-semibold">
                    {selectedDeal.car_info?.brand} {selectedDeal.car_info?.model}
                  </h3>
                  <p className="text-slate-400 text-sm">
                    Сделка #{selectedDeal.id?.slice(0, 8)}
                  </p>
                </div>
                
                {/* Stage Filter */}
                <Select value={selectedStage} onValueChange={setSelectedStage}>
                  <SelectTrigger className="w-[200px] bg-[#0B0F14] border-[#27272A]">
                    <SelectValue placeholder="Все этапы" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#15191E] border-[#27272A]">
                    <SelectItem value="all">Все этапы</SelectItem>
                    {Object.entries(stageLabels).map(([key, label]) => (
                      <SelectItem key={key} value={key}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-[#27272A]">
                <button
                  onClick={() => setActiveTab('files')}
                  className={`flex-1 py-3 text-sm font-medium transition-colors ${
                    activeTab === 'files'
                      ? 'text-[#00E5FF] border-b-2 border-[#00E5FF]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <Folder size={16} className="inline mr-2" />
                  Файлы ({filteredFiles.length})
                </button>
                <button
                  onClick={() => setActiveTab('chat')}
                  className={`flex-1 py-3 text-sm font-medium transition-colors ${
                    activeTab === 'chat'
                      ? 'text-[#00E5FF] border-b-2 border-[#00E5FF]'
                      : 'text-slate-400 hover:text-white'
                  }`}
                >
                  <MessageSquare size={16} className="inline mr-2" />
                  Чат ({filteredMessages.length})
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'files' ? (
                <div className="p-4">
                  {/* Upload Button */}
                  <div className="mb-4">
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                    <Button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={uploading}
                      className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                    >
                      {uploading ? (
                        <Loader2 size={16} className="mr-2 animate-spin" />
                      ) : (
                        <Upload size={16} className="mr-2" />
                      )}
                      Загрузить файл
                    </Button>
                  </div>

                  {/* Files List */}
                  {filteredFiles.length === 0 ? (
                    <div className="text-center py-8">
                      <Folder size={48} className="mx-auto mb-3 text-slate-600" />
                      <p className="text-slate-400">Нет файлов</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredFiles.map(file => (
                        <div
                          key={file.id}
                          className="flex items-center gap-3 p-3 bg-[#0B0F14] rounded-lg"
                        >
                          <div className="w-10 h-10 bg-[#27272A] rounded-lg flex items-center justify-center">
                            {getFileIcon(file.category)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-white text-sm truncate">{file.original_name}</p>
                            <div className="flex items-center gap-2 text-xs text-slate-500">
                              <span>{formatFileSize(file.size)}</span>
                              <span>•</span>
                              <span>{file.uploader_type === 'client' ? (
                                <span className="flex items-center gap-1">
                                  <User size={10} />
                                  {file.uploader_name}
                                </span>
                              ) : (
                                <span className="flex items-center gap-1 text-purple-400">
                                  <Building2 size={10} />
                                  {file.uploader_name}
                                </span>
                              )}</span>
                              {file.stage_key && (
                                <>
                                  <span>•</span>
                                  <span className="text-[#00E5FF]">{stageLabels[file.stage_key]}</span>
                                </>
                              )}
                            </div>
                          </div>
                          <div className="flex gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => downloadFile(file.id, file.original_name)}
                              className="h-8 w-8 p-0 text-slate-400 hover:text-white"
                            >
                              <Download size={16} />
                            </Button>
                            {file.uploader_type === 'client' && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => deleteFile(file.id)}
                                className="h-8 w-8 p-0 text-slate-400 hover:text-red-400"
                              >
                                <Trash2 size={16} />
                              </Button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex flex-col h-[500px]">
                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-3">
                    {filteredMessages.length === 0 ? (
                      <div className="text-center py-8">
                        <MessageSquare size={48} className="mx-auto mb-3 text-slate-600" />
                        <p className="text-slate-400">Нет сообщений</p>
                        <p className="text-slate-500 text-sm">Начните общение с подрядчиком</p>
                      </div>
                    ) : (
                      filteredMessages.map(msg => (
                        <div
                          key={msg.id}
                          className={`flex ${msg.sender_type === 'client' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div className={`max-w-[70%] ${
                            msg.sender_type === 'client'
                              ? 'bg-[#00E5FF]/10 border border-[#00E5FF]/30'
                              : 'bg-[#27272A]'
                          } rounded-lg p-3`}>
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
                            {msg.stage_key && (
                              <span className="inline-block mt-1 px-2 py-0.5 bg-slate-700 text-slate-300 text-xs rounded">
                                {stageLabels[msg.stage_key]}
                              </span>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                    <div ref={messagesEndRef} />
                  </div>

                  {/* Message Input */}
                  <div className="p-4 border-t border-[#27272A]">
                    <div className="flex gap-2">
                      <Input
                        value={newMessage}
                        onChange={(e) => setNewMessage(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                        placeholder="Напишите сообщение..."
                        className="flex-1 bg-[#0B0F14] border-[#27272A]"
                      />
                      <Button
                        onClick={() => fileInputRef.current?.click()}
                        variant="outline"
                        className="border-[#27272A]"
                      >
                        <Paperclip size={16} />
                      </Button>
                      <Button
                        onClick={sendMessage}
                        disabled={sending || !newMessage.trim()}
                        className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
                      >
                        {sending ? (
                          <Loader2 size={16} className="animate-spin" />
                        ) : (
                          <Send size={16} />
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Documents;
