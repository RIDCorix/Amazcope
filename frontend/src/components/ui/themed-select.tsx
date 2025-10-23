import ReactSelect, {
  Props as ReactSelectProps,
  StylesConfig,
} from 'react-select';

// Custom styles that match shadcn UI theme
const customStyles: StylesConfig = {
  control: (base, state) => ({
    ...base,
    minHeight: '40px',
    borderColor: state.isFocused ? 'hsl(var(--ring))' : 'hsl(var(--input))',
    backgroundColor: 'hsl(var(--background))',
    borderRadius: '0.375rem',
    boxShadow: state.isFocused ? '0 0 0 2px hsl(var(--ring))' : 'none',
    '&:hover': {
      borderColor: 'hsl(var(--ring))',
    },
  }),
  menu: base => ({
    ...base,
    backgroundColor: 'hsl(var(--popover))',
    border: '1px solid hsl(var(--border))',
    borderRadius: '0.375rem',
    boxShadow:
      '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    zIndex: 50,
  }),
  menuList: base => ({
    ...base,
    padding: '4px',
  }),
  option: (base, state) => ({
    ...base,
    backgroundColor: state.isFocused
      ? 'hsl(var(--accent))'
      : state.isSelected
        ? 'hsl(var(--primary))'
        : 'transparent',
    color: state.isFocused
      ? 'hsl(var(--accent-foreground))'
      : state.isSelected
        ? 'hsl(var(--primary-foreground))'
        : 'hsl(var(--foreground))',
    cursor: state.isDisabled ? 'not-allowed' : 'pointer',
    padding: '8px 12px',
    borderRadius: '0.25rem',
    '&:active': {
      backgroundColor: 'hsl(var(--accent))',
    },
  }),
  multiValue: base => ({
    ...base,
    backgroundColor: 'hsl(var(--secondary))',
    borderRadius: '0.25rem',
  }),
  multiValueLabel: base => ({
    ...base,
    color: 'hsl(var(--secondary-foreground))',
    padding: '2px 6px',
  }),
  multiValueRemove: base => ({
    ...base,
    color: 'hsl(var(--secondary-foreground))',
    borderRadius: '0 0.25rem 0.25rem 0',
    '&:hover': {
      backgroundColor: 'hsl(var(--destructive))',
      color: 'hsl(var(--destructive-foreground))',
    },
  }),
  input: base => ({
    ...base,
    color: 'hsl(var(--foreground))',
  }),
  placeholder: base => ({
    ...base,
    color: 'hsl(var(--muted-foreground))',
  }),
  singleValue: base => ({
    ...base,
    color: 'hsl(var(--foreground))',
  }),
  dropdownIndicator: base => ({
    ...base,
    color: 'hsl(var(--muted-foreground))',
    '&:hover': {
      color: 'hsl(var(--foreground))',
    },
  }),
  clearIndicator: base => ({
    ...base,
    color: 'hsl(var(--muted-foreground))',
    '&:hover': {
      color: 'hsl(var(--foreground))',
    },
  }),
  indicatorSeparator: base => ({
    ...base,
    backgroundColor: 'hsl(var(--border))',
  }),
  loadingIndicator: base => ({
    ...base,
    color: 'hsl(var(--muted-foreground))',
  }),
  noOptionsMessage: base => ({
    ...base,
    color: 'hsl(var(--muted-foreground))',
  }),
};

interface ThemedSelectProps extends ReactSelectProps {
  className?: string;
}

export function ThemedSelect(props: ThemedSelectProps) {
  return (
    <ReactSelect
      {...props}
      styles={{
        ...customStyles,
        ...props.styles,
      }}
      className={`react-select-container ${props.className || ''}`}
      classNamePrefix="react-select"
      theme={theme => ({
        ...theme,
        borderRadius: 6,
        colors: {
          ...theme.colors,
          primary: 'hsl(var(--primary))',
          primary75: 'hsl(var(--primary) / 0.75)',
          primary50: 'hsl(var(--primary) / 0.5)',
          primary25: 'hsl(var(--primary) / 0.25)',
          danger: 'hsl(var(--destructive))',
          dangerLight: 'hsl(var(--destructive) / 0.25)',
          neutral0: 'hsl(var(--background))',
          neutral5: 'hsl(var(--accent))',
          neutral10: 'hsl(var(--accent))',
          neutral20: 'hsl(var(--border))',
          neutral30: 'hsl(var(--border))',
          neutral40: 'hsl(var(--muted-foreground))',
          neutral50: 'hsl(var(--muted-foreground))',
          neutral60: 'hsl(var(--foreground))',
          neutral70: 'hsl(var(--foreground))',
          neutral80: 'hsl(var(--foreground))',
          neutral90: 'hsl(var(--foreground))',
        },
      })}
    />
  );
}
