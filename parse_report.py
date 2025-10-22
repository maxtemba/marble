# parse_report.py
import re

def parse_timing_report(report_file_path):
    try:
        with open(report_file_path, 'r') as f:
            content = f.read()

        # search for WNS value line
        match = re.search(r"WNS\(ns\)\s+TNS\(ns\).*\n.*\n\s+(-?\d+\.\d+)", content)
        
        if match:
            wns = float(match.group(1))
            print(f"Report-Leser: found WNS {wns} ns")
            return wns
        
        # check for 'NA' case
        match_na = re.search(r"WNS\(ns\)\s+TNS\(ns\).*\n.*\n\s+(NA)", content)
        if match_na:
            print("Report-Leser: WNS is 'NA'.")
            return None
            
        print("Report-Leser: error finding WNS.")
        return None

    except FileNotFoundError:
        print(f"Report-Leser: path not found: {report_file_path}")
        return None
    except Exception as e:
        print(f"Report-Leser: error: {e}")
        return None