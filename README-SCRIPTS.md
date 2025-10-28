# ?? Smart-Trade - Scripts de Desenvolvimento

Scripts PowerShell para facilitar o desenvolvimento e deployment no Windows.

## ?? Setup Inicial

Execute **uma vez** após clonar o repositório:

```powershell
.\setup.ps1
```

**O que faz:**
- ? Verifica Python 3.10+ e Node.js 18+
- ? Cria virtual environment (`.venv`)
- ? Instala dependências Python (`requirements.txt`)
- ? Instala dependências Node.js (`package.json`)
- ? Cria diretórios necessários (`data/`, `artifacts/`)

---

## ??? Desenvolvimento

### Iniciar (Hot-reload ativo)

```powershell
.\start-dev.ps1
```

**O que faz:**
- ?? Inicia **Backend** (FastAPI com `--reload`)
  - URL: `http://127.0.0.1:8000`
  - API Docs: `http://127.0.0.1:8000/docs`
- ?? Inicia **Frontend** (Vite dev server)
  - URL: `http://localhost:5173`
  - Hot Module Replacement (HMR) ativo

**Janelas separadas:**
- Backend ? Nova janela PowerShell
- Frontend ? Nova janela PowerShell

### Parar servidores

```powershell
.\stop-dev.ps1
```

**O que faz:**
- ?? Para todos os processos `uvicorn` (backend)
- ?? Para todos os processos `vite` (frontend)

---

## ?? Produção

### Iniciar servidor de produção

```powershell
.\start-prod.ps1
```

**O que faz:**
1. ?? **Build do frontend** (`npm ci` + `npm run build`)
2. ? **Valida build** (verifica `webapp/dist/`)
3. ?? **Inicia servidor** em `0.0.0.0:8000`

**Acesso:**
- Local: `http://localhost:8000`
- Rede: `http://<seu-ip>:8000`
- API: `http://localhost:8000/docs`

**Diferenças vs Development:**
- ? Frontend otimizado (minified, tree-shaking)
- ? Servido pelo FastAPI (SPA fallback)
- ? Sem hot-reload (produção estável)
- ? Acessível na rede local

---

## ?? Estrutura de Arquivos

```
Smart-Trade/
??? setup.ps1    # Setup inicial (executar 1x)
??? start-dev.ps1      # Desenvolvimento (hot-reload)
??? start-prod.ps1     # Produção (build + serve)
??? stop-dev.ps1       # Parar servidores
??? .venv/    # Virtual environment Python
??? webapp/
?   ??? node_modules/  # Dependências Node
?   ??? dist/   # Build de produção
?   ??? src/         # Código fonte React
??? data/              # Dados persistentes
??? artifacts/         # Resultados de backtests
??? gui_server.py      # FastAPI server
```

---

## ?? Troubleshooting

### "Execution Policy" error

Se aparecer erro ao executar scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Backend não inicia

1. Verificar virtual environment:
   ```powershell
   .\.venv\Scripts\python.exe --version
   ```

2. Reinstalar dependências:
   ```powershell
   .\.venv\Scripts\pip install -r requirements.txt
   ```

### Frontend não inicia

1. Limpar cache:
   ```powershell
   cd webapp
   Remove-Item -Recurse -Force node_modules
   npm install
   ```

2. Verificar porta 5173 disponível:
   ```powershell
   netstat -ano | findstr :5173
   ```

### Build de produção falha

1. Limpar dist:
   ```powershell
   Remove-Item -Recurse -Force webapp\dist
   ```

2. Rebuild:
   ```powershell
   cd webapp
   npm run build
   ```

---

## ?? Quick Reference

| Comando | Uso |
|---------|-----|
| `.\setup.ps1` | Setup inicial do projeto |
| `.\start-dev.ps1` | Dev mode (hot-reload) |
| `.\start-prod.ps1` | Prod mode (optimized) |
| `.\stop-dev.ps1` | Parar servidores dev |

---

## ?? URLs de Acesso

### Development Mode
- **Frontend (Vite):** `http://localhost:5173`
- **Backend (FastAPI):** `http://127.0.0.1:8000`
- **API Docs:** `http://127.0.0.1:8000/docs`

### Production Mode
- **Application:** `http://localhost:8000`
- **API Docs:** `http://localhost:8000/docs`
- **Network Access:** `http://<your-ip>:8000`

---

## ?? Notas

- **Development:** Mudanças no código são aplicadas automaticamente (hot-reload)
- **Production:** Requer rebuild manual (`.\start-prod.ps1`)
- **Virtual environment:** Scripts usam `.venv\Scripts\python.exe` automaticamente
- **Node modules:** Scripts verificam e instalam se necessário

---

## ?? Links Úteis

- **Repository:** https://github.com/Shutaru/Smart-Trade
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Vite Docs:** https://vitejs.dev/
- **React Docs:** https://react.dev/
