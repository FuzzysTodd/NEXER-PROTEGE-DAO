/**
 * Expert Registry RESTful Service
 * ================================
 * A persistent registry for storing and retrieving experts/consultants
 * based on their expertise, PR consulting capabilities, or ideation skills.
 *
 * Endpoints:
 *   GET    /api/v1/experts                - List all experts (with optional filters)
 *   GET    /api/v1/experts/:id            - Get expert by ID
 *   POST   /api/v1/experts                - Register a new expert
 *   PUT    /api/v1/experts/:id            - Update an expert
 *   DELETE /api/v1/experts/:id            - Remove an expert
 *   GET    /api/v1/experts/search         - Search by expertise, role, or tags
 *   GET    /api/v1/experts/category/:cat  - Get experts by category (expertise/pr/ideation)
 *   POST   /api/v1/experts/:id/engage     - Log engagement with an expert
 *   GET    /api/v1/stats                  - Registry statistics
 *
 * Storage: JSON file at ./data/expert-registry.json
 */

const http = require("http");
const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const { URL } = require("url");
const crypto = require("crypto");

const PORT = Number(process.env.EXPERT_REGISTRY_PORT || 8790);
const ROOT = __dirname;
const DATA_DIR = path.join(ROOT, "data");
const REGISTRY_FILE = path.join(DATA_DIR, "expert-registry.json");
const PUBLIC_ORIGIN = process.env.EXPERT_REGISTRY_ORIGIN || "*";

// ─────────────────────────────────────────────────────────────────────────────
// Expert Categories
// ─────────────────────────────────────────────────────────────────────────────
const CATEGORIES = {
    EXPERTISE: "expertise",      // Domain experts to be called upon for knowledge
    PR_CONSULTANT: "pr",         // PR and communications consultants
    IDEATION: "ideation",        // Creative thinkers for new ideas
    GENERAL: "general"           // Multi-purpose consultants
};

// ─────────────────────────────────────────────────────────────────────────────
// Utility Functions
// ─────────────────────────────────────────────────────────────────────────────
function isoNow() {
    return new Date().toISOString();
}

function generateId() {
    return `exp_${Date.now().toString(36)}_${crypto.randomBytes(4).toString("hex")}`;
}

function safeJson(value) {
    return JSON.stringify(value, null, 2);
}

// ─────────────────────────────────────────────────────────────────────────────
// Data Storage
// ─────────────────────────────────────────────────────────────────────────────
function defaultRegistry() {
    return {
        version: "1.0.0",
        createdAt: isoNow(),
        updatedAt: isoNow(),
        experts: [],
        engagements: [],
        stats: {
            totalRegistered: 0,
            totalEngagements: 0,
            byCategory: {
                expertise: 0,
                pr: 0,
                ideation: 0,
                general: 0
            }
        }
    };
}

async function ensureDataDir() {
    try {
        await fsp.mkdir(DATA_DIR, { recursive: true });
    } catch (err) {
        if (err.code !== "EEXIST") throw err;
    }
}

async function loadRegistry() {
    try {
        await ensureDataDir();
        const raw = await fsp.readFile(REGISTRY_FILE, "utf8");
        const parsed = JSON.parse(raw);
        return {
            version: parsed.version || "1.0.0",
            createdAt: parsed.createdAt || isoNow(),
            updatedAt: parsed.updatedAt || isoNow(),
            experts: Array.isArray(parsed.experts) ? parsed.experts : [],
            engagements: Array.isArray(parsed.engagements) ? parsed.engagements : [],
            stats: parsed.stats || defaultRegistry().stats
        };
    } catch (err) {
        if (err.code === "ENOENT") {
            const registry = defaultRegistry();
            await saveRegistry(registry);
            return registry;
        }
        throw err;
    }
}

async function saveRegistry(registry) {
    await ensureDataDir();
    registry.updatedAt = isoNow();
    await fsp.writeFile(REGISTRY_FILE, safeJson(registry));
}

