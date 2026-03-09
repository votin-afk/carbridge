import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { 
  CheckCircle2, 
  XCircle, 
  RefreshCcw, 
  Users, 
  FileText, 
  ListTodo,
  Loader2,
  Building2,
  Send,
  Bell
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const Bitrix24Admin = () => {
  const { token } = useAuth();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [creating, setCreating] = useState(false);
  
  // Form states
  const [dealForm, setDealForm] = useState({
    title: '',
    email: '',
    brand: '',
    model: '',
    price: '',
    comments: ''
  });
  
  const [taskForm, setTaskForm] = useState({
    title: '',
    description: '',
    deadline_days: 3,
    priority: 1
  });

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/api/admin/bitrix24/status`, { headers });
      setStatus(response.data);
    } catch (error) {
      console.error('Error checking Bitrix24 status:', error);
      setStatus({ connected: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    setLoadingUsers(true);
    try {
      const response = await axios.get(`${API}/api/admin/bitrix24/users`, { headers });
      if (response.data.success) {
        setUsers(response.data.result || []);
      }
    } catch (error) {
      toast.error('Ошибка загрузки пользователей');
    } finally {
      setLoadingUsers(false);
    }
  };

  const createDeal = async () => {
    if (!dealForm.title) {
      toast.error('Введите название сделки');
      return;
    }
    
    setCreating(true);
    try {
      const response = await axios.post(`${API}/api/admin/bitrix24/create-deal`, {
        ...dealForm,
        price: dealForm.price ? parseFloat(dealForm.price) : null
      }, { headers });
      
      if (response.data.success) {
        toast.success(`Сделка создана! ID: ${response.data.result}`);
        setDealForm({ title: '', email: '', brand: '', model: '', price: '', comments: '' });
      } else {
        toast.error(response.data.error || 'Ошибка создания сделки');
      }
    } catch (error) {
      toast.error('Ошибка создания сделки');
    } finally {
      setCreating(false);
    }
  };

  const createTask = async () => {
    if (!taskForm.title) {
      toast.error('Введите название задачи');
      return;
    }
    
    setCreating(true);
    try {
      const response = await axios.post(`${API}/api/admin/bitrix24/create-task`, taskForm, { headers });
      
      if (response.data.success) {
        const taskId = response.data.result?.task?.id || response.data.result;
        toast.success(`Задача создана! ID: ${taskId}`);
        setTaskForm({ title: '', description: '', deadline_days: 3, priority: 1 });
      } else {
        toast.error(response.data.error || 'Ошибка создания задачи');
      }
    } catch (error) {
      toast.error('Ошибка создания задачи');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Building2 className="text-[#00E5FF]" />
            Интеграция Bitrix24
          </h1>
          <p className="text-slate-400 mt-1">Управление CRM интеграцией</p>
        </div>
        <Button
          onClick={checkStatus}
          variant="outline"
          className="border-[#27272A] text-slate-300"
          disabled={loading}
        >
          <RefreshCcw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
          Обновить статус
        </Button>
      </div>

      {/* Connection Status */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Статус подключения</h2>
        
        {loading ? (
          <div className="flex items-center gap-3 text-slate-400">
            <Loader2 size={20} className="animate-spin" />
            <span>Проверка подключения...</span>
          </div>
        ) : status?.connected ? (
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-emerald-400">
              <CheckCircle2 size={24} />
              <span className="text-lg font-medium">Подключено</span>
            </div>
            <div className="text-slate-400 text-sm">
              <span className="text-slate-500">Webhook URL: </span>
              {status.webhook_url}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center gap-3 text-red-400">
              <XCircle size={24} />
              <span className="text-lg font-medium">Не подключено</span>
            </div>
            {status?.error && (
              <div className="text-red-400/80 text-sm">
                Ошибка: {status.error}
              </div>
            )}
          </div>
        )}
      </div>

      {status?.connected && (
        <>
          {/* Users */}
          <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                <Users size={20} className="text-[#00E5FF]" />
                Пользователи Bitrix24
              </h2>
              <Button
                onClick={loadUsers}
                variant="outline"
                size="sm"
                className="border-[#27272A] text-slate-300"
                disabled={loadingUsers}
              >
                {loadingUsers ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  'Загрузить'
                )}
              </Button>
            </div>
            
            {users.length > 0 ? (
              <div className="space-y-2">
                {users.map(user => (
                  <div key={user.ID} className="flex items-center gap-3 p-3 bg-[#0B0F14] rounded-lg">
                    <div className="w-10 h-10 rounded-full bg-[#27272A] flex items-center justify-center text-white font-medium">
                      {user.NAME?.[0]}{user.LAST_NAME?.[0]}
                    </div>
                    <div>
                      <div className="text-white font-medium">{user.NAME} {user.LAST_NAME}</div>
                      <div className="text-slate-400 text-sm">ID: {user.ID}</div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-sm">Нажмите "Загрузить" для получения списка</p>
            )}
          </div>

          {/* Create Deal */}
          <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <FileText size={20} className="text-[#00E5FF]" />
              Создать сделку вручную
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-400 mb-2 block">Название сделки *</Label>
                <Input
                  value={dealForm.title}
                  onChange={(e) => setDealForm({...dealForm, title: e.target.value})}
                  placeholder="Сделка: BMW X5 2024"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Email клиента</Label>
                <Input
                  value={dealForm.email}
                  onChange={(e) => setDealForm({...dealForm, email: e.target.value})}
                  placeholder="client@example.com"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Марка авто</Label>
                <Input
                  value={dealForm.brand}
                  onChange={(e) => setDealForm({...dealForm, brand: e.target.value})}
                  placeholder="BMW"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Модель</Label>
                <Input
                  value={dealForm.model}
                  onChange={(e) => setDealForm({...dealForm, model: e.target.value})}
                  placeholder="X5"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Сумма (USD)</Label>
                <Input
                  type="number"
                  value={dealForm.price}
                  onChange={(e) => setDealForm({...dealForm, price: e.target.value})}
                  placeholder="50000"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Комментарий</Label>
                <Input
                  value={dealForm.comments}
                  onChange={(e) => setDealForm({...dealForm, comments: e.target.value})}
                  placeholder="Дополнительная информация"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
            </div>
            
            <Button
              onClick={createDeal}
              disabled={creating}
              className="mt-4 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {creating ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <Send size={16} className="mr-2" />
              )}
              Создать сделку
            </Button>
          </div>

          {/* Create Task */}
          <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
            <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <ListTodo size={20} className="text-[#00E5FF]" />
              Создать задачу вручную
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="md:col-span-2">
                <Label className="text-slate-400 mb-2 block">Название задачи *</Label>
                <Input
                  value={taskForm.title}
                  onChange={(e) => setTaskForm({...taskForm, title: e.target.value})}
                  placeholder="Связаться с клиентом"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div className="md:col-span-2">
                <Label className="text-slate-400 mb-2 block">Описание</Label>
                <textarea
                  value={taskForm.description}
                  onChange={(e) => setTaskForm({...taskForm, description: e.target.value})}
                  placeholder="Детальное описание задачи..."
                  rows={3}
                  className="w-full bg-[#0B0F14] border border-[#27272A] text-white rounded-md px-3 py-2"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Срок (дней)</Label>
                <Input
                  type="number"
                  value={taskForm.deadline_days}
                  onChange={(e) => setTaskForm({...taskForm, deadline_days: parseInt(e.target.value) || 3})}
                  min="1"
                  className="bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 mb-2 block">Приоритет</Label>
                <select
                  value={taskForm.priority}
                  onChange={(e) => setTaskForm({...taskForm, priority: parseInt(e.target.value)})}
                  className="w-full bg-[#0B0F14] border border-[#27272A] text-white rounded-md px-3 py-2"
                >
                  <option value={0}>Низкий</option>
                  <option value={1}>Обычный</option>
                  <option value={2}>Высокий</option>
                </select>
              </div>
            </div>
            
            <Button
              onClick={createTask}
              disabled={creating}
              className="mt-4 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              {creating ? (
                <Loader2 size={16} className="mr-2 animate-spin" />
              ) : (
                <ListTodo size={16} className="mr-2" />
              )}
              Создать задачу
            </Button>
          </div>

          {/* Info */}
          <div className="bg-[#15191E] border border-amber-500/30 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Bell size={20} className="text-amber-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-amber-400 font-medium">Автоматическая синхронизация</h4>
                <p className="text-slate-400 text-sm mt-1">
                  Следующие события автоматически создают записи в Bitrix24:
                </p>
                <ul className="text-slate-400 text-sm mt-2 space-y-1 list-disc list-inside">
                  <li>Регистрация пользователя → Контакт</li>
                  <li>Новая заявка на авто → Лид</li>
                  <li>Новый тендер → Сделка + Задача для менеджера</li>
                  <li>Выбор подрядчика → Сделка + Задача + Уведомление</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default Bitrix24Admin;
