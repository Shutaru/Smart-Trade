import React from 'react';
import BacktestCard from './BacktestCard';
import GridSearchCard from './GridSearchCard';
import WalkForwardCard from './WalkForwardCard';
import OptunaCard from './OptunaCard';
import RunsList from './RunsList';
import { motion } from 'framer-motion';

const Lab: React.FC = () => {
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i: number) => ({
      opacity: 1,
      y: 0,
      transition: {
        delay: i * 0.1,
        duration: 0.5,
      },
    }),
  };

  return (
    <div>
      <h1 className="text-3xl font-bold mb-6">Strategy Lab</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <motion.div custom={0} initial="hidden" animate="visible" variants={cardVariants}>
          <BacktestCard />
        </motion.div>
        <motion.div custom={1} initial="hidden" animate="visible" variants={cardVariants}>
          <GridSearchCard />
        </motion.div>
        <motion.div custom={2} initial="hidden" animate="visible" variants={cardVariants}>
          <WalkForwardCard />
        </motion.div>
        <motion.div custom={3} initial="hidden" animate="visible" variants={cardVariants}>
          <OptunaCard />
        </motion.div>
      </div>
      <div>
        <RunsList />
      </div>
    </div>
  );
};

export default Lab;
