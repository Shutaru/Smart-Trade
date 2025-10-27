export const formatCurrency = (value: number, currency = 'USD'): string =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 2,
  }).format(value);

export const formatPercent = (value: number, fractionDigits = 2): string =>
  `${value.toFixed(fractionDigits)}%`;
