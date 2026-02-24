import { Link } from 'react-router-dom';

export const Logo = ({ className = "", size = "default" }) => {
  const sizes = {
    small: "text-xl",
    default: "text-2xl",
    large: "text-4xl"
  };

  return (
    <Link to="/" className={`font-bold tracking-tight ${sizes[size]} ${className}`} style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
      <span className="text-white">CAR</span>
      <span className="text-[#00E5FF]">BRIDGE</span>
    </Link>
  );
};

export default Logo;
