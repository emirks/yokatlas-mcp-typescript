#!/usr/bin/env python3
import json
import sys
import asyncio
import os
from datetime import datetime
from typing import Dict, Any, Optional


# Setup logging
def setup_logging():
    logs_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_file = os.path.join(
        logs_dir, f"python-helper-{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    # Initialize log file
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"=== YOKATLAS Python Helper Log - {datetime.now().isoformat()} ===\n")

    return log_file


def log_to_file(message: str, level: str = "INFO"):
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [{level}] {message}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line)

    # Also print to stderr so it shows in TypeScript logs
    print(f"🐍 [{level}] {message}", file=sys.stderr)


# Initialize logging
LOG_FILE = setup_logging()

# Import the yokatlas_py functions with graceful fallback
NEW_SMART_API = False
YOKATLAS_AVAILABLE = False

try:
    from yokatlas_py import search_lisans_programs, search_onlisans_programs
    from yokatlas_py import YOKATLASLisansAtlasi, YOKATLASOnlisansAtlasi
    from yokatlas_py.models import SearchParams, ProgramInfo

    NEW_SMART_API = True
    YOKATLAS_AVAILABLE = True
except ImportError:
    try:
        from yokatlas_py import (
            YOKATLASLisansTercihSihirbazi,
            YOKATLASOnlisansTercihSihirbazi,
        )
        from yokatlas_py import YOKATLASLisansAtlasi, YOKATLASOnlisansAtlasi
        from yokatlas_py.models import SearchParams, ProgramInfo

        NEW_SMART_API = False
        YOKATLAS_AVAILABLE = True
    except ImportError:
        try:
            from yokatlas_py.lisansatlasi import YOKATLASLisansAtlasi
            from yokatlas_py.lisanstercihsihirbazi import YOKATLASLisansTercihSihirbazi
            from yokatlas_py.onlisansatlasi import YOKATLASOnlisansAtlasi
            from yokatlas_py.onlisanstercihsihirbazi import (
                YOKATLASOnlisansTercihSihirbazi,
            )

            NEW_SMART_API = False
            YOKATLAS_AVAILABLE = True
        except ImportError:
            # yokatlas_py is not available - provide graceful fallback
            NEW_SMART_API = False
            YOKATLAS_AVAILABLE = False


def get_module_unavailable_error(function_name: str) -> Dict[str, Any]:
    """Return a helpful error message when yokatlas_py is not available."""
    return {
        "error": f"yokatlas_py module is not available",
        "function": function_name,
        "suggestion": "Please install the yokatlas_py package: pip install git+https://github.com/emirks/yokatlas-py.git",
        "status": "module_not_found",
        "available_functions": ["health_check"] if not YOKATLAS_AVAILABLE else ["all"],
    }


async def health_check() -> Dict[str, Any]:
    """Simple health check to verify the server is running."""
    return {
        "status": "healthy",
        "server": "YOKATLAS API Server",
        "api_version": "v1.0",
        "smart_search": NEW_SMART_API,
        "yokatlas_available": YOKATLAS_AVAILABLE,
        "message": (
            "All systems operational"
            if YOKATLAS_AVAILABLE
            else "yokatlas_py module not available - install required for full functionality"
        ),
    }


async def get_associate_degree_atlas_details(
    yop_kodu: str, year: int
) -> Dict[str, Any]:
    """Get comprehensive details for a specific associate degree program."""
    if not YOKATLAS_AVAILABLE:
        return get_module_unavailable_error("get_associate_degree_atlas_details")

    try:
        onlisans_atlasi = YOKATLASOnlisansAtlasi({"program_id": yop_kodu, "year": year})
        result = await onlisans_atlasi.fetch_all_details()
        return result
    except Exception as e:
        return {"error": str(e), "program_id": yop_kodu, "year": year}


async def get_bachelor_degree_atlas_details(yop_kodu: str, year: int) -> Dict[str, Any]:
    """Get comprehensive details for a specific bachelor's degree program."""
    if not YOKATLAS_AVAILABLE:
        return get_module_unavailable_error("get_bachelor_degree_atlas_details")

    try:
        lisans_atlasi = YOKATLASLisansAtlasi({"program_id": yop_kodu, "year": year})
        result = await lisans_atlasi.fetch_all_details()
        return result
    except Exception as e:
        return {"error": str(e), "program_id": yop_kodu, "year": year}


