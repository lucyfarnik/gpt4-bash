import subprocess
import re
from openai import OpenAI
from colorama import Fore, Style

client = OpenAI()

sys_prompt = "You are being run in a scaffold in a shell on a Macbook. You will be shown the result of the command and be able to run more commands. Other things you say will be sent to the user. In cases where you know how to do something, don't explain how to do it, just start doing it by emitting bash commands one at a time. The user uses fish, but you're in a bash shell. Remember that you can't interact with stdin directly, so if you want to e.g. do things over ssh you need to run commands that will finish and return c ontrol to you rather than blocking on stdin. Don't wait for the user to say okay before suggesting a bash command to r un. If possible, don't include explanation, just say the command.  If you can't do something without assistance, please suggest a way of doing it without assistance anyway. Your output should be a bash command written in a <bash> XML tag — make sure you always use this format."
def generate_response(history: list[dict]):
    """
    Function to send the conversation history to OpenAI's Chat API and return its response.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": sys_prompt},
                *history,
            ],
            max_tokens=150,
        )
        return response.choices[0].message.content
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"

def extract_command(response):
    """
    Extracts a command enclosed in <bash> tags from the response.
    """
    match = re.search(r"<bash>(.*?)</bash>", response, re.DOTALL)
    return match.group(1).strip() if match else None

def execute_command(command):
    """
    Execute a shell command.
    """
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout if result.stdout else result.stderr
    except subprocess.CalledProcessError as e:
        return f"Execution Error: {e}"

def main():
    history = []
    print(Fore.CYAN, "System: ", sys_prompt, Style.RESET_ALL, "\n\n")

    execution_result = None
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break

        # if we have an execution result from last time, add it to the user input
        user_input = f"<user_input>{user_input.strip()}</user_input>"
        if execution_result is not None:
            user_input = f"<execution_result>{execution_result}</execution_result>\n\n{user_input}"
        history.append({"role": "user", "content": user_input})

        gpt4_response = generate_response(history)
        print(Fore.BLUE, "GPT-4:", gpt4_response, Style.RESET_ALL, "\n")
        history.append({"role": "assistant", "content": gpt4_response})

        command = extract_command(gpt4_response)
        print(Fore.YELLOW, "GPT-4 suggests to execute: ", command, Style.RESET_ALL)
        confirm = input("Do you want to execute this command? ([y]/n): \n")
        if confirm.lower() in ['y', '']:
            execution_result = execute_command(command)
            print(Fore.MAGENTA + "Execution result:\n", execution_result, Style.RESET_ALL, "\n")
        else:
            execution_result = None
            print("Command execution cancelled.")

if __name__ == "__main__":
    main()
