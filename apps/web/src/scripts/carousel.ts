/**
 * Pricing carousel behaviour, mobile only.
 *
 * The layout is pure CSS scroll-snap - this only does the two things CSS cannot:
 * start the carousel centred on the featured plan rather than on the first one,
 * and keep the dots in step with the swipe. On desktop the same markup is a grid
 * and this stays out of the way.
 *
 * Bundled, so `script-src 'self'` is untouched.
 */

const MOBILE = '(max-width: 760px)';

function setup(carousel: HTMLElement): void {
  const cards = Array.from(carousel.querySelectorAll<HTMLElement>('.plan'));
  const dots = carousel.parentElement?.querySelectorAll<HTMLElement>('.carousel-dots span');
  if (!cards.length) return;

  const featured = cards.findIndex((c) => c.classList.contains('plan--featured'));
  const active = featured >= 0 ? featured : 0;

  const centre = (index: number, smooth = false) => {
    const card = cards[index];
    if (!card) return;
    const left = card.offsetLeft - (carousel.clientWidth - card.offsetWidth) / 2;
    carousel.scrollTo({ left, behavior: smooth ? 'smooth' : 'auto' });
  };

  const markActive = (index: number) => {
    dots?.forEach((dot, i) => dot.classList.toggle('is-active', i === index));
  };

  // Which card is nearest the centre of the viewport right now.
  const nearest = () => {
    const mid = carousel.scrollLeft + carousel.clientWidth / 2;
    let best = 0;
    let bestGap = Infinity;
    cards.forEach((card, i) => {
      const cardMid = card.offsetLeft + card.offsetWidth / 2;
      const gap = Math.abs(cardMid - mid);
      if (gap < bestGap) {
        bestGap = gap;
        best = i;
      }
    });
    return best;
  };

  let ticking = false;
  carousel.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        markActive(nearest());
        ticking = false;
      });
    },
    { passive: true },
  );

  dots?.forEach((dot, i) => {
    dot.addEventListener('click', () => centre(i, true));
  });

  // Centre on the featured plan whenever the carousel layout is (re)activated.
  const query = window.matchMedia(MOBILE);
  const apply = () => {
    if (query.matches) {
      centre(active);
      markActive(active);
    } else {
      carousel.scrollLeft = 0;
    }
  };
  query.addEventListener('change', apply);
  apply();
}

document.querySelectorAll<HTMLElement>('.plans[data-carousel]').forEach(setup);
