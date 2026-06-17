if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('./sw.js')
      .then((reg) => console.log('Service Worker zarejestrowany pomyślnie.', reg))
      .catch((err) => console.log('Błąd rejestracji Service Workera:', err));
  });
}
