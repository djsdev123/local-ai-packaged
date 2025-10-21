#!/bin/bash
# LAPTOP_SETUP.sh
# Run on MacBook

echo "=== LAPTOP SETUP (NordVPN Meshnet + Wake-on-LAN) ==="
echo ""

# Check if Homebrew installed (Mac)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # Install NordVPN
    if ! command -v nordvpn &> /dev/null; then
        echo "Installing NordVPN..."
        brew install --cask nordvpn
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SETUP STEPS:"
echo "1. Open NordVPN app"
echo "2. Login to your account"
echo "3. Connect to a VPN server (for public WiFi protection)"
echo "4. Go to Settings → Meshnet → Enable"
echo "5. Add your home PC to meshnet devices"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press Enter after you've completed these steps..."

echo ""
read -p "Enter your HOME PC meshnet address (from desktop file): " GPU_IP
echo ""

# Test connection
echo "Testing GPU connection..."
if curl -s --max-time 5 "http://${GPU_IP}:11434/api/tags" > /dev/null 2>&1; then
    echo "✅ SUCCESS! GPU accessible via meshnet!"
else
    echo "⚠️  GPU not responding (might be asleep)"
fi

# Install Ollama CLI
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama CLI..."
    brew install ollama
fi

# Install Open WebUI via Docker
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installing Open WebUI (Web Interface)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    brew install --cask docker
    echo ""
    echo "⚠️  IMPORTANT: Docker Desktop installed!"
    echo "   Please:"
    echo "   1. Open Docker Desktop from Applications"
    echo "   2. Wait for it to start (whale icon in menu bar)"
    echo "   3. Come back and press Enter"
    read -p "Press Enter after Docker Desktop is running..."
fi

# Wait for Docker to be ready
echo "Waiting for Docker to be ready..."
for i in {1..30}; do
    if docker info > /dev/null 2>&1; then
        echo "✅ Docker is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Docker not responding. Please start Docker Desktop manually."
        exit 1
    fi
    sleep 2
done

# Pull and run Open WebUI
echo "Setting up Open WebUI..."
docker pull ghcr.io/open-webui/open-webui:main

# Create Open WebUI start script
cat > ~/gpu-tools/start-webui << EOF
#!/bin/bash
# Start Open WebUI connected to GPU

GPU_URL="http://${GPU_IP}:11434"

echo "Starting Open WebUI connected to GPU..."
echo "GPU Server: \$GPU_URL"
echo ""

# Stop existing container if running
docker stop open-webui 2>/dev/null
docker rm open-webui 2>/dev/null

# Start Open WebUI
docker run -d \\
  --name open-webui \\
  -p 3000:8080 \\
  -e OLLAMA_BASE_URL=\$GPU_URL \\
  -v open-webui:/app/backend/data \\
  --restart unless-stopped \\
  ghcr.io/open-webui/open-webui:main

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Open WebUI Started!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Open in browser: http://localhost:3000"
echo ""
echo "GPU Server: \$GPU_URL"
echo ""
echo "Opening browser in 3 seconds..."
sleep 3
open "http://localhost:3000"
EOF

chmod +x ~/gpu-tools/start-webui

# Start Open WebUI now
~/gpu-tools/start-webui

# Create wake utility directory
mkdir -p ~/gpu-tools

# Create the wake utility with status monitoring
cat > ~/gpu-tools/gpu-wake << 'EOFWAKE'
#!/bin/bash
# GPU Wake & Status Tool

GPU_IP="GPU_IP_PLACEHOLDER"
WAKE_PORT=9999
OLLAMA_PORT=11434

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
GPU Wake & Status Tool

Usage:
  gpu-wake status      Show current GPU status
  gpu-wake wake        Wake up the GPU server
  gpu-wake test        Test GPU connection
  gpu-wake troubleshoot Run diagnostics
  gpu-wake help        Show this help

Examples:
  gpu-wake status
  gpu-wake wake
EOF
}

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

check_status() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  GPU STATUS CHECK${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Check wake service
    echo -n "Wake Service:  "
    if response=$(curl -s --max-time 3 "http://${GPU_IP}:${WAKE_PORT}/status" 2>/dev/null); then
        echo -e "${GREEN}✅ ONLINE${NC}"

        # Parse response
        if echo "$response" | grep -q "awake"; then
            echo -e "Status:        ${GREEN}AWAKE${NC}"

            # Check if Ollama is running
            if echo "$response" | grep -q '"ollama_running": true'; then
                echo -e "Ollama:        ${GREEN}✅ RUNNING${NC}"

                # Test Ollama
                echo -n "GPU Ready:     "
                if curl -s --max-time 3 "http://${GPU_IP}:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
                    echo -e "${GREEN}✅ READY FOR INFERENCE${NC}"
                else
                    echo -e "${YELLOW}⚠️  Ollama starting...${NC}"
                fi
            else
                echo -e "Ollama:        ${YELLOW}⏳ STARTING${NC}"
            fi
        fi
    else
        echo -e "${RED}❌ OFFLINE (sleeping or unreachable)${NC}"
        echo ""
        echo "Try: gpu-wake wake"
        return 1
    fi

    echo ""
    echo -e "GPU URL: ${BLUE}http://${GPU_IP}:${OLLAMA_PORT}${NC}"
}

