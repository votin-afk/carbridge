import { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../components/ui/dialog";
import { 
  Car, 
  Plus, 
  Trash2, 
  Send,
  ExternalLink,
  Search
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const MyGarage = () => {
  const { token } = useAuth();
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formData, setFormData] = useState({
    brand: '',
    model: '',
    year: new Date().getFullYear(),
    price_cny: '',
    engine_type: 'ice',
    engine_volume: '',
    mileage: '',
    image_url: '',
    source_url: '',
    description: ''
  });

  const headers = { Authorization: `Bearer ${token}` };

  const fetchCars = async () => {
    try {
      const response = await axios.get(`${API}/garage`, { headers });
      setCars(response.data);
    } catch (error) {
      console.error('Error fetching garage:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCars();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAddCar = async () => {
    if (!formData.brand || !formData.model || !formData.price_cny) {
      toast.error('Заполните обязательные поля');
      return;
    }

    setSubmitting(true);
    try {
      await axios.post(`${API}/garage`, {
        ...formData,
        year: parseInt(formData.year),
        price_cny: parseFloat(formData.price_cny),
        engine_volume: formData.engine_volume ? parseInt(formData.engine_volume) : null,
        mileage: formData.mileage ? parseInt(formData.mileage) : null
      }, { headers });
      
      toast.success('Авто добавлено в гараж');
      setIsAddDialogOpen(false);
      setFormData({
        brand: '', model: '', year: new Date().getFullYear(),
        price_cny: '', engine_type: 'ice', engine_volume: '',
        mileage: '', image_url: '', source_url: '', description: ''
      });
      fetchCars();
    } catch (error) {
      toast.error('Ошибка при добавлении');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteCar = async (carId) => {
    if (!window.confirm('Удалить авто из гаража?')) return;
    
    try {
      await axios.delete(`${API}/garage/${carId}`, { headers });
      toast.success('Авто удалено');
      setCars(cars.filter(c => c.id !== carId));
    } catch (error) {
      toast.error('Ошибка при удалении');
    }
  };

  const handleStartTender = async (carId) => {
    try {
      await axios.post(`${API}/tenders`, { car_id: carId }, { headers });
      toast.success('Тендер запущен! Проверьте раздел "Тендеры"');
      fetchCars();
    } catch (error) {
      toast.error('Ошибка при запуске тендера');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      saved: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
      tender_active: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
      in_progress: 'bg-[#00E5FF]/10 text-[#00E5FF] border-[#00E5FF]/20'
    };
    const labels = {
      saved: 'Сохранен',
      tender_active: 'Тендер активен',
      in_progress: 'В работе'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs border ${styles[status] || styles.saved}`}>
        {labels[status] || status}
      </span>
    );
  };

  const getEngineTypeLabel = (type) => {
    const labels = { ice: 'ДВС', hybrid: 'Гибрид', electric: 'Электро' };
    return labels[type] || type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="my-garage">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Мой гараж</h1>
          <p className="text-slate-400 mt-1">
            Сохраненные автомобили для тендера
          </p>
        </div>

        <Dialog open={isAddDialogOpen} onOpenChange={setIsAddDialogOpen}>
          <DialogTrigger asChild>
            <Button data-testid="add-car-btn" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
              <Plus size={18} className="mr-2" />
              Добавить авто
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-[#15191E] border-[#27272A] text-white max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Добавить автомобиль</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Марка *</Label>
                  <Input
                    data-testid="add-car-brand"
                    name="brand"
                    value={formData.brand}
                    onChange={handleChange}
                    placeholder="BYD, Li Auto..."
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Модель *</Label>
                  <Input
                    data-testid="add-car-model"
                    name="model"
                    value={formData.model}
                    onChange={handleChange}
                    placeholder="Han, L9..."
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-300">Год</Label>
                  <Input
                    type="number"
                    name="year"
                    value={formData.year}
                    onChange={handleChange}
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
                <div>
                  <Label className="text-slate-300">Цена (CNY) *</Label>
                  <Input
                    data-testid="add-car-price"
                    type="number"
                    name="price_cny"
                    value={formData.price_cny}
                    onChange={handleChange}
                    placeholder="150000"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              </div>

              <div>
                <Label className="text-slate-300">Тип двигателя</Label>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  {['ice', 'hybrid', 'electric'].map(type => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, engine_type: type }))}
                      className={`py-2 px-3 rounded-sm border text-sm ${
                        formData.engine_type === type
                          ? 'bg-[#00E5FF] text-black border-[#00E5FF]'
                          : 'bg-[#0B0F14] text-slate-400 border-[#27272A]'
                      }`}
                    >
                      {getEngineTypeLabel(type)}
                    </button>
                  ))}
                </div>
              </div>

              {formData.engine_type !== 'electric' && (
                <div>
                  <Label className="text-slate-300">Объем двигателя (см³)</Label>
                  <Input
                    type="number"
                    name="engine_volume"
                    value={formData.engine_volume}
                    onChange={handleChange}
                    placeholder="2000"
                    className="mt-1 bg-[#0B0F14] border-[#27272A]"
                  />
                </div>
              )}

              <div>
                <Label className="text-slate-300">Пробег (км)</Label>
                <Input
                  type="number"
                  name="mileage"
                  value={formData.mileage}
                  onChange={handleChange}
                  placeholder="50000"
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              <div>
                <Label className="text-slate-300">Ссылка на объявление</Label>
                <Input
                  name="source_url"
                  value={formData.source_url}
                  onChange={handleChange}
                  placeholder="https://che168.com/..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              <div>
                <Label className="text-slate-300">URL изображения</Label>
                <Input
                  name="image_url"
                  value={formData.image_url}
                  onChange={handleChange}
                  placeholder="https://..."
                  className="mt-1 bg-[#0B0F14] border-[#27272A]"
                />
              </div>

              <div>
                <Label className="text-slate-300">Описание</Label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleChange}
                  placeholder="Дополнительная информация..."
                  className="mt-1 w-full bg-[#0B0F14] border border-[#27272A] rounded-sm px-3 py-2 text-white placeholder:text-slate-500 focus:border-[#00E5FF] min-h-[80px]"
                />
              </div>

              <Button
                data-testid="add-car-submit"
                onClick={handleAddCar}
                disabled={submitting}
                className="w-full bg-[#00E5FF] hover:bg-[#22D3EE] text-black mt-4"
              >
                {submitting ? 'Добавление...' : 'Добавить в гараж'}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {/* Cars Grid */}
      {cars.length > 0 ? (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {cars.map((car) => (
            <div 
              key={car.id}
              className="bg-[#15191E] border border-[#27272A] rounded-sm overflow-hidden card-hover"
            >
              {/* Image */}
              <div className="h-40 bg-[#1C2128] relative">
                {car.image_url ? (
                  <img 
                    src={car.image_url} 
                    alt={`${car.brand} ${car.model}`}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Car size={48} className="text-slate-600" />
                  </div>
                )}
                <div className="absolute top-3 right-3">
                  {getStatusBadge(car.status)}
                </div>
              </div>

              {/* Content */}
              <div className="p-4">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-white font-semibold text-lg">
                    {car.brand} {car.model}
                  </h3>
                  <span className="text-[#00E5FF] font-semibold">
                    ¥{car.price_cny?.toLocaleString()}
                  </span>
                </div>

                <div className="flex flex-wrap gap-2 text-sm text-slate-400 mb-4">
                  <span>{car.year}</span>
                  <span>•</span>
                  <span>{getEngineTypeLabel(car.engine_type)}</span>
                  {car.engine_volume && (
                    <>
                      <span>•</span>
                      <span>{car.engine_volume} см³</span>
                    </>
                  )}
                  {car.mileage && (
                    <>
                      <span>•</span>
                      <span>{car.mileage.toLocaleString()} км</span>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2">
                  {car.status === 'saved' && (
                    <Button
                      data-testid={`start-tender-${car.id}`}
                      onClick={() => handleStartTender(car.id)}
                      className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black text-sm"
                    >
                      <Send size={14} className="mr-1" />
                      Запустить тендер
                    </Button>
                  )}
                  {car.source_url && (
                    <a 
                      href={car.source_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="p-2 border border-[#27272A] rounded-sm text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF]"
                    >
                      <ExternalLink size={16} />
                    </a>
                  )}
                  <button
                    data-testid={`delete-car-${car.id}`}
                    onClick={() => handleDeleteCar(car.id)}
                    className="p-2 border border-[#27272A] rounded-sm text-slate-400 hover:text-red-400 hover:border-red-400"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-sm">
          <Car size={64} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-xl font-semibold text-white mb-2">Гараж пуст</h3>
          <p className="text-slate-400 mb-6 max-w-md mx-auto">
            Добавьте автомобили, которые вас интересуют, и запустите тендер для получения предложений от подрядчиков
          </p>
          <Button
            onClick={() => setIsAddDialogOpen(true)}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            <Plus size={18} className="mr-2" />
            Добавить первое авто
          </Button>
        </div>
      )}
    </div>
  );
};

export default MyGarage;
