const AGE_GROUPS = [
    {
        id: 1,
        name: 'Children (Ages 5-10)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'memory',
        games: [
            'Memory Match MCP',
            'Treasure Hunt Nodes',
            'Pattern Block Chain',
            'Color Code Quest',
            'Number Node Navigator',
            'Shape Shifter Protocol',
            'Animal Token Collector',
            'Adventure Map Builder',
            'Puzzle Token Master',
            'Story Chain Creator'
        ]
    },
    {
        id: 2,
        name: 'Tweens (Ages 11-13)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'trader',
        games: [
            'Strategy Node Wars',
            'Token Trading Academy',
            'VPN Quest Adventure',
            'Crypto Puzzle Challenge',
            'Network Builder Pro',
            'Smart Contract Basics',
            'Resource Management Game',
            'Team Node Battles',
            'Economic Simulator Lite',
            'Chain Reaction Strategy'
        ]
    },
    {
        id: 3,
        name: 'Teens (Ages 14-17)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'governance',
        games: [
            'Advanced Game Theory Wars',
            'DeFi Trading Simulator',
            'VPN Security Challenge',
            'NFT Creation Studio',
            'DAO Governance Sim',
            'Capital Allocation Strategy',
            'Blockchain Developer Quest',
            'Cryptocurrency Arbitrage',
            'Network Security Battle',
            'Smart Contract Programming'
        ]
    },
    {
        id: 4,
        name: 'Young Adults (Ages 18-25)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'trader',
        games: [
            'Professional Trading Platform',
            'Enterprise Node Management',
            'Advanced DeFi Strategies',
            'Institutional Capital Game',
            'Quantitative Trading Sim',
            'Venture Capital Simulator',
            'Global Markets Strategy',
            'Portfolio Optimization Game',
            'Risk Management Pro',
            'Algorithmic Trading Battle'
        ]
    },
    {
        id: 5,
        name: 'Adults (Ages 26-40)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'governance',
        games: [
            'Wealth Management Simulator',
            'Real Estate Token Trading',
            'Business Strategy Game',
            'Investment Portfolio Builder',
            'Corporate Finance Challenge',
            'Market Analysis Pro',
            'Retirement Planning Game',
            'Tax Optimization Strategy',
            'Asset Diversification Sim',
            'Executive Decision Maker'
        ]
    },
    {
        id: 6,
        name: 'Mature Adults (Ages 41-60)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'governance',
        games: [
            'Legacy Wealth Planning',
            'Passive Income Builder',
            'Estate Management Game',
            'Multi-Generation Strategy',
            'Conservative Portfolio Sim',
            'Trust Fund Manager',
            'Dividend Strategy Game',
            'Bond Market Navigator',
            'Insurance Optimization',
            'Retirement Income Planner'
        ]
    },
    {
        id: 7,
        name: 'Seniors (Ages 60+)',
        tokenAllocation: 10,
        developmentHours: 1,
        recommendedGame: 'memory',
        games: [
            'Simple Portfolio Manager',
            'Fixed Income Strategy',
            'Legacy Token Creator',
            'Simplified Trading Game',
            'Income Protection Sim',
            'Healthcare Finance Game',
            'Social Security Optimizer',
            'Estate Distribution Planner',
            'Memory Lane NFT Creator',
            'Grandchildren Fund Builder'
        ]
    }
];

const FEATURED_GAMES = {
    memory: {
        id: 'memory',
        name: 'Memory Match MCP',
        eyebrow: 'Fast browser play',
        description: 'Match protocol icons, build momentum, and clear the board in the fewest moves.'
    },
    trader: {
        id: 'trader',
        name: 'Token Trading Academy',
        eyebrow: 'Portfolio challenge',
        description: 'Manage cash, react to market swings, and finish six rounds with the best net worth.'
    },
    governance: {
        id: 'governance',
        name: 'DAO Governance Sprint',
        eyebrow: 'Decision game',
        description: 'Pick the strongest governance move in each scenario and stack your authority score.'
    }
};

