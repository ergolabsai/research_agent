import anthropic
import os
import subprocess
import json

client = anthropic.Anthropic(api_key="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")

# Initialize the conversation
messages = [
    {
        "role": "user",
        "content": "Create a plot showing a sine wave and save it as plot.png"
    }
]

tools = [
    {
        "type": "bash_20250124",
        "name": "bash"
    },
    {
        "type": "text_editor_20250728",
        "name": "str_replace_based_edit_tool"
    }
]

# Tool use loop
while True:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        tools=tools,
        messages=messages
    )

    print(f"\nStop reason: {response.stop_reason}")

    # Print any text content
    for block in response.content:
        if block.type == "text":
            print(f"Claude: {block.text}")

    # Check if we're done
    if response.stop_reason == "end_turn":
        print("\nTask completed!")
        break

    # Handle tool use
    if response.stop_reason == "tool_use":
        # Add Claude's response to messages
        messages.append({
            "role": "assistant",
            "content": response.content
        })

        # Process each tool use
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"\nTool: {block.name}")
                print(f"Input: {json.dumps(block.input, indent=2)}")

                if block.name == "bash":
                    # Execute bash command
                    try:
                        result = subprocess.run(
                            block.input["command"],
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        output = result.stdout + result.stderr
                        print(f"Output: {output}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output if output else "Command executed successfully"
                        })
                    except subprocess.TimeoutExpired:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": "Command timed out",
                            "is_error": True
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

                elif block.name == "str_replace_based_edit_tool":
                    # Handle file editing
                    command = block.input.get("command")
                    path = block.input.get("path", "")

                    try:
                        if command == "create":
                            # Create new file
                            with open(path, 'w') as f:
                                f.write(block.input.get("file_text", ""))
                            output = f"File created: {path}"

                        elif command == "str_replace":
                            # Replace text in file
                            with open(path, 'r') as f:
                                content = f.read()

                            old_str = block.input.get("old_str", "")
                            new_str = block.input.get("new_str", "")

                            if old_str in content:
                                content = content.replace(old_str, new_str, 1)
                                with open(path, 'w') as f:
                                    f.write(content)
                                output = f"File edited: {path}"
                            else:
                                output = f"String not found in file: {old_str}"

                        elif command == "view":
                            # View file
                            with open(path, 'r') as f:
                                content = f.read()
                            output = content

                        else:
                            output = f"Unknown command: {command}"

                        print(f"Output: {output}")

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output
                        })

                    except Exception as e:
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": f"Error: {str(e)}",
                            "is_error": True
                        })

        # Add tool results to messages
        messages.append({
            "role": "user",
            "content": tool_results
        })

    else:
        # Unexpected stop reason
        print(f"Unexpected stop reason: {response.stop_reason}")
        break

print("\nCheck your directory for plot.png!")