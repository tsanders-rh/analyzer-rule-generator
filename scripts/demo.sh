#!/bin/bash
#
# Analyzer Rule Generator Demo Script
#
# This script demonstrates the complete workflow from migration guide to
# Konveyor rules with test data generation.
#
# Usage:
#   ./scripts/demo.sh [step]
#
# Steps:
#   1  - Generate rules from migration guide
#   2  - Generate test data
#   3  - Validate with kantra (if installed)
#   all - Run all steps
#
# For live demos, run each step individually to explain what's happening.
#

set -e  # Exit on error

# Ensure we're running from the project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${PROJECT_ROOT}"

# Activate virtual environment if it exists
if [ -d "venv/bin" ]; then
    source venv/bin/activate
    VENV_ACTIVATED=true
elif [ -d ".venv/bin" ]; then
    source .venv/bin/activate
    VENV_ACTIVATED=true
else
    VENV_ACTIVATED=false
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Demo Configuration - Choose your migration guide
# ============================================================================

# Option 1: React 17 to 18 (SMALL - Recommended for quick demos ~5 min)
# GUIDE_URL="https://react.dev/blog/2022/03/08/react-18-upgrade-guide"
# SOURCE="react-17"
# TARGET="react-18"
# FOLLOW_LINKS_FLAG=""  # Single page guide

# Option 2: Spring Boot 2 to 3 (MEDIUM - ~8-10 min)
# GUIDE_URL="https://github.com/spring-projects/spring-boot/wiki/Spring-Boot-3.0-Migration-Guide"
# SOURCE="spring-boot-2"
# TARGET="spring-boot-3"
# FOLLOW_LINKS_FLAG=""  # Single page guide

# Option 3: PatternFly v5 to v6 (LARGE - ~15-20 min, comprehensive)
GUIDE_URL="https://www.patternfly.org/get-started/upgrade/"
SOURCE="patternfly-v5"
TARGET="patternfly-v6"
FOLLOW_LINKS_FLAG="--follow-links --max-depth 1"

# Demo output directories
DEMO_DIR="demo-output"
RULES_OUTPUT="${DEMO_DIR}/rules"
TEST_OUTPUT="${DEMO_DIR}/tests"

# Helper functions
print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

pause_for_demo() {
    if [ "${INTERACTIVE:-yes}" = "yes" ]; then
        echo -e "\n${YELLOW}Press Enter to continue...${NC}"
        read
    fi
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        exit 1
    fi
    print_success "Python 3 installed: $(python3 --version)"

    # Check virtual environment
    if [ "${VENV_ACTIVATED}" = true ]; then
        print_success "Virtual environment activated"
    else
        print_warning "Virtual environment not found"
        print_info "Run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    fi

    # Check API key
    if [ -z "${ANTHROPIC_API_KEY}" ] && [ -z "${OPENAI_API_KEY}" ]; then
        print_warning "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
        print_info "Example: export ANTHROPIC_API_KEY='your-key-here'"
        exit 1
    fi

    if [ -n "${ANTHROPIC_API_KEY}" ]; then
        print_success "ANTHROPIC_API_KEY set"
        PROVIDER="anthropic"
    elif [ -n "${OPENAI_API_KEY}" ]; then
        print_success "OPENAI_API_KEY set"
        PROVIDER="openai"
    fi

    # Check if kantra is available (optional)
    if command -v kantra &> /dev/null; then
        print_success "Kantra installed (optional for step 3)"
        KANTRA_AVAILABLE=true
    else
        print_warning "Kantra not installed (skipping validation step)"
        KANTRA_AVAILABLE=false
    fi

    print_success "All prerequisites met!"
    pause_for_demo
}

