import React from 'react';
import { motion } from 'framer-motion';
import AccountKPIs from './AccountKPIs';
import AccountEquityChart from './AccountEquityChart';
import ActiveBotsList from './ActiveBotsList';
import ActivityFeed from './ActivityFeed';

const Dashboard: React.FC = () => {
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
            <h1 className="text-3xl font-bold mb-6">Dashboard</h1>
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
                
                {/* Linha 1 */}
                <motion.div custom={0} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-6">
                    <AccountKPIs />
                </motion.div>
                
                <motion.div custom={1} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-2">
                    <ActiveBotsList />
                </motion.div>

                {/* Linha 2 */}
                <motion.div custom={2} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-4">
                    <AccountEquityChart />
                </motion.div>
                
                {/* Linha 3 */}
                <motion.div custom={3} initial="hidden" animate="visible" variants={cardVariants} className="lg:col-span-4">
                    <ActivityFeed />
                </motion.div>
            </div>
        </div>
    );
};

export default Dashboard;
