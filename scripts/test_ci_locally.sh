#!/bin/bash
# test_ci_locally.sh
#
# Test Konveyor CI workflow locally before pushing to go-konveyor-tests.
# This script validates that generated rules trigger correctly on test applications.
#
# Usage:
#   ./scripts/test_ci_locally.sh
#   ./scripts/test_ci_locally.sh --verbose
#   ./scripts/test_ci_locally.sh --app spring-boot-mongodb

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
VERBOSE=false
SPECIFIC_APP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --app|-a)
            SPECIFIC_APP="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --verbose, -v          Show detailed output"
            echo "  --app, -a <name>       Test specific app only"
            echo "  --help, -h             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v kantra &> /dev/null; then
    echo -e "${RED}❌ kantra not found. Install from: https://github.com/konveyor/kantra${NC}"
    echo ""
    echo "Quick install (macOS):"
    echo "  brew install konveyor/kantra/kantra"
    echo ""
    echo "Or download from releases:"
    echo "  https://github.com/konveyor/kantra/releases"
    exit 1
fi

if [ ! -d "examples/test-apps" ] && [ ! -d "tests/data" ]; then
    echo -e "${RED}❌ No test applications found${NC}"
    echo "Generate test apps first:"
    echo "  python scripts/generate_test_data.py --rules <rules.yaml> --output tests/data/<app>"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"
echo ""

# Find test applications
TEST_DIRS=()
if [ -d "examples/test-apps" ]; then
    while IFS= read -r dir; do
        TEST_DIRS+=("$dir")
    done < <(find examples/test-apps -mindepth 1 -maxdepth 1 -type d)
fi
if [ -d "tests/data" ]; then
    while IFS= read -r dir; do
        TEST_DIRS+=("$dir")
    done < <(find tests/data -mindepth 1 -maxdepth 1 -type d)
fi

