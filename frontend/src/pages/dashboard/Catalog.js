import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { 
  Search, 
  Car, 
  Filter, 
  ChevronDown, 
  ChevronUp,
  Fuel,
  Gauge,
  Calendar,
  Plus,
  Loader2,
  X,
  RotateCcw,
  DollarSign,
  Speedometer
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const DashboardCatalog = () => {
  const { token } = useAuth();
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState(null);
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    yearFrom: '',
    yearTo: '',
    priceFrom: '',
    priceTo: '',
    mileageFrom: '',
    mileageTo: '',
    engineType: ''
  });
  const [showFilters, setShowFilters] = useState(true);
  const [addingToGarage, setAddingToGarage] = useState(null);
  const [totalResults, setTotalResults] = useState(0);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const response = await axios.get(`${API}/api/catalog/brands`);
      setBrands(response.data);
    } catch (error) {
      console.error('Error fetching brands:', error);
    }
  };

  const fetchModels = async (brandSlug) => {
    setLoadingModels(true);
    try {
      const response = await axios.get(`${API}/api/catalog/brands/${brandSlug}/models`);
      setModels(response.data);
    } catch (error) {
      console.error('Error fetching models:', error);
      setModels([]);
    } finally {
      setLoadingModels(false);
    }
  };

  const searchCars = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (selectedBrand) params.append('brand', selectedBrand.name);
      if (selectedModel) params.append('model', selectedModel.name || selectedModel);
      if (filters.yearFrom) params.append('year_from', filters.yearFrom);
      if (filters.yearTo) params.append('year_to', filters.yearTo);
      if (filters.priceFrom) params.append('price_from', filters.priceFrom);
      if (filters.priceTo) params.append('price_to', filters.priceTo);
      if (filters.mileageFrom) params.append('mileage_from', filters.mileageFrom);
      if (filters.mileageTo) params.append('mileage_to', filters.mileageTo);
      if (filters.engineType) params.append('engine_type', filters.engineType);

      const response = await axios.get(`${API}/api/catalog/search?${params.toString()}`);
      setCars(response.data.cars || []);
      setTotalResults(response.data.total || response.data.cars?.length || 0);
    } catch (error) {
      console.error('Error searching cars:', error);
      toast.error('Ошибка поиска');
    } finally {
      setLoading(false);
    }
  };

  const addToGarage = async (car) => {
    setAddingToGarage(car.id);
    try {
      await axios.post(`${API}/api/garage`, {
        brand: car.brand,
        model: car.model,
        year: car.year,
        price_cny: car.price,
        engine_type: car.engine_type || 'petrol',
        engine_volume: car.engine_volume,
        mileage: car.mileage,
        image_url: car.image_url,
        source_url: car.source_url,
        description: car.description
      }, { headers });
      toast.success('Авто добавлено в гараж');
    } catch (error) {
      toast.error('Ошибка добавления в гараж');
    } finally {
      setAddingToGarage(null);
    }
  };

  const handleBrandSelect = (brand) => {
    if (selectedBrand?.slug === brand.slug) {
      // Deselect
      setSelectedBrand(null);
      setModels([]);
      setSelectedModel(null);
    } else {
      setSelectedBrand(brand);
      setSelectedModel(null);
      fetchModels(brand.slug);
    }
  };

  const handleModelSelect = (model) => {
    if (selectedModel === model) {
      setSelectedModel(null);
    } else {
      setSelectedModel(model);
    }
  };

  const resetFilters = () => {
    setSelectedBrand(null);
    setSelectedModel(null);
    setModels([]);
    setSearchQuery('');
    setFilters({
      yearFrom: '',
      yearTo: '',
      priceFrom: '',
      priceTo: '',
      mileageFrom: '',
      mileageTo: '',
      engineType: ''
    });
    setCars([]);
    setTotalResults(0);
  };

  const engineTypes = [
    { value: '', label: 'Любой тип' },
    { value: 'petrol', label: 'Бензин' },
    { value: 'diesel', label: 'Дизель' },
    { value: 'electric', label: 'Электро' },
    { value: 'hybrid', label: 'Гибрид' },
    { value: 'phev', label: 'Плагин-гибрид' }
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 30 }, (_, i) => currentYear - i);

  const hasActiveFilters = selectedBrand || selectedModel || searchQuery || 
    filters.yearFrom || filters.yearTo || filters.priceFrom || filters.priceTo ||
    filters.mileageFrom || filters.mileageTo || filters.engineType;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Каталог автомобилей</h1>
          <p className="text-slate-400 mt-1">Поиск и подбор авто из Китая</p>
        </div>
        {hasActiveFilters && (
          <Button
            onClick={resetFilters}
            variant="outline"
            size="sm"
            className="border-[#27272A] text-slate-400 hover:text-white"
          >
            <RotateCcw size={16} className="mr-2" />
            Сбросить фильтры
          </Button>
        )}
      </div>

      {/* Search Bar */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
        <div className="flex gap-3">
          <div className="relative flex-1">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <Input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Поиск по марке, модели..."
              className="pl-10 bg-[#0B0F14] border-[#27272A] text-white"
              onKeyDown={(e) => e.key === 'Enter' && searchCars()}
            />
          </div>
          <Button
            onClick={() => setShowFilters(!showFilters)}
            variant="outline"
            className={`border-[#27272A] ${showFilters ? 'bg-[#27272A] text-white' : 'text-slate-300'}`}
          >
            <Filter size={18} className="mr-2" />
            Фильтры
            {showFilters ? <ChevronUp size={16} className="ml-2" /> : <ChevronDown size={16} className="ml-2" />}
          </Button>
          <Button
            onClick={searchCars}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black px-6"
          >
            <Search size={18} className="mr-2" />
            Найти
          </Button>
        </div>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-6 space-y-6">
          {/* Brand Selection */}
          <div>
            <Label className="text-white font-medium mb-3 flex items-center gap-2">
              <Car size={16} className="text-[#00E5FF]" />
              Марка автомобиля
            </Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {brands.slice(0, 24).map(brand => (
                <button
                  key={brand.slug}
                  onClick={() => handleBrandSelect(brand)}
                  className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                    selectedBrand?.slug === brand.slug
                      ? 'bg-[#00E5FF] text-black font-medium'
                      : 'bg-[#0B0F14] text-slate-300 hover:bg-[#27272A] border border-[#27272A]'
                  }`}
                >
                  {brand.name}
                  <span className="ml-1 opacity-60">({brand.count})</span>
                </button>
              ))}
            </div>
          </div>

          {/* Model Selection - Shows when brand is selected */}
          {selectedBrand && (
            <div className="border-t border-[#27272A] pt-4">
              <Label className="text-white font-medium mb-3 flex items-center gap-2">
                <Car size={16} className="text-[#00E5FF]" />
                Модель {selectedBrand.name}
              </Label>
              {loadingModels ? (
                <div className="flex items-center gap-2 text-slate-400 py-2">
                  <Loader2 size={16} className="animate-spin" />
                  <span>Загрузка моделей...</span>
                </div>
              ) : models.length > 0 ? (
                <div className="flex flex-wrap gap-2 mt-2">
                  {models.map((model, idx) => {
                    const modelName = typeof model === 'string' ? model : model.name;
                    const modelCount = typeof model === 'object' ? model.count : null;
                    return (
                      <button
                        key={idx}
                        onClick={() => handleModelSelect(modelName)}
                        className={`px-3 py-1.5 rounded-md text-sm transition-all ${
                          selectedModel === modelName
                            ? 'bg-[#00E5FF] text-black font-medium'
                            : 'bg-[#0B0F14] text-slate-300 hover:bg-[#27272A] border border-[#27272A]'
                        }`}
                      >
                        {modelName}
                        {modelCount && <span className="ml-1 opacity-60">({modelCount})</span>}
                      </button>
                    );
                  })}
                </div>
              ) : (
                <p className="text-slate-500 text-sm py-2">Модели не найдены</p>
              )}
            </div>
          )}

          {/* Other Filters Grid */}
          <div className="border-t border-[#27272A] pt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Engine Type */}
            <div>
              <Label className="text-slate-300 text-sm mb-2 flex items-center gap-2">
                <Fuel size={14} className="text-[#00E5FF]" />
                Тип двигателя
              </Label>
              <select
                value={filters.engineType}
                onChange={(e) => setFilters({...filters, engineType: e.target.value})}
                className="w-full bg-[#0B0F14] border border-[#27272A] text-white rounded-md px-3 py-2 text-sm"
              >
                {engineTypes.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* Year */}
            <div>
              <Label className="text-slate-300 text-sm mb-2 flex items-center gap-2">
                <Calendar size={14} className="text-[#00E5FF]" />
                Год выпуска
              </Label>
              <div className="flex gap-2">
                <select
                  value={filters.yearFrom}
                  onChange={(e) => setFilters({...filters, yearFrom: e.target.value})}
                  className="flex-1 bg-[#0B0F14] border border-[#27272A] text-white rounded-md px-3 py-2 text-sm"
                >
                  <option value="">От</option>
                  {years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
                <select
                  value={filters.yearTo}
                  onChange={(e) => setFilters({...filters, yearTo: e.target.value})}
                  className="flex-1 bg-[#0B0F14] border border-[#27272A] text-white rounded-md px-3 py-2 text-sm"
                >
                  <option value="">До</option>
                  {years.map(year => (
                    <option key={year} value={year}>{year}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Price */}
            <div>
              <Label className="text-slate-300 text-sm mb-2 flex items-center gap-2">
                <DollarSign size={14} className="text-[#00E5FF]" />
                Цена (¥)
              </Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="От"
                  value={filters.priceFrom}
                  onChange={(e) => setFilters({...filters, priceFrom: e.target.value})}
                  className="flex-1 bg-[#0B0F14] border-[#27272A] text-white text-sm"
                />
                <Input
                  type="number"
                  placeholder="До"
                  value={filters.priceTo}
                  onChange={(e) => setFilters({...filters, priceTo: e.target.value})}
                  className="flex-1 bg-[#0B0F14] border-[#27272A] text-white text-sm"
                />
              </div>
            </div>

            {/* Mileage */}
            <div>
              <Label className="text-slate-300 text-sm mb-2 flex items-center gap-2">
                <Gauge size={14} className="text-[#00E5FF]" />
                Пробег (км)
              </Label>
              <div className="flex gap-2">
                <Input
                  type="number"
                  placeholder="От"
                  value={filters.mileageFrom}
                  onChange={(e) => setFilters({...filters, mileageFrom: e.target.value})}
                  className="flex-1 bg-[#0B0F14] border-[#27272A] text-white text-sm"
                />
                <Input
                  type="number"
                  placeholder="До"
                  value={filters.mileageTo}
                  onChange={(e) => setFilters({...filters, mileageTo: e.target.value})}
                  className="flex-1 bg-[#0B0F14] border-[#27272A] text-white text-sm"
                />
              </div>
            </div>
          </div>

          {/* Active Filters Tags */}
          {hasActiveFilters && (
            <div className="border-t border-[#27272A] pt-4">
              <Label className="text-slate-400 text-xs mb-2 block">Активные фильтры:</Label>
              <div className="flex flex-wrap gap-2">
                {selectedBrand && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#00E5FF]/20 text-[#00E5FF] rounded text-xs">
                    Марка: {selectedBrand.name}
                    <X size={12} className="cursor-pointer hover:text-white" onClick={() => {
                      setSelectedBrand(null);
                      setModels([]);
                      setSelectedModel(null);
                    }} />
                  </span>
                )}
                {selectedModel && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#00E5FF]/20 text-[#00E5FF] rounded text-xs">
                    Модель: {selectedModel}
                    <X size={12} className="cursor-pointer hover:text-white" onClick={() => setSelectedModel(null)} />
                  </span>
                )}
                {filters.engineType && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#00E5FF]/20 text-[#00E5FF] rounded text-xs">
                    {engineTypes.find(t => t.value === filters.engineType)?.label}
                    <X size={12} className="cursor-pointer hover:text-white" onClick={() => setFilters({...filters, engineType: ''})} />
                  </span>
                )}
                {(filters.yearFrom || filters.yearTo) && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#00E5FF]/20 text-[#00E5FF] rounded text-xs">
                    Год: {filters.yearFrom || '...'} - {filters.yearTo || '...'}
                    <X size={12} className="cursor-pointer hover:text-white" onClick={() => setFilters({...filters, yearFrom: '', yearTo: ''})} />
                  </span>
                )}
                {(filters.priceFrom || filters.priceTo) && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#00E5FF]/20 text-[#00E5FF] rounded text-xs">
                    Цена: ¥{filters.priceFrom || '0'} - ¥{filters.priceTo || '∞'}
                    <X size={12} className="cursor-pointer hover:text-white" onClick={() => setFilters({...filters, priceFrom: '', priceTo: ''})} />
                  </span>
                )}
                {(filters.mileageFrom || filters.mileageTo) && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-[#00E5FF]/20 text-[#00E5FF] rounded text-xs">
                    Пробег: {filters.mileageFrom || '0'} - {filters.mileageTo || '∞'} км
                    <X size={12} className="cursor-pointer hover:text-white" onClick={() => setFilters({...filters, mileageFrom: '', mileageTo: ''})} />
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
        </div>
      ) : cars.length > 0 ? (
        <div>
          <div className="flex items-center justify-between mb-4">
            <p className="text-slate-400 text-sm">Найдено: <span className="text-white font-medium">{totalResults}</span> автомобилей</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {cars.map(car => (
              <div key={car.id} className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden hover:border-[#00E5FF]/50 transition-colors group">
                {/* Image */}
                <div className="aspect-video bg-[#0B0F14] relative overflow-hidden">
                  {car.image_url ? (
                    <img 
                      src={car.image_url} 
                      alt={`${car.brand} ${car.model}`} 
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" 
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Car size={48} className="text-slate-600" />
                    </div>
                  )}
                  {/* Quick Add Button */}
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
                  <h3 className="text-white font-semibold text-lg">{car.brand} {car.model}</h3>
                  
                  <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-400">
                      <Calendar size={14} />
                      <span>{car.year} г.</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Gauge size={14} />
                      <span>{car.mileage?.toLocaleString() || '—'} км</span>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400">
                      <Fuel size={14} />
                      <span>{car.engine_type || 'Бензин'}</span>
                    </div>
                    {car.engine_volume && (
                      <div className="flex items-center gap-2 text-slate-400">
                        <span className="text-xs bg-[#27272A] px-1.5 py-0.5 rounded">{car.engine_volume}L</span>
                      </div>
                    )}
                  </div>

                  <div className="mt-4 flex items-center justify-between">
                    <div>
                      <div className="text-[#00E5FF] text-xl font-bold">¥{car.price?.toLocaleString()}</div>
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
      ) : (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-white font-medium mb-2">Начните поиск</h3>
          <p className="text-slate-400">Выберите марку или используйте фильтры для поиска автомобилей</p>
          <Button
            onClick={searchCars}
            className="mt-4 bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
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
