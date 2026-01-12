import anthropic
import os
import subprocess
import json


def ask_claude_to_plot(description, verbose=False):
    """
    Ask Claude to perform a task that may require code execution and file operations.

    Args:
        prompt (str): The task you want Claude to perform
        verbose (bool): Whether to print progress information

    Returns:
        str: Claude's final response text
    """
    client = anthropic.Anthropic(api_key=os.environ.get("CLAUDE_API_KEY"))

    # Initialize the conversation
    messages = [
        {
            "role": "user",
            "content": "Save a figure at reconstructed_figure.jpg based on this description: \n" + description
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

    final_response = ""

    # Tool use loop
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            tools=tools,
            messages=messages
        )

        if verbose:
            print(f"\nStop reason: {response.stop_reason}")

        # Collect text content
        for block in response.content:
            if block.type == "text":
                final_response = block.text
                if verbose:
                    print(f"Claude: {block.text}")

        # Check if we're done
        if response.stop_reason == "end_turn":
            if verbose:
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
                    if verbose:
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
                            if verbose:
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

                            if verbose:
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
            if verbose:
                print(f"Unexpected stop reason: {response.stop_reason}")
            break

    return final_response


# Example usage:
if __name__ == "__main__":
    # Create a sine wave plot
    response = ask_claude_for_plot("Create a plot showing a sine wave and save it as plot.png")
    print(f"\nFinal response: {response}")

    # Create a bar chart
    response = ask_claude_for_plot(
        "Create a bar chart showing sales data for Q1-Q4: [100, 150, 120, 180] and save as sales.png",
        verbose=False  # Set to False for quieter output
    )
    print(f"\nFinal response: {response}")