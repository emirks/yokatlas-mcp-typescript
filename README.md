# YOKATLAS MCP Server

🚀 **[Live Deployment on Smithery](https://smithery.ai/server/@emirks/yokatlas-mcp-typescript)** | 🌐 **[Tercihify Website](https://www.tercihify.com/)**

TypeScript MCP wrapper for the [yokatlas-py](https://github.com/emirks/yokatlas-py) package, providing access to Turkish higher education data through Model Context Protocol.

## Features

- **Bachelor's Degree Search** - Smart fuzzy search for 4-year university programs
- **Associate Degree Search** - Search for 2-year college programs  
- **Program Details** - Get comprehensive information for specific programs
- **Health Check** - Server status and availability monitoring

## Requirements

- Node.js 18+ (handled by Smithery runtime)
- Python 3.8+ (automatically installed during deployment)
- npm (for local development)

## Setup

### Local Development
1. **Install dependencies:**
   ```bash
   npm ci
   pip install -r requirements.txt
   ```

### Smithery Deployment
Uses **Custom Deploy** with a custom Dockerfile for full control over the build environment. Dependencies are automatically installed during Docker build - no manual setup required!

2. **Development:**
   ```bash
   npm run dev
   ```

3. **Deploy:**
   ```bash
   npm run deploy
   ```

## MCP Tools

### `search_bachelor_degree_programs`
Search 4-year university programs with fuzzy matching.

**Parameters:**
- `universite` - University name (fuzzy matching)
- `program` - Program/department name
- `sehir` - City name
- `puan_turu` - Score type: SAY, EA, SOZ, DIL
- `universite_turu` - University type: Devlet, Vakıf, KKTC, Yurt Dışı
- `ucret` - Fee status: Ücretsiz, Ücretli, Burslu, etc.
- `ogretim_turu` - Education type: Örgün, İkinci, Açıköğretim, Uzaktan

### `search_associate_degree_programs`
Search 2-year college programs.

**Parameters:**
- `university` - University name (fuzzy matching)
- `program` - Program name
- `city` - City name
- `university_type` - University type
- `fee_type` - Fee status
- `education_type` - Education type

### `get_bachelor_degree_atlas_details`
Get detailed information for a specific bachelor's program.

**Parameters:**
- `yop_kodu` - Program YÖP code (e.g., "102210277")
- `year` - Data year (e.g., 2024)

### `get_associate_degree_atlas_details`
Get detailed information for a specific associate degree program.

**Parameters:**
- `yop_kodu` - Program YÖP code (e.g., "120910060")
- `year` - Data year (e.g., 2024)

### `health_check`
Verify server status and yokatlas-py availability.

## Tech Stack

- **TypeScript** - MCP server implementation
- **Python** - yokatlas-py package runner
- **Smithery SDK** - MCP TypeScript framework
- **Zod** - Schema validation

## License

MIT 