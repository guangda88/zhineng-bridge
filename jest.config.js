module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom', // Required for testing browser APIs like IndexedDB and Web Crypto
  roots: ['<rootDir>/tests/frontend', '<rootDir>/tests/unit'],
  testMatch: [
    '**/tests/**/*.test.{js,jsx,ts,tsx}',
    '**/__tests__/**/*.{js,jsx,ts,tsx}'
  ],
  collectCoverageFrom: [
    'web/ui/js/**/*.{js,ts}',
    'phase3/encryption/**/*.js',
    'phase3/storage/**/*.js',
    'phase4/**/*.js',
    '!**/*.test.{js,ts}',
    '!**/node_modules/**',
    '!**/dist/**'
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1'
  },
  setupFilesAfterEnv: ['<rootDir>/tests/frontend/setup.js'],
  testTimeout: 10000,
  verbose: true
};