wake_gpu() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  WAKING GPU SERVER${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # First check if already awake
    if curl -s --max-time 2 "http://${GPU_IP}:${WAKE_PORT}/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ GPU is already awake!${NC}"
        check_status
        return 0
    fi

    echo -e "${YELLOW}⏳ Sending wake signal...${NC}"

    # Send wake signal
    if curl -s --max-time 5 "http://${GPU_IP}:${WAKE_PORT}/wake" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Wake signal sent${NC}"
    else
        echo -e "${YELLOW}⏳ PC may be sleeping, trying to wake...${NC}"
    fi

    # Monitor wake progress
    echo ""
    echo "Waiting for GPU to respond..."

    for i in {1..30}; do
        if curl -s --max-time 2 "http://${GPU_IP}:${WAKE_PORT}/status" > /dev/null 2>&1; then
            echo -e "\n${GREEN}✅ GPU is awake!${NC}"
            echo ""

            # Wait a bit for Ollama
            echo "Starting Ollama service..."
            sleep 5

            check_status
            return 0
        fi

        printf "."
        sleep 1
    done

    echo -e "\n${RED}❌ GPU did not respond${NC}"
    echo ""
    echo "Possible issues:"
    echo "  • PC is off (not sleeping)"
    echo "  • NordVPN/Meshnet not running on home PC"
    echo "  • Network connectivity issue"
    echo ""
    echo "Try: gpu-wake troubleshoot"
    return 1
}

test_connection() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  CONNECTION TEST${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Test basic connectivity
    echo -n "Ping GPU:      "
    if ping -c 1 -W 2 "${GPU_IP}" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ REACHABLE${NC}"
    else
        echo -e "${RED}❌ NO RESPONSE${NC}"
    fi

    # Test wake service
    echo -n "Wake Service:  "
    if curl -s --max-time 3 "http://${GPU_IP}:${WAKE_PORT}/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ RESPONDING${NC}"
    else
        echo -e "${RED}❌ NOT RESPONDING${NC}"
    fi

    # Test Ollama
    echo -n "Ollama API:    "
    if curl -s --max-time 3 "http://${GPU_IP}:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ READY${NC}"
    else
        echo -e "${RED}❌ NOT READY${NC}"
    fi
}

troubleshoot() {
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  TROUBLESHOOTER${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    # Check NordVPN status
    echo -e "${BLUE}[1/5] Checking NordVPN status...${NC}"
    if command -v nordvpn &> /dev/null; then
        if nordvpn status | grep -q "Connected"; then
            echo -e "   ${GREEN}✅ NordVPN connected${NC}"
            nordvpn status | grep "Country" | sed 's/^/   /'
        else
            echo -e "   ${RED}❌ NordVPN not connected${NC}"
            echo "   Fix: Open NordVPN and connect to a server"
        fi
    else
        echo -e "   ${RED}❌ NordVPN not installed${NC}"
    fi
    echo ""

    # Check meshnet
    echo -e "${BLUE}[2/5] Checking Meshnet...${NC}"
    if nordvpn meshnet peer list 2>/dev/null | grep -q "${GPU_IP}"; then
        echo -e "   ${GREEN}✅ Meshnet peer found${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Cannot verify meshnet peers${NC}"
        echo "   Check: NordVPN app → Meshnet"
    fi
    echo ""

    # Check network connectivity
    echo -e "${BLUE}[3/5] Testing network connectivity...${NC}"
    if ping -c 1 -W 3 "${GPU_IP}" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Can reach ${GPU_IP}${NC}"
    else
        echo -e "   ${RED}❌ Cannot reach ${GPU_IP}${NC}"
        echo "   Possible causes:"
        echo "     • Home PC is off"
        echo "     • Meshnet not configured"
        echo "     • Network issue"
    fi
    echo ""

    # Check wake service
    echo -e "${BLUE}[4/5] Checking wake service...${NC}"
    if curl -s --max-time 3 "http://${GPU_IP}:${WAKE_PORT}/status" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Wake service responding${NC}"
    else
        echo -e "   ${RED}❌ Wake service not responding${NC}"
        echo "   Home PC might be:"
        echo "     • Sleeping (try: gpu-wake wake)"
        echo "     • Powered off"
        echo "     • Wake service not running"
    fi
    echo ""

    # Check Ollama
    echo -e "${BLUE}[5/5] Checking Ollama...${NC}"
    if curl -s --max-time 3 "http://${GPU_IP}:${OLLAMA_PORT}/api/tags" > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ Ollama ready${NC}"
    else
        echo -e "   ${YELLOW}⚠️  Ollama not ready${NC}"
        echo "   Try waking the GPU first"
    fi
    echo ""

    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Quick fixes:"
    echo "  1. Ensure home PC is on"
    echo "  2. Check NordVPN is running on both devices"
    echo "  3. Verify meshnet is enabled and paired"
    echo "  4. Try: gpu-wake wake"
}

# Main command handler
case "${1:-status}" in
    status)
        check_status
        ;;
    wake)
        wake_gpu
        ;;
    test)
        test_connection
        ;;
    troubleshoot|diagnose)
        troubleshoot
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
EOFWAKE

