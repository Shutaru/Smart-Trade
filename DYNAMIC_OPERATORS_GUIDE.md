# ?? DYNAMIC INDICATOR OPERATORS - Implementation Guide

## ? **BACKEND JÁ IMPLEMENTADO!**

### **Novos Ficheiros:**
1. ? `lab_indicators.py` - Expandido com metadados completos
2. ? `routers/lab.py` - Novo endpoint `/indicators/{indicator_id}/operators`

### **Novo Endpoint:**
```
GET /api/lab/indicators/{indicator_id}/operators
```

**Response Example (RSI):**
```json
{
  "indicator_id": "rsi",
  "indicator_name": "RSI (Relative Strength Index)",
  "category": "oscillator",
  "range": {
  "min": 0,
    "max": 100,
"bounded": true
  },
  "recommended_operators": [
    "crosses_above",  // RSI crosses above 30 (oversold ? bullish)
    "crosses_below",  // RSI crosses below 70 (overbought ? bearish)
    ">",              // RSI > 50 (bullish momentum)
    "<", // RSI < 30 (oversold)
    "between" // RSI between 40-60 (neutral zone)
  ],
  "typical_levels": {
    "oversold": 30,
    "neutral": 50,
    "overbought": 70,
    "extreme_oversold": 20,
    "extreme_overbought": 80
  },
  "usage_hint": "Use crossover/crossunder for entry signals, > or < for filters"
}
```

---

## ?? **FRONTEND IMPLEMENTATION**

### **1. Atualizar `webapp/src/lib/api-lab.ts`**

Adiciona esta função:

```typescript
// ============================================================================
// INDICATOR OPERATORS (DYNAMIC)
// ============================================================================

export interface IndicatorOperatorsInfo {
  indicator_id: string;
  indicator_name: string;
  category: string;
  range: {
  min?: number;
    max?: number;
    bounded: boolean;
  };
  recommended_operators: string[];
  typical_levels: Record<string, number>;
  usage_hint: string;
}

export async function getIndicatorOperators(indicatorId: string): Promise<IndicatorOperatorsInfo> {
  try {
    const { data } = await api.get<IndicatorOperatorsInfo>(`/indicators/${indicatorId}/operators`);
    return data;
  } catch (error) {
    return handleError(error);
  }
}

// Adiciona ao export default no final do ficheiro:
export default {
  // ...existing exports...
  getIndicatorOperators,  // ? ADICIONA AQUI
};
```

---

### **2. Criar Hook React para Operators**

Cria novo ficheiro: `webapp/src/hooks/useIndicatorOperators.ts`

```typescript
import { useQuery } from '@tanstack/react-query';
import { getIndicatorOperators, type IndicatorOperatorsInfo } from '@/lib/api-lab';

export function useIndicatorOperators(indicatorId: string | null) {
  return useQuery<IndicatorOperatorsInfo | null>({
    queryKey: ['indicator-operators', indicatorId],
    queryFn: () => indicatorId ? getIndicatorOperators(indicatorId) : Promise.resolve(null),
    enabled: !!indicatorId,
    staleTime: 5 * 60 * 1000, // Cache por 5 minutos
  });
}
```

---

### **3. Atualizar `StrategyBuilder.tsx`**

Substitui a parte do **Operator Select** por:

```tsx
import { useIndicatorOperators } from '@/hooks/useIndicatorOperators';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { HelpCircle } from 'lucide-react';

// Dentro do componente StrategyBuilder:

const renderConditionsList = (side: 'long' | 'short', type: 'entry_all' | 'entry_any') => {
    const conditions = value[side][type];
    
    return (
   <Table>
       <TableBody>
    {conditions.map((condition, index) => {
       // Hook para buscar operadores recomendados
       const { data: operatorsInfo } = useIndicatorOperators(condition.indicator);
   
       return (
      <TableRow key={index}>
                 {/* ... Indicator Select ... */}
  
             {/* OPERATOR SELECT - DYNAMIC */}
 <TableCell>
          <div className="flex items-center gap-2">
      <Select
 value={condition.op}
     onValueChange={(v) => updateCondition(side, type, index, { op: v })}
   >
              <SelectTrigger className="w-[150px]">
         <SelectValue />
      </SelectTrigger>
    <SelectContent>
              {operatorsInfo ? (
        // Use recommended operators if available
 <>
         <SelectItem value="group-recommended" disabled className="font-semibold text-xs">
              RECOMMENDED
</SelectItem>
       {operatorsInfo.recommended_operators.map((op) => (
  <SelectItem key={op} value={op}>
         {formatOperator(op)}
             </SelectItem>
  ))}
          <SelectItem value="group-other" disabled className="font-semibold text-xs mt-2">
     OTHER
       </SelectItem>
  {getAllOperators()
  .filter(op => !operatorsInfo.recommended_operators.includes(op))
        .map((op) => (
               <SelectItem key={op} value={op}>
             {formatOperator(op)}
     </SelectItem>
       ))}
         </>
) : (
           // Fallback to all operators
  getAllOperators().map((op) => (
      <SelectItem key={op} value={op}>
          {formatOperator(op)}
  </SelectItem>
           ))
          )}
   </SelectContent>
      </Select>
  
            {/* HELP ICON - Shows usage hint */}
      {operatorsInfo && operatorsInfo.usage_hint && (
          <TooltipProvider>
         <Tooltip>
          <TooltipTrigger>
             <HelpCircle className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
          <TooltipContent className="max-w-xs">
            <p className="text-xs">{operatorsInfo.usage_hint}</p>
       
       {/* Show typical levels if available */}
     {Object.keys(operatorsInfo.typical_levels).length > 0 && (
    <div className="mt-2 space-y-1">
             <p className="font-semibold text-xs">Typical Levels:</p>
        {Object.entries(operatorsInfo.typical_levels).map(([name, value]) => (
          <p key={name} className="text-xs">
           • {name}: {value}
     </p>
   ))}
       </div>
    )}
      </TooltipContent>
           </Tooltip>
      </TooltipProvider>
           )}
   </div>
     </TableCell>
   
    {/* ... Rest of the row ... */}
          </TableRow>
        );
     })}
    </TableBody>
        </Table>
    );
};

// Helper functions:
function formatOperator(op: string): string {
    const formats: Record<string, string> = {
        'crosses_above': '? Crosses Above',
   'crosses_below': '? Crosses Below',
        '>': '> Greater Than',
 '<': '< Less Than',
        '>=': '? Greater or Equal',
        '<=': '? Less or Equal',
    '==': '= Equal',
        'between': '? Between',
    };
    return formats[op] || op;
}

function getAllOperators(): string[] {
  return ['>', '<', '>=', '<=', '==', 'crosses_above', 'crosses_below', 'between'];
}
```

