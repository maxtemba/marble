# helper functions TODO: either add more functions here or move back
import os

def read_vivado_results(results_file_path='./build/results.txt'):
    """reads WNS, WHS, and power from the Vivado generated results.txt file."""
    wns = None
    whs = None # currently unused
    power = None
    try:
        with open(results_file_path, 'r') as f:
            for line in f:
                if line.startswith('WNS:'):
                    wns_str = line.split(':')[1].strip()
                    if wns_str != "N/A":
                        wns = float(wns_str)
                elif line.startswith('WHS:'):
                    whs_str = line.split(':')[1].strip()
                    if whs_str != "N/A":
                        whs = float(whs_str) 
                elif line.startswith('Power:'):
                    power_str = line.split(':')[1].strip()
                    if power_str != "N/A":
                        power = float(power_str)
        
        # error handling for missing values
        if wns is None:
            print(f"WARN: WNS not found or N/A in {results_file_path}")
        if power is None:
            print(f"WARN: Power not found or N/A in {results_file_path}")

        return wns, power

    except FileNotFoundError:
        print(f"ERROR: File {results_file_path} not found")
        return None, None
    except Exception as e:
        print(f"ERROR reading results file: {e}")
        return None, None