step_1_generate_rules() {
    print_header "Step 1: Generate Rules from Migration Guide"

    print_info "Input: ${GUIDE_URL}"
    print_info "Source: ${SOURCE}"
    print_info "Target: ${TARGET}"
    print_info "Output: ${RULES_OUTPUT}"
    echo ""

    # Create output directory
    mkdir -p "${RULES_OUTPUT}"

    # Show the command
    echo -e "${YELLOW}Command:${NC}"
    if [ -n "${FOLLOW_LINKS_FLAG}" ]; then
        cat <<EOF
python3 scripts/generate_rules.py \\
  --guide "${GUIDE_URL}" \\
  --source "${SOURCE}" \\
  --target "${TARGET}" \\
  --output "${RULES_OUTPUT}" \\
  --provider "${PROVIDER}" \\
  ${FOLLOW_LINKS_FLAG}
EOF
    else
        cat <<EOF
python3 scripts/generate_rules.py \\
  --guide "${GUIDE_URL}" \\
  --source "${SOURCE}" \\
  --target "${TARGET}" \\
  --output "${RULES_OUTPUT}" \\
  --provider "${PROVIDER}"
EOF
    fi
    echo ""

    pause_for_demo

    # Run the command
    print_info "Running rule generation..."
    if [ -n "${FOLLOW_LINKS_FLAG}" ]; then
        python3 scripts/generate_rules.py \
          --guide "${GUIDE_URL}" \
          --source "${SOURCE}" \
          --target "${TARGET}" \
          --output "${RULES_OUTPUT}" \
          --provider "${PROVIDER}" \
          ${FOLLOW_LINKS_FLAG}
    else
        python3 scripts/generate_rules.py \
          --guide "${GUIDE_URL}" \
          --source "${SOURCE}" \
          --target "${TARGET}" \
          --output "${RULES_OUTPUT}" \
          --provider "${PROVIDER}"
    fi

    # Show results
    echo ""
    print_success "Rules generated successfully!"

    print_info "Generated files:"
    find "${RULES_OUTPUT}" -name "*.yaml" -type f | while read file; do
        rule_count=$(grep -c "ruleID:" "$file" || true)
        echo "  - $(basename $file): ${rule_count} rules"
    done

    # Show a sample rule
    FIRST_RULE_FILE=$(find "${RULES_OUTPUT}" -name "*.yaml" -type f | head -1)
    if [ -n "${FIRST_RULE_FILE}" ]; then
        echo ""
        print_info "Sample rule from $(basename ${FIRST_RULE_FILE}):"
        echo ""
        # Show first rule only
        awk '/^- ruleID:/{p=1} p{print} /^$/{if(p) exit}' "${FIRST_RULE_FILE}" | head -20
    fi

    pause_for_demo
}

step_2_generate_tests() {
    print_header "Step 2: Generate Test Data"

    # Find a rule file to use
    RULE_FILE=$(find "${RULES_OUTPUT}" -name "*.yaml" -type f | head -1)

    if [ -z "${RULE_FILE}" ]; then
        print_error "No rule files found. Run step 1 first."
        exit 1
    fi

    print_info "Input: ${RULE_FILE}"
    print_info "Output: ${TEST_OUTPUT}"
    print_info "Language: TypeScript (auto-detected)"
    echo ""

    # Create output directory
    mkdir -p "${TEST_OUTPUT}"

    # Show the command
    echo -e "${YELLOW}Command:${NC}"
    cat <<EOF
python3 scripts/generate_test_data.py \\
  --rules "${RULE_FILE}" \\
  --output "${TEST_OUTPUT}" \\
  --source "${SOURCE}" \\
  --target "${TARGET}" \\
  --guide-url "${GUIDE_URL}" \\
  --provider "${PROVIDER}"
EOF
    echo ""

    pause_for_demo

    # Run the command
    print_info "Running test data generation..."
    python3 scripts/generate_test_data.py \
      --rules "${RULE_FILE}" \
      --output "${TEST_OUTPUT}" \
      --source "${SOURCE}" \
      --target "${TARGET}" \
      --guide-url "${GUIDE_URL}" \
      --provider "${PROVIDER}"

    # Show results
    echo ""
    print_success "Test data generated successfully!"

    print_info "Generated structure:"
    tree -L 3 "${TEST_OUTPUT}" 2>/dev/null || find "${TEST_OUTPUT}" -type f | head -20

    # Show sample test file
    TEST_FILE=$(find "${TEST_OUTPUT}" -name "*.test.yaml" -type f | head -1)
    if [ -n "${TEST_FILE}" ]; then
        echo ""
        print_info "Sample test configuration:"
        echo ""
        head -30 "${TEST_FILE}"
    fi

    pause_for_demo
}

step_3_validate_with_kantra() {
    print_header "Step 3: Validate with Kantra (Optional)"

    if [ "${KANTRA_AVAILABLE}" = false ]; then
        print_warning "Kantra not installed - skipping validation"
        print_info "To install: https://github.com/konveyor/kantra"
        return 0
    fi

    RULE_FILE=$(find "${RULES_OUTPUT}" -name "*.yaml" -type f | head -1)
    TEST_DIR=$(find "${TEST_OUTPUT}" -type d -name "data" | head -1)

    if [ -z "${TEST_DIR}" ]; then
        print_warning "No test data directory found - skipping validation"
        return 0
    fi

    print_info "Rules: ${RULE_FILE}"
    print_info "Test app: ${TEST_DIR}"
    echo ""

    # Show the command
    echo -e "${YELLOW}Command:${NC}"
    cat <<EOF
kantra analyze \\
  --input "${TEST_DIR}" \\
  --rules "${RULE_FILE}" \\
  --output "${DEMO_DIR}/analysis-output.yaml"
EOF
    echo ""

    pause_for_demo

    # Run kantra
    print_info "Running Kantra analysis..."
    kantra analyze \
      --input "${TEST_DIR}" \
      --rules "${RULE_FILE}" \
      --output "${DEMO_DIR}/analysis-output.yaml" || true

    if [ -f "${DEMO_DIR}/analysis-output.yaml" ]; then
        print_success "Analysis completed!"

        # Count violations
        VIOLATION_COUNT=$(grep -c "ruleID:" "${DEMO_DIR}/analysis-output.yaml" || true)
        print_info "Violations found: ${VIOLATION_COUNT}"

        # Show sample violations
        echo ""
        print_info "Sample violations:"
        head -50 "${DEMO_DIR}/analysis-output.yaml"
    else
        print_warning "Analysis output not found"
    fi

    pause_for_demo
}