// ─────────────────────────────────────────────────────────────────────────────
// Expert Schema Validation
// ─────────────────────────────────────────────────────────────────────────────
function validateExpert(data) {
    const errors = [];
    
    if (!data.name || typeof data.name !== "string" || data.name.trim().length === 0) {
        errors.push("name is required and must be a non-empty string");
    }
    
    if (!data.category || !Object.values(CATEGORIES).includes(data.category)) {
        errors.push(`category must be one of: ${Object.values(CATEGORIES).join(", ")}`);
    }
    
    if (!data.expertise || !Array.isArray(data.expertise) || data.expertise.length === 0) {
        errors.push("expertise must be a non-empty array of strings");
    }
    
    if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
        errors.push("email must be a valid email address");
    }
    
    if (data.rate && (typeof data.rate !== "number" || data.rate < 0)) {
        errors.push("rate must be a positive number");
    }
    
    return errors;
}

function createExpert(data) {
    const now = isoNow();
    return {
        id: generateId(),
        name: data.name.trim(),
        category: data.category,
        expertise: data.expertise.map(e => e.toLowerCase().trim()),
        description: data.description || "",
        email: data.email || null,
        contact: data.contact || null,
        rate: data.rate || null,
        currency: data.currency || "USD",
        availability: data.availability || "available",
        tags: Array.isArray(data.tags) ? data.tags.map(t => t.toLowerCase().trim()) : [],
        metadata: data.metadata || {},
        engagementCount: 0,
        rating: null,
        createdAt: now,
        updatedAt: now
    };
}

// ─────────────────────────────────────────────────────────────────────────────
// HTTP Response Helpers
// ─────────────────────────────────────────────────────────────────────────────
function sendJson(res, statusCode, payload) {
    res.writeHead(statusCode, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
        "Access-Control-Allow-Origin": PUBLIC_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization"
    });
    res.end(JSON.stringify(payload));
}

function sendError(res, statusCode, message, details = null) {
    sendJson(res, statusCode, {
        ok: false,
        error: message,
        details,
        timestamp: isoNow()
    });
}

