// theme/static/src/tailwind.config.js

/** @type {import('tailwindcss').Config} */

module.exports = {
  plugins: {
    "@tailwindcss/postcss": {},
    "postcss-simple-vars": {},
    "postcss-nested": {}
  },
  content: [
    // Ścieżki do Twoich szablonów HTML
    '../../templates/**/*.html', // Wyszukuje w główym folderze templates
    '../../../templates/**/*.html', // Wyszukuje w folderze templates na poziomie projektu
    '../../../**/templates/**/*.html', // Wyszukuje we wszystkich aplikacjach
],
theme: {
  extend: {},
},
}
