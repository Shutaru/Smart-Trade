from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import time
import random

# Ponto de acesso para as rotas relacionadas com os bots
router = APIRouter()

# --- Base de Dados Falsa (Placeholder) ---
DB_BOTS = {
    1: {"id": 1, "name": 'BTC Scalper', "status": 'Running', "mode": 'Live', "pnl": 5.23, "profile": "scalper_v1.yaml"},
    2: {"id": 2, "name": 'ETH Trend Follower', "status": 'Paused', "mode": 'Paper', "pnl": -1.45, "profile": "trend_v2.yaml"},
    3: {"id": 3, "name": 'SOL Momentum', "status": 'Stopped', "mode": 'Live', "pnl": 12.81, "profile": "momentum_v1.yaml"},
}
next_bot_id = 4

# --- Modelos Pydantic (Tipagem de Dados da API) ---
class BotCreateModel(BaseModel):
    name: str
    profile: str
    mode: str  # "paper" ou "live"

class BotControlModel(BaseModel):
    id: int

# --- Endpoints da API ---

@router.get("/api/bots/list")
async def get_bots_list():
    """Retorna a lista de todos os bots configurados."""
    time.sleep(0.5) # Simular latência da rede
    return list(DB_BOTS.values())

@router.post("/api/bots/create")
async def create_bot(bot_data: BotCreateModel):
    """Cria um novo bot."""
    global next_bot_id
    new_bot = {
        "id": next_bot_id,
        "name": bot_data.name,
        "profile": bot_data.profile,
        "mode": bot_data.mode,
        "status": "Stopped",
        "pnl": 0.0,
    }
    DB_BOTS[next_bot_id] = new_bot
    next_bot_id += 1
    return new_bot

@router.post("/api/bots/{action}")
async def control_bot(action: str, bot_control: BotControlModel):
    """Controla um bot: start, stop, pause."""
    if bot_control.id not in DB_BOTS:
        raise HTTPException(status_code=404, detail="Bot not found")
        
    valid_actions = ["start", "stop", "pause"]
    if action not in valid_actions:
        raise HTTPException(status_code=400, detail="Invalid action")

    action_to_status = {"start": "Running", "stop": "Stopped", "pause": "Paused"}
    DB_BOTS[bot_control.id]["status"] = action_to_status[action]
    
    return {"status": "success", "bot_id": bot_control.id, "new_status": DB_BOTS[bot_control.id]["status"]}

@router.post("/api/bots/delete")
async def delete_bot(bot_control: BotControlModel):
    """Remove um bot."""
    if bot_control.id not in DB_BOTS:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    del DB_BOTS[bot_control.id]
    return {"status": "success", "deleted_bot_id": bot_control.id}

@router.get("/api/bots/detail")
async def get_bot_detail(id: int):
    """Retorna os detalhes de um bot específico."""
    if id not in DB_BOTS:
        raise HTTPException(status_code=404, detail="Bot not found")

    # Gerar dados de exemplo dinâmicos
    performance_data = [{
        "time": time.strftime('%Y-%m-%d', time.gmtime(time.time() - (100 - i) * 3600 * 24)),
        "value": 1000 + i * 10 + random.uniform(-50, 50)
    } for i in range(100)]
    
    trades_data = [{
        "id": i, "timestamp": time.time() - i * 3600 * 24, "symbol": 'BTC/USDT', 
        "side": 'buy' if i % 2 == 0 else 'sell', "price": 50000 + i * 100, 
        "amount": 0.01, "pnl": random.uniform(-10, 20)
    } for i in range(15)]

    mock_detail = {
        "name": DB_BOTS[id]["name"],
        "kpis": { "pnl": 1250.75, "winRate": 68.4, "totalTrades": 212, "sharpe": 1.87 },
        "performanceData": performance_data,
        "trades": trades_data,
    }
    return mock_detail