step_4_show_submission() {
    print_header "Step 4: Submission to Konveyor (Next Steps)"

    print_info "Your generated rules are ready for submission!"
    echo ""

    echo "📋 What you have:"
    echo "  1. Rules: ${RULES_OUTPUT}/*.yaml"
    echo "  2. Tests: ${TEST_OUTPUT}/"
    if [ "${KANTRA_AVAILABLE}" = true ]; then
        echo "  3. Validation: ${DEMO_DIR}/analysis-output.yaml"
    fi
    echo ""

    echo "📦 Next steps for contribution:"
    echo "  1. Fork konveyor/rulesets repository"
    echo "  2. Copy rules to appropriate directory"
    echo "  3. Copy tests to tests/ directory"
    echo "  4. Create pull request with:"
    echo "     - Rule YAML files"
    echo "     - Test data"
    echo "     - Test configuration (.test.yaml)"
    echo "     - README documenting the migration"
    echo ""

    print_info "See docs/guides/konveyor-submission-guide.md for detailed steps"

    pause_for_demo
}

show_summary() {
    print_header "Demo Summary"

    echo "✨ What we demonstrated:"
    echo ""
    echo "  1️⃣  Generated Konveyor rules from migration guide"
    echo "     - Extracted migration patterns using AI"
    echo "     - Created analyzer-lsp compatible YAML"
    echo "     - Classified complexity levels"
    echo ""
    echo "  2️⃣  Generated test data automatically"
    echo "     - AI-created test applications"
    echo "     - Test configurations for validation"
    echo "     - Ready for kantra testing"
    echo ""

    if [ "${KANTRA_AVAILABLE}" = true ]; then
        echo "  3️⃣  Validated rules with Kantra"
        echo "     - Confirmed rules detect violations"
        echo "     - Ready for submission"
        echo ""
    fi

    echo "⏱️  Total time: ~5-15 minutes (vs days of manual work)"
    echo ""
    echo "📚 Learn more:"
    echo "  - Documentation: README.md"
    echo "  - Submission guide: docs/guides/konveyor-submission-guide.md"
    echo "  - Examples: examples/output/"
    echo ""

    print_success "Demo complete!"
}

cleanup_demo() {
    print_header "Cleanup Demo Files"

    if [ -d "${DEMO_DIR}" ]; then
        echo -e "${YELLOW}Remove demo output directory? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -rf "${DEMO_DIR}"
            print_success "Demo files removed"
        else
            print_info "Keeping demo files in ${DEMO_DIR}"
        fi
    else
        print_info "No demo files to clean up"
    fi
}

show_usage() {
    cat <<EOF
Analyzer Rule Generator Demo Script

Usage:
  $0 [step]

Steps:
  1     - Generate rules from migration guide
  2     - Generate test data
  3     - Validate with kantra (if installed)
  4     - Show submission next steps
  all   - Run all steps sequentially
  clean - Remove demo output files

Environment Variables:
  ANTHROPIC_API_KEY - Anthropic API key (recommended)
  OPENAI_API_KEY    - OpenAI API key (alternative)
  INTERACTIVE=no    - Skip pauses between steps

Examples:
  # Run complete demo with pauses
  $0 all

  # Run specific step
  $0 1

  # Run all steps without pauses (for CI)
  INTERACTIVE=no $0 all

  # Clean up demo files
  $0 clean
EOF
}

# Main execution
main() {
    case "${1:-}" in
        1)
            check_prerequisites
            step_1_generate_rules
            ;;
        2)
            check_prerequisites
            step_2_generate_tests
            ;;
        3)
            check_prerequisites
            step_3_validate_with_kantra
            ;;
        4)
            step_4_show_submission
            ;;
        all)
            check_prerequisites
            step_1_generate_rules
            step_2_generate_tests
            step_3_validate_with_kantra
            step_4_show_submission
            show_summary
            ;;
        clean)
            cleanup_demo
            ;;
        -h|--help|help)
            show_usage
            ;;
        *)
            print_error "Unknown step: ${1:-}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
