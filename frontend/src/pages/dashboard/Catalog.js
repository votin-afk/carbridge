import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../components/ui/select";
import { 
  Search, 
  Car, 
  Zap, 
  Fuel, 
  Battery,
  Plus,
  Loader2,
  X,
  SlidersHorizontal,
  Gauge,
  Calendar,
  ExternalLink
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// Helper to proxy Chinese CDN images
const getProxiedImageUrl = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
  if (url.includes('autoimg.cn') || url.includes('che168.com') || url.includes('autohome.com')) {
    return `${API}/api/proxy/image?url=${encodeURIComponent(url)}`;
  }
  return url;
};

const DashboardCatalog = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [cars, setCars] = useState([]);
  const [brands, setBrands] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [showFilters, setShowFilters] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);
  const [addingToGarage, setAddingToGarage] = useState(null);
  
  // Excluded brands state
  const [excludedBrands, setExcludedBrands] = useState([]);
  const [showExcludeBrands, setShowExcludeBrands] = useState(false);
  const [brandsInResults, setBrandsInResults] = useState([]);
  
  const [filters, setFilters] = useState({
    query: '',
    brand: '',
    model: '',
    engine_type: '',
    body_type: '',
    min_price: '',
    max_price: '',
    min_year: '',
    max_year: '',
    min_mileage: '',
    max_mileage: ''
  });

  const headers = { Authorization: `Bearer ${token}` };

  // Fetch brands on mount
  useEffect(() => {
    const fetchBrands = async () => {
      try {
        const response = await axios.get(`${API}/api/catalog/brands`);
        setBrands(response.data);
      } catch (error) {
        console.error('Error fetching brands:', error);
      }
    };
    fetchBrands();
  }, []);

  // Fetch models when brand changes
  useEffect(() => {
    const fetchModels = async () => {
      if (!filters.brand) {
        setModels([]);
        return;
      }
      
      try {
        const selectedBrand = brands.find(b => b.name === filters.brand);
        if (selectedBrand) {
          const response = await axios.get(`${API}/api/catalog/models/${selectedBrand.slug}`);
          setModels(response.data);
        }
      } catch (error) {
        console.error('Error fetching models:', error);
        setModels([]);
      }
    };
    fetchModels();
  }, [filters.brand, brands]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => {
      const newFilters = { ...prev, [key]: value };
      // Clear model when brand changes
      if (key === 'brand') {
        newFilters.model = '';
      }
      return newFilters;
    });
  };

  const searchCars = useCallback(async () => {
    setLoading(true);
    setHasSearched(true);
    
    try {
      const params = new URLSearchParams();
      if (filters.query) params.append('query', filters.query);
      if (filters.brand) params.append('brand', filters.brand);
      if (filters.model) params.append('model', filters.model);
      if (filters.engine_type) params.append('engine_type', filters.engine_type);
      if (filters.body_type) params.append('body_type', filters.body_type);
      if (filters.min_price) params.append('min_price', filters.min_price);
      if (filters.max_price) params.append('max_price', filters.max_price);
      if (filters.min_year) params.append('min_year', filters.min_year);
      if (filters.max_year) params.append('max_year', filters.max_year);
      if (filters.min_mileage) params.append('mileage_from', filters.min_mileage);
      if (filters.max_mileage) params.append('mileage_to', filters.max_mileage);
      if (excludedBrands.length > 0) params.append('exclude_brands', excludedBrands.join(','));
      params.append('limit', '20');

      const response = await axios.get(`${API}/api/catalog/search?${params}`);
      setCars(response.data.cars || []);
      setTotal(response.data.total || response.data.cars?.length || 0);
    } catch (error) {
      console.error('Error searching cars:', error);
      toast.error('Ошибка поиска');
    } finally {
      setLoading(false);
    }
  }, [filters, excludedBrands]);

  const handleSearch = (e) => {
    e.preventDefault();
    searchCars();
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      brand: '',
      model: '',
      engine_type: '',
      body_type: '',
      min_price: '',
      max_price: '',
      min_year: '',
      max_year: '',
      min_mileage: '',
      max_mileage: ''
    });
    setExcludedBrands([]);
    setCars([]);
    setTotal(0);
    setHasSearched(false);
  };

  // Toggle brand exclusion
  const toggleExcludeBrand = (brandName) => {
    setExcludedBrands(prev => {
      if (prev.includes(brandName)) {
        return prev.filter(b => b !== brandName);
      } else {
        return [...prev, brandName];
      }
    });
  };

  // Remove excluded brand
  const removeExcludedBrand = (brandName) => {
    setExcludedBrands(prev => prev.filter(b => b !== brandName));
  };

  const addToGarage = async (car) => {
    setAddingToGarage(car.id);
    try {
      const response = await axios.post(`${API}/api/catalog/${car.id}/add-to-garage`, {}, { headers });
      toast.success(
        <div className="flex flex-col gap-2">
          <span>Авто добавлено в гараж!</span>
          <Button 
            size="sm" 
            onClick={() => navigate('/dashboard/garage')}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            <ExternalLink size={14} className="mr-1" />
            Перейти в гараж
          </Button>
        </div>,
        { duration: 5000 }
      );
    } catch (error) {
      toast.error('Ошибка при добавлении');
    } finally {
      setAddingToGarage(null);
    }
  };

  const getEngineIcon = (type) => {
    switch (type) {
      case 'electric': return <Battery className="text-emerald-400" size={14} />;
      case 'hybrid': return <Zap className="text-amber-400" size={14} />;
      default: return <Fuel className="text-slate-400" size={14} />;
    }
  };

  const formatPrice = (price) => {
    if (!price || price === 0) return '—';
    if (price >= 10000) {
      return `¥${(price / 10000).toFixed(2)}万`;
    }
    return `¥${price.toLocaleString()}`;
  };

  const formatMileage = (km) => {
    if (!km) return '—';
    return `${km.toLocaleString('ru-RU')} км`;
  };

  const activeFiltersCount = [
    filters.brand,
    filters.model,
    filters.engine_type,
    filters.body_type,
    filters.min_price,
    filters.max_price,
    filters.min_year,
    filters.max_year,
    filters.min_mileage,
    filters.max_mileage
  ].filter(Boolean).length;

  // Generate year options
  const currentYear = new Date().getFullYear();
  const yearOptions = [];
  for (let y = currentYear; y >= 2015; y--) {
    yearOptions.push(y);
  }

  return (
    <div className="space-y-6" data-testid="dashboard-catalog">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Каталог автомобилей</h1>
        <p className="text-slate-400 mt-1">
          Реальные объявления с che168.com — крупнейшей площадки б/у авто в Китае
        </p>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch}>
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={20} />
            <Input
              data-testid="catalog-search-input"
              type="text"
              placeholder="Поиск по марке, модели..."
              value={filters.query}
              onChange={(e) => handleFilterChange('query', e.target.value)}
              className="pl-10 bg-[#15191E] border-[#27272A] text-white placeholder:text-slate-500 h-12"
            />
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={() => setShowFilters(!showFilters)}
            className={`border-[#27272A] text-slate-300 hover:bg-[#27272A] h-12 px-4 ${activeFiltersCount > 0 ? 'border-[#00E5FF]' : ''}`}
          >
            <SlidersHorizontal size={20} className="mr-2" />
            Фильтры
            {activeFiltersCount > 0 && (
              <span className="ml-2 bg-[#00E5FF] text-black text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {activeFiltersCount}
              </span>
            )}
          </Button>
          <Button
            type="submit"
            data-testid="catalog-search-btn"
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black h-12 px-6"
          >
            <Search size={20} className="mr-2" />
            Найти
          </Button>
        </div>
      </form>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold">Фильтры</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="text-slate-400 hover:text-white"
            >
              <X size={16} className="mr-1" />
              Сбросить
            </Button>
          </div>
          
          {/* Row 1: Brand, Model, Engine, Body */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {/* Brand */}
            <div>
              <Label className="text-slate-400 mb-2 block">Марка</Label>
              <Select value={filters.brand || "all"} onValueChange={(v) => handleFilterChange('brand', v === "all" ? "" : v)}>
                <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                  <SelectValue placeholder="Все марки" />
                </SelectTrigger>
                <SelectContent className="bg-[#15191E] border-[#27272A] max-h-60">
                  <SelectItem value="all" className="text-white">Все марки</SelectItem>
                  {brands.slice(0, 50).map((b) => (
                    <SelectItem key={b.slug || b.name} value={b.name} className="text-white">
                      {b.name} ({b.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Model */}
            <div>
              <Label className="text-slate-400 mb-2 block">Модель</Label>
              <Select 
                value={filters.model || "all"} 
                onValueChange={(v) => handleFilterChange('model', v === "all" ? "" : v)}
                disabled={!filters.brand}
              >
                <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                  <SelectValue placeholder={filters.brand ? "Выберите модель" : "Сначала марку"} />
                </SelectTrigger>
                <SelectContent className="bg-[#15191E] border-[#27272A] max-h-60">
                  <SelectItem value="all" className="text-white">Все модели</SelectItem>
                  {models.map((m) => (
                    <SelectItem key={m.name} value={m.name} className="text-white">
                      {m.name} ({m.count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Engine Type */}
            <div>
              <Label className="text-slate-400 mb-2 block">Двигатель</Label>
              <Select value={filters.engine_type || "all"} onValueChange={(v) => handleFilterChange('engine_type', v === "all" ? "" : v)}>
                <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                  <SelectValue placeholder="Любой" />
                </SelectTrigger>
                <SelectContent className="bg-[#15191E] border-[#27272A]">
                  <SelectItem value="all" className="text-white">Любой</SelectItem>
                  <SelectItem value="ice" className="text-white">
                    <div className="flex items-center gap-2">
                      <Fuel size={14} className="text-slate-400" />
                      ДВС (бензин/дизель)
                    </div>
                  </SelectItem>
                  <SelectItem value="hybrid" className="text-white">
                    <div className="flex items-center gap-2">
                      <Zap size={14} className="text-amber-400" />
                      Гибрид
                    </div>
                  </SelectItem>
                  <SelectItem value="electric" className="text-white">
                    <div className="flex items-center gap-2">
                      <Battery size={14} className="text-emerald-400" />
                      Электро
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Body Type */}
            <div>
              <Label className="text-slate-400 mb-2 block">Кузов</Label>
              <Select value={filters.body_type || "all"} onValueChange={(v) => handleFilterChange('body_type', v === "all" ? "" : v)}>
                <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                  <SelectValue placeholder="Любой" />
                </SelectTrigger>
                <SelectContent className="bg-[#15191E] border-[#27272A]">
                  <SelectItem value="all" className="text-white">Любой</SelectItem>
                  <SelectItem value="sedan" className="text-white">Седан</SelectItem>
                  <SelectItem value="suv" className="text-white">Кроссовер / SUV</SelectItem>
                  <SelectItem value="hatchback" className="text-white">Хэтчбек</SelectItem>
                  <SelectItem value="mpv" className="text-white">Минивэн / MPV</SelectItem>
                  <SelectItem value="wagon" className="text-white">Универсал</SelectItem>
                  <SelectItem value="pickup" className="text-white">Пикап</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* Row 2: Year, Price */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {/* Year From */}
            <div>
              <Label className="text-slate-400 mb-2 block">Год от</Label>
              <Select value={filters.min_year || "all"} onValueChange={(v) => handleFilterChange('min_year', v === "all" ? "" : v)}>
                <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                  <SelectValue placeholder="Любой" />
                </SelectTrigger>
                <SelectContent className="bg-[#15191E] border-[#27272A] max-h-60">
                  <SelectItem value="all" className="text-white">Любой</SelectItem>
                  {yearOptions.map((y) => (
                    <SelectItem key={y} value={y.toString()} className="text-white">{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Year To */}
            <div>
              <Label className="text-slate-400 mb-2 block">Год до</Label>
              <Select value={filters.max_year || "all"} onValueChange={(v) => handleFilterChange('max_year', v === "all" ? "" : v)}>
                <SelectTrigger className="bg-[#0B0F14] border-[#27272A] text-white">
                  <SelectValue placeholder="Любой" />
                </SelectTrigger>
                <SelectContent className="bg-[#15191E] border-[#27272A] max-h-60">
                  <SelectItem value="all" className="text-white">Любой</SelectItem>
                  {yearOptions.map((y) => (
                    <SelectItem key={y} value={y.toString()} className="text-white">{y}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Price From */}
            <div>
              <Label className="text-slate-400 mb-2 block">Цена от (¥)</Label>
              <Input
                type="number"
                placeholder="От"
                value={filters.min_price}
                onChange={(e) => handleFilterChange('min_price', e.target.value)}
                className="bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
              />
            </div>

            {/* Price To */}
            <div>
              <Label className="text-slate-400 mb-2 block">Цена до (¥)</Label>
              <Input
                type="number"
                placeholder="До"
                value={filters.max_price}
                onChange={(e) => handleFilterChange('max_price', e.target.value)}
                className="bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
              />
            </div>
          </div>

          {/* Row 3: Mileage */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {/* Mileage From */}
            <div>
              <Label className="text-slate-400 mb-2 block">Пробег от (км)</Label>
              <Input
                type="number"
                placeholder="От"
                value={filters.min_mileage}
                onChange={(e) => handleFilterChange('min_mileage', e.target.value)}
                className="bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
              />
            </div>

            {/* Mileage To */}
            <div>
              <Label className="text-slate-400 mb-2 block">Пробег до (км)</Label>
              <Input
                type="number"
                placeholder="До"
                value={filters.max_mileage}
                onChange={(e) => handleFilterChange('max_mileage', e.target.value)}
                className="bg-[#0B0F14] border-[#27272A] text-white placeholder:text-slate-500"
              />
            </div>
          </div>

          {/* Excluded Brands Section */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <Label className="text-slate-400">Исключить марки</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowExcludeBrands(!showExcludeBrands)}
                className="text-[#00E5FF] hover:text-white text-sm"
              >
                {showExcludeBrands ? 'Скрыть' : 'Показать список'}
              </Button>
            </div>
            
            {/* Excluded brands tags */}
            {excludedBrands.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-3">
                {excludedBrands.map(brand => (
                  <span 
                    key={brand}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-red-900/30 text-red-400 border border-red-800 rounded-full text-sm"
                  >
                    <X size={12} />
                    {brand}
                    <button
                      onClick={() => removeExcludedBrand(brand)}
                      className="ml-1 hover:text-red-300"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Brand selection for exclusion */}
            {showExcludeBrands && (
              <div className="bg-[#0B0F14] border border-[#27272A] rounded-lg p-3 max-h-48 overflow-y-auto">
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                  {brands.slice(0, 50).map((b) => (
                    <label
                      key={b.slug || b.name}
                      className={`flex items-center gap-2 p-2 rounded cursor-pointer transition-colors ${
                        excludedBrands.includes(b.name) 
                          ? 'bg-red-900/30 border border-red-800' 
                          : 'hover:bg-slate-800 border border-transparent'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={excludedBrands.includes(b.name)}
                        onChange={() => toggleExcludeBrand(b.name)}
                        className="w-4 h-4 rounded border-slate-600 bg-slate-800 text-red-500 focus:ring-red-500"
                      />
                      <span className={`text-sm ${excludedBrands.includes(b.name) ? 'text-red-400' : 'text-slate-300'}`}>
                        {b.name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="flex justify-end">
            <Button
              onClick={searchCars}
              className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
            >
              Применить фильтры
            </Button>
          </div>
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
        </div>
      ) : hasSearched && cars.length > 0 ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-400">
              Найдено: <span className="text-white font-semibold">{total.toLocaleString()}</span> автомобилей
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cars.map(car => (
              <div key={car.id} className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden hover:border-[#00E5FF]/50 transition-colors group">
                {/* Image */}
                <div className="aspect-video bg-[#0B0F14] relative overflow-hidden">
                  <img 
                    src={getProxiedImageUrl(car.image_url)} 
                    alt={`${car.brand} ${car.model}`} 
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    onError={(e) => {
                      e.target.src = 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
                    }}
                  />
                  <button
                    onClick={() => addToGarage(car)}
                    disabled={addingToGarage === car.id}
                    className="absolute top-2 right-2 p-2 bg-black/60 hover:bg-emerald-500 rounded-full text-white transition-colors"
                    title="Добавить в гараж"
                  >
                    {addingToGarage === car.id ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <Plus size={16} />
                    )}
                  </button>
                </div>

                {/* Content */}
                <div className="p-4">
                  <h3 className="text-white font-semibold text-lg truncate">{car.brand} {car.model}</h3>
                  
                  <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-400">
                      <Calendar size={14} />
                      <span>{car.year_from || car.year || '—'} г.</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Gauge size={14} />
                      <span>{formatMileage(car.mileage)}</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      {getEngineIcon(car.engine_type)}
                      <span>{car.engine_type === 'electric' ? 'Электро' : car.engine_type === 'hybrid' ? 'Гибрид' : 'ДВС'}</span>
                    </div>
                    {car.engine_volume && car.engine_volume > 0 && (
                      <div className="flex items-center gap-2 text-slate-400">
                        <span className="text-xs bg-[#27272A] px-1.5 py-0.5 rounded">{car.engine_volume >= 100 ? (car.engine_volume / 1000).toFixed(1) : car.engine_volume}L</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      <div className="text-[#00E5FF] text-xl font-bold">{formatPrice(car.price_from_cny || car.price)}</div>
                      {car.price_usd && (
                        <div className="text-slate-400 text-sm">≈ ${car.price_usd?.toLocaleString()}</div>
                      )}
                    </div>
                    <Button
                      onClick={() => addToGarage(car)}
                      disabled={addingToGarage === car.id}
                      size="sm"
                      className="bg-emerald-500 hover:bg-emerald-600 text-white"
                    >
                      {addingToGarage === car.id ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <>
                          <Plus size={16} className="mr-1" />
                          В гараж
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : hasSearched ? (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-white font-medium mb-2">Ничего не найдено</h3>
          <p className="text-slate-400">Попробуйте изменить параметры поиска</p>
        </div>
      ) : (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-white font-medium mb-2">Начните поиск</h3>
          <p className="text-slate-400 mb-4">Используйте фильтры или поисковую строку для поиска автомобилей</p>
          <Button
            onClick={searchCars}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            <Search size={18} className="mr-2" />
            Показать все автомобили
          </Button>
        </div>
      )}
    </div>
  );
};

export default DashboardCatalog;
