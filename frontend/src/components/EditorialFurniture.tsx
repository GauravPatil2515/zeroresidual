import { useState, useRef, useEffect, type CSSProperties, type MouseEvent, type ReactNode } from 'react';

/**
 * The Signature House Accent Dot in Flame Vermilion
 */
export function AccentDot() {
  return <span style={{ color: 'var(--color-flame)' }}>.</span>;
}

/**
 * Registration CrossMark (Print Heritage Architectural Mark)
 */
export function CrossMark({
  filled = false,
  size = 14,
  className = '',
}: {
  filled?: boolean;
  size?: number;
  className?: string;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
      className={className}
      aria-hidden
    >
      <rect
        x="0.6"
        y="0.6"
        width="14.8"
        height="14.8"
        fill={filled ? 'var(--color-charcoal)' : 'none'}
        stroke="currentColor"
        strokeWidth="1.1"
      />
      <path
        d="M0.6 0.6 L15.4 15.4 M15.4 0.6 L0.6 15.4"
        stroke={filled ? 'var(--color-paper)' : 'currentColor'}
        strokeWidth="1.1"
      />
    </svg>
  );
}

/**
 * MarkStack: 3 Architectural registration marks in a vertical stack
 */
export function MarkStack({ count = 3 }: { count?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', color: 'var(--color-faint)' }} aria-hidden>
      {Array.from({ length: count }).map((_, i) => (
        <CrossMark key={i} filled={i === count - 1} size={12} />
      ))}
    </div>
  );
}

/**
 * Standard Section Heading Protocol
 */
export function SectionHead({ index, label }: { index: string; label: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid var(--color-line)',
        paddingBottom: '10px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <CrossMark size={12} />
        <span
          className="font-mono"
          style={{
            fontSize: '11px',
            fontWeight: 600,
            letterSpacing: '0.2em',
            textTransform: 'uppercase',
            color: 'var(--color-flame-ink)',
          }}
        >
          {label}
        </span>
      </div>
      <span
        className="font-mono"
        style={{
          fontSize: '12px',
          letterSpacing: '0.15em',
          color: 'var(--color-faint)',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {index}
      </span>
    </div>
  );
}

/**
 * 2px Vermilion Hairline Scroll Progress Bar
 */
export function ScrollProgress() {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const handleScroll = () => {
      const totalScroll = document.documentElement.scrollTop || document.body.scrollTop;
      const windowHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      if (windowHeight > 0) {
        setWidth((totalScroll / windowHeight) * 100);
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div
      className="scroll-progress-line"
      style={{ width: `${width}%`, transition: 'width 0.1s linear' }}
      aria-hidden
    />
  );
}

/**
 * 3D Spatial Tilt Card with Dynamic Specular Glare
 */
export function TiltCard({
  children,
  className = '',
  style = {},
  max = 6,
}: {
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
  max?: number;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const [rotX, setRotX] = useState(0);
  const [rotY, setRotY] = useState(0);
  const [glare, setGlare] = useState({ x: 50, y: 50, opacity: 0 });

  const handleMouseMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const px = (x / rect.width - 0.5) * 2;
    const py = (y / rect.height - 0.5) * 2;

    setRotY(px * max);
    setRotX(-py * max);
    setGlare({
      x: (x / rect.width) * 100,
      y: (y / rect.height) * 100,
      opacity: 0.15,
    });
  };

  const handleMouseLeave = () => {
    setRotX(0);
    setRotY(0);
    setGlare((prev) => ({ ...prev, opacity: 0 }));
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`hairline-card ${className}`}
      style={{
        transform: `perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg)`,
        transition: 'transform 0.15s ease-out, border-color 0.2s ease',
        position: 'relative',
        overflow: 'hidden',
        ...style,
      }}
    >
      {children}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: `radial-gradient(circle at ${glare.x}% ${glare.y}%, rgba(255,255,255,0.4) 0%, transparent 60%)`,
          opacity: glare.opacity,
          transition: 'opacity 0.2s ease',
        }}
        aria-hidden
      />
    </div>
  );
}

export function RegistrationMarks() {
  return (
    <div className="pointer-events-none fixed inset-0 z-40 select-none overflow-hidden" aria-hidden>
      <div className="absolute top-4 left-4 text-[#8b8472]/40 font-mono text-[10px]">+</div>
      <div className="absolute top-4 right-4 text-[#8b8472]/40 font-mono text-[10px]">+</div>
      <div className="absolute bottom-4 left-4 text-[#8b8472]/40 font-mono text-[10px]">+</div>
      <div className="absolute bottom-4 right-4 text-[#8b8472]/40 font-mono text-[10px]">+</div>
    </div>
  );
}

export function FolioNumber({ text }: { text: string }) {
  return (
    <div className="border-b border-[#e0d8c8] bg-[#faf4ec] py-1.5 px-6 font-mono text-[11px] tracking-widest text-[#8b8472] uppercase flex justify-between items-center">
      <span>{text}</span>
      <span className="text-[#e8501f] font-bold">● LIVE VERIFIED</span>
    </div>
  );
}

export function EditorialHeader({ 
  eyebrow, 
  title, 
  subtitle, 
  stampText 
}: { 
  eyebrow: string; 
  title: string; 
  subtitle: string; 
  stampText?: string; 
}) {
  return (
    <div className="relative border-b-2 border-[#141210] pb-8 pt-4">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="font-mono text-xs uppercase tracking-widest text-[#e8501f] font-bold mb-2">
            {eyebrow}
          </div>
          <h1 className="font-serif text-4xl md:text-5xl font-extrabold text-[#141210] tracking-tight">
            {title}
            <span className="text-[#e8501f]">.</span>
          </h1>
          <p className="mt-2 text-sm md:text-base text-[#514b3f] max-w-2xl leading-relaxed">
            {subtitle}
          </p>
        </div>
        {stampText && (
          <div className="font-mono text-xs px-3 py-1.5 border-2 border-[#141210] rounded uppercase tracking-wider font-bold bg-[#faf4ec] text-[#141210] shadow-sm whitespace-nowrap self-start md:self-auto">
            {stampText}
          </div>
        )}
      </div>
    </div>
  );
}

