/* eslint-env node */
module.exports = {
  'semi': true,
  'trailingComma': 'es5',
  'singleQuote': true,
  'printWidth': 80,
  'tabWidth': 2,
  'useTabs': false,
  'bracketSpacing': true,
  'bracketSameLine': false,
  'arrowParens': 'avoid',
  'endOfLine': 'lf',
  'plugins': [require.resolve('prettier-plugin-organize-imports')],
  'overrides':
    [
      { 'files': '*.json', 'options': { 'singleQuote': false } },
      {
        'files': '*.md',
        'options': { 'printWidth': 100, 'proseWrap': 'always' },
      },
    ],
}
