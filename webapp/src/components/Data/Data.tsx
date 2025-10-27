import React from 'react';
import Backfill from './Backfill';
import PairsList from './PairsList';

const Data: React.FC = () => {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Data Management</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div>
          <PairsList />
        </div>
        <div>
          <Backfill />
        </div>
      </div>
    </div>
  );
};

export default Data;
