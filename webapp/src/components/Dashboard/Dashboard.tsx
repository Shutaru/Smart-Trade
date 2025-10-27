import React from 'react';
import { motion } from 'framer-motion';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api';
import ModeToggle from './ModeToggle';
import AccountKPIs from './AccountKPIs';
import PaperKPIs from './PaperKPIs';
import AccountEquityChart from './AccountEquityChart';
import ActiveBotsList from './ActiveBotsList';
import ActivityFeed from './ActivityFeed';

const fetchConfig = async () => {
    const { data } = await api.get('/api/config/read');
    return data;
};

const Dashboard: React.FC = () => {
    const { data: config } = useQuery({ 
        queryKey: ['config'], 
        queryFn: fetchConfig 
    });

    const isLiveMode = config?.mode === 'live';

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
 <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">Dashboard</h1>
         <div className="w-80">
        <ModeToggle />
                </div>
   </div>
            
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
    
       {/* Linha 1 - KPIs */}
  <motion.div custom={0} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
     {isLiveMode ? <AccountKPIs /> : <PaperKPIs />}
  </motion.div>
   
    <motion.div custom={1} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-2">
          <ActiveBotsList />
       </motion.div>

       {/* Linha 2 - Gráfico de Equity */}
       <motion.div custom={2} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-4">
        <AccountEquityChart mode={isLiveMode ? 'live' : 'paper'} />
       </motion.div>
      
      {/* Linha 3 - Activity Feed */}
  <motion.div custom={3} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-4">
  <ActivityFeed />
          </motion.div>
    </div>
        </div>
    );
};

export default Dashboard;
