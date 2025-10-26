"""
Setup script for configuring multiple Hyperliquid vaults
"""

import os
import json
from typing import List, Dict

def create_vault_configs() -> List[Dict]:
    """Create vault configurations interactively"""
    print("🚀 Hyperliquid Multi-Vault Setup")
    print("=" * 50)
    
    vault_configs = []
    
    # Get number of vaults
    while True:
        try:
            num_vaults = int(input("\nHow many vaults do you want to configure? (1-5): "))
            if 1 <= num_vaults <= 5:
                break
            else:
                print("Please enter a number between 1 and 5")
        except ValueError:
            print("Please enter a valid number")
    
    print(f"\nConfiguring {num_vaults} vault(s)...")
    
    for i in range(num_vaults):
        print(f"\n--- Vault {i+1} Configuration ---")
        
        # Get vault name
        vault_name = input(f"Vault {i+1} name (default: 'Vault {i+1}'): ").strip()
        if not vault_name:
            vault_name = f"Vault {i+1}"
        
        # Get API key
        api_key = input(f"API Key for {vault_name}: ").strip()
        if not api_key:
            print("❌ API key is required")
            continue
        
        # Get secret key
        secret_key = input(f"Secret Key for {vault_name}: ").strip()
        if not secret_key:
            print("❌ Secret key is required")
            continue
        
        # Get vault address
        vault_address = input(f"Vault Address for {vault_name}: ").strip()
        if not vault_address:
            print("❌ Vault address is required")
            continue
        
        # Get weight (optional)
        weight_input = input(f"Weight for {vault_name} (default: 1.0): ").strip()
        try:
            weight = float(weight_input) if weight_input else 1.0
        except ValueError:
            weight = 1.0
            print("Using default weight: 1.0")
        
        vault_config = {
            'name': vault_name,
            'api_key': api_key,
            'secret_key': secret_key,
            'vault_address': vault_address,
            'weight': weight
        }
        
        vault_configs.append(vault_config)
        print(f"✅ {vault_name} configured")
    
    return vault_configs

def save_vault_configs(vault_configs: List[Dict], filename: str = "vault_configs.json"):
    """Save vault configurations to file"""
    with open(filename, 'w') as f:
        json.dump(vault_configs, f, indent=2)
    print(f"\n💾 Vault configurations saved to {filename}")

def create_env_file(vault_configs: List[Dict], filename: str = ".env"):
    """Create .env file with vault configurations"""
    env_content = []
    
    for i, vault in enumerate(vault_configs, 1):
        env_content.append(f"HL_API_KEY_{i}={vault['api_key']}")
        env_content.append(f"HL_SECRET_KEY_{i}={vault['secret_key']}")
        env_content.append(f"VAULT_ADDRESS_{i}={vault['vault_address']}")
    
    # Add other required environment variables
    env_content.extend([
        "",
        "# Telegram Configuration",
        "TELEGRAM_TOKEN=your_telegram_bot_token",
        "TELEGRAM_CHAT_ID=your_chat_id",
        "",
        "# Strategy Configuration", 
        "UPDATE_INTERVAL_MINUTES=60",
        "ENABLE_TELEGRAM_NOTIFICATIONS=true",
        "ENABLE_EMA_FILTER=true"
    ])
    
    with open(filename, 'w') as f:
        f.write('\n'.join(env_content))
    
    print(f"💾 Environment file created: {filename}")

def update_config_file(vault_configs: List[Dict]):
    """Update config.py with vault configurations"""
    config_content = f'''# Multi-Vault Configuration
VAULT_CONFIGS = {json.dumps(vault_configs, indent=4)}
'''
    
    print("\n📝 Add this to your config.py file:")
    print("=" * 50)
    print(config_content)
    print("=" * 50)

def main():
    """Main setup function"""
    print("Welcome to the Hyperliquid Multi-Vault Setup!")
    print("This script will help you configure multiple vaults for the macro quadrant strategy.")
    
    # Create vault configurations
    vault_configs = create_vault_configs()
    
    if not vault_configs:
        print("❌ No vaults configured. Exiting.")
        return
    
    # Save configurations
    save_vault_configs(vault_configs)
    create_env_file(vault_configs)
    update_config_file(vault_configs)
    
    print(f"\n✅ Setup complete!")
    print(f"📊 Configured {len(vault_configs)} vault(s)")
    
    # Show next steps
    print(f"\n📋 Next Steps:")
    print(f"1. Update your .env file with your actual API keys")
    print(f"2. Add the vault configurations to config.py")
    print(f"3. Run test_vaults.py to test connections")
    print(f"4. Run the strategy with: python main.py")

if __name__ == "__main__":
    main() 