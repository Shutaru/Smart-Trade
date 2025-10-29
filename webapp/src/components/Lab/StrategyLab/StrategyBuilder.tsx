import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
	Select,
	SelectContent,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from '@/components/ui/select';
import {
	Table,
	TableBody,
	TableCell,
	TableHead,
	TableHeader,
	TableRow,
} from '@/components/ui/table';
import {
	Tooltip,
	TooltipContent,
	TooltipProvider,
	TooltipTrigger,
} from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { Plus, Trash2, HelpCircle } from 'lucide-react';
import { useIndicatorOperators } from '@/hooks/useIndicatorOperators';
import {
	formatOperator,
	getAllOperators,
	getCategoryVariant,
	formatCategory,
} from '@/lib/indicator-utils';

interface Condition {
	indicator: string;
	timeframe: string;
	op: string;
	params: Array<{ name: string; value: any }>;
	rhs?: number;
	rhs_indicator?: string;
	rhs_params?: Array<{ name: string; value: any }>;
}

interface StrategySide {
	entry_all: Condition[];
	entry_any: Condition[];
	exit_rules: any[];
}

interface StrategyBuilderProps {
	value: {
		long: StrategySide;
		short: StrategySide;
	};
	onChange: (value: any) => void;
}

// Component for dynamic operator selection with recommendations
function OperatorSelectCell({
	condition,
	side,
	type,
	index,
	updateCondition,
}: {
	condition: Condition;
	side: 'long' | 'short';
	type: 'entry_all' | 'entry_any';
	index: number;
	updateCondition: (
		side: 'long' | 'short',
		type: 'entry_all' | 'entry_any',
		index: number,
		updates: Partial<Condition>
	) => void;
}) {
	const { data: operatorsInfo } = useIndicatorOperators(condition.indicator || null);

	return (
		<TableCell>
			<div className="flex items-center gap-2">
				<Select
					value={condition.op}
					onValueChange={(v) => updateCondition(side, type, index, { op: v })}
				>
					<SelectTrigger className="w-[180px]">
						<SelectValue />
					</SelectTrigger>
					<SelectContent>
						{operatorsInfo && operatorsInfo.recommended_operators.length > 0 ? (
							<>
								{/* Recommended Section */}
								<SelectItem
									value="group-recommended"
									disabled
									className="font-semibold text-xs text-primary"
								>
									? RECOMMENDED
								</SelectItem>
								{operatorsInfo.recommended_operators.map((op) => (
									<SelectItem key={`rec-${op}`} value={op} className="pl-6">
										{formatOperator(op)}
									</SelectItem>
								))}

								{/* Other Section */}
								{(() => {
									const allOps = getAllOperators();
									const otherOps = allOps.filter(
										(op) => !operatorsInfo.recommended_operators.includes(op)
									);

									if (otherOps.length === 0) return null;

									return (
										<>
											<SelectItem
												value="group-other"
												disabled
												className="font-semibold text-xs mt-2"
											>
												OTHER
											</SelectItem>
											{otherOps.map((op) => (
												<SelectItem key={`other-${op}`} value={op} className="pl-6 opacity-70">
													{formatOperator(op)}
												</SelectItem>
											))}
										</>
									);
								})()}
							</>
						) : (
							// Fallback: show all operators
							getAllOperators().map((op) => (
								<SelectItem key={op} value={op}>
									{formatOperator(op)}
								</SelectItem>
							))
						)}
					</SelectContent>
				</Select>

				{/* HELP ICON - Shows usage hint */}
				{operatorsInfo?.usage_hint && (
					<TooltipProvider>
						<Tooltip>
							<TooltipTrigger asChild>
								<button
									type="button"
									className="text-muted-foreground hover:text-foreground"
								>
									<HelpCircle className="h-4 w-4" />
								</button>
							</TooltipTrigger>
							<TooltipContent className="max-w-xs" side="right">
								<div className="space-y-2">
									{/* Category Badge */}
									<div className="flex items-center gap-2">
										<Badge variant={getCategoryVariant(operatorsInfo.category)}>
											{formatCategory(operatorsInfo.category)}
										</Badge>
										{operatorsInfo.range.bounded && (
											<span className="text-xs text-muted-foreground">
												Range: {operatorsInfo.range.min} - {operatorsInfo.range.max}
											</span>
										)}
									</div>

									{/* Usage Hint */}
									<p className="text-sm">{operatorsInfo.usage_hint}</p>

									{/* Typical Levels */}
									{Object.keys(operatorsInfo.typical_levels).length > 0 && (
										<div className="mt-2 pt-2 border-t space-y-1">
											<p className="font-semibold text-xs">Typical Levels:</p>
											{Object.entries(operatorsInfo.typical_levels).map(
												([name, value]) => (
													<div
														key={name}
														className="flex justify-between text-xs"
													>
														<span className="capitalize">{name.replace(/_/g, ' ')}:</span>
														<span className="font-mono font-semibold">{value}</span>
													</div>
												)
											)}
										</div>
									)}
								</div>
							</TooltipContent>
						</Tooltip>
					</TooltipProvider>
				)}
			</div>
		</TableCell>
	);
}

