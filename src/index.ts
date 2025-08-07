import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { spawn } from "child_process";
import { join } from "path";
import { writeFileSync, appendFileSync, existsSync, mkdirSync } from "fs";

// Configuration schema
export const configSchema = z.object({
  debug: z.boolean().default(false).describe("Enable debug logging"),
});

// Setup logging
const logsDir = join(process.cwd(), "logs");
if (!existsSync(logsDir)) {
  mkdirSync(logsDir, { recursive: true });
}

const logFile = join(logsDir, `mcp-server-${new Date().toISOString().slice(0, 10)}.log`);

function log(message: string, level: 'INFO' | 'ERROR' | 'DEBUG' = 'INFO') {
  const timestamp = new Date().toISOString();
  const logLine = `[${timestamp}] [${level}] ${message}\n`;
  appendFileSync(logFile, logLine);

  // Also log to console for important messages
  if (level === 'ERROR') {
    console.error(message);
  } else if (level === 'INFO') {
    console.log(message);
  }
}

// Initialize log file
writeFileSync(logFile, `=== YOKATLAS MCP Server Log - ${new Date().toISOString()} ===\n`);

// Utility function to call Python helper
async function callPythonHelper(functionName: string, params: any = {}): Promise<any> {
  log(`🔄 [CallPythonHelper] Function: ${functionName}`, 'DEBUG');
  log(`📤 [CallPythonHelper] Input params: ${JSON.stringify(params, null, 2)}`, 'DEBUG');

  // Use process.cwd() to get the current working directory and build the path from there
  const pythonScriptPath = join(process.cwd(), "python_helpers", "yokatlas_helper.py");
  log(`📁 [CallPythonHelper] Python script path: ${pythonScriptPath}`, 'DEBUG');

  const commandArgs = [pythonScriptPath, functionName, JSON.stringify(params)];
  log(`🐍 [CallPythonHelper] Executing: python3 ${commandArgs.join(' ')}`, 'DEBUG');

  return new Promise((resolve, reject) => {
    const pythonProcess = spawn("python3", commandArgs);

    let stdout = "";
    let stderr = "";

    pythonProcess.stdout.on("data", (data) => {
      const chunk = data.toString();
      stdout += chunk;
      log(`📥 [CallPythonHelper] Python stdout chunk: ${chunk.trim()}`, 'DEBUG');
    });

    pythonProcess.stderr.on("data", (data) => {
      const chunk = data.toString();
      stderr += chunk;
      log(`❌ [CallPythonHelper] Python stderr chunk: ${chunk.trim()}`, 'DEBUG');
    });

    pythonProcess.on("close", (code) => {
      log(`🏁 [CallPythonHelper] Python process closed with code: ${code}`, 'DEBUG');

      if (code !== 0) {
        log(`❌ [CallPythonHelper] Error - Full stderr: ${stderr}`, 'ERROR');
        reject(new Error(`Python process exited with code ${code}: ${stderr}`));
        return;
      }

      log(`📥 [CallPythonHelper] Full stdout: ${stdout.trim()}`, 'DEBUG');

      try {
        const result = JSON.parse(stdout);
        log(`✅ [CallPythonHelper] Parsed result: ${JSON.stringify(result, null, 2)}`, 'DEBUG');
        resolve(result);
      } catch (error) {
        log(`❌ [CallPythonHelper] JSON parse error: ${error}`, 'ERROR');
        log(`📥 [CallPythonHelper] Raw output that failed to parse: ${stdout}`, 'ERROR');
        reject(new Error(`Failed to parse JSON output: ${error}\nOutput: ${stdout}`));
      }
    });

    pythonProcess.on("error", (error) => {
      log(`❌ [CallPythonHelper] Process error: ${error.message}`, 'ERROR');
      reject(new Error(`Failed to start Python process: ${error.message}`));
    });
  });
}

