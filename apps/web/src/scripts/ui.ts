/**
 * Back-to-top button.
 *
 * Bundled rather than inlined so the CSP stays at `script-src 'self'`. The button
 * is a plain anchor to #top, so it still works with scripting disabled - this only
 * decides when it is worth showing.
 */

const button = document.querySelector<HTMLElement>('.totop');

if (button) {
  const SHOW_AFTER = 500;
  let ticking = false;

  const update = () => {
    button.classList.toggle('is-visible', window.scrollY > SHOW_AFTER);
    ticking = false;
  };

  window.addEventListener(
    'scroll',
    () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    },
    { passive: true },
  );

  update();
}
