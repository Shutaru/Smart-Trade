# ? Strategy Lab - FAQ & Troubleshooting

## ?? ERROS COMUNS

### **Erro 1: "No symbols specified in config"**

**Mensagem completa:**
```
ValueError: No symbols specified in strategy configuration.
Please add at least one symbol in the Data tab
```

**Causa:** O campo `symbols` est� vazio no JSON enviado ao backend.

**Solu��o:**
1. Ir ao **separador "Data"**
2. Clicar no bot�o **"Select symbols..."**
3. ?? Procurar pelo s�mbolo (ex: `BTC/USDT`)
4. ? Clicar no s�mbolo para selecionar (aparece ?)
5. Clicar fora para fechar o popup
6. Verificar que aparece um **badge azul** com o s�mbolo
7. Agora podes fazer **"Validate"** e **"Run"**

**Screenshot da sele��o:**
```
???????????????????????????????????
? Symbols (1 selected)      ?
???????????????????????????????????
? [Select symbols... ?]           ?
?   ?
? ?????????????????????????????  ?
? ? BTC/USDT:USDT             ?  ?  ? Badge azul confirma sele��o
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

**Causa:** Ainda n�o fizeste download dos dados hist�ricos.

**Solu��o:**
1. Selecionar s�mbolo (ver Erro 1)
2. Clicar no bot�o **"Backfill Data"**
3. Aguardar 10-30 segundos
4. Deve aparecer: **"Backfill Complete - Downloaded X candles"**
5. Agora podes rodar o backtest

**O que faz o Backfill:**
- Baixa dados OHLCV do exchange via CCXT
- Calcula indicadores (RSI, EMA, SMA, ATR, etc)
- Guarda em SQLite (`data/lab/{exchange}/{symbol}_{timeframe}.db`)
- S� precisa fazer uma vez por s�mbolo/timeframe

---

### **Erro 3: "No data found for {symbol} in specified date range"**

**Mensagem completa:**
```
ValueError: No data found for BTC/USDT:USDT in the specified date range.
Period: 2024-01-01 to 2024-10-28
Try backfilling data or adjusting the date range.
```

**Causa:** O per�odo selecionado n�o tem dados no DB.

**Solu��o:**
1. Verificar **Start Date** e **End Date** no separador Data
2. Fazer backfill novamente para o per�odo desejado
3. Ou ajustar datas para um per�odo mais recente

**Nota:** CCXT pode ter limites de quanto dados consegue baixar de uma vez.

---

### **Erro 4: "Insufficient data: got 50 bars, need at least 300"**

**Mensagem completa:**
```
ValueError: Insufficient data: got 50 bars, need at least 300
```

**Causa:** `warmup_bars: 300` (default) precisa de pelo menos 300 candles para calcular indicadores.

**Solu��o:**
1. Aumentar per�odo de tempo (Start Date mais atr�s)
2. Ou diminuir `warmup_bars` no JSON (separador "Preview")
3. Fazer backfill com per�odo maior

---

### **Erro 5: Charts n�o aparecem**

**Sintomas:**
- Backtest completa com sucesso
- Tab "Metrics" mostra m�tricas
- Mas charts est�o vazios/brancos

**Causa:** Problema de rendering do Lightweight Charts.

**Solu��o:**
1. Abrir DevTools (F12)
2. Ir ao **Console**
3. Copiar erros JavaScript
4. Partilhar com desenvolvedor

**Causas comuns:**
- Dados com timestamps inv�lidos
- NaN values nos dados
- Biblioteca n�o carregou

---

### **Erro 6: "Failed to fetch trades"**

**Sintomas:**
- Tab "Trades" mostra erro vermelho
- "Failed to load trades"

**Causa:** Backend crashou ou `trades.csv` n�o foi gerado.

**Solu��o:**
1. Verificar logs do backend (janela PowerShell)
2. Procurar por tracebacks Python
3. Reiniciar backend se necess�rio:
```sh
Ctrl+C (para parar)
python -m uvicorn gui_server:app --host 127.0.0.1 --port 8000 --reload
```

---

### **Erro 7: "Validation Errors"**

**Sintomas:**
- Bot�o "Validate" mostra ?
- Lista de erros aparece

**Causas comuns:**
- **No long or short conditions:** Precisa definir pelo menos 1 condi��o
- **Invalid indicator:** Nome de indicador inv�lido
- **Invalid operator:** Operador n�o suportado

**Solu��o:**
1. Ir ao separador **"Strategy"**
2. Adicionar pelo menos 1 condi��o Long OU Short
3. Verificar que indicadores s�o v�lidos (RSI, EMA, SMA, etc)
4. Re-validar

---

## ? CHECKLIST ANTES DE RODAR BACKTEST

- [ ] **S�mbolo selecionado** (badge azul vis�vel)
- [ ] **Data backfilled** (bot�o "Backfill Data" clicado com sucesso)
- [ ] **Condi��es definidas** (pelo menos 1 Long OU Short)
- [ ] **Objective configurado** (ex: `sharpe`)
- [ ] **Valida��o OK** (bot�o "Validate" mostra ?)
- [ ] **Backend a correr** (http://127.0.0.1:8000)

---

## ?? COMO DEBUGGAR

### **Ver payload JSON enviado:**
1. Abrir DevTools (F12)
2. Ir ao separador **"Network"**
3. Filtrar por `backtest`
4. Clicar no request `POST /api/lab/run/backtest`
5. Ver **"Payload"** ou **"Request Body"**
6. Verificar que `symbols: ["BTC/USDT:USDT"]` (n�o vazio!)

### **Ver logs do backend:**
- Janela PowerShell onde iniciaste o uvicorn
- Procurar por `[run_id] ERROR:` linhas
- Copiar traceback completo

### **Ver state do frontend:**
Adicionar no console DevTools:
```javascript
// Ver estrat�gia atual
console.log(JSON.stringify(strategy, null, 2));

// Ver se symbols est� populated
console.log("Symbols:", strategy.data.symbols);
```

---

## ?? SUPORTE

**Erro n�o listado aqui?**
1. Copiar **mensagem de erro completa**
2. Copiar **logs do backend** (janela PowerShell)
3. Copiar **JSON da estrat�gia** (separador "Preview")
4. Abrir issue no GitHub ou contactar desenvolvedor

---

**�ltima atualiza��o:** 28/10/2025 19:45
