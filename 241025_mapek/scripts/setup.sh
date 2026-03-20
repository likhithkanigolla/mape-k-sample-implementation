#!/bin/bash

# Complete IoT MAPE-K System Setup Script
# This script will guide you through the entire setup process

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   IoT MAPE-K System - Complete Setup                          ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo ""

# Step 1: Check Python
echo -e "${YELLOW}Step 1: Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Step 2: Check PostgreSQL
echo -e "\n${YELLOW}Step 2: Checking PostgreSQL installation...${NC}"
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version)
    echo -e "${GREEN}✓ PostgreSQL found: $PSQL_VERSION${NC}"
else
    echo -e "${RED}✗ PostgreSQL not found. Please install PostgreSQL.${NC}"
    echo -e "${YELLOW}  Install with: brew install postgresql (macOS)${NC}"
    exit 1
fi

# Step 3: Install Python dependencies
echo -e "\n${YELLOW}Step 3: Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found${NC}"
    exit 1
fi

# Step 4: Database setup
echo -e "\n${YELLOW}Step 4: Database Setup${NC}"
echo -e "${BLUE}This will create the database 'mapek_dt' and all required tables.${NC}"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if database exists
    if psql -U postgres -lqt | cut -d \| -f 1 | grep -qw mapek_dt; then
        echo -e "${YELLOW}⚠️  Database 'mapek_dt' already exists${NC}"
        read -p "Drop and recreate? This will DELETE all data! (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            dropdb -U postgres mapek_dt
            createdb -U postgres mapek_dt
            echo -e "${GREEN}✓ Database recreated${NC}"
        fi
    else
        createdb -U postgres mapek_dt
        echo -e "${GREEN}✓ Database created${NC}"
    fi
    
    # Run setup script
    if [ -f "setup_complete_database.sql" ]; then
        psql -U postgres -d mapek_dt -f setup_complete_database.sql
        echo -e "${GREEN}✓ All database tables created${NC}"
    else
        echo -e "${RED}✗ setup_complete_database.sql not found${NC}"
        exit 1
    fi

    # Create knowledge base views
    if [ -f "setup_knowledge_base.sql" ]; then
        psql -U postgres -d mapek_dt -f setup_knowledge_base.sql
        echo -e "${GREEN}✓ Knowledge base views created${NC}"
    else
        echo -e "${RED}✗ setup_knowledge_base.sql not found${NC}"
        exit 1
    fi

    # Create knowledge base views
    if [ -f "setup_iot_gateway_views.sql" ]; then
        psql -U postgres -d mapek_dt -f setup_iot_gateway_views.sql
        echo -e "${GREEN}✓ IoT Gateway views created${NC}"
    else
        echo -e "${RED}✗ setup_iot_gateway_views.sql not found${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  Skipping database setup${NC}"
fi

# Step 5: Verify configuration
echo -e "\n${YELLOW}Step 5: Verifying configuration...${NC}"

# Check knowledge.py database config
if grep -q "database.*mapek_dt" plain_mapek/knowledge.py; then
    echo -e "${GREEN}✓ MAPE-K database config correct${NC}"
else
    echo -e "${YELLOW}⚠️  MAPE-K may need database config update in plain_mapek/knowledge.py${NC}"
fi

# Check iot_gateway.py database config
if grep -q "database.*mapek_dt" iot_gateway.py; then
    echo -e "${GREEN}✓ IoT Gateway database config correct${NC}"
else
    echo -e "${YELLOW}⚠️  IoT Gateway may need database config update in iot_gateway.py${NC}"
fi

# Step 6: Make scripts executable
echo -e "\n${YELLOW}Step 6: Making scripts executable...${NC}"
chmod +x scripts/start_iot_gateway.sh scripts/stop_iot_gateway.sh test_system.py
echo -e "${GREEN}✓ Scripts are executable${NC}"

# Step 7: Summary
echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Setup Complete!                                              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Your IoT MAPE-K system is ready!${NC}"
echo ""
echo -e "${YELLOW}Database Tables Created:${NC}"
echo "  ✓ 4 Sensor data tables (water_quality, water_level, water_flow, motor)"
echo "  ✓ 3 Configuration tables (nodes, thresholds, plans)"
echo "  ✓ 3 MAPE-K log tables (analyze, plan_selection, execution)"
echo "  ✓ 1 Gateway log table (execution_log)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo ""
echo -e "${BLUE}1. Start the IoT Gateway and Sensors:${NC}"
echo -e "   ${GREEN}./scripts/start_iot_gateway.sh${NC}"
echo ""
echo -e "${BLUE}2. In a new terminal, start the MAPE-K loop:${NC}"
echo -e "   ${GREEN}cd plain_mapek && python3 main.py${NC}"
echo ""
echo -e "${BLUE}3. Test the system:${NC}"
echo -e "   ${GREEN}python3 test_system.py${NC}"
echo ""
echo -e "${BLUE}4. Monitor the database:${NC}"
echo -e "   ${GREEN}psql -U postgres -d mapek_dt -c \"SELECT * FROM recent_executions;\"${NC}"
echo ""
echo -e "${BLUE}5. Stop everything:${NC}"
echo -e "   ${GREEN}./scripts/stop_iot_gateway.sh${NC}"
echo ""
echo -e "${YELLOW}Documentation:${NC}"
echo "  • DATABASE_SCHEMA.md - Complete database documentation"
echo "  • QUICKSTART_IOT_GATEWAY.md - Quick start guide"
echo "  • IOT_GATEWAY_README.md - Full technical documentation"
echo "  • ARCHITECTURE_FLOW.md - System architecture and flow"
echo ""
echo -e "${GREEN}Happy MAPE-K-ing! 🚀${NC}"
