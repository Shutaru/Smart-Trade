# ? Strategy Lab - FAQ & Troubleshooting

## ?? ERROS COMUNS

### **Erro 1: "No symbols specified in config"**

**Mensagem completa:**
```
ValueError: No symbols specified in strategy configuration.
Please add at least one symbol in the Data tab
```

**Causa:** O campo `symbols` está vazio no JSON enviado ao backend.

**Solução:**
1. Ir ao **separador "Data"**
2. Clicar no botão **"Select symbols..."**
3. ?? Procurar pelo símbolo (ex: `BTC/USDT`)
4. ? Clicar no símbolo para selecionar (aparece ?)
5. Clicar fora para fechar o popup
6. Verificar que aparece um **badge azul** com o símbolo
7. Agora podes fazer **"Validate"** e **"Run"**

**Screenshot da seleção:**
```
???????????????????????????????????
? Symbols (1 selected)      ?
???????????????????????????????????
? [Select symbols... ?]           ?
?   ?
? ?????????????????????????????  ?
? ? BTC/USDT:USDT             ?  ?  ? Badge azul confirma seleção
? ?????????????????????????????  ?
???????????????????????????????????
```

---

### **Erro 2: "Database not found"**

**Mensagem completa:**
```
FileNotFoundError: Database not found: data/lab/bitget/BTC_USDT_USDT_5m.db
Please backfill data first
```

**Causa:** Ainda não fizeste download dos dados históricos.

**Solução:**
1. Selecionar símbolo (ver Erro 1)
2. Clicar no botão **"Backfill Data"**
3. Aguardar 10-30 segundos
4. Deve aparecer: **"Backfill Complete - Downloaded X candles"**
5. Agora podes rodar o backtest

**O que faz o Backfill:**
- Baixa dados OHLCV do exchange via CCXT
- Calcula indicadores (RSI, EMA, SMA, ATR, etc)
- Guarda em SQLite (`data/lab/{exchange}/{symbol}_{timeframe}.db`)
- Só precisa fazer uma vez por símbolo/timeframe

---

### **Erro 3: "No data found for {symbol} in specified date range"**

**Mensagem completa:**
```
ValueError: No data found for BTC/USDT:USDT in the specified date range.
Period: 2024-01-01 to 2024-10-28
Try backfilling data or adjusting the date range.
```

**Causa:** O período selecionado não tem dados no DB.

**Solução:**
1. Verificar **Start Date** e **End Date** no separador Data
2. Fazer backfill novamente para o período desejado
3. Ou ajustar datas para um período mais recente

**Nota:** CCXT pode ter limites de quanto dados consegue baixar de uma vez.

---

### **Erro 4: "Insufficient data: got 50 bars, need at least 300"**

**Mensagem completa:**
```
ValueError: Insufficient data: got 50 bars, need at least 300
```

**Causa:** `warmup_bars: 300` (default) precisa de pelo menos 300 candles para calcular indicadores.

**Solução:**
1. Aumentar período de tempo (Start Date mais atrás)
2. Ou diminuir `warmup_bars` no JSON (separador "Preview")
3. Fazer backfill com período maior

---

### **Erro 5: Charts não aparecem**

**Sintomas:**
- Backtest completa com sucesso
- Tab "Metrics" mostra métricas
- Mas charts estão vazios/brancos

**Causa:** Problema de rendering do Lightweight Charts.

**Solução:**
1. Abrir DevTools (F12)
2. Ir ao **Console**
3. Copiar erros JavaScript
4. Partilhar com desenvolvedor

**Causas comuns:**
- Dados com timestamps inválidos
- NaN values nos dados
- Biblioteca não carregou

---

### **Erro 6: "Failed to fetch trades"**

**Sintomas:**
- Tab "Trades" mostra erro vermelho
- "Failed to load trades"

**Causa:** Backend crashou ou `trades.csv` não foi gerado.

**Solução:**
1. Verificar logs do backend (janela PowerShell)
2. Procurar por tracebacks Python
3. Reiniciar backend se necessário:
```sh
Ctrl+C (para parar)
python -m uvicorn gui_server:app --host 127.0.0.1 --port 8000 --reload
```

---

### **Erro 7: "Validation Errors"**

**Sintomas:**
- Botão "Validate" mostra ?
- Lista de erros aparece

**Causas comuns:**
- **No long or short conditions:** Precisa definir pelo menos 1 condição
- **Invalid indicator:** Nome de indicador inválido
- **Invalid operator:** Operador não suportado

**Solução:**
1. Ir ao separador **"Strategy"**
2. Adicionar pelo menos 1 condição Long OU Short
3. Verificar que indicadores são válidos (RSI, EMA, SMA, etc)
4. Re-validar

---

## ? CHECKLIST ANTES DE RODAR BACKTEST

- [ ] **Símbolo selecionado** (badge azul visível)
- [ ] **Data backfilled** (botão "Backfill Data" clicado com sucesso)
- [ ] **Condições definidas** (pelo menos 1 Long OU Short)
- [ ] **Objective configurado** (ex: `sharpe`)
- [ ] **Validação OK** (botão "Validate" mostra ?)
- [ ] **Backend a correr** (http://127.0.0.1:8000)

---

## ?? COMO DEBUGGAR

### **Ver payload JSON enviado:**
1. Abrir DevTools (F12)
2. Ir ao separador **"Network"**
3. Filtrar por `backtest`
4. Clicar no request `POST /api/lab/run/backtest`
5. Ver **"Payload"** ou **"Request Body"**
6. Verificar que `symbols: ["BTC/USDT:USDT"]` (não vazio!)

### **Ver logs do backend:**
- Janela PowerShell onde iniciaste o uvicorn
- Procurar por `[run_id] ERROR:` linhas
- Copiar traceback completo

### **Ver state do frontend:**
Adicionar no console DevTools:
```javascript
// Ver estratégia atual
console.log(JSON.stringify(strategy, null, 2));

// Ver se symbols está populated
console.log("Symbols:", strategy.data.symbols);
```

---

## ?? SUPORTE

**Erro não listado aqui?**
1. Copiar **mensagem de erro completa**
2. Copiar **logs do backend** (janela PowerShell)
3. Copiar **JSON da estratégia** (separador "Preview")
4. Abrir issue no GitHub ou contactar desenvolvedor

---

**Última atualização:** 28/10/2025 19:45
