// eslint.config.mjs
import globals from 'globals';
import pluginJs from '@eslint/js';
import tseslint from 'typescript-eslint';
import pluginReact from 'eslint-plugin-react';
import pluginReactHooks from 'eslint-plugin-react-hooks';
import pluginJsxA11y from 'eslint-plugin-jsx-a11y';
import pluginPrettier from 'eslint-plugin-prettier';
import configPrettier from 'eslint-config-prettier';
import importPlugin from 'eslint-plugin-import';

export default tseslint.config(
  // Global ignores - these apply to all configurations
  {
    ignores: [
      // Build outputs
      '.next/**',
      'dist/**',
      'out/**',
      'node_modules/**',
      // Config files that don't need linting
      '*.config.{js,mjs,ts,mts}',
      '.prettierrc.js', // Prettier config uses Node.js syntax
      'tailwind.config.ts',
      'vite.config.ts',
      'jest.config.js',
      'jest.setup.js',
      // Script files
      '*.script.js',
      'test-*.js',
      'fix-*.js',
      'remove-*.js',
      // Type declaration files
      '*.d.ts',
      'next-env.d.ts',
    ],
  },

  pluginJs.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{js,jsx,ts,tsx}'], // Only lint source files
    languageOptions: {
      parser: tseslint.parser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
        ecmaVersion: 'latest',
        sourceType: 'module',
        // Remove project option to avoid path issues
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      react: pluginReact,
      'react-hooks': pluginReactHooks,
      'jsx-a11y': pluginJsxA11y,
      prettier: pluginPrettier,
      import: importPlugin,

    },
    rules: {
      // Relaxed rules for migration
      'prettier/prettier': 'error',
      'react/react-in-jsx-scope': 'off',
      '@typescript-eslint/no-unused-vars': 'warn',
      '@typescript-eslint/no-explicit-any': 'warn', // Warning instead of error
      '@typescript-eslint/no-empty-object-type': 'warn',
      '@typescript-eslint/no-require-imports': 'warn',
      // Import order
      'import/order': [
        'error',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            'parent',
            'sibling',
            'index',
          ],
          'newlines-between': 'always',
          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },
        },
      ],
    },
  },
  configPrettier // Make sure this is last to override other configs
);
