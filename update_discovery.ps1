# Discovery Engine - Configuration Update Script
# Adds symbol, exchange, and timeframe parameters

$file = "backend/agents/discovery/discovery_engine.py"
$content = Get-Content $file -Raw

# Find the __init__ method and replace it
$oldInit = @'
    def __init__(self, config_path: str = "config.yaml", max_parallel: int = 5, timeframe: str = None):
        self.config_path = config_path
  self.max_parallel = max_parallel
     self.timeframe = timeframe  # Override timeframe if provided
        self.catalog = StrategyCatalog()
self.ranker = StrategyRanker()

        # Load base config
        with open(config_path, "r", encoding="utf-8") as f:
         self.base_config = yaml.safe_load(f) or {}
        
        # Override timeframe if specified
        if self.timeframe:
       self.base_config['timeframe'] = self.timeframe

  print(f"[StrategyDiscovery] Initialized with {len(self.catalog.INDICATORS)} indicators")
        if self.timeframe:
  print(f"[StrategyDiscovery] Using timeframe override: {self.timeframe}")
'@

$newInit = @'
    def __init__(
        self, 
 config_path: str = "config.yaml",
symbol: str = None,
        exchange: str = None,
 timeframe: str = None,
        max_parallel: int = 5
):
self.config_path = config_path
        self.max_parallel = max_parallel
        self.catalog = StrategyCatalog()
       self.ranker = StrategyRanker()

      # Load base config
        with open(config_path, "r", encoding="utf-8") as f:
         self.base_config = yaml.safe_load(f) or {}
        
        # Override with provided parameters
    if symbol:
self.base_config['symbol'] = symbol
  if exchange:
       self.base_config['exchange'] = exchange
        if timeframe:
            self.base_config['timeframe'] = timeframe
        
        # Store current configuration
  self.symbol = self.base_config.get('symbol', 'BTC/USDT:USDT')
        self.exchange = self.base_config.get('exchange', 'binance')
        self.timeframe = self.base_config.get('timeframe', '5m')

        print(f"[StrategyDiscovery] Initialized:")
        print(f"  Symbol: {self.symbol}")
print(f"  Exchange: {self.exchange}")
        print(f"  Timeframe: {self.timeframe}")
print(f"  Indicators: {len(self.catalog.INDICATORS)}")
'@

$content = $content -replace [regex]::Escape($oldInit), $newInit

Set-Content -Path $file -Value $content -NoNewline
Write-Host "Updated discovery_engine.py" -ForegroundColor Green
