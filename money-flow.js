/**
 * Nexus Protocol Money Flow Calculator
 * Advanced revenue analysis and ROI calculations
 */

// Revenue stream configurations with realistic APY ranges
const REVENUE_STREAMS = {
    dividends: {
        name: "Dividend Distributions",
        minAPY: 0.05,
        maxAPY: 0.20,
        risk: "low",
        passive: true
    },
    gameToEarn: {
        name: "Game-to-Earn Rewards",
        minAPY: 0.50,
        maxAPY: 3.00,
        risk: "low",
        passive: false
    },
    nftStaking: {
        name: "NFT Staking",
        minAPY: 0.15,
        maxAPY: 0.40,
        risk: "low",
        passive: true
    },
    liquidityProvision: {
        name: "Liquidity Provision",
        minAPY: 0.30,
        maxAPY: 1.20,
        risk: "medium",
        passive: false
    },
    reflectionFees: {
        name: "Reflection Fees",
        minAPY: 0.08,
        maxAPY: 0.15,
        risk: "low",
        passive: true
    },
    buybackBurn: {
        name: "Buyback & Burn",
        minAPY: 0.10,
        maxAPY: 0.25,
        risk: "low",
        passive: true
    },
    mcpGroups: {
        name: "MCP Group Profits",
        minAPY: 0.20,
        maxAPY: 1.00,
        risk: "low",
        passive: false
    },
    arbitrage: {
        name: "Arbitrage Trading",
        minAPY: 1.00,
        maxAPY: 5.00,
        risk: "high",
        passive: false
    },
    governance: {
        name: "Governance Rewards",
        minAPY: 0.05,
        maxAPY: 0.15,
        risk: "low",
        passive: true
    },
    lending: {
        name: "Lending & Borrowing",
        minAPY: 0.08,
        maxAPY: 0.35,
        risk: "medium",
        passive: true
    }
};

// Strategy configurations
const STRATEGIES = {
    conservative: {
        name: "Conservative",
        allocation: {
            dividends: 0.30,
            reflectionFees: 0.25,
            nftStaking: 0.20,
            buybackBurn: 0.15,
            governance: 0.10
        },
        multiplier: 0.7 // More conservative estimates
    },
    balanced: {
        name: "Balanced",
        allocation: {
            dividends: 0.20,
            gameToEarn: 0.15,
            nftStaking: 0.15,
            liquidityProvision: 0.15,
            reflectionFees: 0.15,
            mcpGroups: 0.10,
            governance: 0.10
        },
        multiplier: 1.0 // Standard estimates
    },
    aggressive: {
        name: "Aggressive",
        allocation: {
            liquidityProvision: 0.25,
            arbitrage: 0.20,
            gameToEarn: 0.20,
            mcpGroups: 0.15,
            lending: 0.10,
            reflectionFees: 0.10
        },
        multiplier: 1.3 // Higher risk, higher reward
    },
    expert: {
        name: "Expert",
        allocation: {
            arbitrage: 0.25,
            liquidityProvision: 0.20,
            gameToEarn: 0.15,
            lending: 0.15,
            mcpGroups: 0.10,
            nftStaking: 0.10,
            governance: 0.05
        },
        multiplier: 1.5 // Maximum potential with expert execution
    }
};

// Timeframe multipliers
const TIMEFRAMES = {
    daily: { days: 1, label: "Daily" },
    weekly: { days: 7, label: "Weekly" },
    monthly: { days: 30, label: "Monthly" },
    yearly: { days: 365, label: "Yearly" }
};

const TESTNET_CHAINS = new Set([
    "sepolia",
    "goerli",
    "holesky",
    "localhost",
    "hardhat",
    "anvil"
]);

const STABLE_SYMBOLS = new Set([
    "USDC",
    "USDT",
    "DAI",
    "USDE",
    "USDS",
    "PYUSD",
    "EURC",
    "XDAI"
]);

const COINBASE_DESTINATION_CHAINS = new Set([
    "ethereum",
    "base"
]);