def search_bachelor_degree_programs(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for bachelor's degree programs with smart fuzzy matching."""
    if not YOKATLAS_AVAILABLE:
        return get_module_unavailable_error("search_bachelor_degree_programs")

    try:
        if NEW_SMART_API:
            # Parameters are already in final format from TypeScript side
            # No mapping needed - pass directly to search function
            results = search_lisans_programs(params, smart_search=True)

            validated_results = []
            for program_data in results:
                try:
                    program = ProgramInfo(**program_data)
                    validated_results.append(program.model_dump())
                except Exception:
                    validated_results.append(program_data)

            return {
                "programs": validated_results,
                "total_found": len(validated_results),
                "search_method": "smart_search_v0.4.3",
                "fuzzy_matching": True,
            }
        else:
            # Fallback to legacy API - map final format to legacy format
            legacy_params = {
                "uni_adi": params.get("universite", ""),
                "program_adi": params.get("program", ""),
                "sehir_adi": params.get("sehir", ""),
                "puan_turu": params.get("puan_turu", "say"),
                "universite_turu": params.get("universite_turu", ""),
                "ucret_burs": params.get("ucret", ""),
                "ogretim_turu": params.get("ogretim_turu", ""),
                "page": 1,
            }

            legacy_params = {k: v for k, v in legacy_params.items() if v}

            lisans_tercih = YOKATLASLisansTercihSihirbazi(legacy_params)
            result = lisans_tercih.search()

            results_limit = params.get("length", 50)
            return {
                "programs": (
                    result[:results_limit] if isinstance(result, list) else result
                ),
                "total_found": len(result) if isinstance(result, list) else 0,
                "search_method": "legacy_api",
                "fuzzy_matching": False,
            }

    except Exception as e:
        return {
            "error": str(e),
            "search_method": "smart_search" if NEW_SMART_API else "legacy_api",
            "parameters_used": params,
        }


def search_associate_degree_programs(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for associate degree programs with smart fuzzy matching."""
    if not YOKATLAS_AVAILABLE:
        return get_module_unavailable_error("search_associate_degree_programs")

    try:
        if NEW_SMART_API:
            # Parameters are already in final format from TypeScript side
            # No mapping needed - pass directly to search function
            results = search_onlisans_programs(params, smart_search=True)

            return {
                "programs": results,
                "total_found": len(results),
                "search_method": "smart_search_v0.4.3",
                "fuzzy_matching": True,
                "program_type": "associate_degree",
            }
        else:
            # Fallback to legacy API - map final format to legacy format
            legacy_params = {
                "yop_kodu": "",
                "uni_adi": params.get("universite", ""),
                "program_adi": params.get("program", ""),
                "sehir_adi": params.get("sehir", ""),
                "universite_turu": params.get("universite_turu", ""),
                "ucret_burs": params.get("ucret", ""),
                "ogretim_turu": params.get("ogretim_turu", ""),
                "doluluk": params.get("doluluk", ""),
                "ust_puan": 550.0,
                "alt_puan": 150.0,
                "page": 1,
            }

            legacy_params = {
                k: v
                for k, v in legacy_params.items()
                if v or isinstance(v, (int, float))
            }

            onlisans_tercih = YOKATLASOnlisansTercihSihirbazi(legacy_params)
            result = onlisans_tercih.search()

            results_limit = params.get("length", 50)
            return {
                "programs": (
                    result[:results_limit] if isinstance(result, list) else result
                ),
                "total_found": len(result) if isinstance(result, list) else 0,
                "search_method": "legacy_api",
                "fuzzy_matching": False,
                "program_type": "associate_degree",
            }

    except Exception as e:
        return {
            "error": str(e),
            "search_method": "smart_search" if NEW_SMART_API else "legacy_api",
            "parameters_used": params,
            "program_type": "associate_degree",
        }


async def main():
    """Main entry point for the helper script."""
    log_to_file(f"Starting with {len(sys.argv)} arguments", "DEBUG")

    if len(sys.argv) < 2:
        print(json.dumps({"error": "No function specified"}))
        sys.exit(1)

    function_name = sys.argv[1]
    log_to_file(f"Function: {function_name}", "DEBUG")

    if len(sys.argv) > 2:
        try:
            params = json.loads(sys.argv[2])
            log_to_file(f"Parsed params: {json.dumps(params)}", "DEBUG")
        except json.JSONDecodeError as e:
            log_to_file(f"JSON decode error: {e}", "ERROR")
            print(json.dumps({"error": "Invalid JSON parameters"}))
            sys.exit(1)
    else:
        params = {}
        log_to_file(f"No params provided", "DEBUG")

    try:
        log_to_file(f"Calling function: {function_name}", "INFO")

        if function_name == "health_check":
            result = await health_check()
        elif function_name == "get_associate_degree_atlas_details":
            result = await get_associate_degree_atlas_details(
                params["yop_kodu"], params["year"]
            )
        elif function_name == "get_bachelor_degree_atlas_details":
            result = await get_bachelor_degree_atlas_details(
                params["yop_kodu"], params["year"]
            )
        elif function_name == "search_bachelor_degree_programs":
            log_to_file(
                f"Calling search_bachelor_degree_programs with: {params}", "DEBUG"
            )
            result = search_bachelor_degree_programs(params)
            log_to_file(
                f"Got result type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}",
                "DEBUG",
            )
        elif function_name == "search_associate_degree_programs":
            log_to_file(
                f"Calling search_associate_degree_programs with: {params}", "DEBUG"
            )
            result = search_associate_degree_programs(params)
            log_to_file(
                f"Got result type: {type(result)}, keys: {list(result.keys()) if isinstance(result, dict) else 'not dict'}",
                "DEBUG",
            )
        else:
            result = {"error": f"Unknown function: {function_name}"}

        log_to_file(f"About to print result: {json.dumps(result)[:100]}...", "DEBUG")
        print(json.dumps(result))
        log_to_file(f"Result printed successfully", "DEBUG")

    except Exception as e:
        log_to_file(f"Exception occurred: {e}", "ERROR")
        log_to_file(f"Exception type: {type(e)}", "ERROR")
        import traceback

        log_to_file(f"Traceback: {traceback.format_exc()}", "ERROR")
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
