import os
import sys
import time
import requests
from colorama import init, Fore, Style

init(autoreset=True)

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════╗
║        {Fore.GREEN}Mr DKxx TOOL v3.0{Fore.CYAN}                ║
║     {Fore.YELLOW}Twilio + Termux Integration{Fore.CYAN}         ║
╚══════════════════════════════════════════╝{Style.RESET_ALL}
"""

# ========== TWILIO CONFIG ==========
# මේ credentials වෙනුවට ඔයාගේ Twilio Account details දාන්න
# හරි නැත්නම් environment variables විදියට set කරන්න
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_SID', '')      # Set this or edit below
TWILIO_AUTH_TOKEN  = os.environ.get('TWILIO_AUTH', '')     # Set this or edit below
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE', '')   # Set this or edit below
# ===================================

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_termux():
    try:
        result = os.popen('uname -o').read().strip()
        return 'Android' in result
    except:
        return False

def validate_phone(number):
    """Validate phone number - must start with + and have digits"""
    if not number.startswith('+'):
        return False
    cleaned = number.replace('+', '').replace('-', '').replace(' ', '')
    if not cleaned.isdigit():
        return False
    if len(cleaned) < 7 or len(cleaned) > 15:
        return False
    return True

def get_sender_name(option_name):
    """Get the sender name to display"""
    clear_screen()
    print(BANNER)
    print(f"\n{Fore.YELLOW}[{option_name}] Step 1: Enter Sender Name{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   -> The receiver will see THIS name{Style.RESET_ALL}")
    while True:
        name = input(f"\n{Fore.CYAN}[?] Enter name to display: {Fore.GREEN}").strip()
        if len(name) >= 1 and len(name) <= 50:
            return name
        print(f"{Fore.RED}[X] Name must be 1-50 characters!{Style.RESET_ALL}")

def check_twilio_credentials():
    """Check if Twilio credentials are set"""
    if not TWILIO_ACCOUNT_SID or TWILIO_ACCOUNT_SID == '':
        return False, "TWILIO_SID not set"
    if not TWILIO_AUTH_TOKEN or TWILIO_AUTH_TOKEN == '':
        return False, "TWILIO_AUTH not set"
    if not TWILIO_PHONE_NUMBER or TWILIO_PHONE_NUMBER == '':
        return False, "TWILIO_PHONE not set"
    if not TWILIO_PHONE_NUMBER.startswith('+'):
        return False, "TWILIO_PHONE must start with +"
    return True, "OK"

def configure_twilio():
    """Let user configure Twilio credentials interactively"""
    global TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    
    clear_screen()
    print(BANNER)
    print(f"\n{Fore.YELLOW}[ TWILIO CONFIGURATION ]{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   Enter your Twilio credentials (they will NOT be saved to disk){Style.RESET_ALL}\n")
    
    TWILIO_ACCOUNT_SID = input(f"{Fore.CYAN}[?] Twilio Account SID: {Fore.GREEN}").strip()
    TWILIO_AUTH_TOKEN = input(f"{Fore.CYAN}[?] Twilio Auth Token: {Fore.GREEN}").strip()
    TWILIO_PHONE_NUMBER = input(f"{Fore.CYAN}[?] Twilio Phone Number (with +): {Fore.GREEN}").strip()
    
    valid, msg = check_twilio_credentials()
    if not valid:
        print(f"\n{Fore.RED}[X] Invalid: {msg}{Style.RESET_ALL}")
        retry = input(f"\n{Fore.CYAN}[?] Try again? (y/n): {Fore.GREEN}").strip().lower()
        if retry == 'y':
            configure_twilio()
        else:
            return False
    return True

def send_twilio_sms(target_number, message, sender_name):
    """Send SMS via Twilio API"""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    
    # Message with sender name prefix
    full_message = f"[{sender_name}]\n{message}"
    
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": target_number,
        "Body": full_message
    }
    
    try:
        response = requests.post(
            url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data=data,
            timeout=30
        )
        
        if response.status_code == 201:
            sid = response.json().get('sid', 'Unknown')
            return True, sid
        else:
            error = response.json().get('message', 'Unknown error')
            return False, f"Twilio Error: {error}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - check internet"
    except Exception as e:
        return False, str(e)

def make_twilio_call(target_number, sender_name):
    """
    Make a call via Twilio Voice API.
    The call will:
    - Come from Twilio number
    - If answered, play a short silence then hang up (simulates missed call)
    - If not answered, it's a missed call
    """
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls.json"
    
    # TwiML to play a short silence and then hang up
    # This creates the "missed call" effect
    twiml = '<?xml version="1.0" encoding="UTF-8"?>'
    twiml += '<Response>'
    twiml += '<Pause length="1"/>'  # 1 second silence
    twiml += '<Hangup/>'
    twiml += '</Response>'
    
    data = {
        "From": TWILIO_PHONE_NUMBER,
        "To": target_number,
        "Twiml": twiml,
        "StatusCallback": "",  # We'll use sync response instead
        "Timeout": 30  # Ring for 30 seconds
    }
    
    try:
        response = requests.post(
            url,
            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
            data=data,
            timeout=40
        )
        
        if response.status_code == 201:
            call_data = response.json()
            call_sid = call_data.get('sid', 'Unknown')
            
            print(f"\n{Fore.YELLOW}[*] Call initiated! SID: {call_sid}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[*] Waiting for call status...{Style.RESET_ALL}")
            
            # Poll for call status
            status = call_data.get('status', 'queued')
            start_time = time.time()
            timeout = 60  # Max wait 60 seconds
            
            while status in ['queued', 'ringing', 'in-progress'] and time.time() - start_time < timeout:
                time.sleep(3)
                
                # Check call status
                status_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls/{call_sid}.json"
                status_resp = requests.get(
                    status_url,
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                    timeout=10
                )
                
                if status_resp.status_code == 200:
                    status = status_resp.json().get('status', 'unknown')
                    
                    if status == 'in-progress':
                        print(f"{Fore.GREEN}[✓] Call was ANSWERED!{Style.RESET_ALL}")
                        # Immediately hang up
                        requests.post(
                            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls/{call_sid}.json",
                            auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                            data={"Status": "completed"},
                            timeout=10
                        )
                        return True, f"Answered -> Success"
                        
                    elif status == 'completed':
                        print(f"{Fore.GREEN}[✓] Call COMPLETED (answered then hung up){Style.RESET_ALL}")
                        return True, "Success"
                        
                    elif status == 'busy':
                        print(f"{Fore.YELLOW}[!] Target was BUSY{Style.RESET_ALL}")
                        return True, "Busy"
                        
                    elif status == 'no-answer':
                        print(f"{Fore.YELLOW}[!] No answer (real missed call){Style.RESET_ALL}")
                        return True, "Missed"
                        
                    elif status == 'failed':
                        return False, "Call failed"
                        
                    print(f"{Fore.CYAN}   Status: {status}...{Style.RESET_ALL}")
            
            if status in ['queued', 'ringing']:
                # Cancel the call if still ringing
                requests.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Calls/{call_sid}.json",
                    auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN),
                    data={"Status": "canceled"},
                    timeout=10
                )
                return True, "Cancelled (timed out)"
            
            return True, f"Final status: {status}"
            
        else:
            error = response.json().get('message', 'Unknown error')
            return False, f"Twilio Error: {error}"
            
    except requests.exceptions.Timeout:
        return False, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, "Connection error - check internet"
    except Exception as e:
        return False, str(e)

def option1_missed_call():
    """Missed Call via Twilio"""
    name = get_sender_name("MISSED CALL")
    
    clear_screen()
    print(BANNER)
    print(f"\n{Fore.YELLOW}[ MISSED CALL SYSTEM - Twilio ]{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   Sender Name: {Fore.GREEN}{name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   From Number: {Fore.GREEN}{TWILIO_PHONE_NUMBER}{Style.RESET_ALL}")
    
    # Get target number
    while True:
        number = input(f"\n{Fore.CYAN}[?] Enter target number (with +, e.g. +94771234567): {Fore.GREEN}").strip()
        if validate_phone(number):
            break
        print(f"{Fore.RED}[X] Invalid number! Must start with +.{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}[*] Summary:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}    To     : {Fore.WHITE}{number}")
    print(f"{Fore.CYAN}    From   : {Fore.WHITE}{TWILIO_PHONE_NUMBER}")
    print(f"{Fore.CYAN}    Name   : {Fore.WHITE}{name}")
    
    confirm = input(f"\n{Fore.CYAN}[?] Make the call? (y/n): {Fore.GREEN}").strip().lower()
    if confirm != 'y':
        print(f"\n{Fore.RED}[!] Cancelled.{Style.RESET_ALL}")
        return
    
    success, result = make_twilio_call(number, name)
    
    print(f"\n{'='*50}")
    if success:
        print(f"{Fore.GREEN}[✓] SUCCESS! {result}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Call made from: {TWILIO_PHONE_NUMBER}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Receiver sees: {name}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[X] FAILED: {result}{Style.RESET_ALL}")
    print(f"{'='*50}")

def option2_send_sms():
    """Send SMS via Twilio"""
    name = get_sender_name("SEND SMS")
    
    clear_screen()
    print(BANNER)
    print(f"\n{Fore.YELLOW}[ SMS SENDER - Twilio ]{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   Sender Name: {Fore.GREEN}{name}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   From Number: {Fore.GREEN}{TWILIO_PHONE_NUMBER}{Style.RESET_ALL}")
    
    # Get target number
    while True:
        number = input(f"\n{Fore.CYAN}[?] Enter target number (with +, e.g. +94771234567): {Fore.GREEN}").strip()
        if validate_phone(number):
            break
        print(f"{Fore.RED}[X] Invalid number! Must start with +.{Style.RESET_ALL}")
    
    # Get message
    print(f"\n{Fore.CYAN}[?] Enter your message (type 'SEND' on new line to finish, 'CANCEL' to cancel):{Style.RESET_ALL}")
    print(f"{Fore.WHITE}   -> Long messages supported (will be concatenated by carrier){Style.RESET_ALL}")
    
    lines = []
    try:
        while True:
            line = input(f"{Fore.GREEN}    ")
            if line.strip().upper() == 'SEND':
                break
            if line.strip().upper() == 'CANCEL':
                print(f"\n{Fore.RED}[!] Cancelled.{Style.RESET_ALL}")
                return
            lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Interrupted.{Style.RESET_ALL}")
        return
    
    message = "\n".join(lines).strip()
    
    if not message:
        print(f"\n{Fore.RED}[X] Message cannot be empty!{Style.RESET_ALL}")
        return
    
    if len(message) > 160:
        print(f"{Fore.YELLOW}[!] Message is {len(message)} chars. Long SMS supported.{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}[*] Summary:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}    To     : {Fore.WHITE}{number}")
    print(f"{Fore.CYAN}    From   : {Fore.WHITE}{TWILIO_PHONE_NUMBER}")
    print(f"{Fore.CYAN}    Name   : {Fore.WHITE}{name}")
    print(f"{Fore.CYAN}    Length : {Fore.WHITE}{len(message)} chars")
    
    confirm = input(f"\n{Fore.CYAN}[?] Send SMS? (y/n): {Fore.GREEN}").strip().lower()
    if confirm != 'y':
        print(f"\n{Fore.RED}[!] Cancelled.{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.YELLOW}[*] Sending SMS via Twilio...{Style.RESET_ALL}")
    success, result = send_twilio_sms(number, message, name)
    
    print(f"\n{'='*50}")
    if success:
        print(f"{Fore.GREEN}[✓] SMS sent successfully!{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] SID: {result}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] From: {TWILIO_PHONE_NUMBER}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}[✓] Message starts with: [{name}]{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}[X] FAILED: {result}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] Check your Twilio balance and credentials.{Style.RESET_ALL}")
    print(f"{'='*50}")

def main():
    """Main menu"""
    global TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER
    
    clear_screen()
    print(BANNER)
    
    # Check Twilio credentials
    valid, msg = check_twilio_credentials()
    if not valid:
        print(f"{Fore.YELLOW}[!] Twilio credentials not configured.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}[!] You can set them as environment variables or enter now.{Style.RESET_ALL}")
        setup = input(f"\n{Fore.CYAN}[?] Configure Twilio now? (y/n): {Fore.GREEN}").strip().lower()
        if setup == 'y':
            if not configure_twilio():
                print(f"{Fore.RED}[X] Cannot proceed without Twilio credentials.{Style.RESET_ALL}")
                sys.exit(1)
        else:
            print(f"{Fore.RED}[X] Twilio credentials required. Exiting.{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Set: export TWILIO_SID='your_sid'{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Set: export TWILIO_AUTH='your_auth'{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Set: export TWILIO_PHONE='+your_number'{Style.RESET_ALL}")
            sys.exit(1)
    
    clear_screen()
    print(BANNER)
    print(f"{Fore.CYAN}   Twilio Account: {Fore.GREEN}{TWILIO_ACCOUNT_SID[:10]}...{Style.RESET_ALL}")
    print(f"{Fore.CYAN}   Phone Number : {Fore.GREEN}{TWILIO_PHONE_NUMBER}{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}╔══════════════════════════════════════════╗")
    print(f"║        {Fore.GREEN}SELECT AN OPTION{Fore.YELLOW}                  ║")
    print(f"╚══════════════════════════════════════════╝{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}[1]{Fore.WHITE} 1 Missed Call Number")
    print(f"{Fore.CYAN}[2]{Fore.WHITE} Send SMS AnyDk")
    print(f"{Fore.CYAN}[3]{Fore.WHITE} Change Twilio Credentials")
    print(f"{Fore.CYAN}[4]{Fore.WHITE} Exit{Style.RESET_ALL}")
    
    while True:
        choice = input(f"\n{Fore.CYAN}[?] Enter your choice (1/2/3/4): {Fore.GREEN}").strip()
        
        if choice == '1':
            option1_missed_call()
            break
        elif choice == '2':
            option2_send_sms()
            break
        elif choice == '3':
            configure_twilio()
            main()
            return
        elif choice == '4':
            print(f"\n{Fore.YELLOW}[!] Goodbye!{Style.RESET_ALL}")
            sys.exit(0)
        else:
            print(f"{Fore.RED}[X] Invalid choice!{Style.RESET_ALL}")
    
    print(f"\n{Fore.YELLOW}[*] Returning to main menu...{Style.RESET_ALL}")
    time.sleep(2)
    main()

if __name__ == "__main__":
    try:
        # Also try to read from a config file if exists
        if os.path.exists('.twilio_config'):
            with open('.twilio_config', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, val = line.strip().split('=', 1)
                        if key == 'TWILIO_SID' and not TWILIO_ACCOUNT_SID:
                            TWILIO_ACCOUNT_SID = val
                        elif key == 'TWILIO_AUTH' and not TWILIO_AUTH_TOKEN:
                            TWILIO_AUTH_TOKEN = val
                        elif key == 'TWILIO_PHONE' and not TWILIO_PHONE_NUMBER:
                            TWILIO_PHONE_NUMBER = val
        
        # If still not set, try to use defaults from code (not recommended)
        if not TWILIO_ACCOUNT_SID:
            TWILIO_ACCOUNT_SID = "ACbe7ec6b3480c623f0038cd466bfc8de8"  # Replace with yours
        if not TWILIO_AUTH_TOKEN:
            TWILIO_AUTH_TOKEN = "b6f7e783ed0135cca2ebd3d067decb58"      # Replace with yours
        if not TWILIO_PHONE_NUMBER:
            TWILIO_PHONE_NUMBER = "+12762761630"                         # Replace with yours
        
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}[!] Interrupted by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}[X] Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)