function formatChainLabel(chain) {
    const value = String(chain ?? "").trim();
    if (!value) return "Unknown";
    if (value.toLowerCase() === "base") return "Base";
    if (value.toLowerCase() === "ethereum") return "Ethereum";
    return value.charAt(0).toUpperCase() + value.slice(1);
}

function determineAssetType(asset) {
    if (asset && String(asset.asset_type || "").trim()) {
        return String(asset.asset_type).toLowerCase();
    }
    if (asset && asset.token_standard) {
        return "collectible";
    }
    return "balance";
}

function classifySettlementRail(asset) {
    const chain = String(asset.chain || "").toLowerCase();
    const assetType = determineAssetType(asset);
    const chainLabel = formatChainLabel(chain);
    const supportedChain = COINBASE_DESTINATION_CHAINS.has(chain);

    if (assetType === "collectible") {
        return {
            network: chainLabel,
            destination: chain === "base" ? "Base wallet review" : "Manual NFT review",
            supportsDirectTransfer: false,
            reason: supportedChain
                ? `Collectibles on ${chainLabel} require manual Coinbase or wallet support checks before transfer.`
                : `Collectibles on ${chainLabel} require manual bridge and destination review before transfer.`
        };
    }

    if (chain === "base") {
        return {
            network: "Base",
            destination: "Coinbase Base deposit",
            supportsDirectTransfer: true,
            reason: "Use a Base-compatible Coinbase deposit address for direct routing."
        };
    }

    if (chain === "ethereum") {
        return {
            network: "Ethereum",
            destination: "Coinbase Ethereum deposit",
            supportsDirectTransfer: true,
            reason: "Use an Ethereum-compatible Coinbase deposit address for direct routing."
        };
    }

    return {
        network: chainLabel,
        destination: "Manual bridge review",
        supportsDirectTransfer: false,
        reason: `Verify bridge and destination support before sending funds from ${chainLabel}.`
    };
}

function parseDecimalAmount(amount, decimals) {
    const raw = String(amount ?? "0").trim();
    const precision = Number.isFinite(Number(decimals)) ? Math.max(0, Number(decimals)) : 0;
    if (!/^\d+$/.test(raw)) {
        return Number.NaN;
    }
    if (precision === 0) {
        return Number(raw);
    }
    const padded = raw.padStart(precision + 1, "0");
    const whole = padded.slice(0, -precision) || "0";
    const fraction = padded.slice(-precision).replace(/0+$/, "");
    return Number(fraction ? `${whole}.${fraction}` : whole);
}

function formatUsd(value) {
    const amount = Number(value);
    if (!Number.isFinite(amount)) {
        return "—";
    }
    return new Intl.NumberFormat("en-US", {
        style: "currency",
        currency: "USD",
        maximumFractionDigits: amount >= 1000 ? 0 : 2
    }).format(amount);
}

function classifyOffRamp(balance) {
    const chain = String(balance.chain || "").toLowerCase();
    const symbol = String(balance.symbol || "").toUpperCase();
    const valueUsd = Number(balance.value_usd);
    const poolSize = Number(balance.pool_size);
    const settlement = classifySettlementRail(balance);

    if (String(balance.asset_type || "").toLowerCase() === "collectible" || balance.token_standard) {
        return {
            status: balance.is_spam ? "blocked" : "review",
            label: balance.is_spam ? "Spam / ignore" : "Collectible review",
            reason: balance.is_spam
                ? "Spam collectibles should be ignored and never routed."
                : "Collectibles are excluded from fiat routing and need manual Coinbase/Base transfer review.",
            settlement
        };
    }

    if (TESTNET_CHAINS.has(chain)) {
        return {
            status: "blocked",
            label: "Testnet only",
            reason: "Testnet assets cannot be redeemed for fiat.",
            settlement
        };
    }
    if (!Number.isFinite(valueUsd) || valueUsd <= 0) {
        return {
            status: "review",
            label: "Unpriced",
            reason: "No USD valuation is available yet.",
            settlement
        };
    }
    if (balance.low_liquidity) {
        return {
            status: "review",
            label: "Low liquidity",
            reason: "Swap impact may be too high for a clean off-ramp.",
            settlement
        };
    }
    if (symbol === "ETH" || symbol === "WETH" || STABLE_SYMBOLS.has(symbol)) {
        return {
            status: "ready",
            label: "Off-ramp ready",
            reason: "Asset is already a common swap or withdrawal asset.",
            settlement
        };
    }
    if (Number.isFinite(poolSize) && poolSize >= 100000) {
        return {
            status: "swap",
            label: "Swap first",
            reason: "Swap into a stablecoin or native asset before off-ramping.",
            settlement
        };
    }
    return {
        status: "review",
        label: "Manual review",
        reason: "Verify liquidity and routing before attempting fiat conversion.",
        settlement
    };
}

