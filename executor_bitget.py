# executor_bitget.py — versão corrigida (indentação e funções novas OK)
import ccxt

class BitgetExecutor:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ex = ccxt.bitget({
            "apiKey": cfg.get("bitget", {}).get("api_key", ""),
            "secret": cfg.get("bitget", {}).get("api_secret", ""),
            "password": cfg.get("bitget", {}).get("password", ""),
            "options": {"defaultType": "swap"},
        })
        self.symbol = cfg.get("symbol", "BTC/USDT:USDT")

    def fetch_positions(self):
        try:
            return self.ex.fetch_positions([self.symbol])
        except Exception:
            try:
                return self.ex.fetch_positions()
            except Exception:
                return []

    def fetch_balance(self):
        try:
            return self.ex.fetch_balance({"type": "swap"})
        except Exception:
            try:
                return self.ex.fetch_balance()
            except Exception:
                return {}

    def fetch_ticker(self):
        try:
            return self.ex.fetch_ticker(self.symbol)
        except Exception:
            return {}

    def fetch_open_orders(self):
        try:
            return self.ex.fetch_open_orders(self.symbol)
        except Exception:
            return []

    def fetch_funding(self):
        try:
            fr = self.ex.fetch_funding_rate(self.symbol)
            return {"rate": fr.get("fundingRate"), "next": fr.get("nextFundingTime")}
        except Exception:
            return {}

    def set_leverage(self, leverage=3, margin_mode="cross"):
        try:
            return self.ex.set_leverage(leverage, self.symbol, {"marginMode": margin_mode})
        except Exception as e:
            return {"error": str(e)}

    def market_order(self, side, amount, reduce_only=False):
        side = side.lower()
        try:
            params = {"reduceOnly": True} if reduce_only else {}
            return self.ex.create_order(self.symbol, "market", side, amount, None, params)
        except Exception as e:
            return {"error": str(e)}

    def cancel_all(self):
        try:
            return self.ex.cancel_all_orders(self.symbol)
        except Exception as e:
            return {"error": str(e)}

    def close_market(self, side, amount):
        try:
            if str(side).upper() == "LONG":
                return self.market_order("sell", amount, reduce_only=True)
            else:
                return self.market_order("buy", amount, reduce_only=True)
        except Exception as e:
            return {"error": str(e)}

    def limit_order(self, side, amount, price, reduce_only=False, post_only=False):
        side = side.lower()
        try:
            params = {}
            if reduce_only:
                params["reduceOnly"] = True
            if post_only:
                params["postOnly"] = True
            return self.ex.create_order(self.symbol, "limit", side, amount, price, params)
        except Exception as e:
            return {"error": str(e)}

    def stop_order(self, side, amount, stopPrice, price=None, reduce_only=False, tp=False, sl=False):
        """
        Cria ordens condicionais:
          - tp=True  -> take profit             (usa takeProfitPrice)
          - sl=True  -> stop loss               (usa stopLossPrice)
          - default  -> stop/trigger genérico   (usa stopPrice)
        Fallback: usa params 'triggerPrice' se a rota unificada falhar.
        """
        side = side.lower()
        params = {}
        if reduce_only:
            params["reduceOnly"] = True
        try:
            # Tentativa unificada
            if tp:
                params["takeProfitPrice"] = stopPrice
                order_type = "takeProfit"
            elif sl:
                params["stopLossPrice"] = stopPrice
                order_type = "stopLoss"
            else:
                params["stopPrice"] = stopPrice
                order_type = "stop"
            return self.ex.create_order(self.symbol, order_type, side, amount, price, params)
        except Exception as e:
            # Fallback com triggerPrice
            try:
                params2 = {"triggerPrice": stopPrice}
                if reduce_only:
                    params2["reduceOnly"] = True
                if price is not None:
                    params2["price"] = price
                return self.ex.create_order(self.symbol, "limit", side, amount, price, params2)
            except Exception as e2:
                return {"error": f"{e} / fallback: {e2}"}

