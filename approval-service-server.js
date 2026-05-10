const http = require("http");
const fs = require("fs");
const fsp = fs.promises;
const path = require("path");
const { URL } = require("url");

const PORT = Number(process.env.APPROVAL_SERVICE_PORT || 8787);
const ROOT = __dirname;
const STATE_FILE = path.join(ROOT, ".approval-service-state.json");
const DEFAULT_SERVICE_URL = `http://localhost:${PORT}`;

function isoNow() {
    return new Date().toISOString();
}

function safeJson(value) {
    return JSON.stringify(value, null, 2);
}

function normalizeServiceUrl(value) {
    const parsed = new URL(String(value || "").trim());
    if (!/^https?:$/.test(parsed.protocol)) {
        throw new Error("Only http and https URLs are supported.");
    }
    return parsed.toString().replace(/\/$/, "");
}

function createAuditEntry(action, serviceUrl, ok, message, extra = {}) {
    return {
        action,
        serviceUrl,
        ok,
        message,
        timestamp: isoNow(),
        ...extra,
    };
}

function defaultState() {
    return {
        serviceUrl: DEFAULT_SERVICE_URL,
        audit: [createAuditEntry("service-started", DEFAULT_SERVICE_URL, true, "Approval service started.")],
        lastTest: null,
        lastError: null,
    };
}

async function loadState() {
    try {
        const raw = await fsp.readFile(STATE_FILE, "utf8");
        const parsed = JSON.parse(raw);
        return {
            serviceUrl: parsed.serviceUrl || DEFAULT_SERVICE_URL,
            audit: Array.isArray(parsed.audit) ? parsed.audit : [],
            lastTest: parsed.lastTest || null,
            lastError: parsed.lastError || null,
        };
    } catch (_) {
        return defaultState();
    }
}

async function saveState(state) {
    await fsp.writeFile(STATE_FILE, safeJson(state));
}

function sendJson(res, statusCode, payload) {
    res.writeHead(statusCode, {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
    });
    res.end(JSON.stringify(payload));
}

function sendText(res, statusCode, body, contentType = "text/plain; charset=utf-8") {
    res.writeHead(statusCode, {
        "Content-Type": contentType,
        "Cache-Control": "no-store",
    });
    res.end(body);
}

function createMarkdownAudit(state) {
    const lines = [
        "# Approval Service Audit",
        "",
        `- Service URL: ${state.serviceUrl || DEFAULT_SERVICE_URL}`,
        `- Exported at: ${isoNow()}`,
        `- Audit entries: ${Array.isArray(state.audit) ? state.audit.length : 0}`,
        "",
        "| Time | Action | Result | URL | Message |",
        "| --- | --- | --- | --- | --- |",
    ];

    for (const entry of state.audit || []) {
        lines.push(
            `| ${entry.timestamp || ""} | ${entry.action || ""} | ${entry.ok === false ? "failed" : "ok"} | ${entry.serviceUrl || ""} | ${(entry.message || "").replace(/\|/g, "\\|")} |`
        );
    }

    return lines.join("\n");
}

async function readJsonBody(req) {
    const chunks = [];
    for await (const chunk of req) {
        chunks.push(chunk);
    }
    const raw = Buffer.concat(chunks).toString("utf8").trim();
    if (!raw) {
        return {};
    }
    return JSON.parse(raw);
}

async function testTargetUrl(serviceUrl) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const startedAt = Date.now();
    try {
        let response = await fetch(serviceUrl, {
            method: "HEAD",
            signal: controller.signal,
        });
        if (response.status === 405 || response.status === 501) {
            response = await fetch(serviceUrl, {
                method: "GET",
                signal: controller.signal,
            });
        }
        return {
            ok: response.ok,
            status: response.status,
            statusText: response.statusText,
            durationMs: Date.now() - startedAt,
            finalUrl: response.url || serviceUrl,
        };
    } finally {
        clearTimeout(timeout);
    }
}

