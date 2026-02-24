import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { Logo } from '../components/Logo';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../components/ui/select";
import { 
  Search, 
  Filter, 
  Car, 
  Zap, 
  Fuel, 
  Battery,
  ExternalLink,
  Plus,
  ChevronLeft,
  ChevronRight,
  Loader2,
  X,
  ArrowLeft
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CatalogPage = () => {
  const { isAuthenticated, token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [cars, setCars] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [searchLinks, setSearchLinks] = useState({});
  const [showFilters, setShowFilters] = useState(false);
  
  const [filters, setFilters] = useState({
    query: searchParams.get('q') || '',
    brand: searchParams.get('brand') || '',
    engine_type: searchParams.get('engine') || '',
    body_type: searchParams.get('body') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    page: parseInt(searchParams.get('page')) || 1
  });

  // Fetch brands on mount
  useEffect(() => {
    const fetchBrands = async () => {
      try {
        const response = await axios.get(`${API}/catalog/brands`);
        setBrands(response.data);
      } catch (error) {
        console.error('Error fetching brands:', error);
      }
    };
    fetchBrands();
  }, []);

  // Search cars when filters change
  useEffect(() => {
    const searchCars = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (filters.query) params.append('query', filters.query);
        if (filters.brand) params.append('brand', filters.brand);
        if (filters.engine_type) params.append('engine_type', filters.engine_type);
        if (filters.body_type) params.append('body_type', filters.body_type);
        if (filters.min_price) params.append('min_price', filters.min_price);
        if (filters.max_price) params.append('max_price', filters.max_price);
        params.append('page', filters.page.toString());
        params.append('limit', '12');

        const response = await axios.get(`${API}/catalog/search?${params}`);
        setCars(response.data.cars);
        setTotal(response.data.total);
        setPages(response.data.pages);
        setSearchLinks(response.data.search_links);
      } catch (error) {
        console.error('Error searching catalog:', error);
      } finally {
        setLoading(false);
      }
    };
    searchCars();
  }, [filters]);

  const handleSearch = (e) => {
    e.preventDefault();
    setFilters(prev => ({ ...prev, page: 1 }));
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, page: 1 }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      brand: '',
      engine_type: '',
      body_type: '',
      min_price: '',
      max_price: '',
      page: 1
    });
  };

  const handleAddToGarage = async (carId) => {
    if (!isAuthenticated) {
      toast.error('Войдите в аккаунт для добавления в гараж');
      return;
    }
    
    try {
      await axios.post(`${API}/catalog/${carId}/add-to-garage`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Авто добавлено в гараж!');
    } catch (error) {
      toast.error('Ошибка при добавлении');
    }
  };

  const getEngineIcon = (type) => {
    switch (type) {
      case 'electric': return <Battery className="text-emerald-400" size={16} />;
      case 'hybrid': return <Zap className="text-amber-400" size={16} />;
      default: return <Fuel className="text-slate-400" size={16} />;
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
      shooting_brake: 'Shooting Brake'
    };
    return labels[type] || type;
  };

  const formatPrice = (price) => {
    if (price >= 10000) {
      return `¥${(price / 10000).toFixed(1)}万`;
    }
    return `¥${price.toLocaleString()}`;
  };

  const activeFiltersCount = [
    filters.brand,
    filters.engine_type,
    filters.body_type,
    filters.min_price,
    filters.max_price
  ].filter(Boolean).length;

  return (
    <div className="min-h-screen bg-[#0B0F14]">
      {/* Header */}
      <header className="bg-[#0B0F14]/90 backdrop-blur-md border-b border-[#27272A] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-6">
              <Link to="/" className="text-slate-400 hover:text-white transition-colors">
                <ArrowLeft size={20} />
              </Link>
              <Logo />
            </div>
            
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <Link to="/dashboard/garage">
                  <Button variant="outline" className="border-[#27272A] text-slate-300 hover:border-[#00E5FF]">
                    <Car size={18} className="mr-2" />
                    Мой гараж
                  </Button>
                </Link>
              ) : (
                <Link to="/auth">
                  <Button className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black">
                    Войти
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Title & Search */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Каталог авто из Китая</h1>
          <p className="text-slate-400">
            Популярные модели китайских автомобилей с ценами и характеристиками
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search size={20} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
              <Input
                data-testid="catalog-search-input"
                value={filters.query}
                onChange={(e) => setFilters(prev => ({ ...prev, query: e.target.value }))}
                placeholder="Поиск по марке, модели..."
                className="pl-12 bg-[#15191E] border-[#27272A] text-white h-12"
              />
            </div>
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowFilters(!showFilters)}
              className={`border-[#27272A] h-12 px-4 ${showFilters ? 'bg-[#00E5FF]/10 border-[#00E5FF] text-[#00E5FF]' : 'text-slate-400'}`}
            >
              <Filter size={18} className="mr-2" />
              Фильтры
              {activeFiltersCount > 0 && (
                <span className="ml-2 px-2 py-0.5 bg-[#00E5FF] text-black text-xs rounded-full">
                  {activeFiltersCount}
                </span>
              )}
            </Button>
            <Button type="submit" className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black h-12 px-6">
              Найти
            </Button>
          </div>
        </form>

        {/* Filters Panel */}
        {showFilters && (
          <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-white font-semibold">Фильтры</h3>
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearFilters}
                  className="text-slate-400 hover:text-[#00E5FF] text-sm flex items-center gap-1"
                >
                  <X size={14} /> Сбросить
                </button>
              )}
            </div>
            
            <div className="grid sm:grid-cols-2 lg:grid-cols-5 gap-4">
              {/* Brand */}
              <div>
                <Label className="text-slate-400 text-sm">Марка</Label>
                <Select value={filters.brand || "all"} onValueChange={(v) => handleFilterChange('brand', v === 'all' ? '' : v)}>
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A] text-white">
                    <SelectValue placeholder="Все марки" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1C2128] border-[#27272A]">
                    <SelectItem value="all">Все марки</SelectItem>
                    {brands.map(b => (
                      <SelectItem key={b.name} value={b.name}>
                        {b.name} ({b.count})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Engine Type */}
              <div>
                <Label className="text-slate-400 text-sm">Двигатель</Label>
                <Select value={filters.engine_type || "all"} onValueChange={(v) => handleFilterChange('engine_type', v === 'all' ? '' : v)}>
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A] text-white">
                    <SelectValue placeholder="Любой" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1C2128] border-[#27272A]">
                    <SelectItem value="all">Любой</SelectItem>
                    <SelectItem value="electric">Электро</SelectItem>
                    <SelectItem value="hybrid">Гибрид</SelectItem>
                    <SelectItem value="ice">ДВС</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Body Type */}
              <div>
                <Label className="text-slate-400 text-sm">Кузов</Label>
                <Select value={filters.body_type || "all"} onValueChange={(v) => handleFilterChange('body_type', v === 'all' ? '' : v)}>
                  <SelectTrigger className="mt-1 bg-[#0B0F14] border-[#27272A] text-white">
                    <SelectValue placeholder="Любой" />
                  </SelectTrigger>
                  <SelectContent className="bg-[#1C2128] border-[#27272A]">
                    <SelectItem value="">Любой</SelectItem>
                    <SelectItem value="sedan">Седан</SelectItem>
                    <SelectItem value="suv">Кроссовер</SelectItem>
                    <SelectItem value="hatchback">Хэтчбек</SelectItem>
                    <SelectItem value="mpv">Минивэн</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Price Range */}
              <div>
                <Label className="text-slate-400 text-sm">Цена от (¥)</Label>
                <Input
                  type="number"
                  value={filters.min_price}
                  onChange={(e) => handleFilterChange('min_price', e.target.value)}
                  placeholder="От"
                  className="mt-1 bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
              <div>
                <Label className="text-slate-400 text-sm">Цена до (¥)</Label>
                <Input
                  type="number"
                  value={filters.max_price}
                  onChange={(e) => handleFilterChange('max_price', e.target.value)}
                  placeholder="До"
                  className="mt-1 bg-[#0B0F14] border-[#27272A] text-white"
                />
              </div>
            </div>
          </div>
        )}

        {/* Results Count & External Links */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <p className="text-slate-400">
            Найдено: <span className="text-white font-medium">{total}</span> моделей
          </p>
          
          {/* Search on Chinese platforms */}
          <div className="flex items-center gap-2">
            <span className="text-slate-500 text-sm">Искать на:</span>
            {Object.entries(searchLinks).map(([platform, url]) => (
              <a
                key={platform}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 bg-[#1C2128] border border-[#27272A] rounded text-xs text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF] transition-colors"
              >
                {platform}
              </a>
            ))}
          </div>
        </div>

        {/* Cars Grid */}
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
          </div>
        ) : cars.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {cars.map((car) => (
              <div
                key={car.id}
                className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden card-hover group"
              >
                {/* Image */}
                <div className="relative h-44 bg-[#1C2128]">
                  <img
                    src={car.image_url}
                    alt={`${car.brand} ${car.model}`}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                      e.target.src = 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
                    }}
                  />
                  <div className="absolute top-3 left-3 flex items-center gap-1 px-2 py-1 bg-black/60 backdrop-blur-sm rounded text-xs">
                    {getEngineIcon(car.engine_type)}
                    <span className="text-white">{getEngineLabel(car.engine_type)}</span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <p className="text-slate-500 text-xs">{car.brand}</p>
                      <h3 className="text-white font-semibold">{car.model}</h3>
                    </div>
                    <span className="text-[#00E5FF] font-semibold text-sm">
                      {formatPrice(car.price_from_cny)}
                      {car.price_to_cny && car.price_to_cny !== car.price_from_cny && (
                        <span className="text-slate-500 font-normal"> — {formatPrice(car.price_to_cny)}</span>
                      )}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    <span className="px-2 py-0.5 bg-[#27272A] rounded text-xs text-slate-400">
                      {car.year_from}{car.year_to && car.year_to !== car.year_from ? `-${car.year_to}` : ''}
                    </span>
                    <span className="px-2 py-0.5 bg-[#27272A] rounded text-xs text-slate-400">
                      {getBodyLabel(car.body_type)}
                    </span>
                  </div>

                  <p className="text-slate-400 text-xs line-clamp-2 mb-4">
                    {car.description}
                  </p>

                  {/* Features */}
                  {car.features && car.features.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-4">
                      {car.features.slice(0, 2).map((f, i) => (
                        <span key={i} className="px-2 py-0.5 bg-[#00E5FF]/10 text-[#00E5FF] rounded text-xs">
                          {f}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      data-testid={`add-to-garage-${car.id}`}
                      onClick={() => handleAddToGarage(car.id)}
                      className="flex-1 bg-[#00E5FF] hover:bg-[#22D3EE] text-black text-sm h-9"
                    >
                      <Plus size={14} className="mr-1" />
                      В гараж
                    </Button>
                    <a
                      href={`https://www.dongchedi.com/search?keyword=${encodeURIComponent(car.brand + ' ' + car.model)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="p-2 border border-[#27272A] rounded text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF] transition-colors"
                    >
                      <ExternalLink size={16} />
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-16 bg-[#15191E] border border-[#27272A] rounded-lg">
            <Car size={64} className="mx-auto mb-4 text-slate-600" />
            <h3 className="text-xl font-semibold text-white mb-2">Ничего не найдено</h3>
            <p className="text-slate-400 mb-6">Попробуйте изменить параметры поиска</p>
            <Button onClick={clearFilters} variant="outline" className="border-[#27272A] text-slate-300">
              Сбросить фильтры
            </Button>
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <Button
              variant="outline"
              onClick={() => handlePageChange(filters.page - 1)}
              disabled={filters.page === 1}
              className="border-[#27272A] text-slate-400 disabled:opacity-50"
            >
              <ChevronLeft size={18} />
            </Button>
            
            {[...Array(Math.min(5, pages))].map((_, i) => {
              let pageNum;
              if (pages <= 5) {
                pageNum = i + 1;
              } else if (filters.page <= 3) {
                pageNum = i + 1;
              } else if (filters.page >= pages - 2) {
                pageNum = pages - 4 + i;
              } else {
                pageNum = filters.page - 2 + i;
              }
              
              return (
                <Button
                  key={pageNum}
                  variant={filters.page === pageNum ? "default" : "outline"}
                  onClick={() => handlePageChange(pageNum)}
                  className={filters.page === pageNum 
                    ? "bg-[#00E5FF] text-black" 
                    : "border-[#27272A] text-slate-400"
                  }
                >
                  {pageNum}
                </Button>
              );
            })}
            
            <Button
              variant="outline"
              onClick={() => handlePageChange(filters.page + 1)}
              disabled={filters.page === pages}
              className="border-[#27272A] text-slate-400 disabled:opacity-50"
            >
              <ChevronRight size={18} />
            </Button>
          </div>
        )}

        {/* Info Section */}
        <div className="mt-12 bg-[#15191E] border border-[#27272A] rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4">Как пользоваться каталогом</h3>
          <div className="grid md:grid-cols-3 gap-6 text-sm">
            <div>
              <div className="w-10 h-10 bg-[#00E5FF]/10 rounded-full flex items-center justify-center mb-3">
                <span className="text-[#00E5FF] font-bold">1</span>
              </div>
              <h4 className="text-white font-medium mb-1">Выберите модель</h4>
              <p className="text-slate-400">Используйте фильтры для поиска подходящего авто по параметрам</p>
            </div>
            <div>
              <div className="w-10 h-10 bg-[#00E5FF]/10 rounded-full flex items-center justify-center mb-3">
                <span className="text-[#00E5FF] font-bold">2</span>
              </div>
              <h4 className="text-white font-medium mb-1">Добавьте в гараж</h4>
              <p className="text-slate-400">Нажмите "В гараж" чтобы сохранить авто для дальнейшей работы</p>
            </div>
            <div>
              <div className="w-10 h-10 bg-[#00E5FF]/10 rounded-full flex items-center justify-center mb-3">
                <span className="text-[#00E5FF] font-bold">3</span>
              </div>
              <h4 className="text-white font-medium mb-1">Запустите тендер</h4>
              <p className="text-slate-400">В личном кабинете запустите тендер и получите предложения от подрядчиков</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default CatalogPage;