const MEMORY_SYMBOLS = ['⬡', '🪙', '⚡', '🧠', '🌐', '🎮'];
const TRADER_PRICES = [12, 18, 10, 22, 16, 24];
const GOVERNANCE_QUESTIONS = [
    {
        prompt: 'A wallet requests a high-value transaction without prior review. What should the DAO do first?',
        options: [
            {
                label: 'Execute immediately to keep momentum high.',
                correct: false,
                detail: 'Speed alone is risky; high-value actions need deliberate review.'
            },
            {
                label: 'Require proposal review, signer verification, and explicit approval.',
                correct: true,
                detail: 'Correct. Controlled review and approval protect governance and funds.'
            },
            {
                label: 'Ignore the request until the market improves.',
                correct: false,
                detail: 'Waiting without process is not a governance plan.'
            }
        ]
    },
    {
        prompt: 'Treasury yield is strong, but one strategy adds much higher risk. What is the healthiest move?',
        options: [
            {
                label: 'Concentrate all capital in the highest APY option.',
                correct: false,
                detail: 'Over-concentration creates avoidable downside.'
            },
            {
                label: 'Diversify, cap exposure, and monitor risk-adjusted returns.',
                correct: true,
                detail: 'Correct. Balanced allocation keeps upside while protecting the treasury.'
            },
            {
                label: 'Stop all yield activity permanently.',
                correct: false,
                detail: 'That removes opportunity rather than managing risk.'
            }
        ]
    },
    {
        prompt: 'Community members want a new game feature. Which rollout strategy is strongest?',
        options: [
            {
                label: 'Ship it to every user instantly with no feedback loop.',
                correct: false,
                detail: 'A full rollout without feedback increases the chance of broad issues.'
            },
            {
                label: 'Prototype, gather player feedback, and iterate before expanding.',
                correct: true,
                detail: 'Correct. A staged rollout improves quality and trust.'
            },
            {
                label: 'Reject all changes to keep the interface static forever.',
                correct: false,
                detail: 'A protocol still needs measured evolution.'
            }
        ]
    },
    {
        prompt: 'An on-chain action affects multiple stakeholders. What communication pattern works best?',
        options: [
            {
                label: 'Publish the decision path, timeline, and expected impact clearly.',
                correct: true,
                detail: 'Correct. Transparency supports alignment and informed participation.'
            },
            {
                label: 'Share only the final result and hide the reasoning.',
                correct: false,
                detail: 'Missing context weakens trust.'
            },
            {
                label: 'Let rumors explain the decision instead of official updates.',
                correct: false,
                detail: 'Unofficial channels should not replace governance communication.'
            }
        ]
    }
];

const state = {
    activeGroupId: AGE_GROUPS[0].id,
    activeGameId: 'memory',
    memory: createMemoryState(),
    trader: createTraderState(),
    governance: createGovernanceState()
};

const elements = {};

document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
    cacheElements();
    bindEvents();
    renderAgeGroups();
    renderGroupDetails();
    renderCatalog();
    setActiveGame(state.activeGameId);
}

function cacheElements() {
    elements.ageGroupButtons = document.getElementById('age-group-buttons');
    elements.groupName = document.getElementById('group-name');
    elements.groupMeta = document.getElementById('group-meta');
    elements.groupHighlights = document.getElementById('group-highlights');
    elements.recommendedLaunch = document.getElementById('recommended-launch');
    elements.catalogList = document.getElementById('catalog-list');
    elements.gameTabs = document.getElementById('game-tabs');
    elements.gamePanels = Array.from(document.querySelectorAll('[data-game-panel]'));
    elements.memoryBoard = document.getElementById('memory-board');
    elements.memoryStatus = document.getElementById('memory-status');
    elements.memoryFeedback = document.getElementById('memory-feedback');
    elements.traderRound = document.getElementById('trader-round');
    elements.traderPrice = document.getElementById('trader-price');
    elements.traderCash = document.getElementById('trader-cash');
    elements.traderTokens = document.getElementById('trader-tokens');
    elements.traderWorth = document.getElementById('trader-worth');
    elements.traderFeedback = document.getElementById('trader-feedback');
    elements.traderHistory = document.getElementById('trader-history');
    elements.traderActions = Array.from(document.querySelectorAll('[data-trader-action]'));
    elements.governancePrompt = document.getElementById('governance-prompt');
    elements.governanceOptions = document.getElementById('governance-options');
    elements.governanceProgress = document.getElementById('governance-progress');
    elements.governanceScore = document.getElementById('governance-score');
    elements.governanceFeedback = document.getElementById('governance-feedback');
    elements.governanceNext = document.getElementById('governance-next');
}

