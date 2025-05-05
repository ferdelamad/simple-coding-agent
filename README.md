# Simple Coding Agent

A minimalist implementation of an AI coding assistant built with less than 350 lines of Python code. This project demonstrates how to create a functional AI agent using the Anthropic Claude API.

## Overview

This project shows that building a useful AI coding assistant doesn't require complex architecture or thousands of lines of code. With a straightforward approach, you can create a terminal-based agent that:

- Chats with Claude 3.7 Sonnet
- Executes tools to interact with your filesystem
- Maintains conversation context

## Features

- Interactive terminal-based chat interface
- File system operations:
  - Read file contents
  - List files in directories
  - Edit existing files or create new ones
- Clean, easy-to-understand implementation

## Installation

1. Clone this repository
2. Install dependencies:
```
pip install anthropic
pip install python-dotenv  # Optional
```
3. Set up your Anthropic API key:
   - Create an `.env` file with `ANTHROPIC_API_KEY=your_key_here`
   - Or set it as an environment variable
   - Or enter it when prompted

## Usage

Run the agent with:
```
python agent.py
```

Example commands:
```
You: What files are in this project?
Claude: [Uses list_files tool]

You: Show me the agent.py file
Claude: [Uses read_file tool to display content]

You: Create a new file called hello.py with a simple "Hello, World" program
Claude: [Uses edit_file tool to create the file]
```

## How It Works

The implementation consists of:

1. An `Agent` class that manages conversations with Claude
2. Tool definitions for file operations
3. A simple loop that handles user input and Claude responses

The agent uses Claude's tool-use capabilities to execute actions on your file system based on your instructions.

## Limitations & Future Improvements

This implementation is intentionally minimal to demonstrate core concepts. Potential improvements include:

- Better error handling
- More robust file operations
- Additional tools (executing code, web search, etc.)
- Modularization into separate files
- Configuration options
- Persistent chat history

## License

MIT 