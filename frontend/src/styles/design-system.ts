/**
 * FieldMind Design System - Succulents Color Palette
 * Tailwind CSS Configuration
 */

export const colors = {
  // Primary - Deep Teal
  primary: {
    DEFAULT: '#27768A',
    50: '#E8F4F7',
    100: '#D1E9EF',
    200: '#A8CCD3',
    300: '#7FB0B7',
    400: '#53939F',
    500: '#27768A',
    600: '#1F5E6E',
    700: '#174653',
    800: '#0F2E37',
    900: '#07171C',
  },
  // Primary Light - Mid Teal
  primaryLight: {
    DEFAULT: '#589DA4',
    50: '#EBF6F7',
    100: '#D7EDEF',
    200: '#AFDADF',
    300: '#87C8CF',
    400: '#6FB5BE',
    500: '#589DA4',
    600: '#467E83',
    700: '#345E62',
    800: '#223F42',
    900: '#111F21',
  },
  // Secondary - Olive Green
  secondary: {
    DEFAULT: '#748D44',
    50: '#F2F5EB',
    100: '#E5EBD7',
    200: '#CBD7AF',
    300: '#B1C387',
    400: '#92AB65',
    500: '#748D44',
    600: '#5C7136',
    700: '#455529',
    800: '#2E381B',
    900: '#171C0E',
  },
  // Secondary Light - Light Olive
  secondaryLight: {
    DEFAULT: '#85A156',
    50: '#F3F7EC',
    100: '#E7EFD9',
    200: '#CFDFB3',
    300: '#B7CF8D',
    400: '#9EBF67',
    500: '#85A156',
    600: '#6A8145',
    700: '#506134',
    800: '#354022',
    900: '#1B2011',
  },
  // Accent - Cream
  accent: {
    DEFAULT: '#F0F5E2',
    50: '#FCFDFB',
    100: '#F9FBF6',
    200: '#F5F8ED',
    300: '#F0F5E2',
    400: '#E6EFD0',
    500: '#DCEABD',
    600: '#C9DD96',
    700: '#B5D06F',
    800: '#A2C448',
    900: '#8EB721',
  },
  // Semantic Colors
  success: '#85A156',
  warning: '#F8B042',
  error: '#EC6A52',
  info: '#589DA4',
}

export const designTokens = {
  // Spacing
  spacing: {
    xs: '0.25rem',    // 4px
    sm: '0.5rem',     // 8px
    md: '1rem',       // 16px
    lg: '1.5rem',     // 24px
    xl: '2rem',       // 32px
    '2xl': '3rem',    // 48px
    '3xl': '4rem',    // 64px
  },
  // Border Radius
  radius: {
    sm: '0.25rem',    // 4px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    full: '9999px',
  },
  // Shadows
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  },
  // Typography
  fontSize: {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
  },
  fontWeight: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
  },
  // Transitions
  transition: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: '250ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '350ms cubic-bezier(0.4, 0, 0.2, 1)',
  },
}

export default {
  colors,
  designTokens,
}