export default function createStatelessServer({
  config,
}: {
  config: z.infer<typeof configSchema>;
}) {
  log(`🚀 [Server] Creating YOKATLAS MCP Server with config: ${JSON.stringify(config)}`, 'INFO');

  const server = new McpServer({
    name: "YOKATLAS Local Search Server",
    version: "2.0.1",
  });

  // Health check tool
  server.tool(
    "health_check",
    "Check the health and capabilities of the YOKATLAS server, including search method and data availability",
    {},
    async () => {
      log(`🔧 [health_check] Tool called`, 'DEBUG');
      try {
        const result = await callPythonHelper("health_check", {});
        log(`✅ [health_check] Success - status: ${result.status}`, 'INFO');
        
        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        log(`❌ [health_check] Error: ${errorMessage}`, 'ERROR');
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: errorMessage }, null, 2),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Get associate degree atlas details
  server.tool(
    "get_associate_degree_atlas_details",
    "Get comprehensive details for a specific associate degree program from YOKATLAS Atlas",
    {
      yop_kodu: z.string().describe("Program YÖP code (e.g., '120910060') - unique identifier for the associate degree program"),
      year: z.number().describe("Data year for statistics (e.g., 2024, 2023)"),
    },
    async (args) => {
      log(`🔧 [get_associate_degree_atlas_details] Tool called with args: ${JSON.stringify(args)}`, 'DEBUG');
      try {
        const { yop_kodu, year } = args;
        log(`📋 [get_associate_degree_atlas_details] Extracted params - yop_kodu: ${yop_kodu}, year: ${year}`, 'DEBUG');

        const result = await callPythonHelper("get_associate_degree_atlas_details", {
          yop_kodu,
          year,
        });

        log(`✅ [get_associate_degree_atlas_details] Success`, 'INFO');
        if (config.debug) {
          log("Associate degree atlas details result: " + JSON.stringify(result), 'DEBUG');
        }

        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        log(`❌ [get_associate_degree_atlas_details] Error: ${errorMessage}`, 'ERROR');
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: errorMessage }, null, 2),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Get bachelor degree atlas details
  server.tool(
    "get_bachelor_degree_atlas_details",
    "Get comprehensive details for a specific bachelor's degree program from YOKATLAS Atlas",
    {
      yop_kodu: z.string().describe("Program YÖP code (e.g., '102210277') - unique identifier for the bachelor's degree program"),
      year: z.number().describe("Data year for statistics (e.g., 2024, 2023)"),
    },
    async (args) => {
      log(`🔧 [get_bachelor_degree_atlas_details] Tool called with args: ${JSON.stringify(args)}`, 'DEBUG');
      try {
        const { yop_kodu, year } = args;
        log(`📋 [get_bachelor_degree_atlas_details] Extracted params - yop_kodu: ${yop_kodu}, year: ${year}`, 'DEBUG');

        const result = await callPythonHelper("get_bachelor_degree_atlas_details", {
          yop_kodu,
          year,
        });

        log(`✅ [get_bachelor_degree_atlas_details] Success`, 'INFO');
        if (config.debug) {
          log("Bachelor degree atlas details result: " + JSON.stringify(result), 'DEBUG');
        }

        return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        log(`❌ [get_bachelor_degree_atlas_details] Error: ${errorMessage}`, 'ERROR');
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: errorMessage }, null, 2),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Search bachelor degree programs
  server.tool(
    "search_bachelor_degree_programs",
    "Search for bachelor's degree programs using LOCAL DATA with instant results, smart fuzzy matching, and bell curve sampling for large result sets",
    {
      universite: z.union([z.string(), z.array(z.string())]).optional().describe("University name(s) with fuzzy matching support. Can be a single string or array of strings (e.g., 'boğaziçi' or ['boğaziçi', 'odtü'] → matches any of the specified universities)"),
      program: z.union([z.string(), z.array(z.string())]).optional().describe("Program/department name(s) with partial matching. Can be a single string or array of strings (e.g., 'bilgisayar' or ['bilgisayar', 'yazılım'] → matches any of the specified programs)"),
      sehir: z.union([z.string(), z.array(z.string())]).optional().describe("City name(s) where the university is located. Can be a single string or array of strings (e.g., 'istanbul' or ['istanbul', 'ankara'] → matches any of the specified cities)"),
      puan_turu: z.enum(["SAY", "EA", "SOZ", "DIL"]).optional().describe("Score type: SAY (Science), EA (Equal Weight), SOZ (Verbal), DIL (Language)"),
      universite_turu: z.enum(["Devlet", "Vakıf", "KKTC", "Yurt Dışı"]).optional().describe("University type: Devlet (State), Vakıf (Foundation), KKTC (TRNC), Yurt Dışı (International)"),
      ucret: z.enum(["Ücretsiz", "Ücretli", "İÖ-Ücretli", "Burslu", "%50 İndirimli", "%25 İndirimli", "AÖ-Ücretli", "UÖ-Ücretli"]).optional().describe("Fee status: Ücretsiz (Free), Ücretli (Paid), İÖ-Ücretli (Evening-Paid), Burslu (Scholarship), İndirimli (Discounted), AÖ-Ücretli (Open Education-Paid), UÖ-Ücretli (Distance Learning-Paid)"),
      ogretim_turu: z.enum(["Örgün", "İkinci", "Açıköğretim", "Uzaktan"]).optional().describe("Education type: Örgün (Regular), İkinci (Evening), Açıköğretim (Open Education), Uzaktan (Distance Learning)"),
      doluluk: z.enum(["Doldu", "Doldu#", "Dolmadı", "Yeni"]).optional().describe("Program availability: Doldu (Filled), Doldu# (Filled with conditions), Dolmadı (Not filled), Yeni (New program)"),
      siralama: z.number().optional().describe("Target success ranking - applies bell curve sampling centered at this ranking. Programs closer to this ranking are more likely to be selected. Automatically filters to range [sıralama * 0.5, sıralama * 1.5]"),
      max_results: z.number().optional().describe("Maximum number of results to return. If more results are found, bell curve sampling is applied for representative distribution (default: 100)"),
    },
    async (args) => {
      log(`🔧 [search_bachelor_degree_programs] Tool called with args: ${JSON.stringify(args)}`, 'DEBUG');
      try {
        // Map directly to final yokatlas_py parameter format
        log(`📋 [search_bachelor_degree_programs] Final params for yokatlas_py: ${JSON.stringify(args)}`, 'DEBUG');
        const result = await callPythonHelper("search_bachelor_degree_programs", args);

        log(`✅ [search_bachelor_degree_programs] Success`, 'INFO');
        if (config.debug) {
          log("Bachelor degree search result: " + result, 'DEBUG');
        }

        return { content: [{ type: "text", text: result }] };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        log(`❌ [search_bachelor_degree_programs] Error: ${errorMessage}`, 'ERROR');
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: errorMessage }, null, 2),
            },
          ],
          isError: true,
        };
      }
    }
  );

  // Search associate degree programs
  server.tool(
    "search_associate_degree_programs",
    "Search for associate degree (önlisans) programs using LOCAL DATA with instant results, smart fuzzy matching, and bell curve sampling for large result sets",
    {
      university: z.union([z.string(), z.array(z.string())]).optional().describe("University name(s) with fuzzy matching support. Can be a single string or array of strings (e.g., 'anadolu' or ['anadolu', 'istanbul'] → matches any of the specified universities)"),
      program: z.union([z.string(), z.array(z.string())]).optional().describe("Program name(s) with partial matching. Can be a single string or array of strings (e.g., 'turizm' or ['turizm', 'otel'] → matches any of the specified programs)"),
      city: z.union([z.string(), z.array(z.string())]).optional().describe("City name(s) where the university is located. Can be a single string or array of strings (e.g., 'istanbul' or ['istanbul', 'ankara'] → matches any of the specified cities)"),
      university_type: z.enum(["Devlet", "Vakıf", "KKTC", "Yurt Dışı"]).optional().describe("University type: Devlet (State), Vakıf (Foundation), KKTC (TRNC), Yurt Dışı (International)"),
      fee_type: z.enum(["Ücretsiz", "Ücretli", "İÖ-Ücretli", "Burslu", "%50 İndirimli", "%25 İndirimli", "AÖ-Ücretli", "UÖ-Ücretli"]).optional().describe("Fee status: Ücretsiz (Free), Ücretli (Paid), İÖ-Ücretli (Evening-Paid), Burslu (Scholarship), İndirimli (Discounted), AÖ-Ücretli (Open Education-Paid), UÖ-Ücretli (Distance Learning-Paid)"),
      education_type: z.enum(["Örgün", "İkinci", "Açıköğretim", "Uzaktan"]).optional().describe("Education type: Örgün (Regular), İkinci (Evening), Açıköğretim (Open Education), Uzaktan (Distance Learning)"),
      availability: z.enum(["Doldu", "Doldu#", "Dolmadı", "Yeni"]).optional().describe("Program availability: Doldu (Filled), Doldu# (Filled with conditions), Dolmadı (Not filled), Yeni (New program)"),
      siralama: z.number().optional().describe("Target success ranking - applies bell curve sampling centered at this ranking. Programs closer to this ranking are more likely to be selected. Automatically filters to range [sıralama * 0.5, sıralama * 1.5]. Associate degree programs use TYT-based rankings."),
      max_results: z.number().optional().describe("Maximum number of results to return. If more results are found, bell curve sampling is applied for representative distribution (default: 100)"),
    },
    async (args) => {
      log(`🔧 [search_associate_degree_programs] Tool called with args: ${JSON.stringify(args)}`, 'DEBUG');
      try {
        // Map directly to final yokatlas_py parameter format
        const finalParams = {
          universite: args.university || "",
          program: args.program || "",
          sehir: args.city || "",
          puan_turu: "tyt", // Associate degree always uses TYT
          universite_turu: args.university_type || "",
          ucret: args.fee_type || "",
          ogretim_turu: args.education_type || "",
          doluluk: args.availability || "",
          siralama: args.siralama, // Support for bell curve sampling with sıralama
          max_results: args.max_results || 100,
        };

        log(`📋 [search_associate_degree_programs] Final params for yokatlas_py: ${JSON.stringify(finalParams)}`, 'DEBUG');
        const result = await callPythonHelper("search_associate_degree_programs", finalParams);

        log(`✅ [search_associate_degree_programs] Success`, 'INFO');
        if (config.debug) {
          log("Associate degree search result: " + result, 'DEBUG');
        }

        return { content: [{ type: "text", text: result }] };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        log(`❌ [search_associate_degree_programs] Error: ${errorMessage}`, 'ERROR');
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ error: errorMessage }, null, 2),
            },
          ],
          isError: true,
        };
      }
    }
  );

  log(`✅ [Server] YOKATLAS MCP Server created successfully`, 'INFO');
  return server;
}
