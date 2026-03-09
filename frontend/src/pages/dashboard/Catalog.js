import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../../contexts/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { 
  Search, 
  Car, 
  Filter, 
  ChevronDown, 
  ChevronUp,
  Star,
  Fuel,
  Gauge,
  Calendar,
  ExternalLink,
  Heart,
  Plus,
  Loader2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const DashboardCatalog = () => {
  const { token } = useAuth();
  const [brands, setBrands] = useState([]);
  const [selectedBrand, setSelectedBrand] = useState(null);
  const [models, setModels] = useState([]);
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    yearFrom: '',
    yearTo: '',
    priceFrom: '',
    priceTo: '',
    engineType: ''
  });
  const [showFilters, setShowFilters] = useState(false);
  const [addingToGarage, setAddingToGarage] = useState(null);

  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchBrands();
  }, []);

  const fetchBrands = async () => {
    try {
      const response = await axios.get(`${API}/catalog/brands`);
      setBrands(response.data);
    } catch (error) {
      console.error('Error fetching brands:', error);
    }
  };

  const fetchModels = async (brandId) => {
    try {
      const response = await axios.get(`${API}/catalog/brands/${brandId}/models`);
      setModels(response.data);
    } catch (error) {
      console.error('Error fetching models:', error);
    }
  };

  const searchCars = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('query', searchQuery);
      if (selectedBrand) params.append('brand', selectedBrand.name);
      if (filters.yearFrom) params.append('year_from', filters.yearFrom);
      if (filters.yearTo) params.append('year_to', filters.yearTo);
      if (filters.priceFrom) params.append('price_from', filters.priceFrom);
      if (filters.priceTo) params.append('price_to', filters.priceTo);
      if (filters.engineType) params.append('engine_type', filters.engineType);

      const response = await axios.get(`${API}/catalog/search?${params.toString()}`);
      setCars(response.data.cars || []);
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
      await axios.post(`${API}/garage`, {
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
    setSelectedBrand(brand);
    fetchModels(brand.slug);
    setTimeout(() => searchCars(), 100);
  };

  const engineTypes = [
    { value: '', label: 'Любой' },
    { value: 'petrol', label: 'Бензин' },
    { value: 'diesel', label: 'Дизель' },
    { value: 'electric', label: 'Электро' },
    { value: 'hybrid', label: 'Гибрид' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Каталог автомобилей</h1>
          <p className="text-slate-400 mt-1">Поиск и подбор авто из Китая</p>
        </div>
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
            className="border-[#27272A] text-slate-300"
          >
            <Filter size={18} className="mr-2" />
            Фильтры
            {showFilters ? <ChevronUp size={16} className="ml-2" /> : <ChevronDown size={16} className="ml-2" />}
          </Button>
          <Button
            onClick={searchCars}
            className="bg-[#00E5FF] hover:bg-[#22D3EE] text-black"
          >
            <Search size={18} className="mr-2" />
            Найти
          </Button>
        </div>

        {/* Filters */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-[#27272A] grid grid-cols-2 md:grid-cols-5 gap-3">
            <Input
              type="number"
              placeholder="Год от"
              value={filters.yearFrom}
              onChange={(e) => setFilters({...filters, yearFrom: e.target.value})}
              className="bg-[#0B0F14] border-[#27272A] text-white"
            />
            <Input
              type="number"
              placeholder="Год до"
              value={filters.yearTo}
              onChange={(e) => setFilters({...filters, yearTo: e.target.value})}
              className="bg-[#0B0F14] border-[#27272A] text-white"
            />
            <Input
              type="number"
              placeholder="Цена от (¥)"
              value={filters.priceFrom}
              onChange={(e) => setFilters({...filters, priceFrom: e.target.value})}
              className="bg-[#0B0F14] border-[#27272A] text-white"
            />
            <Input
              type="number"
              placeholder="Цена до (¥)"
              value={filters.priceTo}
              onChange={(e) => setFilters({...filters, priceTo: e.target.value})}
              className="bg-[#0B0F14] border-[#27272A] text-white"
            />
            <select
              value={filters.engineType}
              onChange={(e) => setFilters({...filters, engineType: e.target.value})}
              className="bg-[#0B0F14] border border-[#27272A] text-white rounded-md px-3"
            >
              {engineTypes.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Brands */}
      <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-4">
        <h3 className="text-white font-medium mb-3">Популярные марки</h3>
        <div className="flex flex-wrap gap-2">
          {brands.slice(0, 20).map(brand => (
            <button
              key={brand.id}
              onClick={() => handleBrandSelect(brand)}
              className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                selectedBrand?.id === brand.id
                  ? 'bg-[#00E5FF] text-black'
                  : 'bg-[#0B0F14] text-slate-300 hover:bg-[#27272A]'
              }`}
            >
              {brand.name} ({brand.count})
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 size={32} className="text-[#00E5FF] animate-spin" />
        </div>
      ) : cars.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {cars.map(car => (
            <div key={car.id} className="bg-[#15191E] border border-[#27272A] rounded-lg overflow-hidden hover:border-[#00E5FF]/50 transition-colors">
              {/* Image */}
              <div className="aspect-video bg-[#0B0F14] relative">
                {car.image_url ? (
                  <img src={car.image_url} alt={`${car.brand} ${car.model}`} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Car size={48} className="text-slate-600" />
                  </div>
                )}
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
                      <span>{car.engine_volume}L</span>
                    </div>
                  )}
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <div>
                    <div className="text-[#00E5FF] text-xl font-bold">¥{car.price?.toLocaleString()}</div>
                    {car.price_usd && (
                      <div className="text-slate-400 text-sm">${car.price_usd?.toLocaleString()}</div>
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
      ) : (
        <div className="bg-[#15191E] border border-[#27272A] rounded-lg p-12 text-center">
          <Car size={48} className="mx-auto mb-4 text-slate-600" />
          <h3 className="text-white font-medium mb-2">Начните поиск</h3>
          <p className="text-slate-400">Выберите марку или введите запрос для поиска автомобилей</p>
        </div>
      )}
    </div>
  );
};

export default DashboardCatalog;