---

## ?? **EXEMPLOS POR INDICADOR**

### **RSI (Oscillator)**
```
Recommended: crosses_above, crosses_below, >, <, between
Typical: Oversold=30, Overbought=70
Use: Crossovers for entries, thresholds for filters
```

### **Williams %R (Inverted Oscillator)**
```
Recommended: crosses_above, crosses_below, >, <
Typical: Oversold=-80, Overbought=-20
Use: Inverted scale! -80 to -100 is oversold
```

### **EMA/SMA (Trend)**
```
Recommended: crosses_above, crosses_below, >, <
Use: Price crosses EMA for trend changes
```

### **SuperTrend (Trend)**
```
Recommended: crosses_above, crosses_below, >, <
Use: Price crosses SuperTrend line for reversal
```

### **MACD (Momentum)**
```
Recommended: crosses_above, crosses_below, >, <
Typical: Zero Line=0
Use: MACD crosses signal for momentum change
```

### **ADX (Strength)**
```
Recommended: >, <, crosses_above
Typical: Weak=20, Strong=25, Very Strong=40
Use: Filter only - trade when ADX > 25
```

### **ATR (Volatility)**
```
Recommended: >, <, crosses_above
Use: For position sizing, not entry signals
```

---

## ? **TESTING**

### **1. Test Backend:**
```bash
curl http://localhost:8000/api/lab/indicators/rsi/operators
```

### **2. Test Frontend:**
```typescript
// In browser console:
import { getIndicatorOperators } from '@/lib/api-lab';
const ops = await getIndicatorOperators('rsi');
console.log(ops);
```

---

## ?? **UI IMPROVEMENTS**

### **Visual Enhancements:**

1. **Category Badge** - Show indicator category:
   ```tsx
   <Badge variant={getCategoryVariant(operatorsInfo.category)}>
 {operatorsInfo.category}
   </Badge>
   ```

2. **Range Indicator** - For bounded indicators:
   ```tsx
   {operatorsInfo.range.bounded && (
       <span className="text-xs text-muted-foreground">
 Range: {operatorsInfo.range.min} - {operatorsInfo.range.max}
       </span>
   )}
   ```

3. **Suggested Values** - Auto-fill typical levels:
   ```tsx
   <div className="flex gap-2">
       {Object.entries(operatorsInfo.typical_levels).map(([name, value]) => (
           <Button
       key={name}
    size="sm"
    variant="outline"
             onClick={() => updateCondition(side, type, index, { rhs: value })}
           >
   {name}: {value}
   </Button>
       ))}
   </div>
   ```

---

## ?? **NEXT STEPS**

1. ? Implementar frontend hook (`useIndicatorOperators`)
2. ? Atualizar `StrategyBuilder.tsx` com Select dinâmico
3. ? Adicionar tooltips com sugestões
4. ? Criar preset buttons para níveis típicos (oversold/overbought)
5. ? Adicionar visual feedback por categoria (cores)

---

## ?? **DOCUMENTATION**

Cada indicador agora inclui:
- ? **Category** (oscillator/trend/momentum/volatility/volume/strength)
- ? **Range** (bounded 0-100, unbounded, min/max)
- ? **Recommended Operators** (contextualized to indicator type)
- ? **Typical Levels** (oversold/overbought/neutral)
- ? **Usage Hint** (best practices for each indicator)

**Isto facilita IMENSO a vida do utilizador!** ??

---

**Implementado por:** GitHub Copilot  
**Data:** 2025-01-XX  
**Status:** ? Backend Ready | ? Frontend Pending