function bindEvents() {
    elements.gameTabs.addEventListener('click', (event) => {
        const button = event.target.closest('[data-game-target]');
        if (!button) {
            return;
        }
        setActiveGame(button.dataset.gameTarget);
    });

    elements.recommendedLaunch.addEventListener('click', () => {
        const activeGroup = getActiveGroup();
        setActiveGame(activeGroup.recommendedGame);
        document.getElementById('arcade').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    document.getElementById('memory-reset').addEventListener('click', resetMemoryGame);
    document.getElementById('trader-reset').addEventListener('click', resetTraderGame);
    document.getElementById('governance-reset').addEventListener('click', resetGovernanceGame);
    elements.governanceNext.addEventListener('click', advanceGovernanceQuestion);

    elements.traderActions.forEach((button) => {
        button.addEventListener('click', () => handleTraderAction(button.dataset.traderAction));
    });
}

function getActiveGroup() {
    return AGE_GROUPS.find((group) => group.id === state.activeGroupId) || AGE_GROUPS[0];
}

function renderAgeGroups() {
    elements.ageGroupButtons.replaceChildren();

    AGE_GROUPS.forEach((group) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'chip-button';
        if (group.id === state.activeGroupId) {
            button.classList.add('is-active');
        }
        button.textContent = group.name;
        button.dataset.groupId = String(group.id);
        button.addEventListener('click', () => {
            state.activeGroupId = group.id;
            renderAgeGroups();
            renderGroupDetails();
            renderCatalog();
        });
        elements.ageGroupButtons.appendChild(button);
    });
}

function renderGroupDetails() {
    const group = getActiveGroup();
    const demo = FEATURED_GAMES[group.recommendedGame];

    elements.groupName.textContent = group.name;
    const hourLabel = group.developmentHours === 1 ? 'hour' : 'hours';
    elements.groupMeta.textContent = `${group.games.length} game concepts • ${group.tokenAllocation} tokens • ${group.developmentHours} dev ${hourLabel}`;
    elements.recommendedLaunch.textContent = `Launch ${demo.name}`;

    elements.groupHighlights.replaceChildren();
    group.games.slice(0, 4).forEach((gameName) => {
        const item = document.createElement('li');
        item.textContent = gameName;
        elements.groupHighlights.appendChild(item);
    });
}

function renderCatalog() {
    const group = getActiveGroup();
    elements.catalogList.replaceChildren();

    group.games.forEach((gameName, index) => {
        const item = document.createElement('li');
        item.className = 'catalog-item';

        const count = document.createElement('span');
        count.className = 'catalog-index';
        count.textContent = String(index + 1).padStart(2, '0');

        const title = document.createElement('span');
        title.className = 'catalog-name';
        title.textContent = gameName;

        item.append(count, title);
        elements.catalogList.appendChild(item);
    });
}

function setActiveGame(gameId) {
    state.activeGameId = gameId;

    Array.from(elements.gameTabs.querySelectorAll('[data-game-target]')).forEach((button) => {
        button.classList.toggle('is-active', button.dataset.gameTarget === gameId);
    });

    elements.gamePanels.forEach((panel) => {
        panel.hidden = panel.dataset.gamePanel !== gameId;
    });

    if (gameId === 'memory') {
        renderMemoryGame();
    } else if (gameId === 'trader') {
        renderTraderGame();
    } else if (gameId === 'governance') {
        renderGovernanceGame();
    }
}

function createMemoryState() {
    const deck = shuffle([...MEMORY_SYMBOLS, ...MEMORY_SYMBOLS]).map((symbol, index) => ({
        id: index,
        symbol,
        matched: false
    }));

    return {
        deck,
        flipped: [],
        moves: 0,
        lockBoard: false,
        message: 'Match every pair to complete the MCP memory board.'
    };
}

function resetMemoryGame() {
    state.memory = createMemoryState();
    renderMemoryGame();
}

function renderMemoryGame() {
    const matches = state.memory.deck.filter((card) => card.matched).length / 2;
    elements.memoryStatus.textContent = `Matches ${matches}/${MEMORY_SYMBOLS.length} • Moves ${state.memory.moves}`;
    elements.memoryFeedback.textContent = state.memory.message;
    elements.memoryBoard.replaceChildren();

    state.memory.deck.forEach((card, index) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'memory-card';
        const isVisible = card.matched || state.memory.flipped.includes(index);
        if (isVisible) {
            button.classList.add('is-visible');
        }
        if (card.matched) {
            button.classList.add('is-matched');
            button.disabled = true;
        }
        button.textContent = isVisible ? card.symbol : '?';
        button.setAttribute('aria-label', isVisible ? `Card ${card.symbol}` : 'Hidden card');
        button.addEventListener('click', () => handleMemoryCard(index));
        elements.memoryBoard.appendChild(button);
    });
}