# Replace placeholder with actual IP
sed -i.bak "s/GPU_IP_PLACEHOLDER/${GPU_IP}/g" ~/gpu-tools/gpu-wake
rm ~/gpu-tools/gpu-wake.bak

chmod +x ~/gpu-tools/gpu-wake

# Create GPU wrapper for Ollama
cat > ~/gpu-tools/ollama-gpu << EOF
#!/bin/bash
# Use GPU remotely via NordVPN Meshnet

export OLLAMA_HOST="http://${GPU_IP}:11434"
ollama "\$@"
EOF

chmod +x ~/gpu-tools/ollama-gpu

# Create desktop shortcuts
cat > ~/Desktop/GPU_Wake.command << EOF
#!/bin/bash
cd ~/gpu-tools
./gpu-wake wake
echo ""
read -p "Press Enter to close..."
EOF

chmod +x ~/Desktop/GPU_Wake.command

cat > ~/Desktop/GPU_Status.command << EOF
#!/bin/bash
cd ~/gpu-tools
./gpu-wake status
echo ""
read -p "Press Enter to close..."
EOF

chmod +x ~/Desktop/GPU_Status.command

cat > ~/Desktop/Open_WebUI.command << EOF
#!/bin/bash
# Open WebUI Launcher

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  OPEN WEBUI LAUNCHER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running"
    echo ""
    echo "Please start Docker Desktop first:"
    echo "1. Open Applications"
    echo "2. Launch Docker Desktop"
    echo "3. Wait for whale icon in menu bar"
    echo "4. Run this script again"
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# Check if Open WebUI container exists
if docker ps -a | grep -q "open-webui"; then
    # Container exists, check if running
    if docker ps | grep -q "open-webui"; then
        echo "✅ Open WebUI is already running"
        echo ""
        echo "Opening browser..."
        open "http://localhost:3000"
    else
        echo "Starting Open WebUI..."
        docker start open-webui
        echo ""
        echo "✅ Open WebUI started!"
        echo ""
        echo "Opening browser in 3 seconds..."
        sleep 3
        open "http://localhost:3000"
    fi
else
    echo "Open WebUI not found. Starting fresh..."
    cd ~/gpu-tools
    ./start-webui
fi

echo ""
read -p "Press Enter to close..."
EOF

chmod +x ~/Desktop/Open_WebUI.command

# Add to PATH
if ! grep -q "gpu-tools" ~/.zshrc 2>/dev/null; then
    echo 'export PATH="$HOME/gpu-tools:$PATH"' >> ~/.zshrc
fi

if ! grep -q "gpu-tools" ~/.bash_profile 2>/dev/null; then
    echo 'export PATH="$HOME/gpu-tools:$PATH"' >> ~/.bash_profile
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SETUP COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Desktop shortcuts created:"
echo "  • Open_WebUI.command - Start web interface (MAIN)"
echo "  • GPU_Wake.command - Wake up GPU"
echo "  • GPU_Status.command - Check GPU status"
echo ""
echo "Open WebUI (Web Interface):"
echo "  • Browser: http://localhost:3000"
echo "  • Restart: start-webui"
echo "  • Already connected to your GPU!"
echo ""
echo "Command-line tools:"
echo "  gpu-wake status      - Check GPU status"
echo "  gpu-wake wake        - Wake GPU from sleep"
echo "  gpu-wake test        - Test connection"
echo "  gpu-wake troubleshoot - Run diagnostics"
echo ""
echo "  ollama-gpu list      - List models on GPU"
echo "  ollama-gpu run llama2 - Run model on GPU"
echo ""
echo "GPU Server: http://${GPU_IP}:11434"
echo ""
echo "Security: ✅ E2E encrypted via NordVPN Meshnet"
echo "          ✅ Public WiFi protected via NordVPN server"
echo ""
echo "Testing GPU now..."
echo ""

# Initial test
~/gpu-tools/gpu-wake status

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 Open WebUI should be opening in your browser!"
echo ""
echo "First time setup in Open WebUI:"
echo "1. Create an account (stored locally)"
echo "2. Models from GPU will appear automatically"
echo "3. Start chatting!"
echo ""
echo "If GPU is asleep, wake it first:"
echo "  gpu-wake wake"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
