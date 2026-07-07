import os
import sys
import requests
from colorama import init, Fore, Style

init(autoreset=True)

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════╗
║        {Fore.GREEN}SMS SENDER TOOL v1.0{Fore.CYAN}           ║
║     {Fore.YELLOW}Made for GitHub Deployment{Fore.CYAN}         ║
╚══════════════════════════════════════════╝{Style.RESET_ALL}
"""

# ========== CONFIGURATION ==========
YOUR_NAME = "Kavinda"           # <-- මෙතන ඔබේ නම දාන්න
TWILIO_ACCOUNT_SID = "ACbe7ec6b3480c623f0038cd466bfc8de8"  # <-- Twilio SID
TWILIO_AUTH_TOKEN = "b6f7e783ed0135cca2ebd3d067decb58"    # <-- Twilio Auth Token
TWILIO_PHONE_NUMBER = "+12762761630"   # <-- Twilio එකෙන් ගත්ත number
# ===================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def validate_phone(number):
    # Simple validation - must start with + and have digits
    if not number.startswith('+'):
        return False
    if not number[1:].isdigit():
        return False
    if len(number) < 10:
        return False
    return True

def send_sms_twilio(target_number, message):
    """Send SMS using Twilio API"""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": target_number,
        "Body": message
    }
    
    try:
        response = requests.post(
            url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data=data,
            timeout=30
        )
        
        if response.status_code == 201:
            return True, response.json().get('sid', 'Unknown')
        else:
            error = response.json().get('message', 'Unknown error')
            return False, f"Twilio Error: {error}"
            
    except Exception as e:
        return False, str(e)

def main():
    clear_screen()
    print(BANNER)
    
    print(f"\n{Fore.YELLOW}[!] Sender will appear as: {Fore.GREEN}{YOUR_NAME}{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}[!] Using Twilio number: {Fore.CYAN}{TWILIO_PHONE_NUMBER}{Style.RESET_ALL}\n")
    
    # Step 1: Get target number
    while True:
        target = input(f"{Fore.WHITE}[+] Enter target phone number (with country code, e.g. +94771234567): {Fore.GREEN}")
        if validate_phone(target):
            break
        print(f"{Fore.RED}[X] Invalid number! Must start with + and contain only digits.{Style.RESET_ALL}")
    
    # Step 2: Get message
    print(f"\n{Fore.WHITE}[+] Enter your message (press Ctrl+D or type 'SEND' on new line to finish):{Style.RESET_ALL}")
    lines = []
    try:
        while True:
            line = input()
            if line.strip().upper() == 'SEND':
                break
            lines.append(line)
    except EOFError:
        pass
    
    message = "\n".join(lines).strip()
    
    if not message:
        print(f"\n{Fore.RED}[X] Message cannot be empty!{Style.RESET_ALL}")
        sys.exit(1)
    
    # Add sender name to message
    full_message = f"From: {YOUR_NAME}\n\n{message}"
    
    print(f"\n{Fore.YELLOW}[*] Preparing to send...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}    Target : {Fore.WHITE}{target}")
    print(f"{Fore.CYAN}    Sender : {Fore.WHITE}{YOUR_NAME}")
    print(f"{Fore.CYAN}    Message: {Fore.WHITE}{message[:50]}{'...' if len(message) > 50 else ''}{Style.RESET_ALL}")
    
    confirm = input(f"\n{Fore.YELLOW}[?] Send SMS? (y/n): {Fore.GREEN}").strip().lower()
    if confirm != 'y':
        print(f"\n{Fore.RED}[!] Cancelled.{Style.RESET_ALL}")
        sys.exit(0)
    
    print(f"\n{Fore.YELLOW}[*] Sending SMS via Twilio...{Style.RESET_ALL}")
    success, result = send_sms_twilio(target, full_message)
    
    if success:
        print(f"\n{Fore.GREEN}[✓] SMS sent successfully!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Message SID: {result}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Receiver will see: {YOUR_NAME}{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}[X] Failed to send SMS!{Style.RESET_ALL}")
        print(f"{Fore.RED}[X] Error: {result}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Check your Twilio credentials and balance.{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