function summarizeImportedBalances(balances) {
    const summary = {
        totalValueUsd: 0,
        pricedAssetCount: 0,
        unpricedAssetCount: 0,
        lowLiquidityCount: 0,
        lowLiquidityValueUsd: 0,
        readyValueUsd: 0,
        swapValueUsd: 0,
        reviewValueUsd: 0,
        blockedValueUsd: 0,
        nativeAssetCount: 0,
        coinbaseReadyCount: 0,
        baseReadyCount: 0,
        chains: {}
    };

    (balances || []).forEach(balance => {
        const valueUsd = Number(balance.value_usd);
        const priced = Number.isFinite(valueUsd) && valueUsd > 0;
        const chain = String(balance.chain || "unknown").toLowerCase();
        const offRamp = classifyOffRamp(balance);

        if (!summary.chains[chain]) {
            summary.chains[chain] = { count: 0, valueUsd: 0 };
        }
        summary.chains[chain].count += 1;

        if (String(balance.address || "").toLowerCase() === "native") {
            summary.nativeAssetCount += 1;
        }
        if (priced && offRamp.status === "ready" && offRamp.settlement && offRamp.settlement.supportsDirectTransfer) {
            summary.coinbaseReadyCount += 1;
            if (offRamp.settlement.network === "Base") {
                summary.baseReadyCount += 1;
            }
        }

        if (!priced) {
            summary.unpricedAssetCount += 1;
            return;
        }

        summary.pricedAssetCount += 1;
        summary.totalValueUsd += valueUsd;
        summary.chains[chain].valueUsd += valueUsd;

        if (balance.low_liquidity) {
            summary.lowLiquidityCount += 1;
            summary.lowLiquidityValueUsd += valueUsd;
        }

        if (offRamp.status === "ready") {
            summary.readyValueUsd += valueUsd;
        } else if (offRamp.status === "swap") {
            summary.swapValueUsd += valueUsd;
        } else if (offRamp.status === "blocked") {
            summary.blockedValueUsd += valueUsd;
        } else {
            summary.reviewValueUsd += valueUsd;
        }
    });

    return summary;
}

/**
 * Calculate returns based on investment, strategy, and timeframe
 */
function calculateReturns() {
    const investment = parseFloat(document.getElementById('investment').value) || 0;
    const timeframe = document.getElementById('timeframe').value;
    const strategyType = document.getElementById('strategy').value;

    if (investment <= 0) {
        alert('Please enter a valid investment amount');
        return;
    }

    const strategy = STRATEGIES[strategyType];
    const timeConfig = TIMEFRAMES[timeframe];
    
    let totalReturn = 0;
    let passiveReturn = 0;
    
    // Calculate returns from each allocated stream
    for (const [streamKey, allocation] of Object.entries(strategy.allocation)) {
        const stream = REVENUE_STREAMS[streamKey];
        if (!stream) continue;

        // Use average APY, adjusted by strategy multiplier
        const avgAPY = (stream.minAPY + stream.maxAPY) / 2;
        const adjustedAPY = avgAPY * strategy.multiplier;
        
        // Calculate return for this stream
        const streamInvestment = investment * allocation;
        const yearlyReturn = streamInvestment * adjustedAPY;
        const periodReturn = (yearlyReturn / 365) * timeConfig.days;
        
        totalReturn += periodReturn;
        
        if (stream.passive) {
            passiveReturn += periodReturn;
        }
    }

    // Calculate metrics
    const roi = (totalReturn / investment) * 100;
    const annualizedReturn = (totalReturn / timeConfig.days) * 365;
    const apy = (annualizedReturn / investment) * 100;

    // Display results
    document.getElementById('results').style.display = 'grid';
    document.getElementById('total-return').textContent = formatCurrency(totalReturn);
    document.getElementById('roi').textContent = roi.toFixed(2) + '%';
    document.getElementById('apy').textContent = apy.toFixed(2) + '%';
    document.getElementById('passive').textContent = formatCurrency(passiveReturn);

    // Add success animation
    const resultsEl = document.getElementById('results');
    resultsEl.style.animation = 'none';
    setTimeout(() => {
        resultsEl.style.animation = 'fadeIn 0.5s ease-in';
    }, 10);
}

