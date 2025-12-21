# DealFinder Desktop App

Electron wrapper for the DealFinder real estate analysis platform.

## Features

- **Local scraping**: Property URLs are scraped locally using Puppeteer, bypassing IP blocks from listing sites
- **Seamless integration**: Uses the same API for financial analysis and rent estimates
- **Cross-platform**: Builds for Mac, Windows, and Linux

## Development

### Prerequisites

- Node.js 18+
- npm or yarn
- The Next.js frontend running on localhost:3000 (for dev mode)

### Install dependencies

```bash
cd electron
npm install
```

### Run in development mode

First, start the Next.js dev server:

```bash
cd ../web
npm run dev
```

Then start Electron:

```bash
cd ../electron
npm run dev
```

### Build for production

Build the Next.js app first:

```bash
cd ../web
npm run build
```

Then build Electron:

```bash
cd ../electron
npm run build:mac   # For macOS
npm run build:win   # For Windows
npm run build:linux # For Linux
```

The built app will be in `electron/dist/`.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron App                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐  │
│  │   main.js   │◄──►│ preload.js  │◄──►│  Next.js App    │  │
│  │  (Node.js)  │    │   (Bridge)  │    │  (Renderer)     │  │
│  └──────┬──────┘    └─────────────┘    └────────┬────────┘  │
│         │                                        │           │
│         ▼                                        │           │
│  ┌─────────────┐                                │           │
│  │ scraper.js  │ ◄── Puppeteer (local scraping) │           │
│  │ (Puppeteer) │                                │           │
│  └─────────────┘                                │           │
└─────────────────────────────────────────────────┼───────────┘
                                                  │
                                                  ▼
                                        ┌─────────────────┐
                                        │   Vercel API    │
                                        │  (Analysis &    │
                                        │   Rent Data)    │
                                        └─────────────────┘
```

## How it works

1. User pastes a Zillow/Redfin/Realtor URL
2. Electron detects it's running as a desktop app
3. main.js launches Puppeteer to scrape the listing locally (residential IP = no blocks)
4. Parsed property data is sent to the API via `/api/import/parsed`
5. API enriches with rent estimates and market data, returns analysis
6. Results displayed in the app
