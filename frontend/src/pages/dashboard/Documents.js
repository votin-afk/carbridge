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
  AlertCircle,
  Plus
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';
import StageInfographic from '../../components/deal/StageInfographic';

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
  const [showCreateHelpDialog, setShowCreateHelpDialog] = useState(false);
  const [helpDescription, setHelpDescription] = useState('');
  
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

  const createHelpRequest = async () => {
    if (!helpDescription.trim()) {
      toast.error('Опишите, в чём вам нужна помощь');
      return;
    }
    try {
      await axios.post(`${API}/help-requests`, {
        request_type: 'general',
        description: helpDescription.trim()
      }, { headers });
      toast.success('Запрос на помощь менеджера отправлен');
      setHelpDescription('');
      setShowCreateHelpDialog(false);
      fetchHelpRequests();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка при создании запроса');
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

  const downloadFile = (fileId, filename) => {
    const url = `${API}/files/${fileId}/public-download?token=${encodeURIComponent(token)}`;
    window.open(url, '_blank');
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
        <h1 className="text-2xl font-bold text-white">Документы и коммуникации</h1>
        <p className="text-slate-400 mt-1">Обмен документами, чат по сделкам и связь с менеджерами</p>
      </div>

      {/* Main Tabs */}
      <Tabs value={mainTab} onValueChange={setMainTab}>
        <TabsList className="bg-[#15191E] p-1">
          <TabsTrigger value="deals" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <Car size={16} className="mr-2" />
            Сделки ({deals.length})
          </TabsTrigger>
          <TabsTrigger value="manager_help" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <Headphones size={16} className="mr-2" />
            Помощь менеджера ({helpRequests.length})
          </TabsTrigger>
          <TabsTrigger value="legal_help" className="data-[state=active]:bg-[#00E5FF] data-[state=active]:text-black">
            <Scale size={16} className="mr-2" />
            Юридическая помощь ({legalRequests.length})
          </TabsTrigger>
        </TabsList>

        {/* Deals Tab */}
        <TabsContent value="deals">
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
              {renderDealContent()}
            </div>
          </div>
        </TabsContent>

        {/* Manager Help Tab */}
        <TabsContent value="manager_help">
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Help Requests List */}
            <div className="lg:col-span-1 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-white font-medium">Запросы на помощь</h3>
                <Button
                  onClick={() => setShowCreateHelpDialog(true)}
                  size="sm"
                  className="bg-amber-500 hover:bg-amber-600 text-black"
                  data-testid="create-help-request-btn"
                >
                  <Plus size={14} className="mr-1" />
                  Создать запрос
                </Button>
              </div>
              
              {helpRequests.length === 0 ? (
                <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 text-center">
                  <Headphones size={48} className="mx-auto mb-3 text-slate-600" />
                  <p className="text-slate-400">Нет запросов на помощь</p>
                  <p className="text-slate-500 text-sm mt-1">Создайте запрос, чтобы получить помощь менеджера</p>
                </div>
              ) : (
                helpRequests.map(req => (
                  <div
                    key={req.id}
                    onClick={() => setSelectedHelpRequest(req)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedHelpRequest?.id === req.id
                        ? 'bg-amber-500/10 border-amber-500'
                        : 'bg-[#15191E] border-[#27272A] hover:border-amber-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                        req.status === 'pending' ? 'bg-amber-500/20' : 'bg-emerald-500/20'
                      }`}>
                        <Headphones size={18} className={req.status === 'pending' ? 'text-amber-400' : 'text-emerald-400'} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">
                          {req.car_details?.brand ? `${req.car_details.brand} ${req.car_details.model}` : 'Помощь в подборе'}
                        </p>
                        <div className="flex items-center gap-2 text-xs">
                          <span className={req.status === 'pending' ? 'text-amber-400' : 'text-emerald-400'}>
                            {req.status === 'pending' ? 'Ожидает' : 'В работе'}
                          </span>
                          {req.assigned_manager_name && (
                            <>
                              <span className="text-slate-500">•</span>
                              <span className="text-slate-400">{req.assigned_manager_name}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Help Request Content */}
            <div className="lg:col-span-2">
              {renderHelpRequestContent()}
            </div>
          </div>
        </TabsContent>

        {/* Legal Help Tab */}
        <TabsContent value="legal_help">
          <div className="grid lg:grid-cols-3 gap-6">
            {/* Legal Requests List */}
            <div className="lg:col-span-1 space-y-3">
              <h3 className="text-white font-medium">Юридические консультации</h3>
              
              {legalRequests.length === 0 ? (
                <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 text-center">
                  <Scale size={48} className="mx-auto mb-3 text-slate-600" />
                  <p className="text-slate-400">Нет запросов</p>
                  <p className="text-slate-500 text-sm mt-1">Запросите юридическую помощь в соответствующем разделе</p>
                </div>
              ) : (
                legalRequests.map(req => (
                  <div
                    key={req.id}
                    onClick={() => setSelectedLegalRequest(req)}
                    className={`p-4 rounded-lg border cursor-pointer transition-all ${
                      selectedLegalRequest?.id === req.id
                        ? 'bg-purple-500/10 border-purple-500'
                        : 'bg-[#15191E] border-[#27272A] hover:border-purple-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                        <Scale size={18} className="text-purple-400" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-white font-medium truncate">Консультация #{req.id?.slice(0, 8)}</p>
                        <p className="text-slate-500 text-xs">
                          {new Date(req.created_at).toLocaleDateString('ru-RU')}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Legal Request Content */}
            <div className="lg:col-span-2">
              {renderLegalRequestContent()}
            </div>
          </div>
        </TabsContent>
      </Tabs>

      {/* Create Help Request Dialog */}
      <Dialog open={showCreateHelpDialog} onOpenChange={setShowCreateHelpDialog}>
        <DialogContent className="bg-[#15191E] border-[#27272A]">
          <DialogHeader>
            <DialogTitle className="text-white">Запрос помощи менеджера</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-400 mb-2 block">Опишите, в чём вам нужна помощь</label>
              <Textarea
                value={helpDescription}
                onChange={(e) => setHelpDescription(e.target.value)}
                placeholder="Например: Нужна помощь с подбором авто, оформлением документов..."
                className="bg-[#0B0F14] border-[#27272A] text-white min-h-[120px]"
                data-testid="help-description-input"
              />
            </div>
            <div className="flex gap-3 justify-end">
              <Button
                variant="outline"
                onClick={() => setShowCreateHelpDialog(false)}
                className="border-[#27272A] text-slate-400"
              >
                Отмена
              </Button>
              <Button
                onClick={createHelpRequest}
                disabled={!helpDescription.trim()}
                className="bg-amber-500 hover:bg-amber-600 text-black"
                data-testid="submit-help-request-btn"
              >
                Отправить запрос
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );

  // Render functions for each section
  function renderDealContent() {
    if (!selectedDeal) {
      return (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <MessageSquare size={64} className="mx-auto mb-4 text-slate-600" />
          <p className="text-slate-400">Выберите сделку для просмотра документов и чата</p>
        </div>
      );
    }

    return (
      <div className="space-y-4">
        {/* Deal Header */}
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {selectedDeal.car_info?.image_url ? (
                <img src={selectedDeal.car_info.image_url} alt="" className="w-16 h-12 object-cover rounded" />
              ) : (
                <div className="w-16 h-12 bg-[#0B0F14] rounded flex items-center justify-center">
                  <Car size={24} className="text-slate-600" />
                </div>
              )}
              <div>
                <h3 className="text-white font-semibold text-lg">
                  {selectedDeal.car_info?.brand} {selectedDeal.car_info?.model}
                </h3>
                <p className="text-slate-400 text-sm">
                  Сделка #{selectedDeal.id?.slice(0, 8)} • {selectedDeal.car_info?.year || ''}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Stage Infographic */}
        <StageInfographic 
          deal={selectedDeal} 
          token={token}
          onRefresh={fetchDeals}
        />

        {/* Legacy Files & Chat Section (collapsed by default) */}
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden">
          <div className="p-3 border-b border-[#27272A] flex items-center justify-between">
            <p className="text-slate-400 text-sm">Все файлы и общий чат сделки</p>
            <Select value={selectedStage} onValueChange={setSelectedStage}>
              <SelectTrigger className="w-[180px] bg-[#0B0F14] border-[#27272A] h-8 text-sm">
                <SelectValue placeholder="Фильтр по этапу" />
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
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                activeTab === 'files'
                  ? 'text-[#00E5FF] border-b-2 border-[#00E5FF]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Folder size={14} className="inline mr-2" />
              Файлы ({filteredFiles.length})
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex-1 py-2 text-sm font-medium transition-colors ${
                activeTab === 'chat'
                  ? 'text-[#00E5FF] border-b-2 border-[#00E5FF]'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <MessageSquare size={14} className="inline mr-2" />
              Чат ({filteredMessages.length})
            </button>
          </div>

          {/* Tab Content */}
          {activeTab === 'files' ? renderFilesContent() : renderChatContent()}
        </div>
      </div>
    );
  }

  function renderFilesContent() {
    return (
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
    );
  }

  function renderChatContent() {
    return (
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
                  {msg.source === 'telegram' && (
                    <span className="inline-block mt-1 mr-1 px-1.5 py-0.5 bg-blue-500/20 text-blue-400 text-xs rounded">
                      Telegram
                    </span>
                  )}
                  {msg.file_ids && msg.file_ids.length > 0 && (
                    <div className="mt-1">
                      {msg.file_ids.map(fid => (
                        <button
                          key={fid}
                          onClick={() => downloadFile(fid, `file_${fid}`)}
                          className="flex items-center gap-1 text-xs text-[#00E5FF] hover:underline cursor-pointer"
                        >
                          <Paperclip size={10} /> Скачать файл
                        </button>
                      ))}
                    </div>
                  )}
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
    );
  }

  function renderHelpRequestContent() {
    if (!selectedHelpRequest) {
      return (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <Headphones size={64} className="mx-auto mb-4 text-slate-600" />
          <p className="text-slate-400">Выберите запрос для общения с менеджером</p>
        </div>
      );
    }

    return (
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden">
        {/* Help Request Header */}
        <div className="p-4 border-b border-[#27272A]">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h3 className="text-white font-semibold">
                {selectedHelpRequest.car_details?.brand 
                  ? `Помощь в подборе: ${selectedHelpRequest.car_details.brand} ${selectedHelpRequest.car_details.model}`
                  : 'Помощь менеджера'
                }
              </h3>
              <p className="text-slate-400 text-sm">
                Запрос #{selectedHelpRequest.id?.slice(0, 8)}
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm ${
              selectedHelpRequest.status === 'pending' 
                ? 'bg-amber-500/20 text-amber-400' 
                : 'bg-emerald-500/20 text-emerald-400'
            }`}>
              {selectedHelpRequest.status === 'pending' ? 'Ожидает ответа' : 'В работе'}
            </div>
          </div>
          
          {/* Manager Info */}
          {selectedHelpRequest.assigned_manager_name ? (
            <div className="flex items-center gap-3 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
              <div className="w-10 h-10 bg-emerald-500/20 rounded-full flex items-center justify-center">
                <User size={20} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-emerald-400 font-medium">Ваш менеджер</p>
                <p className="text-white">{selectedHelpRequest.assigned_manager_name}</p>
              </div>
              <Button
                onClick={requestCallback}
                variant="outline"
                size="sm"
                className="ml-auto border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10"
              >
                <Phone size={14} className="mr-1" />
                Запросить звонок
              </Button>
            </div>
          ) : (
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
              <p className="text-amber-400 text-sm flex items-center gap-2">
                <Clock size={14} />
                Ожидайте назначения персонального менеджера
              </p>
            </div>
          )}
        </div>

        {/* Chat with Manager */}
        <div className="flex flex-col h-[400px]">
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {helpMessages.length === 0 ? (
              <div className="text-center py-8">
                <MessageSquare size={48} className="mx-auto mb-3 text-slate-600" />
                <p className="text-slate-400">Нет сообщений</p>
                <p className="text-slate-500 text-sm">Менеджер ответит вам в ближайшее время</p>
              </div>
            ) : (
              helpMessages.map(msg => (
                <div
                  key={msg.id}
                  className={`flex ${msg.sender_type === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`max-w-[70%] ${
                    msg.sender_type === 'user'
                      ? 'bg-amber-500/10 border border-amber-500/30'
                      : 'bg-emerald-500/10 border border-emerald-500/30'
                  } rounded-lg p-3`}>
                    <div className="flex items-center gap-2 mb-1">
                      {msg.sender_type === 'user' ? (
                        <User size={12} className="text-amber-400" />
                      ) : (
                        <Headphones size={12} className="text-emerald-400" />
                      )}
                      <span className={`text-xs font-medium ${
                        msg.sender_type === 'user' ? 'text-amber-400' : 'text-emerald-400'
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
            <div ref={helpMessagesEndRef} />
          </div>

          {/* Message Input */}
          <div className="p-4 border-t border-[#27272A]">
            <div className="flex gap-2">
              <Input
                value={newHelpMessage}
                onChange={(e) => setNewHelpMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendHelpMessage()}
                placeholder="Напишите сообщение менеджеру..."
                className="flex-1 bg-[#0B0F14] border-[#27272A]"
              />
              <Button
                onClick={sendHelpMessage}
                disabled={sendingHelp || !newHelpMessage.trim()}
                className="bg-amber-500 hover:bg-amber-600 text-black"
              >
                {sendingHelp ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Send size={16} />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function renderLegalRequestContent() {
    if (!selectedLegalRequest) {
      return (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <Scale size={64} className="mx-auto mb-4 text-slate-600" />
          <p className="text-slate-400">Выберите запрос для просмотра</p>
        </div>
      );
    }

    return (
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
        <h3 className="text-white font-semibold mb-4">Юридическая консультация</h3>
        <p className="text-slate-400">Раздел в разработке</p>
      </div>
    );
  }
};

export default Documents;
