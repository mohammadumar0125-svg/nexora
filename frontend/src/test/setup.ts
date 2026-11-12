import '@testing-library/jest-dom';

if (!window.matchMedia) {
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

if (typeof IntersectionObserver === 'undefined') {
  class MockIntersectionObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (window as any).IntersectionObserver = MockIntersectionObserver;
  (globalThis as any).IntersectionObserver = MockIntersectionObserver;
}

if (typeof ResizeObserver === 'undefined') {
  class MockResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  (window as any).ResizeObserver = MockResizeObserver;
  (globalThis as any).ResizeObserver = MockResizeObserver;
}

window.scrollTo = () => {};
globalThis.fetch = (async () => ({
  ok: true,
  json: async () => ([]),
})) as any;
