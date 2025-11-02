#!/bin/bash
# Start IB Gateway with IBC on AWS
# Usage: ./start_ibgateway.sh

echo "🚀 Starting IB Gateway..."

# Check if already running
if ps aux | grep -v grep | grep "ibcalpha.ibc.IbcGateway" > /dev/null; then
    echo "✅ IB Gateway is already running"
    ps aux | grep java | grep ibgateway | head -1
    exit 0
fi

# Start Xvfb (virtual display) if needed
if ! ps aux | grep -v grep | grep "Xvfb :1" > /dev/null; then
    echo "📺 Starting Xvfb (virtual display)..."
    sudo Xvfb :1 -screen 0 1024x768x24 &
    sleep 2
fi

# Start IB Gateway with IBC
echo "🔧 Launching IB Gateway..."
cd /opt/ibc
sudo DISPLAY=:1 /opt/ibc/gatewaystart.sh -inline &

echo ""
echo "⏳ Waiting for startup (30 seconds)..."
sleep 30

echo ""
echo "="*70
echo "✅ IB Gateway startup initiated!"
echo "="*70
echo ""
echo "📱 CHECK YOUR PHONE FOR 2FA APPROVAL"
echo ""
echo "After approving, verify connection:"
echo "  cd ~/strategy && source venv/bin/activate"
echo "  python3 -c \"from ib_insync import IB; ib = IB(); ib.connect('127.0.0.1', 4001); print('✅ Connected' if ib.isConnected() else '❌ Failed'); ib.disconnect()\""
echo ""
