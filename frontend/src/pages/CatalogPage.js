import { useState, useEffect, useCallback } from 'react';
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
  ArrowLeft,
  SlidersHorizontal
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Helper to proxy Chinese CDN images
const getProxiedImageUrl = (url) => {
  if (!url) return 'https://images.unsplash.com/photo-1619767886558-efdc259cde1a?w=800';
  // Check if it's a Chinese CDN image
  if (url.includes('autoimg.cn') || url.includes('che168.com') || url.includes('autohome.com')) {
    return `${API}/proxy/image?url=${encodeURIComponent(url)}`;
  }
  return url;
};

const CatalogPage = () => {
  const { isAuthenticated, token } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const [cars, setCars] = useState([]);
  const [brands, setBrands] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [pages, setPages] = useState(1);
  const [searchLinks, setSearchLinks] = useState({});
  const [showFilters, setShowFilters] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  
  const [filters, setFilters] = useState({
    query: searchParams.get('q') || '',
    brand: searchParams.get('brand') || '',
    model: searchParams.get('model') || '',
    engine_type: searchParams.get('engine') || '',
    body_type: searchParams.get('body') || '',
    min_price: searchParams.get('min_price') || '',
    max_price: searchParams.get('max_price') || '',
    min_year: searchParams.get('min_year') || '',
    max_year: searchParams.get('max_year') || '',
    page: parseInt(searchParams.get('page')) || 1
  });
  
  // State for excluded brands
  const [excludedBrands, setExcludedBrands] = useState([]);
  const [showExcludeBrands, setShowExcludeBrands] = useState(false);
  const [brandsInResults, setBrandsInResults] = useState([]);

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

  // Fetch models when brand changes
  useEffect(() => {
    const fetchModels = async () => {
      if (!filters.brand) {
        setModels([]);
        return;
      }
      
      try {
        // Find brand slug
        const selectedBrand = brands.find(b => b.name === filters.brand);
        if (selectedBrand) {
          const response = await axios.get(`${API}/catalog/models/${selectedBrand.slug}`);
          setModels(response.data);
        }
      } catch (error) {
        console.error('Error fetching models:', error);
        setModels([]);
      }
    };
    fetchModels();
  }, [filters.brand, brands]);

  // Auto-search when URL parameters are present on initial load
  useEffect(() => {
    const hasUrlParams = searchParams.get('brand') || searchParams.get('q') || 
                         searchParams.get('engine') || searchParams.get('body');
    if (hasUrlParams && !hasSearched) {
      searchCars();
    }
  }, [brands]); // Trigger after brands are loaded

  // Search cars function
  const searchCars = useCallback(async () => {
    // Don't search if no filters are applied
    const hasFilters = filters.query || filters.brand || filters.engine_type || 
                       filters.body_type || filters.min_price || filters.max_price ||
                       filters.min_year || filters.max_year || filters.model || excludedBrands.length > 0;
    
    if (!hasFilters && !hasSearched) {
      setCars([]);
      setTotal(0);
      setPages(1);
      return;
    }

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
      if (excludedBrands.length > 0) params.append('exclude_brands', excludedBrands.join(','));
      params.append('page', filters.page.toString());
      params.append('limit', '12');

      const response = await axios.get(`${API}/catalog/search?${params}`);
      const carsData = response.data.cars;
      setCars(carsData);
      setTotal(response.data.total);
      setPages(response.data.pages);
      setSearchLinks(response.data.search_links);
      
      // Get brands from API response
      setBrandsInResults(response.data.brands_in_results || []);
    } catch (error) {
      console.error('Error searching catalog:', error);
      toast.error('Ошибка при загрузке каталога');
    } finally {
      setLoading(false);
    }
  }, [filters, hasSearched, excludedBrands]);

  // Only search when page changes (for pagination)
  useEffect(() => {
    if (hasSearched) {
      searchCars();
    }
  }, [filters.page]);

  const handleSearch = (e) => {
    e.preventDefault();
    setFilters(prev => ({ ...prev, page: 1 }));
    searchCars();
  };

  const handleApplyFilters = () => {
    setFilters(prev => ({ ...prev, page: 1 }));
    setShowFilters(false);
    searchCars();
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    // Reset model when brand changes
    if (key === 'brand') {
      setFilters(prev => ({ ...prev, [key]: value, model: '' }));
    }
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
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
      page: 1
    });
    setExcludedBrands([]);
    setBrandsInResults([]);
    setCars([]);
    setTotal(0);
    setPages(1);
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
      wagon: 'Универсал',
      pickup: 'Пикап'
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
    if (!km) return null;
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
    filters.max_year
  ].filter(Boolean).length;

  // Generate year options
  const currentYear = new Date().getFullYear();
  const yearOptions = [];
  for (let y = currentYear; y >= 2015; y--) {
    yearOptions.push(y);
  }

  return (
    <div className="min-h-screen bg-[#0D1117]" data-testid="catalog-page">
      {/* Header */}
      <header className="bg-[#15191E]/80 backdrop-blur-md border-b border-[#27272A] sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/" className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors">
                <ArrowLeft size={20} />
              </Link>
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
        {/* Title & Description */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">Каталог авто из Китая</h1>
          <p className="text-slate-400">
            Реальные объявления с che168.com — крупнейшей площадки б/у авто в Китае
          </p>
          <p className="text-blue-400/80 text-xs mt-1 flex items-center gap-1">
            <span className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></span>
            Данные синхронизируются через API che168.com в реальном времени
          </p>
        </div>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="mb-6">
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
          <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 mb-6">
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
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {/* Brand */}
              <div>
                <Label className="text-slate-400 mb-2 block">Марка</Label>
                <Select value={filters.brand || "all"} onValueChange={(v) => handleFilterChange('brand', v === "all" ? "" : v)}>
                  <SelectTrigger className="bg-[#0D1117] border-[#27272A] text-white">
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
                  <SelectTrigger className="bg-[#0D1117] border-[#27272A] text-white">
                    <SelectValue placeholder={filters.brand ? "Выберите модель" : "Сначала выберите марку"} />
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
                  <SelectTrigger className="bg-[#0D1117] border-[#27272A] text-white">
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
                  <SelectTrigger className="bg-[#0D1117] border-[#27272A] text-white">
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

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              {/* Year From */}
              <div>
                <Label className="text-slate-400 mb-2 block">Год от</Label>
                <Select value={filters.min_year || "all"} onValueChange={(v) => handleFilterChange('min_year', v === "all" ? "" : v)}>
                  <SelectTrigger className="bg-[#0D1117] border-[#27272A] text-white">
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
                  <SelectTrigger className="bg-[#0D1117] border-[#27272A] text-white">
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
                  className="bg-[#0D1117] border-[#27272A] text-white placeholder:text-slate-500"
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
                  className="bg-[#0D1117] border-[#27272A] text-white placeholder:text-slate-500"
                />
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                onClick={handleApplyFilters}
                className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
              >
                Применить фильтры
              </Button>
            </div>
          </div>
        )}

        {/* Results Count with Brand Badges */}
        {hasSearched && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-3">
              <p className="text-slate-400">
                Найдено: <span className="text-white font-semibold">{total.toLocaleString()}</span> авто
              </p>
              {excludedBrands.length > 0 && (
                <button
                  onClick={() => setExcludedBrands([])}
                  className="text-sm text-[#00E5FF] hover:text-white transition-colors"
                >
                  Сбросить исключения ({excludedBrands.length})
                </button>
              )}
            </div>
            
            {/* Brand badges from results */}
            {brandsInResults.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {brandsInResults.map((brandName) => (
                  <button
                    key={brandName}
                    onClick={() => toggleExcludeBrand(brandName)}
                    className={`px-3 py-1.5 rounded-full text-sm font-medium transition-all ${
                      excludedBrands.includes(brandName)
                        ? 'bg-red-900/40 text-red-400 border border-red-700 line-through opacity-60'
                        : 'bg-[#1C2128] text-slate-300 border border-[#27272A] hover:border-[#00E5FF] hover:text-[#00E5FF]'
                    }`}
                  >
                    {brandName}
                    {excludedBrands.includes(brandName) && (
                      <X size={14} className="inline ml-1" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Initial State - No Search Yet */}
        {!hasSearched && !loading && (
          <div className="flex flex-col items-center justify-center py-20">
            <div className="w-24 h-24 bg-[#15191E] rounded-full flex items-center justify-center mb-6">
              <Search size={40} className="text-[#00E5FF]" />
            </div>
            <h2 className="text-xl font-semibold text-white mb-2">Начните поиск</h2>
            <p className="text-slate-400 text-center max-w-md mb-6">
              Введите название марки или модели в поисковую строку, либо используйте фильтры для поиска авто
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {['Geely', 'BYD', 'Changan', 'Haval', 'Li Auto'].map((brandName) => (
                <Button
                  key={brandName}
                  variant="outline"
                  onClick={async () => {
                    setFilters(prev => ({ ...prev, brand: brandName, page: 1 }));
                    setHasSearched(true);
                    setLoading(true);
                    try {
                      const params = new URLSearchParams();
                      params.append('brand', brandName);
                      params.append('page', '1');
                      params.append('limit', '12');
                      const response = await axios.get(`${API}/catalog/search?${params}`);
                      setCars(response.data.cars);
                      setTotal(response.data.total);
                      setPages(response.data.pages);
                      setSearchLinks(response.data.search_links);
                    } catch (error) {
                      console.error('Error:', error);
                      toast.error('Ошибка при загрузке');
                    } finally {
                      setLoading(false);
                    }
                  }}
                  className="border-[#27272A] text-slate-300 hover:bg-[#27272A] hover:border-[#00E5FF]"
                >
                  {brandName}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="animate-spin text-[#00E5FF]" size={40} />
          </div>
        )}

        {/* Cars Grid */}
        {hasSearched && !loading && cars.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8">
            {cars.map((car) => (
              <div
                key={car.id}
                data-testid={`car-card-${car.id}`}
                className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden card-hover group"
              >
                {/* Image - clickable */}
                <Link to={`/catalog/${car.id}`} className="block">
                  <div className="relative h-44 bg-[#1C2128]">
                    <img
                      src={getProxiedImageUrl(car.image_url)}
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
                    {car.source === 'che168' && (
                      <div className="absolute top-3 right-3 px-2 py-1 bg-blue-500/80 backdrop-blur-sm rounded text-xs text-white font-medium">
                        CHE168
                      </div>
                    )}
                  </div>
                </Link>

                {/* Content */}
                <div className="p-4">
                  <Link to={`/catalog/${car.id}`} className="block mb-2">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="text-slate-500 text-xs">{car.brand}</p>
                        <h3 className="text-white font-semibold hover:text-[#00E5FF] transition-colors">{car.model}</h3>
                      </div>
                      <div className="text-right">
                        <span className="text-[#00E5FF] font-bold text-lg">
                          {formatPrice(car.price_from_cny)}
                        </span>
                      </div>
                    </div>
                  </Link>

                  <div className="flex flex-wrap gap-1.5 mb-3">
                    <span className="px-2 py-0.5 bg-[#27272A] rounded text-xs text-slate-400">
                      {car.year_from} г
                    </span>
                    <span className="px-2 py-0.5 bg-[#27272A] rounded text-xs text-slate-400">
                      {getBodyLabel(car.body_type)}
                    </span>
                    {car.mileage && (
                      <span className="px-2 py-0.5 bg-[#27272A] rounded text-xs text-slate-400">
                        {formatMileage(car.mileage)}
                      </span>
                    )}
                    {car.color && (
                      <span className="px-2 py-0.5 bg-[#27272A] rounded text-xs text-slate-400">
                        {car.color}
                      </span>
                    )}
                  </div>

                  {car.address && (
                    <p className="text-slate-500 text-xs mb-2 truncate">
                      📍 {car.address}
                    </p>
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
                    {car.source_url ? (
                      <a
                        href={car.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 border border-[#27272A] rounded text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF] transition-colors"
                      >
                        <ExternalLink size={16} />
                      </a>
                    ) : (
                      <a
                        href={`https://www.che168.com/china/a0_0msdgscncgpi1ltocsp1exx0/?keyword=${encodeURIComponent(car.brand + ' ' + car.model)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 border border-[#27272A] rounded text-slate-400 hover:text-[#00E5FF] hover:border-[#00E5FF] transition-colors"
                      >
                        <ExternalLink size={16} />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : hasSearched && !loading && cars.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-20">
            <Car size={48} className="text-slate-600 mb-4" />
            <p className="text-slate-400 text-center">
              Авто не найдены. Попробуйте изменить параметры поиска.
            </p>
          </div>
        ) : null}

        {/* Pagination */}
        {hasSearched && pages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <Button
              variant="outline"
              onClick={() => handlePageChange(filters.page - 1)}
              disabled={filters.page === 1}
              className="border-[#27272A] text-slate-300 hover:bg-[#27272A]"
            >
              <ChevronLeft size={20} />
            </Button>
            
            <div className="flex items-center gap-1">
              {Array.from({ length: Math.min(5, pages) }, (_, i) => {
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
                      ? "bg-[#00E5FF] text-black hover:bg-[#22D3EE]" 
                      : "border-[#27272A] text-slate-300 hover:bg-[#27272A]"
                    }
                  >
                    {pageNum}
                  </Button>
                );
              })}
            </div>
            
            <Button
              variant="outline"
              onClick={() => handlePageChange(filters.page + 1)}
              disabled={filters.page === pages}
              className="border-[#27272A] text-slate-300 hover:bg-[#27272A]"
            >
              <ChevronRight size={20} />
            </Button>
          </div>
        )}

        {/* Search Links */}
        {hasSearched && Object.keys(searchLinks).length > 0 && (
          <div className="mt-12 p-6 bg-[#15191E] border border-[#27272A] rounded-lg">
            <h3 className="text-white font-semibold mb-4">Искать на китайских площадках</h3>
            <div className="flex flex-wrap gap-3">
              {Object.entries(searchLinks).map(([key, url]) => (
                <a
                  key={key}
                  href={url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-[#0D1117] border border-[#27272A] rounded-lg text-slate-300 hover:border-[#00E5FF] hover:text-[#00E5FF] transition-colors"
                >
                  <ExternalLink size={16} />
                  {key === 'che168' && 'Che168.com'}
                  {key === '58' && '58.com'}
                  {key === 'guazi' && 'Guazi.com'}
                  {key === 'dongchedi' && 'Dongchedi.com'}
                </a>
              ))}
            </div>
          </div>
        )}
      </main>

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

export default CatalogPage;
