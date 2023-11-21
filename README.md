# GPT-4 Bash Scaffold (Redwood Research MATS & Astra applications)
This is a CLI that uses the OpenAI streaming API to send prompts (including
the previous dialogue and command outputs) to GPT-4, gets it to output bash commands,
then checks with the user for confirmation before running them.

I also started implemented a web app version of this using Streamlit, that part is
pretty close to being done but not quite there yet.

This repo was put together within 2 hours for Buck's and Fabien's MATS and Astra
applications. It's not robustly tested (yet), if you're not from Redwood and you
found this somehow, maybe consider not over-relying on this codebase.