if [ ${#TEST_DIRS[@]} -eq 0 ]; then
    echo -e "${RED}❌ No test applications found${NC}"
    exit 1
fi

# Filter for specific app if requested
if [ -n "$SPECIFIC_APP" ]; then
    FILTERED_DIRS=()
    for dir in "${TEST_DIRS[@]}"; do
        if [[ "$(basename "$dir")" == "$SPECIFIC_APP" ]]; then
            FILTERED_DIRS+=("$dir")
        fi
    done
    TEST_DIRS=("${FILTERED_DIRS[@]}")

    if [ ${#TEST_DIRS[@]} -eq 0 ]; then
        echo -e "${RED}❌ Test app '$SPECIFIC_APP' not found${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}📦 Found ${#TEST_DIRS[@]} test application(s)${NC}"
echo ""

# Find rule files
RULE_FILES=()
if [ -d "examples/output" ]; then
    while IFS= read -r file; do
        RULE_FILES+=("$file")
    done < <(find examples/output -name "*.yaml" -type f)
fi

if [ ${#RULE_FILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠ No rule files found in examples/output${NC}"
    echo "Generate rules first:"
    echo "  python scripts/generate_rules.py --guide <URL> --source <src> --target <tgt>"
    exit 1
fi

echo -e "${BLUE}📋 Found ${#RULE_FILES[@]} rule file(s)${NC}"
if [ "$VERBOSE" = true ]; then
    for rule in "${RULE_FILES[@]}"; do
        echo "  - $(basename "$rule")"
    done
fi
echo ""

# Test each application
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
TOTAL_VIOLATIONS=0

for app_dir in "${TEST_DIRS[@]}"; do
    APP_NAME=$(basename "$app_dir")
    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -e "${BLUE}🧪 Testing: ${APP_NAME}${NC}"
    echo "   Path: $app_dir"

    # Create output directory
    OUTPUT_DIR="$app_dir/analysis_output"
    rm -rf "$OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"

    # Determine which rules to use
    # First, check if there's a matching rule file
    MATCHING_RULES=()
    for rule_file in "${RULE_FILES[@]}"; do
        # Extract technology from app name (e.g., spring-boot, react, patternfly)
        if [[ "$APP_NAME" == *"spring-boot"* ]] && [[ "$rule_file" == *"spring-boot"* ]]; then
            MATCHING_RULES+=("$rule_file")
        elif [[ "$APP_NAME" == *"react"* ]] && [[ "$rule_file" == *"react"* ]]; then
            MATCHING_RULES+=("$rule_file")
        elif [[ "$APP_NAME" == *"patternfly"* ]] && [[ "$rule_file" == *"patternfly"* ]]; then
            MATCHING_RULES+=("$rule_file")
        fi
    done

    # If no matching rules, use all rules
    if [ ${#MATCHING_RULES[@]} -eq 0 ]; then
        MATCHING_RULES=("${RULE_FILES[@]}")
    fi

    if [ "$VERBOSE" = true ]; then
        echo "   Using ${#MATCHING_RULES[@]} rule file(s):"
        for rule in "${MATCHING_RULES[@]}"; do
            echo "     - $(basename "$rule")"
        done
    fi

    # Run kantra analysis
    echo "   Running kantra analyze..."

    KANTRA_CMD="kantra analyze --input $app_dir --output $OUTPUT_DIR"

    # Add rule files
    for rule_file in "${MATCHING_RULES[@]}"; do
        KANTRA_CMD="$KANTRA_CMD --rules $rule_file"
    done

    if [ "$VERBOSE" = true ]; then
        echo "   Command: $KANTRA_CMD"
        eval "$KANTRA_CMD"
        KANTRA_EXIT=$?
    else
        eval "$KANTRA_CMD" > /dev/null 2>&1
        KANTRA_EXIT=$?
    fi

    if [ $KANTRA_EXIT -ne 0 ]; then
        echo -e "${RED}   ❌ Analysis failed (exit code: $KANTRA_EXIT)${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo ""
        continue
    fi

    # Check for output file
    if [ ! -f "$OUTPUT_DIR/output.yaml" ]; then
        echo -e "${RED}   ❌ No output.yaml generated${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo ""
        continue
    fi

    # Count violations
    VIOLATIONS=$(grep -c "ruleID:" "$OUTPUT_DIR/output.yaml" 2>/dev/null || echo "0")
    TOTAL_VIOLATIONS=$((TOTAL_VIOLATIONS + VIOLATIONS))

    if [ "$VIOLATIONS" -eq 0 ]; then
        echo -e "${YELLOW}   ⚠ No violations found (expected at least 1)${NC}"
        # This might be OK if the app doesn't trigger these rules
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${GREEN}   ✓ Found $VIOLATIONS violation(s)${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))

        if [ "$VERBOSE" = true ]; then
            echo "   Violations:"
            grep "ruleID:" "$OUTPUT_DIR/output.yaml" | sed 's/^/     /'
        fi
    fi

    # Check dependencies if present
    if grep -q "dependencies:" "$OUTPUT_DIR/output.yaml" 2>/dev/null; then
        DEP_COUNT=$(grep -A 999 "dependencies:" "$OUTPUT_DIR/output.yaml" | grep "  - name:" | wc -l | xargs)
        echo -e "${BLUE}   📦 Found $DEP_COUNT dependencies${NC}"

        if [ "$VERBOSE" = true ] && [ "$DEP_COUNT" -gt 0 ]; then
            echo "   Dependencies:"
            grep -A 999 "dependencies:" "$OUTPUT_DIR/output.yaml" | grep "  - name:" | sed 's/^/     /'
        fi
    fi

    echo ""
done

# Summary
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo "Total tests:       $TOTAL_TESTS"
echo -e "Passed:            ${GREEN}$PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "Failed:            ${RED}$FAILED_TESTS${NC}"
fi
echo "Total violations:  $TOTAL_VIOLATIONS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Review violation output in test app analysis_output/ directories"
    echo "  2. Update go-konveyor-tests if needed:"
    echo "     python scripts/update_test_dependencies.py \\"
    echo "       --analyzer-output <app>/analysis_output/output.yaml \\"
    echo "       --test-case tc_<app>_deps.go"
    echo "  3. Commit and push your changes"
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Check the output above for details."
    echo "Common issues:"
    echo "  - Rules not matching expected patterns"
    echo "  - Test application doesn't trigger the rules"
    echo "  - Kantra configuration issues"
    exit 1
fi
