import { useEffect, useRef, useState, useCallback } from 'react';
import { FiCpu, FiCalendar, FiMail, FiFolder } from 'react-icons/fi';
import { playHeavyClickSound } from '../utils/sound';
import './LoginPage.css';

function LoginPage() {
  const heroCanvasRef = useRef(null);
  const footerCanvasRef = useRef(null);
  const featuresCanvasRef = useRef(null);
  const footerRef = useRef(null);
  const featuresRef = useRef(null);

  const mousePosRef = useRef({ x: 0, y: 0 });
  const [footerVisible, setFooterVisible] = useState(false);
  const confettiRef = useRef([]); // Store confetti state

  // Handle mouse movement for spaceship tracking
  useEffect(() => {
    const handleMouseMove = (e) => {
      mousePosRef.current = { x: e.clientX, y: e.clientY };
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  // Set up Intersection Observers for animation triggers
  useEffect(() => {
    // 1. Feature Cards turning animation
    const featureObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const cards = entry.target.querySelectorAll('.feature-card-wrapper');
          cards.forEach((card, index) => {
            setTimeout(() => {
              card.classList.add('visible');
            }, index * 150); // Staggered delay
          });
          featureObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });

    if (featuresRef.current) {
      featureObserver.observe(featuresRef.current);
    }

    // 2. Footer Confetti trigger
    const footerObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !footerVisible) {
          setFooterVisible(true);
          // Delay confetti slightly so it fires ON fist impact!
          setTimeout(() => {
            initConfetti();
          }, 550);
        } else if (!entry.isIntersecting) {
          // Reset confetti if they scroll away and back
          setFooterVisible(false);
        }
      });
    }, { threshold: 0.5 });

    if (footerRef.current) {
      footerObserver.observe(footerRef.current);
    }

    return () => {
      featureObserver.disconnect();
      footerObserver.disconnect();
    };
  }, []);

  // Confetti setup
  const initConfetti = useCallback(() => {
    const colors = ['#8B5CF6', '#4DAB9A', '#FBBC05', '#EA4335', '#E4E4E7'];
    const newConfetti = [];
    for (let i = 0; i < 120; i++) {
      newConfetti.push({
        x: window.innerWidth / 2,
        y: window.innerHeight, // Start from bottom of screen
        vx: (Math.random() - 0.5) * 20, // Explosive X velocity
        vy: (Math.random() * -15) - 5,  // Explosive Y velocity upwards
        size: Math.floor(Math.random() * 5) + 2, // 2-7 pixels
        color: colors[Math.floor(Math.random() * colors.length)],
        life: 1.0,
        decay: Math.random() * 0.015 + 0.005,
        rotation: Math.random() * 360,
        rotSpeed: (Math.random() - 0.5) * 10
      });
    }
    confettiRef.current = newConfetti;
  }, []);

  // Reusable Canvas animation (Spaceship + Stars)
  const renderSpaceCanvas = useCallback((canvas, contextId) => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;
    const stars = [];

    function resize() {
      canvas.width = window.innerWidth;
      // For footer we might want to check its actual height, but window height serves as a good default for the starfield
      canvas.height = window.innerHeight;
    }
    resize();

    // Only attach global listener to the hero canvas so it doesn't duplicate overly
    if (contextId === 'hero') {
      window.addEventListener('resize', resize);
    }

    // Create stars
    for (let i = 0; i < 150; i++) {
      stars.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * window.innerHeight,
        size: Math.random() * 2,
        speed: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.5 + 0.2,
      });
    }

    // Spaceship state
    let shipX = window.innerWidth / 2;
    let shipY = window.innerHeight / 2;
    const shipSpeed = 0.08;

    function drawSpaceship(x, y, angle) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);

      // Draw pixelated spaceship
      ctx.fillStyle = '#E4E4E7';
      ctx.fillRect(-10, -10, 20, 20);
      ctx.fillStyle = '#6D28D9';
      ctx.fillRect(10, -5, 5, 10);
      ctx.fillStyle = '#4DAB9A';
      ctx.fillRect(-15, -15, 10, 10);
      ctx.fillRect(-15, 5, 10, 10);

      // Thruster
      if (Math.random() > 0.2) {
        ctx.fillStyle = '#FBBC05';
        ctx.fillRect(-20, -5, 8, 10);
        ctx.fillStyle = '#EA4335';
        ctx.fillRect(-25, -2, 5, 4);
      }

      ctx.restore();
    }



    function drawConfetti() {
      const confetti = confettiRef.current;
      if (!confetti || confetti.length === 0) return;

      for (let i = confetti.length - 1; i >= 0; i--) {
        const c = confetti[i];
        ctx.save();
        ctx.translate(c.x, c.y);
        ctx.rotate(c.rotation * Math.PI / 180);

        ctx.fillStyle = c.color;
        ctx.globalAlpha = c.life;
        ctx.fillRect(-c.size / 2, -c.size / 2, c.size, c.size);

        ctx.restore();

        // Physics
        c.x += c.vx;
        c.y += c.vy;
        c.vy += 0.3; // gravity
        c.rotation += c.rotSpeed;
        c.life -= c.decay;

        // Remove dead confetti
        if (c.life <= 0 || c.y > canvas.height) {
          confetti.splice(i, 1);
        }
      }
    }

    function draw() {
      // Create trailing effect
      ctx.fillStyle = 'rgba(5, 5, 8, 0.3)';
      const isLightMode = getComputedStyle(document.body).backgroundColor === 'rgb(255, 255, 255)';
      if (isLightMode) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      }
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw stars 
      stars.forEach(s => {
        ctx.fillStyle = `rgba(${isLightMode ? '100,100,100' : '200,200,250'}, ${s.opacity})`;
        ctx.fillRect(Math.floor(s.x), Math.floor(s.y), Math.ceil(s.size), Math.ceil(s.size));
        s.x -= s.speed;
        if (s.x < 0) {
          s.x = canvas.width;
          s.y = Math.random() * canvas.height;
        }
      });

      // Update spaceship position (easing towards mouse inside the specific canvas)
      // We adjust mouse Y for footer if needed, but since it's position:fixed/sticky or absolute usually
      let targetY = mousePosRef.current.y || canvas.height / 2;

      // If we are drawing the footer canvas, we need to map mouse Y to the local canvas coords
      if (contextId === 'footer') {
        const rect = canvas.getBoundingClientRect();
        targetY = mousePosRef.current.y - rect.top;
      }

      const targetX = mousePosRef.current.x || canvas.width / 2;
      const dx = targetX - shipX;
      const dy = targetY - shipY;

      shipX += dx * shipSpeed;
      shipY += dy * shipSpeed;
      const angle = Math.atan2(dy, dx);

      drawSpaceship(shipX, shipY, angle);

      // Draw Confetti independently (only over the footer canvas)
      if (contextId === 'footer' && footerVisible) {
        drawConfetti();
      }

      animId = requestAnimationFrame(draw);
    }

    setTimeout(() => { draw(); }, 100);

    return () => {
      cancelAnimationFrame(animId);
      if (contextId === 'hero') {
        window.removeEventListener('resize', resize);
      }
    };
  }, [footerVisible]);

  // Mount canvases
  useEffect(() => {
    let cleanupHero = renderSpaceCanvas(heroCanvasRef.current, 'hero');
    let cleanupFooter = renderSpaceCanvas(footerCanvasRef.current, 'footer');

    return () => {
      if (cleanupHero) cleanupHero();
      if (cleanupFooter) cleanupFooter();
    }
  }, [renderSpaceCanvas]);

  // Pacman Canvas effect
  useEffect(() => {
    const canvas = featuresCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    // State
    let pacX = window.innerWidth / 2;
    let pacY = 100;
    let mouthOpen = 0;
    let mouthDir = 1;

    // Dots State
    const dots = [];
    for (let i = 0; i < 40; i++) {
      dots.push({
        x: Math.random() * window.innerWidth,
        y: Math.random() * (canvas.height || 1000),
        eaten: false
      });
    }

    function resize() {
      const parent = canvas.parentElement;
      canvas.width = window.innerWidth;
      canvas.height = parent.clientHeight;
      dots.forEach(d => {
        if (!d.eaten) d.y = Math.random() * canvas.height;
      });
    }
    resize();
    window.addEventListener('resize', resize);

    const resizeObserver = new ResizeObserver(() => resize());
    if (canvas.parentElement) resizeObserver.observe(canvas.parentElement);

    function drawPacman() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.fillStyle = '#FBBC05';
      dots.forEach(d => {
        if (!d.eaten) {
          ctx.beginPath();
          ctx.arc(d.x, d.y, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      const rect = canvas.getBoundingClientRect();
      const targetX = mousePosRef.current.x || canvas.width / 2;
      const targetY = mousePosRef.current.y - rect.top;

      const dx = targetX - pacX;
      const dy = targetY - pacY;

      pacX += dx * 0.04;
      pacY += dy * 0.04;

      const angle = Math.atan2(dy, dx);

      mouthOpen += 0.05 * mouthDir;
      if (mouthOpen >= 0.4 || mouthOpen <= 0) mouthDir *= -1;

      dots.forEach(d => {
        if (!d.eaten) {
          const dist = Math.hypot(pacX - d.x, pacY - d.y);
          if (dist < 30) d.eaten = true;
        }
      });

      ctx.save();
      ctx.translate(pacX, pacY);
      ctx.rotate(angle);

      ctx.beginPath();
      ctx.arc(0, 0, 30, mouthOpen * Math.PI, (2 - mouthOpen) * Math.PI);
      ctx.lineTo(0, 0);
      ctx.fillStyle = '#FBBC05';
      ctx.fill();

      ctx.beginPath();
      ctx.arc(0, -15, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#050508';
      ctx.fill();
      ctx.restore();

      animId = requestAnimationFrame(drawPacman);
    }

    setTimeout(() => { drawPacman(); }, 100);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
      resizeObserver.disconnect();
    };
  }, []);

  return (
    <div className="login-wrapper">
      <div className="login-hero">
        <canvas ref={heroCanvasRef} className="login-canvas" />
        <div className="login-card glass-card glow-border">
          <div className="login-logo" style={{ color: '#8B5CF6' }}>◈</div>
          <h1 className="pixel-text login-title" style={{ color: '#8B5CF6', textShadow: '0 0 10px rgba(139, 92, 246, 0.4)' }}>CALEMINDER</h1>
          <p className="login-subtitle">Your AI-powered scheduling command center</p>
          <a href="/api/auth/google" className="login-btn" onClick={() => playHeavyClickSound()}>
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
            </svg>
            <span className="pixel-text">► START GAME</span>
          </a>
          <p className="login-footer">Sign in with Google to begin</p>
        </div>

        <div className="scroll-indicator pixel-text">
          SCROLL DOWN
          <div className="scroll-arrow">▼</div>
        </div>
      </div>

      <div className="features-section" ref={featuresRef} style={{ position: 'relative' }}>
        <canvas ref={featuresCanvasRef} className="pacman-canvas" />
        <h2 className="pixel-text features-header">WHAT THE HECK CAN I DO?</h2>
        <div className="features-list">

          <div className="feature-card-wrapper hidden-card align-left">
            <div className="feature-card">
              <div className="feature-card-front glass-card">
                <div className="feature-icon"><FiCpu /></div>
                <h3 className="pixel-text feature-title">LITERAL BRAINPOWER</h3>
              </div>
              <div className="feature-card-back glass-card">
                <p className="feature-desc">The AI power you desire !. Basically, I remember stuff, figure things out, and search the web so you don't have to use your own squishy human brain.</p>
              </div>
            </div>
          </div>

          <div className="feature-card-wrapper hidden-card align-right">
            <div className="feature-card">
              <div className="feature-card-front glass-card">
                <div className="feature-icon"><FiCalendar /></div>
                <h3 className="pixel-text feature-title">SCHEDULE DOMINATION</h3>
              </div>
              <div className="feature-card-back glass-card">
                <p className="feature-desc">Throw a messy PDF timetable at me or literally just rant about your day. I'll silently organize it into perfect Google Calendar events while you watch.</p>
              </div>
            </div>
          </div>

          <div className="feature-card-wrapper hidden-card align-left">
            <div className="feature-card">
              <div className="feature-card-front glass-card">
                <div className="feature-icon"><FiMail /></div>
                <h3 className="pixel-text feature-title">AGGRESSIVE OUTREACH</h3>
              </div>
              <div className="feature-card-back glass-card">
                <p className="feature-desc">Need to yell at someone? Or just politely ask for an extension? I rummage through your Google Contacts and draft the exact Gmail you're too anxious to write.</p>
              </div>
            </div>
          </div>

          <div className="feature-card-wrapper hidden-card align-right">
            <div className="feature-card">
              <div className="feature-card-front glass-card">
                <div className="feature-icon"><FiFolder /></div>
                <h3 className="pixel-text feature-title">DRIVE JANITOR</h3>
              </div>
              <div className="feature-card-back glass-card">
                <p className="feature-desc">Your Google Drive is a mess and we both know it. Hand me a folder and I'll create directories and forcefully shove your scattered files exactly where they belong.</p>
              </div>
            </div>
          </div>

        </div>
      </div>

      <div className="login-footer-section" ref={footerRef}>
        <canvas ref={footerCanvasRef} className="login-canvas" />
        <div className="footer-content">
          <div className={`fist-bump-container ${footerVisible ? 'animate-bump' : ''}`}>
            <img src="/hussain.png" alt="Hussain" className="fist-bump-avatar hussain-avatar" />
            <div className="fist-bump-impact"></div>
            <img src="/robot.png" alt="AI" className="fist-bump-avatar robot-avatar" />
          </div>
          <h2 className="pixel-text" style={{ fontSize: '1.2rem', margin: 0 }}>
            Made by <span style={{ color: '#8B5CF6' }}>Hussain</span> and <span style={{ color: '#8B5CF6' }}>AI</span>
          </h2>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
