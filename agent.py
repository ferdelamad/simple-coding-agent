import json
import os
import anthropic
from typing import Dict, Any, List, Optional, Callable, Tuple

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        function: Callable[[Dict[str, Any]], Tuple[str, Optional[str]]]
    ):
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.function = function

class Agent:
    def __init__(
        self,
        client: anthropic.Anthropic,
        get_user_message: Callable[[], Tuple[str, bool]],
        tools: List[ToolDefinition]
    ):
        self.client = client
        self.get_user_message = get_user_message
        self.tools = tools
    
    def run_inference(self, conversation: List[Dict[str, Any]]) -> Dict[str, Any]:
        anthropic_tools = []
        for tool in self.tools:
            anthropic_tools.append({
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            })
        
        message = self.client.messages.create(
            model="claude-3-7-sonnet-latest",
            max_tokens=1024,
            messages=conversation,
            tools=anthropic_tools if anthropic_tools else []
        )
        return message
    
    def execute_tool(self, tool_id: str, name: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        tool_def = None
        for tool in self.tools:
            if tool.name == name:
                tool_def = tool
                break
        
        if tool_def is None:
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": "tool not found",
                "is_error": True
            }
        
        print(f"\u001b[92mtool\u001b[0m: {name}({json.dumps(input_data)})")
        result, error = tool_def.function(input_data)
        
        if error:
            return {
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": error,
                "is_error": True
            }
        
        return {
            "type": "tool_result",
            "tool_use_id": tool_id,
            "content": result,
            "is_error": False
        }
    
    def run(self):
        conversation = []
        print("\n\u001b[1mChat with Claude\u001b[0m")
        print("Type your messages and press Enter to chat")
        print("Press Ctrl+C to exit\n")
        
        read_user_input = True
        while True:
            if read_user_input:
                print("\u001b[94mYou\u001b[0m: ", end="")
                user_input, ok = self.get_user_message()
                if not ok:
                    break
                
                user_message = {
                    "role": "user",
                    "content": [{"type": "text", "text": user_input}]
                }
                conversation.append(user_message)
            
            message = self.run_inference(conversation)
            
            assistant_message = {
                "role": "assistant",
                "content": []
            }
            
            tool_results = []
            for content in message.content:
                if content.type == "text":
                    print(f"\u001b[93mClaude\u001b[0m: {content.text}")
                    assistant_message["content"].append({
                        "type": "text",
                        "text": content.text
                    })
                elif content.type == "tool_use":
                    result = self.execute_tool(content.id, content.name, content.input)
                    tool_results.append(result)
                    assistant_message["content"].append({
                        "type": "tool_use",
                        "id": content.id,
                        "name": content.name,
                        "input": content.input
                    })
            
            conversation.append(assistant_message)
            
            if not tool_results:
                read_user_input = True
                continue
            
            read_user_input = False
            conversation.append({
                "role": "user",
                "content": tool_results
            })


# Tool Definitions
def read_file(input_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    try:
        path = input_data["path"]
        with open(path, "r") as f:
            content = f.read()
        return content, None
    except Exception as e:
        return "", str(e)


read_file_definition = ToolDefinition(
    name="read_file",
    description="Read the contents of a given relative file path. Use this when you want to see what's inside a file. Do not use this with directory names.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string", 
                "description": "The relative path of a file in the working directory."
            }
        },
        "required": ["path"]
    },
    function=read_file
)

def list_files(input_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    try:
        path = input_data.get("path", ".")
        files = []
        
        if os.path.isdir(path):
            for root, dirs, filenames in os.walk(path):
                # Get relative path from the base directory
                rel_root = os.path.relpath(root, path)
                if rel_root == ".":
                    rel_root = ""
                
                # Add directories
                for d in dirs:
                    if rel_root:
                        files.append(os.path.join(rel_root, d) + "/")
                    else:
                        files.append(d + "/")
                
                # Add files
                for f in filenames:
                    if rel_root:
                        files.append(os.path.join(rel_root, f))
                    else:
                        files.append(f)
                
                # Only process first level if not root
                if rel_root != "":
                    break
        
        return json.dumps(files), None
    except Exception as e:
        return "", str(e)

list_files_definition = ToolDefinition(
    name="list_files",
    description="List files and directories at a given path. If no path is provided, lists files in the current directory.",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Optional relative path to list files from. Defaults to current directory if not provided."
            }
        },
        "required": []
    },
    function=list_files
)

def edit_file(input_data: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    try:
        path = input_data["path"]
        old_str = input_data["old_str"]
        new_str = input_data["new_str"]
        
        if not path or old_str == new_str:
            return "", "invalid input parameters"
        
        try:
            with open(path, "r") as f:
                content = f.read()
            
            old_content = content
            new_content = content.replace(old_str, new_str)
            
            if old_content == new_content and old_str != "":
                return "", "old_str not found in file"
            
            with open(path, "w") as f:
                f.write(new_content)
            
            return "OK", None
            
        except FileNotFoundError:
            if old_str == "":
                return create_new_file(path, new_str)
            else:
                raise
    except Exception as e:
        return "", str(e)

def create_new_file(file_path: str, content: str) -> Tuple[str, Optional[str]]:
    try:
        directory = os.path.dirname(file_path)
        if directory and directory != ".":
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, "w") as f:
            f.write(content)
        
        return f"Successfully created file {file_path}", None
    except Exception as e:
        return "", str(e)

edit_file_definition = ToolDefinition(
    name="edit_file",
    description="""Make edits to a text file.
Replaces 'old_str' with 'new_str' in the given file. 'old_str' and 'new_str' MUST be different from each other.
If the file specified with path doesn't exist, it will be created.
""",
    input_schema={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The path to the file"
            },
            "old_str": {
                "type": "string",
                "description": "Text to search for - must match exactly and must only have one match exactly"
            },
            "new_str": {
                "type": "string",
                "description": "Text to replace old_str with"
            }
        },
        "required": ["path", "old_str", "new_str"]
    },
    function=edit_file
)

def main():
    # Try to load from .env file if available
    if DOTENV_AVAILABLE:
        load_dotenv()
    
    # Get API key from environment variable or use provided value
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Warning: ANTHROPIC_API_KEY environment variable not set")
        api_key = input("Please enter your Anthropic API key: ")
    
    client = anthropic.Anthropic(api_key=api_key)
    
    def get_user_message() -> Tuple[str, bool]:
        try:
            return input(), True
        except (EOFError, KeyboardInterrupt):
            return "", False
    
    tools = [read_file_definition, list_files_definition, edit_file_definition]
    agent = Agent(client, get_user_message, tools)
    
    try:
        agent.run()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()