function handleMemoryCard(index) {
    const card = state.memory.deck[index];
    if (!card || card.matched || state.memory.lockBoard || state.memory.flipped.includes(index)) {
        return;
    }

    state.memory.flipped.push(index);
    renderMemoryGame();

    if (state.memory.flipped.length < 2) {
        state.memory.message = 'Find the matching pair.';
        renderMemoryGame();
        return;
    }

    state.memory.moves += 1;
    const [firstIndex, secondIndex] = state.memory.flipped;
    const firstCard = state.memory.deck[firstIndex];
    const secondCard = state.memory.deck[secondIndex];

    if (firstCard.symbol === secondCard.symbol) {
        firstCard.matched = true;
        secondCard.matched = true;
        state.memory.flipped = [];
        const cleared = state.memory.deck.every((currentCard) => currentCard.matched);
        state.memory.message = cleared
            ? `Board cleared in ${state.memory.moves} moves. DOMINANT memory run.`
            : `Match locked: ${firstCard.symbol} ${secondCard.symbol}`;
        renderMemoryGame();
        return;
    }

    state.memory.lockBoard = true;
    state.memory.message = 'No match. Re-center and try the next pair.';
    renderMemoryGame();

    window.setTimeout(() => {
        state.memory.flipped = [];
        state.memory.lockBoard = false;
        renderMemoryGame();
    }, 700);
}

function createTraderState() {
    return {
        round: 0,
        cash: 120,
        tokens: 0,
        history: ['Starting treasury loaded with 120 credits.'],
        feedback: 'Round 1 is live. Choose buy, hold, or sell.',
        completed: false
    };
}

function resetTraderGame() {
    state.trader = createTraderState();
    renderTraderGame();
}

function getTraderPriceForRound(round = state.trader.round) {
    const safeRound = Math.max(0, Math.min(round, TRADER_PRICES.length - 1));
    return TRADER_PRICES[safeRound];
}

function renderTraderGame() {
    const price = getTraderPriceForRound();
    const netWorth = state.trader.cash + state.trader.tokens * price;

    elements.traderRound.textContent = `Round ${Math.min(state.trader.round + 1, TRADER_PRICES.length)} of ${TRADER_PRICES.length}`;
    elements.traderPrice.textContent = `${price} credits`;
    elements.traderCash.textContent = `${state.trader.cash} credits`;
    elements.traderTokens.textContent = `${state.trader.tokens} tokens`;
    elements.traderWorth.textContent = `${netWorth} credits`;
    elements.traderFeedback.textContent = state.trader.feedback;
    elements.traderHistory.replaceChildren();

    state.trader.history.forEach((entry) => {
        const item = document.createElement('li');
        item.textContent = entry;
        elements.traderHistory.appendChild(item);
    });

    elements.traderActions.forEach((button) => {
        button.disabled = state.trader.completed;
    });
}

