import subprocess
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import os

class WifiScanner:
    def __init__(self):
        self.networks = []
        
    def scan_networks(self):
        """Scan for nearby Wi-Fi networks using system commands"""
        try:
            # For Windows
            if os.name == 'nt':
                command = ['netsh', 'wlan', 'show', 'networks', 'mode=Bssid']
                output = subprocess.check_output(command, universal_newlines=True)
                return self._parse_windows_output(output)
            # For Linux/MacOS
            else:
                command = ['iwlist', 'wlan0', 'scan']
                output = subprocess.check_output(command, universal_newlines=True, stderr=subprocess.DEVNULL)
                return self._parse_linux_output(output)
        except subprocess.CalledProcessError:
            print("Error: Unable to scan networks. Make sure you have necessary permissions.")
            return []

    def _parse_windows_output(self, output):
        """Parse Windows netsh command output"""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if 'SSID' in line and 'BSSID' not in line:
                if current_network:
                    if len(current_network) >= 3 and current_network.get('ssid'):  
                        current_network['timestamp'] = datetime.now()
                        networks.append(current_network.copy())
                    current_network = {}
                current_network['ssid'] = line.split(':')[1].strip()
            elif 'Signal' in line:
                try:
                    signal_str = line.split(':')[1].strip()
                    signal = int(signal_str.replace('%', ''))
                    current_network['signal_strength'] = signal
                except (ValueError, IndexError):
                    continue
            elif 'Channel' in line:
                try:
                    channel_str = line.split(':')[1].strip()
                    channel = int(re.search(r'(\d+)', channel_str).group(1))
                    current_network['channel'] = channel
                except (ValueError, IndexError, AttributeError):
                    continue
        
        # add the last network if it exists and SSID is not empty
        if current_network and len(current_network) >= 3 and current_network.get('ssid'):
            current_network['timestamp'] = datetime.now()
            networks.append(current_network)
        
        return networks

    def _parse_linux_output(self, output):
        """Parse Linux iwlist command output"""
        networks = []
        current_network = {}
        
        for line in output.split('\n'):
            line = line.strip()
            if 'ESSID' in line:
                current_network['ssid'] = line.split(':')[1].strip('"')
            elif 'Quality' in line:
                signal = re.search(r'Signal level=(-\d+)', line)
                if signal:
                    # Convert dBm to percentage (rough approximation)
                    signal_strength = int((100 + int(signal.group(1))) * 2)
                    current_network['signal_strength'] = min(100, max(0, signal_strength))
            elif 'Channel' in line:
                current_network['channel'] = int(line.split(':')[1])
                if len(current_network) == 3 and current_network.get('ssid'):
                    current_network['timestamp'] = datetime.now()
                    networks.append(current_network.copy())
                    current_network = {}
        
        return networks

    def create_heatmap(self, location_name='current_location'):
        """Create a simple heatmap of signal strengths"""
        networks = self.scan_networks()
        if not networks:
            print("No networks found!")
            return

        # Convert to DataFrame
        df = pd.DataFrame(networks)
        print("Found networks:")
        print(df)  # Debug print
        
        # Create a pivot table for the heatmap
        pivot_data = df.pivot_table(
            values='signal_strength',
            index='ssid',
            columns='channel',
            aggfunc='mean'
        )

        # Create heatmap
        plt.figure(figsize=(12, 8))
        sns.heatmap(pivot_data, annot=True, cmap='YlOrRd', fmt='.0f')
        plt.title(f'Wi-Fi Networks Signal Strength at {location_name}')
        plt.xlabel('Channel')
        plt.ylabel('SSID')
        
        # Save the plot
        filename = f'wifi_heatmap_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename)
        plt.close()
        
        return filename

    def save_to_csv(self):
        """Save network data to CSV file"""
        networks = self.scan_networks()
        if networks:
            df = pd.DataFrame(networks)
            filename = f'wifi_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            df.to_csv(filename, index=False)
            print("Network data:")  # Debug print
            print(df)  # Debug print
            return filename
        return None

def main():
    scanner = WifiScanner()
    
    # Scan and save data
    csv_file = scanner.save_to_csv()
    if csv_file:
        print(f"Network data saved to {csv_file}")
    
    # Create and save heatmap
    heatmap_file = scanner.create_heatmap()
    if heatmap_file:
        print(f"Heatmap saved to {heatmap_file}")

if __name__ == "__main__":
    main()
