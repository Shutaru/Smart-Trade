"""
Execution tool for realistic paper trading simulation

Supports:
- Market orders (immediate fill with slippage)
- Limit orders (fill when price crosses, otherwise pending)
- Stop-market orders (trigger → market fill)
- Take-profit orders
- OCO (One-Cancels-Other) for SL+TP pairs
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import time
import uuid
from enum import Enum

from ..schemas import OrderSide, OrderType, OrderStatus
from ..config import AgentConfig
from .portfolio import PortfolioTool


@dataclass
class OrderRequest:
    """Order request from agent"""
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    take_profit: Optional[float] = None  # TP price
    stop_loss: Optional[float] = None  # SL price
    oco: bool = False  # One-Cancels-Other (for TP+SL)
    client_order_id: Optional[str] = None  # For idempotency


@dataclass
class FilledOrder:
    """Filled order result"""
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    filled_quantity: float
    filled_price: float
    average_price: float
    fee: float
    status: OrderStatus
    timestamp: int
    slippage_bps: float
    is_maker: bool
    notes: str = ""


@dataclass
class PendingOrder:
    """Order waiting for trigger"""
    order_id: str
    client_order_id: Optional[str]
    symbol: str
    side: OrderSide
    type: OrderType
    quantity: float
    price: Optional[float]  # Limit price
    stop_price: Optional[float]  # Stop trigger
    created_at: int
    oco_group: Optional[str] = None  # Group ID for OCO orders


class ExecutionTool:
    """
    Realistic paper trading execution engine
    
    Features:
    - Market orders: immediate fill with slippage
    - Limit orders: fill when price crosses, otherwise pending
    - Stop orders: trigger → market execution
    - OCO orders: TP+SL pairs (cancel one when other fills)
    - Order book: tracks pending orders
    - Idempotency: prevents duplicate orders
    - Realistic fees: maker vs taker
    """
    
    def __init__(self, config: AgentConfig, portfolio: PortfolioTool):
        self.config = config
        self.portfolio = portfolio
        
        # Pending orders book
        self._pending_orders: Dict[str, PendingOrder] = {}
        
        # Executed order IDs (for idempotency)
        self._executed_orders: set = set()
        
        # OCO groups tracking
        self._oco_groups: Dict[str, List[str]] = {}  # group_id -> [order_id1, order_id2]
    
    def execute_orders(self, orders: List[OrderRequest], 
                       current_prices: Dict[str, float]) -> Tuple[List[FilledOrder], List[PendingOrder]]:
        """
        Execute batch of orders
        
        Args:
            orders: List of order requests from agent
            current_prices: Current market prices {symbol: price}
        
        Returns:
            Tuple of (filled_orders, pending_orders)
        """
        filled = []
        pending = []
        
        for order_req in orders:
            # Check idempotency
            if order_req.client_order_id and order_req.client_order_id in self._executed_orders:
                print(f"[Execution] Skipping duplicate order: {order_req.client_order_id}")
                continue
            
            # Get current price
            current_price = current_prices.get(order_req.symbol)
            if current_price is None:
                print(f"[Execution] No price available for {order_req.symbol}, skipping")
                continue
            
            # Handle OCO orders (TP+SL pair)
            if order_req.oco and order_req.take_profit and order_req.stop_loss:
                filled_oco, pending_oco = self._execute_oco_order(order_req, current_price)
                filled.extend(filled_oco)
                pending.extend(pending_oco)
            else:
                # Single order
                result = self._execute_single_order(order_req, current_price)
                if isinstance(result, FilledOrder):
                    filled.append(result)
                elif isinstance(result, PendingOrder):
                    pending.append(result)
        
        return filled, pending
    
    def process_pending_orders(self, current_prices: Dict[str, float]) -> List[FilledOrder]:
        """
        Check pending orders against current prices and fill if triggered
        
        Args:
            current_prices: Current market prices
        
        Returns:
            List of newly filled orders
        """
        filled = []
        to_remove = []
        
        for order_id, pending in self._pending_orders.items():
            price = current_prices.get(pending.symbol)
            if price is None:
                continue
            
            # Check if order should trigger
            should_fill = False
            
            if pending.type == OrderType.LIMIT:
                # Limit order: fill when price crosses
                if pending.side == OrderSide.BUY and price <= pending.price:
                    should_fill = True
                elif pending.side == OrderSide.SELL and price >= pending.price:
                    should_fill = True
            
            elif pending.type == OrderType.STOP_MARKET:
                # Stop order: trigger when price hits stop_price
                if pending.side == OrderSide.BUY and price >= pending.stop_price:
                    should_fill = True
                elif pending.side == OrderSide.SELL and price <= pending.stop_price:
                    should_fill = True
            
            if should_fill:
                # Fill the order
                fill_price = pending.price if pending.type == OrderType.LIMIT else self._apply_slippage(price, pending.side)
                
                filled_order = self._fill_order(
                    order_id=pending.order_id,
                    client_order_id=pending.client_order_id,
                    symbol=pending.symbol,
                    side=pending.side,
                    type=pending.type,
                    quantity=pending.quantity,
                    fill_price=fill_price,
                    is_maker=(pending.type == OrderType.LIMIT)
                )
                
                filled.append(filled_order)
                to_remove.append(order_id)
                
                # Handle OCO cancellation
                if pending.oco_group:
                    self._cancel_oco_group(pending.oco_group, except_order_id=order_id)
        
        # Remove filled orders from pending
        for order_id in to_remove:
            del self._pending_orders[order_id]
        
        return filled
    
    def _execute_single_order(self, order_req: OrderRequest, current_price: float) -> Optional[FilledOrder | PendingOrder]:
        """Execute a single order"""
        
        order_id = str(uuid.uuid4())
        
        # MARKET ORDER: immediate fill
        if order_req.type == OrderType.MARKET:
            fill_price = self._apply_slippage(current_price, order_req.side)
            
            return self._fill_order(
                order_id=order_id,
                client_order_id=order_req.client_order_id,
                symbol=order_req.symbol,
                side=order_req.side,
                type=order_req.type,
                quantity=order_req.quantity,
                fill_price=fill_price,
                is_maker=False
            )
        
        # LIMIT ORDER: check if can fill immediately, otherwise pending
        elif order_req.type == OrderType.LIMIT:
            if order_req.price is None:
                print(f"[Execution] Limit order requires price")
                return None
            
            # Check if limit price already crossed
            can_fill_now = (
                (order_req.side == OrderSide.BUY and current_price <= order_req.price) or
                (order_req.side == OrderSide.SELL and current_price >= order_req.price)
            )
            
            if can_fill_now:
                # Fill at limit price (maker)
                return self._fill_order(
                    order_id=order_id,
                    client_order_id=order_req.client_order_id,
                    symbol=order_req.symbol,
                    side=order_req.side,
                    type=order_req.type,
                    quantity=order_req.quantity,
                    fill_price=order_req.price,
                    is_maker=True
                )
            else:
                # Add to pending
                pending = PendingOrder(
                    order_id=order_id,
                    client_order_id=order_req.client_order_id,
                    symbol=order_req.symbol,
                    side=order_req.side,
                    type=order_req.type,
                    quantity=order_req.quantity,
                    price=order_req.price,
                    stop_price=None,
                    created_at=int(time.time() * 1000)
                )
                self._pending_orders[order_id] = pending
                return pending
        
        # STOP-MARKET ORDER: pending until triggered
        elif order_req.type == OrderType.STOP_MARKET:
            if order_req.stop_price is None:
                print(f"[Execution] Stop order requires stop_price")
                return None
            
            # Check if already triggered
            triggered = (
                (order_req.side == OrderSide.BUY and current_price >= order_req.stop_price) or
                (order_req.side == OrderSide.SELL and current_price <= order_req.stop_price)
            )
            
            if triggered:
                # Execute as market
                fill_price = self._apply_slippage(current_price, order_req.side)
                return self._fill_order(
                    order_id=order_id,
                    client_order_id=order_req.client_order_id,
                    symbol=order_req.symbol,
                    side=order_req.side,
                    type=order_req.type,
                    quantity=order_req.quantity,
                    fill_price=fill_price,
                    is_maker=False
                )
            else:
                # Add to pending
                pending = PendingOrder(
                    order_id=order_id,
                    client_order_id=order_req.client_order_id,
                    symbol=order_req.symbol,
                    side=order_req.side,
                    type=order_req.type,
                    quantity=order_req.quantity,
                    price=None,
                    stop_price=order_req.stop_price,
                    created_at=int(time.time() * 1000)
                )
                self._pending_orders[order_id] = pending
                return pending
        
        return None
    
    def _execute_oco_order(self, order_req: OrderRequest, current_price: float) -> Tuple[List[FilledOrder], List[PendingOrder]]:
        """
        Execute OCO (One-Cancels-Other) order pair (TP + SL)
        
        Args:
            order_req: Order request with take_profit and stop_loss
            current_price: Current market price
        
        Returns:
            Tuple of (filled, pending)
        """
        filled = []
        pending = []
        
        oco_group_id = str(uuid.uuid4())
        
        # Create TP order (LIMIT)
        tp_order = OrderRequest(
            symbol=order_req.symbol,
            side=OrderSide.SELL if order_req.side == OrderSide.BUY else OrderSide.BUY,
            type=OrderType.LIMIT,
            quantity=order_req.quantity,
            price=order_req.take_profit,
            client_order_id=f"{order_req.client_order_id}_TP" if order_req.client_order_id else None
        )
        
        # Create SL order (STOP_MARKET)
        sl_order = OrderRequest(
            symbol=order_req.symbol,
            side=OrderSide.SELL if order_req.side == OrderSide.BUY else OrderSide.BUY,
            type=OrderType.STOP_MARKET,
            quantity=order_req.quantity,
            stop_price=order_req.stop_loss,
            client_order_id=f"{order_req.client_order_id}_SL" if order_req.client_order_id else None
        )
        
        # Execute TP
        tp_result = self._execute_single_order(tp_order, current_price)
        if isinstance(tp_result, PendingOrder):
            tp_result.oco_group = oco_group_id
            self._pending_orders[tp_result.order_id] = tp_result
            pending.append(tp_result)
            self._oco_groups.setdefault(oco_group_id, []).append(tp_result.order_id)
        elif isinstance(tp_result, FilledOrder):
            filled.append(tp_result)
        
        # Execute SL (only if TP didn't fill immediately)
        if not filled:
            sl_result = self._execute_single_order(sl_order, current_price)
            if isinstance(sl_result, PendingOrder):
                sl_result.oco_group = oco_group_id
                self._pending_orders[sl_result.order_id] = sl_result
                pending.append(sl_result)
                self._oco_groups.setdefault(oco_group_id, []).append(sl_result.order_id)
            elif isinstance(sl_result, FilledOrder):
                filled.append(sl_result)
        
        return filled, pending
    
    def _fill_order(self, order_id: str, client_order_id: Optional[str], symbol: str,
                    side: OrderSide, type: OrderType, quantity: float, 
                    fill_price: float, is_maker: bool) -> FilledOrder:
        """
        Fill an order and update portfolio
        
        Args:
            order_id: Internal order ID
            client_order_id: Client-provided ID (for idempotency)
            symbol: Trading symbol
            side: BUY or SELL
            type: Order type
            quantity: Order quantity
            fill_price: Execution price
            is_maker: True if maker order (limit), False if taker
        
        Returns:
            FilledOrder object
        """
        # Calculate fee
        notional = quantity * fill_price
        fee_bps = self.config.maker_fee_bps if is_maker else self.config.taker_fee_bps
        fee = notional * (fee_bps / 10000.0)
        
        # Calculate slippage (0 for limit orders)
        slippage_bps = 0.0 if is_maker else self.config.slippage_bps
        
        # Update portfolio
        self.portfolio.execute_trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=fill_price,
            fee=fee
        )
        
        # Mark as executed (idempotency)
        if client_order_id:
            self._executed_orders.add(client_order_id)
        
        # Create filled order
        filled = FilledOrder(
            order_id=order_id,
            client_order_id=client_order_id,
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            filled_quantity=quantity,
            filled_price=fill_price,
            average_price=fill_price,
            fee=fee,
            status=OrderStatus.FILLED,
            timestamp=int(time.time() * 1000),
            slippage_bps=slippage_bps,
            is_maker=is_maker,
            notes=f"{'Maker' if is_maker else 'Taker'} fill at ${fill_price:.2f}"
        )
        
        return filled
    
    def _apply_slippage(self, price: float, side: OrderSide) -> float:
        """Apply slippage to market order"""
        slippage_factor = self.config.slippage_bps / 10000.0
        
        if side == OrderSide.BUY:
            return price * (1 + slippage_factor)
        else:  # SELL
            return price * (1 - slippage_factor)
    
    def _cancel_oco_group(self, oco_group_id: str, except_order_id: str):
        """Cancel all orders in OCO group except the one that filled"""
        if oco_group_id not in self._oco_groups:
            return
        
        for order_id in self._oco_groups[oco_group_id]:
            if order_id != except_order_id and order_id in self._pending_orders:
                del self._pending_orders[order_id]
        
        del self._oco_groups[oco_group_id]
    
    def get_pending_orders(self) -> List[PendingOrder]:
        """Get all pending orders"""
        return list(self._pending_orders.values())
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order"""
        if order_id in self._pending_orders:
            del self._pending_orders[order_id]
            return True
        return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None):
        """Cancel all pending orders, optionally filtered by symbol"""
        if symbol:
            to_remove = [oid for oid, order in self._pending_orders.items() if order.symbol == symbol]
        else:
            to_remove = list(self._pending_orders.keys())
        
        for order_id in to_remove:
            del self._pending_orders[order_id]