function handleTraderAction(action) {
    if (state.trader.completed) {
        return;
    }

    const price = getTraderPriceForRound();
    let message = '';

    if (action === 'buy') {
        if (state.trader.cash >= price) {
            state.trader.cash -= price;
            state.trader.tokens += 1;
            message = `Bought 1 token at ${price} credits.`;
        } else {
            message = `Not enough cash to buy at ${price} credits. Hold your treasury.`;
        }
    } else if (action === 'sell') {
        if (state.trader.tokens > 0) {
            state.trader.tokens -= 1;
            state.trader.cash += price;
            message = `Sold 1 token at ${price} credits.`;
        } else {
            message = 'No tokens to sell. Build a position first.';
        }
    } else {
        message = `Held your position while the market printed ${price} credits.`;
    }

    state.trader.history.unshift(`Round ${state.trader.round + 1}: ${message}`);
    state.trader.round += 1;

    if (state.trader.round >= TRADER_PRICES.length) {
        const finalWorth = state.trader.cash + state.trader.tokens * TRADER_PRICES[TRADER_PRICES.length - 1];
        state.trader.completed = true;
        state.trader.feedback = evaluateTraderRun(finalWorth);
    } else {
        state.trader.feedback = `${message} Next price unlocked.`;
    }

    renderTraderGame();
}

function evaluateTraderRun(finalWorth) {
    if (finalWorth >= 150) {
        return `Finished with ${finalWorth} credits. DOMINANT trading run.`;
    }
    if (finalWorth >= 120) {
        return `Finished with ${finalWorth} credits. Stable treasury growth achieved.`;
    }
    return `Finished with ${finalWorth} credits. Reset and refine your trade timing.`;
}

function createGovernanceState() {
    return {
        questionIndex: 0,
        score: 0,
        answered: false,
        feedback: 'Answer each prompt with the strongest DAO move.',
        completed: false
    };
}

function resetGovernanceGame() {
    state.governance = createGovernanceState();
    renderGovernanceGame();
}

function renderGovernanceGame() {
    const currentQuestion = GOVERNANCE_QUESTIONS[state.governance.questionIndex];
    elements.governanceScore.textContent = `${state.governance.score}/${GOVERNANCE_QUESTIONS.length}`;
    elements.governanceFeedback.textContent = state.governance.feedback;
    elements.governanceNext.hidden = !state.governance.answered || state.governance.completed;

    if (!currentQuestion) {
        elements.governancePrompt.textContent = 'Governance sprint complete.';
        elements.governanceProgress.textContent = 'All scenarios cleared';
        elements.governanceOptions.replaceChildren();
        return;
    }

    elements.governancePrompt.textContent = currentQuestion.prompt;
    elements.governanceProgress.textContent = `Scenario ${state.governance.questionIndex + 1} of ${GOVERNANCE_QUESTIONS.length}`;
    elements.governanceOptions.replaceChildren();

    currentQuestion.options.forEach((option) => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'option-button';
        button.textContent = option.label;
        button.disabled = state.governance.answered;
        button.addEventListener('click', () => submitGovernanceAnswer(option));
        elements.governanceOptions.appendChild(button);
    });
}

function submitGovernanceAnswer(option) {
    if (state.governance.answered || state.governance.completed) {
        return;
    }

    state.governance.answered = true;
    if (option.correct) {
        state.governance.score += 1;
    }
    state.governance.feedback = option.detail;
    renderGovernanceGame();
}

function advanceGovernanceQuestion() {
    if (state.governance.completed || !state.governance.answered) {
        return;
    }

    state.governance.questionIndex += 1;
    state.governance.answered = false;

    if (state.governance.questionIndex >= GOVERNANCE_QUESTIONS.length) {
        state.governance.completed = true;
        state.governance.feedback = `Sprint complete with ${state.governance.score}/${GOVERNANCE_QUESTIONS.length} strong decisions.`;
    } else {
        state.governance.feedback = 'Next scenario loaded.';
    }

    renderGovernanceGame();
}

function shuffle(items) {
    const copy = [...items];
    for (let index = copy.length - 1; index > 0; index -= 1) {
        const randomIndex = Math.floor(Math.random() * (index + 1));
        [copy[index], copy[randomIndex]] = [copy[randomIndex], copy[index]];
    }
    return copy;
}

window.NexusGames = {
    AGE_GROUPS,
    FEATURED_GAMES,
    initializeApp,
    resetMemoryGame,
    handleTraderAction,
    submitGovernanceAnswer
};