/**
 * Format number as currency
 */
function formatCurrency(amount) {
    if (amount >= 1000000) {
        return '$' + (amount / 1000000).toFixed(2) + 'M';
    } else if (amount >= 1000) {
        return '$' + (amount / 1000).toFixed(2) + 'K';
    } else {
        return '$' + amount.toFixed(2);
    }
}

/**
 * Calculate potential monthly income at different investment levels
 */
function calculateIncomeBreakdown(investment) {
    const results = {};
    
    for (const [strategyKey, strategy] of Object.entries(STRATEGIES)) {
        let monthlyIncome = 0;
        
        for (const [streamKey, allocation] of Object.entries(strategy.allocation)) {
            const stream = REVENUE_STREAMS[streamKey];
            if (!stream) continue;
            
            const avgAPY = (stream.minAPY + stream.maxAPY) / 2;
            const adjustedAPY = avgAPY * strategy.multiplier;
            const streamInvestment = investment * allocation;
            const yearlyReturn = streamInvestment * adjustedAPY;
            const monthlyReturn = yearlyReturn / 12;
            
            monthlyIncome += monthlyReturn;
        }
        
        results[strategyKey] = {
            monthly: monthlyIncome,
            yearly: monthlyIncome * 12,
            strategy: strategy.name
        };
    }
    
    return results;
}

/**
 * Calculate time to reach financial goals
 */
function calculateTimeToGoal(currentInvestment, monthlyContribution, targetIncome, strategy) {
    const strategyConfig = STRATEGIES[strategy];
    let months = 0;
    let investment = currentInvestment;
    const maxMonths = 120; // 10 years max
    
    while (months < maxMonths) {
        // Calculate monthly return
        let monthlyReturn = 0;
        
        for (const [streamKey, allocation] of Object.entries(strategyConfig.allocation)) {
            const stream = REVENUE_STREAMS[streamKey];
            if (!stream) continue;
            
            const avgAPY = (stream.minAPY + stream.maxAPY) / 2;
            const adjustedAPY = avgAPY * strategyConfig.multiplier;
            const streamInvestment = investment * allocation;
            const yearlyReturn = streamInvestment * adjustedAPY;
            monthlyReturn += yearlyReturn / 12;
        }
        
        // Check if we've reached the target
        if (monthlyReturn >= targetIncome) {
            return { months, investment, monthlyIncome: monthlyReturn };
        }
        
        // Add monthly contribution and returns
        investment += monthlyContribution + monthlyReturn;
        months++;
    }
    
    return { months: maxMonths, investment, monthlyIncome: 0, reachedGoal: false };
}

/**
 * Generate expert recommendations based on investment size
 */
