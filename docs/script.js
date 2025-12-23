/* ============================================
   EideticRAG Landing Page - JavaScript
   Scroll Animations, Interactions, Particles
   ============================================ */

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initScrollAnimations();
    initNavbarScroll();
    initMobileMenu();
    initSmoothScroll();
});

/* ============================================
   Particle Animation for Hero
   ============================================ */
function initParticles() {
    const container = document.getElementById('particles');
    if (!container) return;
    
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        createParticle(container);
    }
}

function createParticle(container) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    
    // Random styling
    const size = Math.random() * 4 + 1;
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const duration = Math.random() * 20 + 10;
    const delay = Math.random() * 5;
    const opacity = Math.random() * 0.5 + 0.1;
    
    particle.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        background: linear-gradient(135deg, #8b5cf6, #06b6d4);
        border-radius: 50%;
        left: ${x}%;
        top: ${y}%;
        opacity: ${opacity};
        animation: float ${duration}s ease-in-out ${delay}s infinite;
        pointer-events: none;
    `;
    
    container.appendChild(particle);
}

// Add float animation to stylesheet
const style = document.createElement('style');
style.textContent = `
    @keyframes float {
        0%, 100% { 
            transform: translate(0, 0) scale(1);
            opacity: 0.2;
        }
        25% { 
            transform: translate(20px, -30px) scale(1.1);
            opacity: 0.5;
        }
        50% { 
            transform: translate(-10px, -60px) scale(1);
            opacity: 0.3;
        }
        75% { 
            transform: translate(30px, -30px) scale(0.9);
            opacity: 0.4;
        }
    }
`;
document.head.appendChild(style);

/* ============================================
   Scroll Animations (Intersection Observer)
   ============================================ */
function initScrollAnimations() {
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                
                // Add staggered animation for children if needed
                const children = entry.target.querySelectorAll('[data-aos-delay]');
                children.forEach((child, index) => {
                    setTimeout(() => {
                        child.classList.add('visible');
                    }, index * 100);
                });
            }
        });
    }, observerOptions);
    
    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach((card, index) => {
        card.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(card);
    });
    
    // Observe install steps
    document.querySelectorAll('.install-step').forEach((step, index) => {
        step.style.transitionDelay = `${index * 0.15}s`;
        observer.observe(step);
    });
    
    // Observe other animatable elements
    document.querySelectorAll('.arch-layer, .skill-category, .comparison-card').forEach((el, index) => {
        el.style.transitionDelay = `${index * 0.1}s`;
        observer.observe(el);
    });
}

/* ============================================
   Navbar Scroll Effect
   ============================================ */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        // Add/remove background on scroll
        if (currentScroll > 50) {
            navbar.style.background = 'rgba(10, 10, 15, 0.95)';
            navbar.style.borderBottomColor = 'rgba(255, 255, 255, 0.1)';
        } else {
            navbar.style.background = 'rgba(10, 10, 15, 0.8)';
        }
        
        // Hide/show on scroll direction
        if (currentScroll > lastScroll && currentScroll > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
}

/* ============================================
   Mobile Menu Toggle
   ============================================ */
function initMobileMenu() {
    const menuBtn = document.querySelector('.mobile-menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (!menuBtn || !navLinks) return;
    
    menuBtn.addEventListener('click', () => {
        navLinks.classList.toggle('mobile-open');
        menuBtn.textContent = navLinks.classList.contains('mobile-open') ? '✕' : '☰';
    });
    
    // Add mobile menu styles
    const mobileStyle = document.createElement('style');
    mobileStyle.textContent = `
        @media (max-width: 768px) {
            .nav-links.mobile-open {
                display: flex !important;
                flex-direction: column;
                position: absolute;
                top: 100%;
                left: 0;
                right: 0;
                background: rgba(10, 10, 15, 0.98);
                padding: 24px;
                gap: 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }
        }
    `;
    document.head.appendChild(mobileStyle);
}

/* ============================================
   Smooth Scrolling for Anchor Links
   ============================================ */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const target = document.querySelector(targetId);
            
            if (target) {
                const navHeight = document.querySelector('.navbar').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                const navLinks = document.querySelector('.nav-links');
                if (navLinks.classList.contains('mobile-open')) {
                    navLinks.classList.remove('mobile-open');
                    document.querySelector('.mobile-menu-btn').textContent = '☰';
                }
            }
        });
    });
}

/* ============================================
   Copy Code Functionality
   ============================================ */
function copyCode(button) {
    const codeBlock = button.parentElement;
    const code = codeBlock.querySelector('code').textContent;
    
    navigator.clipboard.writeText(code).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.style.background = '#10b981';
        button.style.borderColor = '#10b981';
        
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '';
            button.style.borderColor = '';
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        button.textContent = 'Failed';
        
        setTimeout(() => {
            button.textContent = 'Copy';
        }, 2000);
    });
}

/* ============================================
   Typing Animation for Hero (Optional)
   ============================================ */
function initTypingAnimation() {
    const gradientText = document.querySelector('.hero-title .gradient-text');
    if (!gradientText) return;
    
    const text = gradientText.textContent;
    gradientText.textContent = '';
    gradientText.style.borderRight = '2px solid #8b5cf6';
    
    let i = 0;
    const typeInterval = setInterval(() => {
        if (i < text.length) {
            gradientText.textContent += text.charAt(i);
            i++;
        } else {
            clearInterval(typeInterval);
            gradientText.style.borderRight = 'none';
        }
    }, 100);
}

/* ============================================
   Counter Animation for Stats
   ============================================ */
function animateCounters() {
    const stats = document.querySelectorAll('.stat-value');
    
    stats.forEach(stat => {
        const target = stat.textContent;
        const hasNumber = /\d/.test(target);
        
        if (hasNumber && !target.includes('GB') && !target.includes('ms')) {
            // Simple percentage counter
            const numMatch = target.match(/\d+/);
            if (numMatch) {
                const targetNum = parseInt(numMatch[0]);
                let current = 0;
                const increment = targetNum / 50;
                
                const counter = setInterval(() => {
                    current += increment;
                    if (current >= targetNum) {
                        stat.textContent = target;
                        clearInterval(counter);
                    } else {
                        stat.textContent = target.replace(/\d+/, Math.floor(current).toString());
                    }
                }, 30);
            }
        }
    });
}

// Trigger counter animation when stats are visible
const statsObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            animateCounters();
            statsObserver.disconnect();
        }
    });
}, { threshold: 0.5 });

const statsSection = document.querySelector('.hero-stats');
if (statsSection) {
    statsObserver.observe(statsSection);
}

/* ============================================
   Parallax Effect for Hero Background
   ============================================ */
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const heroBg = document.querySelector('.hero-bg');
    
    if (heroBg && scrolled < window.innerHeight) {
        heroBg.style.transform = `translateY(${scrolled * 0.3}px)`;
    }
});

/* ============================================
   Hover Tilt Effect for Cards
   ============================================ */
document.querySelectorAll('.feature-card, .comparison-card').forEach(card => {
    card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        
        const rotateX = (y - centerY) / 20;
        const rotateY = (centerX - x) / 20;
        
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
    });
    
    card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
    });
});

console.log('🧠 EideticRAG Landing Page Loaded Successfully!');
