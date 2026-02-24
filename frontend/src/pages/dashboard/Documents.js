import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { 
  FileText, 
  Download,
  Eye,
  Folder,
  File,
  FileImage,
  FilePlus
} from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Documents = () => {
  const { token } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await axios.get(`${API}/documents`, { headers });
        setDocuments(response.data);
      } catch (error) {
        console.error('Error fetching documents:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  const getDocIcon = (type) => {
    const icons = {
      report: FileText,
      contract: File,
      invoice: FileText,
      photo: FileImage
    };
    const Icon = icons[type] || File;
    return <Icon size={20} />;
  };

  const getDocTypeLabel = (type) => {
    const labels = {
      report: 'Отчет',
      contract: 'Договор',
      invoice: 'Инвойс',
      photo: 'Фото'
    };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Sample document categories for UI
  const categories = [
    { id: 'all', label: 'Все документы', count: documents.length },
    { id: 'reports', label: 'Отчеты о состоянии', count: documents.filter(d => d.doc_type === 'report').length },
    { id: 'contracts', label: 'Договоры', count: documents.filter(d => d.doc_type === 'contract').length },
    { id: 'invoices', label: 'Инвойсы', count: documents.filter(d => d.doc_type === 'invoice').length },
  ];

  return (
    <div className="space-y-6" data-testid="documents-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Мои документы</h1>
        <p className="text-slate-400 mt-1">
          Отчеты, договоры и документы по сделкам
        </p>
      </div>

      {/* Categories */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {categories.map((cat) => (
          <div 
            key={cat.id}
            className="bg-[#15191E] border border-[#27272A] rounded-sm p-4 card-hover cursor-pointer"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center">
                <Folder size={20} className="text-[#00E5FF]" />
              </div>
              <div>
                <p className="text-white font-medium">{cat.label}</p>
                <p className="text-slate-500 text-sm">{cat.count} файлов</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Documents List */}
      {documents.length > 0 ? (
        <div className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden">
          <div className="p-4 border-b border-[#27272A]">
            <h2 className="text-white font-semibold">Последние документы</h2>
          </div>
          <div className="divide-y divide-[#27272A]">
            {documents.map((doc) => (
              <div 
                key={doc.id}
                className="p-4 flex items-center justify-between hover:bg-[#1C2128] transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-[#1C2128] rounded-sm flex items-center justify-center text-slate-400">
                    {getDocIcon(doc.doc_type)}
                  </div>
                  <div>
                    <p className="text-white font-medium">{doc.title}</p>
                    <div className="flex items-center gap-3 text-sm text-slate-500">
                      <span>{getDocTypeLabel(doc.doc_type)}</span>
                      <span>•</span>
                      <span>{new Date(doc.created_at).toLocaleDateString('ru-RU')}</span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <a 
                    href={doc.file_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="p-2 text-slate-400 hover:text-[#00E5FF] transition-colors"
                  >
                    <Eye size={18} />
                  </a>
                  <a 
                    href={doc.file_url} 
                    download
                    className="p-2 text-slate-400 hover:text-[#00E5FF] transition-colors"
                  >
                    <Download size={18} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <FileText size={64} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-xl font-semibold text-white mb-2">Нет документов</h3>
          <p className="text-slate-400 mb-6 max-w-md mx-auto">
            Документы появятся здесь после начала работы по сделкам. Здесь будут отчеты о состоянии авто, договоры и инвойсы.
          </p>
        </div>
      )}

      {/* Info Section */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-6">
        <h3 className="text-white font-semibold mb-4">Какие документы вы получите</h3>
        <div className="grid md:grid-cols-2 gap-4">
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center flex-shrink-0">
              <FileText size={16} className="text-[#00E5FF]" />
            </div>
            <div>
              <p className="text-white font-medium">Отчет о состоянии</p>
              <p className="text-slate-400 text-sm">Профессиональная проверка авто с фото и видео</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center flex-shrink-0">
              <File size={16} className="text-[#00E5FF]" />
            </div>
            <div>
              <p className="text-white font-medium">Договор купли-продажи</p>
              <p className="text-slate-400 text-sm">Юридически оформленный договор</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center flex-shrink-0">
              <FileText size={16} className="text-[#00E5FF]" />
            </div>
            <div>
              <p className="text-white font-medium">Таможенные документы</p>
              <p className="text-slate-400 text-sm">Полный пакет для растаможки</p>
            </div>
          </div>
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-[#00E5FF]/10 rounded-sm flex items-center justify-center flex-shrink-0">
              <FileText size={16} className="text-[#00E5FF]" />
            </div>
            <div>
              <p className="text-white font-medium">ЭПТС</p>
              <p className="text-slate-400 text-sm">Электронный паспорт транспортного средства</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Documents;