function getExpertRecommendations(investment) {
    const recommendations = [];
    
    if (investment < 1000) {
        recommendations.push({
            title: "Start with Game-to-Earn",
            description: "Focus on playing games to accumulate NGTT tokens with zero additional investment. Aim for 100+ skill points for maximum multipliers.",
            priority: "high"
        });
        recommendations.push({
            title: "Compound Everything",
            description: "Reinvest 100% of earnings for the first 6 months to build your position faster.",
            priority: "high"
        });
    } else if (investment < 10000) {
        recommendations.push({
            title: "Balanced Passive Strategy",
            description: "Split between dividends (40%), reflections (30%), and NFT staking (30%) for steady passive income.",
            priority: "high"
        });
        recommendations.push({
            title: "Join MCP Groups",
            description: "Participate in profit pool distributions to boost your returns by 20-50%.",
            priority: "medium"
        });
    } else if (investment < 50000) {
        recommendations.push({
            title: "Add Liquidity Provision",
            description: "Allocate 25% to Uniswap V3 concentrated liquidity for 50-100% APY on that portion.",
            priority: "high"
        });
        recommendations.push({
            title: "Diversify Across Streams",
            description: "Use the Balanced or Aggressive strategy to maximize returns across 7+ revenue streams.",
            priority: "high"
        });
        recommendations.push({
            title: "Consider Governance",
            description: "Your holdings qualify you for Super Delegate status - apply for 3x governance rewards.",
            priority: "medium"
        });
    } else {
        recommendations.push({
            title: "Expert Strategy Stack",
            description: "Implement the Ultimate Hybrid Stack: Hold 40% for passive, 20% liquidity, 20% NFTs, 10% gaming, 10% arbitrage.",
            priority: "high"
        });
        recommendations.push({
            title: "Leverage Lending Protocols",
            description: "Use Aave to leverage your position 2-3x. Earn on collateral + borrowed funds for amplified returns.",
            priority: "high"
        });
        recommendations.push({
            title: "Automate Arbitrage",
            description: "Your capital qualifies for automated flash loan arbitrage. Expected 200-500% APY on allocated funds.",
            priority: "medium"
        });
        recommendations.push({
            title: "Whale Status Benefits",
            description: "You qualify for exclusive whale benefits. Contact DAO for treasury participation opportunities.",
            priority: "low"
        });
    }
    
    return recommendations;
}

/**
 * Format timeframe label
 */
function formatTimeframe(months) {
    if (months < 12) {
        return months + ' month' + (months !== 1 ? 's' : '');
    } else {
        const years = Math.floor(months / 12);
        const remainingMonths = months % 12;
        let result = years + ' year' + (years !== 1 ? 's' : '');
        if (remainingMonths > 0) {
            result += ' ' + remainingMonths + ' month' + (remainingMonths !== 1 ? 's' : '');
        }
        return result;
    }
}

