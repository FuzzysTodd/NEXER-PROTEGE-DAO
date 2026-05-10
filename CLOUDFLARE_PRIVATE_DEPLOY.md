# Cloudflare Private Deployment Guide

This guide walks you through deploying the **Nexus Withdraw Dashboard** on **Cloudflare Pages** and locking it down so only you (or approved users) can access it using **Cloudflare Zero Trust Access**.

---

## Overview

| Step | What you do |
|------|-------------|
| 1 | Deploy the static site to Cloudflare Pages |
| 2 | Add a Zero Trust Access policy (login gate) |
| 3 | Verify private access is working |

---

## Part 1 — Deploy to Cloudflare Pages

### 1.1 Log in to Cloudflare

1. Go to [https://dash.cloudflare.com](https://dash.cloudflare.com).
2. Log in with your Cloudflare account.

### 1.2 Open Pages

1. In the left sidebar, click **Workers & Pages**.
2. Click the **Pages** tab.
3. Click **Create a project**.

### 1.3 Connect your GitHub repo

1. Click **Connect to Git**.
2. If prompted, click **Connect GitHub** and authorise Cloudflare to access your account.
3. Find and select the repo `FuzzysTodd/The-Nexus-Protocol-Token-DAO`.
4. Click **Begin setup**.

### 1.4 Configure build settings

On the **Set up builds and deployments** screen fill in:

| Field | Value |
|-------|-------|
| **Project name** | `nexus-withdraw` (or any name you like) |
| **Production branch** | `main` |
| **Framework preset** | `None` |
| **Build command** | *(leave blank)* |
| **Build output directory** | `/` |

> **Why `/`?**  Cloudflare Pages looks for `index.html` in the output directory and serves it at the site root (`/`).  
> The repo already has `index.html` at the root, which is the withdraw dashboard.

5. Click **Save and Deploy**.
6. Wait ~30 seconds for the first deploy to finish.
7. Cloudflare will show a green **Success** banner and a URL like:
   ```
   https://nexus-withdraw.pages.dev
   ```
   Copy this URL — you will need it in Part 2.

---

## Part 2 — Restrict Access with Cloudflare Zero Trust

This step adds a mandatory login screen in front of your Pages site. Anyone without an approved account will be blocked.

### 2.1 Open Zero Trust

1. In the Cloudflare dashboard sidebar, click **Zero Trust**.
   - If this is your first time, you may be asked to pick a team name (e.g. `fuzzystodd`). Choose any name and click **Get started**.

### 2.2 Add a Self-hosted Application

1. In the Zero Trust sidebar, click **Access** → **Applications**.
2. Click **Add an application**.
3. Choose **Self-hosted**.

### 2.3 Fill in Application details

| Field | Value |
|-------|-------|
| **Application name** | `Nexus Withdraw Dashboard` |
| **Session Duration** | `24 hours` (or whatever you prefer) |
| **Application domain** | `nexus-withdraw.pages.dev` (your Pages URL without `https://`) |
| **Path** | *(leave blank — protects the whole site)* |

Click **Next**.

### 2.4 Add the Allow policy

1. Click **Add a policy**.
2. **Policy name:** `Allow owner`
3. **Action:** `Allow`
4. Under **Configure rules → Include**, choose **Emails** and enter your email address(es):
   ```
   your-email@example.com
   ```
   - You can add multiple email addresses, one per line.
   - Optional: also add **GitHub** → your GitHub username to allow GitHub login.
5. Click **Save policy**.

### 2.5 Add the Deny-everyone policy (recommended)

1. Click **Add a policy** again.
2. **Policy name:** `Deny everyone else`
3. **Action:** `Deny`
4. Under **Configure rules → Include**, choose **Everyone**.
5. Click **Save policy**.

> **Order matters.** The Allow policy must be listed before the Deny policy. Drag to reorder if needed.

6. Click **Next**, review the settings, then click **Save application**.

---

## Part 3 — Verify Private Access

### 3.1 Test in an incognito window

1. Open a new **incognito / private browsing** window.
2. Navigate to your Pages URL (e.g. `https://nexus-withdraw.pages.dev`).
3. You should be redirected to a **Cloudflare Access login screen** — not the dashboard.
4. Enter your approved email address and complete the one-time code sent to your email.
5. After logging in you should see the **Nexus Withdraw Dashboard**.

### 3.2 Test MetaMask

1. Make sure MetaMask is installed in your browser.
2. Click **Connect Wallet** on the dashboard.
3. Approve the connection in MetaMask.
4. Switch to the correct network (Ethereum Mainnet, Base, etc.) that your contracts are deployed on.
5. Add a contract address and click **Withdraw**.

> **Important:** The wallet that connects must be the owner/admin of the contract. Transparent proxy admin addresses cannot call fallback functions; connect the non-admin owner wallet if you hit reverts.

---

## Notes

### Pages default `index.html` behavior

Cloudflare Pages automatically serves `index.html` from the root of your output directory when a request is made to `/`.  
The repo's `index.html` is the withdraw dashboard, so no redirect rules are needed.

### Both `index.html` and `withdraw.html` work

- `/` → `index.html` (withdraw dashboard, served by Cloudflare Pages default)
- `/withdraw.html` → same dashboard (direct file access, also works on Pages)

### Optional: Add a custom domain

In **Workers & Pages → your project → Custom Domains**, you can attach a domain you own (e.g. `withdraw.yourdomain.com`) instead of using the default `.pages.dev` URL.  
Cloudflare Zero Trust Access works with custom domains — just update the **Application domain** in the Access application settings to match.

### Re-deployments

Every push to the `main` branch triggers a new Cloudflare Pages deployment automatically. No extra action required.

### MetaMask network selection

Switch networks in MetaMask before connecting. Common networks:

| Network | Chain ID |
|---------|----------|
| Ethereum Mainnet | 1 |
| Base | 8453 |
| Binance Smart Chain | 56 |
| Polygon | 137 |
| Arbitrum One | 42161 |
| Optimism | 10 |

### Security reminders

- Cloudflare Access is the authentication layer — the HTML/JS itself is public once authenticated.
- Never add private keys to any file in this repo.
- The `withdraw.js` script only uses MetaMask (browser wallet injection); no keys are stored anywhere.
