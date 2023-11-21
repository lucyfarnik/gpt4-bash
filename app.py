#! /usr/bin/env python3
import subprocess
import re
import sys
import os
import argparse
from openai import OpenAI
from colorama import Fore, Style
import streamlit as st

client = OpenAI()

sys_prompt = "You are being run in a scaffold in a shell on a Macbook.  You will be shown the result of the command and be able to run more commands.  Other things you say will be sent to the user. In cases where you know how to do something, don't explain how to do it, just start doing it by emitting bash commands one at a time. The user uses fish, but you're in a bash shell.  Remember that you can't interact with stdin directly, so if you want to e.g.  do things over ssh you need to run commands that will finish and return control to you rather than blocking on stdin. Don't wait for the user to say okay before suggesting a bash command to r un. If possible, don't include explanation, just say the command. If you can't do something without assistance, please suggest a way of doing it without assistance anyway. Most of the time the best way to reply will be by just outputting a single bash command written in a <bash> XML tag — make sure you always use this format when you want to run something in the terminal."

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

def cli_main():
    # !FIXME right now we're always adding to history; eventually we should summarize/filter it 
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


        print(Fore.BLUE, "GPT-4:", )
        gpt4_response = ""
        for resp in client.chat.completions.create(model="gpt-4-1106-preview",
                                                   messages=[
                                                       {"role": "system", "content": sys_prompt},
                                                       *history,
                                                   ],
                                                   max_tokens=150,
                                                   stream=True):
            resp_token = resp.choices[0].delta.content
            if resp_token is None:
                break
            gpt4_response += resp_token
            sys.stdout.write(resp_token)
            sys.stdout.flush()
        print(Style.RESET_ALL, "\n")
        history.append({"role": "assistant", "content": gpt4_response})

        command = extract_command(gpt4_response)
        if command is not None:
            print(Fore.YELLOW, "GPT-4 suggests to execute: ", command, Style.RESET_ALL)
            confirm = input("Do you want to execute this command? ([y]/n): \n")
            if confirm.lower() in ['y', '']:
                execution_result = execute_command(command)
                print(Fore.MAGENTA + "Execution result:\n", execution_result, 
                      Style.RESET_ALL, "\n")
            else:
                execution_result = None
                print("Command execution cancelled.")

def gpt4_tokens_streamlit(history):
    st.session_state.gpt4_currently_responding = True
    for resp in client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": sys_prompt},
            *history,
        ],
        max_tokens=150,
        stream=True):
        
        resp_token = resp.choices[0].delta.content
        if resp_token is None:
            break

        # Update session state and rerun
        st.session_state.gpt4_response += resp_token
        st.rerun()
    st.session_state.gpt4_currently_responding = False

def streamlit_main():
    if 'gpt4_response' not in st.session_state:
        st.session_state.gpt4_response = ""
    if 'gpt4_currently_responding' not in st.session_state:
        st.session_state.gpt4_currently_responding = False
    if 'history' not in st.session_state:
        st.session_state.history = []
    
    st.title("GPT-4 Command Execution App")
    execution_result = None

    user_input = st.text_input("Your instructions:", key="user_input")
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})

        if execution_result:
            st.session_state.history.append({"role": "execution_result", "content": execution_result})

        # Call OpenAI and get response
        gpt4_tokens_streamlit(st.session_state.history)

        if not st.session_state.gpt4_currently_responding:
            st.session_state.history.append({"role": "assistant", "content": st.session_state.gpt4_response})
        st.text(st.session_state.gpt4_response)

        if not st.session_state.gpt4_currently_responding:
            command = extract_command(st.session_state.gpt4_response)
            if command:
                if st.button("Execute: " + command):
                    execution_result = execute_command(command)
                    st.text(st.session_state.gpt4_response)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", "--web-app", help="Run in web app mode", action="store_true")
    parser.add_argument("--internal-streamlit-gui", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.web_app:
        raise NotImplementedError("The web app mode hasn't been finished yet.")
        subprocess.Popen(["streamlit", "run", __file__, "--server.port=8501", "--", "--internal-streamlit-gui"])
    elif args.internal_streamlit_gui:
        streamlit_main()
    else: 
        cli_main()
