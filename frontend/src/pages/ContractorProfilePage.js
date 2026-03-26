import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import {
  Building2, Star, MapPin, Clock, Users, Award, Briefcase, Globe,
  Phone, Mail, MessageCircle, ExternalLink, ChevronLeft, BadgeCheck,
  Settings, Calendar, Shield, ArrowLeft, Image
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const ContractorProfilePage = () => {
  const { contractorId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const res = await axios.get(`${API}/contractors/${contractorId}/page`);
        setData(res.data);
      } catch (e) {
        console.error(e);
      } finally { setLoading(false); }
    })();
  }, [contractorId]);

  if (loading) return (
    <div className="min-h-screen bg-[#0B0F14] flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-[#00E5FF] border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!data) return (
    <div className="min-h-screen bg-[#0B0F14] flex flex-col items-center justify-center text-white">
      <p className="text-xl mb-4">Подрядчик не найден</p>
      <Link to="/contractors" className="text-[#00E5FF] hover:underline">Вернуться к списку</Link>
    </div>
  );

  const { contractor: c, profile: p, files } = data;
  const facilityPhotos = (files || []).filter(f => f.category === 'facility');
  const certificateFiles = (files || []).filter(f => f.category === 'certificate');

  return (
    <div className="min-h-screen bg-[#0B0F14] text-white">
      {/* Header */}
      <div className="bg-gradient-to-b from-[#15191E] to-[#0B0F14] border-b border-[#27272A]">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <Link to="/contractors" className="inline-flex items-center gap-1 text-slate-400 hover:text-[#00E5FF] text-sm mb-4 transition-colors">
            <ArrowLeft size={14} /> Все подрядчики
          </Link>

          <div className="flex items-start gap-5">
            <div className="w-20 h-20 bg-[#1E2329] border border-[#27272A] rounded-lg flex items-center justify-center flex-shrink-0">
              <Building2 size={36} className="text-[#00E5FF]" />
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h1 className="text-2xl font-bold">{c.company_name}</h1>
                {c.verified && <BadgeCheck size={22} className="text-[#00E5FF]" />}
              </div>
              {p?.slogan && <p className="text-slate-400 text-sm mb-3 italic">"{p.slogan}"</p>}
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  {[1,2,3,4,5].map(s => (
                    <Star key={s} size={14} className={s <= (c.rating || 5) ? 'text-amber-400 fill-amber-400' : 'text-slate-600'} />
                  ))}
                  <span className="text-slate-400 ml-1">{c.rating || 5.0}</span>
                </div>
                {p?.city && <span className="text-slate-400 flex items-center gap-1"><MapPin size={12} />{p.city}</span>}
                {p?.founded_year && <span className="text-slate-400 flex items-center gap-1"><Calendar size={12} />С {p.founded_year} г.</span>}
                {p?.employees_count && <span className="text-slate-400 flex items-center gap-1"><Users size={12} />{p.employees_count} сотрудников</span>}
                <span className="text-emerald-400 flex items-center gap-1"><Shield size={12} />{c.completed_deals} завершённых сделок</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* About */}
        {p?.about && (
          <section>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Building2 size={18} className="text-purple-400" /> О компании</h2>
            <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-5">
              <p className="text-slate-300 leading-relaxed">{p.about}</p>
              <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                {p.address && (
                  <div className="bg-[#0B0F14] p-3 rounded">
                    <p className="text-slate-500 text-xs mb-1">Адрес</p>
                    <p className="text-slate-300 text-sm">{p.address}</p>
                  </div>
                )}
                {p.working_hours && (
                  <div className="bg-[#0B0F14] p-3 rounded">
                    <p className="text-slate-500 text-xs mb-1">Часы работы</p>
                    <p className="text-slate-300 text-sm">{p.working_hours}</p>
                  </div>
                )}
                {p.languages?.length > 0 && (
                  <div className="bg-[#0B0F14] p-3 rounded">
                    <p className="text-slate-500 text-xs mb-1">Языки</p>
                    <p className="text-slate-300 text-sm">{p.languages.join(', ')}</p>
                  </div>
                )}
                {c.services?.length > 0 && (
                  <div className="bg-[#0B0F14] p-3 rounded">
                    <p className="text-slate-500 text-xs mb-1">Услуги</p>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {c.services.map(s => <span key={s} className="px-2 py-0.5 bg-[#15191E] text-[#00E5FF] text-xs rounded">{s}</span>)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* Contacts */}
        <section>
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Phone size={18} className="text-cyan-400" /> Контакты</h2>
          <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-5">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {c.contact_person && (
                <div className="bg-[#0B0F14] p-3 rounded">
                  <p className="text-slate-500 text-xs mb-1">Контактное лицо</p>
                  <p className="text-white text-sm">{c.contact_person}</p>
                </div>
              )}
              {c.phone && (
                <div className="bg-[#0B0F14] p-3 rounded">
                  <p className="text-slate-500 text-xs mb-1">Телефон</p>
                  <a href={`tel:${c.phone}`} className="text-[#00E5FF] text-sm hover:underline">{c.phone}</a>
                </div>
              )}
              {c.email && (
                <div className="bg-[#0B0F14] p-3 rounded">
                  <p className="text-slate-500 text-xs mb-1">Email</p>
                  <a href={`mailto:${c.email}`} className="text-[#00E5FF] text-sm hover:underline">{c.email}</a>
                </div>
              )}
              {c.telegram && (
                <div className="bg-[#0B0F14] p-3 rounded">
                  <p className="text-slate-500 text-xs mb-1">Telegram</p>
                  <span className="text-slate-300 text-sm">{c.telegram}</span>
                </div>
              )}
              {c.whatsapp && (
                <div className="bg-[#0B0F14] p-3 rounded">
                  <p className="text-slate-500 text-xs mb-1">WhatsApp</p>
                  <span className="text-slate-300 text-sm">{c.whatsapp}</span>
                </div>
              )}
              {c.website && (
                <div className="bg-[#0B0F14] p-3 rounded">
                  <p className="text-slate-500 text-xs mb-1">Сайт</p>
                  <a href={c.website} target="_blank" rel="noopener noreferrer" className="text-[#00E5FF] text-sm hover:underline flex items-center gap-1"><Globe size={12} /> Открыть</a>
                </div>
              )}
            </div>
            {/* Social links */}
            {p?.social_links && Object.values(p.social_links).some(v => v) && (
              <div className="mt-4 flex flex-wrap gap-2">
                {Object.entries(p.social_links).map(([k, v]) => v ? (
                  <a key={k} href={v} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-[#0B0F14] rounded text-sm text-slate-300 hover:text-[#00E5FF] transition-colors">
                    <ExternalLink size={12} /> {k.charAt(0).toUpperCase() + k.slice(1)}
                  </a>
                ) : null)}
              </div>
            )}
          </div>
        </section>

        {/* Staff */}
        {p?.staff?.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Users size={18} className="text-blue-400" /> Команда</h2>
            <div className="grid md:grid-cols-3 gap-4">
              {p.staff.map((s, i) => (
                <div key={i} className="bg-[#15191E] border border-[#27272A] rounded-sm p-4">
                  <div className="w-12 h-12 bg-[#0B0F14] rounded-full flex items-center justify-center mb-3">
                    <Users size={20} className="text-blue-400" />
                  </div>
                  <h4 className="text-white font-medium">{s.name}</h4>
                  <p className="text-[#00E5FF] text-sm mb-2">{s.position}</p>
                  {s.description && <p className="text-slate-400 text-sm">{s.description}</p>}
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Certificates */}
        {(p?.certificates?.length > 0 || certificateFiles.length > 0) && (
          <section>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Award size={18} className="text-amber-400" /> Сертификаты и лицензии</h2>
            <div className="bg-[#15191E] border border-[#27272A] rounded-sm p-5">
              {p.certificates?.length > 0 && (
                <div className="space-y-3 mb-4">
                  {p.certificates.map((cert, i) => (
                    <div key={i} className="flex items-start gap-3 bg-[#0B0F14] p-3 rounded">
                      <Award size={20} className="text-amber-400 flex-shrink-0 mt-0.5" />
                      <div>
                        <h4 className="text-white font-medium text-sm">{cert.title}</h4>
                        {cert.description && <p className="text-slate-400 text-sm">{cert.description}</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {certificateFiles.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {certificateFiles.map(f => (
                    <a key={f.id} href={`${API}/profile-files/${f.id}/download`} target="_blank" rel="noopener noreferrer"
                      className="bg-[#0B0F14] p-3 rounded text-center hover:border-amber-400/50 border border-transparent transition-colors">
                      <Image size={24} className="text-slate-600 mx-auto mb-1" />
                      <p className="text-slate-400 text-xs truncate">{f.original_name}</p>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </section>
        )}

        {/* Portfolio */}
        {p?.portfolio_cases?.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Briefcase size={18} className="text-emerald-400" /> Портфолио</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {p.portfolio_cases.map((c, i) => (
                <div key={i} className="bg-[#15191E] border border-[#27272A] rounded-sm p-5">
                  <h4 className="text-white font-medium mb-2">{c.title}</h4>
                  <p className="text-slate-400 text-sm leading-relaxed">{c.description}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Facility Photos */}
        {facilityPhotos.length > 0 && (
          <section>
            <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><Image size={18} className="text-cyan-400" /> Фото офиса и площадок</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {facilityPhotos.map(f => (
                <a key={f.id} href={`${API}/profile-files/${f.id}/download`} target="_blank" rel="noopener noreferrer">
                  <img src={`${API}/profile-files/${f.id}/download`} alt={f.title || 'Фото'}
                    className="w-full h-40 object-cover rounded border border-[#27272A] hover:border-[#00E5FF]/50 transition-colors" />
                </a>
              ))}
            </div>
          </section>
        )}
      </div>
    </div>
  );
};

export default ContractorProfilePage;
