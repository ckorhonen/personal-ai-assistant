# Working with this Project

This repository contains a multi-agent personal assistant built with LangGraph and LangChain.  Use this guide to navigate the codebase and run the project locally.

## Repository layout

- `app.py` – Entry point for Slack or Telegram interactions.  Polls for new messages and relays them to the personal assistant.
- `app_whatsapp.py` – FastAPI application exposing a webhook for Twilio WhatsApp messages.
- `src/` – Main Python package.
  - `agents/` – Agent abstractions and the `PersonalAssistant` implementation.
  - `channels/` – Channel-specific helpers for Telegram, Slack and WhatsApp.
  - `prompts/` – Prompt templates for all agents.
  - `tools/` – Custom LangChain tools such as email/calendar/Notion utilities.
  - `utils.py` – Helper functions for credentials and LLM configuration.
- `db/` – SQLite database used as a LangGraph checkpoint store.

## Style guidelines

- Code is Python 3.9+ and follows standard **PEP8** conventions with four-space indentation.
- Use descriptive docstrings for modules, classes and functions.
- Prefer `f"..."` strings for formatting.
- When adding new tools or channels keep the structure under `src/` consistent.

## Setup & local development

1. Install dependencies using:

   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in all required credentials (LLM keys, Google credentials, communication channel tokens…).

3. For Google APIs place `credentials.json` in the project root and run the application once to generate `token.json`.

4. Run the Telegram/Slack version with:

   ```bash
   python app.py
   ```

   For WhatsApp, start the FastAPI server:

   ```bash
   python app_whatsapp.py
   ```

   Expose the webhook to Twilio using a tunnelling tool such as `ngrok`.

## Additional notes

- No automated tests are provided, so please test any changes manually.
- The SQLite database under `db/` stores conversation checkpoints.  Remove it if you want to start with a fresh agent memory.
