import React from 'react';
import CandleChart from '../Chart/CandleChart';
import OrderPanel from './OrderPanel';
import PositionsTable from './PositionsTable';
import OrdersTable from './OrdersTable';
import ActionsPanel from './ActionsPanel';

const SmartTrade: React.FC = () => {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Smart Trade</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="md:col-span-2">
          <CandleChart />
        </div>
        <div>
          <OrderPanel />
          <div className="mt-4">
            <ActionsPanel />
          </div>
        </div>
      </div>
      <div className="mt-4">
        <PositionsTable />
      </div>
      <div className="mt-4">
        <OrdersTable />
      </div>
    </div>
  );
};

export default SmartTrade;
