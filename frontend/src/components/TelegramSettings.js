import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import {
  Send,
  Link2,
  Unlink,
  CheckCircle2,
  Loader2,
  ExternalLink,
  Bell,
  BellOff
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TelegramSettings = ({ token, isOpen, onClose }) => {
  const [status, setStatus] = useState({ linked: false, username: null });
  const [loading, setLoading] = useState(true);
  const [linking, setLinking] = useState(false);
  const [linkData, setLinkData] = useState(null);
  const [testing, setTesting] = useState(false);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    if (isOpen && token) {
      fetchStatus();
    }
  }, [isOpen, token]);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/telegram/status`, { headers });
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching Telegram status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLink = async () => {
    setLinking(true);
    try {
      const response = await axios.post(`${API}/telegram/link`, {}, { headers });
      setLinkData(response.data);
    } catch (error) {
      toast.error('Ошибка получения ссылки');
    } finally {
      setLinking(false);
    }
  };

  const handleUnlink = async () => {
    try {
      await axios.post(`${API}/telegram/unlink`, {}, { headers });
      setStatus({ linked: false, username: null });
      setLinkData(null);
      toast.success('Telegram отвязан');
    } catch (error) {
      toast.error('Ошибка отвязки Telegram');
    }
  };

  const handleTest = async () => {
    setTesting(true);
    try {
      await axios.post(`${API}/telegram/test`, {}, { headers });
      toast.success('Тестовое уведомление отправлено в Telegram');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ошибка отправки');
    } finally {
      setTesting(false);
    }
  };

  const openTelegramLink = () => {
    if (linkData?.link) {
      window.open(linkData.link, '_blank');
      // Start polling for status change
      const pollInterval = setInterval(async () => {
        try {
          const response = await axios.get(`${API}/telegram/status`, { headers });
          if (response.data.linked) {
            setStatus(response.data);
            setLinkData(null);
            clearInterval(pollInterval);
            toast.success('Telegram успешно привязан!');
          }
        } catch (e) {}
      }, 2000);
      
      // Stop polling after 2 minutes
      setTimeout(() => clearInterval(pollInterval), 120000);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Send size={20} className="text-[#0088cc]" />
            Telegram уведомления
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="animate-spin text-[#0088cc]" size={32} />
            </div>
          ) : status.linked ? (
            // Connected state
            <div className="space-y-4">
              <div className="p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle2 size={24} className="text-emerald-400" />
                  <div>
                    <p className="text-emerald-400 font-medium">Telegram подключен</p>
                    {status.username && (
                      <p className="text-slate-400 text-sm">@{status.username}</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="p-4 bg-[#0B0F14] rounded-lg">
                <p className="text-slate-400 text-sm mb-3">Вы будете получать уведомления о:</p>
                <ul className="space-y-2 text-sm">
                  <li className="flex items-center gap-2 text-white">
                    <Bell size={14} className="text-[#0088cc]" />
                    Новых сообщениях в чатах сделок
                  </li>
                  <li className="flex items-center gap-2 text-white">
                    <Bell size={14} className="text-[#0088cc]" />
                    Изменениях статуса этапов
                  </li>
                  <li className="flex items-center gap-2 text-white">
                    <Bell size={14} className="text-[#0088cc]" />
                    Действиях модератора
                  </li>
                </ul>
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={handleTest}
                  disabled={testing}
                  className="flex-1 bg-[#0088cc] hover:bg-[#006699] text-white"
                >
                  {testing ? <Loader2 size={16} className="animate-spin mr-2" /> : <Send size={16} className="mr-2" />}
                  Тест уведомления
                </Button>
                <Button
                  onClick={handleUnlink}
                  variant="outline"
                  className="border-red-500/50 text-red-400 hover:bg-red-500/10"
                >
                  <Unlink size={16} className="mr-2" />
                  Отвязать
                </Button>
              </div>
            </div>
          ) : linkData ? (
            // Linking in progress
            <div className="space-y-4">
              <div className="p-4 bg-[#0088cc]/10 border border-[#0088cc]/30 rounded-lg text-center">
                <Send size={48} className="mx-auto mb-3 text-[#0088cc]" />
                <p className="text-white font-medium mb-2">Нажмите кнопку ниже</p>
                <p className="text-slate-400 text-sm">
                  Откроется Telegram бот. Нажмите "Запустить" чтобы привязать аккаунт.
                </p>
              </div>

              <Button
                onClick={openTelegramLink}
                className="w-full bg-[#0088cc] hover:bg-[#006699] text-white"
              >
                <ExternalLink size={16} className="mr-2" />
                Открыть Telegram
              </Button>

              <p className="text-slate-500 text-xs text-center">
                После привязки страница обновится автоматически
              </p>
            </div>
          ) : (
            // Not connected state
            <div className="space-y-4">
              <div className="p-4 bg-[#0B0F14] rounded-lg text-center">
                <BellOff size={48} className="mx-auto mb-3 text-slate-600" />
                <p className="text-slate-400">Telegram не привязан</p>
                <p className="text-slate-500 text-sm mt-1">
                  Привяжите Telegram для получения мгновенных уведомлений
                </p>
              </div>

              <Button
                onClick={handleLink}
                disabled={linking}
                className="w-full bg-[#0088cc] hover:bg-[#006699] text-white"
              >
                {linking ? <Loader2 size={16} className="animate-spin mr-2" /> : <Link2 size={16} className="mr-2" />}
                Привязать Telegram
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default TelegramSettings;