export function StrategyBuilder({ value, onChange }: StrategyBuilderProps) {
	const [activeTab, setActiveTab] = useState<'long' | 'short'>('long');

	const { data: indicatorsData } = useQuery({
		queryKey: ['indicators'],
		queryFn: async () => {
			const res = await fetch('/api/lab/indicators');
			return res.json();
		},
	});

	const addCondition = (side: 'long' | 'short', type: 'entry_all' | 'entry_any') => {
		const newCondition: Condition = {
			indicator: '',
			timeframe: '5m',
			op: '>',
			params: [],
		};

		const newValue = { ...value };
		newValue[side][type] = [...newValue[side][type], newCondition];
		onChange(newValue);
	};

	const updateCondition = (
		side: 'long' | 'short',
		type: 'entry_all' | 'entry_any',
		index: number,
		updates: Partial<Condition>
	) => {
		const newValue = { ...value };
		newValue[side][type][index] = { ...newValue[side][type][index], ...updates };
		onChange(newValue);
	};

	const removeCondition = (
		side: 'long' | 'short',
		type: 'entry_all' | 'entry_any',
		index: number
	) => {
		const newValue = { ...value };
		newValue[side][type] = newValue[side][type].filter((_, i) => i !== index);
		onChange(newValue);
	};

	const renderConditionsList = (
		side: 'long' | 'short',
		type: 'entry_all' | 'entry_any'
	) => {
		const conditions = value[side][type];
		const title = type === 'entry_all' ? 'ALL Conditions (AND)' : 'ANY Conditions (OR)';

		return (
			<div className="space-y-4">
				<div className="flex items-center justify-between">
					<h3 className="text-lg font-semibold">{title}</h3>
					<Button
						size="sm"
						onClick={() => addCondition(side, type)}
						className="gap-2"
					>
						<Plus className="h-4 w-4" />
						Add Condition
					</Button>
				</div>

				{conditions.length === 0 ? (
					<p className="text-sm text-muted-foreground">No conditions added yet</p>
				) : (
					<Table>
						<TableHeader>
							<TableRow>
								<TableHead>Indicator</TableHead>
								<TableHead>Timeframe</TableHead>
								<TableHead>Operator</TableHead>
								<TableHead>Value</TableHead>
								<TableHead className="w-[50px]"></TableHead>
							</TableRow>
						</TableHeader>
						<TableBody>
							{conditions.map((condition, index) => (
								<TableRow key={index}>
									<TableCell>
										<Select
											value={condition.indicator}
											onValueChange={(v) => {
												const indicator = indicatorsData?.indicators?.find(
													(ind: any) => ind.id === v
												);
												const defaultParams = indicator
													? Object.entries(indicator.params).map(
															([name, config]: [string, any]) => ({
																name,
																value: config.default,
															})
													  )
													: [];
												updateCondition(side, type, index, {
													indicator: v,
													params: defaultParams,
												});
											}}
										>
											<SelectTrigger className="w-[180px]">
												<SelectValue placeholder="Select indicator" />
											</SelectTrigger>
											<SelectContent>
												{indicatorsData?.indicators?.map((ind: any) => (
													<SelectItem key={ind.id} value={ind.id}>
														{ind.name}
													</SelectItem>
												))}
											</SelectContent>
										</Select>
									</TableCell>

									<TableCell>
										<Select
											value={condition.timeframe}
											onValueChange={(v) => updateCondition(side, type, index, { timeframe: v })}
										>
											<SelectTrigger className="w-[120px]">
												<SelectValue />
											</SelectTrigger>
											<SelectContent>
												<SelectItem value="1m">1m</SelectItem>
												<SelectItem value="5m">5m</SelectItem>
												<SelectItem value="15m">15m</SelectItem>
												<SelectItem value="1h">1h</SelectItem>
												<SelectItem value="4h">4h</SelectItem>
												<SelectItem value="1d">1d</SelectItem>
											</SelectContent>
										</Select>
									</TableCell>

									{/* OPERATOR SELECT - DYNAMIC */}
									<OperatorSelectCell
										condition={condition}
										side={side}
										type={type}
										index={index}
										updateCondition={updateCondition}
									/>

									<TableCell>
										<Input
											type="number"
											value={condition.rhs || ''}
											onChange={(e) =>
												updateCondition(side, type, index, {
													rhs: parseFloat(e.target.value),
												})
											}
											placeholder="Value"
											className="w-[120px]"
										/>
									</TableCell>

									<TableCell>
										<Button
											size="icon"
											variant="ghost"
											onClick={() => removeCondition(side, type, index)}
										>
											<Trash2 className="h-4 w-4 text-destructive" />
										</Button>
									</TableCell>
								</TableRow>
							))}
						</TableBody>
					</Table>
				)}
			</div>
		);
	};

	return (
		<Card>
			<CardHeader>
				<CardTitle>Strategy Builder</CardTitle>
				<CardDescription>
					Define entry conditions for long and short positions
				</CardDescription>
			</CardHeader>
			<CardContent>
				<Tabs
					value={activeTab}
					onValueChange={(v) => setActiveTab(v as 'long' | 'short')}
				>
					<TabsList className="grid w-full grid-cols-2">
						<TabsTrigger value="long">Long Side</TabsTrigger>
						<TabsTrigger value="short">Short Side</TabsTrigger>
					</TabsList>

					<TabsContent value="long" className="space-y-6 mt-6">
						{renderConditionsList('long', 'entry_all')}
						{renderConditionsList('long', 'entry_any')}
					</TabsContent>

					<TabsContent value="short" className="space-y-6 mt-6">
						{renderConditionsList('short', 'entry_all')}
						{renderConditionsList('short', 'entry_any')}
					</TabsContent>
				</Tabs>
			</CardContent>
		</Card>
	);
}