function sendSuccess(res, statusCode, data, meta = {}) {
    sendJson(res, statusCode, {
        ok: true,
        data,
        meta: {
            timestamp: isoNow(),
            ...meta
        }
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Request Body Parser
// ─────────────────────────────────────────────────────────────────────────────
async function parseBody(req) {
    return new Promise((resolve, reject) => {
        let body = "";
        req.on("data", chunk => { body += chunk; });
        req.on("end", () => {
            if (!body) return resolve({});
            try {
                resolve(JSON.parse(body));
            } catch (err) {
                reject(new Error("Invalid JSON body"));
            }
        });
        req.on("error", reject);
    });
}

// ─────────────────────────────────────────────────────────────────────────────
// Route Handlers
// ─────────────────────────────────────────────────────────────────────────────

// GET /api/v1/experts - List all experts with optional filters
async function handleListExperts(req, res, query) {
    const registry = await loadRegistry();
    let experts = [...registry.experts];
    
    // Filter by category
    if (query.category) {
        experts = experts.filter(e => e.category === query.category);
    }
    
    // Filter by availability
    if (query.availability) {
        experts = experts.filter(e => e.availability === query.availability);
    }
    
    // Filter by tag
    if (query.tag) {
        const tag = query.tag.toLowerCase();
        experts = experts.filter(e => e.tags.includes(tag));
    }
    
    // Pagination
    const page = Math.max(1, parseInt(query.page) || 1);
    const limit = Math.min(100, Math.max(1, parseInt(query.limit) || 20));
    const start = (page - 1) * limit;
    const paginatedExperts = experts.slice(start, start + limit);
    
    sendSuccess(res, 200, paginatedExperts, {
        total: experts.length,
        page,
        limit,
        totalPages: Math.ceil(experts.length / limit)
    });
}

// GET /api/v1/experts/:id - Get expert by ID
async function handleGetExpert(res, expertId) {
    const registry = await loadRegistry();
    const expert = registry.experts.find(e => e.id === expertId);
    
    if (!expert) {
        return sendError(res, 404, "Expert not found", { id: expertId });
    }
    
    sendSuccess(res, 200, expert);
}

// POST /api/v1/experts - Register a new expert
async function handleCreateExpert(req, res) {
    const body = await parseBody(req);
    const errors = validateExpert(body);
    
    if (errors.length > 0) {
        return sendError(res, 400, "Validation failed", errors);
    }
    
    const registry = await loadRegistry();
    const expert = createExpert(body);
    
    registry.experts.push(expert);
    registry.stats.totalRegistered++;
    registry.stats.byCategory[expert.category]++;
    
    await saveRegistry(registry);
    
    sendSuccess(res, 201, expert, { message: "Expert registered successfully" });
}

// PUT /api/v1/experts/:id - Update an expert
async function handleUpdateExpert(req, res, expertId) {
    const body = await parseBody(req);
    const registry = await loadRegistry();
    const index = registry.experts.findIndex(e => e.id === expertId);
    
    if (index === -1) {
        return sendError(res, 404, "Expert not found", { id: expertId });
    }
    
    const existing = registry.experts[index];
    const oldCategory = existing.category;
    
    // Merge updates
    const updated = {
        ...existing,
        name: body.name || existing.name,
        category: body.category || existing.category,
        expertise: body.expertise || existing.expertise,
        description: body.description !== undefined ? body.description : existing.description,
        email: body.email !== undefined ? body.email : existing.email,
        contact: body.contact !== undefined ? body.contact : existing.contact,
        rate: body.rate !== undefined ? body.rate : existing.rate,
        currency: body.currency || existing.currency,
        availability: body.availability || existing.availability,
        tags: body.tags || existing.tags,
        metadata: body.metadata || existing.metadata,
        updatedAt: isoNow()
    };
    
    // Update category stats if changed
    if (oldCategory !== updated.category) {
        registry.stats.byCategory[oldCategory]--;
        registry.stats.byCategory[updated.category]++;
    }
    
    registry.experts[index] = updated;
    await saveRegistry(registry);
    
    sendSuccess(res, 200, updated, { message: "Expert updated successfully" });
}

// DELETE /api/v1/experts/:id - Remove an expert
async function handleDeleteExpert(res, expertId) {
    const registry = await loadRegistry();
    const index = registry.experts.findIndex(e => e.id === expertId);
    
    if (index === -1) {
        return sendError(res, 404, "Expert not found", { id: expertId });
    }
    
    const removed = registry.experts.splice(index, 1)[0];
    registry.stats.totalRegistered--;
    registry.stats.byCategory[removed.category]--;
    
    await saveRegistry(registry);
    
    sendSuccess(res, 200, { id: expertId }, { message: "Expert removed successfully" });
}

// GET /api/v1/experts/search - Search experts
async function handleSearchExperts(res, query) {
    const registry = await loadRegistry();
    let experts = [...registry.experts];
    
    const searchTerm = (query.q || "").toLowerCase().trim();
    
    if (searchTerm) {
        experts = experts.filter(e => {
            // Search in name, description, expertise, and tags
            return e.name.toLowerCase().includes(searchTerm) ||
                   e.description.toLowerCase().includes(searchTerm) ||
                   e.expertise.some(ex => ex.includes(searchTerm)) ||
                   e.tags.some(t => t.includes(searchTerm));
        });
    }
    
    // Filter by expertise domain
    if (query.expertise) {
        const exp = query.expertise.toLowerCase();
        experts = experts.filter(e => e.expertise.some(ex => ex.includes(exp)));
    }
    
    // Filter by category
    if (query.category) {
        experts = experts.filter(e => e.category === query.category);
    }
    
    // Sort by engagement count (most engaged first)
    if (query.sort === "popular") {
        experts.sort((a, b) => b.engagementCount - a.engagementCount);
    }
    
    // Sort by rating
    if (query.sort === "rating") {
        experts.sort((a, b) => (b.rating || 0) - (a.rating || 0));
    }
    
    sendSuccess(res, 200, experts, {
        total: experts.length,
        searchTerm,
        filters: { expertise: query.expertise, category: query.category }
    });
}

// GET /api/v1/experts/category/:cat - Get experts by category
async function handleGetByCategory(res, category) {
    if (!Object.values(CATEGORIES).includes(category)) {
        return sendError(res, 400, "Invalid category", {
            valid: Object.values(CATEGORIES)
        });
    }
    
    const registry = await loadRegistry();
    const experts = registry.experts.filter(e => e.category === category);
    
    sendSuccess(res, 200, experts, {
        category,
        total: experts.length,
        categoryDescription: getCategoryDescription(category)
    });
}

function getCategoryDescription(category) {
    const descriptions = {
        expertise: "Domain experts to be called upon for specialized knowledge",
        pr: "PR and communications consultants for public relations needs",
        ideation: "Creative thinkers and innovators for new ideas and brainstorming",
        general: "Multi-purpose consultants for various needs"
    };
    return descriptions[category] || "";
}

// POST /api/v1/experts/:id/engage - Log engagement with an expert
async function handleEngage(req, res, expertId) {
    const body = await parseBody(req);
    const registry = await loadRegistry();
    const expert = registry.experts.find(e => e.id === expertId);
    
    if (!expert) {
        return sendError(res, 404, "Expert not found", { id: expertId });
    }
    
    const engagement = {
        id: `eng_${Date.now().toString(36)}_${crypto.randomBytes(4).toString("hex")}`,
        expertId,
        type: body.type || "consultation",
        purpose: body.purpose || "",
        requestedBy: body.requestedBy || "anonymous",
        rating: body.rating || null,
        notes: body.notes || "",
        createdAt: isoNow()
    };
    
    registry.engagements.push(engagement);
    expert.engagementCount++;
    expert.updatedAt = isoNow();
    
    // Update rating if provided
    if (body.rating && typeof body.rating === "number" && body.rating >= 1 && body.rating <= 5) {
        const expertEngagements = registry.engagements.filter(e => e.expertId === expertId && e.rating);
        const totalRating = expertEngagements.reduce((sum, e) => sum + (e.rating || 0), 0) + body.rating;
        expert.rating = Math.round((totalRating / (expertEngagements.length + 1)) * 10) / 10;
    }
    
    registry.stats.totalEngagements++;
    await saveRegistry(registry);
    
    sendSuccess(res, 201, engagement, { 
        message: "Engagement logged successfully",
        expertEngagementCount: expert.engagementCount
    });
}

// GET /api/v1/stats - Registry statistics
async function handleStats(res) {
    const registry = await loadRegistry();
    
    // Calculate additional stats
    const availableExperts = registry.experts.filter(e => e.availability === "available").length;
    const topExperts = [...registry.experts]
        .sort((a, b) => b.engagementCount - a.engagementCount)
        .slice(0, 5)
        .map(e => ({ id: e.id, name: e.name, engagements: e.engagementCount, rating: e.rating }));
    
    const expertiseDomains = {};
    registry.experts.forEach(e => {
        e.expertise.forEach(exp => {
            expertiseDomains[exp] = (expertiseDomains[exp] || 0) + 1;
        });
    });
    
    sendSuccess(res, 200, {
        registry: {
            version: registry.version,
            createdAt: registry.createdAt,
            updatedAt: registry.updatedAt
        },
        counts: {
            totalExperts: registry.experts.length,
            availableExperts,
            totalEngagements: registry.stats.totalEngagements,
            byCategory: registry.stats.byCategory
        },
        topExperts,
        expertiseDomains,
        categories: CATEGORIES
    });
}

// GET /api/v1/categories - List available categories
async function handleListCategories(res) {
    const descriptions = Object.entries(CATEGORIES).map(([key, value]) => ({
        key,
        value,
        description: getCategoryDescription(value)
    }));
    
    sendSuccess(res, 200, descriptions);
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Request Router
// ─────────────────────────────────────────────────────────────────────────────
async function handleRequest(req, res) {
    const url = new URL(req.url, `http://localhost:${PORT}`);
    const pathname = url.pathname;
    const method = req.method.toUpperCase();
    const query = Object.fromEntries(url.searchParams);
    
    // CORS preflight
    if (method === "OPTIONS") {
        res.writeHead(204, {
            "Access-Control-Allow-Origin": PUBLIC_ORIGIN,
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "86400"
        });
        return res.end();
    }
    
    try {
        // Route: GET /api/v1/stats
        if (method === "GET" && pathname === "/api/v1/stats") {
            return await handleStats(res);
        }
        
        // Route: GET /api/v1/categories
        if (method === "GET" && pathname === "/api/v1/categories") {
            return await handleListCategories(res);
        }
        
        // Route: GET /api/v1/experts/search
        if (method === "GET" && pathname === "/api/v1/experts/search") {
            return await handleSearchExperts(res, query);
        }
        
        // Route: GET /api/v1/experts/category/:cat
        const categoryMatch = pathname.match(/^\/api\/v1\/experts\/category\/([^/]+)$/);
        if (method === "GET" && categoryMatch) {
            return await handleGetByCategory(res, categoryMatch[1]);
        }
        
        // Route: POST /api/v1/experts/:id/engage
        const engageMatch = pathname.match(/^\/api\/v1\/experts\/([^/]+)\/engage$/);
        if (method === "POST" && engageMatch) {
            return await handleEngage(req, res, engageMatch[1]);
        }
        
        // Route: GET /api/v1/experts
        if (method === "GET" && pathname === "/api/v1/experts") {
            return await handleListExperts(req, res, query);
        }
        
        // Route: POST /api/v1/experts
        if (method === "POST" && pathname === "/api/v1/experts") {
            return await handleCreateExpert(req, res);
        }
        
        // Route: GET/PUT/DELETE /api/v1/experts/:id
        const expertMatch = pathname.match(/^\/api\/v1\/experts\/([^/]+)$/);
        if (expertMatch) {
            const expertId = expertMatch[1];
            if (method === "GET") {
                return await handleGetExpert(res, expertId);
            }
            if (method === "PUT") {
                return await handleUpdateExpert(req, res, expertId);
            }
            if (method === "DELETE") {
                return await handleDeleteExpert(res, expertId);
            }
        }
        
        // Health check
        if (method === "GET" && pathname === "/health") {
            return sendSuccess(res, 200, { status: "healthy", service: "expert-registry" });
        }
        
        // 404 - Route not found
        sendError(res, 404, "Route not found", { path: pathname, method });
        
    } catch (err) {
        console.error(`[ERROR] ${isoNow()} - ${err.message}`);
        sendError(res, 500, "Internal server error", { message: err.message });
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Server Initialization
// ─────────────────────────────────────────────────────────────────────────────
const server = http.createServer(handleRequest);

server.listen(PORT, () => {
    console.log(`
╔══════════════════════════════════════════════════════════════════════╗
║               Expert Registry RESTful Service                        ║
╠══════════════════════════════════════════════════════════════════════╣
║  Port:        ${String(PORT).padEnd(54)}║
║  Storage:     ${REGISTRY_FILE.slice(-50).padEnd(54)}║
║  Started:     ${isoNow().padEnd(54)}║
╠══════════════════════════════════════════════════════════════════════╣
║  Endpoints:                                                          ║
║    GET    /api/v1/experts              - List experts                ║
║    GET    /api/v1/experts/:id          - Get expert                  ║
║    POST   /api/v1/experts              - Register expert             ║
║    PUT    /api/v1/experts/:id          - Update expert               ║
║    DELETE /api/v1/experts/:id          - Remove expert               ║
║    GET    /api/v1/experts/search       - Search experts              ║
║    GET    /api/v1/experts/category/:c  - Get by category             ║
║    POST   /api/v1/experts/:id/engage   - Log engagement              ║
║    GET    /api/v1/stats                - Registry statistics         ║
║    GET    /api/v1/categories           - List categories             ║
╠══════════════════════════════════════════════════════════════════════╣
║  Categories: expertise | pr | ideation | general                     ║
╚══════════════════════════════════════════════════════════════════════╝
    `);
});

module.exports = { server, CATEGORIES };
