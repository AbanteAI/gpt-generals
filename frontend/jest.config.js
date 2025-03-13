export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  testPathIgnorePatterns: ['/node_modules/', '/dist/'],
  testMatch: ['**/*.test.{ts,tsx}'],
  collectCoverage: true,
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/tests/**'],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  moduleNameMapper: {
    '\\.(css|less|sass|scss)$': '<rootDir>/src/tests/__mocks__/styleMock.js'
  },
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: 'tsconfig.json',
      useESM: true
    }],
  },
};