async function handleRequest(req, res) {
    const state = await loadState();
    const requestUrl = new URL(req.url, `http://${req.headers.host || `localhost:${PORT}`}`);

    if ((req.method === "GET" || req.method === "HEAD") && requestUrl.pathname === "/health") {
        return sendJson(res, 200, {
            ok: true,
            service: "approval-service",
            serviceUrl: state.serviceUrl,
            timestamp: isoNow(),
        });
    }

    if (req.method === "GET" && requestUrl.pathname === "/api/state") {
        return sendJson(res, 200, state);
    }

    if (req.method === "POST" && requestUrl.pathname === "/api/service-url") {
        try {
            const payload = await readJsonBody(req);
            const serviceUrl = normalizeServiceUrl(payload.serviceUrl || "");
            const nextState = {
                ...state,
                serviceUrl,
                lastError: null,
            };
            nextState.audit = [
                ...(nextState.audit || []),
                createAuditEntry("save-url", serviceUrl, true, `Saved service URL: ${serviceUrl}`),
            ];
            await saveState(nextState);
            return sendJson(res, 200, nextState);
        } catch (error) {
            const nextState = {
                ...state,
                lastError: { message: error.message },
            };
            nextState.audit = [
                ...(nextState.audit || []),
                createAuditEntry("save-url", state.serviceUrl || DEFAULT_SERVICE_URL, false, error.message),
            ];
            await saveState(nextState);
            return sendJson(res, 400, { error: error.message, ...nextState });
        }
    }

    if (req.method === "POST" && requestUrl.pathname === "/api/test-service") {
        try {
            const payload = await readJsonBody(req);
            const serviceUrl = normalizeServiceUrl(payload.serviceUrl || state.serviceUrl || DEFAULT_SERVICE_URL);
            const testResult = await testTargetUrl(serviceUrl);
            const message = testResult.ok
                ? `Service reachable: ${testResult.status} ${testResult.statusText}`
                : `Service responded with ${testResult.status} ${testResult.statusText}`;
            const nextState = {
                ...state,
                serviceUrl,
                lastTest: {
                    ...testResult,
                    serviceUrl,
                    timestamp: isoNow(),
                },
                lastError: testResult.ok ? null : { message },
            };
            nextState.audit = [
                ...(nextState.audit || []),
                createAuditEntry("test-service", serviceUrl, testResult.ok, message, testResult),
            ];
            await saveState(nextState);
            return sendJson(res, 200, {
                message,
                ...nextState,
            });
        } catch (error) {
            const nextState = {
                ...state,
                lastError: { message: error.message },
            };
            nextState.audit = [
                ...(nextState.audit || []),
                createAuditEntry("test-service", state.serviceUrl || DEFAULT_SERVICE_URL, false, error.message),
            ];
            await saveState(nextState);
            return sendJson(res, 400, { error: error.message, ...nextState });
        }
    }

    if (req.method === "GET" && requestUrl.pathname === "/api/export-audit") {
        const format = String(requestUrl.searchParams.get("format") || "md").toLowerCase();
        const auditFileName = format === "json" ? "approval-service-audit.json" : "approval-service-audit.md";
        const exportPayload = {
            exportedAt: isoNow(),
            serviceUrl: state.serviceUrl || DEFAULT_SERVICE_URL,
            audit: state.audit || [],
            lastTest: state.lastTest || null,
            lastError: state.lastError || null,
        };
        const nextState = {
            ...state,
            audit: [
                ...(state.audit || []),
                createAuditEntry("export-audit", state.serviceUrl || DEFAULT_SERVICE_URL, true, `Exported audit as ${format}`),
            ],
        };
        await saveState(nextState);

        if (format === "json") {
            res.writeHead(200, {
                "Content-Type": "application/json; charset=utf-8",
                "Content-Disposition": `attachment; filename="${auditFileName}"`,
                "Cache-Control": "no-store",
            });
            return res.end(JSON.stringify(exportPayload, null, 2));
        }

        const markdown = createMarkdownAudit(exportPayload);
        res.writeHead(200, {
            "Content-Type": "text/markdown; charset=utf-8",
            "Content-Disposition": `attachment; filename="${auditFileName}"`,
            "Cache-Control": "no-store",
        });
        return res.end(markdown);
    }

    if ((req.method === "GET" || req.method === "HEAD") && (requestUrl.pathname === "/" || requestUrl.pathname === "/approval-service.html")) {
        const htmlPath = path.join(ROOT, "approval-service.html");
        try {
            const html = await fsp.readFile(htmlPath, "utf8");
            if (req.method === "HEAD") {
                res.writeHead(200, {
                    "Content-Type": "text/html; charset=utf-8",
                    "Cache-Control": "no-store",
                });
                return res.end();
            }
            return sendText(res, 200, html, "text/html; charset=utf-8");
        } catch (error) {
            return sendText(res, 500, `Unable to load approval-service.html: ${error.message}`);
        }
    }

    const filePath = path.normalize(path.join(ROOT, requestUrl.pathname));
    if (!filePath.startsWith(ROOT)) {
        return sendText(res, 403, "Forbidden");
    }

    try {
        const stat = await fsp.stat(filePath);
        if (stat.isDirectory()) {
            return sendText(res, 404, "Not found");
        }

        const ext = path.extname(filePath).toLowerCase();
        const mimeTypes = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".md": "text/markdown; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".txt": "text/plain; charset=utf-8",
        };
        const data = await fsp.readFile(filePath);
        res.writeHead(200, {
            "Content-Type": mimeTypes[ext] || "application/octet-stream",
            "Cache-Control": "no-store",
        });
        if (req.method === "HEAD") {
            return res.end();
        }
        return res.end(data);
    } catch (_) {
        return sendText(res, 404, "Not found");
    }
}

async function bootstrap() {
    const state = await loadState();
    if (!state.audit || !state.audit.length) {
        await saveState(defaultState());
    }

    const server = http.createServer((req, res) => {
        handleRequest(req, res).catch(error => {
            sendJson(res, 500, { error: error.message || "Internal server error" });
        });
    });

    server.listen(PORT, "0.0.0.0", () => {
        console.log(`Approval service listening on http://localhost:${PORT}`);
    });
}

bootstrap().catch(error => {
    console.error(error);
    process.exitCode = 1;
});