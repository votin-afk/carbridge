import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import { 
  ArrowLeft, 
  Car, 
  Zap, 
  Fuel, 
  Battery,
  ExternalLink,
  Plus,
  Loader2,
  MapPin,
  Calendar,
  Gauge,
  Settings,
  Palette,
  Shield,
  ChevronLeft,
  ChevronRight,
  X
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CarDetailPage = () => {
  const { carId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, token } = useAuth();
  
  const [car, setCar] = useState(null);
  const [loading, setLoading] = useState(true);
  const [addingToGarage, setAddingToGarage] = useState(false);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [showGallery, setShowGallery] = useState(false);

  useEffect(() => {
    const fetchCarDetails = async () => {
      try {
        const response = await axios.get(`${API}/catalog/${carId}`);
        setCar(response.data);
      } catch (error) {
        console.error('Error fetching car details:', error);
        toast.error('Ошибка загрузки данных автомобиля');
      } finally {
        setLoading(false);
      }
    };
    
    if (carId) {
      fetchCarDetails();
    }
  }, [carId]);

  const handleAddToGarage = async () => {
    if (!isAuthenticated) {
      toast.error('Войдите в аккаунт для добавления в гараж');
      navigate('/auth');
      return;
    }
    
    setAddingToGarage(true);
    try {
      await axios.post(`${API}/catalog/${carId}/add-to-garage`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Авто добавлено в гараж!');
      navigate('/dashboard/garage');
    } catch (error) {
      console.error('Error adding to garage:', error);
      toast.error(error.response?.data?.detail || 'Ошибка при добавлении в гараж');
    } finally {
      setAddingToGarage(false);
    }
  };

  const getEngineIcon = (type) => {
    switch (type) {
      case 'electric': return <Battery className="text-emerald-400" size={20} />;
      case 'hybrid': return <Zap className="text-amber-400" size={20} />;
      default: return <Fuel className="text-slate-400" size={20} />;
    }
  };

  const getEngineLabel = (type) => {
    const labels = { ice: 'ДВС', hybrid: 'Гибрид', electric: 'Электро' };
    return labels[type] || type;
  };

  const getBodyLabel = (type) => {
    const labels = { 
      sedan: 'Седан', 
      suv: 'Кроссовер', 
      hatchback: 'Хэтчбек',
      mpv: 'Минивэн',
      wagon: 'Универсал',
      pickup: 'Пикап',
      coupe: 'Купе'
    };
    return labels[type] || type;
  };

  const formatPrice = (price) => {
    if (!price || price === 0) return '—';
    if (price >= 10000) {
      return `¥${(price / 10000).toFixed(2)}万`;
    }
    return `¥${price.toLocaleString()}`;
  };

  const formatMileage = (km) => {
    if (!km) return 'Н/Д';
    return `${km.toLocaleString('ru-RU')} км`;
  };

  // Get images array
  const images = car?.images && car.images.length > 0 
    ? car.images 
    : car?.image_url 
      ? [car.image_url] 
      : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0D1117] flex items-center justify-center">
        <Loader2 className="animate-spin text-[#00E5FF]" size={48} />
      </div>
    );
  }

  if (!car) {
    return (
      <div className="min-h-screen bg-[#0D1117] flex flex-col items-center justify-center">
        <Car size={64} className="text-slate-600 mb-4" />
        <h2 className="text-xl text-white mb-2">Автомобиль не найден</h2>
        <Link to="/catalog">
          <Button variant="outline" className="border-[#27272A] text-slate-300">
            <ArrowLeft size={16} className="mr-2" />
            Вернуться в каталог
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0D1117]">
      {/* Header */}
      <header className="bg-[#15191E]/80 backdrop-blur-md border-b border-[#27272A] sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button 
                onClick={() => navigate(-1)} 
                className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors"
              >
                <ArrowLeft size={20} />
              </button>
              <Link to="/">
                <Logo />
              </Link>
            </div>
            <nav className="flex items-center gap-4">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button variant="outline" className="border-[#27272A] text-slate-300 hover:bg-[#27272A]">
                    Личный кабинет
                  </Button>
                </Link>
              ) : (
                <Link to="/auth">
                  <Button className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
                    Войти
                  </Button>
                </Link>
              )}
            </nav>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Breadcrumbs */}
        <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
          <Link to="/" className="hover:text-[#00E5FF]">Главная</Link>
          <span>/</span>
          <Link to="/catalog" className="hover:text-[#00E5FF]">Каталог</Link>
          <span>/</span>
          <span className="text-white">{car.brand} {car.model}</span>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Images Section */}
          <div>
            {/* Main Image */}
            <div 
              className="relative aspect-[4/3] bg-[#15191E] rounded-lg overflow-hidden mb-4 cursor-pointer"
              onClick={() => images.length > 0 && setShowGallery(true)}
            >
              {images.length > 0 ? (
                <img
                  src={images[selectedImageIndex]}
                  alt={`${car.brand} ${car.model}`}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.src = 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Car size={80} className="text-slate-600" />
                </div>
              )}
              
              {/* Source badge */}
              {car.source === 'che168' && (
                <div className="absolute top-4 right-4 px-3 py-1 bg-blue-500/80 backdrop-blur-sm rounded text-sm text-white font-medium">
                  CHE168
                </div>
              )}
              
              {/* Image counter */}
              {images.length > 1 && (
                <div className="absolute bottom-4 right-4 px-3 py-1 bg-black/60 backdrop-blur-sm rounded text-sm text-white">
                  {selectedImageIndex + 1} / {images.length}
                </div>
              )}
            </div>

            {/* Thumbnails */}
            {images.length > 1 && (
              <div className="flex gap-2 overflow-x-auto pb-2">
                {images.slice(0, 8).map((img, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedImageIndex(index)}
                    className={`flex-shrink-0 w-20 h-16 rounded overflow-hidden border-2 transition-colors ${
                      index === selectedImageIndex ? 'border-[#00E5FF]' : 'border-transparent'
                    }`}
                  >
                    <img
                      src={img}
                      alt={`Фото ${index + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
                      }}
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Details Section */}
          <div>
            <div className="mb-6">
              <p className="text-slate-400 text-sm mb-1">{car.brand}</p>
              <h1 className="text-3xl font-bold text-white mb-2">{car.model}</h1>
              
              <div className="flex items-center gap-4 mb-4">
                <span className="text-[#00E5FF] text-3xl font-bold">
                  {formatPrice(car.price_from_cny)}
                </span>
                <span className="text-slate-400 text-sm">
                  ≈ ${car.price_from_cny ? Math.round(car.price_from_cny / 7.2).toLocaleString() : '—'} USD
                </span>
              </div>

              {car.address && (
                <div className="flex items-center gap-2 text-slate-400 mb-4">
                  <MapPin size={16} />
                  <span>{car.address}</span>
                </div>
              )}
            </div>

            {/* Key Specs */}
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-1">
                  <Calendar size={16} />
                  <span className="text-sm">Год выпуска</span>
                </div>
                <p className="text-white font-semibold">{car.year_from} г.</p>
              </div>
              
              <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-1">
                  <Gauge size={16} />
                  <span className="text-sm">Пробег</span>
                </div>
                <p className="text-white font-semibold">{formatMileage(car.mileage)}</p>
              </div>
              
              <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-1">
                  {getEngineIcon(car.engine_type)}
                  <span className="text-sm">Двигатель</span>
                </div>
                <p className="text-white font-semibold">{getEngineLabel(car.engine_type)}</p>
              </div>
              
              <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
                <div className="flex items-center gap-2 text-slate-400 mb-1">
                  <Car size={16} />
                  <span className="text-sm">Кузов</span>
                </div>
                <p className="text-white font-semibold">{getBodyLabel(car.body_type)}</p>
              </div>
            </div>

            {/* Additional Info */}
            <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 mb-6">
              <h3 className="text-white font-semibold mb-4">Характеристики</h3>
              <div className="space-y-3">
                {car.color && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Цвет</span>
                    <span className="text-white">{car.color}</span>
                  </div>
                )}
                {car.transmission && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">КПП</span>
                    <span className="text-white">{car.transmission}</span>
                  </div>
                )}
                {car.drive_type && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Привод</span>
                    <span className="text-white">{car.drive_type}</span>
                  </div>
                )}
                {car.power && car.power > 0 && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Мощность</span>
                    <span className="text-white">{car.power} л.с.</span>
                  </div>
                )}
                {car.engine_volume && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Объём двигателя</span>
                    <span className="text-white">{(car.engine_volume / 1000).toFixed(1)} л</span>
                  </div>
                )}
                {car.vin && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">VIN</span>
                    <span className="text-white font-mono text-sm">{car.vin}</span>
                  </div>
                )}
                {car.offer_created && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Дата объявления</span>
                    <span className="text-white">{car.offer_created}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-4">
              <Button
                onClick={handleAddToGarage}
                disabled={addingToGarage}
                className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black font-semibold py-6"
                data-testid="add-to-garage-btn"
              >
                {addingToGarage ? (
                  <Loader2 size={20} className="animate-spin mr-2" />
                ) : (
                  <Plus size={20} className="mr-2" />
                )}
                Добавить в гараж
              </Button>
              
              {car.source_url && (
                <a
                  href={car.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-6 py-3 border border-[#27272A] rounded-lg text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF] transition-colors flex items-center gap-2"
                >
                  <ExternalLink size={20} />
                  Che168
                </a>
              )}
            </div>

            {/* Dealer info */}
            {car.is_dealer && (
              <div className="mt-4 flex items-center gap-2 text-emerald-400 text-sm">
                <Shield size={16} />
                <span>Официальный дилер</span>
              </div>
            )}
          </div>
        </div>

        {/* Description */}
        {car.description && (
          <div className="mt-8 bg-[#15191E] border border-[#27272A] rounded-lg p-6">
            <h3 className="text-white font-semibold mb-4">Описание</h3>
            <p className="text-slate-400 whitespace-pre-wrap">{car.description}</p>
          </div>
        )}
      </main>

      {/* Image Gallery Modal */}
      {showGallery && images.length > 0 && (
        <div className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center">
          <button
            onClick={() => setShowGallery(false)}
            className="absolute top-4 right-4 p-2 text-white hover:text-[#00E5FF] transition-colors"
          >
            <X size={32} />
          </button>
          
          <button
            onClick={() => setSelectedImageIndex(prev => prev > 0 ? prev - 1 : images.length - 1)}
            className="absolute left-4 p-2 text-white hover:text-[#00E5FF] transition-colors"
          >
            <ChevronLeft size={48} />
          </button>
          
          <img
            src={images[selectedImageIndex]}
            alt={`Фото ${selectedImageIndex + 1}`}
            className="max-w-[90vw] max-h-[90vh] object-contain"
            onError={(e) => {
              e.target.src = 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
            }}
          />
          
          <button
            onClick={() => setSelectedImageIndex(prev => prev < images.length - 1 ? prev + 1 : 0)}
            className="absolute right-4 p-2 text-white hover:text-[#00E5FF] transition-colors"
          >
            <ChevronRight size={48} />
          </button>
          
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 text-white">
            {selectedImageIndex + 1} / {images.length}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-[#15191E] border-t border-[#27272A] py-8 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <Logo />
            <p className="text-slate-500 text-sm">
              © 2025 CARBRIDGE. Все права защищены.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default CarDetailPage;