// Add CSS animation for results
if (typeof document !== 'undefined' && document.head) {
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    `;
    document.head.appendChild(style);
}

// Auto-calculate on load if values are present
if (typeof window !== 'undefined') {
    window.addEventListener('DOMContentLoaded', () => {
        // Add event listeners for real-time updates
        const investment = document.getElementById('investment');
        const timeframe = document.getElementById('timeframe');
        const strategy = document.getElementById('strategy');

        if (investment && timeframe && strategy) {
            [investment, timeframe, strategy].forEach(el => {
                el.addEventListener('change', calculateReturns);
            });

            // Calculate initial results
            if (investment.value && parseFloat(investment.value) > 0) {
                calculateReturns();
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Fractal Compounding Model
// (MIT 15.401 / Wharton Crypto Finance — compound interest with reinvestment)
// ---------------------------------------------------------------------------

/**
 * Computes compound growth using the continuous-compounding formula:
 *   FV = PV × (1 + r)^n
 * where r is the per-period rate and n is the number of periods.
 *
 * @param {number} principal    Starting capital (any currency unit).
 * @param {number} ratePerPeriod Per-period yield rate as a decimal (e.g. 0.01 = 1%).
 * @param {number} periods      Number of compounding periods.
 * @param {number} [reinvestBps=10000] Fraction of each yield to reinvest, in basis points
 *                              (10 000 = 100% reinvest, 5 000 = 50% reinvest).
 * @returns {{ finalValue: number, totalYield: number, growthMultiple: number }}
 */
function fractalCompound(principal, ratePerPeriod, periods, reinvestBps) {
    const pv = Number(principal);
    const r = Number(ratePerPeriod);
    const n = Math.floor(Number(periods));
    const bps = Number.isFinite(reinvestBps) ? Math.min(Math.max(reinvestBps, 0), 10000) : 10000;
    const reinvestFraction = bps / 10000;

    if (!Number.isFinite(pv) || pv <= 0) return { finalValue: 0, totalYield: 0, growthMultiple: 1 };
    if (!Number.isFinite(r) || r < 0) return { finalValue: pv, totalYield: 0, growthMultiple: 1 };
    if (n <= 0) return { finalValue: pv, totalYield: 0, growthMultiple: 1 };

    let value = pv;
    for (let i = 0; i < n; i++) {
        const periodYield = value * r;
        value += periodYield * reinvestFraction;
    }

    return {
        finalValue: value,
        totalYield: value - pv,
        growthMultiple: value / pv,
    };
}

/**
 * Returns a full schedule of compounding values, one entry per period.
 * Useful for charting the fractal growth curve on the dashboard.
 *
 * @param {number} principal       Starting capital.
 * @param {number} ratePerPeriod   Per-period yield rate as a decimal.
 * @param {number} periods         Number of periods to project.
 * @param {number} [reinvestBps=10000] Reinvestment fraction in basis points.
 * @returns {Array<{ period: number, value: number, cumulativeYield: number }>}
 */
function fractalCompoundSchedule(principal, ratePerPeriod, periods, reinvestBps) {
    const pv = Number(principal);
    const r = Number(ratePerPeriod);
    const n = Math.floor(Number(periods));
    const bps = Number.isFinite(reinvestBps) ? Math.min(Math.max(reinvestBps, 0), 10000) : 10000;
    const reinvestFraction = bps / 10000;
    const schedule = [];

    if (!Number.isFinite(pv) || pv <= 0 || !Number.isFinite(r) || r < 0 || n <= 0) {
        return schedule;
    }

    let value = pv;
    for (let i = 1; i <= n; i++) {
        value += value * r * reinvestFraction;
        schedule.push({ period: i, value: Number(value.toFixed(8)), cumulativeYield: Number((value - pv).toFixed(8)) });
    }
    return schedule;
}

/**
 * Kelly Criterion: computes the optimal fraction of capital to invest per cycle.
 *   f* = (b × p - q) / b
 * where:
 *   b = net odds (profit per unit bet, e.g. 1 for even money)
 *   p = probability of winning
 *   q = probability of losing (1 - p)
 *
 * Capped at 1 (100%) and floored at 0 (do not invest when edge is negative).
 *
 * @param {number} winProbability  Probability of a winning outcome (0–1).
 * @param {number} netOdds         Net profit per unit invested if winning.
 * @returns {number} Optimal fraction of capital to invest (0–1).
 */
function kellyFraction(winProbability, netOdds) {
    const p = Number(winProbability);
    const b = Number(netOdds);
    if (!Number.isFinite(p) || p <= 0 || p >= 1) return 0;
    if (!Number.isFinite(b) || b <= 0) return 0;
    const q = 1 - p;
    const f = (b * p - q) / b;
    return Math.min(1, Math.max(0, f));
}

// Export functions for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        REVENUE_STREAMS,
        STRATEGIES,
        TIMEFRAMES,
        parseDecimalAmount,
        formatUsd,
        classifySettlementRail,
        classifyOffRamp,
        summarizeImportedBalances,
        calculateReturns,
        calculateIncomeBreakdown,
        calculateTimeToGoal,
        getExpertRecommendations,
        formatCurrency,
        formatTimeframe,
        fractalCompound,
        fractalCompoundSchedule,
        kellyFraction,
    };
}

if (typeof window !== 'undefined') {
    window.NexusMoneyFlow = {
        parseDecimalAmount,
        formatUsd,
        classifySettlementRail,
        classifyOffRamp,
        summarizeImportedBalances,
        formatCurrency,
        formatTimeframe,
        fractalCompound,
        fractalCompoundSchedule,
        kellyFraction,
    };
}
