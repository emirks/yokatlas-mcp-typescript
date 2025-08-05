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

# Import the local search functions
try:
    from yokatlas_py.local_search_wrappers import (
        search_local_lisans_programs,
        search_local_onlisans_programs,
    )
    from yokatlas_py import YOKATLASLisansAtlasi, YOKATLASOnlisansAtlasi
    from yokatlas_py.models import ProgramInfo

    YOKATLAS_AVAILABLE = True
    log_to_file("LOCAL SEARCH API loaded successfully", "INFO")
except ImportError as e:
    YOKATLAS_AVAILABLE = False
    log_to_file(f"Failed to load yokatlas_py local search: {e}", "ERROR")


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
        "status": "healthy" if YOKATLAS_AVAILABLE else "error",
        "server": "YOKATLAS Local Search Server",
        "api_version": "v2.0",
        "search_method": "local_search_only",
        "yokatlas_available": YOKATLAS_AVAILABLE,
        "message": (
            "Local search operational - using cached JSON data"
            if YOKATLAS_AVAILABLE
            else "yokatlas_py local search module not available - install required"
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
        # Check if sıralama filtering is requested
        siralama = params.get("siralama") or params.get("sıralama")
        if siralama:
            log_to_file(
                f"Using sıralama filtering with target ranking: {siralama}", "INFO"
            )

        # Use local search with bell curve sampling
        max_results = params.get("max_results", 100)
        if siralama:
            # When siralama is used, we want more results for bell curve sampling
            max_results = min(max_results, 200)  # Cap to prevent memory issues

        search_result = search_local_lisans_programs(
            params, smart_search=True, max_results=max_results, return_formatted=True
        )

        # Return just the formatted string for clean output
        formatted_output = search_result["formatted"]

        # Add search method info at the end
        method_info = (
            f"\n\n🔍 Search method: Local search v2.0 with bell curve sampling"
        )
        if siralama:
            method_info += f" (centered at ranking {siralama})"
        method_info += f"\n📊 Total found: {search_result['total_found']} programs"

        return formatted_output + method_info

    except Exception as e:
        return {
            "error": str(e),
            "search_method": "local_search_v2.0",
            "parameters_used": params,
        }


def search_associate_degree_programs(params: Dict[str, Any]) -> Dict[str, Any]:
    """Search for associate degree programs using local data with bell curve sampling."""
    if not YOKATLAS_AVAILABLE:
        return get_module_unavailable_error("search_associate_degree_programs")

    try:
        # Use local search with bell curve sampling
        max_results = params.get("max_results", 100)

        search_result = search_local_onlisans_programs(
            params, smart_search=True, max_results=max_results, return_formatted=True
        )

        # Return just the formatted string for clean output
        formatted_output = search_result["formatted"]

        # Add search method info at the end
        method_info = f"\n\n🔍 Search method: Local search v2.0 with bell curve sampling (Associate Degree)"
        method_info += f"\n📊 Total found: {search_result['total_found']} programs"

        return formatted_output + method_info

    except Exception as e:
        return {
            "error": str(e),
            "search_method": "local_search_v2.0",
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
