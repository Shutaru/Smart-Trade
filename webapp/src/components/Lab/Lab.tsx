import React from 'react';
import { useNavigate } from 'react-router-dom';
import BacktestCard from './BacktestCard';
import GridSearchCard from './GridSearchCard';
import WalkForwardCard from './WalkForwardCard';
import OptunaCard from './OptunaCard';
import RunsList from './RunsList';
import { Button } from '@/components/ui/button';
import { Beaker, GitCompare } from 'lucide-react';
import { motion } from 'framer-motion';

const Lab: React.FC = () => {
    const navigate = useNavigate();

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
                <h1 className="text-3xl font-bold">Strategy Lab</h1>
                <div className="flex gap-2">
                    <Button onClick={() => navigate('/lab/compare')} variant="outline" className="gap-2">
                        <GitCompare className="h-4 w-4" />
                        Compare Runs
                    </Button>
                    <Button onClick={() => navigate('/lab/strategy')} className="gap-2">
                        <Beaker className="h-4 w-4" />
                        Strategy Builder
                    </Button>
                </div>
            </div>

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